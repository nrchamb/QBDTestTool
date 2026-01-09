"""
Customer action handlers for QuickBooks Desktop Test Tool.

Extracted from app.py to reduce monolithic file size.
"""

import threading
from tkinter import messagebox
from workers import create_customer_worker
from actions.paste_parser import parse_pasted_text
from config import AppConfig


def update_customer_combo(app):
    """
    Update all customer dropdowns with current customer list from state.

    Uses full_name (Customer:Job format) with visual indentation for sub-customers.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

    # Build display list with indentation based on sublevel
    customer_names = []
    app.customer_listid_map = {}

    for c in state.customers:
        # Use full_name which shows Customer:Job hierarchy
        full_name = c.get('full_name', c['name'])
        sublevel = c.get('sublevel', 0)

        # Add visual indentation for sub-customers/jobs (2 spaces per level)
        indent = "  " * sublevel
        display_name = f"{indent}{full_name}"

        # Add email for additional context
        email = c.get('email', '')
        if email:
            display_name = f"{display_name} ({email})"
        else:
            display_name = f"{display_name} (no email)"

        customer_names.append(display_name)
        app.customer_listid_map[display_name] = c['list_id']

    # Update all customer comboboxes
    for combo in app.customer_combos:
        # Support both SearchableCombobox and regular Combobox
        if hasattr(combo, 'set_values'):
            combo.set_values(customer_names)
        else:
            combo['values'] = customer_names

        if customer_names:
            combo.current(len(customer_names) - 1)

    # Update status label on Setup subtab
    count = len(state.customers)
    items_count = len(state.items)

    if count > 0:
        app.customers_status_label.config(
            text=f"{count} customer{'s' if count != 1 else ''} loaded",
            foreground='green'
        )
    else:
        app.customers_status_label.config(
            text="No customers loaded",
            foreground='red'
        )

    # Update summary - only show ready when BOTH customers and items are loaded
    if hasattr(app, 'setup_summary_label'):
        if count > 0 and items_count > 0:
            app.setup_summary_label.config(
                text=f"{count} customers, {items_count} items loaded - Ready to create transactions"
            )
        elif count > 0 or items_count > 0:
            app.setup_summary_label.config(
                text=f"{count} customers, {items_count} items loaded - Load both to begin"
            )
        else:
            app.setup_summary_label.config(
                text="Load customers and items from QuickBooks to begin"
            )


def create_customer(app):
    """
    Create a customer in QuickBooks (wrapper - launches background thread).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    email = app.customer_email.get().strip()

    if not email:
        messagebox.showerror("Error", "Email is required!")
        return

    # Collect field enable states (True = random, False = manual)
    field_config = {
        'first_name': app.random_first_name.get(),
        'last_name': app.random_last_name.get(),
        'company': app.random_company.get(),
        'phone': app.random_phone.get(),
        'billing_address': app.random_billing_address.get(),
        'shipping_address': app.random_shipping_address.get()
    }

    # Collect manual values (only used when field_config[field] is False)
    manual_values = {
        'first_name': app.customer_first_name.get().strip() if not app.random_first_name.get() else None,
        'last_name': app.customer_last_name.get().strip() if not app.random_last_name.get() else None,
        'company': app.customer_company.get().strip() if not app.random_company.get() else None,
        'phone': app.customer_phone.get().strip() if not app.random_phone.get() else None,
    }

    # Collect billing address if not random
    if not app.random_billing_address.get():
        bill_addr1 = app.customer_bill_addr1.get().strip()
        bill_city = app.customer_bill_city.get().strip()
        bill_state = app.customer_bill_state.get().strip()
        bill_zip = app.customer_bill_zip.get().strip()

        # Only include billing address if at least one field has data
        if bill_addr1 or bill_city or bill_state or bill_zip:
            manual_values['billing_address'] = {
                'addr1': bill_addr1 or None,
                'city': bill_city or None,
                'state': bill_state or None,
                'postal_code': bill_zip or None
            }
        else:
            manual_values['billing_address'] = None
    else:
        manual_values['billing_address'] = None

    # Collect shipping address if not random
    if not app.random_shipping_address.get():
        ship_addr1 = app.customer_ship_addr1.get().strip()
        ship_city = app.customer_ship_city.get().strip()
        ship_state = app.customer_ship_state.get().strip()
        ship_zip = app.customer_ship_zip.get().strip()

        # Only include shipping address if at least one field has data
        if ship_addr1 or ship_city or ship_state or ship_zip:
            manual_values['shipping_address'] = {
                'addr1': ship_addr1 or None,
                'city': ship_city or None,
                'state': ship_state or None,
                'postal_code': ship_zip or None
            }
        else:
            manual_values['shipping_address'] = None
    else:
        manual_values['shipping_address'] = None

    # Collect CID (Account Number) if provided
    cid = app.customer_cid.get().strip() if hasattr(app, 'customer_cid') else ''
    if cid:
        manual_values['account_number'] = cid

    # Collect Notes if provided
    if hasattr(app, 'customer_notes'):
        notes = app.customer_notes.get('1.0', 'end-1c').strip()
        if notes:
            manual_values['notes'] = notes

    # Collect job configuration
    try:
        num_jobs = int(app.num_jobs.get() or 0)
        num_subjobs = int(app.num_subjobs.get() or 0)
    except ValueError:
        messagebox.showerror("Error", "Invalid job count values!")
        return

    # Disable button and update status
    app.create_customer_btn.config(state='disabled')
    total_records = 1 + num_jobs + (num_jobs * num_subjobs)
    app.status_bar.config(text=f"Creating {total_records} record(s)...")

    # Launch background thread
    thread = threading.Thread(
        target=create_customer_worker,
        args=(app, email, field_config, manual_values, num_jobs, num_subjobs),
        daemon=True
    )
    thread.start()


