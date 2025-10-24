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


import typing as tp

import chex
import jax
import jax.numpy as jnp
from jax.experimental.pallas import BlockSpec

INTERPRET = False
MIN_BLOCK_SIZE = 128
TRANS_B_DIM_NUMBERS = (((1,), (1,)), ((), ()))
DEFAULT_MASK_VALUE = -0.7 * float(jnp.finfo(jnp.dtype("float32")).max)
NUM_LANES = 128
NUM_SUBLANES = 8


class PatchBlockSpec(BlockSpec):
    def __init__(self, index_map, block_shape):
        super().__init__(block_shape=block_shape, index_map=index_map)


class SegmentIds(tp.NamedTuple):
    """SegmentIds for Q and KV sequences.

    SegmentIds are used to generate segment mask, which prevents attention between
    different segments in the input sequence. Each array is a list of ids
    (integers).
    Only the token with the same id can attend to each other.

    Attributes:
      query: segment ids along the Q sequence.
      kv: segment ids along the KV sequence.
    """

    query: jax.Array
    kv: jax.Array


@chex.dataclass
class BlockSizes:
    block_q: int
    block_k_major: int
    block_k: int
    block_b: int

    block_q_major_dkv: int | None = None
    block_k_major_dkv: int | None = None
    block_k_dkv: int | None = None
    block_q_dkv: int | None = None

    block_k_major_dq: int | None = None
    block_k_dq: int | None = None
    block_q_dq: int | None = None

    def __post_init__(self):
        def verify_major_minor(prefix, suffix, major, minor):
            if minor > major:
                raise ValueError(f"{prefix}{suffix}={minor} should be smaller than {prefix}_major{suffix}={major}")
            if major % minor != 0:
                raise ValueError(f"{prefix}{suffix}={minor} should divide {prefix}_major{suffix}={major}")

        verify_major_minor("block_k", "", self.block_k_major, self.block_k)
        if self.block_q_major_dkv is not None and self.block_q_dkv is not None:
            verify_major_minor("block_q", "_dkv", self.block_q_major_dkv, self.block_q_dkv)
        if self.block_k_major_dkv is not None and self.block_k_dkv is not None:
            verify_major_minor("block_k", "_dkv", self.block_k_major_dkv, self.block_k_dkv)
        if self.block_k_major_dq is not None and self.block_k_dq is not None:
            verify_major_minor("block_k", "_dq", self.block_k_major_dq, self.block_k_dq)

    @property
    def has_backward_blocks(self) -> bool:
        backward_blocks = (
            self.block_q_major_dkv,
            self.block_k_major_dkv,
            self.block_q_dkv,
            self.block_k_dkv,
            self.block_k_major_dq,
            self.block_k_dq,
            self.block_q_dq,
        )
        return all(b is not None for b in backward_blocks)

    @classmethod
    def get_default(cls, batch_size, num_heads, q_seq_len, kv_len, d_model):
        del batch_size, num_heads, q_seq_len, kv_len, d_model
        return BlockSizes(
            block_q=128,
            block_k_major=128,
            block_k=128,
            block_b=1,
            block_q_major_dkv=128,
            block_k_major_dkv=128,
            block_k_dkv=128,
            block_q_dkv=128,
            block_k_major_dq=128,
            block_k_dq=128,
            block_q_dq=128,
        )


def _verify_block(blocksizename, dim_name, block, dim, should_divide=True):
    if block > dim:
        raise ValueError(f"{blocksizename}={block} should be smaller or equal to {dim_name}={dim}")
    if should_divide and dim % block != 0:
        raise ValueError(f"{dim_name}={dim} should be divisible by {blocksizename}={block}")


def below_or_on_diag(
    r: int,
    r_blk_size: int,
    c: int,
    c_blk_size: int,
    causal_block_size: int,
):
    """Checks if the element at (r, c) is below or on the diagonal.

    Args:
            r: Row index.
            r_blk_size: Block size of the row.
            c: Column index.
            c_blk_size: Block size of the column.
            causal_block_size: Size of causal blocks.

    Returns:
            True if the element is below or on the diagonal, False otherwise.
    """
    causal_blocksize_q = max(causal_block_size, r_blk_size)
    causal_blocksize_k = max(causal_block_size, c_blk_size)
    r = jax.lax.div(r, causal_blocksize_q // r_blk_size)
    c = jax.lax.div(c, causal_blocksize_k // c_blk_size)
    return ((r + 1) * causal_blocksize_q - 1) > (c * causal_blocksize_k)


def compute_sliding_window_mask(
    block_q: int,
    block_k: int,
    q_seq_index: int,
    kv_seq_index: int,
    q_chunk_idx_start: int,
    k_chunk_idx_start: int,
    sliding_window: int | tuple[int, int],
    attention_sink_size: int = 0,
):
    """Compute sliding window attention mask.

    Args:
            block_q: Query block size.
            block_k: Key block size.
            q_seq_index: Query sequence index.
            kv_seq_index: Key sequence index.
            q_chunk_idx_start: Query chunk start index.
            k_chunk_idx_start: Key chunk start index.
            sliding_window: Size of sliding window. Can be int or tuple (left_window, right_window).
            attention_sink_size: Number of initial tokens to always attend to.

    Returns:
            Boolean mask of shape (block_q, block_k).
    """

    if isinstance(sliding_window, tuple):
        left_window, right_window = sliding_window
    else:
        left_window = right_window = sliding_window

    mask_shape = (block_q, block_k)
    query_idx = jax.lax.broadcasted_iota(jnp.int32, mask_shape, 0)
    query_idx += q_seq_index * block_q + q_chunk_idx_start * block_q
    key_idx = jax.lax.broadcasted_iota(jnp.int32, mask_shape, 1)
    key_idx += kv_seq_index * block_k + k_chunk_idx_start * block_k

    pos_diff = query_idx - key_idx
    window_mask = (pos_diff >= -right_window) & (pos_diff <= left_window)

    if attention_sink_size > 0:
        sink_mask = key_idx < attention_sink_size
        window_mask = window_mask | sink_mask

    return window_mask
