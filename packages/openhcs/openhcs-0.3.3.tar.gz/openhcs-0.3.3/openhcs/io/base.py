# openhcs/io/storage/backends/base.py
"""
Abstract base classes for storage backends.

This module defines the fundamental interfaces for storage backends,
independent of specific implementations. It establishes the contract
that all storage backends must fulfill.
"""

import logging
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from openhcs.constants.constants import Backend
from openhcs.io.exceptions import StorageResolutionError

logger = logging.getLogger(__name__)


class DataSink(ABC):
    """
    Abstract base class for data destinations.

    Defines the minimal interface for sending data to any destination,
    whether storage, streaming, or other data handling systems.

    This interface follows OpenHCS principles:
    - Fail-loud: No defensive programming, explicit error handling
    - Minimal: Only essential operations both storage and streaming need
    - Generic: Enables any type of data destination backend
    """

    @abstractmethod
    def save(self, data: Any, identifier: Union[str, Path], **kwargs) -> None:
        """
        Send data to the destination.

        Args:
            data: The data to send
            identifier: Unique identifier for the data (path-like for compatibility)
            **kwargs: Backend-specific arguments

        Raises:
            TypeError: If identifier is not a valid type
            ValueError: If data cannot be sent to destination
        """
        pass

    @abstractmethod
    def save_batch(self, data_list: List[Any], identifiers: List[Union[str, Path]], **kwargs) -> None:
        """
        Send multiple data objects to the destination in a single operation.

        Args:
            data_list: List of data objects to send
            identifiers: List of unique identifiers (must match length of data_list)
            **kwargs: Backend-specific arguments

        Raises:
            ValueError: If data_list and identifiers have different lengths
            TypeError: If any identifier is not a valid type
            ValueError: If any data cannot be sent to destination
        """
        pass


class VirtualBackend(DataSink):
    """
    Abstract base for backends that provide virtual filesystem semantics.

    Virtual backends generate file listings on-demand without real filesystem operations.
    Examples: OMERO (generates filenames from plate structure), S3 (lists objects), HTTP APIs.

    Virtual backends may require additional context via kwargs.
    Backends MUST validate required kwargs and raise TypeError if missing.
    """

    @abstractmethod
    def load(self, file_path: Union[str, Path], **kwargs) -> Any:
        """
        Load data from virtual path.

        Args:
            file_path: Virtual path to load
            **kwargs: Backend-specific context (e.g., plate_id for OMERO)

        Returns:
            The loaded data

        Raises:
            FileNotFoundError: If the virtual path does not exist
            TypeError: If required kwargs are missing
            ValueError: If the data cannot be loaded
        """
        pass

    @abstractmethod
    def load_batch(self, file_paths: List[Union[str, Path]], **kwargs) -> List[Any]:
        """
        Load multiple virtual paths in a single batch operation.

        Args:
            file_paths: List of virtual paths to load
            **kwargs: Backend-specific context

        Returns:
            List of loaded data objects in the same order as file_paths

        Raises:
            FileNotFoundError: If any virtual path does not exist
            TypeError: If required kwargs are missing
            ValueError: If any data cannot be loaded
        """
        pass

    @abstractmethod
    def list_files(self, directory: Union[str, Path], pattern: Optional[str] = None,
                  extensions: Optional[Set[str]] = None, recursive: bool = False,
                  **kwargs) -> List[str]:
        """
        Generate virtual file listing.

        Args:
            directory: Virtual directory path
            pattern: Optional file pattern filter
            extensions: Optional set of file extensions to filter
            recursive: Whether to list recursively
            **kwargs: Backend-specific context (e.g., plate_id for OMERO)

        Returns:
            List of virtual filenames

        Raises:
            TypeError: If required kwargs are missing
            ValueError: If directory is invalid
        """
        pass

    @property
    def requires_filesystem_validation(self) -> bool:
        """
        Whether this backend requires filesystem validation.

        Virtual backends return False - they don't have real filesystem paths.
        Real backends return True - they need path validation.

        Returns:
            False for virtual backends
        """
        return False


