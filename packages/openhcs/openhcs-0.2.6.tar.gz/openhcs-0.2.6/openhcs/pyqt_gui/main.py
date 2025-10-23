"""
OpenHCS PyQt6 Main Window

Main application window implementing QDockWidget system to replace
textual-window floating windows with native Qt docking.
"""

import logging
from typing import Optional, Dict
from pathlib import Path
import webbrowser

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QMessageBox, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt, QSettings, QTimer, pyqtSignal, QUrl
from PyQt6.QtGui import QAction, QKeySequence, QDesktopServices

from openhcs.core.config import GlobalPipelineConfig
from openhcs.io.filemanager import FileManager
from openhcs.io.base import storage_registry

from openhcs.pyqt_gui.services.service_adapter import PyQtServiceAdapter

logger = logging.getLogger(__name__)


class OpenHCSMainWindow(QMainWindow):
    """
    Main OpenHCS PyQt6 application window.
    
    Implements QDockWidget system to replace textual-window floating windows
    with native Qt docking, providing better desktop integration.
    """
    
    # Signals for application events
    config_changed = pyqtSignal(object)  # GlobalPipelineConfig
    status_message = pyqtSignal(str)  # Status message
    
    def __init__(self, global_config: Optional[GlobalPipelineConfig] = None):
        """
        Initialize the main OpenHCS window.

        Args:
            global_config: Global configuration (uses default if None)
        """
        super().__init__()

        # Core configuration
        self.global_config = global_config or GlobalPipelineConfig()
        
        # Create shared components
        self.storage_registry = storage_registry
        self.file_manager = FileManager(self.storage_registry)
        
        # Service adapter for Qt integration
        self.service_adapter = PyQtServiceAdapter(self)
        
        # Floating windows registry (replaces dock widgets)
        self.floating_windows: Dict[str, QDialog] = {}

        # Settings for window state persistence
        self.settings = QSettings("OpenHCS", "PyQt6GUI")

        # Initialize Log Viewer on startup (hidden) for continuous log monitoring
        self._initialize_log_viewer()
        
        # Initialize UI
        self.setup_ui()
        self.setup_dock_system()
        self.create_floating_windows()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.setup_connections()

        # Apply initial theme
        self.apply_initial_theme()

        # Restore window state
        self.restore_window_state()

        # Show default windows (plate manager and pipeline editor visible by default)
        self.show_default_windows()

        logger.info("OpenHCS PyQt6 main window initialized")
    
    def setup_ui(self):
        """Setup basic UI structure."""
        self.setWindowTitle("OpenHCS")
        self.setMinimumSize(640, 480)

        # Make main window floating (not tiled) like other OpenHCS components
        self.setWindowFlags(Qt.WindowType.Dialog)
        
        # Central widget with system monitor background
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        
        # System monitor widget (background)
        from openhcs.pyqt_gui.widgets.system_monitor import SystemMonitorWidget
        self.system_monitor = SystemMonitorWidget()
        central_layout.addWidget(self.system_monitor)
        
        self.setCentralWidget(central_widget)

    def apply_initial_theme(self):
        """Apply initial color scheme to the main window."""
        # Get theme manager from service adapter
        theme_manager = self.service_adapter.get_theme_manager()

        # Note: ServiceAdapter already applied dark theme globally in its __init__
        # Just register for theme change notifications, don't re-apply
        theme_manager.register_theme_change_callback(self.on_theme_changed)

        logger.debug("Registered for theme change notifications (theme already applied by ServiceAdapter)")

    def on_theme_changed(self, color_scheme):
        """
        Handle theme change notifications.

        Args:
            color_scheme: New color scheme that was applied
        """
        # Update any main window specific styling if needed
        # Most styling is handled automatically by the theme manager
        logger.debug("Main window received theme change notification")
    
    def setup_dock_system(self):
        """Setup window system mirroring Textual TUI floating windows."""
        # In Textual TUI, widgets are floating windows, not docked
        # We'll create windows on-demand when menu items are clicked
        # Only the system monitor stays as the central background widget
        pass
    
    def create_floating_windows(self):
        """Create floating windows mirroring Textual TUI window system."""
        # Windows are created on-demand when menu items are clicked
        # This mirrors the Textual TUI pattern where windows are mounted dynamically
        self.floating_windows = {}  # Track created windows

    def show_default_windows(self):
        """Show plate manager and pipeline editor by default (like Textual TUI)."""
        # Show plate manager by default
        self.show_plate_manager()

        # Show pipeline editor by default
        self.show_pipeline_editor()

    def show_plate_manager(self):
        """Show plate manager window (mirrors Textual TUI pattern)."""
        if "plate_manager" not in self.floating_windows:
            from openhcs.pyqt_gui.widgets.plate_manager import PlateManagerWidget

            # Create floating window
            window = QDialog(self)
            window.setWindowTitle("Plate Manager")
            window.setModal(False)
            window.resize(600, 400)

            # Add widget to window
            layout = QVBoxLayout(window)
            plate_widget = PlateManagerWidget(
                self.file_manager,
                self.service_adapter,
                self.service_adapter.get_current_color_scheme()
            )
            layout.addWidget(plate_widget)

            self.floating_windows["plate_manager"] = window

            # Connect to pipeline editor if it exists (mirrors Textual TUI)
            self._connect_plate_to_pipeline_manager(plate_widget)

        # Show the window
        self.floating_windows["plate_manager"].show()
        self.floating_windows["plate_manager"].raise_()
        self.floating_windows["plate_manager"].activateWindow()

    def show_pipeline_editor(self):
        """Show pipeline editor window (mirrors Textual TUI pattern)."""
        if "pipeline_editor" not in self.floating_windows:
            from openhcs.pyqt_gui.widgets.pipeline_editor import PipelineEditorWidget

            # Create floating window
            window = QDialog(self)
            window.setWindowTitle("Pipeline Editor")
            window.setModal(False)
            window.resize(800, 600)

            # Add widget to window
            layout = QVBoxLayout(window)
            pipeline_widget = PipelineEditorWidget(
                self.file_manager,
                self.service_adapter,
                self.service_adapter.get_current_color_scheme()
            )
            layout.addWidget(pipeline_widget)

            self.floating_windows["pipeline_editor"] = window

            # Connect to plate manager for current plate selection (mirrors Textual TUI)
            self._connect_pipeline_to_plate_manager(pipeline_widget)

        # Show the window
        self.floating_windows["pipeline_editor"].show()
        self.floating_windows["pipeline_editor"].raise_()
        self.floating_windows["pipeline_editor"].activateWindow()



    def show_image_browser(self):
        """Show image browser window."""
        if "image_browser" not in self.floating_windows:
            from openhcs.pyqt_gui.widgets.image_browser import ImageBrowserWidget
            from openhcs.pyqt_gui.widgets.plate_manager import PlateManagerWidget

            # Create floating window
            window = QDialog(self)
            window.setWindowTitle("Image Browser")
            window.setModal(False)
            window.resize(900, 600)

            # Add widget to window
            layout = QVBoxLayout(window)
            image_browser_widget = ImageBrowserWidget(
                orchestrator=None,
                color_scheme=self.service_adapter.get_current_color_scheme()
            )
            layout.addWidget(image_browser_widget)

            self.floating_windows["image_browser"] = window

            # Connect to plate manager to get current orchestrator
            if "plate_manager" in self.floating_windows:
                plate_dialog = self.floating_windows["plate_manager"]
                plate_widget = plate_dialog.findChild(PlateManagerWidget)
                if plate_widget:
                    # Connect to plate selection changes
                    def on_plate_selected():
                        if hasattr(plate_widget, 'get_selected_orchestrator'):
                            orchestrator = plate_widget.get_selected_orchestrator()
                            if orchestrator:
                                image_browser_widget.set_orchestrator(orchestrator)

                    # Try to connect to selection signal if it exists
                    if hasattr(plate_widget, 'plate_selected'):
                        plate_widget.plate_selected.connect(on_plate_selected)

                    # Set initial orchestrator if available
                    on_plate_selected()

        # Show the window
        self.floating_windows["image_browser"].show()
        self.floating_windows["image_browser"].raise_()
        self.floating_windows["image_browser"].activateWindow()

    def _initialize_log_viewer(self):
        """
        Initialize Log Viewer on startup (hidden) for continuous log monitoring.

        This ensures all server logs are captured regardless of when the
        Log Viewer window is opened by the user.
        """
        from openhcs.pyqt_gui.widgets.log_viewer import LogViewerWindow

        # Create floating window (hidden)
        window = QDialog(self)
        window.setWindowTitle("Log Viewer")
        window.setModal(False)
        window.resize(900, 700)

        # Add widget to window
        layout = QVBoxLayout(window)
        log_viewer_widget = LogViewerWindow(self.file_manager, self.service_adapter)
        layout.addWidget(log_viewer_widget)

        self.floating_windows["log_viewer"] = window

        # Window stays hidden until user opens it
        logger.info("Log Viewer initialized (hidden) - monitoring for new logs")

    def show_log_viewer(self):
        """Show log viewer window (mirrors Textual TUI pattern)."""
        # Log viewer is already initialized on startup, just show it
        if "log_viewer" in self.floating_windows:
            self.floating_windows["log_viewer"].show()
            self.floating_windows["log_viewer"].raise_()
            self.floating_windows["log_viewer"].activateWindow()
        else:
            # Fallback: initialize if somehow not created
            self._initialize_log_viewer()
            self.show_log_viewer()

    def show_zmq_server_manager(self):
        """Show ZMQ server manager window."""
        if "zmq_server_manager" not in self.floating_windows:
            from openhcs.pyqt_gui.widgets.shared.zmq_server_manager import ZMQServerManagerWidget
            from openhcs.constants.constants import DEFAULT_NAPARI_STREAM_PORT

            # Create floating window
            window = QDialog(self)
            window.setWindowTitle("ZMQ Server Manager")
            window.setModal(False)
            window.resize(600, 400)

            # Add widget to window
            layout = QVBoxLayout(window)

            # Scan common ports:
            # - 7777: Default ZMQ execution server
            # - 5555-5564: Napari viewers (10 ports)
            # - 5565-5574: Fiji viewers (10 ports, non-overlapping with Napari)
            napari_ports = [DEFAULT_NAPARI_STREAM_PORT + i for i in range(10)]
            fiji_ports = [5565 + i for i in range(10)]  # 5565-5574 (avoid overlap with Napari)
            ports_to_scan = [7777] + napari_ports + fiji_ports

            zmq_manager_widget = ZMQServerManagerWidget(
                ports_to_scan=ports_to_scan,
                title="ZMQ Servers (Execution + Napari + Fiji)",
                style_generator=self.service_adapter.get_style_generator()
            )

            # Connect log file opened signal to log viewer
            zmq_manager_widget.log_file_opened.connect(self._open_log_file_in_viewer)

            layout.addWidget(zmq_manager_widget)

            self.floating_windows["zmq_server_manager"] = window

        # Show window
        self.floating_windows["zmq_server_manager"].show()
        self.floating_windows["zmq_server_manager"].raise_()
        self.floating_windows["zmq_server_manager"].activateWindow()

    def _open_log_file_in_viewer(self, log_file_path: str):
        """
        Open a log file in the log viewer.

        Args:
            log_file_path: Path to log file to open
        """
        # Show log viewer if not already open
        self.show_log_viewer()

        # Switch to the log file
        if "log_viewer" in self.floating_windows:
            log_dialog = self.floating_windows["log_viewer"]
            from openhcs.pyqt_gui.widgets.log_viewer import LogViewerWindow
            log_viewer_widget = log_dialog.findChild(LogViewerWindow)
            if log_viewer_widget:
                # Switch to the log file
                from pathlib import Path
                log_viewer_widget.switch_to_log(Path(log_file_path))
                logger.info(f"Switched log viewer to: {log_file_path}")

    def setup_menu_bar(self):
        """Setup application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        
       # Theme submenu
        theme_menu = file_menu.addMenu("&Theme")

        # Dark theme action
        dark_theme_action = QAction("&Dark Theme", self)
        dark_theme_action.triggered.connect(self.switch_to_dark_theme)
        theme_menu.addAction(dark_theme_action)

        # Light theme action
        light_theme_action = QAction("&Light Theme", self)
        light_theme_action.triggered.connect(self.switch_to_light_theme)
        theme_menu.addAction(light_theme_action)

        theme_menu.addSeparator()

        # Load theme from file action
        load_theme_action = QAction("&Load Theme from File...", self)
        load_theme_action.triggered.connect(self.load_theme_from_file)
        theme_menu.addAction(load_theme_action)

        # Save theme to file action
        save_theme_action = QAction("&Save Theme to File...", self)
        save_theme_action.triggered.connect(self.save_theme_to_file)
        theme_menu.addAction(save_theme_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Plate Manager window
        plate_action = QAction("&Plate Manager", self)
        plate_action.setShortcut("Ctrl+P")
        plate_action.triggered.connect(self.show_plate_manager)
        view_menu.addAction(plate_action)

        # Pipeline Editor window
        pipeline_action = QAction("Pipeline &Editor", self)
        pipeline_action.setShortcut("Ctrl+E")
        pipeline_action.triggered.connect(self.show_pipeline_editor)
        view_menu.addAction(pipeline_action)

        # Image Browser window
        image_browser_action = QAction("&Image Browser", self)
        image_browser_action.setShortcut("Ctrl+I")
        image_browser_action.triggered.connect(self.show_image_browser)
        view_menu.addAction(image_browser_action)

        # Log Viewer window
        log_action = QAction("&Log Viewer", self)
        log_action.setShortcut("Ctrl+L")
        log_action.triggered.connect(self.show_log_viewer)
        view_menu.addAction(log_action)

        # ZMQ Server Manager window
        zmq_server_action = QAction("&ZMQ Server Manager", self)
        zmq_server_action.setShortcut("Ctrl+Z")
        zmq_server_action.triggered.connect(self.show_zmq_server_manager)
        view_menu.addAction(zmq_server_action)

        # Configuration action
        config_action = QAction("&Global Configuration", self)
        config_action.setShortcut("Ctrl+G")
        config_action.triggered.connect(self.show_configuration)
        view_menu.addAction(config_action)

        # Generate Synthetic Plate action
        generate_plate_action = QAction("Generate &Synthetic Plate", self)
        generate_plate_action.setShortcut("Ctrl+Shift+G")
        generate_plate_action.triggered.connect(self.show_synthetic_plate_generator)
        view_menu.addAction(generate_plate_action)

        view_menu.addSeparator()


        # Help menu
        help_menu = menubar.addMenu("&Help")

        # General help action
        help_action = QAction("&Documentation", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

    
    def setup_status_bar(self):
        """Setup application status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("OpenHCS PyQt6 GUI Ready")

        # Add graph layout toggle button to the right side of status bar
        # Only add if system monitor widget exists and has the method
        if hasattr(self, 'system_monitor') and hasattr(self.system_monitor, 'create_layout_toggle_button'):
            toggle_button = self.system_monitor.create_layout_toggle_button()
            self.status_bar.addPermanentWidget(toggle_button)

        # Connect status message signal
        self.status_message.connect(self.status_bar.showMessage)
    
    def setup_connections(self):
        """Setup signal/slot connections."""
        # Connect config changes
        self.config_changed.connect(self.on_config_changed)
        
        # Connect service adapter to application
        self.service_adapter.set_global_config(self.global_config)
        
        # Setup auto-save timer for window state
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.save_window_state)
        self.auto_save_timer.start(30000)  # Save every 30 seconds
    
    def restore_window_state(self):
        """Restore window state from settings."""
        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            window_state = self.settings.value("windowState")
            if window_state:
                self.restoreState(window_state)
                
        except Exception as e:
            logger.warning(f"Failed to restore window state: {e}")
    
    def save_window_state(self):
        """Save window state to settings."""
        # Skip settings save for now to prevent hanging
        # TODO: Investigate QSettings hanging issue
        logger.debug("Skipping window state save to prevent hanging")
    
    # Menu action handlers
    def new_pipeline(self):
        """Create new pipeline."""
        if "pipeline_editor" in self.dock_widgets:
            pipeline_widget = self.dock_widgets["pipeline_editor"].widget()
            if hasattr(pipeline_widget, 'new_pipeline'):
                pipeline_widget.new_pipeline()
    
    def open_pipeline(self):
        """Open existing pipeline."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Pipeline",
            "",
            "Function Files (*.func);;All Files (*)"
        )
        
        if file_path and "pipeline_editor" in self.dock_widgets:
            pipeline_widget = self.dock_widgets["pipeline_editor"].widget()
            if hasattr(pipeline_widget, 'load_pipeline'):
                pipeline_widget.load_pipeline(Path(file_path))
    
    def save_pipeline(self):
        """Save current pipeline."""
        if "pipeline_editor" in self.dock_widgets:
            pipeline_widget = self.dock_widgets["pipeline_editor"].widget()
            if hasattr(pipeline_widget, 'save_pipeline'):
                pipeline_widget.save_pipeline()
    
    def show_configuration(self):
        """Show configuration dialog for global config editing."""
        from openhcs.pyqt_gui.windows.config_window import ConfigWindow

        def handle_config_save(new_config):
            """Handle configuration save (mirrors Textual TUI pattern)."""
            # new_config is already a GlobalPipelineConfig (concrete class)
            self.global_config = new_config

            # Update thread-local storage for MaterializationPathConfig defaults
            from openhcs.core.config import GlobalPipelineConfig
            from openhcs.config_framework.global_config import set_global_config_for_editing
            set_global_config_for_editing(GlobalPipelineConfig, new_config)

            # Emit signal for other components to update
            self.config_changed.emit(new_config)

            # Save config to cache for future sessions (matches TUI)
            self._save_config_to_cache(new_config)

        # Use concrete GlobalPipelineConfig for global config editing (static context)
        config_window = ConfigWindow(
            GlobalPipelineConfig,  # config_class (concrete class for static context)
            self.service_adapter.get_global_config(),  # current_config (concrete instance)
            handle_config_save,    # on_save_callback
            self.service_adapter.get_current_color_scheme(),  # color_scheme
            self                   # parent
        )
        # Show as non-modal window (like plate manager and pipeline editor)
        config_window.show()
        config_window.raise_()
        config_window.activateWindow()

    def _connect_pipeline_to_plate_manager(self, pipeline_widget):
        """Connect pipeline editor to plate manager (mirrors Textual TUI pattern)."""
        # Get plate manager if it exists
        if "plate_manager" in self.floating_windows:
            plate_manager_window = self.floating_windows["plate_manager"]

            # Find the actual plate manager widget
            plate_manager_widget = None
            for child in plate_manager_window.findChildren(QWidget):
                if hasattr(child, 'selected_plate_path') and hasattr(child, 'orchestrators'):
                    plate_manager_widget = child
                    break

            if plate_manager_widget:
                # Connect plate selection signal to pipeline editor (mirrors Textual TUI)
                plate_manager_widget.plate_selected.connect(pipeline_widget.set_current_plate)

                # Connect orchestrator config changed signal for placeholder refresh
                plate_manager_widget.orchestrator_config_changed.connect(pipeline_widget.on_orchestrator_config_changed)

                # Set pipeline editor reference in plate manager
                if hasattr(plate_manager_widget, 'set_pipeline_editor'):
                    plate_manager_widget.set_pipeline_editor(pipeline_widget)

                # Set current plate if one is already selected
                if plate_manager_widget.selected_plate_path:
                    pipeline_widget.set_current_plate(plate_manager_widget.selected_plate_path)

                logger.debug("Connected pipeline editor to plate manager")
            else:
                logger.warning("Could not find plate manager widget to connect")
        else:
            logger.debug("Plate manager not yet created - connection will be made when both exist")

    def _connect_plate_to_pipeline_manager(self, plate_manager_widget):
        """Connect plate manager to pipeline editor (reverse direction)."""
        # Get pipeline editor if it exists
        if "pipeline_editor" in self.floating_windows:
            pipeline_editor_window = self.floating_windows["pipeline_editor"]

            # Find the actual pipeline editor widget
            pipeline_editor_widget = None
            for child in pipeline_editor_window.findChildren(QWidget):
                if hasattr(child, 'set_current_plate') and hasattr(child, 'pipeline_steps'):
                    pipeline_editor_widget = child
                    break

            if pipeline_editor_widget:
                # Connect plate selection signal to pipeline editor (mirrors Textual TUI)
                plate_manager_widget.plate_selected.connect(pipeline_editor_widget.set_current_plate)

                # Connect orchestrator config changed signal for placeholder refresh
                plate_manager_widget.orchestrator_config_changed.connect(pipeline_editor_widget.on_orchestrator_config_changed)

                # Set pipeline editor reference in plate manager
                if hasattr(plate_manager_widget, 'set_pipeline_editor'):
                    plate_manager_widget.set_pipeline_editor(pipeline_editor_widget)

                # Set current plate if one is already selected
                if plate_manager_widget.selected_plate_path:
                    pipeline_editor_widget.set_current_plate(plate_manager_widget.selected_plate_path)

                logger.debug("Connected plate manager to pipeline editor")
            else:
                logger.warning("Could not find pipeline editor widget to connect")
        else:
            logger.debug("Pipeline editor not yet created - connection will be made when both exist")

    def show_synthetic_plate_generator(self):
        """Show synthetic plate generator window."""
        from openhcs.pyqt_gui.windows.synthetic_plate_generator_window import SyntheticPlateGeneratorWindow

        # Create and show the generator window
        generator_window = SyntheticPlateGeneratorWindow(
            color_scheme=self.service_adapter.get_current_color_scheme(),
            parent=self
        )

        # Connect the plate_generated signal to add the plate to the manager
        generator_window.plate_generated.connect(self._on_synthetic_plate_generated)

        # Show the window
        generator_window.exec()

    def _on_synthetic_plate_generated(self, output_dir: str, pipeline_path: str):
        """
        Handle synthetic plate generation completion.

        Args:
            output_dir: Path to the generated plate directory
            pipeline_path: Path to the test pipeline to load
        """
        from pathlib import Path

        # Get the plate manager widget
        if "plate_manager" in self.floating_windows:
            plate_dialog = self.floating_windows["plate_manager"]
            from openhcs.pyqt_gui.widgets.plate_manager import PlateManagerWidget
            plate_manager = plate_dialog.findChild(PlateManagerWidget)

            if plate_manager:
                # Add the generated plate - this triggers plate_selected signal
                # which automatically updates pipeline editor via existing connections
                plate_manager.add_plate_callback([Path(output_dir)])

                # Load the test pipeline
                self._load_pipeline_file(pipeline_path)

                # Show the plate manager window if it's hidden
                self.show_plate_manager()

                logger.info(f"Added synthetic plate and loaded test pipeline: {output_dir}")

    def _load_pipeline_file(self, pipeline_path: str):
        """
        Load a pipeline file into the pipeline editor.

        Args:
            pipeline_path: Path to the pipeline file to load
        """
        try:
            # Get the pipeline editor widget
            if "pipeline_editor" not in self.floating_windows:
                logger.debug("Pipeline editor not available - skipping pipeline load")
                return

            pipeline_dialog = self.floating_windows["pipeline_editor"]
            from openhcs.pyqt_gui.widgets.pipeline_editor import PipelineEditorWidget
            pipeline_editor = pipeline_dialog.findChild(PipelineEditorWidget)

            if not pipeline_editor:
                logger.debug("Pipeline editor widget not found - skipping pipeline load")
                return

            # Load the pipeline file
            from pathlib import Path
            pipeline_file = Path(pipeline_path)

            if not pipeline_file.exists():
                logger.warning(f"Pipeline file not found: {pipeline_path}")
                return

            # For .py files, read code and use existing _handle_edited_pipeline_code
            if pipeline_file.suffix == '.py':
                with open(pipeline_file, 'r') as f:
                    code = f.read()

                # Use existing infrastructure that already handles code execution
                pipeline_editor._handle_edited_pipeline_code(code)
                logger.info(f"Loaded pipeline from Python file: {pipeline_path}")
            else:
                # For pickled files, use existing infrastructure
                pipeline_editor.load_pipeline_from_file(pipeline_file)
                logger.info(f"Loaded pipeline: {pipeline_path}")

        except Exception as e:
            logger.error(f"Failed to load pipeline: {e}", exc_info=True)



    def show_help(self):
        """Opens documentation URL in default web browser."""
        from openhcs.constants.constants import DOCUMENTATION_URL

        url =  (DOCUMENTATION_URL)
        if not QDesktopServices.openUrl(QUrl.fromUserInput(url)):
            #fallback for wsl users because it wants to be special
            webbrowser.open(url)
            
    
    def on_config_changed(self, new_config: GlobalPipelineConfig):
        """Handle global configuration changes."""
        self.global_config = new_config
        self.service_adapter.set_global_config(new_config)

        # Notify all floating windows of config change
        for window in self.floating_windows.values():
            # Get the widget from the window's layout
            layout = window.layout()
            widget = layout.itemAt(0).widget()
            # Only call on_config_changed if the widget has this method
            if hasattr(widget, 'on_config_changed'):
                widget.on_config_changed(new_config)

    def _save_config_to_cache(self, config):
        """Save config to cache asynchronously (matches TUI pattern)."""
        try:
            from openhcs.pyqt_gui.services.config_cache_adapter import get_global_config_cache
            cache = get_global_config_cache()
            cache.save_config_to_cache_async(config)
            logger.info("Global config save to cache initiated")
        except Exception as e:
            logger.error(f"Error saving global config to cache: {e}")

    def closeEvent(self, event):
        """Handle application close event."""
        logger.info("Starting application shutdown...")

        try:
            # Stop system monitor first with timeout
            if hasattr(self, 'system_monitor'):
                logger.info("Stopping system monitor...")
                self.system_monitor.stop_monitoring()

            # Close floating windows and cleanup their resources
            for window_name, window in list(self.floating_windows.items()):
                try:
                    layout = window.layout()
                    if layout and layout.count() > 0:
                        widget = layout.itemAt(0).widget()
                        if hasattr(widget, 'cleanup'):
                            widget.cleanup()
                    window.close()
                    window.deleteLater()
                except Exception as e:
                    logger.warning(f"Error cleaning up window {window_name}: {e}")

            # Clear floating windows dict
            self.floating_windows.clear()

            # Save window state
            self.save_window_state()

            # Force Qt to process pending events before shutdown
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()

            # Additional cleanup - force garbage collection
            import gc
            gc.collect()

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        # Accept close event
        event.accept()
        logger.info("OpenHCS PyQt6 application closed")

        # Force application quit with a short delay
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: QApplication.instance().quit())

    # ========== THEME MANAGEMENT METHODS ==========

    def switch_to_dark_theme(self):
        """Switch to dark theme variant."""
        self.service_adapter.switch_to_dark_theme()
        self.status_message.emit("Switched to dark theme")

    def switch_to_light_theme(self):
        """Switch to light theme variant."""
        self.service_adapter.switch_to_light_theme()
        self.status_message.emit("Switched to light theme")

    def load_theme_from_file(self):
        """Load theme from JSON configuration file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Theme Configuration",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            success = self.service_adapter.load_theme_from_config(file_path)
            if success:
                self.status_message.emit(f"Loaded theme from {Path(file_path).name}")
            else:
                QMessageBox.warning(
                    self,
                    "Theme Load Error",
                    f"Failed to load theme from {Path(file_path).name}"
                )

    def save_theme_to_file(self):
        """Save current theme to JSON configuration file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Theme Configuration",
            "pyqt6_color_scheme.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            success = self.service_adapter.save_current_theme(file_path)
            if success:
                self.status_message.emit(f"Saved theme to {Path(file_path).name}")
            else:
                QMessageBox.warning(
                    self,
                    "Theme Save Error",
                    f"Failed to save theme to {Path(file_path).name}"
                )
