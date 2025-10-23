"""
Dual Editor Window for PyQt6

Step and function editing dialog with tabbed interface.
Uses hybrid approach: extracted business logic + clean PyQt6 UI.
"""

import logging
from typing import Optional, Callable, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QWidget, QStackedWidget
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from openhcs.core.steps.function_step import FunctionStep
from openhcs.ui.shared.pattern_data_manager import PatternDataManager

from openhcs.pyqt_gui.shared.color_scheme import PyQt6ColorScheme
from openhcs.pyqt_gui.shared.style_generator import StyleSheetGenerator
from openhcs.pyqt_gui.windows.base_form_dialog import BaseFormDialog
logger = logging.getLogger(__name__)


class DualEditorWindow(BaseFormDialog):
    """
    PyQt6 Multi-Tab Parameter Editor Window.

    Generic parameter editing dialog with inheritance hierarchy-based tabbed interface.
    Creates one tab per class in the inheritance hierarchy, showing parameters specific
    to each class level. Preserves all business logic from Textual version with clean PyQt6 UI.

    Inherits from BaseFormDialog to automatically handle unregistration from
    cross-window placeholder updates when the dialog closes.
    """

    # Signals
    step_saved = pyqtSignal(object)  # FunctionStep
    step_cancelled = pyqtSignal()
    changes_detected = pyqtSignal(bool)  # has_changes
    
    def __init__(self, step_data: Optional[FunctionStep] = None, is_new: bool = False,
                 on_save_callback: Optional[Callable] = None, color_scheme: Optional[PyQt6ColorScheme] = None,
                 orchestrator=None, gui_config=None, parent=None):
        """
        Initialize the dual editor window.

        Args:
            step_data: FunctionStep to edit (None for new step)
            is_new: Whether this is a new step
            on_save_callback: Function to call when step is saved
            color_scheme: Color scheme for UI components
            orchestrator: Orchestrator instance for context management
            gui_config: Optional GUI configuration passed from PipelineEditor
            parent: Parent widget
        """
        super().__init__(parent)

        # Make window non-modal (like plate manager and pipeline editor)
        self.setModal(False)

        # Initialize color scheme and style generator
        self.color_scheme = color_scheme or PyQt6ColorScheme()
        self.style_generator = StyleSheetGenerator(self.color_scheme)
        self.gui_config = gui_config

        # Business logic state (extracted from Textual version)
        self.is_new = is_new
        self.on_save_callback = on_save_callback
        self.orchestrator = orchestrator  # Store orchestrator for context management
        
        # Pattern management (extracted from Textual version)
        self.pattern_manager = PatternDataManager()

        # Store original step reference (never modified)
        self.original_step_reference = step_data

        if step_data:
            # CRITICAL FIX: Work on a copy to prevent immediate modification of original
            self.editing_step = self._clone_step(step_data)
            self.original_step = self._clone_step(step_data)
        else:
            self.editing_step = self._create_new_step()
            self.original_step = None
        
        # Change tracking
        self.has_changes = False
        self.current_tab = "step"
        
        # UI components
        self.tab_widget: Optional[QTabWidget] = None
        self.parameter_editors: Dict[str, QWidget] = {}  # Map tab titles to editor widgets
        self.class_hierarchy: List = []  # Store inheritance hierarchy info
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        
        logger.debug(f"Dual editor window initialized (new={is_new})")

    def set_original_step_for_change_detection(self):
        """Set the original step for change detection. Must be called within proper context."""
        # Original step is already set in __init__ when working on a copy
        # This method is kept for compatibility but no longer needed
        pass

    def setup_ui(self):
        """Setup the user interface."""
        title = "New Step" if self.is_new else f"Edit Step: {getattr(self.editing_step, 'name', 'Unknown')}"
        self.setWindowTitle(title)
        # Keep non-modal (already set in __init__)
        # No minimum size - let it be determined by content
        self.resize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Single row: tabs + title + status + buttons
        tab_row = QHBoxLayout()
        tab_row.setContentsMargins(5, 5, 5, 5)
        tab_row.setSpacing(10)

        # Tab widget (tabs on the left)
        self.tab_widget = QTabWidget()
        # Get the tab bar and add it to our horizontal layout
        self.tab_bar = self.tab_widget.tabBar()
        # Prevent tab scrolling by setting expanding to false and using minimum size hint
        self.tab_bar.setExpanding(False)
        self.tab_bar.setUsesScrollButtons(False)
        tab_row.addWidget(self.tab_bar, 0)  # 0 stretch - don't expand

        # Title on the right of tabs (allow it to be cropped if needed)
        header_label = QLabel(title)
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setStyleSheet(f"color: {self.color_scheme.to_hex(self.color_scheme.text_accent)};")
        from PyQt6.QtWidgets import QSizePolicy
        header_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        tab_row.addWidget(header_label, 1)  # 1 stretch - allow to expand and be cropped

        tab_row.addStretch()

        # Status indicator
        self.changes_label = QLabel("")
        self.changes_label.setStyleSheet(f"color: {self.color_scheme.to_hex(self.color_scheme.status_warning)}; font-style: italic;")
        tab_row.addWidget(self.changes_label)

        # Get centralized button styles
        button_styles = self.style_generator.generate_config_button_styles()

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(28)
        cancel_button.setMinimumWidth(70)
        cancel_button.clicked.connect(self.cancel_edit)
        cancel_button.setStyleSheet(button_styles["cancel"])
        tab_row.addWidget(cancel_button)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setFixedHeight(28)
        self.save_button.setMinimumWidth(70)
        self.save_button.setEnabled(False)  # Initially disabled
        self.save_button.clicked.connect(self.save_edit)
        self.save_button.setStyleSheet(button_styles["save"] + f"""
            QPushButton:disabled {{
                background-color: {self.color_scheme.to_hex(self.color_scheme.panel_bg)};
                color: {self.color_scheme.to_hex(self.color_scheme.border_light)};
                border: none;
            }}
        """)
        tab_row.addWidget(self.save_button)

        layout.addLayout(tab_row)
        # Style the tab bar
        self.tab_bar.setStyleSheet(f"""
            QTabBar::tab {{
                background-color: {self.color_scheme.to_hex(self.color_scheme.input_bg)};
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: none;
            }}
            QTabBar::tab:selected {{
                background-color: {self.color_scheme.to_hex(self.color_scheme.selection_bg)};
            }}
            QTabBar::tab:hover {{
                background-color: {self.color_scheme.to_hex(self.color_scheme.button_hover_bg)};
            }}
        """)

        # Create tabs (this adds content to the tab widget)
        self.create_step_tab()
        self.create_function_tab()

        # Add the tab widget's content area (stacked widget) below the tab row
        # The tab bar is already in tab_row, so we only add the content pane here
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Get the stacked widget from the tab widget and add it
        stacked_widget = self.tab_widget.findChild(QStackedWidget)
        if stacked_widget:
            content_layout.addWidget(stacked_widget)

        layout.addWidget(content_container)

        # Apply centralized styling
        self.setStyleSheet(self.style_generator.generate_config_window_style())
    
    def create_step_tab(self):
        """Create the step settings tab (using dedicated widget)."""
        from openhcs.pyqt_gui.widgets.step_parameter_editor import StepParameterEditorWidget
        from openhcs.config_framework.context_manager import config_context

        # Create step parameter editor widget with proper nested context
        # Step must be nested: GlobalPipelineConfig -> PipelineConfig -> Step
        # CRITICAL: Pass orchestrator's plate_path as scope_id to limit cross-window updates to same orchestrator
        scope_id = str(self.orchestrator.plate_path) if self.orchestrator else None
        with config_context(self.orchestrator.pipeline_config):  # Pipeline level
            with config_context(self.editing_step):              # Step level
                self.step_editor = StepParameterEditorWidget(
                    self.editing_step,
                    service_adapter=None,
                    color_scheme=self.color_scheme,
                    pipeline_config=self.orchestrator.pipeline_config,
                    scope_id=scope_id
                )

        # Connect parameter changes - use form manager signal for immediate response
        self.step_editor.form_manager.parameter_changed.connect(self.on_form_parameter_changed)

        self.tab_widget.addTab(self.step_editor, "Step Settings")

    def create_function_tab(self):
        """Create the function pattern tab (using dedicated widget)."""
        from openhcs.pyqt_gui.widgets.function_list_editor import FunctionListEditorWidget

        # Convert step func to function list format
        initial_functions = self._convert_step_func_to_list()

        # Create function list editor widget (mirrors Textual TUI)
        step_id = getattr(self.editing_step, 'name', 'unknown_step')
        self.func_editor = FunctionListEditorWidget(
            initial_functions=initial_functions,
            step_identifier=step_id,
            service_adapter=None
        )

        # Store main window reference for orchestrator access (find it through parent chain)
        main_window = self._find_main_window()
        if main_window:
            self.func_editor.main_window = main_window

        # Initialize step configuration settings in function editor (mirrors Textual TUI)
        self.func_editor.current_group_by = self.editing_step.group_by
        self.func_editor.current_variable_components = self.editing_step.variable_components or []

        # Refresh component button to show correct text and state (mirrors Textual TUI reactive updates)
        self.func_editor._refresh_component_button()

        # Connect function pattern changes
        self.func_editor.function_pattern_changed.connect(self._on_function_pattern_changed)

        self.tab_widget.addTab(self.func_editor, "Function Pattern")

    def _on_function_pattern_changed(self):
        """Handle function pattern changes from function editor."""
        # Update step func from function editor - use current_pattern to get full pattern data
        current_pattern = self.func_editor.current_pattern

        # CRITICAL FIX: Use fresh imports to avoid unpicklable registry wrappers
        if callable(current_pattern) and hasattr(current_pattern, '__module__'):
            try:
                import importlib
                module = importlib.import_module(current_pattern.__module__)
                current_pattern = getattr(module, current_pattern.__name__)
            except Exception:
                pass  # Use original if refresh fails

        self.editing_step.func = current_pattern
        self.detect_changes()
        logger.debug(f"Function pattern changed: {current_pattern}")





    def setup_connections(self):
        """Setup signal/slot connections."""
        # Tab change tracking
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Change detection
        self.changes_detected.connect(self.on_changes_detected)

    def _convert_step_func_to_list(self):
        """Convert step func to initial pattern format for function list editor."""
        if not hasattr(self.editing_step, 'func') or not self.editing_step.func:
            return []

        # Return the step func directly - the function list editor will handle the conversion
        result = self.editing_step.func
        print(f"🔍 DUAL EDITOR _convert_step_func_to_list: returning {result}")
        return result



    def _find_main_window(self):
        """Find the main window through the parent chain."""
        try:
            # Navigate up the parent chain to find OpenHCSMainWindow
            current = self.parent()
            while current:
                # Check if this is the main window (has floating_windows attribute)
                if hasattr(current, 'floating_windows') and hasattr(current, 'service_adapter'):
                    logger.debug(f"Found main window: {type(current).__name__}")
                    return current
                current = current.parent()

            logger.warning("Could not find main window in parent chain")
            return None

        except Exception as e:
            logger.error(f"Error finding main window: {e}")
            return None

    def _get_current_plate_from_pipeline_editor(self):
        """Get current plate from pipeline editor (mirrors Textual TUI pattern)."""
        try:
            # Navigate up to find pipeline editor widget
            current = self.parent()
            while current:
                # Check if this is a pipeline editor widget
                if hasattr(current, 'current_plate') and hasattr(current, 'pipeline_steps'):
                    current_plate = getattr(current, 'current_plate', None)
                    if current_plate:
                        logger.debug(f"Found current plate from pipeline editor: {current_plate}")
                        return current_plate

                # Check children for pipeline editor widget
                for child in current.findChildren(QWidget):
                    if hasattr(child, 'current_plate') and hasattr(child, 'pipeline_steps'):
                        current_plate = getattr(child, 'current_plate', None)
                        if current_plate:
                            logger.debug(f"Found current plate from pipeline editor child: {current_plate}")
                            return current_plate

                current = current.parent()

            logger.warning("Could not find current plate from pipeline editor")
            return None

        except Exception as e:
            logger.error(f"Error getting current plate from pipeline editor: {e}")
            return None

    # Old function pane methods removed - now using dedicated FunctionListEditorWidget
    
    def get_function_info(self) -> str:
        """
        Get function information for display.
        
        Returns:
            Function information string
        """
        if not self.editing_step or not hasattr(self.editing_step, 'func'):
            return "No function assigned"
        
        func = self.editing_step.func
        func_name = getattr(func, '__name__', 'Unknown Function')
        func_module = getattr(func, '__module__', 'Unknown Module')
        
        info = f"Function: {func_name}\n"
        info += f"Module: {func_module}\n"
        
        # Add parameter info if available
        if hasattr(self.editing_step, 'parameters'):
            params = self.editing_step.parameters
            if params:
                info += f"\nParameters ({len(params)}):\n"
                for param_name, param_value in params.items():
                    info += f"  {param_name}: {param_value}\n"
        
        return info
    
    def on_form_parameter_changed(self, param_name: str, value):
        """Handle form parameter changes directly from form manager."""
        # CRITICAL FIX: For function parameters, use fresh imports to avoid unpicklable registry wrappers
        if param_name == 'func' and callable(value) and hasattr(value, '__module__'):
            try:
                import importlib
                module = importlib.import_module(value.__module__)
                value = getattr(module, value.__name__)
            except Exception:
                pass  # Use original if refresh fails

        setattr(self.editing_step, param_name, value)

        if param_name in ('group_by', 'variable_components'):
            self.func_editor.current_group_by = self.editing_step.group_by
            self.func_editor.current_variable_components = self.editing_step.variable_components or []
            self.func_editor._refresh_component_button()

        self.detect_changes()
    
    def on_tab_changed(self, index: int):
        """Handle tab changes."""
        tab_names = ["step", "function"]
        if 0 <= index < len(tab_names):
            self.current_tab = tab_names[index]
            logger.debug(f"Tab changed to: {self.current_tab}")
    
    def detect_changes(self):
        """Detect if changes have been made."""
        has_changes = self.original_step != self.editing_step

        # Check function pattern
        if not has_changes:
            original_func = getattr(self.original_step, 'func', None)
            current_func = getattr(self.editing_step, 'func', None)
            # Simple comparison - could be enhanced for deep comparison
            has_changes = str(original_func) != str(current_func)

        if has_changes != self.has_changes:
            self.has_changes = has_changes
            self.changes_detected.emit(has_changes)
    
    def on_changes_detected(self, has_changes: bool):
        """Handle changes detection."""
        if has_changes:
            self.changes_label.setText("● Unsaved changes")
            self.save_button.setEnabled(True)
        else:
            self.changes_label.setText("")
            self.save_button.setEnabled(False)
    
    def save_edit(self):
        """Save the edited step."""
        try:
            # CRITICAL FIX: Sync function pattern from function editor BEFORE collecting form values
            # The function editor doesn't use a form manager, so we need to explicitly sync it
            if self.func_editor:
                current_pattern = self.func_editor.current_pattern

                # CRITICAL FIX: Use fresh imports to avoid unpicklable registry wrappers
                if callable(current_pattern) and hasattr(current_pattern, '__module__'):
                    try:
                        import importlib
                        module = importlib.import_module(current_pattern.__module__)
                        current_pattern = getattr(module, current_pattern.__name__)
                    except Exception:
                        pass  # Use original if refresh fails

                self.editing_step.func = current_pattern
                logger.debug(f"Synced function pattern before save: {current_pattern}")

            # CRITICAL FIX: Collect current values from all form managers before saving
            # This ensures nested dataclass field values are properly saved to the step object
            for tab_index in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(tab_index)
                if hasattr(tab_widget, 'form_manager'):
                    # Get current values from this tab's form manager
                    current_values = tab_widget.form_manager.get_current_values()

                    # Apply values to the editing step
                    for param_name, value in current_values.items():
                        if hasattr(self.editing_step, param_name):
                            setattr(self.editing_step, param_name, value)
                            logger.debug(f"Applied {param_name}={value} to editing step")

            # Validate step
            step_name = getattr(self.editing_step, 'name', None)
            if not step_name or not step_name.strip():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Validation Error", "Step name cannot be empty.")
                return

            # CRITICAL FIX: For existing steps, apply changes to original step object
            # This ensures the pipeline gets the updated step with the same object identity
            if self.original_step_reference is not None:
                # Copy all attributes from editing_step to original_step_reference
                self._apply_changes_to_original()
                step_to_save = self.original_step_reference
            else:
                # For new steps, use the editing_step directly
                step_to_save = self.editing_step

            # Emit signals and call callback
            self.step_saved.emit(step_to_save)

            if self.on_save_callback:
                self.on_save_callback(step_to_save)

            self.accept()  # BaseFormDialog handles unregistration
            logger.debug(f"Step saved: {getattr(step_to_save, 'name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Failed to save step: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Save Error", f"Failed to save step:\n{e}")

    def _apply_changes_to_original(self):
        """Apply all changes from editing_step to original_step_reference."""
        if self.original_step_reference is None:
            return

        # Copy all attributes from editing_step to original_step_reference
        from dataclasses import fields, is_dataclass

        if is_dataclass(self.editing_step):
            # For dataclass steps, copy all field values
            for field in fields(self.editing_step):
                value = getattr(self.editing_step, field.name)
                setattr(self.original_step_reference, field.name, value)
        else:
            # CRITICAL FIX: Use reflection to copy ALL attributes, not just hardcoded list
            # This ensures optional dataclass attributes like step_materialization_config are copied
            for attr_name in dir(self.editing_step):
                # Skip private/magic attributes and methods
                if not attr_name.startswith('_') and not callable(getattr(self.editing_step, attr_name, None)):
                    if hasattr(self.editing_step, attr_name) and hasattr(self.original_step_reference, attr_name):
                        value = getattr(self.editing_step, attr_name)
                        setattr(self.original_step_reference, attr_name, value)
                        logger.debug(f"Copied attribute {attr_name}: {value}")

        logger.debug("Applied changes to original step object")

    def _clone_step(self, step):
        """Clone a step object using deep copy."""
        import copy
        return copy.deepcopy(step)

    def _create_new_step(self):
        """Create a new empty step."""
        from openhcs.core.steps.function_step import FunctionStep
        return FunctionStep(
            func=[],  # Start with empty function list
            name="New_Step"
        )

    def cancel_edit(self):
        """Cancel editing and close dialog."""
        if self.has_changes:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        self.step_cancelled.emit()
        self.reject()  # BaseFormDialog handles unregistration
        logger.debug("Step editing cancelled")

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.has_changes:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        super().closeEvent(event)  # BaseFormDialog handles unregistration

    def _get_form_managers(self):
        """Return list of form managers to unregister (required by BaseFormDialog)."""
        if hasattr(self, 'step_editor') and hasattr(self.step_editor, 'form_manager'):
            return [self.step_editor.form_manager]
        return []
