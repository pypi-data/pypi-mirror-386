"""
OMERO microscope implementations for openhcs.

This module provides concrete implementations of FilenameParser and MetadataHandler
for OMERO microscopes using native OMERO metadata.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import omero.model

from openhcs.constants.constants import Backend
from openhcs.io.filemanager import FileManager
from openhcs.microscopes.microscope_base import MicroscopeHandler
from openhcs.microscopes.microscope_interfaces import FilenameParser, MetadataHandler

logger = logging.getLogger(__name__)


class OMEROMetadataHandler(MetadataHandler):
    """
    Metadata handler that queries OMERO API for native metadata with caching.

    Does NOT read OpenHCS metadata files - uses OMERO's native metadata.
    Caches metadata per plate to avoid repeated OMERO queries.
    
    Retrieves OMERO connection from backend registry via filemanager (Option B pattern).
    """

    def __init__(self, filemanager: FileManager):
        super().__init__()
        self.filemanager = filemanager
        self._metadata_cache: Dict[int, Dict[str, Dict[int, str]]] = {}  # plate_id → metadata

    def _get_omero_conn(self):
        """
        Get OMERO connection from backend registry.

        Retrieves the connection from the OMERO backend instance in the registry,
        using the backend's _get_connection() method which handles lazy connection
        management for multiprocessing compatibility.

        Returns:
            BlitzGateway connection instance

        Raises:
            RuntimeError: If OMERO backend cannot provide a connection
        """
        # Get OMERO backend from registry (via filemanager)
        omero_backend = self.filemanager.registry[Backend.OMERO_LOCAL.value]

        # Use the backend's connection retrieval method
        # This handles lazy connection management and multiprocessing
        try:
            conn = omero_backend._get_connection()
            return conn
        except Exception as e:
            raise RuntimeError(
                f"Failed to get OMERO connection from backend: {e}. "
                "Ensure OMERO backend is properly initialized with connection."
            ) from e

    def _load_plate_metadata(self, plate_id: int) -> Dict[str, Dict[int, str]]:
        """
        Load all metadata for a plate in one OMERO query (cached).

        Queries OMERO once per plate and caches results.
        Subsequent calls return cached data.
        """
        if plate_id in self._metadata_cache:
            return self._metadata_cache[plate_id]

        # Get connection from backend registry
        conn = self._get_omero_conn()
        
        plate = conn.getObject("Plate", plate_id)
        if not plate:
            raise ValueError(f"OMERO Plate not found: {plate_id}")

        # Query OMERO once for all metadata
        metadata = {}

        # Get metadata from all wells to ensure complete coverage
        # (different wells might have different dimensions)
        all_channels = {}
        max_z = 0
        max_t = 0

        for well in plate.listChildren():
            well_sample = well.getWellSample(0)
            if well_sample:
                image = well_sample.getImage()

                # Collect channel names
                for i, channel in enumerate(image.getChannels()):
                    channel_idx = i + 1
                    if channel_idx not in all_channels:
                        all_channels[channel_idx] = channel.getLabel() or f"Channel {channel_idx}"

                # Track max dimensions
                max_z = max(max_z, image.getSizeZ())
                max_t = max(max_t, image.getSizeT())

        # Build metadata dict
        metadata['channel'] = all_channels
        metadata['z_index'] = {z + 1: f"Z{z + 1}" for z in range(max_z)}
        metadata['timepoint'] = {t + 1: f"T{t + 1}" for t in range(max_t)}

        # Cache it
        self._metadata_cache[plate_id] = metadata
        return metadata

    def find_metadata_file(self, plate_path: Union[str, Path]) -> Optional[Path]:
        """
        OMERO doesn't use metadata files, but detects based on /omero/ path pattern.

        Returns the plate_path itself if it matches the OMERO virtual path pattern,
        otherwise returns None.
        """
        plate_path = Path(plate_path)
        # OMERO plates use virtual paths like /omero/plate_123
        if str(plate_path).startswith('/omero/plate_'):
            return plate_path
        return None

    def _extract_plate_id(self, plate_path: Union[str, Path, int]) -> int:
        """
        Extract plate_id from various path formats.

        Handles:
        - int: plate_id directly
        - Path('/omero/plate_57'): extracts 57 from 'plate_57'
        - Path('/omero/plate_57_outputs'): extracts 57 from 'plate_57_outputs'

        Args:
            plate_path: Plate identifier (int or Path)

        Returns:
            Plate ID as integer

        Raises:
            ValueError: If path format is invalid
        """
        if isinstance(plate_path, int):
            return plate_path

        # Extract from path: /omero/plate_57 or /omero/plate_57_outputs
        path_str = str(Path(plate_path).name)  # Get just the filename part

        # Match 'plate_<id>' or 'plate_<id>_<suffix>'
        match = re.match(r'plate_(\d+)', path_str)
        if not match:
            raise ValueError(f"Invalid OMERO path format: {plate_path}. Expected /omero/plate_<id> or /omero/plate_<id>_<suffix>")

        return int(match.group(1))

    def get_channel_values(self, plate_path: Union[str, Path, int]) -> Dict[int, str]:
        """Get channel metadata (cached)."""
        plate_id = self._extract_plate_id(plate_path)
        metadata = self._load_plate_metadata(plate_id)
        return metadata.get('channel', {})

    def get_z_index_values(self, plate_path: Union[str, Path, int]) -> Dict[int, str]:
        """Get Z-index metadata (cached)."""
        plate_id = self._extract_plate_id(plate_path)
        metadata = self._load_plate_metadata(plate_id)
        return metadata.get('z_index', {})

    def get_timepoint_values(self, plate_path: Union[str, Path, int]) -> Dict[int, str]:
        """Get timepoint metadata (cached)."""
        plate_id = self._extract_plate_id(plate_path)
        metadata = self._load_plate_metadata(plate_id)
        return metadata.get('timepoint', {})

    # Other component methods return empty dicts (not applicable for OMERO)
    def get_site_values(self, plate_path: Union[str, Path, int]) -> Dict[int, str]:
        return {}

    def get_well_values(self, plate_path: Union[str, Path, int]) -> Dict[str, str]:
        return {}

    def get_grid_dimensions(self, plate_path: Union[str, Path, int]) -> Tuple[int, int]:
        """
        Extract grid dimensions from OMERO plate metadata.

        Grid dimensions should be stored in the plate's MapAnnotation under
        the key "openhcs.grid_dimensions" as "rows,cols" (e.g., "2,2").

        Returns:
            Tuple of (rows, cols) representing the grid dimensions
        """
        plate_id = self._extract_plate_id(plate_path)

        try:
            conn = self._get_omero_conn()
            plate = conn.getObject("Plate", plate_id)

            if not plate:
                logger.warning(f"Plate {plate_id} not found, using fallback grid_dimensions")
                return self.FALLBACK_VALUES.get('grid_dimensions', (1, 1))

            # Try to get grid dimensions from MapAnnotation
            for ann in plate.listAnnotations():
                if ann.OMERO_TYPE == omero.model.MapAnnotationI:
                    if ann.getNs() == "openhcs.metadata":
                        # Parse key-value pairs
                        for nv in ann.getMapValue():
                            if nv.name == "openhcs.grid_dimensions":
                                # Parse "rows,cols" format
                                rows, cols = map(int, nv.value.split(','))
                                logger.info(f"Found grid_dimensions ({rows}, {cols}) in OMERO metadata")
                                return (rows, cols)

            # Grid dimensions not found in metadata
            logger.warning(f"Grid dimensions not found in OMERO metadata for plate {plate_id}, using fallback")
            return self.FALLBACK_VALUES.get('grid_dimensions', (1, 1))

        except Exception as e:
            logger.warning(f"Error extracting grid_dimensions from OMERO: {e}")
            return self.FALLBACK_VALUES.get('grid_dimensions', (1, 1))

    def get_pixel_size(self, plate_path: Union[str, Path, int]) -> float:
        """
        Get pixel size from OMERO image metadata.

        Queries the first image in the plate for pixel size.
        Falls back to DEFAULT_PIXEL_SIZE if not available.
        """
        try:
            plate_id = plate_path if isinstance(plate_path, int) else int(Path(plate_path).name)
            conn = self._get_omero_conn()
            plate = conn.getObject("Plate", plate_id)

            if plate:
                # Get first well's first image
                for well in plate.listChildren():
                    well_sample = well.getWellSample(0)
                    if well_sample:
                        image = well_sample.getImage()
                        pixels = image.getPrimaryPixels()
                        # Get physical pixel size in micrometers
                        pixel_size_x = pixels.getPhysicalSizeX()
                        if pixel_size_x:
                            return float(pixel_size_x)
                        break
        except Exception:
            pass

        # Fallback to default
        return self.FALLBACK_VALUES.get('pixel_size', 1.0)

    def get_image_files(self, plate_path: Union[str, Path, int]) -> List[str]:
        """
        Get list of virtual filenames from OMERO backend.

        Delegates to OMEROLocalBackend.list_files() to generate virtual filenames.
        """
        plate_id = plate_path if isinstance(plate_path, int) else int(Path(plate_path).name)

        # Get OMERO backend from registry
        omero_backend = self.filemanager.registry[Backend.OMERO_LOCAL.value]

        # Call list_files with plate_id to get virtual filenames
        virtual_files = omero_backend.list_files(str(plate_id), plate_id=plate_id)

        # Return just the basenames (they're already basenames from backend)
        return [Path(f).name for f in virtual_files]


class OMEROFilenameParser(FilenameParser):
    """
    Parser for OMERO virtual filenames.

    OMERO backend generates filenames in standard format with ALL components:
    A01_s001_w1_z001_t001.tif

    This is compatible with ImageXpress format, but OMERO always includes
    all components (well, site, channel, z_index, timepoint) since it knows
    the full plate structure from OMERO metadata.

    For now, this just uses the ImageXpress pattern since they're compatible.
    In the future, this could enforce that all components are present.
    """

    # Use ImageXpress pattern - it's compatible
    from openhcs.microscopes.imagexpress import ImageXpressFilenameParser
    _pattern = ImageXpressFilenameParser._pattern

    @classmethod
    def can_parse(cls, filename: str) -> bool:
        """Check if this parser can parse the given filename."""
        return cls._pattern.match(filename) is not None

    def parse_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Parse OMERO virtual filename using ImageXpress pattern."""
        from openhcs.microscopes.imagexpress import ImageXpressFilenameParser
        parser = ImageXpressFilenameParser()
        return parser.parse_filename(filename)

    def construct_filename(self, well, site, channel, z_index, timepoint, extension='.tif', **kwargs) -> str:
        """
        Construct OMERO virtual filename.

        OMERO always generates complete filenames with all components.
        """
        from openhcs.microscopes.imagexpress import ImageXpressFilenameParser
        parser = ImageXpressFilenameParser()
        return parser.construct_filename(
            well=well,
            site=site,
            channel=channel,
            z_index=z_index,
            timepoint=timepoint,
            extension=extension,
            **kwargs
        )

    def extract_component_coordinates(self, component_value: str) -> Tuple[str, str]:
        """Extract coordinates from well identifier (e.g., 'A01' → ('A', '01'))."""
        from openhcs.microscopes.imagexpress import ImageXpressFilenameParser
        parser = ImageXpressFilenameParser()
        return parser.extract_component_coordinates(component_value)


