"""
Unified Transaction subtab for QuickBooks Desktop Test Tool.

Consolidates Invoice, Sales Receipt, and Statement Charge creation into a single interface.
"""

import tkinter as tk
from tkinter import ttk
from actions.transaction_actions import create_transaction
from actions.ui_utility_actions import update_transaction_form_visibility
from .ui_utils import create_scrollable_frame
from .ui_constants import (
    SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    FONT_HEADING, ENTRY_WIDTH_SHORT, ENTRY_WIDTH_LONG,
    COMBOBOX_WIDTH_SHORT, COMBOBOX_WIDTH_MEDIUM, SPINBOX_WIDTH_SHORT, SPINBOX_WIDTH_MEDIUM
)


def setup_transaction_subtab(app):
    """
    Setup the unified Transaction subtab for batch creation of invoices, sales receipts, and charges.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.transaction_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=SPACING_XL)
    content.pack(fill='x')

    # Instructions
    ttk.Label(
        content,
        text="Create batch transactions with randomized parameters",
        font=FONT_HEADING
    ).pack(pady=(0, SPACING_LG))

    # Transaction Type Selector
    type_frame = ttk.LabelFrame(content, text="Transaction Type", padding=SPACING_MD)
    type_frame.pack(fill='x', pady=(0, SPACING_LG))

    app.transaction_type = tk.StringVar(value="Invoice")

    # Create three radio buttons for transaction type
    ttk.Radiobutton(
        type_frame,
        text="Invoice",
        variable=app.transaction_type,
        value="Invoice",
        command=lambda: update_transaction_form_visibility(app)
    ).pack(side='left', padx=SPACING_MD)

    ttk.Radiobutton(
        type_frame,
        text="Sales Receipt",
        variable=app.transaction_type,
        value="SalesReceipt",
        command=lambda: update_transaction_form_visibility(app)
    ).pack(side='left', padx=SPACING_MD)

    ttk.Radiobutton(
        type_frame,
        text="Statement Charge",
        variable=app.transaction_type,
        value="Charge",
        command=lambda: update_transaction_form_visibility(app)
    ).pack(side='left', padx=SPACING_MD)

    # Form
    form_frame = ttk.Frame(content)
    form_frame.pack(fill='x')

    row = 0

    # Customer selector
    ttk.Label(form_frame, text="Select Customer:").grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_customer_combo = ttk.Combobox(form_frame, width=ENTRY_WIDTH_LONG, state='readonly')
    app.txn_customer_combo.grid(row=row, column=1, pady=SPACING_SM, padx=SPACING_SM, sticky='w')
    app.customer_combos.append(app.txn_customer_combo)
    row += 1

    # Number of transactions
    ttk.Label(form_frame, text="Number of Transactions:").grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_count = ttk.Spinbox(form_frame, from_=1, to=100, width=SPINBOX_WIDTH_MEDIUM)
    app.txn_count.set(1)
    app.txn_count.grid(row=row, column=1, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    row += 1

    # Line items range (conditional - hidden for Statement Charge)
    app.txn_line_items_label = ttk.Label(form_frame, text="Line Items Range:")
    app.txn_line_items_label.grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_line_items_frame = ttk.Frame(form_frame)
    app.txn_line_items_frame.grid(row=row, column=1, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_lines_min = ttk.Spinbox(app.txn_line_items_frame, from_=1, to=20, width=SPINBOX_WIDTH_SHORT)
    app.txn_lines_min.set(1)
    app.txn_lines_min.pack(side='left')
    ttk.Label(app.txn_line_items_frame, text=" to ").pack(side='left', padx=SPACING_SM)
    app.txn_lines_max = ttk.Spinbox(app.txn_line_items_frame, from_=1, to=20, width=SPINBOX_WIDTH_SHORT)
    app.txn_lines_max.set(5)
    app.txn_lines_max.pack(side='left')
    row += 1

    # Amount range
    ttk.Label(form_frame, text="Amount Range ($):").grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    amount_frame = ttk.Frame(form_frame)
    amount_frame.grid(row=row, column=1, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_amount_min = ttk.Entry(amount_frame, width=ENTRY_WIDTH_SHORT)
    app.txn_amount_min.insert(0, "100")
    app.txn_amount_min.pack(side='left')
    ttk.Label(amount_frame, text=" to ").pack(side='left', padx=SPACING_SM)
    app.txn_amount_max = ttk.Entry(amount_frame, width=ENTRY_WIDTH_SHORT)
    app.txn_amount_max.insert(0, "5000")
    app.txn_amount_max.pack(side='left')
    row += 1

    # Date range
    ttk.Label(form_frame, text="Transaction Date Range:").grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_date_range = ttk.Combobox(form_frame, width=COMBOBOX_WIDTH_SHORT, state='readonly')
    app.txn_date_range['values'] = ('Today Only', 'Last 7 Days', 'Last 30 Days')
    app.txn_date_range.current(0)
    app.txn_date_range.grid(row=row, column=1, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    row += 1

    # PO Number Prefix (Invoice only - hidden for Sales Receipt and Statement Charge)
    app.txn_po_label = ttk.Label(form_frame, text="PO Number Prefix:")
    app.txn_po_label.grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_po_prefix = ttk.Entry(form_frame, width=ENTRY_WIDTH_SHORT)
    app.txn_po_prefix.insert(0, "PO-")
    app.txn_po_prefix.grid(row=row, column=1, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    row += 1

    # Terms (Invoice only - hidden for Sales Receipt and Statement Charge)
    app.txn_terms_label = ttk.Label(form_frame, text="Terms (optional):")
    app.txn_terms_label.grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_terms_combo = ttk.Combobox(form_frame, width=COMBOBOX_WIDTH_MEDIUM, state='readonly')
    app.txn_terms_combo['values'] = ['(None)']
    app.txn_terms_combo.current(0)
    app.txn_terms_combo.grid(row=row, column=1, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    row += 1

    # Class (Invoice only - hidden for Sales Receipt and Statement Charge)
    app.txn_class_label = ttk.Label(form_frame, text="Class (optional):")
    app.txn_class_label.grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    app.txn_class_combo = ttk.Combobox(form_frame, width=COMBOBOX_WIDTH_MEDIUM, state='readonly')
    app.txn_class_combo['values'] = ['(None)']
    app.txn_class_combo.current(0)
    app.txn_class_combo.grid(row=row, column=1, sticky='w', pady=SPACING_SM, padx=SPACING_SM)
    row += 1

    # Create button
    app.create_transaction_btn = ttk.Button(
        content,
        text="Create Invoices (Batch)",
        command=lambda: create_transaction(app)
    )
    app.create_transaction_btn.pack(pady=SPACING_LG)

    # Initialize field visibility based on default transaction type
    update_transaction_form_visibility(app)
