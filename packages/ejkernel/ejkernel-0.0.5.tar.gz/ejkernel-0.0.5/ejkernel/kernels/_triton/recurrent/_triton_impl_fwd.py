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
import triton
import triton.language as tl
from jax import numpy as jnp
from jaxtyping import Array, Float, Int

from ejkernel.callib import cdiv, triton_call


@triton.autotune(
    configs=[triton.Config({}, num_warps=num_warps) for num_warps in [4, 8]],
    key=["key_chunk_size", "blocksize_v", "USE_G", "USE_G_GAMMA", "USE_GK", "USE_GV"],
)
@triton.heuristics(
    {
        "USE_INITIAL_STATE": lambda args: args["h0"] != 1,
        "STORE_FINAL_STATE": lambda args: args["ht"] != 1,
        "IS_VARLEN": lambda args: args["cu_seqlens"] != 1,
    }
)
@triton.jit
def fwd_kernel(
    q,
    k,
    v,
    g,
    g_gamma,
    gk,
    gv,
    h0,
    cu_seqlens,
    softmax_scale,
    o,
    ht,
    T: tl.constexpr,
    B: tl.constexpr,
    H: tl.constexpr,
    K: tl.constexpr,
    V: tl.constexpr,
    key_chunk_size: tl.constexpr,
    blocksize_v: tl.constexpr,
    REVERSE: tl.constexpr,
    USE_G: tl.constexpr,
    USE_G_GAMMA: tl.constexpr,
    USE_GK: tl.constexpr,
    USE_GV: tl.constexpr,
    USE_INITIAL_STATE: tl.constexpr,
    STORE_FINAL_STATE: tl.constexpr,
    IS_VARLEN: tl.constexpr,
):
    """Triton kernel for forward pass of recurrent linear attention.

    Processes sequences step-by-step with O(N) complexity, maintaining a
    hidden state that accumulates key-value information. Supports various
    gating mechanisms and both forward/reverse processing.

    Args:
        q, k, v: Query, key, value tensor pointers
        g: Optional gate tensor for GLA-style gating
        g_gamma: Optional decay factor for Lightning attention
        gk, gv: Optional gates applied to keys and values
        h0: Initial hidden state pointer
        cu_seqlens: Cumulative sequence lengths for variable-length mode
        softmax_scale: Query scaling factor
        o: Output tensor pointer
        ht: Final hidden state pointer
        T, B, H, K, V: Tensor dimensions (sequence, batch, heads, key/value dims)
        key_chunk_size, blocksize_v: Block sizes for tiling
        REVERSE: Process sequence in reverse order
        USE_G, USE_G_GAMMA, USE_GK, USE_GV: Gating configuration flags
        USE_INITIAL_STATE: Whether to use initial hidden state
        STORE_FINAL_STATE: Whether to store final hidden state
        IS_VARLEN: Variable-length sequence mode
    """
    i_v, i_k, i_nh = tl.program_id(0).to(tl.int64), tl.program_id(1).to(tl.int64), tl.program_id(2).to(tl.int64)
    i_n, i_h = i_nh // H, i_nh % H
    if IS_VARLEN:
        bos, eos = tl.load(cu_seqlens + i_n).to(tl.int64), tl.load(cu_seqlens + i_n + 1).to(tl.int64)
        scope = T
        T = eos - bos
    else:
        bos, eos = i_n * T, i_n * T + T
        scope = B * T

    o_k = i_k * key_chunk_size + tl.arange(0, key_chunk_size)
    o_v = i_v * blocksize_v + tl.arange(0, blocksize_v)
    p_q = q + (bos + ((T - 1) if REVERSE else 0)) * H * K + i_h * K + o_k
    p_k = k + (bos + ((T - 1) if REVERSE else 0)) * H * K + i_h * K + o_k
    p_v = v + (bos + ((T - 1) if REVERSE else 0)) * H * V + i_h * V + o_v
    p_o = o + ((i_k * scope + bos) + ((T - 1) if REVERSE else 0)) * H * V + i_h * V + o_v
    if USE_G:
        p_g = g + (bos + ((T - 1) if REVERSE else 0)) * H + i_h
    if USE_GK:
        p_gk = gk + (bos + ((T - 1) if REVERSE else 0)) * H * K + i_h * K + o_k
    if USE_GV:
        p_gv = gv + (bos + ((T - 1) if REVERSE else 0)) * H * V + i_h * V + o_v
    if USE_G_GAMMA:
        b_g_gamma = tl.load(g_gamma + i_h)

    mask_k = o_k < K
    mask_v = o_v < V
    mask_h = mask_k[:, None] & mask_v[None, :]
    b_h = tl.zeros([key_chunk_size, blocksize_v], dtype=tl.float32)

    if USE_INITIAL_STATE:
        p_h0 = h0 + i_nh * K * V + o_k[:, None] * V + o_v[None, :]
        b_h += tl.load(p_h0, mask=mask_h, other=0).to(tl.float32)

    for _ in range(0, T):
        b_q = tl.load(p_q, mask=mask_k, other=0).to(tl.float32) * softmax_scale
        b_k = tl.load(p_k, mask=mask_k, other=0).to(tl.float32)
        b_v = tl.load(p_v, mask=mask_v, other=0).to(tl.float32)
        if USE_G:
            b_g = tl.load(p_g).to(tl.float32)
            b_h = b_h * tl.exp(b_g)
        if USE_G_GAMMA:
            b_h = b_h * tl.exp(b_g_gamma)
        if USE_GK:
            b_gk = tl.load(p_gk, mask=mask_k, other=0).to(tl.float32)
            b_h = b_h * tl.exp(b_gk[:, None])
        if USE_GV:
            b_gv = tl.load(p_gv, mask=mask_v, other=0).to(tl.float32)
            b_h = b_h * tl.exp(b_gv[None, :])
        b_h += b_k[:, None] * b_v[None, :]
        b_o = b_h * b_q[:, None]
        b_o = tl.sum(b_o, axis=0)
        tl.store(p_o, b_o.to(p_o.dtype.element_ty), mask=mask_v)
        p_q += (-1 if REVERSE else 1) * H * K
        p_k += (-1 if REVERSE else 1) * H * K
        p_v += (-1 if REVERSE else 1) * H * V
        p_o += (-1 if REVERSE else 1) * H * V
        if USE_G:
            p_g += (-1 if REVERSE else 1) * H
        if USE_GK:
            p_gk += (-1 if REVERSE else 1) * H * K
        if USE_GV:
            p_gv += (-1 if REVERSE else 1) * H * V

    if STORE_FINAL_STATE:
        p_ht = ht + i_nh * K * V + o_k[:, None] * V + o_v[None, :]
        tl.store(p_ht, b_h.to(p_ht.dtype.element_ty), mask=mask_h)


