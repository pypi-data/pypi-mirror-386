"""
Function registry for processing backends.

This module provides a registry for functions that can be executed by different
processing backends (numpy, cupy, torch, etc.). It automatically scans the
processing directory to register functions with matching input and output
memory types.

The function registry is a global singleton that is initialized during application
startup and shared across all components.

Valid memory types:
- numpy
- cupy
- torch
- tensorflow
- jax

Thread Safety:
    All functions in this module are thread-safe and use a lock to ensure
    consistent access to the global registry.
"""
from __future__ import annotations 

import importlib
import inspect
import logging
import os
import pkgutil
import sys
import threading
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Thread-safe lock for registry access
_registry_lock = threading.Lock()

# Import hook system for auto-decorating external libraries
_original_import = __builtins__['__import__']
_decoration_applied = set()
_import_hook_installed = False

# Global registry of functions by backend type
# Structure: {backend_name: [function1, function2, ...]}
FUNC_REGISTRY: Dict[str, List[Callable]] = {}

# Valid memory types
VALID_MEMORY_TYPES = {"numpy", "cupy", "torch", "tensorflow", "jax", "pyclesperanto"}

# CPU-only memory types (for CI/testing without GPU)
CPU_ONLY_MEMORY_TYPES = {"numpy"}

# Check if CPU-only mode is enabled
CPU_ONLY_MODE = os.getenv('OPENHCS_CPU_ONLY', 'false').lower() == 'true'

# Flag to track if the registry has been initialized
_registry_initialized = False

# Flag to track if we're currently in the initialization process (prevent recursion)
_registry_initializing = False


# Import hook system removed - using existing comprehensive registries with clean decoration


# Import hook decoration functions removed - using existing registries


def _create_virtual_modules() -> None:
    """Create virtual modules that mirror external library structure under openhcs namespace."""
    import types
    from openhcs.processing.backends.lib_registry.registry_service import RegistryService

    # Get all registered functions
    all_functions = RegistryService.get_all_functions_with_metadata()

    # Group functions by their full module path
    functions_by_module = {}
    for composite_key, metadata in all_functions.items():
        # Only create virtual modules for external library functions with slice_by_slice
        if (hasattr(metadata.func, 'slice_by_slice') and
            not hasattr(metadata.func, '__processing_contract__') and
            not metadata.func.__module__.startswith('openhcs.')):

            original_module = metadata.func.__module__
            virtual_module = f'openhcs.{original_module}'
            if virtual_module not in functions_by_module:
                functions_by_module[virtual_module] = {}
            functions_by_module[virtual_module][metadata.func.__name__] = metadata.func

    # Create virtual modules for each module path
    created_modules = []
    all_virtual_modules = set()

    # First, collect all module paths including intermediate ones
    for virtual_module in functions_by_module.keys():
        parts = virtual_module.split('.')
        for i in range(2, len(parts) + 1):  # Start from 'openhcs.xxx'
            intermediate_module = '.'.join(parts[:i])
            all_virtual_modules.add(intermediate_module)

    # Create intermediate modules first (in order)
    for virtual_module in sorted(all_virtual_modules):
        if virtual_module not in sys.modules:
            module = types.ModuleType(virtual_module)
            module.__doc__ = f"Virtual module mirroring {virtual_module.replace('openhcs.', '')} with OpenHCS decorations"
            sys.modules[virtual_module] = module
            created_modules.append(virtual_module)

    # Then add functions to the leaf modules
    for virtual_module, functions in functions_by_module.items():
        if virtual_module in sys.modules:
            module = sys.modules[virtual_module]
            # Add all functions from this module
            for func_name, func in functions.items():
                setattr(module, func_name, func)

    if created_modules:
        logger.info(f"Created {len(created_modules)} virtual modules: {', '.join(created_modules)}")


