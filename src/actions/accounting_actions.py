"""
Accounting action handlers for QuickBooks Desktop Test Tool.

Handles customer creation and field management for Accounting mode.
All fields are manual entry - no random generation.
"""

import threading
from tkinter import messagebox

from actions.paste_parser import parse_pasted_text
from config import AppConfig
from workers import create_customer_worker


def parse_and_populate_accounting(app):
    """
    Parse pasted text and populate accounting form fields.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Get pasted text
    paste_text = app.acct_paste_text.get('1.0', 'end-1c').strip()

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

    # Auto-populate form with recognized fields immediately
    recognized_data = result.get('data', {})
    _populate_accounting_fields(app, recognized_data)

    # Check if we have unrecognized fields that need mapping
    has_unrecognized = bool(result.get('unrecognized'))

    if has_unrecognized:
        # Show preview dialog for mapping unrecognized fields
        from ui.parse_preview_dialog import ParsePreviewDialog
        dialog = ParsePreviewDialog(app.root, result)
        additional_data = dialog.show()

        if additional_data:
            # Add any newly mapped fields to the form
            _populate_accounting_fields(app, additional_data)
            field_count = len(additional_data)
            app.acct_paste_status.config(
                text=f"Populated {field_count} field(s)",
                foreground='green'
            )
        else:
            # User cancelled - form already has recognized fields
            app.acct_paste_status.config(
                text=f"Populated {len(recognized_data)} field(s) (some unrecognized)",
                foreground='orange'
            )
    else:
        # All fields recognized - already populated
        app.acct_paste_status.config(
            text=f"Populated {len(recognized_data)} field(s)",
            foreground='green'
        )


def _populate_accounting_fields(app, data):
    """
    Populate accounting form fields from parsed data.

    Args:
        app: Reference to the main QBDTestToolApp instance
        data: Dict of field_name -> value
    """
    # Email
    if 'email' in data:
        app.acct_email.delete(0, 'end')
        app.acct_email.insert(0, data['email'])

    # ISO (read-only)
    if 'iso' in data:
        app.acct_iso.config(state='normal')
        app.acct_iso.delete(0, 'end')
        app.acct_iso.insert(0, data['iso'])
        app.acct_iso.config(state='readonly')

    # CID (Account Number)
    if 'account_number' in data:
        app.acct_cid.delete(0, 'end')
        app.acct_cid.insert(0, data['account_number'])

    # First Name
    if 'first_name' in data:
        app.acct_first_name.delete(0, 'end')
        app.acct_first_name.insert(0, data['first_name'])

    # Last Name
    if 'last_name' in data:
        app.acct_last_name.delete(0, 'end')
        app.acct_last_name.insert(0, data['last_name'])

    # Company
    if 'company' in data:
        app.acct_company.delete(0, 'end')
        app.acct_company.insert(0, data['company'])

    # Phone
    if 'phone' in data:
        app.acct_phone.delete(0, 'end')
        app.acct_phone.insert(0, data['phone'])

    # Address
    if 'bill_addr1' in data:
        app.acct_address.delete(0, 'end')
        app.acct_address.insert(0, data['bill_addr1'])

    # City
    if 'bill_city' in data:
        app.acct_city.delete(0, 'end')
        app.acct_city.insert(0, data['bill_city'])

    # State
    if 'bill_state' in data:
        app.acct_state.delete(0, 'end')
        app.acct_state.insert(0, data['bill_state'])

    # Zip
    if 'bill_zip' in data:
        app.acct_zip.delete(0, 'end')
        app.acct_zip.insert(0, data['bill_zip'])

    # Notes
    if 'notes' in data:
        app.acct_notes.delete('1.0', 'end')
        app.acct_notes.insert('1.0', data['notes'])


def clear_accounting_fields(app):
    """
    Clear all accounting form fields.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Clear paste text
    app.acct_paste_text.delete('1.0', 'end')
    app.acct_paste_status.config(text="", foreground='gray')

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


def create_accounting_customer(app):
    """
    Create customer in QuickBooks from accounting form fields.

    All fields are treated as manual values (no random generation).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Validate email
    email = app.acct_email.get().strip()
    if not email:
        messagebox.showerror("Error", "Email is required!")
        return

    # Collect all fields as manual values
    # field_config: all False = all manual
    field_config = {
        'first_name': False,
        'last_name': False,
        'company': False,
        'phone': False,
        'billing_address': False,
        'shipping_address': False
    }

    # Collect manual values
    manual_values = {
        'first_name': app.acct_first_name.get().strip() or None,
        'last_name': app.acct_last_name.get().strip() or None,
        'company': app.acct_company.get().strip() or None,
        'phone': app.acct_phone.get().strip() or None,
    }

    # Collect billing address
    addr = app.acct_address.get().strip()
    city = app.acct_city.get().strip()
    state = app.acct_state.get().strip()
    zip_code = app.acct_zip.get().strip()

    if addr or city or state or zip_code:
        manual_values['billing_address'] = {
            'addr1': addr or None,
            'city': city or None,
            'state': state or None,
            'postal_code': zip_code or None
        }
    else:
        manual_values['billing_address'] = None

    # No shipping address in accounting mode (can be same as billing)
    manual_values['shipping_address'] = None

    # Collect CID (Account Number)
    cid = app.acct_cid.get().strip()
    if cid:
        manual_values['account_number'] = cid

    # Notes field is for BO reference only - NOT sent to QuickBooks

    # No jobs in accounting mode
    num_jobs = 0
    num_subjobs = 0

    # Disable button and update status
    app.acct_create_btn.config(state='disabled')
    app.acct_status_label.config(text="Creating customer...", foreground='orange')

    # Launch background thread
    thread = threading.Thread(
        target=_create_customer_worker_wrapper,
        args=(app, email, field_config, manual_values, num_jobs, num_subjobs),
        daemon=True
    )
    thread.start()


def _create_customer_worker_wrapper(app, email, field_config, manual_values, num_jobs, num_subjobs):
    """
    Wrapper for create_customer_worker that handles accounting-specific UI updates.
    """
    # Call the existing worker
    create_customer_worker(app, email, field_config, manual_values, num_jobs, num_subjobs)

    # Re-enable button (worker already does this for create_customer_btn)
    # But we need to handle acct_create_btn
    def update_ui():
        app.acct_create_btn.config(state='normal')
        # Status will be updated by the worker callback

    app.root.after(0, update_ui)
