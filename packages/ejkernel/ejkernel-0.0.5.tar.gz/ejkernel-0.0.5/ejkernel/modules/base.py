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


"""Base configuration for kernel modules.

Provides shared configuration infrastructure for kernel execution,
but does NOT provide a base Kernel class. Each kernel module should
implement its own custom Kernel subclass tailored to its specific needs.

Note:
    The ``create_default_executor()`` function is deprecated. Use
    ``Executor(ConfigSelectorChain(...))`` directly instead. See the
    function documentation for migration examples.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import jax

from ejkernel.ops import (
    ConfigCache,
    ConfigSelectorChain,
    Executor,
    PersistentCache,
)

from ..kernels._registry import Backend, Platform, kernel_registry


def detect_platform(
    algorithm: str,
    platform: Platform | Literal["triton", "pallas", "cuda", "xla", "auto"] | None = "auto",
    maybe_pallas: bool = False,
) -> Platform:
    """Detect the best platform for a given algorithm.

    Automatically selects the optimal platform based on:
        1. Explicit platform request (if provided)
        2. Available implementations for the algorithm
        3. Current JAX backend (GPU/TPU/CPU)
        4. Platform-specific optimizations

    The selection priority:
        - GPU backend + Triton available -> Triton (best GPU performance)
        - GPU backend + no Triton -> XLA
        - TPU backend -> Pallas (TPU-optimized) or XLA fallback
        - CPU backend -> XLA

    Args:
        algorithm: The algorithm name to check for availability (e.g., "flash_attention")
        platform: Requested platform. Options:
            - "triton": Triton GPU kernels (CUDA/ROCm)
            - "pallas": Pallas kernels (TPU/GPU)
            - "cuda": CUDA-specific implementations
            - "xla": XLA compiler-based implementations
            - "auto" or None: Automatic selection (default)

    Returns:
        The selected Platform enum value

    Raises:
        ValueError: If the requested platform is not available for the algorithm

    Example:
        >>>
        >>> platform = detect_platform("flash_attention", platform="auto")
        >>>
        >>>
        >>> platform = detect_platform("flash_attention", platform="triton")
        >>>
        >>>
        >>> print(f"Selected: {detect_platform('ring_attention')}")

    Note:
        Triton is preferred on NVIDIA GPUs for best performance, but XLA provides
        broader compatibility across hardware backends.
    """
    if platform not in ("auto", None):
        return Platform(platform) if isinstance(platform, str) else platform

    try:
        jax_backend = jax.default_backend()
    except Exception:
        jax_backend = "cpu"

    specs = kernel_registry.list_implementations(algorithm)
    has_triton = any(spec.platform == Platform.TRITON for spec in specs)
    has_pallas = any(spec.platform == Platform.PALLAS for spec in specs)

    if has_pallas and jax_backend in ("gpu") and maybe_pallas:
        return Platform.PALLAS

    if has_triton and jax_backend in ("gpu", "cuda"):
        return Platform.TRITON

    return Platform.XLA


@dataclass
class KernelConfig:
    """Configuration for kernel execution with block size tuning.

    This is a shared configuration class that can be used by all kernel modules
    to specify block sizes for autotuning and performance optimization.

    Attributes:
        block_q: Query block size for tiling
        block_k: Key/value block size for tiling
        block_d: Head dimension block size (if applicable)
        num_warps: Number of warps for GPU kernels
        num_stages: Number of pipeline stages for overlapping compute/memory
        platform: Implementation platform (triton, pallas, cuda, xla, auto)
        backend: Target hardware backend (gpu, tpu, cpu, any)
        algorithm: Specific algorithm variant if multiple exist
        priority: Selection priority when multiple configs match
    """

    block_q: int = 128
    block_k: int = 128
    block_d: int = 64
    num_warps: int = 4
    num_stages: int = 2
    platform: Platform | Literal["triton", "pallas", "cuda", "xla", "auto"] = "auto"
    backend: Backend | Literal["gpu", "tpu", "cpu", "any"] = Backend.ANY
    algorithm: str | None = None
    priority: int = 0

    def __post_init__(self):
        if self.platform == "xla":
            self.backend = "any"


def create_default_executor(
    persistent_cache_path: str | None = None,
    enable_autotuning: bool = True,
    warmup_iterations: int = 2,
    timing_iterations: int = 5,
) -> Executor[KernelConfig, jax.Array | tuple[jax.Array, jax.Array]]:
    """Create a default executor with standard configuration.

    .. deprecated::
        Use ``Executor(ConfigSelectorChain(...))`` directly instead of ``create_default_executor()``.
        This function will be removed in a future version.

    Sets up an executor with in-memory and optional persistent caching,
    and autotuning enabled by default.

    Args:
        persistent_cache_path: Optional path for persistent cache storage.
            If None, only in-memory caching is used.
        enable_autotuning: Whether to enable automatic performance tuning.
            When enabled, the executor will benchmark different implementations.
        warmup_iterations: Number of warmup runs before timing measurements
        timing_iterations: Number of timing iterations to average over

    Returns:
        Configured Executor instance ready for kernel execution

    Example:
        >>>
        >>>
        >>> executor = create_default_executor("/tmp/kernel_cache")
        >>>
        >>>
        >>> from ejkernel.ops import Executor, ConfigSelectorChain, ConfigCache, AutotunePolicy, Tuner, PersistentCache
        >>> executor = Executor(
        ...     ConfigSelectorChain(
        ...         cache=ConfigCache(),
        ...         policy=AutotunePolicy(allow_autotune=True),
        ...         tuner=Tuner(warmup=2, iters=5),
        ...         persistent=PersistentCache("/tmp/kernel_cache")
        ...     )
        ... )
        >>>
        >>> from ejkernel.modules import FlashAttention
        >>> attn = FlashAttention()
        >>> output = executor(attn, q, k, v, causal=True)
    """
    import warnings

    warnings.warn(
        "create_default_executor() is deprecated. "
        "Use Executor(ConfigSelectorChain(...)) directly instead. "
        "See the documentation for migration examples.",
        DeprecationWarning,
        stacklevel=2,
    )

    from ejkernel.ops import AutotunePolicy, Tuner

    return Executor[KernelConfig, jax.Array | tuple[jax.Array, jax.Array]](
        ConfigSelectorChain(
            cache=ConfigCache(),
            policy=AutotunePolicy(allow_autotune=enable_autotuning),
            tuner=Tuner(warmup=warmup_iterations, iters=timing_iterations),
            persistent=PersistentCache(persistent_cache_path) if persistent_cache_path else None,
        )
    )