def parse_and_populate_from_paste(app):
    """
    Parse pasted text and show preview dialog, then populate customer fields.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Get pasted text
    paste_text = app.paste_text.get('1.0', 'end-1c').strip()

    if not paste_text:
        messagebox.showinfo("No Data", "Please paste customer data first.")
        return

    # Get custom mappings from config
    custom_mappings = AppConfig.get_custom_field_mappings()

    # Parse the text
    result = parse_pasted_text(paste_text, custom_mappings)

    if not result['success'] and not result.get('unrecognized'):
        # Nothing parsed at all
        messagebox.showwarning(
            "Parse Failed",
            "Could not parse any fields from the pasted text.\n\n"
            "Expected format:\nLabel: Value\nLabel: Value\n..."
        )
        return

    # Show preview dialog
    from ui.parse_preview_dialog import ParsePreviewDialog
    dialog = ParsePreviewDialog(app.root, result)
    final_data = dialog.show()

    if final_data is None:
        # User cancelled
        app.paste_status_label.config(text="Cancelled", foreground='gray')
        return

    # Populate form fields with parsed data
    _populate_customer_fields(app, final_data)

    # Update status
    field_count = len(final_data)
    app.paste_status_label.config(
        text=f"Populated {field_count} field(s)",
        foreground='green'
    )


def _populate_customer_fields(app, data):
    """
    Populate customer form fields from parsed data.

    Args:
        app: Reference to the main QBDTestToolApp instance
        data: Dict of field_name -> value
    """
    # Email
    if 'email' in data:
        app.customer_email.delete(0, 'end')
        app.customer_email.insert(0, data['email'])

    # ISO (read-only)
    if 'iso' in data:
        app.customer_iso.config(state='normal')
        app.customer_iso.delete(0, 'end')
        app.customer_iso.insert(0, data['iso'])
        app.customer_iso.config(state='readonly')

    # CID (Account Number)
    if 'account_number' in data:
        app.customer_cid.delete(0, 'end')
        app.customer_cid.insert(0, data['account_number'])

    # First Name
    if 'first_name' in data:
        app.random_first_name.set(False)  # Disable random
        app.customer_first_name.delete(0, 'end')
        app.customer_first_name.insert(0, data['first_name'])

    # Last Name
    if 'last_name' in data:
        app.random_last_name.set(False)
        app.customer_last_name.delete(0, 'end')
        app.customer_last_name.insert(0, data['last_name'])

    # Company
    if 'company' in data:
        app.random_company.set(False)
        app.customer_company.delete(0, 'end')
        app.customer_company.insert(0, data['company'])

    # Phone
    if 'phone' in data:
        app.random_phone.set(False)
        app.customer_phone.delete(0, 'end')
        app.customer_phone.insert(0, data['phone'])

    # Billing Address fields
    has_billing = any(k in data for k in ['bill_addr1', 'bill_city', 'bill_state', 'bill_zip'])
    if has_billing:
        app.random_billing_address.set(False)

        if 'bill_addr1' in data:
            app.customer_bill_addr1.delete(0, 'end')
            app.customer_bill_addr1.insert(0, data['bill_addr1'])
        if 'bill_city' in data:
            app.customer_bill_city.delete(0, 'end')
            app.customer_bill_city.insert(0, data['bill_city'])
        if 'bill_state' in data:
            app.customer_bill_state.delete(0, 'end')
            app.customer_bill_state.insert(0, data['bill_state'])
        if 'bill_zip' in data:
            app.customer_bill_zip.delete(0, 'end')
            app.customer_bill_zip.insert(0, data['bill_zip'])

    # Notes
    if 'notes' in data:
        app.customer_notes.delete('1.0', 'end')
        app.customer_notes.insert('1.0', data['notes'])
