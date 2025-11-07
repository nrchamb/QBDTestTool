"""
Settings tab setup for QuickBooks Desktop Test Tool.

Handles log verbosity, session persistence, and transaction cleanup.
"""

import tkinter as tk
from tkinter import ttk
from config import AppConfig
from app_logging import LOG_LEVELS
from actions.ui_utility_actions import save_log_level_setting, save_persistence_settings
from .ui_utils import create_scrollable_frame
from .ui_constants import (
    SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    FONT_BODY, FONT_BOLD, FONT_CAPTION, FONT_CAPTION_BOLD,
    COMBOBOX_WIDTH_SHORT, TEXT_WRAPLENGTH
)


def setup_settings_tab(app):
    """
    Setup the Settings tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.settings_tab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=SPACING_XL)
    content.pack(fill='x')

    # Settings section
    settings_frame = ttk.LabelFrame(content, text="Log Verbosity", padding=SPACING_MD)
    settings_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Log verbosity control
    log_control_frame = ttk.Frame(settings_frame)
    log_control_frame.pack(fill='x')

    ttk.Label(log_control_frame, text="Log Verbosity:").pack(side='left', padx=(0, SPACING_MD))

    app.log_level_combo = ttk.Combobox(log_control_frame, width=COMBOBOX_WIDTH_SHORT, state='readonly', values=LOG_LEVELS)
    app.log_level_combo.set(AppConfig.get_log_level())
    app.log_level_combo.pack(side='left', padx=SPACING_SM)

    app.log_level_combo.bind('<<ComboboxSelected>>', lambda event: save_log_level_setting(app))

    # Help text for log levels
    help_text = ttk.Label(
        settings_frame,
        text="• MINIMAL: Only summaries and errors\n"
             "• NORMAL: Operations, results, errors (default)\n"
             "• VERBOSE: Add progress per item\n"
             "• DEBUG: Add full QBXML request/response",
        font=FONT_CAPTION,
        foreground='gray',
        justify='left'
    )
    help_text.pack(anchor='w', pady=(SPACING_MD, 0))

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=SPACING_LG)

    # Persistence Settings Section
    persistence_frame = ttk.LabelFrame(content, text="Session Persistence", padding=SPACING_MD)
    persistence_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Get current persistence settings
    persistence_settings = AppConfig.get_persistence_settings()

    # Auto-load checkbox
    app.auto_load_var = tk.BooleanVar(value=persistence_settings.get('auto_load', False))
    auto_load_check = ttk.Checkbutton(
        persistence_frame,
        text="Auto-load previous session on startup",
        variable=app.auto_load_var,
        command=lambda: save_persistence_settings(app)
    )
    auto_load_check.pack(anchor='w', pady=SPACING_SM)

    # Session file management
    ttk.Separator(persistence_frame, orient='horizontal').pack(fill='x', pady=SPACING_MD)

    button_frame = ttk.Frame(persistence_frame)
    button_frame.pack(fill='x', pady=(0, SPACING_SM))

    app.save_session_btn = ttk.Button(
        button_frame,
        text="Save Session Now",
        command=app._save_session_now
    )
    app.save_session_btn.pack(side='left', padx=SPACING_SM)

    app.load_session_btn = ttk.Button(
        button_frame,
        text="Load Previous Session",
        command=app._load_session_now
    )
    app.load_session_btn.pack(side='left', padx=SPACING_SM)

    app.clear_session_btn = ttk.Button(
        button_frame,
        text="Clear Session",
        command=app._clear_session
    )
    app.clear_session_btn.pack(side='left', padx=SPACING_SM)

    # Session status label
    app.session_status_label = ttk.Label(
        persistence_frame,
        text="No session loaded",
        foreground='gray'
    )
    app.session_status_label.pack(anchor='w', pady=(SPACING_SM, 0))

    # Help text
    session_help_text = ttk.Label(
        persistence_frame,
        text="Sessions store created transactions for tracking. Enable auto-load to restore your work when restarting the app.",
        font=FONT_CAPTION,
        foreground='gray',
        wraplength=TEXT_WRAPLENGTH,
        justify='left'
    )
    session_help_text.pack(anchor='w', pady=(SPACING_MD, 0))

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=SPACING_LG)

    # Transaction Cleanup Section
    archival_frame = ttk.LabelFrame(content, text="Transaction Cleanup", padding=SPACING_MD)
    archival_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Help text
    archival_help_text = ttk.Label(
        archival_frame,
        text="Archive closed/paid transactions to clean up your session, or permanently delete them from QuickBooks.",
        font=FONT_CAPTION,
        foreground='gray',
        wraplength=TEXT_WRAPLENGTH,
        justify='left'
    )
    archival_help_text.pack(anchor='w', pady=(0, SPACING_MD))

    # Archival buttons
    archival_button_frame = ttk.Frame(archival_frame)
    archival_button_frame.pack(fill='x', pady=(0, 0))

    app.archive_closed_btn = ttk.Button(
        archival_button_frame,
        text="Archive Closed Transactions",
        command=app._archive_closed_transactions
    )
    app.archive_closed_btn.pack(side='left', padx=SPACING_SM)

    app.archive_all_btn = ttk.Button(
        archival_button_frame,
        text="Archive All Transactions",
        command=app._archive_all_transactions
    )
    app.archive_all_btn.pack(side='left', padx=SPACING_SM)

    app.delete_archived_qb_btn = ttk.Button(
        archival_button_frame,
        text="Delete Archived from QuickBooks",
        command=app._delete_archived_from_qb
    )
    app.delete_archived_qb_btn.pack(side='left', padx=SPACING_SM)

    app.remove_archived_session_btn = ttk.Button(
        archival_button_frame,
        text="Remove Archived from Session",
        command=app._remove_archived_from_session
    )
    app.remove_archived_session_btn.pack(side='left', padx=SPACING_SM)

    # Archival status label
    app.archival_status_label = ttk.Label(
        archival_frame,
        text="",
        foreground='gray'
    )
    app.archival_status_label.pack(anchor='w', pady=(SPACING_MD, 0))

    # Warning label
    warning_label = ttk.Label(
        archival_frame,
        text="⚠ Warning: Deleting from QuickBooks is permanent and cannot be undone!",
        font=FONT_CAPTION_BOLD,
        foreground='red'
    )
    warning_label.pack(anchor='w', pady=(SPACING_SM, 0))
