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

    # Application Mode Section (at top)
    mode_frame = ttk.LabelFrame(content, text="Application Mode", padding=SPACING_MD)
    mode_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Mode radio buttons
    app.mode_var = tk.StringVar(value=app.current_mode)

    def on_mode_change():
        new_mode = app.mode_var.get()
        if new_mode != app.current_mode:
            app.switch_mode(new_mode)

    mode_radio_frame = ttk.Frame(mode_frame)
    mode_radio_frame.pack(fill='x')

    testing_radio = ttk.Radiobutton(
        mode_radio_frame,
        text="Testing Mode",
        variable=app.mode_var,
        value='testing',
        command=on_mode_change
    )
    testing_radio.pack(side='left', padx=(0, SPACING_LG))

    accounting_radio = ttk.Radiobutton(
        mode_radio_frame,
        text="Accounting Mode",
        variable=app.mode_var,
        value='accounting',
        command=on_mode_change
    )
    accounting_radio.pack(side='left')

    # Mode descriptions
    mode_help_text = ttk.Label(
        mode_frame,
        text="• Testing: Generate random test data for QuickBooks\n"
             "• Accounting: Paste customer data and create in QuickBooks",
        font=FONT_CAPTION,
        foreground='gray',
        justify='left'
    )
    mode_help_text.pack(anchor='w', pady=(SPACING_MD, 0))

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=SPACING_LG)

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

    # File Locations Section
    locations_frame = ttk.LabelFrame(content, text="Application Data", padding=SPACING_MD)
    locations_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Help text
    locations_help_text = ttk.Label(
        locations_frame,
        text="Open the folder containing configuration and session data files.",
        font=FONT_CAPTION,
        foreground='gray',
        wraplength=TEXT_WRAPLENGTH,
        justify='left'
    )
    locations_help_text.pack(anchor='w', pady=(0, SPACING_MD))

    # Location buttons
    location_button_frame = ttk.Frame(locations_frame)
    location_button_frame.pack(fill='x', pady=(0, 0))

    ttk.Button(
        location_button_frame,
        text="Open Data Folder",
        command=app._open_data_folder
    ).pack(side='left', padx=SPACING_SM)

    # Show current path
    from pathlib import Path
    data_path = Path.home() / ".qbd_test_tool"
    path_label = ttk.Label(
        locations_frame,
        text=f"Location: {data_path}",
        font=FONT_CAPTION,
        foreground='gray'
    )
    path_label.pack(anchor='w', pady=(SPACING_MD, 0))

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

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=SPACING_LG)

    # Performance Options Section
    perf_frame = ttk.LabelFrame(content, text="Performance Options", padding=SPACING_MD)
    perf_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Monitoring enabled checkbox
    initial_monitoring_state = AppConfig.get_monitoring_enabled()
    app.monitoring_enabled_var = tk.BooleanVar(value=initial_monitoring_state)

    def on_monitoring_toggle():
        enabled = app.monitoring_enabled_var.get()
        AppConfig.save_monitoring_enabled(enabled)
        # Show restart notice if changed from initial state
        if enabled != initial_monitoring_state:
            app.monitoring_restart_label.config(text="Restart required to apply changes")
        else:
            app.monitoring_restart_label.config(text="")

    monitoring_check = ttk.Checkbutton(
        perf_frame,
        text="Enable monitoring tab",
        variable=app.monitoring_enabled_var,
        command=on_monitoring_toggle
    )
    monitoring_check.pack(anchor='w', pady=SPACING_SM)

    # Help text
    monitoring_help_text = ttk.Label(
        perf_frame,
        text="Disable monitoring on low-resource VMs to reduce overhead.\nRequires app restart to take effect.",
        font=FONT_CAPTION,
        foreground='gray',
        justify='left'
    )
    monitoring_help_text.pack(anchor='w', pady=(0, SPACING_SM))

    # Restart notice label
    app.monitoring_restart_label = ttk.Label(
        perf_frame,
        text="",
        foreground='orange'
    )
    app.monitoring_restart_label.pack(anchor='w')

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=SPACING_LG)

    # Developer Options Section
    dev_frame = ttk.LabelFrame(content, text="Developer Options", padding=SPACING_MD)
    dev_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Debug tools checkbox
    initial_debug_state = AppConfig.get_debug_tools_enabled()
    app.debug_tools_var = tk.BooleanVar(value=initial_debug_state)

    def on_debug_tools_toggle():
        enabled = app.debug_tools_var.get()
        AppConfig.save_debug_tools_enabled(enabled)
        # Show restart notice if changed from initial state
        if enabled != initial_debug_state:
            app.debug_restart_label.config(text="Restart required to apply changes")
        else:
            app.debug_restart_label.config(text="")

    debug_check = ttk.Checkbutton(
        dev_frame,
        text="Enable debug tools",
        variable=app.debug_tools_var,
        command=on_debug_tools_toggle
    )
    debug_check.pack(anchor='w', pady=SPACING_SM)

    # Help text
    debug_help_text = ttk.Label(
        dev_frame,
        text="Shows additional testing tools on the Monitor tab (e.g., apply test payments).\nRequires app restart to take effect.",
        font=FONT_CAPTION,
        foreground='gray',
        justify='left'
    )
    debug_help_text.pack(anchor='w', pady=(0, SPACING_SM))

    # Restart notice label
    app.debug_restart_label = ttk.Label(
        dev_frame,
        text="",
        foreground='orange'
    )
    app.debug_restart_label.pack(anchor='w')
