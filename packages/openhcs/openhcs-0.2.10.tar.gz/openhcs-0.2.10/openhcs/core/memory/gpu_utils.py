"""
GPU utility functions for OpenHCS.

This module provides utility functions for checking GPU availability
across different frameworks (cupy, torch, tensorflow, jax).

Doctrinal Clauses:
- Clause 88 — No Inferred Capabilities
- Clause 293 — GPU Pre-Declaration Enforcement
"""

import logging
import os
from typing import Optional

from openhcs.core.utils import optional_import

logger = logging.getLogger(__name__)


def check_cupy_gpu_available() -> Optional[int]:
    """
    Check if cupy is available and can access a GPU.

    Returns:
        GPU device ID if available, None otherwise
    """
    # Skip GPU checks in subprocess runner mode
    if os.getenv('OPENHCS_SUBPROCESS_NO_GPU') == '1':
        logger.debug("Subprocess runner mode - skipping cupy GPU check")
        return None

    cp = optional_import("cupy")
    if cp is None:
        logger.debug("Cupy not installed")
        return None

    try:
        # Check if cupy is available and can access a GPU
        if cp.cuda.is_available():
            # Get the current device ID
            device_id = cp.cuda.get_device_id()
            logger.debug("Cupy GPU available: device_id=%s", device_id)
            return device_id
        else:
            logger.debug("Cupy CUDA not available")
            return None
    except Exception as e:
        logger.debug("Error checking cupy GPU availability: %s", e)
        return None


def check_torch_gpu_available() -> Optional[int]:
    """
    Check if torch is available and can access a GPU.

    Returns:
        GPU device ID if available, None otherwise
    """
    # Skip GPU checks in subprocess runner mode
    if os.getenv('OPENHCS_SUBPROCESS_NO_GPU') == '1':
        logger.debug("Subprocess runner mode - skipping torch GPU check")
        return None

    torch = optional_import("torch")
    if torch is None:
        logger.debug("Torch not installed")
        return None

    try:
        # Check if torch is available and can access a GPU
        if torch.cuda.is_available():
            # Get the current device ID
            device_id = torch.cuda.current_device()
            logger.debug("Torch GPU available: device_id=%s", device_id)
            return device_id
        else:
            logger.debug("Torch CUDA not available")
            return None
    except Exception as e:
        logger.debug("Error checking torch GPU availability: %s", e)
        return None


def check_tf_gpu_available() -> Optional[int]:
    """
    Check if tensorflow is available and can access a GPU.

    Returns:
        GPU device ID if available, None otherwise
    """
    # Skip GPU checks in subprocess runner mode
    if os.getenv('OPENHCS_SUBPROCESS_NO_GPU') == '1':
        logger.debug("Subprocess runner mode - skipping tensorflow GPU check")
        return None

    tf = optional_import("tensorflow")
    if tf is None:
        logger.debug("TensorFlow not installed")
        return None

    try:
        # Check if tensorflow is available and can access a GPU
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            # Get the first GPU device ID
            # TensorFlow doesn't have a direct way to get the CUDA device ID,
            # so we'll just use the index in the list
            device_id = 0
            logger.debug("TensorFlow GPU available: device_id=%s", device_id)
            return device_id
        else:
            logger.debug("TensorFlow GPU not available")
            return None
    except Exception as e:
        logger.debug("Error checking TensorFlow GPU availability: %s", e)
        return None


def check_jax_gpu_available() -> Optional[int]:
    """
    Check if JAX is available and can access a GPU.

    Returns:
        GPU device ID if available, None otherwise
    """
    # Skip GPU checks in subprocess runner mode
    if os.getenv('OPENHCS_SUBPROCESS_NO_GPU') == '1':
        logger.debug("Subprocess runner mode - skipping JAX GPU check")
        return None

    jax = optional_import("jax")
    if jax is None:
        logger.debug("JAX not installed")
        return None

    try:
        # Check if JAX is available and can access a GPU
        devices = jax.devices()
        gpu_devices = [d for d in devices if d.platform == 'gpu']

        if gpu_devices:
            # Get the first GPU device ID
            # JAX device IDs are typically in the form 'gpu:0'
            device_str = str(gpu_devices[0])
            if ':' in device_str:
                device_id = int(device_str.split(':')[-1])
            else:
                # Default to 0 if we can't parse the device ID
                device_id = 0
            logger.debug("JAX GPU available: device_id=%s", device_id)
            return device_id
        else:
            logger.debug("JAX GPU not available")
            return None
    except Exception as e:
        logger.debug("Error checking JAX GPU availability: %s", e)
        return None
