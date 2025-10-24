"""
Display configuration factory for creating viewer-specific config dataclasses.

Provides generic infrastructure for creating display configuration dataclasses
with component-specific dimension modes, supporting both Napari and Fiji viewers.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Callable, Optional, Type


def create_display_config(
    name: str,
    base_fields: Dict[str, tuple[Type, Any]],
    component_mode_enum: Type[Enum],
    component_defaults: Optional[Dict[str, Any]] = None,
    virtual_components: Optional[Type[Enum]] = None,
    component_order: Optional[list[str]] = None,
    default_mode: Optional[Any] = None,
    methods: Optional[Dict[str, Callable]] = None,
    docstring: Optional[str] = None
) -> Type:
    """
    Generic factory for creating display configuration dataclasses.

    Creates a frozen dataclass with:
    - Base fields (e.g., colormap, variable_size_handling)
    - Component-specific mode fields (e.g., channel_mode, z_index_mode, well_mode)
    - Virtual component mode fields (e.g., step_name_mode, source_mode)
    - Custom methods (e.g., get_dimension_mode, get_colormap_name)
    - COMPONENT_ORDER class attribute for canonical layer naming order

    Args:
        name: Name of the dataclass to create
        base_fields: Dict mapping field names to (type, default_value) tuples
        component_mode_enum: Enum class for component dimension modes
        component_defaults: Optional dict mapping component names to default modes
        virtual_components: Optional enum of virtual components (step_name, source, etc.)
        component_order: Canonical order for layer naming (e.g., ['step_name', 'source', 'well', ...])
        default_mode: Default mode for components not specified in component_defaults (required)
        methods: Optional dict mapping method names to method implementations
        docstring: Optional docstring for the created class

    Returns:
        Dynamically created frozen dataclass

    Example:
        >>> NapariDisplayConfig = create_display_config(
        ...     name='NapariDisplayConfig',
        ...     base_fields={
        ...         'colormap': (NapariColormap, NapariColormap.GRAY),
        ...         'variable_size_handling': (NapariVariableSizeHandling, NapariVariableSizeHandling.SEPARATE_LAYERS)
        ...     },
        ...     component_mode_enum=NapariDimensionMode,
        ...     component_defaults={'channel': NapariDimensionMode.SLICE},
        ...     virtual_components=VirtualComponents,
        ...     component_order=['step_name', 'source', 'well', 'channel'],
        ...     methods={'get_colormap_name': lambda self: self.colormap.value}
        ... )
    """
    from openhcs.constants import AllComponents

    # Use AllComponents instead of VariableComponents so display configs include ALL dimensions
    # (including the multiprocessing axis). Display configuration should be independent of
    # multiprocessing axis choice - users should be able to control how wells/any dimension
    # are displayed regardless of which dimension is used for parallelization.
    all_components = list(AllComponents)
    component_defaults = component_defaults or {}

    # Require explicit default_mode - no magic fallbacks
    if default_mode is None:
        raise ValueError("default_mode is required - specify the default mode for unspecified components")

    annotations = {}
    defaults = {}

    for field_name, (field_type, default_value) in base_fields.items():
        annotations[field_name] = field_type
        defaults[field_name] = default_value

    # Generate mode fields for filename components
    for component in all_components:
        field_name = f"{component.value}_mode"
        annotations[field_name] = component_mode_enum
        defaults[field_name] = component_defaults.get(component.value, default_mode)

    # Generate mode fields for virtual components
    if virtual_components:
        for component in virtual_components:
            field_name = f"{component.value}_mode"
            annotations[field_name] = component_mode_enum
            defaults[field_name] = component_defaults.get(component.value, default_mode)

    def __init__(self, **kwargs):
        for field_name, default_value in defaults.items():
            if field_name not in kwargs:
                kwargs[field_name] = default_value
        for field_name, value in kwargs.items():
            object.__setattr__(self, field_name, value)

    class_attrs = {
        '__annotations__': annotations,
        '__init__': __init__,
        '__doc__': docstring or f"Display configuration for {name}",
    }

    for field_name, default_value in defaults.items():
        class_attrs[field_name] = default_value

    # Add component order as class attribute
    if component_order:
        class_attrs['COMPONENT_ORDER'] = component_order

    if methods:
        class_attrs.update(methods)

    DisplayConfig = type(name, (), class_attrs)
    DisplayConfig = dataclass(frozen=True)(DisplayConfig)

    # Set proper module and qualname for pickling support
    DisplayConfig.__module__ = 'openhcs.core.config'
    DisplayConfig.__qualname__ = name

    return DisplayConfig


def create_napari_display_config(
    colormap_enum: Type[Enum],
    dimension_mode_enum: Type[Enum],
    variable_size_handling_enum: Type[Enum],
    virtual_components: Optional[Type[Enum]] = None,
    component_order: Optional[list[str]] = None,
    virtual_component_defaults: Optional[Dict[str, Any]] = None
) -> Type:
    """
    Create NapariDisplayConfig with component-specific fields.

    Args:
        colormap_enum: Enum for colormap options
        dimension_mode_enum: Enum for dimension modes (SLICE/STACK)
        variable_size_handling_enum: Enum for variable size handling
        virtual_components: Optional enum of virtual components (step_name, source, etc.)
        component_order: Canonical order for layer naming
        virtual_component_defaults: Optional dict mapping virtual component names to default modes

    Returns:
        NapariDisplayConfig dataclass
    """
    def get_dimension_mode(self, component):
        if hasattr(component, 'value'):
            component_value = component.value
        elif hasattr(component, 'name'):
            component_value = component.name.lower()
        else:
            component_value = str(component).lower()

        field_name = f"{component_value}_mode"
        mode = getattr(self, field_name, None)

        if mode is None:
            return dimension_mode_enum.SLICE if component_value == 'channel' else dimension_mode_enum.STACK

        return mode

    def get_colormap_name(self):
        return self.colormap.value

    # Merge component defaults
    component_defaults = {'channel': dimension_mode_enum.SLICE}
    if virtual_component_defaults:
        component_defaults.update(virtual_component_defaults)

    return create_display_config(
        name='NapariDisplayConfig',
        base_fields={
            'colormap': (colormap_enum, colormap_enum.GRAY),
            'variable_size_handling': (variable_size_handling_enum, variable_size_handling_enum.SEPARATE_LAYERS),
        },
        component_mode_enum=dimension_mode_enum,
        component_defaults=component_defaults,
        virtual_components=virtual_components,
        component_order=component_order,
        default_mode=dimension_mode_enum.STACK,
        methods={
            'get_dimension_mode': get_dimension_mode,
            'get_colormap_name': get_colormap_name,
        },
        docstring="""Configuration for napari display behavior for all OpenHCS components.

        This class is dynamically generated with individual fields for each component dimension.
        Each component has a corresponding {component}_mode field that controls whether
        it's displayed as a slice or stack in napari.

        Includes ALL dimensions (site, channel, z_index, timepoint, well) regardless of
        which dimension is used as the multiprocessing axis.

        Also includes virtual components (step_name, step_index, source) for streaming contexts.
        """
    )


def create_fiji_display_config(
    lut_enum: Type[Enum],
    dimension_mode_enum: Type[Enum],
    virtual_components: Optional[Type[Enum]] = None,
    component_order: Optional[list[str]] = None,
    virtual_component_defaults: Optional[Dict[str, Any]] = None
) -> Type:
    """
    Create FijiDisplayConfig with component-specific fields.

    Maps OpenHCS dimensions to ImageJ hyperstack dimensions (C, Z, T).
    Default mapping:
    - well → WINDOW (separate windows per well)
    - site → CHANNEL (sites become channels)
    - channel → CHANNEL (channels become channels)
    - z_index → SLICE (z-planes become slices)
    - timepoint → FRAME (timepoints become frames)

    Args:
        lut_enum: Enum for Fiji LUT options
        dimension_mode_enum: Enum for dimension modes (WINDOW/CHANNEL/SLICE/FRAME)
        virtual_components: Optional enum of virtual components (step_name, source, etc.)
        component_order: Canonical order for layer naming
        virtual_component_defaults: Optional dict mapping virtual component names to default modes

    Returns:
        FijiDisplayConfig dataclass
    """
    def get_dimension_mode(self, component):
        if hasattr(component, 'value'):
            component_value = component.value
        elif hasattr(component, 'name'):
            component_value = component.name.lower()
        else:
            component_value = str(component).lower()

        field_name = f"{component_value}_mode"
        mode = getattr(self, field_name, None)

        if mode is None:
            # Default mapping for Fiji hyperstacks
            defaults = {
                'well': dimension_mode_enum.WINDOW,
                'site': dimension_mode_enum.FRAME,
                'channel': dimension_mode_enum.CHANNEL,
                'z_index': dimension_mode_enum.SLICE,
                'timepoint': dimension_mode_enum.FRAME
            }
            return defaults.get(component_value, dimension_mode_enum.CHANNEL)

        return mode

    def get_lut_name(self):
        return self.lut.value

    # Merge component defaults
    component_defaults = {
        'well': dimension_mode_enum.WINDOW,
        'site': dimension_mode_enum.FRAME,
        'channel': dimension_mode_enum.CHANNEL,
        'z_index': dimension_mode_enum.SLICE,
        'timepoint': dimension_mode_enum.FRAME
    }
    if virtual_component_defaults:
        component_defaults.update(virtual_component_defaults)

    return create_display_config(
        name='FijiDisplayConfig',
        base_fields={
            'lut': (lut_enum, lut_enum.GRAYS),
            'auto_contrast': (bool, True),
        },
        component_mode_enum=dimension_mode_enum,
        component_defaults=component_defaults,
        virtual_components=virtual_components,
        component_order=component_order,
        default_mode=dimension_mode_enum.CHANNEL,
        methods={
            'get_dimension_mode': get_dimension_mode,
            'get_lut_name': get_lut_name,
        },
        docstring="""Configuration for Fiji display behavior for all OpenHCS components.

        This class is dynamically generated with individual fields for each component dimension.
        Each component has a corresponding {component}_mode field that controls how it maps
        to ImageJ hyperstack dimensions (WINDOW/CHANNEL/SLICE/FRAME).

        Includes ALL dimensions (site, channel, z_index, timepoint, well) regardless of
        which dimension is used as the multiprocessing axis.

        Also includes virtual components (step_name, step_index, source) for streaming contexts.

        ImageJ hyperstacks have 3 dimensions:
        - Channels (C): Color channels or sites
        - Slices (Z): Z-planes or depth
        - Frames (T): Time points or temporal dimension

        WINDOW mode creates separate windows instead of combining into hyperstack.
        """
    )