def _auto_initialize_registry() -> None:
    """
    Auto-initialize the function registry on module import.

    This follows the same pattern as storage_registry in openhcs.io.base.
    """
    global _registry_initialized

    if _registry_initialized:
        return

    try:
        # Clear and initialize the registry
        FUNC_REGISTRY.clear()

        # Phase 1: Register all functions from RegistryService (includes OpenHCS and external libraries)
        from openhcs.processing.backends.lib_registry.registry_service import RegistryService
        all_functions = RegistryService.get_all_functions_with_metadata()

        # Initialize registry structure based on discovered registries
        # Handle composite keys from RegistryService (backend:function_name)
        for composite_key, metadata in all_functions.items():
            registry_name = metadata.registry.library_name
            if registry_name not in FUNC_REGISTRY:
                FUNC_REGISTRY[registry_name] = []

        # Register all functions
        for composite_key, metadata in all_functions.items():
            registry_name = metadata.registry.library_name
            FUNC_REGISTRY[registry_name].append(metadata.func)

        # Phase 2: Apply CPU-only filtering if enabled
        if CPU_ONLY_MODE:
            logger.info("CPU-only mode enabled - filtering to numpy functions only")
            _apply_cpu_only_filtering()

        total_functions = sum(len(funcs) for funcs in FUNC_REGISTRY.values())
        logger.info(
            "Function registry auto-initialized with %d functions across %d registries",
            total_functions,
            len(FUNC_REGISTRY)
        )

        # Mark registry as initialized
        _registry_initialized = True

        # Create virtual modules for external library functions
        _create_virtual_modules()

    except Exception as e:
        logger.error(f"Failed to auto-initialize function registry: {e}")
        raise


def initialize_registry() -> None:
    """
    Initialize the function registry and scan for functions to register.

    This function is now optional since the registry auto-initializes on import.
    It can be called to force re-initialization if needed.

    Thread-safe: Uses a lock to ensure consistent access to the global registry.

    Raises:
        RuntimeError: If the registry is already initialized and force=False
    """
    with _registry_lock:
        global _registry_initialized

        # Check if registry is already initialized
        if _registry_initialized:
            logger.info("Function registry already initialized, skipping manual initialization")
            return
        
        # Clear and initialize the registry
        FUNC_REGISTRY.clear()
        
        # Phase 1: Register all functions from RegistryService (includes OpenHCS and external libraries)
        from openhcs.processing.backends.lib_registry.registry_service import RegistryService
        all_functions = RegistryService.get_all_functions_with_metadata()

        # Initialize registry structure based on discovered registries
        # Handle composite keys from RegistryService (backend:function_name)
        for composite_key, metadata in all_functions.items():
            registry_name = metadata.registry.library_name
            if registry_name not in FUNC_REGISTRY:
                FUNC_REGISTRY[registry_name] = []

        # Register all functions
        for composite_key, metadata in all_functions.items():
            registry_name = metadata.registry.library_name
            FUNC_REGISTRY[registry_name].append(metadata.func)

        # Phase 2: Apply CPU-only filtering if enabled
        if CPU_ONLY_MODE:
            logger.info("CPU-only mode enabled - filtering to numpy functions only")
            _apply_cpu_only_filtering()
        
        logger.info(
            "Function registry initialized with %d functions across %d registries",
            sum(len(funcs) for funcs in FUNC_REGISTRY.values()),
            len(FUNC_REGISTRY)
        )
        
        # Mark registry as initialized
        _registry_initialized = True

        # Create virtual modules for external library functions
        _create_virtual_modules()


def load_prebuilt_registry(registry_data: Dict) -> None:
    """
    Load a pre-built function registry from serialized data.

    This allows subprocess workers to skip function discovery by loading
    a registry that was built in the main process.

    Args:
        registry_data: Dictionary containing the pre-built registry
    """
    with _registry_lock:
        global _registry_initialized

        FUNC_REGISTRY.clear()
        FUNC_REGISTRY.update(registry_data)
        _registry_initialized = True

        total_functions = sum(len(funcs) for funcs in FUNC_REGISTRY.values())
        logger.info(f"Loaded pre-built registry with {total_functions} functions")