class StorageBackend(DataSink):
    """
    Abstract base class for persistent storage operations.

    Extends DataSink with retrieval capabilities and file system operations
    for backends that provide persistent storage with file-like semantics.

    Concrete implementations should use StorageBackendMeta for automatic registration.
    """

    # Inherits save() and save_batch() from DataSink

    @abstractmethod
    def load(self, file_path: Union[str, Path], **kwargs) -> Any:
        """
        Load data from a file.

        Args:
            file_path: Path to the file to load
            **kwargs: Additional arguments for the load operation

        Returns:
            The loaded data

        Raises:
            FileNotFoundError: If the file does not exist
            TypeError: If the file_path is not a valid path type
            ValueError: If the file cannot be loaded
        """
        pass

    @abstractmethod
    def save(self, data: Any, output_path: Union[str, Path], **kwargs) -> None:
        """
        Save data to a file.

        Args:
            data: The data to save
            output_path: Path where the data should be saved
            **kwargs: Additional arguments for the save operation

        Raises:
            TypeError: If the output_path is not a valid path type
            ValueError: If the data cannot be saved
        """
        pass

    @abstractmethod
    def load_batch(self, file_paths: List[Union[str, Path]], **kwargs) -> List[Any]:
        """
        Load multiple files in a single batch operation.

        Args:
            file_paths: List of file paths to load
            **kwargs: Additional arguments for the load operation

        Returns:
            List of loaded data objects in the same order as file_paths

        Raises:
            FileNotFoundError: If any file does not exist
            TypeError: If any file_path is not a valid path type
            ValueError: If any file cannot be loaded
        """
        pass

    @abstractmethod
    def save_batch(self, data_list: List[Any], output_paths: List[Union[str, Path]], **kwargs) -> None:
        """
        Save multiple data objects in a single batch operation.

        Args:
            data_list: List of data objects to save
            output_paths: List of destination paths (must match length of data_list)
            **kwargs: Additional arguments for the save operation

        Raises:
            ValueError: If data_list and output_paths have different lengths
            TypeError: If any output_path is not a valid path type
            ValueError: If any data cannot be saved
        """
        pass

    @abstractmethod
    def list_files(self, directory: Union[str, Path], pattern: Optional[str] = None,
                  extensions: Optional[Set[str]] = None, recursive: bool = False,
                  **kwargs) -> List[Path]:
        """
        List files in a directory, optionally filtering by pattern and extensions.

        Args:
            directory: Directory to search.
            pattern: Optional glob pattern to match filenames.
            extensions: Optional set of file extensions to filter by (e.g., {'.tif', '.png'}).
                        Extensions should include the dot and are case-insensitive.
            recursive: Whether to search recursively.
            **kwargs: Backend-specific arguments (unused for most backends)

        Returns:
            List of paths to matching files.

        Raises:
            TypeError: If the directory is not a valid path type
            FileNotFoundError: If the directory does not exist
        """
        pass

    @property
    def requires_filesystem_validation(self) -> bool:
        """
        Whether this backend requires filesystem validation.

        Real filesystem backends return True - they need path validation.
        Virtual backends return False - they don't have real filesystem paths.

        Returns:
            True for real filesystem backends
        """
        return True

    @abstractmethod
    def list_dir(self, path: Union[str, Path]) -> List[str]:
        """
        List the names of immediate entries in a directory.

        Args:
            path: Directory path to list.

        Returns:
            List of entry names (not full paths) in the directory.

        Raises:
            FileNotFoundError: If the path does not exist.
            NotADirectoryError: If the path is not a directory.
            TypeError: If the path is not a valid path type.
        """
        pass

    @abstractmethod
    def delete(self, file_path: Union[str, Path]) -> None:
        """
        Delete a file.

        Args:
            file_path: Path to the file to delete

        Raises:
            TypeError: If the file_path is not a valid path type
            FileNotFoundError: If the file does not exist
            ValueError: If the file cannot be deleted
        """
        pass

    @abstractmethod
    def delete_all(self, file_path: Union[str, Path]) -> None:
        """
        Deletes a file or a folder in full.

        Args:
            file_path: Path to the file to delete

        Raises:
            TypeError: If the file_path is not a valid path type
            ValueError: If the file cannot be deleted
        """
        pass


    @abstractmethod
    def ensure_directory(self, directory: Union[str, Path]) -> Path:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory: Path to the directory to ensure exists

        Returns:
            The path to the directory

        Raises:
            TypeError: If the directory is not a valid path type
            ValueError: If the directory cannot be created
        """
        pass


    @abstractmethod
    def create_symlink(self, source: Union[str, Path], link_name: Union[str, Path]):
        """
        Creates a symlink from source to link_name.

        Args:
            source: Path to the source file
            link_name: Path where the symlink should be created

        Raises:
            TypeError: If the path is not a valid path type
        """
        pass

    @abstractmethod
    def is_symlink(self, source: Union[str, Path]) -> bool:
        """
        Checks if a path is a symlink.

        Args:
            source: Path to the source file

        Raises:
            TypeError: If the path is not a valid path type
        """
    
    @abstractmethod
    def is_file(self, source: Union[str, Path]) -> bool:
        """
        Checks if a path is a file.

        Args:
            source: Path to the source file

        Raises:
            TypeError: If the path is not a valid path type
        """
    @abstractmethod
    def is_dir(self, source: Union[str, Path]) -> bool:
        """
        Checks if a path is a symlink.

        Args:
            source: Path to the source file

        Raises:
            TypeError: If the path is not a valid path type
        """
    
    @abstractmethod
    def move(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """ 
        Move a file or directory from src to dst.

        Args:
            src: Path to the source file
            dst: Path to the destination file

        Raises:
            TypeError: If the path is not a valid path type
            FileNotFoundError: If the source file does not exist
            FileExistsError: If the destination file already exists
            ValueError: If the file cannot be moved
        """
        pass

    @abstractmethod
    def copy(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """
        Copy a file or directory from src to dst.

        Args:
            src: Path to the source file
            dst: Path to the destination file

        Raises:
            TypeError: If the path is not a valid path type
            FileNotFoundError: If the source file does not exist
            FileExistsError: If the destination file already exists
            ValueError: If the file cannot be copied
        """
        pass

    @abstractmethod
    def stat(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get metadata for a file or directory.

        Args:
            src: Path to the source file

        Raises:
            TypeError: If the path is not a valid path type
            FileNotFoundError: If the source file does not exist
        """
        pass

    def exists(self, path: Union[str, Path]) -> bool:
        """
        Declarative truth test: does the path resolve to a valid object?

        A path only 'exists' if:
        - it is a valid file or directory
        - or it is a symlink that resolves to a valid file or directory

        Returns:
            bool: True if path structurally resolves to a real object
        """
        try:
            return self.is_file(path)
        except (FileNotFoundError, NotADirectoryError, StorageResolutionError):
            pass
        except IsADirectoryError:
            # Path exists but is a directory, so check if it's a valid directory
            try:
                return self.is_dir(path)
            except (FileNotFoundError, NotADirectoryError, StorageResolutionError):
                return False

        # If is_file failed for other reasons, try is_dir
        try:
            return self.is_dir(path)
        except (FileNotFoundError, NotADirectoryError, StorageResolutionError):
            return False