def fwd_triton_impl(
    q: Float[Array, "batch seq_len num_heads head_dim"],
    k: Float[Array, "batch seq_len num_heads head_dim"],
    v: Float[Array, "batch seq_len num_heads head_dim"],
    g: Float[Array, "batch seq_len num_heads head_dim"] | None = None,
    g_gamma: Float[Array, "batch num_heads"] | None = None,
    gk: Float[Array, "batch seq_len num_heads head_dim"] | None = None,
    gv: Float[Array, "batch seq_len num_heads head_dim"] | None = None,
    softmax_scale: float | None = None,
    initial_state: Float[Array, "batch num_heads head_dim head_dim"] | None = None,
    reverse: bool = False,
    cu_seqlens: Int[Array, "num_seqs_plus_one"] | None = None,
) -> tuple[Float[Array, "batch seq_len num_heads head_dim"], Float[Array, "batch num_heads head_dim head_dim"]]:
    B, T, H, K, V = *k.shape, v.shape[-1]
    N = B if cu_seqlens is None else len(cu_seqlens) - 1
    key_chunk_size, blocksize_v = min(K, 64), min(V, 64)
    NumKBlocks, NumVBlocks = cdiv(K, key_chunk_size), cdiv(V, blocksize_v)

    h0 = initial_state
    ht_shape = (N, H, K, V)
    out_shape = (NumKBlocks, *v.shape)
    grid = (NumVBlocks, NumKBlocks, N * H)
    metaparams = dict(
        T=T,
        B=B,
        H=H,
        K=K,
        V=V,
        key_chunk_size=key_chunk_size,
        blocksize_v=blocksize_v,
        USE_G=g is not None,
        USE_G_GAMMA=g_gamma is not None,
        USE_GK=gk is not None,
        USE_GV=gv is not None,
        REVERSE=reverse,
    )
    out, ht = triton_call(
        q,
        k,
        v,
        g if g is not None else 1,
        g_gamma if g_gamma is not None else 1,
        gk if gk is not None else 1,
        gv if gv is not None else 1,
        h0 if h0 is not None else 1,
        cu_seqlens if cu_seqlens is not None else 1,
        softmax_scale if softmax_scale is not None else 1,
        kernel=fwd_kernel,
        out_shape=[
            jax.ShapeDtypeStruct(out_shape, q.dtype),
            jax.ShapeDtypeStruct(ht_shape, jnp.float32),
        ],
        name="ejkernel::triton::recurrent_fwd",
        grid=grid,
        **metaparams,
    )
    out = jnp.sum(out, axis=0)
    return out, ht
