# Copyright 2025 The EasyDeL/ejKernel Author @erfanzar (Erfan Zare Chavoshi).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import jax
import jax.numpy as jnp
import triton
import triton.language as tl
from jax import Array

from ejkernel.callib import next_power_of_2, triton_call
from ejkernel.ops import FwdParams


@triton.autotune(
    configs=[triton.Config({}, num_warps=nw) for nw in (1, 2, 4, 8)],
    key=["BLOCK_SIZE", "BLOCK_D"],
)
@triton.jit
def ragged_decode_mqa_fwd_kernel(
    q_ptr,
    k_ptr,
    v_ptr,
    s_ptr,
    e_ptr,
    aux_ptr,
    o_ptr,
    m_ptr,
    l_ptr,
    softmax_scale,
    logits_soft_cap,
    NSINKS: tl.constexpr,
    HAS_AUX: tl.constexpr,
    SL_LEFT: tl.constexpr,
    SL_RIGHT: tl.constexpr,
    B: tl.constexpr,
    S: tl.constexpr,
    G: tl.constexpr,
    D: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
    BLOCK_D: tl.constexpr,
    NBLOCKS: tl.constexpr,
    NS_PAD: tl.constexpr,
):
    """
    One kernel instance computes the streamed decode for a single (b,g) pair:
    - q: [D]
    - K/V streamed across S in tiles of BLOCK_SIZE
    - streaming softmax (m,l accumulation)
    - sinks contribute to normalization (not masked) but are not tied to V
    """
    pid = tl.program_id(0)
    b = pid // G
    g = pid % G

    q_off = b * (G * D) + g * D
    o_off = q_off
    m_off = b * G + g
    l_off = m_off

    s_b = tl.load(s_ptr + b).to(tl.int32)
    e_b = tl.load(e_ptr + b).to(tl.int32)
    qpos = e_b - 1

    d_idx = tl.arange(0, BLOCK_D)
    q_mask = d_idx < D
    q_vec = tl.load(q_ptr + q_off + d_idx, mask=q_mask, other=0.0).to(tl.float32)

    m_prev = tl.full((), float("-inf"), dtype=tl.float32)
    l_prev = tl.zeros((), dtype=tl.float32)
    o_vec = tl.zeros([BLOCK_D], dtype=tl.float32)

    for i in tl.static_range(0, NBLOCKS):
        t_idx = i * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)

        valid = (t_idx >= s_b) & (t_idx < e_b)

        if SL_LEFT >= 0:
            valid = valid & (t_idx >= (qpos - SL_LEFT))
        if SL_RIGHT >= 0:
            valid = valid & (t_idx <= (qpos + SL_RIGHT))

        k_base = b * (S * D) + (i * BLOCK_SIZE) * D
        acc_qk = tl.zeros([BLOCK_SIZE], dtype=tl.float32)

        for kd in tl.static_range(0, D, BLOCK_D):
            d_col = kd + d_idx
            d_m = d_col < D

            k_block = tl.load(
                k_ptr + k_base + d_col[None, :] + (tl.arange(0, BLOCK_SIZE)[:, None] * D),
                mask=d_m[None, :],
                other=0.0,
            ).to(tl.float32)

            acc_qk += tl.sum(k_block * q_vec[None, :], axis=1)

        acc_qk = acc_qk * softmax_scale
        if logits_soft_cap > 0:
            x = acc_qk / logits_soft_cap

            ax = tl.where(x >= 0, x, -x)
            z = tl.exp(-2.0 * ax)
            tanh_x = tl.where(x >= 0, (1 - z) / (1 + z), -(1 - z) / (1 + z))
            acc_qk = logits_soft_cap * tanh_x

        if HAS_AUX and NSINKS > 0:
            aux_off = g * NSINKS if G > 1 else 0
            idx = tl.arange(0, NS_PAD)
            m_aux = idx < NSINKS
            aux_logits = tl.load(
                aux_ptr + aux_off + idx,
                mask=m_aux,
                other=tl.full((), float("-inf"), dtype=tl.float32),
            ).to(tl.float32)
        else:
            aux_logits = tl.zeros([0], dtype=tl.float32)

        neg_inf = tl.full([BLOCK_SIZE], float("-inf"), dtype=tl.float32)
        acc_qk_masked = tl.where(valid, acc_qk, neg_inf)

        sum_valid = tl.sum(valid.to(tl.int32), axis=0)
        any_seq = sum_valid > 0

        if HAS_AUX and NSINKS > 0:
            m_seq = tl.where(any_seq, tl.max(acc_qk_masked), tl.full((), float("-inf"), dtype=tl.float32))
            m_aux = tl.max(aux_logits)
            m_curr = tl.maximum(m_seq, m_aux)
            s_seq = tl.where(any_seq, tl.exp(acc_qk_masked - m_curr), tl.zeros([BLOCK_SIZE], dtype=tl.float32))
            s_sink = tl.exp(aux_logits - m_curr)
        else:
            m_curr = tl.where(any_seq, tl.max(acc_qk_masked), m_prev)
            s_seq = tl.where(any_seq, tl.exp(acc_qk_masked - m_curr), tl.zeros([BLOCK_SIZE], dtype=tl.float32))
            s_sink = tl.zeros([0], dtype=tl.float32)

        o_blk = tl.zeros([BLOCK_D], dtype=tl.float32)
        for vd in tl.static_range(0, D, BLOCK_D):
            d_col = vd + d_idx
            d_m = d_col < D
            v_block = tl.load(
                v_ptr + k_base + d_col[None, :] + (tl.arange(0, BLOCK_SIZE)[:, None] * D),
                mask=d_m[None, :],
                other=0.0,
            ).to(tl.float32)
            o_blk += tl.sum(v_block * s_seq[:, None], axis=0)

        sum_s = tl.sum(s_seq)
        if HAS_AUX and NSINKS > 0:
            sum_s += tl.sum(s_sink)

        has_update = (sum_s > 0) | (l_prev > 0)
        m_next = tl.where(has_update, tl.maximum(m_prev, m_curr), m_prev)
        alpha = tl.where(has_update, tl.exp(m_prev - m_next), 0.0)
        beta = tl.where(has_update, tl.exp(m_curr - m_next), 0.0)
        l_next = tl.where(has_update, alpha * l_prev + beta * sum_s, l_prev)
        l_safe = tl.where(l_next == 0.0, 1.0, l_next)
        o_new = tl.where(has_update, (alpha * l_prev * o_vec + beta * o_blk) / l_safe, o_vec)

        o_vec = o_new
        m_prev = m_next
        l_prev = l_next

    tl.store(o_ptr + o_off + d_idx, o_vec, mask=q_mask)
    tl.store(m_ptr + m_off, m_prev)
    tl.store(l_ptr + l_off, l_prev)


