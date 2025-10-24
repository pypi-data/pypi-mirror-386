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


import jaxtyping
from beartype import beartype
from jaxtyping import Array, Float

from ...._registry import Backend, Platform, kernel_registry
from ._pallas_impl_fwd import ragged_paged_attention as _128_ragged_paged_attention
from ._pallas_impl_fwd_h64 import ragged_paged_attention as _64_ragged_paged_attention


@kernel_registry.register("ragged_page_attention_v3", Platform.PALLAS, Backend.TPU)
@jaxtyping.jaxtyped(typechecker=beartype)
def ragged_page_attention_v3(
    queries: Array,
    keys: Array,
    values: Array,
    kv_cache: Array,
    kv_lens: Array,
    page_indices: Array,
    cu_q_lens: Array,
    distribution: Array,
    *,
    sm_scale: float = 1.0,
    sliding_window: int | None = None,
    soft_cap: float | None = None,
    q_scale: float | None = None,
    k_scale: float | None = None,
    v_scale: float | None = None,
    chunk_prefill_size: int | None = None,
    num_kv_pages_per_block: int | None = None,
    num_queries_per_block: int | None = None,
    vmem_limit_bytes: int | None = None,
) -> Float[Array, "total_tokens num_q_heads head_dim"]:
    """Ragged paged attention that supports mixed prefill and decode.

    Args:
      queries: concatenated all sequences' queries.
      kv_pages: paged KV cache. Normally in HBM.
      context_lens: padded kv lengths. Only the first num_seqs values are valid.
      block_tables: the first index indicates which page to use in the kv cache
        for each sequence. Only the first num_seqs values are valid.
      query_start_loc: the cumulative sum of the effective query lengths. Similar to
        context_lens, only the first num_seqs+1 values are valid.
      num_seqs: the dynamic number of sequences.
      softmax_scale: the softmax softmax_scale which will be applied to the Q@K^T.
      sliding_window: the sliding window size for the attention.
      logits_soft_cap: the logit soft cap for the attention.
      mask_value: mask value for causal mask.
      num_kv_pages_per_block: number of kv pages to be processed in one flash
        attention block in the pallas kernel.
      num_queries_per_block: number of kv pages to be processed in one flash
        attention block in the pallas kernel.
      vmem_limit_bytes: the vmem limit for the pallas kernel.

    Returns:
      The output of the attention.
    """
    del optimized, compute_dtype
    if sm_scale is None:
        sm_scale = queries.shape[-1] ** -0.5
    if queries.shape[-1] == 64:
        return _64_ragged_paged_attention(
            queries,
            keys,
            values,
            kv_cache,
            kv_lens,
            page_indices,
            cu_q_lens,
            distribution,
            sm_scale=sm_scale,
            sliding_window=sliding_window,
            soft_cap=soft_cap,
            q_scale=q_scale,
            k_scale=k_scale,
            v_scale=v_scale,
            chunk_prefill_size=chunk_prefill_size,
            num_kv_pages_per_block=num_kv_pages_per_block,
            num_queries_per_block=num_queries_per_block,
            vmem_limit_bytes=vmem_limit_bytes,
        )
    return _128_ragged_paged_attention(
        queries,
        keys,
        values,
        kv_cache,
        kv_lens,
        page_indices,
        cu_q_lens,
        distribution,
        sm_scale=sm_scale,
        sliding_window=sliding_window,
        soft_cap=soft_cap,
        q_scale=q_scale,
        k_scale=k_scale,
        v_scale=v_scale,
        chunk_prefill_size=chunk_prefill_size,
        num_kv_pages_per_block=num_kv_pages_per_block,
        num_queries_per_block=num_queries_per_block,
        vmem_limit_bytes=vmem_limit_bytes,
    )
