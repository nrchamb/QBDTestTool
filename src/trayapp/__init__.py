"""
Tray app package for QuickBooks Desktop Test Tool.

Handles system tray icon and daemon process management.
"""

from tkinter import messagebox
from .tray_icon import TrayIconManager
from .daemon_actions import on_closing, force_close
from . import single_instance


def check_and_acquire_lock() -> bool:
    """
    Check for existing application instance and acquire lock if available.

    If another instance is already running, shows a message box to the user
    and returns False. Otherwise, acquires the single-instance lock and returns True.

    Returns:
        bool: True if lock acquired (no other instance running), False otherwise
    """
    is_running, existing_pid = single_instance.check_existing()

    if is_running:
        # Another instance is running
        messagebox.showwarning(
            "Already Running",
            f"QBD Test Tool is already running (PID: {existing_pid})\n\n"
            f"Please close the existing instance before starting a new one."
        )
        return False

    # No other instance, acquire lock
    single_instance.acquire_lock()
    return True


__all__ = [
    'TrayIconManager',
    'on_closing',
    'force_close',
    'check_and_acquire_lock',
]
