"""
GPU scheduler registry for OpenHCS.

This module provides a thread-safe registry for GPU assignment during
multi-pipeline execution, enforcing maximum concurrency limits per GPU
and ensuring deterministic GPU assignment without runtime fallbacks.

The GPU registry is a global singleton that must be initialized exactly once
during application startup, before any pipeline threads are created. It is
shared across all threads to ensure consistent GPU resource management.

Thread Safety:
    All functions in this module are thread-safe and use a lock to ensure
    consistent access to the global registry.

Doctrinal Clauses:
- Clause 12 — Absolute Clean Execution
- Clause 88 — No Inferred Capabilities
- Clause 293 — Predeclared GPU Availability
- Clause 295 — GPU Scheduling Affinity
"""

import logging
import math
import os
import threading
from typing import Dict, List, Optional

# DEFAULT_NUM_WORKERS removed
from openhcs.core.memory.gpu_utils import (check_cupy_gpu_available,
                                               check_tf_gpu_available,
                                               check_torch_gpu_available)
# Import necessary config classes
from openhcs.core.config import GlobalPipelineConfig


logger = logging.getLogger(__name__) # Ensure logger is consistently named if used across module

# Thread-safe lock for GPU registry access
_registry_lock = threading.Lock()

# GPU registry singleton
# Structure: {gpu_id: {"max_pipelines": int}}
# Simplified: removed unused "active" count since no runtime coordination exists
GPU_REGISTRY: Dict[int, Dict[str, int]] = {}

# Flag to track if the registry has been initialized
_registry_initialized = False


def initialize_gpu_registry(configured_num_workers: int) -> None:
    """
    Initialize the GPU registry based on available GPUs and configured number of workers.

    This function detects available GPUs, calculates the maximum number of
    concurrent pipelines per GPU (influenced by `configured_num_workers`),
    and initializes the GPU registry.

    Args:
        configured_num_workers (int): The number of workers specified in the
                                      global configuration, used as a fallback
                                      if os.cpu_count() is not available or to
                                      influence pipelines per GPU.

    Must be called exactly once during application startup, before any
    pipeline threads are created. The registry is a global singleton
    shared across all threads.

    Thread-safe: Uses a lock to ensure consistent access to the global registry.

    Raises:
        RuntimeError: If no GPUs are available or if the registry is already initialized.
    """
    global GPU_REGISTRY, _registry_initialized

    with _registry_lock:
        # Check if registry is already initialized
        if _registry_initialized:
            raise RuntimeError(
                "Clause 295 Violation: GPU registry already initialized. "
                "Cannot reinitialize during execution."
            )

        # Detect available GPUs
        available_gpus = _detect_available_gpus()
        logger.info(f"Detected GPUs: {available_gpus}")

        if not available_gpus:
            logger.warning("No GPUs detected. GPU memory types will not be available.")
            _registry_initialized = True
            GPU_REGISTRY.clear()
            return

        # Get maximum CPU threads (use CPU count as a proxy, fallback to configured_num_workers)
        max_cpu_threads = os.cpu_count() or configured_num_workers
        if max_cpu_threads <= 0: # Ensure positive
            max_cpu_threads = 1


        # Calculate maximum pipelines per GPU
        max_pipelines_per_gpu = math.ceil(max_cpu_threads / len(available_gpus))

        # Initialize registry
        GPU_REGISTRY.clear()
        for gpu_id in available_gpus:
            GPU_REGISTRY[gpu_id] = {"max_pipelines": max_pipelines_per_gpu}

        logger.info(
            "GPU registry initialized with %s GPUs. Maximum %s pipelines per GPU.",
            len(available_gpus), max_pipelines_per_gpu
        )

        # Mark registry as initialized
        _registry_initialized = True


def _detect_available_gpus() -> List[int]:
    """
    Detect available GPUs across all supported frameworks.

    Returns:
        List of available GPU IDs
    """
    available_gpus = set()

    # Check cupy GPUs
    try:
        cupy_gpu = check_cupy_gpu_available()
        if cupy_gpu is not None:
            available_gpus.add(cupy_gpu)
    except Exception as e:
        logger.debug("Cupy GPU detection failed: %s", e)

    # Check torch GPUs
    try:
        torch_gpu = check_torch_gpu_available()
        if torch_gpu is not None:
            available_gpus.add(torch_gpu)
    except Exception as e:
        logger.debug("Torch GPU detection failed: %s", e)

    # Check tensorflow GPUs
    try:
        tf_gpu = check_tf_gpu_available()
        if tf_gpu is not None:
            available_gpus.add(tf_gpu)
    except Exception as e:
        logger.debug("TensorFlow GPU detection failed: %s", e)

    # Skip JAX GPU detection to prevent thread explosion
    # JAX creates 54+ threads during jax.devices() call
    # JAX GPU detection will be done lazily only when JAX functions are actually used
    # TODO: Add JAX GPU detection back when we have proper lazy initialization
    logger.debug("Skipping JAX GPU detection to prevent thread explosion")

    return sorted(list(available_gpus))


# NOTE: acquire_gpu_slot() and release_gpu_slot() functions removed
# These were orphaned code that was never actually called in the execution path.
# GPU assignment happens at compilation time via GPUMemoryTypeValidator, not at runtime.


def get_gpu_registry_status() -> Dict[int, Dict[str, int]]:
    """
    Get the current status of the GPU registry.

    Thread-safe: Uses a lock to ensure consistent access to the global registry.

    Returns:
        Copy of the GPU registry

    Raises:
        RuntimeError: If the GPU registry is not initialized
    """

    with _registry_lock:
        # Check if registry is initialized
        if not _registry_initialized:
            raise RuntimeError(
                "Clause 295 Violation: GPU registry not initialized. "
                "Must call initialize_gpu_registry() first."
            )

        # Return a copy of the registry to prevent external modification
        return {gpu_id: info.copy() for gpu_id, info in GPU_REGISTRY.items()}


def is_gpu_registry_initialized() -> bool:
    """
    Check if the GPU registry has been initialized.

    Thread-safe: Uses a lock to ensure consistent access to the initialization flag.

    Returns:
        True if the registry is initialized, False otherwise
    """
    with _registry_lock:
        return _registry_initialized


def setup_global_gpu_registry(global_config: Optional[GlobalPipelineConfig] = None) -> None:
    """
    Initializes the global GPU registry using the provided or default global configuration.

    This function should be called once at application startup. It ensures that the
    GPU registry is initialized with worker configurations derived from the
    GlobalPipelineConfig.

    Args:
        global_config (Optional[GlobalPipelineConfig]): An optional pre-loaded global
            configuration object. If None, the default global configuration will be used.
    """
    # Use the existing thread-safe check from is_gpu_registry_initialized()
    # but need to acquire lock to make the check-and-set atomic if we were to set _registry_initialized here.
    # However, initialize_gpu_registry itself is internally locked and handles the _registry_initialized flag.
    
    if is_gpu_registry_initialized():
        logger.info("GPU registry is already initialized. Skipping setup.")
        return

    config_to_use: GlobalPipelineConfig
    if global_config is None:
        logger.info("No global_config provided to setup_global_gpu_registry, using default configuration.")
        config_to_use = GlobalPipelineConfig()
    else:
        config_to_use = global_config
    
    # initialize_gpu_registry is already designed to be called once and is thread-safe.
    # FAIL LOUD: No try-except - let exceptions bubble up to caller
    initialize_gpu_registry(configured_num_workers=config_to_use.num_workers)
    logger.info("Global GPU registry setup complete via setup_global_gpu_registry.")