def ragged_decode_mqa_triton(
    q: Array,
    k: Array,
    v: Array,
    starts: Array,
    ends: Array,
    softmax_scale: float,
    block_size: int,
    sliding_window: tuple[int, int] | None,
    logits_soft_cap: float,
    aux: Array | None,
) -> Array:
    B, G, D = q.shape
    S = k.shape[1]
    BLOCK_SIZE = int(block_size)
    BLOCK_D = min(128, next_power_of_2(D))

    HAS_AUX = aux is not None
    NS = int(aux.shape[-1]) if HAS_AUX else 0

    aux_arg = aux if HAS_AUX else jnp.zeros((1,), dtype=q.dtype)

    NBLOCKS = (S + BLOCK_SIZE - 1) // BLOCK_SIZE

    NS_PAD = max(1, int(next_power_of_2(NS)))

    out = triton_call(
        q,
        k,
        v,
        starts.astype(jnp.int32),
        ends.astype(jnp.int32),
        aux_arg,
        kernel=ragged_decode_mqa_fwd_kernel,
        grid=lambda META: (B * G,),
        out_shape=[
            jax.ShapeDtypeStruct((B, G, D), dtype=q.dtype),
            jax.ShapeDtypeStruct((B, G), dtype=jnp.float32),
            jax.ShapeDtypeStruct((B, G), dtype=jnp.float32),
        ],
        softmax_scale=float(softmax_scale),
        logits_soft_cap=float(logits_soft_cap),
        NSINKS=NS,
        HAS_AUX=HAS_AUX,
        SL_LEFT=int(sliding_window[0]) if sliding_window is not None else -1,
        SL_RIGHT=int(sliding_window[1]) if sliding_window is not None else -1,
        B=B,
        S=S,
        G=G,
        D=D,
        BLOCK_SIZE=BLOCK_SIZE,
        BLOCK_D=BLOCK_D,
        NBLOCKS=NBLOCKS,
        NS_PAD=NS_PAD,
        name="ejkernel::triton::ragged_decode_mqa_fwd",
    )[0]
    return out


def inner_decode_triton(
    query_tensor: Array,
    key_tensor: Array,
    value_tensor: Array,
    sequence_start: Array,
    sequence_end: Array,
    softmax_scale: float | None = None,
    fwd_params: FwdParams | None = None,
    sliding_window: tuple[int, int] | None = None,
    logits_soft_cap: float | None = None,
    softmax_aux: Array | None = None,
) -> Array:
    """
    GPU/Triton inner decode. Mirrors your inner_decode_tpu:
      - group Q into [B, HKV, G, D]
      - K/V -> [B, HKV, S, D]
      - run MQA ragged decode per kv head to get [B, G, D]
      - reshape back to [B, HQ, D]
    """
    B, HQ, D = query_tensor.shape

    if softmax_scale is None:
        softmax_scale = query_tensor.shape[-1] ** -0.5

    _S, HKV = key_tensor.shape[1], key_tensor.shape[2]
    assert HQ % HKV == 0, "GQA requires HQ divisible by HKV"
    G = HQ // HKV

    q_grouped = query_tensor.reshape(B, HKV, G, D)

    k_per = jnp.swapaxes(key_tensor, 1, 2)
    v_per = jnp.swapaxes(value_tensor, 1, 2)

    def _aux_for_head(h: int):
        if softmax_aux is None:
            return None
        if softmax_aux.ndim == 2:
            a = softmax_aux[h]
            return jnp.broadcast_to(a[None, :], (G, a.shape[0]))
        else:
            return jnp.broadcast_to(softmax_aux[None, :], (G, softmax_aux.shape[0]))

    outs = []
    for h in range(HKV):
        q_h = q_grouped[:, h, :, :]
        k_h = k_per[:, h, :, :]
        v_h = v_per[:, h, :, :]
        aux_h = _aux_for_head(h)

        out_h = ragged_decode_mqa_triton(
            q=q_h,
            k=k_h,
            v=v_h,
            starts=sequence_start,
            ends=sequence_end,
            softmax_scale=(1.0 if softmax_scale is None else float(softmax_scale)),
            block_size=int(fwd_params.kv_blocksize),
            sliding_window=sliding_window,
            logits_soft_cap=(0.0 if logits_soft_cap is None else float(logits_soft_cap)),
            aux=aux_h,
        )
        outs.append(out_h)

    out = jnp.stack(outs, axis=1).reshape(B, HQ, D)
    return out
