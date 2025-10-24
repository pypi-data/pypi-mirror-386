"""
Opera Phenix microscope implementations for openhcs.

This module provides concrete implementations of FilenameParser and MetadataHandler
for Opera Phenix microscopes.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, Tuple

from openhcs.constants.constants import Backend
from openhcs.microscopes.opera_phenix_xml_parser import OperaPhenixXmlParser
from openhcs.io.filemanager import FileManager
from openhcs.io.metadata_writer import AtomicMetadataWriter
from openhcs.microscopes.microscope_base import MicroscopeHandler
from openhcs.microscopes.microscope_interfaces import (FilenameParser,
                                                            MetadataHandler)

logger = logging.getLogger(__name__)



class OperaPhenixHandler(MicroscopeHandler):
    """
    MicroscopeHandler implementation for Opera Phenix systems.

    This handler combines the OperaPhenix filename parser with its
    corresponding metadata handler. It guarantees aligned behavior
    for plate structure parsing, metadata extraction, and any optional
    post-processing steps required after workspace setup.
    """

    # Explicit microscope type for proper registration
    _microscope_type = 'opera_phenix'

    # Class attribute for automatic metadata handler registration (set after class definition)
    _metadata_handler_class = None

    def __init__(self, filemanager: FileManager, pattern_format: Optional[str] = None):
        self.parser = OperaPhenixFilenameParser(filemanager, pattern_format=pattern_format)
        self.metadata_handler = OperaPhenixMetadataHandler(filemanager)
        super().__init__(parser=self.parser, metadata_handler=self.metadata_handler)

    @property
    def common_dirs(self) -> List[str]:
        """Subdirectory names commonly used by Opera Phenix."""
        return ['Images']

    @property
    def microscope_type(self) -> str:
        """Microscope type identifier (for interface enforcement only)."""
        return 'opera_phenix'

    @property
    def metadata_handler_class(self) -> Type[MetadataHandler]:
        """Metadata handler class (for interface enforcement only)."""
        return OperaPhenixMetadataHandler

    @property
    def compatible_backends(self) -> List[Backend]:
        """
        Opera Phenix is compatible with DISK backend only.

        Legacy microscope format with standard file operations.
        """
        return [Backend.DISK]



    # Uses default workspace initialization from base class

    def _build_virtual_mapping(self, plate_path: Path, filemanager: FileManager) -> Path:
        """
        Build Opera Phenix virtual workspace mapping using plate-relative paths.

        Args:
            plate_path: Path to plate directory
            filemanager: FileManager instance for file operations

        Returns:
            Path to image directory
        """
        plate_path = Path(plate_path)  # Ensure Path object

        logger.info(f"🔄 BUILDING VIRTUAL MAPPING: Opera Phenix field remapping for {plate_path}")

        # Find the image directory using the common_dirs property
        entries = filemanager.list_dir(plate_path, Backend.DISK.value)

        # Look for a directory matching any of the common_dirs patterns
        image_dir = plate_path
        for entry in entries:
            entry_lower = entry.lower()
            if any(common_dir.lower() in entry_lower for common_dir in self.common_dirs):
                # Found a matching directory
                image_dir = Path(plate_path) / entry
                logger.info("Found directory matching common_dirs pattern: %s", image_dir)
                break

        # Default to empty field mapping (no remapping)
        field_mapping = {}

        # Try to load field mapping from Index.xml if available
        xml_parser = None
        try:
            index_xml = filemanager.find_file_recursive(plate_path, "Index.xml", Backend.DISK.value)
            if index_xml:
                xml_parser = OperaPhenixXmlParser(index_xml)
                field_mapping = xml_parser.get_field_id_mapping()
                logger.debug("Loaded field mapping from Index.xml: %s", field_mapping)
            else:
                logger.debug("Index.xml not found. Using default field mapping.")
        except Exception as e:
            logger.error("Error loading Index.xml: %s", e)
            logger.debug("Using default field mapping due to error.")

        # Fill missing images BEFORE building virtual mapping
        # This handles autofocus failures by creating black placeholder images
        if xml_parser:
            num_filled = self._fill_missing_images(image_dir, xml_parser, filemanager)
            if num_filled > 0:
                logger.info(f"Created {num_filled} placeholder images for autofocus failures")

        # Get all image files in the directory (including newly created placeholders)
        image_files = filemanager.list_image_files(image_dir, Backend.DISK.value)

        # Initialize mapping dict (PLATE-RELATIVE paths)
        workspace_mapping = {}

        # Process each file
        for file_path in image_files:
            # FileManager should return strings, but handle Path objects too
            if isinstance(file_path, str):
                file_name = os.path.basename(file_path)
            elif isinstance(file_path, Path):
                file_name = file_path.name
            else:
                # Skip any unexpected types
                logger.warning("Unexpected file path type: %s", type(file_path).__name__)
                continue

            # Parse file metadata
            metadata = self.parser.parse_filename(file_name)
            if not metadata or 'site' not in metadata or metadata['site'] is None:
                continue

            # Remap the field ID using the spatial layout
            original_field_id = metadata['site']
            new_field_id = field_mapping.get(original_field_id, original_field_id)

            # Construct the new filename with proper padding
            metadata['site'] = new_field_id  # Update site with remapped value
            new_name = self.parser.construct_filename(**metadata)

            # Build PLATE-RELATIVE mapping (no workspace directory)
            virtual_relative = str(Path("Images") / new_name)
            real_relative = str(Path("Images") / file_name)
            workspace_mapping[virtual_relative] = real_relative

        logger.info(f"Built {len(workspace_mapping)} virtual path mappings for Opera Phenix")

        # Save virtual workspace mapping to metadata using EXISTING method
        metadata_path = plate_path / "openhcs_metadata.json"
        writer = AtomicMetadataWriter()
        writer.merge_subdirectory_metadata(metadata_path, {
            "Images": {
                "workspace_mapping": workspace_mapping,  # Plate-relative paths
                "available_backends": {"disk": True, "virtual_workspace": True}
            }
        })

        logger.info(f"✅ Saved virtual workspace mapping to {metadata_path}")

        return image_dir

    def _fill_missing_images(
        self,
        image_dir: Path,
        xml_parser: OperaPhenixXmlParser,
        filemanager: FileManager
    ) -> int:
        """
        Fill in missing images with black pixels for wells where autofocus failed.

        Opera Phenix autofocus failures result in missing images. This method:
        1. Extracts expected image structure from Index.xml
        2. Compares with actual files in workspace
        3. Creates black (zero-filled) images for missing files

        Args:
            image_dir: Path to the image directory
            xml_parser: Parsed Index.xml
            filemanager: FileManager for file operations

        Returns:
            Number of missing images created
        """
        import numpy as np

        logger.debug("Checking for missing images in Opera Phenix workspace")

        # 1. Get expected images from XML
        try:
            image_info = xml_parser.get_image_info()
            field_mapping = xml_parser.get_field_id_mapping()
        except Exception as e:
            logger.warning(f"Could not extract image info from XML: {e}")
            return 0

        # 2. Build set of expected filenames (with remapped field IDs)
        expected_files = set()
        for img_id, img_data in image_info.items():
            # Remap field ID
            original_field = img_data['field_id']
            remapped_field = xml_parser.remap_field_id(original_field, field_mapping)

            # Construct filename
            well = f"R{img_data['row']:02d}C{img_data['col']:02d}"

            # Note: plane_id in XML corresponds to z_index in filenames
            # For timepoint, we default to 1 as XML doesn't always have explicit timepoint info
            filename = self.parser.construct_filename(
                well=well,
                site=remapped_field,
                channel=img_data['channel_id'],
                z_index=img_data['plane_id'],
                timepoint=1,  # Default timepoint
                extension='.tiff'
            )
            expected_files.add(filename)

        # 3. Get actual files (excluding broken symlinks)
        # Clause 245: Workspace operations are disk-only by design
        actual_file_paths = filemanager.list_image_files(image_dir, Backend.DISK.value)
        actual_files = set()
        for file_path in actual_file_paths:
            # Check if file is a broken symlink
            file_path_obj = Path(file_path)
            if file_path_obj.is_symlink() and not file_path_obj.exists():
                # Broken symlink - treat as missing
                logger.debug(f"Found broken symlink (will be replaced): {file_path}")
                continue
            actual_files.add(os.path.basename(file_path))

        # 4. Find missing files
        missing_files = expected_files - actual_files

        if not missing_files:
            logger.debug("No missing images detected")
            return 0

        logger.info(f"Found {len(missing_files)} missing images (likely autofocus failures)")

        # 5. Get image dimensions from first existing image
        if actual_file_paths:
            try:
                first_image_path = actual_file_paths[0]
                # Clause 245: Workspace operations are disk-only by design
                first_image = filemanager.load(first_image_path, Backend.DISK.value)
                height, width = first_image.shape
                dtype = first_image.dtype
                logger.debug(f"Using dimensions from existing image: {height}x{width}, dtype={dtype}")
            except Exception as e:
                logger.warning(f"Could not load existing image for dimensions: {e}")
                # Default dimensions for Opera Phenix
                height, width = 2160, 2160
                dtype = np.uint16
                logger.debug(f"Using default dimensions: {height}x{width}, dtype={dtype}")
        else:
            # Default dimensions for Opera Phenix
            height, width = 2160, 2160
            dtype = np.uint16
            logger.debug(f"No existing images, using default dimensions: {height}x{width}, dtype={dtype}")

        # 6. Create black images for missing files
        black_image = np.zeros((height, width), dtype=dtype)

        for filename in missing_files:
            output_path = image_dir / filename
            # Clause 245: Workspace operations are disk-only by design
            filemanager.save(black_image, output_path, Backend.DISK.value)
            logger.debug(f"Created missing image: {filename}")

        logger.info(f"Successfully created {len(missing_files)} missing images with black pixels")
        return len(missing_files)


class OperaPhenixFilenameParser(FilenameParser):
    """Parser for Opera Phenix microscope filenames.

    Handles Opera Phenix format filenames like:
    - r01c01f001p01-ch1sk1fk1fl1.tiff
    - r01c01f001p01-ch1.tiff
    """

    # Regular expression pattern for Opera Phenix filenames
    # Supports: row, column, site (field), z_index (plane), channel, timepoint (sk=stack)
    # sk = stack/timepoint, fk = field stack, fl = focal level
    # Also supports result files with suffixes like: r01c01f001p01-ch1_cell_counts_step7.json
    _pattern = re.compile(r"r(\d{1,2})c(\d{1,2})f(\d+|\{[^\}]*\})p(\d+|\{[^\}]*\})-ch(\d+|\{[^\}]*\})(?:sk(\d+|\{[^\}]*\}))?(?:fk\d+)?(?:fl\d+)?(?:_.*?)?(\.\w+)$", re.I)

    # Pattern for extracting row and column from Opera Phenix well format
    _well_pattern = re.compile(r"R(\d{2})C(\d{2})", re.I)

    def __init__(self, filemanager=None, pattern_format=None):
        """
        Initialize the parser.

        Args:
            filemanager: FileManager instance (not used, but required for interface compatibility)
            pattern_format: Optional pattern format (not used, but required for interface compatibility)
        """
        super().__init__()  # Initialize the generic parser interface

        # These parameters are not used by this parser, but are required for interface compatibility
        self.filemanager = filemanager
        self.pattern_format = pattern_format

    @classmethod
    def can_parse(cls, filename: str) -> bool:
        """
        Check if this parser can parse the given filename.

        Args:
            filename (str): Filename to check

        Returns:
            bool: True if this parser can parse the filename, False otherwise
        """
        # 🔒 Clause 17 — VFS Boundary Method
        # This is a string operation that doesn't perform actual file I/O
        # Extract just the basename
        basename = os.path.basename(filename)
        # Check if the filename matches the Opera Phenix pattern
        return bool(cls._pattern.match(basename))

    def parse_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Parse an Opera Phenix filename to extract all components.
        Supports placeholders like {iii} which will return None for that field.

        Args:
            filename (str): Filename to parse

        Returns:
            dict or None: Dictionary with extracted components or None if parsing fails.
        """
        # 🔒 Clause 17 — VFS Boundary Method
        # This is a string operation that doesn't perform actual file I/O
        basename = os.path.basename(filename)
        logger.debug("OperaPhenixFilenameParser attempting to parse basename: '%s'", basename)

        # Try parsing using the Opera Phenix pattern
        match = self._pattern.match(basename)
        if match:
            logger.debug("Regex match successful for '%s'", basename)
            row, col, site_str, z_str, channel_str, sk_str, ext = match.groups()

            # Helper function to parse component strings
            def parse_comp(s):
                """Parse component string to int or None if it's a placeholder."""
                if not s or '{' in s:
                    return None
                return int(s)

            # Create well ID from row and column
            well = f"R{int(row):02d}C{int(col):02d}"

            # Parse components
            site = parse_comp(site_str)
            channel = parse_comp(channel_str)
            z_index = parse_comp(z_str)
            timepoint = parse_comp(sk_str)  # sk = stack/timepoint

            result = {
                'well': well,
                'site': site,
                'channel': channel,
                'wavelength': channel,  # For backward compatibility
                'z_index': z_index,
                'timepoint': timepoint,  # sk = stack/timepoint
                'extension': ext if ext else '.tif'
            }
            return result

        logger.warning("Regex match failed for basename: '%s'", basename)
        return None

    def construct_filename(self, extension: str = '.tiff', site_padding: int = 3, z_padding: int = 3, **component_values) -> str:
        """
        Construct an Opera Phenix filename from components.

        This method now uses **kwargs to accept any component values dynamically,
        making it compatible with the generic parser interface.

        Note: Opera Phenix uses 'sk' (stack) for timepoint in filenames.

        Args:
            extension (str, optional): File extension (default: '.tiff')
            site_padding (int, optional): Width to pad site numbers to (default: 3)
            z_padding (int, optional): Width to pad Z-index numbers to (default: 3)
            **component_values: Component values as keyword arguments.
                               Expected keys: well, site, channel, z_index, timepoint

        Returns:
            str: Constructed filename
        """
        # Extract components from kwargs
        well = component_values.get('well')
        site = component_values.get('site')
        channel = component_values.get('channel')
        z_index = component_values.get('z_index')
        timepoint = component_values.get('timepoint')

        if not well:
            raise ValueError("Well component is required for filename construction")

        # Extract row and column from well name
        # Check if well is in Opera Phenix format (e.g., 'R01C03')
        match = self._well_pattern.match(well)
        if match:
            # Extract row and column from Opera Phenix format
            row = int(match.group(1))
            col = int(match.group(2))
        else:
            raise ValueError(f"Invalid well format: {well}. Expected format: 'R01C03'")

        # Default Z-index and timepoint to 1 if not provided
        z_index = 1 if z_index is None else z_index
        channel = 1 if channel is None else channel
        timepoint = 1 if timepoint is None else timepoint

        # Construct filename in Opera Phenix format
        if isinstance(site, str):
            # If site is a string (e.g., '{iii}'), use it directly
            site_part = f"f{site}"
        else:
            # Otherwise, format it as a padded integer
            site_part = f"f{site:0{site_padding}d}"

        if isinstance(z_index, str):
            # If z_index is a string (e.g., '{zzz}'), use it directly
            z_part = f"p{z_index}"
        else:
            # Otherwise, format it as a padded integer
            z_part = f"p{z_index:0{z_padding}d}"

        # Always include sk (stack/timepoint) - like ImageXpress always includes _t
        if isinstance(timepoint, str):
            sk_part = f"sk{timepoint}"
        else:
            sk_part = f"sk{timepoint}"

        return f"r{row:02d}c{col:02d}{site_part}{z_part}-ch{channel}{sk_part}fk1fl1{extension}"

    def remap_field_in_filename(self, filename: str, xml_parser: Optional[OperaPhenixXmlParser] = None) -> str:
        """
        Remap the field ID in a filename to follow a top-left to bottom-right pattern.

        Args:
            filename: Original filename
            xml_parser: Parser with XML data

        Returns:
            str: New filename with remapped field ID
        """
        if xml_parser is None:
            return filename

        # Parse the filename
        metadata = self.parse_filename(filename)
        if not metadata or 'site' not in metadata or metadata['site'] is None:
            return filename

        # Get the mapping and remap the field ID
        mapping = xml_parser.get_field_id_mapping()
        new_field_id = xml_parser.remap_field_id(metadata['site'], mapping)

        # Always create a new filename with the remapped field ID and consistent padding
        # This ensures all filenames have the same format, even if the field ID didn't change
        metadata['site'] = new_field_id  # Update site with remapped value
        return self.construct_filename(**metadata)

    def extract_component_coordinates(self, component_value: str) -> Tuple[str, str]:
        """
        Extract coordinates from component identifier (typically well).

        Args:
            component_value (str): Component identifier (e.g., 'R03C04' or 'A01')

        Returns:
            Tuple[str, str]: (row, column) where row is like 'A', 'B' and column is like '01', '04'

        Raises:
            ValueError: If component format is invalid
        """
        if not component_value:
            raise ValueError(f"Invalid component format: {component_value}")

        # Check if component is in Opera Phenix format (e.g., 'R01C03')
        match = self._well_pattern.match(component_value)
        if match:
            # Extract row and column from Opera Phenix format
            row_num = int(match.group(1))
            col_num = int(match.group(2))
            # Convert to letter-number format: R01C03 -> A, 03
            row = chr(ord('A') + row_num - 1)  # R01 -> A, R02 -> B, etc.
            col = f"{col_num:02d}"  # Ensure 2-digit padding
            return row, col
        else:
            # Assume simple format like 'A01', 'C04'
            if len(component_value) < 2:
                raise ValueError(f"Invalid component format: {component_value}")
            row = component_value[0]
            col = component_value[1:]
            if not row.isalpha() or not col.isdigit():
                raise ValueError(f"Invalid Opera Phenix component format: {component_value}. Expected 'R01C03' or 'A01' format")
            return row, col


