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


"""Custom VJP implementation for grouped matrix multiplication.

This module defines the custom forward and backward passes for grouped matrix
multiplication operations, enabling efficient automatic differentiation on TPU.
It wraps the low-level kernel implementations with JAX's custom VJP mechanism
to provide gradient support.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp
import jaxtyping
from beartype import beartype
from jaxtyping import Array, DTypeLike, Float, Int

from ...._registry import Backend, Platform, kernel_registry
from ._pallas_impl import LutFn
from ._pallas_impl import grouped_matmul as back_grouped_matmul
from ._pallas_impl import transposed_grouped_matmul as back_tgrouped_matmul

_back_grouped_matmul = jax.custom_vjp(back_grouped_matmul, nondiff_argnums=(3, 4, 7, 8))


def _grouped_matmul_fwd(
    lhs: jnp.ndarray,
    rhs: jnp.ndarray,
    group_sizes: jnp.ndarray,
    preferred_element_type: DTypeLike = jnp.float32,
    tiling: tuple[int, int, int] = (128, 128, 128),
    group_offset: jnp.ndarray | None = None,
    existing_out: jnp.ndarray | None = None,
    transpose_rhs: bool = False,
    interpret: bool = False,
) -> tuple[
    jnp.ndarray,
    tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray | None, int],
]:
    """Forward pass for grouped matrix multiplication with custom VJP.

    Computes the grouped matrix multiplication and saves necessary tensors
    for the backward pass. This function is called during the forward pass
    of automatic differentiation.

    Args:
        lhs: Left-hand side matrix of shape [m, k].
        rhs: Right-hand side tensor of shape [num_groups, k, n] or
            [num_groups, n, k] if transpose_rhs is True.
        group_sizes: Array of group sizes with shape [num_groups], dtype int32.
            Each element specifies the number of rows from lhs for that group.
        preferred_element_type: Output dtype, defaults to float32.
        tiling: Tile dimensions (tm, tk, tn) for kernel execution.
        group_offset: Starting group index for computation (for sharding).
        existing_out: Optional existing output array to accumulate into.
        transpose_rhs: Whether to transpose the last two dimensions of rhs.
        interpret: Whether to run in interpret mode for debugging.

    Returns:
        Tuple of:
            - out: Result of grouped matmul with shape [m, n]
            - residual: Tuple of tensors needed for backward pass
                (lhs, rhs, group_sizes, group_offset, num_groups)
    """
    out = back_grouped_matmul(
        lhs,
        rhs,
        group_sizes,
        preferred_element_type,
        tiling,
        group_offset,
        existing_out,
        transpose_rhs=transpose_rhs,
        interpret=interpret,
    )
    return out, (lhs, rhs, group_sizes, group_offset, rhs.shape[0])


def _grouped_matmul_bwd(
    preferred_element_type: DTypeLike,
    tiling: tuple[int, int, int],
    transpose_rhs: bool,
    interpret: bool,
    residual: tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray | None, int],
    grad: jnp.ndarray,
) -> tuple[jnp.ndarray, jnp.ndarray, None, None, jnp.ndarray]:
    """Backward pass for grouped matrix multiplication with custom VJP.

    Computes gradients with respect to lhs and rhs using the gradient of the
    output and saved tensors from the forward pass. This function is called
    during the backward pass of automatic differentiation.

    Args:
        preferred_element_type: Output dtype (unused in backward).
        tiling: Tile dimensions (tm, tk, tn) for kernel execution.
        transpose_rhs: Whether rhs was transposed in forward pass.
        interpret: Whether to run in interpret mode for debugging.
        residual: Saved tensors from forward pass containing
            (lhs, rhs, group_sizes, group_offset, num_actual_groups).
        grad: Gradient of the loss with respect to the output, shape [m, n].

    Returns:
        Tuple of gradients:
            - grad_lhs: Gradient w.r.t. lhs, shape [m, k]
            - grad_rhs: Gradient w.r.t. rhs, same shape as original rhs
            - None: Placeholder for group_sizes gradient (non-differentiable)
            - None: Placeholder for group_offset gradient (non-differentiable)
            - grad: Pass-through gradient for existing_out
    """

    del preferred_element_type
    lhs, rhs, group_sizes, group_offset, num_actual_groups = residual
    grad_lhs = back_grouped_matmul(
        grad,
        rhs,
        group_sizes,
        lhs[0].dtype,
        tiling,
        group_offset,
        transpose_rhs=not transpose_rhs,
        interpret=interpret,
    )
    grad_rhs = back_tgrouped_matmul(
        lhs.swapaxes(0, 1),
        grad,
        group_sizes,
        rhs.dtype,
        tiling,
        group_offset,
        num_actual_groups,
        interpret=interpret,
    )

    grad_rhs = grad_rhs.swapaxes(1, 2) if transpose_rhs else grad_rhs
    return grad_lhs, grad_rhs, None, None, grad


_back_grouped_matmul.defvjp(_grouped_matmul_fwd, _grouped_matmul_bwd)


@kernel_registry.register("grouped_matmul", Platform.PALLAS, Backend.TPU)
@jaxtyping.jaxtyped(typechecker=beartype)
def grouped_matmul(
    lhs: Float[Array, "m k"],
    rhs: Float[Array, "num_groups k n"] | Float[Array, "num_groups n k"],
    group_sizes: Int[Array, "num_groups"],
    preferred_element_type: DTypeLike = jnp.float32,
    tiling: tuple[int, int, int] | LutFn | None = (128, 128, 128),
    group_offset: Int[Array, "..."] | None = None,
    existing_out: Float[Array, "m n"] | None = None,
    transpose_rhs: bool = False,
    interpret: bool = False,
    precision: jax.lax.PrecisionLike = jax.lax.Precision.DEFAULT,
) -> Float[Array, "m n"]:
    """Grouped Matrix Multiplication: Compute separate matrix products for each group.

    This function performs grouped matrix multiplication where different row slices of
    the left-hand side matrix are multiplied with different matrices from the right-hand
    side tensor. Mathematically, for each group i:
        out[start_i:end_i, :] = lhs[start_i:end_i, :] @ rhs[i, :, :]
    where start_i and end_i are determined by group_sizes.

    The implementation uses Pallas to generate efficient TPU kernels that:
    - Process multiple groups in a single kernel launch
    - Handle groups that don't align with tile boundaries
    - Support incremental accumulation for memory efficiency
    - Optimize memory access patterns for TPU's memory hierarchy

    Args:
        lhs: Left-hand side matrix of shape [m, k] where m is the total number
            of rows across all groups and k is the inner dimension.
        rhs: Right-hand side tensor of shape [num_groups, k, n] containing a
            separate matrix for each group. Can be transposed if transpose_rhs=True.
        group_sizes: 1D array of shape [num_groups] with int32 dtype. Each element
            specifies the number of rows in lhs belonging to that group.
            Must sum to m (first dimension of lhs).
        preferred_element_type: Output dtype. Defaults to float32. The kernel uses
            float32 for accumulation regardless, then casts to this type.
        tiling: Tile sizes as (tm, tk, tn) tuple, or a callable that returns tile
            sizes based on problem dimensions. Typical TPU tiles are 128x128.
            The callable signature is (m, k, n) -> (tm, tk, tn) | None.
        group_offset: Starting group index for sharded execution. Defaults to 0.
            Useful when distributing groups across multiple devices.
        existing_out: Optional pre-existing output tensor to accumulate into.
            Must have shape [m, n] and dtype matching preferred_element_type.
            Enables incremental computation and memory reuse.
        transpose_rhs: If True, expects rhs shape [num_groups, n, k] and transposes
            during multiplication. Useful for certain memory layouts.
        interpret: Run kernel in interpret mode for debugging. Slower but provides
            better error messages and doesn't require compilation.

    Returns:
        Output matrix of shape [m, n] containing the concatenated results of all
        group matrix multiplications.

    Algorithm Overview:
        1. Validate inputs and determine computation parameters
        2. Create group metadata for efficient tile-to-group mapping
        3. Define Pallas kernel that:
           - Loads tiles from lhs and group-specific slices from rhs
           - Accumulates partial products in on-chip memory
           - Masks and stores results respecting group boundaries
        4. Launch kernel with appropriate grid dimensions
        5. Zero unprocessed regions if doing partial computation

    TPU Optimizations:
        - Tiles sized to match TPU's Matrix Multiply Units (typically 128x128)
        - Prefetch scheduling for hiding memory latency
        - VMEM scratch space for accumulation to minimize HBM traffic
        - Efficient masking for partial tiles using TPU's predication
        - Dimension semantics hints for XLA compiler optimization

    Example:
        >>>
        >>> lhs = jnp.randn(300, 64)
        >>> rhs = jnp.randn(3, 64, 32)
        >>> group_sizes = jnp.array([100, 150, 50], dtype=jnp.int32)
        >>> result = grouped_matmul(lhs, rhs, group_sizes)

    Notes:
        - The k dimension can have partial tiles (handled via masking)
        - The m dimension must be divisible by tm for correctness
        - Empty groups (size 0) are skipped for efficiency
        - Cost estimation helps XLA make scheduling decisions
    """
    return _back_grouped_matmul(
        lhs=lhs,
        rhs=rhs,
        group_sizes=group_sizes,
        preferred_element_type=preferred_element_type,
        tiling=tiling if tiling is not None else (128, 128, 128),
        group_offset=group_offset,
        existing_out=existing_out,
        transpose_rhs=transpose_rhs,
        interpret=interpret,
    )
