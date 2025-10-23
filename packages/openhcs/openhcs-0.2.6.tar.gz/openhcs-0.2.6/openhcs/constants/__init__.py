"""
Constants for OpenHCS.

This module exports all constants defined in the constants submodules.
"""

# These imports are re-exported through __all__
from openhcs.constants.constants import (  # Backend constants; Memory constants; I/O constants; Pipeline constants; Default constants
    CPU_MEMORY_TYPES, DEFAULT_ASSEMBLER_LOG_LEVEL, DEFAULT_BACKEND,
    DEFAULT_CPU_THREAD_COUNT, get_default_group_by, get_multiprocessing_axis, DEFAULT_IMAGE_EXTENSION,
    DEFAULT_IMAGE_EXTENSIONS, DEFAULT_INTERPOLATION_MODE,
    DEFAULT_INTERPOLATION_ORDER, DEFAULT_MARGIN_RATIO, DEFAULT_MAX_SHIFT,
    DEFAULT_MICROSCOPE, DEFAULT_NUM_WORKERS, DEFAULT_PIXEL_SIZE,
    DEFAULT_RECURSIVE_PATTERN_SEARCH,
    DEFAULT_SITE_PADDING, DEFAULT_TILE_OVERLAP,
    get_default_variable_components, FORCE_DISK_WRITE,
    GPU_MEMORY_TYPES, MEMORY_TYPE_CUPY, MEMORY_TYPE_JAX, MEMORY_TYPE_NUMPY,
    MEMORY_TYPE_TENSORFLOW, MEMORY_TYPE_TORCH, Microscope, READ_BACKEND,
    REQUIRES_DISK_READ, REQUIRES_DISK_WRITE, SUPPORTED_MEMORY_TYPES,
    VALID_GPU_MEMORY_TYPES, VALID_MEMORY_TYPES, WRITE_BACKEND, Backend,
    AllComponents, GroupBy, MemoryType, VariableComponents, VirtualComponents)

# Backward compatibility and lazy loading using functional approach
__getattr__ = lambda name: {
    'DEFAULT_VARIABLE_COMPONENTS': get_default_variable_components,
    'DEFAULT_GROUP_BY': get_default_group_by,
    'MULTIPROCESSING_AXIS': get_multiprocessing_axis
}.get(name, lambda: (_ for _ in ()).throw(AttributeError(f"module '{__name__}' has no attribute '{name}'")))()
from openhcs.constants.input_source import InputSource

__all__ = [
    # Backends
    'Backend', 'DEFAULT_BACKEND', 'REQUIRES_DISK_READ', 'REQUIRES_DISK_WRITE',
    'FORCE_DISK_WRITE', 'READ_BACKEND', 'WRITE_BACKEND',

    # Memory
    'MemoryType', 'CPU_MEMORY_TYPES', 'GPU_MEMORY_TYPES', 'SUPPORTED_MEMORY_TYPES',
    'MEMORY_TYPE_NUMPY', 'MEMORY_TYPE_CUPY', 'MEMORY_TYPE_TORCH', 'MEMORY_TYPE_TENSORFLOW',
    'MEMORY_TYPE_JAX', 'VALID_MEMORY_TYPES', 'VALID_GPU_MEMORY_TYPES',

    # I/O
    'DEFAULT_IMAGE_EXTENSION', 'DEFAULT_IMAGE_EXTENSIONS', 'DEFAULT_SITE_PADDING',
    'DEFAULT_RECURSIVE_PATTERN_SEARCH', 'DEFAULT_VARIABLE_COMPONENTS', 'DEFAULT_GROUP_BY',
    'AllComponents', 'GroupBy', 'VariableComponents', 'VirtualComponents', 'Microscope', 'DEFAULT_MICROSCOPE', 'MULTIPROCESSING_AXIS',

    # Input Source
    'InputSource',

    # Pipeline
    'DEFAULT_NUM_WORKERS',

    # Defaults
    'DEFAULT_TILE_OVERLAP', 'DEFAULT_MAX_SHIFT', 'DEFAULT_MARGIN_RATIO',
    'DEFAULT_PIXEL_SIZE', 'DEFAULT_ASSEMBLER_LOG_LEVEL',
    'DEFAULT_INTERPOLATION_MODE', 'DEFAULT_INTERPOLATION_ORDER', 'DEFAULT_CPU_THREAD_COUNT'
]
