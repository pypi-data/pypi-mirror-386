"""
QStyleSheet Generator for OpenHCS PyQt6 GUI

Generates dynamic QStyleSheet strings from PyQt6ColorScheme objects, enabling
centralized styling with theme support. Replaces hardcoded color strings with
semantic color scheme references.
"""

import logging
from openhcs.pyqt_gui.shared.color_scheme import PyQt6ColorScheme

logger = logging.getLogger(__name__)


class StyleSheetGenerator:
    """
    Generates QStyleSheet strings from PyQt6ColorScheme objects.
    
    Provides methods to generate complete stylesheets for different widget types,
    replacing hardcoded colors with centralized color scheme references.
    """
    
    def __init__(self, color_scheme: PyQt6ColorScheme):
        """
        Initialize the style generator with a color scheme.
        
        Args:
            color_scheme: PyQt6ColorScheme instance to use for styling
        """
        self.color_scheme = color_scheme
    
    def update_color_scheme(self, color_scheme: PyQt6ColorScheme):
        """
        Update the color scheme used for style generation.
        
        Args:
            color_scheme: New PyQt6ColorScheme instance
        """
        self.color_scheme = color_scheme
    
    def generate_dialog_style(self) -> str:
        """
        Generate QStyleSheet for dialog windows.
        
        Returns:
            str: Complete QStyleSheet for dialog styling
        """
        cs = self.color_scheme
        return f"""
            QDialog {{
                background-color: {cs.to_hex(cs.window_bg)};
                color: {cs.to_hex(cs.text_primary)};
            }}
            QGroupBox {{
                font-weight: bold;
                border: none;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: {cs.to_hex(cs.panel_bg)};
                color: {cs.to_hex(cs.text_primary)};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {cs.to_hex(cs.text_accent)};
            }}
            QLabel {{
                color: {cs.to_hex(cs.text_secondary)};
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {cs.to_hex(cs.input_bg)};
                color: {cs.to_hex(cs.input_text)};
                border: 1px solid {cs.to_hex(cs.input_border)};
                border-radius: 3px;
                padding: 5px;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border: 1px solid {cs.to_hex(cs.input_focus_border)};
            }}
            QCheckBox {{
                color: {cs.to_hex(cs.text_primary)};
            }}
        """
    
    def generate_tree_widget_style(self) -> str:
        """
        Generate QStyleSheet for tree widgets and list widgets.

        Returns:
            str: Complete QStyleSheet for tree/list widget styling
        """
        cs = self.color_scheme
        return f"""
            QTreeWidget, QListWidget {{
                background-color: {cs.to_hex(cs.panel_bg)};
                color: {cs.to_hex(cs.text_primary)};
                border: none;
                border-radius: 3px;
                selection-background-color: {cs.to_hex(cs.selection_bg)};
            }}
            QTreeWidget::item, QListWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {cs.to_hex(cs.border_color)};
            }}
            QTreeWidget::item:hover, QListWidget::item:hover {{
                background-color: {cs.to_hex(cs.hover_bg)};
            }}
            QTreeWidget::item:selected, QListWidget::item:selected {{
                background-color: {cs.to_hex(cs.selection_bg)};
                color: {cs.to_hex(cs.selection_text)};
            }}
            QHeaderView::section {{
                background-color: {cs.to_hex(cs.panel_bg)};
                color: {cs.to_hex(cs.text_primary)};
                padding: 4px;
                border: none;
                border-bottom: 1px solid {cs.to_hex(cs.border_color)};
                font-weight: normal;
            }}
        """

    def generate_table_widget_style(self) -> str:
        """
        Generate QStyleSheet for table widgets.

        Returns:
            str: Complete QStyleSheet for table widget styling
        """
        cs = self.color_scheme
        return f"""
            QTableWidget {{
                background-color: {cs.to_hex(cs.panel_bg)};
                color: {cs.to_hex(cs.text_primary)};
                border: none;
                border-radius: 3px;
                gridline-color: {cs.to_hex(cs.border_color)};
                selection-background-color: {cs.to_hex(cs.selection_bg)};
            }}
            QTableWidget::item {{
                padding: 4px;
                border: none;
            }}
            QTableWidget::item:hover {{
                background-color: {cs.to_hex(cs.hover_bg)};
            }}
            QTableWidget::item:selected {{
                background-color: {cs.to_hex(cs.selection_bg)};
                color: {cs.to_hex(cs.selection_text)};
            }}
            QHeaderView::section {{
                background-color: {cs.to_hex(cs.input_bg)};
                color: {cs.to_hex(cs.text_primary)};
                padding: 5px;
                border: none;
                border-bottom: 1px solid {cs.to_hex(cs.border_color)};
                font-weight: bold;
            }}
        """
    
    def generate_button_style(self) -> str:
        """
        Generate QStyleSheet for buttons with all states.
        
        Returns:
            str: Complete QStyleSheet for button styling
        """
        cs = self.color_scheme
        return f"""
            QPushButton {{
                background-color: {cs.to_hex(cs.button_normal_bg)};
                color: {cs.to_hex(cs.button_text)};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {cs.to_hex(cs.button_hover_bg)};
            }}
            QPushButton:pressed {{
                background-color: {cs.to_hex(cs.button_pressed_bg)};
            }}
            QPushButton:disabled {{
                background-color: {cs.to_hex(cs.button_disabled_bg)};
                color: {cs.to_hex(cs.button_disabled_text)};
            }}
        """
    
    def generate_combobox_style(self) -> str:
        """
        Generate QStyleSheet for combo boxes with dropdown styling.
        
        Returns:
            str: Complete QStyleSheet for combo box styling
        """
        cs = self.color_scheme
        return f"""
            QComboBox {{
                background-color: {cs.to_hex(cs.input_bg)};
                color: {cs.to_hex(cs.input_text)};
                border: 1px solid {cs.to_hex(cs.input_border)};
                border-radius: 3px;
                padding: 5px;
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: {cs.to_hex(cs.button_normal_bg)};
            }}
            QComboBox::down-arrow {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {cs.to_hex(cs.input_bg)};
                color: {cs.to_hex(cs.input_text)};
                selection-background-color: {cs.to_hex(cs.selection_bg)};
            }}
        """
    
    def generate_progress_bar_style(self) -> str:
        """
        Generate QStyleSheet for progress bars.
        
        Returns:
            str: Complete QStyleSheet for progress bar styling
        """
        cs = self.color_scheme
        return f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background-color: {cs.to_hex(cs.progress_bg)};
                color: {cs.to_hex(cs.text_primary)};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {cs.to_hex(cs.progress_fill)};
                border-radius: 2px;
            }}
        """
    
    def generate_frame_style(self) -> str:
        """
        Generate QStyleSheet for frames and panels.

        Returns:
            str: Complete QStyleSheet for frame styling
        """
        cs = self.color_scheme
        return f"""
            QFrame {{
                background-color: {cs.to_hex(cs.frame_bg)};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
        """

    def generate_tab_widget_style(self) -> str:
        """
        Generate QStyleSheet for tab widgets.

        Returns:
            str: Complete QStyleSheet for tab widget styling
        """
        cs = self.color_scheme
        return f"""
            QTabWidget::pane {{
                border: 1px solid {cs.to_hex(cs.border_color)};
                border-radius: 3px;
                background-color: {cs.to_hex(cs.panel_bg)};
            }}
            QTabBar::tab {{
                background-color: {cs.to_hex(cs.button_normal_bg)};
                color: {cs.to_hex(cs.text_secondary)};
                border: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {cs.to_hex(cs.selection_bg)};
                color: {cs.to_hex(cs.selection_text)};
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: {cs.to_hex(cs.button_hover_bg)};
            }}
        """
    
    def generate_system_monitor_style(self) -> str:
        """
        Generate QStyleSheet for system monitor widget.

        Returns:
            str: Complete QStyleSheet for system monitor styling
        """
        cs = self.color_scheme
        return f"""
            SystemMonitorWidget {{
                background-color: {cs.to_hex(cs.window_bg)};
                color: {cs.to_hex(cs.text_primary)};
                border: 1px solid {cs.to_hex(cs.border_color)};
                border-radius: 5px;
            }}
            QLabel {{
                color: {cs.to_hex(cs.text_primary)};
            }}
            #header_label {{
                color: {cs.to_hex(cs.text_accent)};
                font-weight: bold;
                font-size: 14px;
            }}
            #info_panel {{
                background-color: {cs.to_hex(cs.panel_bg)};
                border: 2px solid {cs.to_hex(cs.border_color)};
                border-radius: 8px;
                padding: 5px;
            }}
            #info_title {{
                color: {cs.to_hex(cs.text_accent)};
                font-weight: bold;
                padding-bottom: 5px;
            }}
            #info_label_key {{
                color: {cs.to_hex(cs.text_secondary)};
            }}
            #info_label_value {{
                color: {cs.to_hex(cs.text_primary)};
                font-weight: bold;
            }}
        """
    
    def generate_complete_application_style(self) -> str:
        """
        Generate complete application-wide QStyleSheet.
        
        Returns:
            str: Complete QStyleSheet for entire application
        """
        return (
            self.generate_dialog_style() + "\n" +
            self.generate_tree_widget_style() + "\n" +
            self.generate_button_style() + "\n" +
            self.generate_combobox_style() + "\n" +
            self.generate_progress_bar_style() + "\n" +
            self.generate_frame_style() + "\n" +
            self.generate_system_monitor_style()
        )
    
    def generate_config_window_style(self) -> str:
        """
        Generate QStyleSheet for configuration windows with button panel.

        Returns:
            str: Complete QStyleSheet for config window styling
        """
        cs = self.color_scheme
        return f"""
            QDialog {{
                background-color: {cs.to_hex(cs.window_bg)};
                color: {cs.to_hex(cs.text_primary)};
            }}
            QGroupBox {{
                font-weight: bold;
                border: none;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: {cs.to_hex(cs.panel_bg)};
                color: {cs.to_hex(cs.text_primary)};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {cs.to_hex(cs.text_accent)};
            }}
            QLabel {{
                color: {cs.to_hex(cs.text_secondary)};
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {cs.to_hex(cs.input_bg)};
                color: {cs.to_hex(cs.input_text)};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border: 1px solid {cs.to_hex(cs.input_focus_border)};
            }}
            QPushButton {{
                background-color: {cs.to_hex(cs.button_normal_bg)};
                color: {cs.to_hex(cs.button_text)};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {cs.to_hex(cs.button_hover_bg)};
            }}
            QPushButton:pressed {{
                background-color: {cs.to_hex(cs.button_pressed_bg)};
            }}
            QPushButton:disabled {{
                background-color: {cs.to_hex(cs.button_disabled_bg)};
                color: {cs.to_hex(cs.button_disabled_text)};
            }}
            QCheckBox {{
                color: {cs.to_hex(cs.text_primary)};
            }}
            QFrame {{
                background-color: {cs.to_hex(cs.panel_bg)};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
        """

    def generate_config_button_styles(self) -> dict:
        """
        Generate individual button styles for config window buttons.

        Returns:
            dict: Dictionary with button styles for reset, cancel, save
        """
        cs = self.color_scheme

        return {
            "reset": f"""
                QPushButton {{
                    background-color: {cs.to_hex(cs.button_normal_bg)};
                    color: {cs.to_hex(cs.button_text)};
                    border: 1px solid {cs.to_hex(cs.border_light)};
                    border-radius: 3px;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: {cs.to_hex(cs.button_hover_bg)};
                }}
            """,
            "cancel": f"""
                QPushButton {{
                    background-color: {cs.to_hex(cs.button_normal_bg)};
                    color: {cs.to_hex(cs.button_text)};
                    border: 1px solid {cs.to_hex(cs.border_light)};
                    border-radius: 3px;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: {cs.to_hex(cs.button_hover_bg)};
                }}
            """,
            "save": f"""
                QPushButton {{
                    background-color: {cs.to_hex(cs.selection_bg)};
                    color: {cs.to_hex(cs.selection_text)};
                    border: 1px solid {cs.to_hex(cs.selection_bg)};
                    border-radius: 3px;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba({cs.selection_bg[0]}, {cs.selection_bg[1]}, {cs.selection_bg[2]}, 0.8);
                }}
            """
        }

    def generate_plate_manager_style(self) -> str:
        """
        Generate QStyleSheet for plate manager widget with all components.

        Returns:
            str: Complete QStyleSheet for plate manager styling
        """
        cs = self.color_scheme
        return f"""
            QListWidget {{
                background-color: {cs.to_hex(cs.panel_bg)};
                color: {cs.to_hex(cs.text_primary)};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {cs.to_hex(cs.selection_bg)};
                color: {cs.to_hex(cs.selection_text)};
            }}
            QListWidget::item:hover {{
                background-color: {cs.to_hex(cs.hover_bg)};
            }}
            QFrame {{
                background-color: {cs.to_hex(cs.window_bg)};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {cs.to_hex(cs.button_normal_bg)};
                color: {cs.to_hex(cs.button_text)};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {cs.to_hex(cs.button_hover_bg)};
            }}
            QPushButton:pressed {{
                background-color: {cs.to_hex(cs.button_pressed_bg)};
            }}
            QPushButton:disabled {{
                background-color: {cs.to_hex(cs.button_disabled_bg)};
                color: {cs.to_hex(cs.button_disabled_text)};
            }}
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background-color: {cs.to_hex(cs.progress_bg)};
                color: {cs.to_hex(cs.text_primary)};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {cs.to_hex(cs.progress_fill)};
                border-radius: 2px;
            }}
        """

    def get_status_color_hex(self, status_type: str) -> str:
        """
        Get hex color string for status type.

        Args:
            status_type: Status type (success, warning, error, info)

        Returns:
            str: Hex color string for the status type
        """
        cs = self.color_scheme
        status_colors = {
            "success": cs.status_success,
            "warning": cs.status_warning,
            "error": cs.status_error,
            "info": cs.status_info,
        }

        color = status_colors.get(status_type, cs.status_info)
        return cs.to_hex(color)