def _scan_and_register_functions() -> None:
    """
    Scan the processing directory for native OpenHCS functions.

    This function recursively imports all modules in the processing directory
    and registers functions that have matching input_memory_type and output_memory_type
    attributes that are in the set of valid memory types.

    This is Phase 1 of initialization - only native OpenHCS functions.
    External library functions are registered in Phase 2.
    """
    from openhcs import processing

    processing_path = os.path.dirname(processing.__file__)
    processing_package = "openhcs.processing"

    logger.info("Phase 1: Scanning for native OpenHCS functions in %s", processing_path)

    # Walk through all modules in the processing package
    for _, module_name, is_pkg in pkgutil.walk_packages([processing_path], f"{processing_package}."):
        try:
            # Import the module
            logger.debug(f"Scanning module: {module_name}")
            module = importlib.import_module(module_name)

            # Skip packages (we'll process their modules separately)
            if is_pkg:
                logger.debug(f"Skipping package: {module_name}")
                continue

            # Find all functions in the module
            function_count = 0
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                # Check if the function has the required attributes
                if hasattr(obj, "input_memory_type") and hasattr(obj, "output_memory_type"):
                    input_type = getattr(obj, "input_memory_type")
                    output_type = getattr(obj, "output_memory_type")

                    # Register if input and output types are valid (OpenHCS functions can have mixed types)
                    if input_type in VALID_MEMORY_TYPES and output_type in VALID_MEMORY_TYPES:
                        _register_function(obj, "openhcs")
                        function_count += 1

            logger.debug(f"Module {module_name}: found {function_count} registerable functions")
        except Exception as e:
            logger.warning("Error importing module %s: %s", module_name, e)


def _apply_unified_decoration(original_func, func_name, memory_type, create_wrapper=True):
    """
    Unified decoration pattern for all external library functions.

    NOTE: Dtype preservation is now handled at the decorator level in decorators.py.
    This function applies memory type attributes, decorator wrappers, and module replacement.

    This applies the same hybrid approach across all registries:
    1. Direct decoration (for subprocess compatibility)
    2. Memory type decorator application (for dtype preservation and other features)
    3. Module replacement (for best user experience and pickling compatibility)

    Args:
        original_func: The original external library function
        func_name: Function name for wrapper creation
        memory_type: MemoryType enum value (NUMPY, CUPY, PYCLESPERANTO, TORCH, TENSORFLOW, JAX)
        create_wrapper: Whether to apply memory type decorator (default: True)

    Returns:
        The function to register (decorated if create_wrapper=True, original if not)
    """
    from openhcs.constants import MemoryType

    # Step 1: Direct decoration (for subprocess compatibility)
    original_func.input_memory_type = memory_type.value
    original_func.output_memory_type = memory_type.value

    if not create_wrapper:
        return original_func

    # Step 2: Apply memory type decorator (includes dtype preservation, streams, OOM recovery)
    from openhcs.core.memory.decorators import numpy, cupy, torch, tensorflow, jax, pyclesperanto

    if memory_type == MemoryType.NUMPY:
        wrapper_func = numpy(original_func)
    elif memory_type == MemoryType.CUPY:
        wrapper_func = cupy(original_func)
    elif memory_type == MemoryType.TORCH:
        wrapper_func = torch(original_func)
    elif memory_type == MemoryType.TENSORFLOW:
        wrapper_func = tensorflow(original_func)
    elif memory_type == MemoryType.JAX:
        wrapper_func = jax(original_func)
    elif memory_type == MemoryType.PYCLESPERANTO:
        wrapper_func = pyclesperanto(original_func)
    else:
        # Fallback for unknown memory types
        wrapper_func = original_func
        wrapper_func.input_memory_type = memory_type.value
        wrapper_func.output_memory_type = memory_type.value

    # Step 3: Module replacement (for best user experience and pickling compatibility)
    module_name = original_func.__module__
    if module_name in sys.modules:
        target_module = sys.modules[module_name]
        if hasattr(target_module, func_name):
            setattr(target_module, func_name, wrapper_func)
            logger.debug(f"Replaced {module_name}.{func_name} with enhanced function")

    return wrapper_func




