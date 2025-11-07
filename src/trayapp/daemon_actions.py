"""
Daemon process action handlers for QuickBooks Desktop Test Tool.

Handles graceful and forced shutdown of the connection manager daemon.
"""

from config import AppConfig
from qb import stop_manager
from . import single_instance


def on_closing(app):
    """
    Handle graceful application shutdown.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Set tray icon to yellow (shutting down)
    if hasattr(app, 'tray_icon'):
        app.tray_icon.set_state('yellow')

    # Stop monitoring if active
    if app.monitoring_stop_flag is False and hasattr(app, 'monitor_thread'):
        app.monitoring_stop_flag = True
        if app.monitor_thread and app.monitor_thread.is_alive():
            print("Waiting for monitoring thread to stop...")
            app.monitor_thread.join(timeout=5.0)

    # Stop connection manager
    print("Stopping connection manager...")
    stop_manager()

    # Release single instance lock
    single_instance.release_lock()

    # Stop tray icon
    if hasattr(app, 'tray_icon'):
        app.tray_icon.stop()

    # Save window geometry before closing
    try:
        geometry = app.root.winfo_geometry()  # Returns "widthxheight+x+y"
        # Parse geometry string: "900x700+100+50"
        parts = geometry.replace('+', ' ').replace('x', ' ').split()
        if len(parts) == 4:
            width, height, x, y = map(int, parts)
            AppConfig.save_window_geometry(width, height, x, y)
            print(f"Saved window geometry: {width}x{height}+{x}+{y}")
    except Exception as e:
        print(f"Error saving window geometry: {e}")

    # Save UI state (activity log collapsed state and sash positions)
    try:
        if hasattr(app, 'create_log_collapsed'):
            activity_log_collapsed = app.create_log_collapsed.get()

            # Get sash positions (only if logs are expanded)
            create_sash_pos = None
            monitor_sash_pos = None

            if not activity_log_collapsed:
                if hasattr(app, 'create_paned'):
                    try:
                        create_sash_pos = app.create_paned.sash_coord(0)[1]
                        print(f"Saving create log sash position: {create_sash_pos}")
                    except Exception as e:
                        print(f"Could not get create sash position: {e}")

                if hasattr(app, 'monitor_paned'):
                    try:
                        monitor_sash_pos = app.monitor_paned.sash_coord(0)[1]
                        print(f"Saving monitor log sash position: {monitor_sash_pos}")
                    except Exception as e:
                        print(f"Could not get monitor sash position: {e}")

            AppConfig.save_ui_state(activity_log_collapsed, create_sash_pos, monitor_sash_pos)
            print(f"Saved UI state: activity_log_collapsed={activity_log_collapsed}")
    except Exception as e:
        print(f"Error saving UI state: {e}")

    # Destroy window
    app.root.destroy()


def force_close(app):
    """
    Force close connection manager and exit immediately.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    print("Force closing connection manager...")

    # Set tray icon to yellow
    if hasattr(app, 'tray_icon'):
        app.tray_icon.set_state('yellow')

    # Import for process termination
    from qb.ipc_client import _manager_process

    # Kill manager process immediately
    if _manager_process and _manager_process.is_alive():
        print(f"Terminating manager process (PID: {_manager_process.pid})")
        _manager_process.terminate()
        _manager_process.join(timeout=2.0)

        if _manager_process.is_alive():
            print("Manager still alive, killing forcefully...")
            _manager_process.kill()

    # Release single instance lock
    single_instance.release_lock()

    # Stop tray icon
    if hasattr(app, 'tray_icon'):
        app.tray_icon.stop()

    # Destroy window
    app.root.destroy()