class OMEROHandler(MicroscopeHandler):
    """OMERO microscope handler - uses OMERO native metadata."""

    _microscope_type = 'omero'
    _metadata_handler_class = None  # Set after class definition

    def __init__(self, filemanager: FileManager, pattern_format: Optional[str] = None):
        """
        Initialize OMERO handler.

        OMERO uses OMEROFilenameParser to parse virtual filenames generated by the backend.
        The orchestrator needs the parser to extract components from filenames.

        Args:
            filemanager: FileManager with OMERO backend in registry
            pattern_format: Unused for OMERO (included for interface compatibility)
        """
        parser = OMEROFilenameParser()
        metadata_handler = OMEROMetadataHandler(filemanager)
        super().__init__(parser=parser, metadata_handler=metadata_handler)

    @property
    def common_dirs(self) -> List[str]:
        """Virtual subdirectory for OMERO (purely for path compatibility)."""
        return ["Images"]

    @property
    def microscope_type(self) -> str:
        return "omero"

    @property
    def metadata_handler_class(self) -> Type[MetadataHandler]:
        """Metadata handler class (for interface enforcement only)."""
        return OMEROMetadataHandler

    @property
    def compatible_backends(self) -> List[Backend]:
        """OMERO is only compatible with OMERO_LOCAL backend."""
        return [Backend.OMERO_LOCAL]

    def _prepare_workspace(self, workspace_path: Path, filemanager: FileManager) -> Path:
        """
        OMERO doesn't need workspace preparation - it's a virtual filesystem.

        Args:
            workspace_path: Path to workspace (unused for OMERO)
            filemanager: FileManager instance (unused for OMERO)

        Returns:
            workspace_path unchanged
        """
        return workspace_path

    def initialize_workspace(self, plate_path: Union[int, Path], workspace_path: Optional[Path], filemanager: FileManager) -> Path:
        """
        OMERO creates a virtual path for the plate.

        For OMERO, plate_path is an int (plate_id). We convert it to a virtual
        Path like "/omero/plate_54/Images" that can be used throughout the system.
        The backend extracts the plate_id from this virtual path when needed.

        Args:
            plate_path: OMERO plate_id (int) or Path (for compatibility)
            workspace_path: Unused for OMERO
            filemanager: Unused for OMERO

        Returns:
            Virtual Path for OMERO plate (e.g., "/omero/plate_54/Images")
        """
        # Convert int plate_id to virtual path
        if isinstance(plate_path, int):
            # Create virtual path: /omero/plate_{id}/Images
            virtual_path = Path(f"/omero/plate_{plate_path}/Images")
            return virtual_path
        else:
            # Already a Path (shouldn't happen for OMERO, but handle it)
            return plate_path


# Set metadata handler class after class definition for automatic registration
from openhcs.microscopes.microscope_base import register_metadata_handler
OMEROHandler._metadata_handler_class = OMEROMetadataHandler
register_metadata_handler(OMEROHandler, OMEROMetadataHandler)