def register_function(func: Callable, backend: str = None, **kwargs) -> None:
    """
    Manually register a function with the function registry.

    This is the public API for registering functions that are not auto-discovered
    by the module scanner (e.g., dynamically decorated functions).

    Args:
        func: The function to register (must have input_memory_type and output_memory_type attributes)
        backend: Optional backend name (defaults to func.input_memory_type)
        **kwargs: Additional metadata (ignored for compatibility)

    Raises:
        ValueError: If function doesn't have required memory type attributes
        ValueError: If memory types are invalid
    """
    with _registry_lock:
        # Ensure registry is initialized
        if not _registry_initialized:
            _auto_initialize_registry()

        # Validate function has required attributes
        if not hasattr(func, "input_memory_type") or not hasattr(func, "output_memory_type"):
            raise ValueError(
                f"Function '{func.__name__}' must have input_memory_type and output_memory_type attributes"
            )

        input_type = func.input_memory_type
        output_type = func.output_memory_type

        # Validate memory types
        if input_type not in VALID_MEMORY_TYPES:
            raise ValueError(f"Invalid input memory type: {input_type}")
        if output_type not in VALID_MEMORY_TYPES:
            raise ValueError(f"Invalid output memory type: {output_type}")

        # Use backend if specified, otherwise register as openhcs
        registry_name = backend or "openhcs"
        if registry_name not in FUNC_REGISTRY:
            raise ValueError(f"Invalid registry name: {registry_name}")

        # Register the function
        _register_function(func, registry_name)


def _apply_cpu_only_filtering() -> None:
    """Filter registry to only include numpy-compatible functions when CPU_ONLY_MODE is enabled."""
    for registry_name, functions in list(FUNC_REGISTRY.items()):
        filtered_functions = []
        for func in functions:
            # Only keep functions with numpy memory types
            if hasattr(func, 'output_memory_type') and func.output_memory_type == "numpy":
                filtered_functions.append(func)

        # Update registry with filtered functions, remove empty registries
        if filtered_functions:
            FUNC_REGISTRY[registry_name] = filtered_functions
        else:
            del FUNC_REGISTRY[registry_name]


def _register_function(func: Callable, registry_name: str) -> None:
    """
    Register a function for a specific registry.

    This is an internal function used during automatic scanning and manual registration.

    Args:
        func: The function to register
        registry_name: The registry name (e.g., "openhcs", "skimage", "pyclesperanto")
    """
    # Skip if function is already registered
    if func in FUNC_REGISTRY[registry_name]:
        logger.debug(
            "Function '%s' already registered for registry '%s'",
            func.__name__, registry_name
        )
        return

    # Add function to registry
    FUNC_REGISTRY[registry_name].append(func)

    # Add registry_name attribute for easier inspection
    setattr(func, "registry", registry_name)

    logger.debug(
        "Registered function '%s' for memory type '%s'",
        func.__name__, memory_type
    )