class OperaPhenixMetadataHandler(MetadataHandler):
    """
    Metadata handler for Opera Phenix microscopes.

    Handles finding and parsing Index.xml files for Opera Phenix microscopes.
    """
    # Microscope-specific directory structure constants
    COMMON_DIRS = ['Images']      # Subdirectories where images are typically stored
    WORKSPACE_DIR = 'workspace'   # Workspace directory name (created by initialize_workspace)

    def __init__(self, filemanager: FileManager):
        """
        Initialize the metadata handler.

        Args:
            filemanager: FileManager instance for file operations.
        """
        super().__init__()
        self.filemanager = filemanager

    # Legacy mode has been completely purged

    def find_metadata_file(self, plate_path: Union[str, Path]):
        """
        Find the Index.xml file in the plate directory.

        Args:
            plate_path: Path to the plate directory

        Returns:
            Path to the Index.xml file

        Raises:
            FileNotFoundError: If no Index.xml file is found
        """
        # Ensure plate_path is a Path object
        if isinstance(plate_path, str):
            plate_path = Path(plate_path)

        # Ensure the path exists
        if not plate_path.exists():
            raise FileNotFoundError(f"Plate path does not exist: {plate_path}")

        # Check for Index.xml in the plate directory
        index_xml = plate_path / "Index.xml"
        if index_xml.exists():
            return index_xml

        # Check for Index.xml in the Images directory
        images_dir = plate_path / "Images"
        if images_dir.exists():
            index_xml = images_dir / "Index.xml"
            if index_xml.exists():
                return index_xml

        # No recursive search - only check root and Images directories
        raise FileNotFoundError(
            f"Index.xml not found in {plate_path} or {plate_path}/Images. "
            "Opera Phenix metadata requires Index.xml file."
        )

        # Ensure result is a Path object
        if isinstance(result, str):
            return Path(result)
        if isinstance(result, Path):
            return result
        # This should not happen if FileManager is properly implemented
        logger.warning("Unexpected result type from find_file_recursive: %s", type(result).__name__)
        return Path(str(result))

    def get_grid_dimensions(self, plate_path: Union[str, Path]):
        """
        Get grid dimensions for stitching from Index.xml file.

        Args:
            plate_path: Path to the plate folder

        Returns:
            Tuple of (grid_rows, grid_cols) - UPDATED: Now returns (rows, cols) for MIST compatibility

        Raises:
            FileNotFoundError: If no Index.xml file is found
            OperaPhenixXmlParseError: If the XML cannot be parsed
            OperaPhenixXmlContentError: If grid dimensions cannot be determined
        """
        # Ensure plate_path is a Path object
        if isinstance(plate_path, str):
            plate_path = Path(plate_path)

        # Ensure the path exists
        if not plate_path.exists():
            raise FileNotFoundError(f"Plate path does not exist: {plate_path}")

        # Find the Index.xml file - this will raise FileNotFoundError if not found
        index_xml = self.find_metadata_file(plate_path)

        # Use the OperaPhenixXmlParser to get the grid size
        # This will raise appropriate exceptions if parsing fails
        xml_parser = self.create_xml_parser(index_xml)
        grid_size = xml_parser.get_grid_size()

        # Validate the grid size
        if grid_size[0] <= 0 or grid_size[1] <= 0:
            raise ValueError(
                f"Invalid grid dimensions: {grid_size[0]}x{grid_size[1]}. "
                "Grid dimensions must be positive integers."
            )

        logger.info("Grid size from Index.xml: %dx%d (cols x rows)", grid_size[0], grid_size[1])
        # FIXED: Return (rows, cols) for MIST compatibility instead of (cols, rows)
        return (grid_size[1], grid_size[0])

    def get_pixel_size(self, plate_path: Union[str, Path]):
        """
        Get the pixel size from Index.xml file.

        Args:
            plate_path: Path to the plate folder

        Returns:
            Pixel size in micrometers

        Raises:
            FileNotFoundError: If no Index.xml file is found
            OperaPhenixXmlParseError: If the XML cannot be parsed
            OperaPhenixXmlContentError: If pixel size cannot be determined
        """
        # Ensure plate_path is a Path object
        if isinstance(plate_path, str):
            plate_path = Path(plate_path)

        # Ensure the path exists
        if not plate_path.exists():
            raise FileNotFoundError(f"Plate path does not exist: {plate_path}")

        # Find the Index.xml file - this will raise FileNotFoundError if not found
        index_xml = self.find_metadata_file(plate_path)

        # Use the OperaPhenixXmlParser to get the pixel size
        # This will raise appropriate exceptions if parsing fails
        xml_parser = self.create_xml_parser(index_xml)
        pixel_size = xml_parser.get_pixel_size()

        # Validate the pixel size
        if pixel_size <= 0:
            raise ValueError(
                f"Invalid pixel size: {pixel_size}. "
                "Pixel size must be a positive number."
            )

        logger.info("Pixel size from Index.xml: %.4f μm", pixel_size)
        return pixel_size

    def get_channel_values(self, plate_path: Union[str, Path]) -> Optional[Dict[str, Optional[str]]]:
        """
        Get channel key→name mapping from Opera Phenix Index.xml.

        Args:
            plate_path: Path to the plate folder (str or Path)

        Returns:
            Dict mapping channel IDs to channel names from metadata
            Example: {"1": "HOECHST 33342", "2": "Calcein", "3": "Alexa 647"}
        """
        try:
            # Ensure plate_path is a Path object
            if isinstance(plate_path, str):
                plate_path = Path(plate_path)

            # Find and parse Index.xml
            index_xml = self.find_metadata_file(plate_path)
            xml_parser = self.create_xml_parser(index_xml)

            # Extract channel information
            channel_mapping = {}

            # Look for channel entries in the XML
            # Opera Phenix stores channel info in multiple places, try the most common
            root = xml_parser.root
            namespace = xml_parser.namespace

            # Find channel entries with ChannelName elements
            channel_entries = root.findall(f".//{namespace}Entry[@ChannelID]")
            for entry in channel_entries:
                channel_id = entry.get('ChannelID')
                channel_name_elem = entry.find(f"{namespace}ChannelName")

                if channel_id and channel_name_elem is not None:
                    channel_name = channel_name_elem.text
                    if channel_name:
                        channel_mapping[channel_id] = channel_name

            return channel_mapping if channel_mapping else None

        except Exception as e:
            logger.debug(f"Could not extract channel names from Opera Phenix metadata: {e}")
            return None

    def get_well_values(self, plate_path: Union[str, Path]) -> Optional[Dict[str, Optional[str]]]:
        """
        Get well key→name mapping from Opera Phenix metadata.

        Args:
            plate_path: Path to the plate folder (str or Path)

        Returns:
            None - Opera Phenix doesn't provide rich well names in metadata
        """
        return None

    def get_site_values(self, plate_path: Union[str, Path]) -> Optional[Dict[str, Optional[str]]]:
        """
        Get site key→name mapping from Opera Phenix metadata.

        Args:
            plate_path: Path to the plate folder (str or Path)

        Returns:
            None - Opera Phenix doesn't provide rich site names in metadata
        """
        return None

    def get_z_index_values(self, plate_path: Union[str, Path]) -> Optional[Dict[str, Optional[str]]]:
        """
        Get z_index key→name mapping from Opera Phenix metadata.

        Args:
            plate_path: Path to the plate folder (str or Path)

        Returns:
            None - Opera Phenix doesn't provide rich z_index names in metadata
        """
        return None

    def get_timepoint_values(self, plate_path: Union[str, Path]) -> Optional[Dict[str, Optional[str]]]:
        """
        Get timepoint key→name mapping from Opera Phenix metadata.

        Args:
            plate_path: Path to the plate folder (str or Path)

        Returns:
            None - Opera Phenix doesn't provide rich timepoint names in metadata
        """
        return None

    def get_image_files(self, plate_path: Union[str, Path]) -> List[str]:
        """
        Get list of image files from the Images directory.

        For Opera Phenix, this lists all image files from the Images subdirectory.

        Args:
            plate_path: Path to the plate folder (str or Path)

        Returns:
            List of image filenames (basenames, not full paths)

        Raises:
            TypeError: If plate_path is not a valid path type
            FileNotFoundError: If plate path does not exist
        """
        # Ensure plate_path is a Path object
        if isinstance(plate_path, str):
            plate_path = Path(plate_path)
        elif not isinstance(plate_path, Path):
            raise TypeError(f"Expected str or Path, got {type(plate_path).__name__}")

        # Ensure the path exists
        if not plate_path.exists():
            raise FileNotFoundError(f"Plate path does not exist: {plate_path}")

        # For Opera Phenix, after workspace preparation, images are in workspace/Images
        # Check for workspace subdirectory first (created by MicroscopeHandler.initialize_workspace)
        workspace_dir = plate_path / self.WORKSPACE_DIR

        if workspace_dir.exists() and workspace_dir.is_dir():
            # Look for common_dirs inside workspace
            image_dir = workspace_dir
            for common_dir in self.COMMON_DIRS:
                potential_dir = workspace_dir / common_dir
                if potential_dir.exists() and potential_dir.is_dir():
                    image_dir = potential_dir
                    break
        else:
            # Fallback to plate root or common_dirs subdirectory
            image_dir = plate_path
            for common_dir in self.COMMON_DIRS:
                potential_dir = plate_path / common_dir
                if potential_dir.exists() and potential_dir.is_dir():
                    image_dir = potential_dir
                    break

        # List all image files in the directory
        image_files = self.filemanager.list_image_files(
            image_dir,
            Backend.DISK.value,
            recursive=False
        )

        # Return paths relative to plate_path
        return [str(Path(f).relative_to(plate_path)) for f in image_files]

    def create_xml_parser(self, xml_path: Union[str, Path]):
        """
        Create an OperaPhenixXmlParser for the given XML file.

        Args:
            xml_path: Path to the XML file

        Returns:
            OperaPhenixXmlParser: Parser for the XML file

        Raises:
            FileNotFoundError: If the XML file does not exist
        """
        # Ensure xml_path is a Path object
        if isinstance(xml_path, str):
            xml_path = Path(xml_path)

        # Ensure the path exists
        if not xml_path.exists():
            raise FileNotFoundError(f"XML file does not exist: {xml_path}")

        # Create the parser
        return OperaPhenixXmlParser(xml_path)


# Set metadata handler class after class definition for automatic registration
from openhcs.microscopes.microscope_base import register_metadata_handler
OperaPhenixHandler._metadata_handler_class = OperaPhenixMetadataHandler
register_metadata_handler(OperaPhenixHandler, OperaPhenixMetadataHandler)
