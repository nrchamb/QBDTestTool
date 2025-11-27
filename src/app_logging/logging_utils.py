"""
Logging utilities for QuickBooks Desktop Test Tool.

Provides logging functions with log levels, rolling buffer support, and file logging.
"""

import tkinter as tk
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import AppConfig
from .logging_config import should_log, LOG_NORMAL

# Maximum number of log messages to retain (rolling buffer for UI)
MAX_LOG_MESSAGES = 250
BATCH_DELETE_SIZE = 50  # Delete in batches for performance

# File logging configuration
LOG_DIR = Path.home() / ".qbd_test_tool" / "logs"
LOG_FILE = LOG_DIR / "qbd_test_tool.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Keep 5 backup files (total ~50MB max)

# Initialize file logger
_file_logger = None


def _get_file_logger():
    """Get or create the file logger with RotatingFileHandler."""
    global _file_logger
    if _file_logger is None:
        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Create logger
        _file_logger = logging.getLogger('qbd_test_tool')
        _file_logger.setLevel(logging.DEBUG)

        # Create rotating file handler
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        _file_logger.addHandler(handler)

    return _file_logger


def _log_to_file(message: str, level: str = 'INFO'):
    """
    Log message to file.

    Args:
        message: Message to log
        level: Log level (INFO, DEBUG, WARNING, ERROR)
    """
    logger = _get_file_logger()
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, message)


def log_create(app, message: str, level: str = LOG_NORMAL):
    """
    Log message to create tab with log level filtering and rolling buffer.

    Args:
        app: Reference to the main QBDTestToolApp instance
        message: Message to log
        level: Log level (MINIMAL, NORMAL, VERBOSE, DEBUG)
    """
    # Check if message should be logged based on current level
    current_level = AppConfig.get_log_level()
    if not should_log(level, current_level):
        return

    # Always log to file (with appropriate level)
    file_level = 'DEBUG' if level == 'DEBUG' else 'INFO'
    _log_to_file(f"[CREATE] {message}", file_level)

    # Apply rolling buffer (keep only last MAX_LOG_MESSAGES)
    _apply_rolling_buffer(app.create_log)

    # Log the message
    timestamp = datetime.now().strftime('%H:%M:%S')
    app.create_log.insert(tk.END, f"[{timestamp}] {message}\n")
    app.create_log.see(tk.END)


def log_monitor(app, message: str, level: str = LOG_NORMAL):
    """
    Log message to monitor tab with log level filtering and rolling buffer.

    Args:
        app: Reference to the main QBDTestToolApp instance
        message: Message to log
        level: Log level (MINIMAL, NORMAL, VERBOSE, DEBUG)
    """
    # Check if message should be logged based on current level
    current_level = AppConfig.get_log_level()
    if not should_log(level, current_level):
        return

    # Always log to file (with appropriate level)
    file_level = 'DEBUG' if level == 'DEBUG' else 'INFO'
    _log_to_file(f"[MONITOR] {message}", file_level)

    # Apply rolling buffer (keep only last MAX_LOG_MESSAGES)
    _apply_rolling_buffer(app.monitor_log)

    # Log the message
    timestamp = datetime.now().strftime('%H:%M:%S')
    app.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n")
    app.monitor_log.see(tk.END)


def _apply_rolling_buffer(text_widget):
    """
    Apply rolling buffer to text widget - delete oldest messages if over limit.

    Args:
        text_widget: ScrolledText widget to apply rolling buffer to
    """
    # Get all text and count lines
    content = text_widget.get("1.0", "end-1c")
    line_count = len(content.split("\n"))

    # If over limit, delete oldest BATCH_DELETE_SIZE lines
    if line_count > MAX_LOG_MESSAGES:
        # Delete lines 1 through BATCH_DELETE_SIZE
        text_widget.delete("1.0", f"{BATCH_DELETE_SIZE + 1}.0")