def get_functions_by_memory_type(memory_type: str) -> List[Callable]:
    """
    Get all functions for a specific memory type using the new RegistryService.

    Args:
        memory_type: The memory type (e.g., "numpy", "cupy", "torch")

    Returns:
        A list of functions for the specified memory type

    Raises:
        ValueError: If the memory type is not valid
    """
    # Check if memory type is valid
    if memory_type not in VALID_MEMORY_TYPES:
        raise ValueError(
            f"Invalid memory type: {memory_type}. "
            f"Valid types are: {', '.join(sorted(VALID_MEMORY_TYPES))}"
        )

    # Get functions from new RegistryService
    from openhcs.processing.backends.lib_registry.registry_service import RegistryService
    all_functions = RegistryService.get_all_functions_with_metadata()

    # Filter functions by memory type using proper architecture
    functions = []
    for func_name, metadata in all_functions.items():
        # Handle two distinct patterns:

        # 1. Runtime Testing Libraries: Use registry's MEMORY_TYPE attribute
        if hasattr(metadata, 'registry') and hasattr(metadata.registry, 'MEMORY_TYPE'):
            if metadata.registry.MEMORY_TYPE == memory_type:
                functions.append(metadata.func)

        # 2. OpenHCS Native Functions: Check function's own memory type attributes
        elif metadata.tags and 'openhcs' in metadata.tags:
            # Check if function has memory type information
            func = metadata.func
            if hasattr(func, 'input_memory_type') and func.input_memory_type == memory_type:
                functions.append(func)
            elif hasattr(func, 'backend') and func.backend == memory_type:
                functions.append(func)

    # Also include legacy FUNC_REGISTRY functions for backward compatibility
    with _registry_lock:
        if _registry_initialized and memory_type in FUNC_REGISTRY:
            functions.extend(FUNC_REGISTRY[memory_type])

    return functions


def get_function_info(func: Callable) -> Dict[str, Any]:
    """
    Get information about a registered function.
    
    Args:
        func: The function to get information about
        
    Returns:
        A dictionary containing information about the function
        
    Raises:
        ValueError: If the function does not have memory type attributes
    """
    if not hasattr(func, "input_memory_type") or not hasattr(func, "output_memory_type"):
        raise ValueError(
            f"Function '{func.__name__}' does not have memory type attributes"
        )
    
    return {
        "name": func.__name__,
        "input_memory_type": func.input_memory_type,
        "output_memory_type": func.output_memory_type,
        "backend": getattr(func, "backend", func.input_memory_type),
        "doc": func.__doc__,
        "module": func.__module__
    }


def is_registry_initialized() -> bool:
    """
    Check if the function registry has been initialized.
    
    Thread-safe: Uses a lock to ensure consistent access to the initialization flag.
    
    Returns:
        True if the registry is initialized, False otherwise
    """
    with _registry_lock:
        return _registry_initialized


def get_valid_memory_types() -> Set[str]:
    """
    Get the set of valid memory types.

    Returns:
        A set of valid memory type names
    """
    return VALID_MEMORY_TYPES.copy()


# Import hook system removed - using existing comprehensive registries


def get_function_by_name(function_name: str, memory_type: str) -> Optional[Callable]:
    """
    Get a specific function by name and memory type from the registry.

    Args:
        function_name: Name of the function to find
        memory_type: The memory type (e.g., "numpy", "cupy", "torch")

    Returns:
        The function if found, None otherwise

    Raises:
        RuntimeError: If the registry is not initialized
        ValueError: If the memory type is not valid
    """
    functions = get_functions_by_memory_type(memory_type)

    for func in functions:
        if func.__name__ == function_name:
            return func

    return None


def get_all_function_names(memory_type: str) -> List[str]:
    """
    Get all function names registered for a specific memory type.

    Args:
        memory_type: The memory type (e.g., "numpy", "cupy", "torch")

    Returns:
        A list of function names

    Raises:
        RuntimeError: If the registry is not initialized
        ValueError: If the memory type is not valid
    """
    functions = get_functions_by_memory_type(memory_type)
    return [func.__name__ for func in functions]


# Auto-initialize the registry on module import (following storage_registry pattern)
# Skip initialization in subprocess runner mode for faster startup
import os
if not os.environ.get('OPENHCS_SUBPROCESS_NO_GPU'):
    _auto_initialize_registry()
