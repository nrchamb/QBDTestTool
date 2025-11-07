"""
Customer subtab setup for QuickBooks Desktop Test Tool.

"""

import tkinter as tk
from tkinter import ttk
from actions.customer_actions import create_customer
from actions.ui_utility_actions import (
    select_all_customer_fields, clear_all_customer_fields,
    update_customer_calculation, toggle_billing_address_fields,
    toggle_shipping_address_fields
)
from .ui_utils import create_scrollable_frame
from .ui_constants import (
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    FONT_BODY, FONT_BOLD, ENTRY_WIDTH_LONG, SPINBOX_WIDTH_MEDIUM, TEXT_WRAPLENGTH
)


def setup_customer_subtab(app):
    """
    Setup the Customer subtab for creating new customers.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.customer_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=SPACING_XL)
    content.pack(fill='x')

    # Instructions
    ttk.Label(
        content,
        text="Create a new customer. Check 'Random' to generate data, uncheck to enter manually (leave blank if not needed).",
        wraplength=TEXT_WRAPLENGTH
    ).pack(pady=(0, SPACING_LG))

    # Form frame with grid layout
    form_frame = ttk.Frame(content)
    form_frame.pack(fill='x', pady=(0, SPACING_LG))

    row = 0

    # Email (required, always enabled)
    ttk.Label(form_frame, text="Email:", font=FONT_BOLD).grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=(0, SPACING_MD))
    ttk.Label(form_frame, text="(required)").grid(row=row, column=1, sticky='w', pady=SPACING_SM)
    app.customer_email = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    app.customer_email.grid(row=row, column=2, pady=SPACING_SM, padx=SPACING_SM, sticky='w')
    row += 1

    # Separator
    ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=SPACING_MD)
    row += 1

    # Jobs configuration
    ttk.Label(form_frame, text="Jobs:", font=FONT_BOLD).grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=(0, SPACING_MD))
    app.num_jobs = tk.Spinbox(form_frame, from_=0, to=10, width=SPINBOX_WIDTH_MEDIUM)
    app.num_jobs.delete(0, tk.END)
    app.num_jobs.insert(0, "0")
    app.num_jobs.grid(row=row, column=2, pady=SPACING_SM, padx=SPACING_SM, sticky='w')
    row += 1

    # Sub-jobs per job configuration
    ttk.Label(form_frame, text="Sub-jobs per Job:", font=FONT_BODY).grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=(0, SPACING_MD))
    app.num_subjobs = tk.Spinbox(form_frame, from_=0, to=10, width=SPINBOX_WIDTH_MEDIUM)
    app.num_subjobs.delete(0, tk.END)
    app.num_subjobs.insert(0, "0")
    app.num_subjobs.grid(row=row, column=2, pady=SPACING_SM, padx=SPACING_SM, sticky='w')
    row += 1

    # Calculation display
    app.customer_calc_label = ttk.Label(form_frame, text="Will create: 1 customer", foreground='gray')
    app.customer_calc_label.grid(row=row, column=0, columnspan=3, sticky='w', pady=SPACING_SM, padx=(0, SPACING_MD))
    row += 1

    # Bind spinboxes to update calculation
    app.num_jobs.config(command=lambda: update_customer_calculation(app))
    app.num_subjobs.config(command=lambda: update_customer_calculation(app))

    # Separator
    ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=SPACING_MD)
    row += 1

    # Helper function to create field row
    def create_field_row(label_text, var_name, entry_name, default_random=True):
        nonlocal row
        # Checkbox
        var = tk.BooleanVar(value=default_random)
        setattr(app, var_name, var)

        chk = ttk.Checkbutton(form_frame, text="Random", variable=var)
        chk.grid(row=row, column=1, sticky='w', pady=SPACING_SM)

        # Label
        ttk.Label(form_frame, text=label_text).grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=(0, SPACING_MD))

        # Entry
        entry = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
        entry.grid(row=row, column=2, pady=SPACING_SM, padx=SPACING_SM, sticky='w')
        setattr(app, entry_name, entry)

        # Bind checkbox to enable/disable entry
        def toggle_entry(*args):
            if var.get():
                entry.config(state='disabled')
            else:
                entry.config(state='normal')

        var.trace_add('write', toggle_entry)
        toggle_entry()  # Set initial state

        row += 1

    # Simple fields
    create_field_row("First Name:", "random_first_name", "customer_first_name")
    create_field_row("Last Name:", "random_last_name", "customer_last_name")
    create_field_row("Company:", "random_company", "customer_company")
    create_field_row("Phone:", "random_phone", "customer_phone")

    # Billing Address section
    ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=SPACING_MD)
    row += 1

    # Billing address checkbox
    app.random_billing_address = tk.BooleanVar(value=True)
    chk = ttk.Checkbutton(form_frame, text="Random", variable=app.random_billing_address)
    chk.grid(row=row, column=1, sticky='w', pady=SPACING_SM)
    ttk.Label(form_frame, text="Billing Address:", font=FONT_BOLD).grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=(0, SPACING_MD))
    row += 1

    # Billing address fields
    app.customer_bill_addr1 = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    ttk.Label(form_frame, text="  Street:").grid(row=row, column=0, sticky='w', pady=SPACING_XS, padx=(0, SPACING_MD))
    app.customer_bill_addr1.grid(row=row, column=2, pady=SPACING_XS, padx=SPACING_SM, sticky='w')
    row += 1

    app.customer_bill_city = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    ttk.Label(form_frame, text="  City:").grid(row=row, column=0, sticky='w', pady=SPACING_XS, padx=(0, SPACING_MD))
    app.customer_bill_city.grid(row=row, column=2, pady=SPACING_XS, padx=SPACING_SM, sticky='w')
    row += 1

    app.customer_bill_state = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    ttk.Label(form_frame, text="  State:").grid(row=row, column=0, sticky='w', pady=SPACING_XS, padx=(0, SPACING_MD))
    app.customer_bill_state.grid(row=row, column=2, pady=SPACING_XS, padx=SPACING_SM, sticky='w')
    row += 1

    app.customer_bill_zip = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    ttk.Label(form_frame, text="  Zip:").grid(row=row, column=0, sticky='w', pady=SPACING_XS, padx=(0, SPACING_MD))
    app.customer_bill_zip.grid(row=row, column=2, pady=SPACING_XS, padx=SPACING_SM, sticky='w')
    row += 1

    # Bind billing address checkbox
    app.random_billing_address.trace_add('write', lambda *args: toggle_billing_address_fields(app))
    toggle_billing_address_fields(app)

    # Shipping Address section
    ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=SPACING_MD)
    row += 1

    # Shipping address checkbox
    app.random_shipping_address = tk.BooleanVar(value=True)
    chk = ttk.Checkbutton(form_frame, text="Random", variable=app.random_shipping_address)
    chk.grid(row=row, column=1, sticky='w', pady=SPACING_SM)
    ttk.Label(form_frame, text="Shipping Address:", font=FONT_BOLD).grid(row=row, column=0, sticky='w', pady=SPACING_SM, padx=(0, SPACING_MD))
    row += 1

    # Shipping address fields
    app.customer_ship_addr1 = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    ttk.Label(form_frame, text="  Street:").grid(row=row, column=0, sticky='w', pady=SPACING_XS, padx=(0, SPACING_MD))
    app.customer_ship_addr1.grid(row=row, column=2, pady=SPACING_XS, padx=SPACING_SM, sticky='w')
    row += 1

    app.customer_ship_city = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    ttk.Label(form_frame, text="  City:").grid(row=row, column=0, sticky='w', pady=SPACING_XS, padx=(0, SPACING_MD))
    app.customer_ship_city.grid(row=row, column=2, pady=SPACING_XS, padx=SPACING_SM, sticky='w')
    row += 1

    app.customer_ship_state = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    ttk.Label(form_frame, text="  State:").grid(row=row, column=0, sticky='w', pady=SPACING_XS, padx=(0, SPACING_MD))
    app.customer_ship_state.grid(row=row, column=2, pady=SPACING_XS, padx=SPACING_SM, sticky='w')
    row += 1

    app.customer_ship_zip = ttk.Entry(form_frame, width=ENTRY_WIDTH_LONG)
    ttk.Label(form_frame, text="  Zip:").grid(row=row, column=0, sticky='w', pady=SPACING_XS, padx=(0, SPACING_MD))
    app.customer_ship_zip.grid(row=row, column=2, pady=SPACING_XS, padx=SPACING_SM, sticky='w')
    row += 1

    # Bind shipping address checkbox
    app.random_shipping_address.trace_add('write', lambda *args: toggle_shipping_address_fields(app))
    toggle_shipping_address_fields(app)

    # Buttons
    button_frame = ttk.Frame(content)
    button_frame.pack(pady=SPACING_MD)

    ttk.Button(button_frame, text="Select All Random", command=lambda: select_all_customer_fields(app)).pack(side='left', padx=SPACING_SM)
    ttk.Button(button_frame, text="Clear All Random", command=lambda: clear_all_customer_fields(app)).pack(side='left', padx=SPACING_SM)

    # Create button
    app.create_customer_btn = ttk.Button(
        content,
        text="Create New Customer",
        command=lambda: create_customer(app)
    )
    app.create_customer_btn.pack(pady=SPACING_MD)
