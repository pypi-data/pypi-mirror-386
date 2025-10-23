"""
OpenHCS Textual TUI Main Application

A modern terminal user interface built with Textual framework.
This is the main application class that orchestrates the entire TUI.
"""

import asyncio
import logging
import traceback
from typing import Optional

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.containers import Container
from textual.widgets import Static, Button, TextArea

# OpenHCS imports
from openhcs.core.config import GlobalPipelineConfig
from openhcs.io.base import storage_registry
from openhcs.io.filemanager import FileManager

# Widget imports (will be created)
from .widgets.main_content import MainContent
from .widgets.status_bar import StatusBar

# Textual-window imports
from textual_window import Window, WindowSwitcher, window_manager, TilingLayout
from openhcs.textual_tui.widgets.custom_window_bar import CustomWindowBar
from openhcs.textual_tui.windows.base_window import BaseOpenHCSWindow



logger = logging.getLogger(__name__)


class ErrorDialog(BaseOpenHCSWindow):
    """Error dialog with syntax highlighting using textual-window system."""

    def __init__(self, error_message: str, error_details: str = ""):
        self.error_message = error_message
        self.error_details = error_details
        super().__init__(
            window_id="error_dialog",
            title="🚨 ERROR",
            mode="temporary"
        )

    def compose(self) -> ComposeResult:
        """Compose the error dialog content."""
        # Error message
        yield Static(self.error_message, classes="error-message", markup=False)

        # Error details with syntax highlighting if available
        if self.error_details:
            yield TextArea(
                text=self.error_details,
                language="python",  # Python syntax highlighting for tracebacks
                theme="monokai",
                read_only=True,  # Make it read-only but selectable
                show_line_numbers=True,
                soft_wrap=True,
                id="error_content"
            )

        # Close button
        with Container(classes="dialog-buttons"):
            yield Button("Close", id="close", compact=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close":
            self.close_window()

    DEFAULT_CSS = """
    ErrorDialog {
        width: auto;
        height: auto;
        max-width: 120;
        max-height: 40;
        min-width: 50;
        min-height: 15;
    }

    .error-message {
        color: $error;
        text-style: bold;
        margin-bottom: 1;
        text-align: center;
    }

    #error_content {
        height: auto;
        width: auto;
        margin: 0;
        max-height: 30;
        min-height: 5;
        border: solid $primary;
    }
    """


class OpenHCSTUIApp(App):
    """
    Main OpenHCS Textual TUI Application.

    This app provides a complete interface for OpenHCS pipeline management
    with proper reactive state management and clean architectural boundaries.
    """
    CSS_PATH = "styles.css"

    # Blocking window for pseudo-modal behavior
    blocking_window = None
#    CSS = """
#    /* General dialog styling */
#    .dialog {
#        background: $surface;
#        border: tall $primary;
#        padding: 1 2;
#        width: auto;
#        height: auto;
#    }
#
#    /* SelectionList styling - remove circles, keep highlighting */
#    SelectionList > .selection-list--option {
#        padding-left: 1;
#        text-style: none;
#    }
#
#    SelectionList > .selection-list--option-highlighted {
#        background: $accent;
#        color: $text;
#    }
#
#    /* MenuBar */
#    MenuBar {
#        height: 3;
#        border: solid white;
#    }
#
#    /* All buttons - uniform height and styling */
#    Button {
#        height: 1;
#    }
#
#    /* MenuBar buttons - content-based width */
#    MenuBar Button {
#        margin: 0 1;
#        width: auto;
#    }
#
#    /* MenuBar title - properly centered */
#    MenuBar Static {
#        text-align: center;
#        content-align: center middle;
#        width: 1fr;
#        text-style: bold;
#    }
#
#    /* Function list header buttons - specific styling for spacing */
#    #function_list_header Button {
#        margin: 0 1; /* 0 vertical, 1 horizontal margin */
#        width: auto; /* Let buttons size to their content */
#    }
#
#    /* Main content containers with proper borders and responsive sizing */
#    #plate_manager_container {
#        border: solid white;
#        width: 1fr;
#        min-width: 0;
#    }
#
#    #pipeline_editor_container {
#        border: solid white;
#        width: 1fr;
#        min-width: 0;
#    }
#
#    /* StatusBar */
#    StatusBar {
#        height: 3;
#        border: solid white;
#    }
#
#    /* Button containers - full width */
#    #plate_manager_container Horizontal,
#    #pipeline_editor_container Horizontal {
#        width: 100%;
#    }
#
#    /* Content area buttons - responsive width distribution */
#    #plate_manager_container Button,
#    #pipeline_editor_container Button {
#        width: 1fr;
#        margin: 0;
#        min-width: 0;
#    }
#
#    /* App fills terminal height properly */
#    OpenHCSTUIApp {
#        height: 100vh;
#    }
#
#    /* Main content layout fills remaining space and is responsive */
#    MainContent {
#        height: 1fr;
#        width: 100%;
#    }
#
#    /* Main horizontal layout is responsive */
#    MainContent > Horizontal {
#        width: 100%;
#        height: 100%;
#    }
#
#
#    /* Content areas adapt to available space */
#    ScrollableContainer {
#        height: 1fr;
#    }
#
#    /* Static content styling */
#    Static {
#        text-align: center;
#    }
#
#
#    """
    
    def _generate_bindings():
        from openhcs.core.config import TilingKeybindings

        keybindings = TilingKeybindings()

        app_bindings = [
            ("ctrl+q", "quit", "Quit"),
            ("tab", "focus_next", "Next"),
            ("shift+tab", "focus_previous", "Previous"),
            ("f1", "toggle_window_switcher", "Switch Windows"),
        ]

        # Add all tiling keybindings from config
        for field_name in keybindings.__dataclass_fields__:
            binding = getattr(keybindings, field_name)
            app_bindings.append((binding.key, binding.action, binding.description))

        return app_bindings

    BINDINGS = _generate_bindings()
    
    # App-level reactive state
    current_status = reactive("Ready")
    
    def __init__(self, global_config: Optional[GlobalPipelineConfig] = None):
        """
        Initialize the OpenHCS TUI App.
        
        Args:
            global_config: Global configuration (uses default if None)
        """
        super().__init__()
        
        # Core configuration - minimal TUI responsibility
        self.global_config = global_config or GlobalPipelineConfig()
        
        # Create shared components (pattern from SimpleOpenHCSTUILauncher)
        self.storage_registry = storage_registry
        self.filemanager = FileManager(self.storage_registry)

        # Toolong compatibility attributes
        self.save_merge = None  # For Toolong LogView compatibility
        self.file_paths = []  # For LogScreen compatibility
        self.watcher = None  # For LogScreen compatibility
        self.merge = False  # For LogScreen compatibility

        logger.debug("OpenHCSTUIApp initialized with Textual reactive system")

    def configure_toolong(self, file_paths: list, watcher, merge: bool = False):
        """Configure app for Toolong LogScreen compatibility."""
        self.file_paths = file_paths
        self.watcher = watcher
        self.merge = merge
        logger.debug(f"App configured for Toolong with {len(file_paths)} files, merge={merge}")
    
    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        # TEMPORARILY DISABLED - testing if WindowSwitcher causes hangs
        # yield WindowSwitcher()  # Invisible Alt-Tab overlay

        # Custom WindowBar with no left button
        yield CustomWindowBar(dock="bottom", start_open=True)



        # Status bar for status messages
        yield StatusBar()

        # Main content fills the rest
        yield MainContent(
            filemanager=self.filemanager,
            global_config=self.global_config
        )
    
    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        logger.info("OpenHCS TUI mounted and ready")
        self.current_status = "OpenHCS TUI Ready"

        # Mount singleton toolong window BEFORE configuring tiling
        # This prevents it from being affected by the tiling system
        try:
            from openhcs.textual_tui.windows.toolong_window import ToolongWindow
            toolong_window = ToolongWindow()
            await self.mount(toolong_window)
            # Start minimized so it doesn't interfere with main UI
            toolong_window.open_state = False
        except Exception as e:
            logger.error(f"Failed to mount toolong window at startup: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Configure default window manager settings from separate TUI config
        from openhcs.core.config import TUIConfig
        tui_config = TUIConfig()  # Use default TUI configuration
        window_manager.set_tiling_layout(tui_config.default_tiling_layout)
        window_manager.set_window_gap(tui_config.default_window_gap)

        # Notify user about tiling mode if enabled in config
        if tui_config.enable_startup_notification:
            layout_name = tui_config.default_tiling_layout.value.replace('_', ' ').title()
            self.notify(f"Window Manager: {layout_name} tiling enabled (gap={tui_config.default_window_gap})", severity="information")



        # Status bar will automatically show this log message
        # No need to manually update it anymore

        # Add our start menu button to the WindowBar using the same pattern as window buttons
        logger.debug("🚀 APP MOUNT: About to add start menu button")
        try:
            await self._add_start_menu_button()
            logger.debug("🚀 APP MOUNT: Start menu button added")
        except Exception as e:
            logger.error(f"🚀 APP MOUNT: Start menu button failed: {e}")
            # Continue without start menu button for now

    def watch_current_status(self, status: str) -> None:
        """Watch for status changes and log them (status bar will show automatically)."""
        # Log the status change - status bar will pick it up automatically
        logger.info(status)
    


    def action_quit(self) -> None:
        """Handle quit action with aggressive cleanup."""
        logger.info("OpenHCS TUI shutting down")

        # Force cleanup of background threads before exit
        try:
            import threading
            import time

            # Give a moment for normal cleanup
            self.exit()

            # Schedule aggressive cleanup after a short delay
            def force_cleanup():
                time.sleep(0.5)  # Give normal exit a chance
                active_threads = [t for t in threading.enumerate() if t != threading.current_thread() and t.is_alive()]
                if active_threads:
                    logger.warning(f"Force cleaning up {len(active_threads)} threads on quit")
                    # Can't set daemon on running threads, just force exit
                    import os
                    os._exit(0)

            # Start cleanup thread as daemon
            cleanup_thread = threading.Thread(target=force_cleanup, daemon=True)
            cleanup_thread.start()

        except Exception as e:
            logger.debug(f"Error in quit cleanup: {e}")
            self.exit()

    def action_toggle_window_switcher(self):
        """Toggle the window switcher."""
        switcher = self.query_one(WindowSwitcher)
        switcher.action_toggle()  # Correct textual-window API method

    # Focus navigation actions - call existing window manager methods
    def action_focus_next_window(self) -> None:
        """Focus next window."""
        window_manager.focus_next_window()

    def action_focus_previous_window(self) -> None:
        """Focus previous window."""
        window_manager.focus_previous_window()

    # Layout control wrapper methods
    def action_set_horizontal_split(self) -> None:
        """Set horizontal split tiling."""
        window_manager.set_tiling_layout(TilingLayout.HORIZONTAL_SPLIT)
        self.notify("Tiling: Horizontal Split")

    def action_set_vertical_split(self) -> None:
        """Set vertical split tiling."""
        window_manager.set_tiling_layout(TilingLayout.VERTICAL_SPLIT)
        self.notify("Tiling: Vertical Split")

    def action_set_grid_layout(self) -> None:
        """Set grid layout tiling."""
        window_manager.set_tiling_layout(TilingLayout.GRID)
        self.notify("Tiling: Grid Layout")

    def action_set_master_detail(self) -> None:
        """Set master-detail tiling."""
        window_manager.set_tiling_layout(TilingLayout.MASTER_DETAIL)
        self.notify("Tiling: Master Detail")

    def action_toggle_floating(self) -> None:
        """Toggle floating mode."""
        current = window_manager.tiling_layout
        new_layout = TilingLayout.HORIZONTAL_SPLIT if current == TilingLayout.FLOATING else TilingLayout.FLOATING
        window_manager.set_tiling_layout(new_layout)
        self.notify("Tiling: Toggled Floating")

    # Window movement actions - call extracted window manager methods
    def action_move_focused_window_prev(self) -> None:
        """Move current window to previous position."""
        window_manager.move_focused_window_prev()

    def action_move_focused_window_next(self) -> None:
        """Move current window to next position."""
        window_manager.move_focused_window_next()

    def action_rotate_window_order_left(self) -> None:
        """Rotate all windows left."""
        window_manager.rotate_window_order_left()

    def action_rotate_window_order_right(self) -> None:
        """Rotate all windows right."""
        window_manager.rotate_window_order_right()

    # Gap control actions
    def action_gap_increase(self) -> None:
        """Increase gap between windows."""
        window_manager.adjust_window_gap(1)

    def action_gap_decrease(self) -> None:
        """Decrease gap between windows."""
        window_manager.adjust_window_gap(-1)

    # Bulk operation actions - call existing window manager methods
    def action_minimize_all_windows(self) -> None:
        """Minimize all windows."""
        window_manager.minimize_all_windows()
        self.notify("Minimized all windows")

    def action_open_all_windows(self) -> None:
        """Open all windows."""
        window_manager.open_all_windows()
        self.notify("Opened all windows")

    async def _add_start_menu_button(self):
        """Add our start menu button to the WindowBar at the leftmost position."""
        try:
            logger.debug("🚀 START MENU: Creating start menu button")
            from openhcs.textual_tui.widgets.start_menu_button import StartMenuButton

            # Get the CustomWindowBar
            logger.debug("🚀 START MENU: Getting CustomWindowBar")
            window_bar = self.query_one(CustomWindowBar)
            logger.debug(f"🚀 START MENU: Found window bar: {window_bar}")

            # Check if right button exists (no left button in CustomWindowBar)
            logger.debug("🚀 START MENU: Looking for right button")
            right_button = window_bar.query_one("#windowbar_button_right")
            logger.debug(f"🚀 START MENU: Found right button: {right_button}")

            # Add our start menu button at the very beginning (leftmost position)
            # Mount before the right button to be at the far left
            logger.debug("🚀 START MENU: Creating StartMenuButton")
            start_button = StartMenuButton(window_bar=window_bar, id="start_menu_button")
            logger.debug(f"🚀 START MENU: Created start button: {start_button}")

            logger.debug("🚀 START MENU: Mounting start button")
            await window_bar.mount(start_button, before=right_button)
            logger.debug("🚀 START MENU: Start menu button mounted successfully")

        except Exception as e:
            logger.error(f"🚀 START MENU: Failed to add start menu button: {e}")
            import traceback
            logger.error(f"🚀 START MENU: Traceback: {traceback.format_exc()}")
            raise



    def open_blocking_window(self, window_class, *args, **kwargs):
        """Open a blocking window that disables main UI interactions."""
        if self.blocking_window:
            return  # Only allow one blocking window at a time

        window = window_class(*args, **kwargs)
        self.blocking_window = window
        self._disable_main_interactions()
        self.mount(window)
        return window

    def _disable_main_interactions(self):
        """Disable main UI interactions when modal window is open."""
        # Note: MenuBar removed - interactions now handled by start menu
        pass

    def _enable_main_interactions(self):
        """Re-enable main UI interactions when modal window closes."""
        # Note: MenuBar removed - interactions now handled by start menu
        pass

    def on_window_closed(self, event: Window.Closed) -> None:
        """Handle window closed events from textual-window."""
        # Check if this is our blocking window
        # Event has window reference through WindowMessage base
        if event.control == self.blocking_window:
            self.blocking_window = None
            self._enable_main_interactions()

    def show_error(self, error_message: str, exception: Exception = None) -> None:
        """Show a global error dialog with optional exception details."""
        error_details = ""
        if exception:
            error_details = f"Exception: {type(exception).__name__}\n"
            error_details += f"Message: {str(exception)}\n\n"
            error_details += "Traceback:\n"
            error_details += traceback.format_exc()

        logger.error(f"Global error: {error_message}", exc_info=exception)

        # Show error dialog using window system
        from textual.css.query import NoMatches

        try:
            # Check if error dialog already exists
            window = self.query_one(ErrorDialog)
            # Update existing dialog
            window.error_message = error_message
            window.error_details = error_details
            window.open_state = True
        except NoMatches:
            # Create new error dialog window
            error_dialog = ErrorDialog(error_message, error_details)
            self.run_worker(self._mount_error_dialog(error_dialog))

    async def _mount_error_dialog(self, error_dialog):
        """Mount error dialog window."""
        await self.mount(error_dialog)
        error_dialog.open_state = True

    def _handle_exception(self, error: Exception) -> None:
        """Handle exceptions with special cases for Toolong internal errors."""
        # Check for known Toolong internal timing errors that are non-fatal
        error_str = str(error)
        if (
            "No nodes match" in error_str and
            ("FindDialog" in error_str or "Label" in error_str) and
            ("InfoOverlay" in error_str or "LogView" in error_str)
        ):
            # This is a known Toolong internal timing issue - log but don't crash
            logger.warning(f"Ignoring Toolong internal timing error: {error_str}")
            return

        # Log the error for debugging
        logger.error(f"Unhandled exception in TUI: {str(error)}", exc_info=True)

        # Re-raise the exception to let it crash loudly
        # This allows the global error handler to catch it
        raise error

    async def _on_exception(self, error: Exception) -> None:
        """Let async exceptions bubble up."""
        self._handle_exception(error)

    def _on_unhandled_exception(self, error: Exception) -> None:
        """Let unhandled exceptions bubble up."""
        self._handle_exception(error)

    async def on_unmount(self) -> None:
        """Clean up when app is shutting down with aggressive thread cleanup."""
        logger.info("OpenHCS TUI app unmounting, cleaning up threads...")

        # Force cleanup of any ReactiveLogMonitor instances
        try:
            from openhcs.textual_tui.widgets.reactive_log_monitor import ReactiveLogMonitor
            monitors = self.query(ReactiveLogMonitor)
            for monitor in monitors:
                monitor.stop_monitoring()
        except Exception as e:
            logger.debug(f"Error cleaning up ReactiveLogMonitors: {e}")

        # Force cleanup of any PlateManager workers
        try:
            from openhcs.textual_tui.widgets.plate_manager import PlateManager
            plate_managers = self.query(PlateManager)
            for pm in plate_managers:
                if hasattr(pm, '_stop_monitoring'):
                    pm._stop_monitoring()
        except Exception as e:
            logger.debug(f"Error cleaning up PlateManagers: {e}")

        # Aggressive thread cleanup
        try:
            import threading
            import time
            time.sleep(0.2)  # Give threads a moment to stop
            active_threads = [t for t in threading.enumerate() if t != threading.current_thread() and t.is_alive()]
            if active_threads:
                logger.warning(f"Found {len(active_threads)} active threads during shutdown")
                # Can't set daemon on running threads, just log them
        except Exception as e:
            logger.debug(f"Error checking threads: {e}")

        logger.info("OpenHCS TUI app cleanup complete")


async def main():
    """
    Main entry point for the OpenHCS Textual TUI.

    This function handles initialization and runs the application.
    Note: Logging is setup by the main entry point, not here.
    """
    logger.info("Starting OpenHCS Textual TUI from app.py...")

    try:
        # Load configuration with cache support
        from openhcs.textual_tui.services.config_cache_adapter import load_cached_global_config_tui as load_cached_global_config
        global_config = await load_cached_global_config()

        # REMOVED: setup_global_gpu_registry - this is now ONLY done in __main__.py
        # to avoid duplicate initialization
        logger.info("Using global_config with GPU registry already initialized by __main__.py")

        # Create and run the app
        app = OpenHCSTUIApp(global_config=global_config)
        await app.run_async()
        
    except KeyboardInterrupt:
        logger.info("TUI terminated by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
    finally:
        logger.info("OpenHCS Textual TUI finished")


if __name__ == "__main__":
    asyncio.run(main())
