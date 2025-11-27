"""
Monitor tab setup for QuickBooks Desktop Test Tool.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from actions.monitor_actions import (
    start_monitoring, stop_monitoring, handle_set_deposit_account, clear_search
)
# Temporarily disabled - search functionality needs refactoring
# from actions.monitor_search_actions import search_transactions
from actions.ui_utility_actions import toggle_monitor_log
from actions.payment_actions import apply_test_payments
from config import AppConfig
from .ui_constants import (
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    FONT_BODY, ENTRY_WIDTH_SHORT, ENTRY_WIDTH_MEDIUM, COMBOBOX_WIDTH_MEDIUM,
    SPINBOX_WIDTH_MEDIUM, TREEVIEW_HEIGHT_SHORT, COLUMN_WIDTH_LG,
    SCROLLEDTEXT_HEIGHT, SCROLLEDTEXT_WIDTH
)

# Color constants for status tags
COLOR_OPEN = '#fff3cd'      # Light yellow - needs attention
COLOR_PARTIAL = '#cce5ff'   # Light blue - partially paid
COLOR_CLOSED = '#d4edda'    # Light green - completed


def setup_monitor_tab(app):
    """
    Setup the Monitor Invoices tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create PanedWindow to split content and log with resize handle
    # Main container
    main_container = ttk.Frame(app.monitor_tab)
    main_container.pack(fill='both', expand=True)

    # Collapse button header - at bottom, always visible
    log_header_frame = ttk.Frame(main_container)
    log_header_frame.pack(side='bottom', fill='x', padx=SPACING_MD, pady=SPACING_SM)

    # PanedWindow for content and log - using tk.PanedWindow for sashrelief support
    app.monitor_paned = tk.PanedWindow(main_container, orient='vertical', sashrelief='raised', sashwidth=8, bg='#d9d9d9')
    app.monitor_paned.pack(fill='both', expand=True)

    # Calculate pane heights from saved ratio and known window height
    usable_height = app._window_height - 150  # account for title bar, tabs, status bar, etc.
    top_height = int(usable_height * app._monitor_sash_ratio)
    bottom_height = int(usable_height * (1 - app._monitor_sash_ratio))

    # Top pane: All content (controls, search, transaction list)
    content_frame = ttk.Frame(app.monitor_paned)
    app.monitor_paned.add(content_frame, height=top_height)

    control_frame = ttk.Frame(content_frame, padding=SPACING_MD)
    control_frame.pack(fill='x')

    app.start_monitor_btn = ttk.Button(control_frame, text="Start Monitoring", command=lambda: start_monitoring(app))
    app.start_monitor_btn.pack(side='left', padx=SPACING_SM)

    app.stop_monitor_btn = ttk.Button(control_frame, text="Stop Monitoring", command=lambda: stop_monitoring(app), state='disabled')
    app.stop_monitor_btn.pack(side='left', padx=SPACING_SM)

    ttk.Label(control_frame, text="Check interval (seconds):").pack(side='left', padx=SPACING_SM)
    app.check_interval = ttk.Spinbox(control_frame, from_=5, to=300, width=SPINBOX_WIDTH_MEDIUM)
    app.check_interval.set(30)
    app.check_interval.pack(side='left', padx=SPACING_SM)

    ttk.Label(control_frame, text="Expected Deposit Account:").pack(side='left', padx=(SPACING_LG, SPACING_SM))
    app.expected_deposit_account_combo = ttk.Combobox(control_frame, width=COMBOBOX_WIDTH_MEDIUM, state='readonly')
    app.expected_deposit_account_combo.pack(side='left', padx=SPACING_SM)

    ttk.Button(control_frame, text="Set", command=lambda: handle_set_deposit_account(app)).pack(side='left', padx=SPACING_SM)

    # Debug tools (hidden by default, enable via config)
    if AppConfig.get_debug_tools_enabled():
        dev_frame = ttk.Frame(content_frame, padding=(SPACING_MD, 0, SPACING_MD, SPACING_SM))
        dev_frame.pack(fill='x')

        def get_selected_refs():
            """Get ref numbers of selected rows, or None for all."""
            selection = app.invoice_tree.selection()
            if not selection:
                return None  # No selection = pay all
            # Column index 1 is 'Ref#'
            return [app.invoice_tree.item(item)['values'][1] for item in selection]

        ttk.Label(dev_frame, text="[Debug Tools]", font=('TkDefaultFont', 9, 'italic')).pack(side='left', padx=SPACING_SM)
        ttk.Button(dev_frame, text="Pay Full (100%)",
                   command=lambda: apply_test_payments(app, 1.0, get_selected_refs())).pack(side='left', padx=SPACING_XS)
        ttk.Button(dev_frame, text="Pay 50%",
                   command=lambda: apply_test_payments(app, 0.5, get_selected_refs())).pack(side='left', padx=SPACING_XS)

    # Memo Change Detection Settings
    memo_validation_frame = ttk.LabelFrame(content_frame, text="Memo Change Detection", padding=SPACING_MD)
    memo_validation_frame.pack(fill='x', padx=SPACING_MD, pady=SPACING_SM)

    ttk.Label(
        memo_validation_frame,
        text="Check for memo updates from initial state (binary change detection):",
        font=FONT_BODY
    ).pack(anchor='w', pady=(0, SPACING_SM))

    validation_options = ttk.Frame(memo_validation_frame)
    validation_options.pack(fill='x')

    app.check_transaction_memo_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        validation_options,
        text="Check Transaction Memo Changed",
        variable=app.check_transaction_memo_var
    ).pack(side='left', padx=SPACING_SM)

    app.check_payment_memo_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        validation_options,
        text="Check Payment Record Memo Changed",
        variable=app.check_payment_memo_var
    ).pack(side='left', padx=SPACING_SM)

    # ==================== SEARCH SECTION - TEMPORARILY DISABLED ====================
    # TODO: Refactor search functionality to be more useful
    # Current implementation is too complex and needs better UX design
    #
    # # Search section
    # search_frame = ttk.LabelFrame(content_frame, text="Search Transactions", padding=SPACING_MD)
    # search_frame.pack(fill='x', padx=SPACING_MD, pady=SPACING_SM)
    #
    # # Row 1: Text search and Transaction Type
    # row1 = ttk.Frame(search_frame)
    # row1.pack(fill='x', pady=SPACING_XS)
    #
    # ttk.Label(row1, text="Customer/Ref#:").pack(side='left', padx=SPACING_SM)
    # app.search_text = ttk.Entry(row1, width=ENTRY_WIDTH_MEDIUM)
    # app.search_text.pack(side='left', padx=SPACING_SM)
    #
    # ttk.Label(row1, text="Transaction ID:").pack(side='left', padx=(SPACING_LG, SPACING_SM))
    # app.search_txn_id = ttk.Entry(row1, width=ENTRY_WIDTH_MEDIUM)
    # app.search_txn_id.pack(side='left', padx=SPACING_SM)
    #
    # ttk.Label(row1, text="Type:").pack(side='left', padx=(SPACING_LG, SPACING_SM))
    # app.search_txn_type = ttk.Combobox(row1, width=18, state='readonly',
    #                                     values=['All', 'Invoices', 'Sales Receipts', 'Statement Charges'])
    # app.search_txn_type.set('All')
    # app.search_txn_type.pack(side='left', padx=SPACING_SM)
    #
    # # Row 2: Date range
    # row2 = ttk.Frame(search_frame)
    # row2.pack(fill='x', pady=SPACING_XS)
    #
    # ttk.Label(row2, text="Date From:").pack(side='left', padx=SPACING_SM)
    # app.search_date_from = ttk.Entry(row2, width=ENTRY_WIDTH_SHORT)
    # app.search_date_from.pack(side='left', padx=SPACING_SM)
    # ttk.Label(row2, text="(YYYY-MM-DD)").pack(side='left')
    #
    # ttk.Label(row2, text="To:").pack(side='left', padx=(SPACING_LG, SPACING_SM))
    # app.search_date_to = ttk.Entry(row2, width=ENTRY_WIDTH_SHORT)
    # app.search_date_to.pack(side='left', padx=SPACING_SM)
    # ttk.Label(row2, text="(YYYY-MM-DD)").pack(side='left')
    #
    # # Row 3: Amount range and buttons
    # row3 = ttk.Frame(search_frame)
    # row3.pack(fill='x', pady=SPACING_XS)
    #
    # ttk.Label(row3, text="Amount Min:").pack(side='left', padx=SPACING_SM)
    # app.search_amount_min = ttk.Entry(row3, width=ENTRY_WIDTH_SHORT)
    # app.search_amount_min.pack(side='left', padx=SPACING_SM)
    #
    # ttk.Label(row3, text="Max:").pack(side='left', padx=(SPACING_LG, SPACING_SM))
    # app.search_amount_max = ttk.Entry(row3, width=ENTRY_WIDTH_SHORT)
    # app.search_amount_max.pack(side='left', padx=SPACING_SM)
    #
    # # Search and Clear buttons
    # ttk.Button(row3, text="Search", command=lambda: search_transactions(app), style='Accent.TButton').pack(side='left', padx=(SPACING_XL, SPACING_SM))
    # ttk.Button(row3, text="Clear", command=lambda: clear_search(app)).pack(side='left', padx=SPACING_SM)
    #
    # # Search scope toggle
    # app.search_scope_var = tk.BooleanVar(value=False)  # False = monitored only, True = all QB
    # app.search_scope_check = ttk.Checkbutton(row3, text="Search all QB transactions",
    #                                            variable=app.search_scope_var)
    # app.search_scope_check.pack(side='left', padx=(SPACING_XL, SPACING_SM))
    #
    # # Toggle for display mode
    # ttk.Label(row3, text="Results:").pack(side='left', padx=(SPACING_LG, SPACING_SM))
    # app.search_display_mode = ttk.Combobox(row3, width=ENTRY_WIDTH_SHORT, state='readonly', values=['Table', 'Popup'])
    # app.search_display_mode.set('Table')
    # app.search_display_mode.pack(side='left', padx=SPACING_SM)
    # ===============================================================================

    # Transaction list
    list_frame = ttk.LabelFrame(content_frame, text="Tracked Transactions", padding=SPACING_MD)
    list_frame.pack(fill='both', expand=True, padx=SPACING_MD, pady=SPACING_SM)

    # Treeview for transactions
    columns = ('Type', 'Ref#', 'Customer', 'Amount', 'Status', 'Last Checked')
    app.invoice_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=TREEVIEW_HEIGHT_SHORT)

    for col in columns:
        app.invoice_tree.heading(col, text=col)
        app.invoice_tree.column(col, width=COLUMN_WIDTH_LG)

    # Configure color tags for status
    app.invoice_tree.tag_configure('open', background=COLOR_OPEN)
    app.invoice_tree.tag_configure('partial', background=COLOR_PARTIAL)
    app.invoice_tree.tag_configure('closed', background=COLOR_CLOSED)

    app.invoice_tree.pack(fill='both', expand=True)

    # Bottom pane: Monitor log
    app.monitor_log_pane = ttk.Frame(app.monitor_paned)
    app.monitor_paned.add(app.monitor_log_pane, height=bottom_height)

    # Log content
    log_content_frame = ttk.Frame(app.monitor_log_pane, relief='sunken', borderwidth=1)
    log_content_frame.pack(fill='both', expand=True, padx=SPACING_MD, pady=SPACING_MD)

    app.monitor_log = scrolledtext.ScrolledText(
        log_content_frame,
        height=SCROLLEDTEXT_HEIGHT,
        width=SCROLLEDTEXT_WIDTH
    )
    app.monitor_log.pack(fill='both', expand=True, padx=2, pady=2)

    # Setup collapse button (in header frame created earlier)
    ttk.Label(log_header_frame, text="Monitor Log", font=('TkDefaultFont', 9, 'bold')).pack(side='left')

    # Load saved UI state
    ui_state = AppConfig.get_ui_state()
    activity_log_collapsed = ui_state.get('activity_log_collapsed', False)

    app.monitor_log_collapsed = tk.BooleanVar(value=activity_log_collapsed)

    # Set initial button text based on state
    initial_btn_text = "▶ Show Log" if activity_log_collapsed else "▼ Hide Log"

    app.monitor_log_toggle_btn = ttk.Button(
        log_header_frame,
        text=initial_btn_text,
        command=lambda: toggle_monitor_log(app),
        width=12
    )
    app.monitor_log_toggle_btn.pack(side='right', padx=SPACING_SM)

    # Apply collapsed state if needed (sash position applied in app.py)
    if activity_log_collapsed:
        app.monitor_paned.remove(app.monitor_log_pane)