def _create_storage_registry() -> Dict[str, DataSink]:
    """
    Create a new storage registry using metaclass-based discovery.

    This function creates a dictionary mapping backend names to their respective
    storage backend instances using automatic discovery and registration.

    Now returns Dict[str, DataSink] to support both StorageBackend and StreamingBackend.

    Returns:
        A dictionary mapping backend names to DataSink instances (polymorphic)

    Note:
        This function now uses the metaclass-based registry system for automatic
        backend discovery, eliminating hardcoded imports.
    """
    # Import the metaclass-based registry system
    from openhcs.io.backend_registry import create_storage_registry

    return create_storage_registry()


class _LazyStorageRegistry(dict):
    """
    Storage registry that auto-initializes on first access.

    This maintains backward compatibility with existing code that
    directly accesses storage_registry without calling ensure_storage_registry().
    All read operations trigger lazy initialization, while write operations
    (like OMERO backend registration) work without initialization.
    """

    def __getitem__(self, key):
        ensure_storage_registry()
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        # Allow setting without initialization (for OMERO backend registration)
        return super().__setitem__(key, value)

    def __contains__(self, key):
        ensure_storage_registry()
        return super().__contains__(key)

    def get(self, key, default=None):
        ensure_storage_registry()
        return super().get(key, default)

    def keys(self):
        ensure_storage_registry()
        return super().keys()

    def values(self):
        ensure_storage_registry()
        return super().values()

    def items(self):
        ensure_storage_registry()
        return super().items()


# Global singleton storage registry - created lazily on first access
# This is the shared registry instance that all components should use
storage_registry: Dict[str, DataSink] = _LazyStorageRegistry()
_registry_initialized = False
_registry_lock = threading.Lock()


def ensure_storage_registry() -> None:
    """
    Ensure storage registry is initialized.

    Lazily creates the registry on first access to avoid importing
    GPU-heavy backends during module import. This provides instant
    imports while maintaining backward compatibility.

    Thread-safe: Multiple threads can call this simultaneously.
    """
    global _registry_initialized

    # Double-checked locking pattern for thread safety
    if not _registry_initialized:
        with _registry_lock:
            if not _registry_initialized:
                storage_registry.update(_create_storage_registry())
                _registry_initialized = True
                logger.info("Lazily initialized storage registry")


def get_backend(backend_type: str) -> DataSink:
    """
    Get a backend by type, ensuring registry is initialized.

    Args:
        backend_type: Backend type (e.g., 'disk', 'memory', 'zarr')

    Returns:
        Backend instance

    Raises:
        KeyError: If backend type not found
    """
    ensure_storage_registry()

    backend_key = backend_type.lower()
    if backend_key not in storage_registry:
        raise KeyError(f"Backend '{backend_type}' not found. "
                      f"Available: {list(storage_registry.keys())}")

    return storage_registry[backend_key]


def reset_memory_backend() -> None:
    """
    Clear files from the memory backend while preserving directory structure.

    This function clears all file entries from the existing memory backend but preserves
    directory entries (None values). This prevents key collisions between plate executions
    while maintaining the directory structure needed for subsequent operations.

    Benefits over full reset:
    - Preserves directory structure created by path planner
    - Prevents "Parent path does not exist" errors on subsequent runs
    - Avoids key collisions for special inputs/outputs
    - Maintains performance by not recreating directory hierarchy

    Note:
        This only affects the memory backend. Other backends (disk, zarr) are not modified.
    """

    # Clear files from existing memory backend while preserving directories
    memory_backend = storage_registry[Backend.MEMORY.value]
    memory_backend.clear_files_only()
    logger.info("Memory backend reset - files cleared, directories preserved")