#!/usr/bin/env python3
"""
OpenHCS Pipeline Script - Multi-Subdirectory Test Pipeline
Generated: 2025-10-21 01:49:14.400609
"""

from openhcs.core.pipeline import Pipeline


def create_pipeline():
    """Create and return the pipeline."""

    # Edit this pipeline and save to apply changes
    # Automatically collected imports
    from openhcs.constants.constants import GroupBy, VariableComponents
    from openhcs.constants.input_source import InputSource
    from openhcs.core.config import LazyNapariStreamingConfig, LazyStepMaterializationConfig, LazyStepWellFilterConfig, NapariVariableSizeHandling
    from openhcs.core.memory.decorators import DtypeConversion
    from openhcs.core.steps.function_step import FunctionStep
    from openhcs.processing.backends.analysis.cell_counting_cpu import DetectionMethod, count_cells_single_channel
    from openhcs.processing.backends.assemblers.assemble_stack_cpu import assemble_stack_cpu
    from openhcs.processing.backends.pos_gen.ashlar_main_gpu import ashlar_compute_tile_positions_gpu
    from openhcs.processing.backends.processors.numpy_processor import create_composite, create_projection, stack_percentile_normalize
    # Pipeline steps
    pipeline_steps = []
    # Step 1: Image Enhancement Processing
    step_1 = FunctionStep(
        func=(stack_percentile_normalize, {
                'low_percentile': 0.5,
                'high_percentile': 99.5
            }),
        name="Image Enhancement Processing",
        step_well_filter_config=LazyStepWellFilterConfig(well_filter=4),
        step_materialization_config=LazyStepMaterializationConfig(),
        napari_streaming_config=LazyNapariStreamingConfig(napari_port=5555),
    )
    pipeline_steps.append(step_1)
    # Step 2: create_composite
    step_2 = FunctionStep(
        func=create_composite,
        name="create_composite",
        variable_components=[VariableComponents.CHANNEL],
        napari_streaming_config=LazyNapariStreamingConfig(napari_port=5557),
    )
    pipeline_steps.append(step_2)
    # Step 3: Z-Stack Flattening
    step_3 = FunctionStep(
        func=create_projection,
        name="Z-Stack Flattening",
        variable_components=[VariableComponents.Z_INDEX],
        step_materialization_config=LazyStepMaterializationConfig()
    )
    pipeline_steps.append(step_3)
    # Step 4: Position Computation
    step_4 = FunctionStep(
        func=ashlar_compute_tile_positions_gpu,
        name="Position Computation"
    )
    pipeline_steps.append(step_4)
    # Step 5: Secondary Enhancement
    step_5 = FunctionStep(
        func=(stack_percentile_normalize, {
                'low_percentile': 0.5,
                'high_percentile': 99.5
            }),
        name="Secondary Enhancement",
        input_source=InputSource.PIPELINE_START
    )
    pipeline_steps.append(step_5)
    # Step 6: CPU Assembly
    step_6 = FunctionStep(
        func=assemble_stack_cpu,
        name="CPU Assembly"
    )
    pipeline_steps.append(step_6)
    # Step 7: Z-Stack Flattening
    step_7 = FunctionStep(
        func=create_projection,
        name="Z-Stack Flattening",
        variable_components=[VariableComponents.Z_INDEX]
    )
    pipeline_steps.append(step_7)
    # Step 8: Cell Counting
    step_8 = FunctionStep(
        func={        '1': (count_cells_single_channel, {
                'min_cell_area': 40,
                'max_cell_area': 200,
                'enable_preprocessing': False,
                'detection_method': DetectionMethod.WATERSHED,
                'dtype_conversion': DtypeConversion.UINT8,
                'return_segmentation_mask': True
            }),
            '2': (count_cells_single_channel, {
                'min_cell_area': 40,
                'max_cell_area': 200,
                'enable_preprocessing': False,
                'detection_method': DetectionMethod.WATERSHED,
                'dtype_conversion': DtypeConversion.UINT8,
                'return_segmentation_mask': True
            })
        },
        name="Cell Counting",
        napari_streaming_config=LazyNapariStreamingConfig(variable_size_handling=NapariVariableSizeHandling.PAD_TO_MAX, napari_port=5559),
    )
    pipeline_steps.append(step_8)

    return Pipeline(
        steps=pipeline_steps,
        name='Multi-Subdirectory Test Pipeline'
    )


pipeline_steps = create_pipeline()
