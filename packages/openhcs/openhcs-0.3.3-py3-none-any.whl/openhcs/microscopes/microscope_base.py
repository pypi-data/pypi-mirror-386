"""
Microscope base implementations for openhcs.

This module provides the base implementations for microscope-specific functionality,
including filename parsing and metadata handling.
"""

import logging
import os
from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Type

# Import constants
from openhcs.constants.constants import Backend
# PatternDiscoveryEngine imported locally to avoid circular imports
from openhcs.io.filemanager import FileManager
# Import interfaces from the base interfaces module
from openhcs.microscopes.microscope_interfaces import (FilenameParser,
                                                            MetadataHandler)

logger = logging.getLogger(__name__)

# Dictionary to store registered microscope handlers
MICROSCOPE_HANDLERS = {}

# Dictionary to store registered metadata handlers for auto-detection
METADATA_HANDLERS = {}


class MicroscopeHandlerMeta(ABCMeta):
    """Metaclass for automatic registration of microscope handlers."""

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        # Only register concrete handler classes (not the abstract base class)
        if bases and not getattr(new_class, '__abstractmethods__', None):
            # Use explicit microscope type if provided, otherwise extract from class name
            microscope_type = getattr(new_class, '_microscope_type', None)
            if not microscope_type:
                if name.endswith('Handler'):
                    microscope_type = name[:-7].lower()  # ImageXpressHandler -> imagexpress
                else:
                    microscope_type = name.lower()

            # Auto-register in MICROSCOPE_HANDLERS
            MICROSCOPE_HANDLERS[microscope_type] = new_class

            # Store the microscope type as the standard class attribute
            new_class._microscope_type = microscope_type

            # Auto-register metadata handler if the class has one
            metadata_handler_class = getattr(new_class, '_metadata_handler_class', None)
            if metadata_handler_class:
                METADATA_HANDLERS[microscope_type] = metadata_handler_class

            logger.debug(f"Auto-registered {name} as '{microscope_type}'")

        return new_class


def register_metadata_handler(handler_class, metadata_handler_class):
    """
    Register a metadata handler for a microscope handler class.

    This function is called when _metadata_handler_class is set after class definition.
    """
    microscope_type = getattr(handler_class, '_microscope_type', None)
    if microscope_type:
        METADATA_HANDLERS[microscope_type] = metadata_handler_class
        logger.debug(f"Registered metadata handler {metadata_handler_class.__name__} for '{microscope_type}'")
    else:
        logger.warning(f"Could not register metadata handler for {handler_class.__name__} - no microscope type found")




