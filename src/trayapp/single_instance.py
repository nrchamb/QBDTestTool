"""
Single instance management for QuickBooks Desktop Test Tool.

Prevents multiple instances of the application from running simultaneously
using a PID file-based approach.
"""

import os
import psutil
from pathlib import Path
from config.app_config import CONFIG_DIR


_pid_file_path: Path = None
_lock_acquired = False


def _get_pid_file_path() -> Path:
    """Get the path to the PID file."""
    global _pid_file_path
    if _pid_file_path is None:
        # Ensure config directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _pid_file_path = CONFIG_DIR / "qbd_test_tool.pid"
    return _pid_file_path


def _read_pid_file() -> int:
    """
    Read the PID from the PID file.

    Returns:
        int: The PID stored in the file, or None if file doesn't exist or is invalid
    """
    pid_file = _get_pid_file_path()
    if not pid_file.exists():
        return None

    try:
        with open(pid_file, 'r') as f:
            pid_str = f.read().strip()
            return int(pid_str)
    except (ValueError, IOError):
        return None


def _write_pid_file(pid: int):
    """
    Write the PID to the PID file.

    Args:
        pid: The process ID to write
    """
    pid_file = _get_pid_file_path()
    try:
        with open(pid_file, 'w') as f:
            f.write(str(pid))
    except IOError as e:
        print(f"[Single Instance] Warning: Could not write PID file: {e}")


def _remove_pid_file():
    """Remove the PID file if it exists."""
    pid_file = _get_pid_file_path()
    try:
        if pid_file.exists():
            pid_file.unlink()
    except IOError as e:
        print(f"[Single Instance] Warning: Could not remove PID file: {e}")


def _is_process_running(pid: int) -> bool:
    """
    Check if a process with the given PID is currently running.

    Args:
        pid: The process ID to check

    Returns:
        bool: True if the process is running, False otherwise
    """
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False


def check_existing() -> tuple:
    """
    Check if another instance of the application is already running.

    Returns:
        tuple: (is_running: bool, pid: int or None)
            - is_running: True if another instance is running
            - pid: The PID of the running instance, or None if not running
    """
    existing_pid = _read_pid_file()

    if existing_pid is None:
        # No PID file exists
        return (False, None)

    if _is_process_running(existing_pid):
        # PID file exists and process is running
        return (True, existing_pid)
    else:
        # PID file exists but process is not running (stale file)
        print(f"[Single Instance] Removing stale PID file (PID {existing_pid} not running)")
        _remove_pid_file()
        return (False, None)


def acquire_lock() -> bool:
    """
    Acquire the single instance lock by creating a PID file with the current process ID.

    Returns:
        bool: True if lock acquired successfully, False otherwise
    """
    global _lock_acquired

    # Check if lock already acquired in this process
    if _lock_acquired:
        return True

    # Get current process ID
    current_pid = os.getpid()

    # Write PID file
    _write_pid_file(current_pid)
    _lock_acquired = True

    print(f"[Single Instance] Lock acquired (Main App PID: {current_pid})")
    return True


def release_lock():
    """
    Release the single instance lock by removing the PID file.
    """
    global _lock_acquired

    if not _lock_acquired:
        return

    _remove_pid_file()
    _lock_acquired = False
    print("[Single Instance] Lock released")
