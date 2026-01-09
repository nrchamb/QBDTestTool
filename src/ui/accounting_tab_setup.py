"""
Accounting tab setup for QuickBooks Desktop Test Tool.

Simplified customer creation interface for accounting workflows.
No random field generation - all fields are manual entry only.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

from .ui_utils import create_scrollable_frame
from .ui_constants import (
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    FONT_BODY, FONT_BOLD, ENTRY_WIDTH_LONG, ENTRY_WIDTH_SHORT, ENTRY_WIDTH_MEDIUM,
    SCROLLEDTEXT_HEIGHT, SCROLLEDTEXT_WIDTH
)
from config import AppConfig
from actions.ui_utility_actions import toggle_create_log


def setup_accounting_tab(app):
    """
    Setup the Accounting tab for customer creation from pasted data.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Main container
    main_container = ttk.Frame(app.accounting_tab)
    main_container.pack(fill='both', expand=True)

    # Collapse button header - at bottom, always visible
    log_header_frame = ttk.Frame(main_container)
    log_header_frame.pack(side='bottom', fill='x', padx=SPACING_MD, pady=SPACING_SM)

    # PanedWindow for content and log
    app.create_paned = tk.PanedWindow(main_container, orient='vertical', sashrelief='raised', sashwidth=8, bg='#d9d9d9')
    app.create_paned.pack(fill='both', expand=True)

    # Calculate pane heights from saved ratio and known window height
    usable_height = app._window_height - 150
    top_height = int(usable_height * app._create_sash_ratio)
    bottom_height = int(usable_height * (1 - app._create_sash_ratio))

    # Top pane: Scrollable form content
    form_container = ttk.Frame(app.create_paned)
    app.create_paned.add(form_container, height=top_height)

    # Create scrollable frame for the form
    canvas, scrollbar, container = create_scrollable_frame(form_container)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=SPACING_XL)
    content.pack(fill='x')

    # =========================================================================
    # Paste Section
    # =========================================================================
    paste_frame = ttk.LabelFrame(content, text="Paste Customer Data", padding=SPACING_SM)
    paste_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Text widget for pasting
    app.acct_paste_text = tk.Text(paste_frame, height=4, width=60)
    app.acct_paste_text.pack(fill='x', pady=(0, SPACING_XS))

    # Add right-click context menu for paste box
    paste_context_menu = tk.Menu(app.acct_paste_text, tearoff=0)
    paste_context_menu.add_command(label="Cut", accelerator="Ctrl+X",
                                   command=lambda: app.acct_paste_text.event_generate("<<Cut>>"))
    paste_context_menu.add_command(label="Copy", accelerator="Ctrl+C",
                                   command=lambda: app.acct_paste_text.event_generate("<<Copy>>"))
    paste_context_menu.add_command(label="Paste", accelerator="Ctrl+V",
                                   command=lambda: app.acct_paste_text.event_generate("<<Paste>>"))
    paste_context_menu.add_separator()
    paste_context_menu.add_command(label="Select All", accelerator="Ctrl+A",
                                   command=lambda: (app.acct_paste_text.tag_add("sel", "1.0", "end"),
                                                   app.acct_paste_text.mark_set("insert", "end")))
    paste_context_menu.add_command(label="Clear",
                                   command=lambda: app.acct_paste_text.delete("1.0", "end"))

    def show_paste_context_menu(event):
        paste_context_menu.tk_popup(event.x_root, event.y_root)

    app.acct_paste_text.bind("<Button-3>", show_paste_context_menu)

    # Paste buttons and status
    paste_btn_frame = ttk.Frame(paste_frame)
    paste_btn_frame.pack(fill='x')

    app.acct_parse_btn = ttk.Button(
        paste_btn_frame,
        text="Parse & Preview",
        command=lambda: _parse_and_populate(app)
    )
    app.acct_parse_btn.pack(side='left', padx=(0, SPACING_SM))

    app.acct_clear_btn = ttk.Button(
        paste_btn_frame,
        text="Clear All",
        command=lambda: _clear_all_fields(app)
    )
    app.acct_clear_btn.pack(side='left')

    app.acct_paste_status = ttk.Label(paste_btn_frame, text="", foreground='gray')
    app.acct_paste_status.pack(side='left', padx=(SPACING_MD, 0))

    # =========================================================================
    # Customer Details Section
    # =========================================================================
    details_frame = ttk.LabelFrame(content, text="Customer Details", padding=SPACING_SM)
    details_frame.pack(fill='x', pady=(0, SPACING_MD))

    # Form grid
    form_frame = ttk.Frame(details_frame)
    form_frame.pack(fill='x', padx=SPACING_SM, pady=SPACING_SM)

    row = 0

    # Email (required)
    ttk.Label(form_frame, text="Email:", font=FONT_BOLD).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_email = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    app.acct_email.grid(row=row, column=1, columnspan=3, sticky='w', pady=SPACING_XS)
    ttk.Label(form_frame, text="(required)", foreground='gray').grid(
        row=row, column=4, sticky='w', padx=(SPACING_SM, 0)
    )
    row += 1

    # ISO and CID on same row
    ttk.Label(form_frame, text="ISO:", font=FONT_BODY).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_iso = ttk.Entry(form_frame, width=ENTRY_WIDTH_SHORT, state='readonly')
    app.acct_iso.grid(row=row, column=1, sticky='w', pady=SPACING_XS)

    ttk.Label(form_frame, text="CID:", font=FONT_BODY).grid(
        row=row, column=2, sticky='e', pady=SPACING_XS, padx=(SPACING_MD, SPACING_SM)
    )
    app.acct_cid = ttk.Entry(form_frame, width=ENTRY_WIDTH_SHORT)
    app.acct_cid.grid(row=row, column=3, sticky='w', pady=SPACING_XS)
    row += 1

    # Separator
    ttk.Separator(form_frame, orient='horizontal').grid(
        row=row, column=0, columnspan=5, sticky='ew', pady=SPACING_MD
    )
    row += 1

    # First Name
    ttk.Label(form_frame, text="First Name:", font=FONT_BODY).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_first_name = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    app.acct_first_name.grid(row=row, column=1, columnspan=3, sticky='w', pady=SPACING_XS)
    row += 1

    # Last Name
    ttk.Label(form_frame, text="Last Name:", font=FONT_BODY).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_last_name = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    app.acct_last_name.grid(row=row, column=1, columnspan=3, sticky='w', pady=SPACING_XS)
    row += 1

    # Company
    ttk.Label(form_frame, text="Company:", font=FONT_BODY).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_company = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    app.acct_company.grid(row=row, column=1, columnspan=3, sticky='w', pady=SPACING_XS)
    row += 1

    # Phone
    ttk.Label(form_frame, text="Phone:", font=FONT_BODY).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_phone = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    app.acct_phone.grid(row=row, column=1, columnspan=3, sticky='w', pady=SPACING_XS)
    row += 1

    # Separator
    ttk.Separator(form_frame, orient='horizontal').grid(
        row=row, column=0, columnspan=5, sticky='ew', pady=SPACING_MD
    )
    row += 1

    # Address
    ttk.Label(form_frame, text="Address:", font=FONT_BODY).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_address = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    app.acct_address.grid(row=row, column=1, columnspan=3, sticky='w', pady=SPACING_XS)
    row += 1

    # City and State on same row
    ttk.Label(form_frame, text="City:", font=FONT_BODY).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_city = ttk.Entry(form_frame, width=ENTRY_WIDTH_MEDIUM)
    app.acct_city.grid(row=row, column=1, sticky='w', pady=SPACING_XS)

    ttk.Label(form_frame, text="State:", font=FONT_BODY).grid(
        row=row, column=2, sticky='e', pady=SPACING_XS, padx=(SPACING_MD, SPACING_SM)
    )
    app.acct_state = ttk.Entry(form_frame, width=8)
    app.acct_state.grid(row=row, column=3, sticky='w', pady=SPACING_XS)
    row += 1

    # Zip
    ttk.Label(form_frame, text="Zip:", font=FONT_BODY).grid(
        row=row, column=0, sticky='e', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_zip = ttk.Entry(form_frame, width=ENTRY_WIDTH_SHORT)
    app.acct_zip.grid(row=row, column=1, sticky='w', pady=SPACING_XS)
    row += 1

    # Separator
    ttk.Separator(form_frame, orient='horizontal').grid(
        row=row, column=0, columnspan=5, sticky='ew', pady=SPACING_MD
    )
    row += 1

    # Notes
    ttk.Label(form_frame, text="Notes:", font=FONT_BODY).grid(
        row=row, column=0, sticky='ne', pady=SPACING_XS, padx=(0, SPACING_SM)
    )
    app.acct_notes = tk.Text(form_frame, height=3, width=45)
    app.acct_notes.grid(row=row, column=1, columnspan=3, sticky='w', pady=SPACING_XS)
    row += 1

    # =========================================================================
    # Action Buttons
    # =========================================================================
    button_frame = ttk.Frame(content)
    button_frame.pack(fill='x', pady=SPACING_MD)

    # Button row
    btn_row = ttk.Frame(button_frame)
    btn_row.pack()

    app.acct_create_btn = ttk.Button(
        btn_row,
        text="Create Customer in QuickBooks",
        command=lambda: _create_customer(app)
    )
    app.acct_create_btn.pack(side='left', padx=SPACING_SM)

    app.acct_clear_form_btn = ttk.Button(
        btn_row,
        text="Clear Form",
        command=lambda: _clear_form_fields(app)
    )
    app.acct_clear_form_btn.pack(side='left', padx=SPACING_SM)

    # Status label
    app.acct_status_label = ttk.Label(button_frame, text="", foreground='gray')
    app.acct_status_label.pack(pady=(SPACING_SM, 0))

    # =========================================================================
    # Bottom pane: Activity log
    # =========================================================================
    app.create_log_pane = ttk.Frame(app.create_paned)
    app.create_paned.add(app.create_log_pane, height=bottom_height)

    # Log content
    log_content_frame = ttk.Frame(app.create_log_pane, relief='sunken', borderwidth=1)
    log_content_frame.pack(fill='both', expand=True, padx=SPACING_MD, pady=SPACING_MD)

    app.create_log = scrolledtext.ScrolledText(
        log_content_frame,
        height=SCROLLEDTEXT_HEIGHT,
        width=SCROLLEDTEXT_WIDTH
    )
    app.create_log.pack(fill='both', expand=True, padx=2, pady=2)

    # Setup collapse button (in header frame created earlier)
    ttk.Label(log_header_frame, text="Activity Log", font=('TkDefaultFont', 9, 'bold')).pack(side='left')

    # Load saved UI state
    ui_state = AppConfig.get_ui_state()
    activity_log_collapsed = ui_state.get('activity_log_collapsed', False)

    app.create_log_collapsed = tk.BooleanVar(value=activity_log_collapsed)

    # Set initial button text based on state
    initial_btn_text = "Show Log" if activity_log_collapsed else "Hide Log"

    app.create_log_toggle_btn = ttk.Button(
        log_header_frame,
        text=initial_btn_text,
        command=lambda: toggle_create_log(app),
        width=12
    )
    app.create_log_toggle_btn.pack(side='right', padx=SPACING_SM)

    # Apply collapsed state if needed
    if activity_log_collapsed:
        app.create_paned.remove(app.create_log_pane)


def _parse_and_populate(app):
    """Parse pasted text and populate form fields."""
    from actions.accounting_actions import parse_and_populate_accounting
    parse_and_populate_accounting(app)


def _clear_all_fields(app):
    """Clear all form fields including paste area."""
    from actions.accounting_actions import clear_accounting_fields
    clear_accounting_fields(app)


def _clear_form_fields(app):
    """Clear only the customer form fields (not paste area)."""
    # Clear all entry fields
    app.acct_email.delete(0, 'end')

    app.acct_iso.config(state='normal')
    app.acct_iso.delete(0, 'end')
    app.acct_iso.config(state='readonly')

    app.acct_cid.delete(0, 'end')
    app.acct_first_name.delete(0, 'end')
    app.acct_last_name.delete(0, 'end')
    app.acct_company.delete(0, 'end')
    app.acct_phone.delete(0, 'end')
    app.acct_address.delete(0, 'end')
    app.acct_city.delete(0, 'end')
    app.acct_state.delete(0, 'end')
    app.acct_zip.delete(0, 'end')

    # Clear notes
    app.acct_notes.delete('1.0', 'end')

    # Clear status
    app.acct_status_label.config(text="")
    app.acct_paste_status.config(text="Form cleared", foreground='gray')


def _create_customer(app):
    """Create customer in QuickBooks."""
    from actions.accounting_actions import create_accounting_customer
    create_accounting_customer(app)