class MicroscopeHandler(ABC, metaclass=MicroscopeHandlerMeta):
    """Composed class for handling microscope-specific functionality."""

    DEFAULT_MICROSCOPE = 'auto'
    _handlers_cache = None

    # Optional class attribute for explicit metadata handler registration
    _metadata_handler_class: Optional[Type[MetadataHandler]] = None

    def __init__(self, parser: Optional[FilenameParser],
                 metadata_handler: MetadataHandler):
        """
        Initialize the microscope handler.

        Args:
            parser: Parser for microscopy filenames. Can be None for virtual backends
                   that don't need workspace preparation or pattern discovery.
            metadata_handler: Handler for microscope metadata.
        """
        self.parser = parser
        self.metadata_handler = metadata_handler
        self.plate_folder: Optional[Path] = None # Store workspace path if needed by methods

        # Pattern discovery engine will be created on demand with the provided filemanager

    @property
    @abstractmethod
    def root_dir(self) -> str:
        """
        Root directory where virtual workspace preparation starts.

        This defines:
        1. The starting point for virtual workspace operations (flattening, remapping)
        2. The subdirectory key used when saving virtual workspace metadata

        Examples:
        - ImageXpress: "." (plate root - TimePoint/ZStep folders are flattened from plate root)
        - OperaPhenix: "Images" (field remapping applied to Images/ subdirectory)
        - OpenHCS: Determined from metadata (e.g., "zarr", "images")
        """
        pass

    @property
    @abstractmethod
    def microscope_type(self) -> str:
        """Microscope type identifier (for interface enforcement only)."""
        pass

    @property
    @abstractmethod
    def metadata_handler_class(self) -> Type[MetadataHandler]:
        """Metadata handler class (for interface enforcement only)."""
        pass

    @property
    @abstractmethod
    def compatible_backends(self) -> List[Backend]:
        """
        List of storage backends this microscope handler is compatible with, in priority order.

        Must be explicitly declared by each handler implementation.
        The first backend in the list is the preferred/highest priority backend.
        The compiler will use the first backend for initial step materialization.

        Common patterns:
        - [Backend.DISK] - Basic handlers (ImageXpress, Opera Phenix)
        - [Backend.ZARR, Backend.DISK] - Advanced handlers (OpenHCS: zarr preferred, disk fallback)

        Returns:
            List of Backend enum values this handler can work with, in priority order
        """
        pass

    def get_available_backends(self, plate_path: Union[str, Path]) -> List[Backend]:
        """
        Get available storage backends for this specific plate.

        Default implementation returns all compatible backends.
        Override this method only if you need to check actual disk state
        (like OpenHCS which reads from metadata).

        Args:
            plate_path: Path to the plate folder

        Returns:
            List of Backend enums that are available for this plate.
        """
        return self.compatible_backends

    def get_primary_backend(self, plate_path: Union[str, Path], filemanager: 'FileManager') -> str:
        """
        Get the primary backend name for this plate.

        Checks FileManager registry first for registered backends (like virtual_workspace),
        then falls back to compatible backends.

        Override this method only if you need custom backend selection logic
        (like OpenHCS which reads from metadata).

        Args:
            plate_path: Path to the plate folder (or subdirectory)
            filemanager: FileManager instance to check for registered backends

        Returns:
            Backend name string (e.g., 'disk', 'zarr', 'virtual_workspace')
        """
        # Check if virtual workspace backend is registered in FileManager
        # This takes priority over compatible backends
        if Backend.VIRTUAL_WORKSPACE.value in filemanager.registry:
            logger.info(f"✅ Using backend '{Backend.VIRTUAL_WORKSPACE.value}' from FileManager registry")
            return Backend.VIRTUAL_WORKSPACE.value

        # Fall back to compatible backends
        available_backends = self.get_available_backends(plate_path)
        if not available_backends:
            raise RuntimeError(f"No available backends for {self.microscope_type} microscope at {plate_path}")
        logger.info(f"⚠️ Using backend '{available_backends[0].value}' from compatible backends (virtual workspace not registered)")
        return available_backends[0].value

    def _register_virtual_workspace_backend(self, plate_path: Union[str, Path], filemanager: FileManager) -> None:
        """
        Register virtual workspace backend if not already registered.

        Centralized registration logic to avoid duplication across handlers.

        Args:
            plate_path: Path to plate directory
            filemanager: FileManager instance
        """
        from openhcs.io.virtual_workspace import VirtualWorkspaceBackend
        from openhcs.constants.constants import Backend

        if Backend.VIRTUAL_WORKSPACE.value not in filemanager.registry:
            backend = VirtualWorkspaceBackend(plate_root=Path(plate_path))
            filemanager.registry[Backend.VIRTUAL_WORKSPACE.value] = backend
            logger.info(f"Registered virtual workspace backend for {plate_path}")

    def initialize_workspace(self, plate_path: Path, filemanager: FileManager) -> Path:
        """
        Initialize plate by creating virtual mapping in metadata.

        No physical workspace directory is created - mapping is purely metadata-based.
        All paths are relative to plate_path.

        Args:
            plate_path: Path to plate directory
            filemanager: FileManager instance

        Returns:
            Path to image directory (determined from plate structure)
        """
        plate_path = Path(plate_path)

        # Set plate_folder for this handler
        self.plate_folder = plate_path

        # Call microscope-specific virtual mapping builder
        # This builds the plate-relative mapping dict and saves to metadata
        self._build_virtual_mapping(plate_path, filemanager)

        # Register virtual workspace backend
        self._register_virtual_workspace_backend(plate_path, filemanager)

        # Return image directory using post_workspace
        # skip_preparation=True because _build_virtual_mapping() already ran
        return self.post_workspace(plate_path, filemanager, skip_preparation=True)

    def post_workspace(self, plate_path: Union[str, Path], filemanager: FileManager, skip_preparation: bool = False) -> Path:
        """
        Apply post-workspace processing using virtual mapping.

        All operations use plate_path - no workspace directory concept.

        Args:
            plate_path: Path to plate directory
            filemanager: FileManager instance
            skip_preparation: Skip microscope-specific preparation (default: False)

        Returns:
            Path to image directory
        """
        # Ensure plate_path is a Path object
        if isinstance(plate_path, str):
            plate_path = Path(plate_path)

        # NO existence check - virtual workspaces are metadata-only

        # Apply microscope-specific preparation logic
        # _build_virtual_mapping() returns the correct image directory for each microscope:
        # - ImageXpress: plate_path (images are at plate root with TimePoint_X/ prefix in mapping)
        # - OperaPhenix: plate_path/Images (images are in Images/ subdirectory)
        if skip_preparation:
            logger.info("📁 SKIPPING PREPARATION: Virtual mapping already built")
            # When skipping, we need to determine image_dir from metadata
            # Read metadata to get the subdirectory key
            from openhcs.microscopes.openhcs import OpenHCSMetadataHandler
            from openhcs.io.exceptions import MetadataNotFoundError
            from openhcs.io.metadata_writer import resolve_subdirectory_path

            openhcs_metadata_handler = OpenHCSMetadataHandler(filemanager)
            metadata = openhcs_metadata_handler._load_metadata_dict(plate_path)
            subdirs = metadata.get("subdirectories", {})

            # Find the subdirectory with workspace_mapping (should be "." or "Images")
            subdir_with_mapping = next(
                (name for name, data in subdirs.items() if "workspace_mapping" in data),
                None
            )

            # Fail if no workspace_mapping found
            if subdir_with_mapping is None:
                raise MetadataNotFoundError(
                    f"skip_preparation=True but no workspace_mapping found in metadata for {plate_path}. "
                    "Virtual workspace must be prepared before skipping."
                )

            # Convert subdirectory name to path (handles "." -> plate_path)
            image_dir = resolve_subdirectory_path(subdir_with_mapping, plate_path)
        else:
            logger.info("🔄 APPLYING PREPARATION: Building virtual mapping")
            # _build_virtual_mapping() returns the image directory
            image_dir = self._build_virtual_mapping(plate_path, filemanager)

        # Determine backend - check if virtual workspace backend is registered
        if Backend.VIRTUAL_WORKSPACE.value in filemanager.registry:
            backend_type = Backend.VIRTUAL_WORKSPACE.value
        else:
            backend_type = Backend.DISK.value

        # Ensure parser is provided
        parser = self.parser

        # Get all image files in the directory
        image_files = filemanager.list_image_files(image_dir, backend_type)

        # Map original filenames to reconstructed filenames
        rename_map = {}

        for file_path in image_files:
            # FileManager should return strings, but handle Path objects too
            if isinstance(file_path, str):
                original_name = os.path.basename(file_path)
            elif isinstance(file_path, Path):
                original_name = file_path.name
            else:
                # Skip any unexpected types
                logger.warning("Unexpected file path type: %s", type(file_path).__name__)
                continue

            # Parse the filename components
            metadata = parser.parse_filename(original_name)
            if not metadata:
                logger.warning("Could not parse filename: %s", original_name)
                continue

            # Validate required components
            if metadata['site'] is None:
                logger.warning("Missing 'site' component in filename: %s", original_name)
                continue

            if metadata['channel'] is None:
                logger.warning("Missing 'channel' component in filename: %s", original_name)
                continue

            # z_index is optional - default to 1 if not present
            site = metadata['site']
            channel = metadata['channel']
            z_index = metadata['z_index'] if metadata['z_index'] is not None else 1

            # Log the components for debugging
            logger.debug(
                "Parsed components for %s: site=%s, channel=%s, z_index=%s",
                original_name, site, channel, z_index
            )

            # Reconstruct the filename with proper padding
            metadata['site'] = site
            metadata['channel'] = channel
            metadata['z_index'] = z_index
            new_name = parser.construct_filename(**metadata)

            # Add to rename map if different
            if original_name != new_name:
                rename_map[original_name] = new_name

        # Perform the renaming
        for original_name, new_name in rename_map.items():
            # Create paths for the source and destination
            if isinstance(image_dir, str):
                original_path = os.path.join(image_dir, original_name)
                new_path = os.path.join(image_dir, new_name)
            else:  # Path object
                original_path = image_dir / original_name
                new_path = image_dir / new_name

            try:
                # Ensure the parent directory exists
                # Clause 245: Workspace operations are disk-only by design
                # This call is structurally hardcoded to use the "disk" backend
                parent_dir = os.path.dirname(new_path) if isinstance(new_path, str) else new_path.parent
                filemanager.ensure_directory(parent_dir, Backend.DISK.value)

                # Rename the file using move operation
                # Clause 245: Workspace operations are disk-only by design
                # This call is structurally hardcoded to use the "disk" backend
                # Use replace_symlinks=True to allow overwriting existing symlinks
                filemanager.move(original_path, new_path, Backend.DISK.value, replace_symlinks=True)
                logger.debug("Renamed %s to %s", original_path, new_path)
            except (OSError, FileNotFoundError) as e:
                logger.error("Filesystem error renaming %s to %s: %s", original_path, new_path, e)
            except TypeError as e:
                logger.error("Type error renaming %s to %s: %s", original_path, new_path, e)
            except Exception as e:
                logger.error("Unexpected error renaming %s to %s: %s", original_path, new_path, e)

        return image_dir

    def _build_virtual_mapping(self, plate_path: Path, filemanager: FileManager) -> Path:
        """
        Build microscope-specific virtual workspace mapping.

        This method creates a plate-relative mapping dict and saves it to metadata.
        All paths in the mapping are relative to plate_path.

        Override in subclasses that need virtual workspace mapping (e.g., ImageXpress, Opera Phenix).
        Handlers that override initialize_workspace() completely (e.g., OMERO, OpenHCS) don't need
        to implement this method.

        Args:
            plate_path: Path to plate directory
            filemanager: FileManager instance for file operations

        Returns:
            Path: Suggested directory for further processing

        Raises:
            NotImplementedError: If called on a handler that doesn't support virtual workspace mapping
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement _build_virtual_mapping(). "
            f"This method is only needed for handlers that use the base class initialize_workspace(). "
            f"Handlers that override initialize_workspace() completely (like OMERO, OpenHCS) don't need this."
        )


    # Delegate methods to parser
    def parse_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Delegate to parser."""
        return self.parser.parse_filename(filename)

    def construct_filename(self, extension: str = '.tif', **component_values) -> str:
        """
        Delegate to parser using pure generic interface.
        """
        return self.parser.construct_filename(extension=extension, **component_values)

    def auto_detect_patterns(self, folder_path: Union[str, Path], filemanager: FileManager, backend: str,
                           extensions=None, group_by=None, variable_components=None, **kwargs):
        """
        Delegate to pattern engine.

        Args:
            folder_path: Path to the folder (string or Path object)
            filemanager: FileManager instance for file operations
            backend: Backend to use for file operations (required)
            extensions: Optional list of file extensions to include
            group_by: GroupBy enum to group patterns by (e.g., GroupBy.CHANNEL, GroupBy.Z_INDEX)
            variable_components: List of components to make variable (e.g., ['site', 'z_index'])
            **kwargs: Dynamic filter parameters (e.g., well_filter, site_filter, channel_filter)

        Returns:
            Dict[str, Any]: Dictionary mapping axis values to patterns
        """
        # Ensure folder_path is a valid path
        if isinstance(folder_path, str):
            folder_path = Path(folder_path)
        elif not isinstance(folder_path, Path):
            raise TypeError(f"Expected string or Path object, got {type(folder_path).__name__}")

        # Ensure the path exists using FileManager abstraction
        if not filemanager.exists(str(folder_path), backend):
            raise ValueError(f"Folder path does not exist: {folder_path}")

        # Set default GroupBy if none provided
        if group_by is None:
            from openhcs.constants.constants import GroupBy
            group_by = GroupBy.CHANNEL

        # Create pattern engine on demand with the provided filemanager
        from openhcs.formats.pattern.pattern_discovery import PatternDiscoveryEngine
        pattern_engine = PatternDiscoveryEngine(self.parser, filemanager)

        # Get patterns from the pattern engine
        patterns_by_well = pattern_engine.auto_detect_patterns(
            folder_path,
            extensions=extensions,
            group_by=group_by,
            variable_components=variable_components,
            backend=backend,
            **kwargs  # Pass through dynamic filter parameters
        )

        # 🔒 Clause 74 — Runtime Behavior Variation
        # Ensure we always return a dictionary, not a generator
        if not isinstance(patterns_by_well, dict):
            # Convert to dictionary if it's not already one
            return dict(patterns_by_well)

        return patterns_by_well

    def path_list_from_pattern(self, directory: Union[str, Path], pattern, filemanager: FileManager, backend: str, variable_components: Optional[List[str]] = None):
        """
        Delegate to pattern engine.

        Args:
            directory: Directory to search (string or Path object)
            pattern: Pattern to match (str for literal filenames)
            filemanager: FileManager instance for file operations
            backend: Backend to use for file operations (required)
            variable_components: List of components that can vary (will be ignored during matching)

        Returns:
            List of matching filenames

        Raises:
            TypeError: If a string with braces is passed (pattern paths are no longer supported)
            ValueError: If directory does not exist
        """
        # Ensure directory is a valid path using FileManager abstraction
        if isinstance(directory, str):
            directory_path = Path(directory)
            if not filemanager.exists(str(directory_path), backend):
                raise ValueError(f"Directory does not exist: {directory}")
        elif isinstance(directory, Path):
            directory_path = directory
            if not filemanager.exists(str(directory_path), backend):
                raise ValueError(f"Directory does not exist: {directory}")
        else:
            raise TypeError(f"Expected string or Path object, got {type(directory).__name__}")

        # Allow string patterns with braces - they are used for template matching
        # The pattern engine will handle template expansion to find matching files

        # Create pattern engine on demand with the provided filemanager
        from openhcs.formats.pattern.pattern_discovery import PatternDiscoveryEngine
        pattern_engine = PatternDiscoveryEngine(self.parser, filemanager)

        # Delegate to the pattern engine
        return pattern_engine.path_list_from_pattern(directory_path, pattern, backend=backend, variable_components=variable_components)

    # Delegate metadata handling methods to metadata_handler with context

    def find_metadata_file(self, plate_path: Union[str, Path]) -> Optional[Path]:
        """Delegate to metadata handler."""
        return self.metadata_handler.find_metadata_file(plate_path)

    def get_grid_dimensions(self, plate_path: Union[str, Path]) -> Tuple[int, int]:
        """Delegate to metadata handler."""
        return self.metadata_handler.get_grid_dimensions(plate_path)

    def get_pixel_size(self, plate_path: Union[str, Path]) -> float:
        """Delegate to metadata handler."""
        return self.metadata_handler.get_pixel_size(plate_path)


