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


import functools

import chex
import jax
import jax.numpy as jnp
import numpy as np
from jax import Array, lax
from jax.experimental import pallas as pl
from jax.experimental.pallas import tpu as pltpu
from jaxtyping import Float, Int

from ejkernel.callib import ejit
from ejkernel.ops import FwdParams


def get_mha_cost_estimate(shape_dtype):
    """Estimates the cost of MHA computation for use with Pallas.

    Args:
        shape_dtype (tuple): Tuple of chex.Array instances (query, key, value, start, end).

    Returns:
        pl.CostEstimate: A rough estimate of compute cost in terms of FLOPs, bytes, etc.
    """
    batch_size, _, num_heads, head_dim = shape_dtype[0].shape
    seq_len = shape_dtype[1].shape[1]

    return pl.CostEstimate(
        flops=batch_size * num_heads * seq_len * (2 * head_dim + seq_len + 2 * head_dim),
        transcendentals=batch_size * num_heads * seq_len,
        bytes_accessed=int(sum(np.prod(s.shape) * s.dtype.itemsize for s in shape_dtype)),
    )


def ragged_flash_attention_kernel(
    s_ref,
    e_ref,
    q_ref,
    k_ref,
    v_ref,
    o_ref,
    m_ref,
    l_ref,
    *,
    block_size: int,
    softmax_scale: float,
):
    """Flash Attention kernel for ragged sequences on TPU via Pallas.

    Applies a block-wise attention pattern while respecting per-sequence boundaries.

    Args:
        s_ref: Start indices of each sequence (prefetched).
        e_ref: End indices of each sequence (prefetched).
        q_ref: Query tensor reference.
        k_ref: Key tensor reference.
        v_ref: Value tensor reference.
        o_ref: Output tensor reference (written in-place).
        m_ref: Max logits (intermediate).
        l_ref: Normalization factors (intermediate).
        block_size (int): Size of blocks to compute attention on.
        softmax_scale (float): Scaling factor applied to attention logits.
    """
    b, i = pl.program_id(0), pl.program_id(1)

    @pl.when(i == 0)
    def init():
        m_ref[...] = jnp.full_like(m_ref, -jnp.inf)
        l_ref[...] = jnp.zeros_like(l_ref)
        o_ref[...] = jnp.zeros_like(o_ref)

    sequence_end = e_ref[b].reshape(1, 1)
    sequence_start = s_ref[b].reshape(1, 1)
    run_index = i * block_size

    @pl.when(run_index < e_ref[b])
    def run():
        q = q_ref[...].astype(jnp.float32)
        k = k_ref[...].astype(jnp.float32)
        v = v_ref[...].astype(jnp.float32)
        m_prev, l_prev = m_ref[...], l_ref[...]

        qk = lax.dot_general(q * softmax_scale, k, (((1,), (1,)), ((), ())), preferred_element_type=jnp.float32)

        ranges = (i * block_size) + jax.lax.broadcasted_iota(jnp.int32, qk.shape, 1)
        mask = (sequence_start <= ranges) & (ranges < sequence_end)

        qk = jnp.where(mask, qk, jnp.finfo(qk.dtype).min)
        m_curr = qk.max(axis=-1)

        s_curr = jnp.exp(qk - m_curr[..., None])
        o_curr_times_l_curr = jnp.dot(s_curr, v)

        m_curr = jax.lax.broadcast_in_dim(m_curr, m_prev.shape, (0,))
        m_next = jnp.maximum(m_prev, m_curr)
        alpha = jnp.exp(m_prev - m_next)
        beta = jnp.exp(m_curr - m_next)
        l_next = alpha * l_prev + beta * jax.lax.broadcast_in_dim(s_curr.sum(axis=-1), l_prev.shape, (0,))
        l_next_safe = jnp.where(l_next == 0.0, 1.0, l_next)

        m_ref[...], l_ref[...] = m_next, l_next_safe
        o_ref[...] = ((l_prev * alpha * o_ref[...] + beta * o_curr_times_l_curr) / l_next_safe).astype(o_ref.dtype)


