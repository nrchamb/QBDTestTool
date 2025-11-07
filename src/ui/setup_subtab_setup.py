"""
Setup subtab setup for QuickBooks Desktop Test Tool.

Handles the Setup subtab for loading customers, items, terms, classes, and accounts.
"""

from tkinter import ttk
from .ui_utils import create_scrollable_frame
from .ui_constants import (
    SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    FONT_BODY, FONT_BOLD, TEXT_WRAPLENGTH
)


def setup_setup_subtab(app):
    """
    Setup the Setup subtab for loading customers and items.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.setup_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=SPACING_XL)
    content.pack(fill='x')

    # Welcome section
    welcome_text = "Initialize the test tool by loading existing customers and items from QuickBooks."
    ttk.Label(content, text=welcome_text, wraplength=TEXT_WRAPLENGTH).pack(pady=(0, SPACING_LG))

    # Grid for compact layout: Label | Button | Status
    grid_frame = ttk.Frame(content)
    grid_frame.pack(fill='x')



    # Configure column weights - keep status column expandable for long messages
    grid_frame.columnconfigure(0, weight=0)  # Label column (fixed)
    grid_frame.columnconfigure(1, weight=0)  # Button column (fixed)
    grid_frame.columnconfigure(2, weight=1)  # Status column (expands for text)

    # Row 0: Customers
    ttk.Label(grid_frame, text="Customers:", font=FONT_BOLD).grid(row=0, column=0, sticky='w', pady=SPACING_SM)
    app.load_customers_btn = ttk.Button(grid_frame, text="Load Existing Customers from QB", command=app._load_customers)
    app.load_customers_btn.grid(row=0, column=1, padx=SPACING_SM, pady=SPACING_SM)
    app.customers_status_label = ttk.Label(grid_frame, text="No customers loaded", foreground='red')
    app.customers_status_label.grid(row=0, column=2, sticky='w', padx=(SPACING_MD, 0), pady=SPACING_SM)

    # Row 1: Items
    ttk.Label(grid_frame, text="Items:", font=FONT_BOLD).grid(row=1, column=0, sticky='w', pady=SPACING_SM)
    app.load_items_btn = ttk.Button(grid_frame, text="Load Items from QB", command=app._load_items)
    app.load_items_btn.grid(row=1, column=1, padx=SPACING_SM, pady=SPACING_SM)
    app.items_status_label = ttk.Label(grid_frame, text="No items loaded", foreground='red')
    app.items_status_label.grid(row=1, column=2, sticky='w', padx=(SPACING_MD, 0), pady=SPACING_SM)

    # Row 2: Terms (Optional)
    ttk.Label(grid_frame, text="Terms:", font=FONT_BODY).grid(row=2, column=0, sticky='w', pady=SPACING_SM)
    app.load_terms_btn = ttk.Button(grid_frame, text="Load Terms from QB", command=app._load_terms)
    app.load_terms_btn.grid(row=2, column=1, padx=SPACING_SM, pady=SPACING_SM)
    app.terms_status_label = ttk.Label(grid_frame, text="No terms loaded (optional)", foreground='gray')
    app.terms_status_label.grid(row=2, column=2, sticky='w', padx=(SPACING_MD, 0), pady=SPACING_SM)

    # Row 3: Classes (Optional)
    ttk.Label(grid_frame, text="Classes:", font=FONT_BODY).grid(row=3, column=0, sticky='w', pady=SPACING_SM)
    app.load_classes_btn = ttk.Button(grid_frame, text="Load Classes from QB", command=app._load_classes)
    app.load_classes_btn.grid(row=3, column=1, padx=SPACING_SM, pady=SPACING_SM)
    app.classes_status_label = ttk.Label(grid_frame, text="No classes loaded (optional)", foreground='gray')
    app.classes_status_label.grid(row=3, column=2, sticky='w', padx=(SPACING_MD, 0), pady=SPACING_SM)

    # Row 4: Accounts (Optional)
    ttk.Label(grid_frame, text="Accounts:", font=FONT_BODY).grid(row=4, column=0, sticky='w', pady=SPACING_SM)
    app.load_accounts_btn = ttk.Button(grid_frame, text="Load Accounts from QB", command=app._load_accounts)
    app.load_accounts_btn.grid(row=4, column=1, padx=SPACING_SM, pady=SPACING_SM)
    app.accounts_status_label = ttk.Label(grid_frame, text="No accounts loaded (optional)", foreground='gray')
    app.accounts_status_label.grid(row=4, column=2, sticky='w', padx=(SPACING_MD, 0), pady=SPACING_SM)

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=SPACING_LG)

    # Load All button
    load_all_frame = ttk.Frame(content)
    load_all_frame.pack(fill='x', pady=(SPACING_LG, 0))
    app.load_all_btn = ttk.Button(load_all_frame, text="Load All / Initialize All", command=app._load_all, style='Accent.TButton')
    app.load_all_btn.pack()

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=SPACING_LG)

    # Verify session transactions button
    verify_frame = ttk.Frame(content)
    verify_frame.pack(fill='x', pady=(SPACING_LG, 0))

    app.verify_session_btn = ttk.Button(
        verify_frame,
        text="Verify Session Transactions",
        command=app._verify_session_transactions
    )
    app.verify_session_btn.pack()

    # Help text for verification
    verify_help = ttk.Label(
        content,
        text="Check session transactions against QuickBooks to detect changes (payments, edits, deletions).",
        wraplength=TEXT_WRAPLENGTH,
        foreground='gray'
    )
    verify_help.pack(pady=(SPACING_SM, 0))

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=SPACING_LG)

    # Status summary
    status_frame = ttk.Frame(content)
    status_frame.pack(fill='x')

    ttk.Label(status_frame, text="Status:", font=FONT_BOLD).pack(side='left', padx=(0, SPACING_MD))
    app.setup_summary_label = ttk.Label(
        status_frame,
        text="Ready to load data from QuickBooks",
        font=FONT_BODY
    )
    app.setup_summary_label.pack(side='left')