# Import handler classes at module level with explicit mapping
# No aliases or legacy compatibility layers (Clause 77)

# Factory function
def create_microscope_handler(microscope_type: str = 'auto',
                              plate_folder: Optional[Union[str, Path]] = None,
                              filemanager: Optional[FileManager] = None,
                              pattern_format: Optional[str] = None,
                              allowed_auto_types: Optional[List[str]] = None) -> MicroscopeHandler:
    """
    Factory function to create a microscope handler.

    This function enforces explicit dependency injection by requiring a FileManager
    instance to be provided. This ensures that all components requiring file operations
    receive their dependencies explicitly, eliminating runtime fallbacks and enforcing
    declarative configuration.

    Args:
        microscope_type: 'auto', 'imagexpress', 'opera_phenix', 'openhcs'.
        plate_folder: Required for 'auto' detection.
        filemanager: FileManager instance. Must be provided.
        pattern_format: Name of the pattern format to use.
        allowed_auto_types: For 'auto' mode, limit detection to these types.
                           'openhcs' is always included and tried first.

    Returns:
        An initialized MicroscopeHandler instance.

    Raises:
        ValueError: If filemanager is None or if microscope_type cannot be determined.
    """
    if filemanager is None:
        raise ValueError(
            "FileManager must be provided to create_microscope_handler. "
            "Default fallback has been removed."
        )

    logger.info("Using provided FileManager for microscope handler.")

    # Auto-detect microscope type if needed
    if microscope_type == 'auto':
        if not plate_folder:
            raise ValueError("plate_folder is required for auto-detection")

        plate_folder = Path(plate_folder) if isinstance(plate_folder, str) else plate_folder
        microscope_type = _auto_detect_microscope_type(plate_folder, filemanager, allowed_types=allowed_auto_types)
        logger.info("Auto-detected microscope type: %s", microscope_type)

    # Ensure all handlers are discovered before lookup
    from openhcs.microscopes.handler_registry_service import discover_all_handlers, get_all_handler_types
    discover_all_handlers()

    # Get the appropriate handler class from the registry
    # No dynamic imports or fallbacks (Clause 77: Rot Intolerance)
    handler_class = MICROSCOPE_HANDLERS.get(microscope_type.lower())
    if not handler_class:
        available_types = get_all_handler_types()
        raise ValueError(
            f"Unsupported microscope type: {microscope_type}. "
            f"Available types: {available_types}"
        )

    # Create and configure the handler
    logger.info(f"Creating {handler_class.__name__}")

    # Create the handler with the parser and metadata handler
    # The filemanager will be passed to methods that need it
    handler = handler_class(filemanager, pattern_format=pattern_format)

    # If the handler is OpenHCSMicroscopeHandler, set its plate_folder attribute.
    # This is crucial for its dynamic parser loading mechanism.
    # Use string comparison to avoid circular import
    if handler.__class__.__name__ == 'OpenHCSMicroscopeHandler':
        if plate_folder:
            handler.plate_folder = Path(plate_folder) if isinstance(plate_folder, str) else plate_folder
            logger.info(f"Set plate_folder for OpenHCSMicroscopeHandler: {handler.plate_folder}")
        else:
            # This case should ideally not happen if auto-detection or explicit type setting
            # implies a plate_folder is known.
            logger.warning("OpenHCSMicroscopeHandler created without an initial plate_folder. "
                           "Parser will load upon first relevant method call with a path e.g. post_workspace.")

    return handler