def ragged_decode_mqa(
    query: chex.Array,
    key: chex.Array,
    value: chex.Array,
    sequence_start: chex.Array,
    sequence_end: chex.Array,
    softmax_scale: float | None = None,
    block_size: int = 256,
    cost_estimate: pl.CostEstimate | None = None,
) -> jax.Array:
    """
    Runs ragged MQA decoding using a Flash Attention Pallas kernel.

    Args:
        query (chex.Array): Query tensor of shape [B, H, D].
        key (chex.Array): Key tensor of shape [B, S, H, D].
        value (chex.Array): Value tensor of shape [B, S, H, D].
        sequence_start (chex.Array): Start indices of each sequence [B].
        sequence_end (chex.Array): End indices of each sequence [B].
        softmax_scale (float | None): Optional scale for attention logits.
        block_size (int): Number of tokens processed per block.
        cost_estimate (pl.CostEstimate | None): Optional cost model for Pallas.

    Returns:
        jax.Array: output array.
    """
    batch_size, num_heads, head_dim = query.shape

    sequence_start = sequence_start.reshape(batch_size)
    assert sequence_start.shape == (batch_size,)
    assert sequence_start.dtype == jnp.int32

    sequence_end = sequence_end.reshape(batch_size)
    assert sequence_end.shape == (batch_size,)
    assert sequence_end.dtype == jnp.int32

    seq_len = key.shape[1]
    if softmax_scale is None:
        softmax_scale = query.shape[-1] ** -0.5

    out, *_ = pl.pallas_call(
        functools.partial(
            ragged_flash_attention_kernel,
            block_size=block_size,
            softmax_scale=softmax_scale,
        ),
        grid_spec=pltpu.PrefetchScalarGridSpec(
            num_scalar_prefetch=2,
            in_specs=[
                pl.BlockSpec((None, num_heads, head_dim), lambda b, i, *_: (b, 0, 0)),
                pl.BlockSpec((None, block_size, head_dim), lambda b, i, *_: (b, i, 0)),
                pl.BlockSpec((None, block_size, head_dim), lambda b, i, *_: (b, i, 0)),
            ],
            out_specs=[
                pl.BlockSpec((None, num_heads, head_dim), lambda b, i, *_: (b, 0, 0)),
                pl.BlockSpec((None, num_heads, head_dim), lambda b, i, *_: (b, 0, 0)),
                pl.BlockSpec((None, num_heads, head_dim), lambda b, i, *_: (b, 0, 0)),
            ],
            grid=(batch_size, seq_len // block_size),
        ),
        compiler_params=pltpu.CompilerParams(dimension_semantics=("parallel", "arbitrary")),
        out_shape=[
            jax.ShapeDtypeStruct((batch_size, num_heads, head_dim), jnp.float32),
            jax.ShapeDtypeStruct((batch_size, num_heads, head_dim), jnp.float32),
            jax.ShapeDtypeStruct((batch_size, num_heads, head_dim), jnp.float32),
        ],
        cost_estimate=cost_estimate,
    )(sequence_start, sequence_end, query, key, value)
    return out


@ejit(static_argnames=["fwd_params", "softmax_scale", "logits_soft_cap"])
def inner_decode_tpu(
    query: Float[Array, "batch num_q_heads head_dim"],
    key: Float[Array, "batch seq_len num_kv_heads head_dim"],
    value: Float[Array, "batch seq_len num_kv_heads head_dim"],
    sequence_start: Int[Array, "batch"],
    sequence_end: Int[Array, "batch"],
    softmax_scale: float | None = None,
    fwd_params: FwdParams | None = None,
    sliding_window: tuple[int, int] | None = None,
    logits_soft_cap: float | None = None,
    softmax_aux: Float[Array, "num_kv_heads num_sinks"] | Float[Array, "num_sinks"] | None = None,
) -> chex.Array:
    """JIT-compiled core implementation of ragged MQA Flash Attention for TPU.

    Args:
        query (chex.Array): Query tensor, optionally with leading singleton dimension.
        key (chex.Array): Key tensor of shape [B, S, H, D].
        value (chex.Array): Value tensor of shape [B, S, H, D].
        sequence_start (chex.Array): Sequence start indices.
        sequence_end (chex.Array): Sequence end indices.
        softmax_scale (float | None): Scaling factor for attention logits.
        block_size (int): Block size to tile attention computation.

    Returns:
        chex.Array: Output tensor of shape [B, H, D].
    """

    if softmax_scale is None:
        softmax_scale = query.shape[-1] ** -0.5
    batch_size = query.shape[0]
    num_heads_q = query.shape[-2]
    head_dim = query.shape[-1]
    _, _, num_heads_kv, _ = key.shape
    out_shape = (batch_size, 1, num_heads_q, head_dim)
    if query.ndim == 3:
        query = jnp.expand_dims(query, 1)
        out_shape = (batch_size, num_heads_q, head_dim)
    shape_dtype = (query, key, value, sequence_start, sequence_end)
    cost_estimate = get_mha_cost_estimate(shape_dtype)

    query = query.reshape(batch_size, num_heads_kv, num_heads_q // num_heads_kv, head_dim)
    key = jnp.swapaxes(key, 1, 2)
    value = jnp.swapaxes(value, 1, 2)

    o = jax.vmap(
        functools.partial(
            ragged_decode_mqa,
            block_size=fwd_params.kv_blocksize,
            cost_estimate=cost_estimate,
            softmax_scale=softmax_scale,
        ),
        in_axes=(1, 1, 1, None, None),
        out_axes=1,
    )(query, key, value, sequence_start, sequence_end)

    return jnp.reshape(o, out_shape)
