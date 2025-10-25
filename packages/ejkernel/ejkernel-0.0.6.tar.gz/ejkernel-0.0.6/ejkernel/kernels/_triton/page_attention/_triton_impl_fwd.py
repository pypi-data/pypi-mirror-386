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


import triton
import triton.language as tl


def get_autotune_configs():
    """Generate dimension-aware autotune configurations for paged attention."""
    configs = []

    configs.extend(
        [
            triton.Config({}, num_warps=2, num_stages=4),
            triton.Config({}, num_warps=4, num_stages=3),
            triton.Config({}, num_warps=4, num_stages=4),
        ]
    )

    configs.extend(
        [
            triton.Config({}, num_warps=8, num_stages=2),
            triton.Config({}, num_warps=8, num_stages=3),
            triton.Config({}, num_warps=8, num_stages=4),
        ]
    )

    configs.extend(
        [
            triton.Config({}, num_warps=16, num_stages=2),
            triton.Config({}, num_warps=16, num_stages=3),
            triton.Config({}, num_warps=16, num_stages=4),
        ]
    )

    return configs


@triton.jit
def _paged_attn_kernel(
    q_ptr,
    k_cache_ptr,
    v_cache_ptr,
    context_lens_ptr,
    block_tables_ptr,
    m_i_ptr,
    l_i_ptr,
    out_ptr,
    attn_scale,
    stride_bt0,
    stride_bt1,
    stride_q0,
    stride_q1,
    stride_q2,
    stride_kv0,
    stride_kv1,
    stride_kv2,
    stride_kv3,
    stride_o0,
    stride_o1,
    stride_o2,
    stride_o3,
    stride_o4,
    HEAD_SIZE: tl.constexpr,
    QUERY_GROUP_SIZE: tl.constexpr,
    PADDED_QUERY_GROUP_SIZE: tl.constexpr,
    NUM_KV_HEADS: tl.constexpr,
    KV_BLOCK_SIZE: tl.constexpr,
    PARTITION_SIZE: tl.constexpr,
):
    seq_idx = tl.program_id(0)
    kv_head_idx = tl.program_id(1)
    part_idx = tl.program_id(2)
    max_num_partitions = tl.num_programs(2)

    log2e: tl.constexpr = 1.4426950408889634

    USE_PARTITIONING = PARTITION_SIZE > 0
    context_len = tl.load(context_lens_ptr + seq_idx).to(tl.int32)
    if USE_PARTITIONING:
        context_start_idx = part_idx * PARTITION_SIZE
        if context_start_idx >= context_len:
            return
        context_end_idx = tl.minimum(context_start_idx + PARTITION_SIZE, context_len)
        context_range = context_end_idx - context_start_idx
        num_blocks = (context_range + KV_BLOCK_SIZE - 1) // KV_BLOCK_SIZE
    else:
        num_blocks = (context_len + KV_BLOCK_SIZE - 1) // KV_BLOCK_SIZE

    block_offset = tl.arange(0, KV_BLOCK_SIZE)
    head_offset = tl.arange(0, HEAD_SIZE)
    padding_group_offset = tl.arange(0, PADDED_QUERY_GROUP_SIZE)

    kv_offset = kv_head_idx * stride_kv1 + block_offset[:, None] * stride_kv2 + head_offset[None, :] * stride_kv3

    q_offset = (
        seq_idx * stride_q0
        + (kv_head_idx * QUERY_GROUP_SIZE + padding_group_offset[:, None]) * stride_q1
        + head_offset[None, :] * stride_q2
    )
    group_mask = padding_group_offset[:, None] < QUERY_GROUP_SIZE

    q = tl.load(q_ptr + q_offset, mask=group_mask, other=0.0)

    m_i = tl.zeros([PADDED_QUERY_GROUP_SIZE], dtype=tl.float32) - float("inf")
    l_i = tl.zeros([PADDED_QUERY_GROUP_SIZE], dtype=tl.float32)
    acc = tl.zeros([PADDED_QUERY_GROUP_SIZE, HEAD_SIZE], dtype=tl.float32)

    if USE_PARTITIONING:
        num_prev_blocks = part_idx * (PARTITION_SIZE // KV_BLOCK_SIZE)
    else:
        num_prev_blocks = 0
    for i in range(num_blocks):
        block_idx = num_prev_blocks + i
        block_number = tl.load(block_tables_ptr + seq_idx * stride_bt0 + block_idx * stride_bt1)

        kv_block_offset = block_number * stride_kv0 + kv_offset
        mask_offset = block_idx * KV_BLOCK_SIZE + block_offset
        kv_mask = mask_offset[:, None] < context_len

        k = tl.load(k_cache_ptr + kv_block_offset, mask=kv_mask, other=0.0)

        if PADDED_QUERY_GROUP_SIZE == 1:
            qk = tl.sum(q[:, None, :] * k[None, :, :], axis=2)
        else:
            qk = tl.dot(q, k.T, out_dtype=tl.float32)

        qk *= attn_scale
        qk = tl.where(mask_offset < context_len, qk, float("-inf"))

        m_i_new = tl.maximum(m_i, tl.max(qk, axis=1))

        p = tl.math.exp2((qk - m_i_new[:, None]) * log2e)
        alpha = tl.math.exp2((m_i - m_i_new) * log2e)
        acc *= alpha[:, None]

        v = tl.load(v_cache_ptr + kv_block_offset, mask=kv_mask, other=0.0)

        if PADDED_QUERY_GROUP_SIZE == 1:
            acc += tl.sum(p.T[:, :, None] * v[:, None, :], axis=0)
        else:
            p = p.to(v.dtype)
            acc += tl.dot(p, v, out_dtype=tl.float32)

        l_i = l_i * alpha + tl.sum(p, axis=1)
        m_i = m_i_new
    acc = acc / l_i[:, None]

    if USE_PARTITIONING:
        part_offset = (
            (seq_idx * NUM_KV_HEADS + kv_head_idx) * max_num_partitions * QUERY_GROUP_SIZE
            + part_idx * QUERY_GROUP_SIZE
            + padding_group_offset
        )
        mask = padding_group_offset < QUERY_GROUP_SIZE
        tl.store(m_i_ptr + part_offset, m_i, mask=mask)
        tl.store(l_i_ptr + part_offset, l_i, mask=mask)

    out_offset = seq_idx * stride_o0
    if USE_PARTITIONING:
        out_offset += kv_head_idx * stride_o1
    else:
        out_offset += kv_head_idx * QUERY_GROUP_SIZE * stride_o1
    out_offset += part_idx * stride_o2 + padding_group_offset[:, None] * stride_o3 + head_offset[None, :] * stride_o4

    group_mask = padding_group_offset[:, None] < QUERY_GROUP_SIZE
    tl.store(out_ptr + out_offset, acc, mask=group_mask)


try:
    _paged_attn_kernel = triton.autotune(
        configs=get_autotune_configs(),
        key=["HEAD_SIZE", "QUERY_GROUP_SIZE", "KV_BLOCK_SIZE", "PARTITION_SIZE"],
    )(_paged_attn_kernel)
except Exception:
    pass


@triton.jit
def _paged_attn_v2_reduce_kernel(
    m_i_ptr,
    l_i_ptr,
    tmp_out_ptr,
    context_lens_ptr,
    out_ptr,
    max_num_partitions,
    stride_o0,
    stride_o1,
    stride_o2,
    HEAD_SIZE: tl.constexpr,
    QUERY_GROUP_SIZE: tl.constexpr,
    NUM_KV_HEADS: tl.constexpr,
    PARTITION_SIZE: tl.constexpr,
    NUM_PARTITIONS: tl.constexpr,
):
    seq_idx = tl.program_id(0)
    kv_head_idx = tl.program_id(1)

    context_len = tl.load(context_lens_ptr + seq_idx)

    num_partitions = (context_len + PARTITION_SIZE - 1) // PARTITION_SIZE
    group_head_offset = tl.arange(0, QUERY_GROUP_SIZE)[:, None] * HEAD_SIZE + tl.arange(0, HEAD_SIZE)[None, :]
    if num_partitions == 1:
        tmp_out_offset = (
            seq_idx * NUM_KV_HEADS + kv_head_idx
        ) * max_num_partitions * QUERY_GROUP_SIZE * HEAD_SIZE + group_head_offset
        tmp_out = tl.load(tmp_out_ptr + tmp_out_offset)

        out_offset = seq_idx * stride_o0 + kv_head_idx * QUERY_GROUP_SIZE * stride_o1 + group_head_offset * stride_o2
        tl.store(out_ptr + out_offset, tmp_out)
        return

    ml_offset = (
        (seq_idx * NUM_KV_HEADS + kv_head_idx) * max_num_partitions * QUERY_GROUP_SIZE
        + tl.arange(0, NUM_PARTITIONS)[:, None] * QUERY_GROUP_SIZE
        + tl.arange(0, QUERY_GROUP_SIZE)[None, :]
    )

    mask = tl.arange(0, NUM_PARTITIONS)[:, None] < num_partitions

    m_i = tl.load(m_i_ptr + ml_offset, mask=mask, other=float("-inf"))

    m = tl.max(m_i, axis=0)

    l_i = tl.load(l_i_ptr + ml_offset, mask=mask, other=0.0)
    l_i *= tl.exp(m_i - m[None, :])

    l = tl.sum(l_i, axis=0)

    r = l_i / l[None, :]
    r = tl.reshape(r, (NUM_PARTITIONS, QUERY_GROUP_SIZE, 1))

    tmp_out_offset = (
        (seq_idx * NUM_KV_HEADS + kv_head_idx) * max_num_partitions * QUERY_GROUP_SIZE * HEAD_SIZE
        + tl.arange(0, NUM_PARTITIONS)[:, None, None] * QUERY_GROUP_SIZE * HEAD_SIZE
        + tl.arange(0, QUERY_GROUP_SIZE)[None, :, None] * HEAD_SIZE
        + tl.arange(0, HEAD_SIZE)[None, None, :]
    )

    tmp_out = tl.load(tmp_out_ptr + tmp_out_offset, mask=mask[:, :, None], other=0.0)

    out = tl.sum((tmp_out * r).to(tl.float32), axis=0)

    out_offset = seq_idx * stride_o0 + kv_head_idx * QUERY_GROUP_SIZE * stride_o1 + group_head_offset * stride_o2
    tl.store(out_ptr + out_offset, out)