def validate_backend_compatibility(handler: MicroscopeHandler, backend: Backend) -> bool:
    """
    Validate that a microscope handler supports a given storage backend.

    Args:
        handler: MicroscopeHandler instance to check
        backend: Backend to validate compatibility with

    Returns:
        bool: True if the handler supports the backend, False otherwise

    Example:
        >>> handler = ImageXpressHandler(filemanager)
        >>> validate_backend_compatibility(handler, Backend.ZARR)
        False
        >>> validate_backend_compatibility(handler, Backend.DISK)
        True
    """
    return backend in handler.supported_backends


def _try_metadata_detection(handler_class, filemanager: FileManager, plate_folder: Path) -> Optional[Path]:
    """
    Try metadata detection with a handler, normalizing return types.

    Args:
        handler_class: MetadataHandler class to try
        filemanager: FileManager instance
        plate_folder: Path to plate directory

    Returns:
        Path if metadata found, None if metadata not found

    Raises:
        Any exception from the handler (fail-loud behavior)
    """
    handler = handler_class(filemanager)
    result = handler.find_metadata_file(plate_folder)

    # Normalize return type: convert any truthy result to Path, falsy to None
    return Path(result) if result else None


def _auto_detect_microscope_type(plate_folder: Path, filemanager: FileManager,
                                allowed_types: Optional[List[str]] = None) -> str:
    """
    Auto-detect microscope type using registry iteration.

    Args:
        plate_folder: Path to plate directory
        filemanager: FileManager instance
        allowed_types: Optional list of microscope types to try.
                      If None, tries all registered types.
                      'openhcs' is always included and tried first.

    Returns:
        Detected microscope type string

    Raises:
        ValueError: If microscope type cannot be determined
        MetadataNotFoundError: If metadata files are missing
        Any other exception from metadata handlers (fail-loud)
    """
    # Ensure all handlers are discovered before auto-detection
    from openhcs.microscopes.handler_registry_service import discover_all_handlers
    from openhcs.io.exceptions import MetadataNotFoundError
    discover_all_handlers()

    # Build detection order: openhcsdata first, then filtered/ordered list
    detection_order = ['openhcsdata']  # Always first, always included (correct registration name)

    if allowed_types is None:
        # Use all registered handlers in registration order
        detection_order.extend([name for name in METADATA_HANDLERS.keys() if name != 'openhcsdata'])
    else:
        # Use filtered list, but ensure openhcsdata is first
        filtered_types = [name for name in allowed_types if name != 'openhcsdata' and name in METADATA_HANDLERS]
        detection_order.extend(filtered_types)

    # Try detection in order - only catch expected "not found" exceptions
    for handler_name in detection_order:
        handler_class = METADATA_HANDLERS.get(handler_name)
        if not handler_class:
            continue

        try:
            result = _try_metadata_detection(handler_class, filemanager, plate_folder)
            if result:
                logger.info(f"Auto-detected {handler_name} microscope type")
                return handler_name
        except (FileNotFoundError, MetadataNotFoundError):
            # Expected - this handler's metadata not found, try next
            logger.debug(f"{handler_name} metadata not found in {plate_folder}")
            continue

    # No handler succeeded - provide detailed error message
    available_types = list(METADATA_HANDLERS.keys())
    msg = (f"Could not auto-detect microscope type in {plate_folder}. "
           f"Tried: {detection_order}. "
           f"Available types: {available_types}. "
           f"Ensure metadata files are present for supported formats.")
    logger.error(msg)
    raise ValueError(msg)
