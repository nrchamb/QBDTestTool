"""
UI utility actions for QuickBooks Desktop Test Tool.

Pure utility functions extracted from UI files to maintain separation of concerns.
UI files should only contain layout code, while this module handles UI state logic.
"""

from config import AppConfig


# Customer field management

def select_all_customer_fields(app):
    """
    Select all customer field checkboxes.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    app.random_first_name.set(True)
    app.random_last_name.set(True)
    app.random_company.set(True)
    app.random_phone.set(True)
    app.random_billing_address.set(True)
    app.random_shipping_address.set(True)


def clear_all_customer_fields(app):
    """
    Clear all customer field checkboxes.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    app.random_first_name.set(False)
    app.random_last_name.set(False)
    app.random_company.set(False)
    app.random_phone.set(False)
    app.random_billing_address.set(False)
    app.random_shipping_address.set(False)


def update_customer_calculation(app):
    """
    Update the customer creation calculation display.

    Calculates total entities to be created based on jobs and sub-jobs.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        jobs = int(app.num_jobs.get() or 0)
        subjobs = int(app.num_subjobs.get() or 0)
        total = 1 + jobs + (jobs * subjobs)

        parts = [f"1 customer"]
        if jobs > 0:
            parts.append(f"{jobs} job{'s' if jobs > 1 else ''}")
        if jobs > 0 and subjobs > 0:
            total_subjobs = jobs * subjobs
            parts.append(f"{total_subjobs} sub-job{'s' if total_subjobs > 1 else ''}")

        app.customer_calc_label.config(text=f"Will create: {' + '.join(parts)} = {total} total")
    except ValueError:
        app.customer_calc_label.config(text="Will create: 1 customer")


def toggle_billing_address_fields(app):
    """
    Toggle billing address fields based on random checkbox state.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = 'disabled' if app.random_billing_address.get() else 'normal'
    app.customer_bill_addr1.config(state=state)
    app.customer_bill_city.config(state=state)
    app.customer_bill_state.config(state=state)
    app.customer_bill_zip.config(state=state)


def toggle_shipping_address_fields(app):
    """
    Toggle shipping address fields based on random checkbox state.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = 'disabled' if app.random_shipping_address.get() else 'normal'
    app.customer_ship_addr1.config(state=state)
    app.customer_ship_city.config(state=state)
    app.customer_ship_state.config(state=state)
    app.customer_ship_zip.config(state=state)


# Transaction form management

def update_transaction_form_visibility(app):
    """
    Update transaction form field visibility based on selected transaction type.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    txn_type = app.transaction_type.get()

    # Get references to conditional fields (need to be stored on app during setup)
    line_items_label = app.txn_line_items_label
    line_items_frame = app.txn_line_items_frame
    po_label = app.txn_po_label
    terms_label = app.txn_terms_label
    class_label = app.txn_class_label

    # Line items: Show for Invoice and Sales Receipt, hide for Charge
    if txn_type in ["Invoice", "SalesReceipt"]:
        line_items_label.grid()
        line_items_frame.grid()
    else:
        line_items_label.grid_remove()
        line_items_frame.grid_remove()

    # Invoice-specific fields: Show only for Invoice
    if txn_type == "Invoice":
        po_label.grid()
        app.txn_po_prefix.grid()
        terms_label.grid()
        app.txn_terms_combo.grid()
        class_label.grid()
        app.txn_class_combo.grid()
    else:
        po_label.grid_remove()
        app.txn_po_prefix.grid_remove()
        terms_label.grid_remove()
        app.txn_terms_combo.grid_remove()
        class_label.grid_remove()
        app.txn_class_combo.grid_remove()

    # Update button text
    if txn_type == "Invoice":
        app.create_transaction_btn.config(text="Create Invoices (Batch)")
    elif txn_type == "SalesReceipt":
        app.create_transaction_btn.config(text="Create Sales Receipts (Batch)")
    else:
        app.create_transaction_btn.config(text="Create Statement Charges (Batch)")


# Log panel management

def toggle_create_log(app):
    """
    Toggle activity log visibility for both Create and Monitor tabs.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    if app.create_log_collapsed.get():
        # Currently collapsed, expand both logs
        app.create_paned.add(app.create_log_pane)
        app.create_log_toggle_btn.config(text="▼ Hide Log")
        app.create_log_collapsed.set(False)

        # Also expand monitor log
        if hasattr(app, 'monitor_paned') and hasattr(app, 'monitor_log_pane'):
            app.monitor_paned.add(app.monitor_log_pane)
            app.monitor_log_toggle_btn.config(text="▼ Hide Log")
            app.monitor_log_collapsed.set(False)
    else:
        # Currently expanded, collapse both logs
        app.create_paned.remove(app.create_log_pane)
        app.create_log_toggle_btn.config(text="▶ Show Log")
        app.create_log_collapsed.set(True)

        # Also collapse monitor log
        if hasattr(app, 'monitor_paned') and hasattr(app, 'monitor_log_pane'):
            app.monitor_paned.remove(app.monitor_log_pane)
            app.monitor_log_toggle_btn.config(text="▶ Show Log")
            app.monitor_log_collapsed.set(True)

        # Save UI state
        AppConfig.save_ui_state(app.create_log_collapsed.get())


def toggle_monitor_log(app):
    """
    Toggle activity log visibility for both Monitor and Create tabs.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    if app.monitor_log_collapsed.get():
        # Currently collapsed, expand both logs
        app.monitor_paned.add(app.monitor_log_pane)
        app.monitor_log_toggle_btn.config(text="▼ Hide Log")
        app.monitor_log_collapsed.set(False)

        # Also expand create log
        if hasattr(app, 'create_paned') and hasattr(app, 'create_log_pane'):
            app.create_paned.add(app.create_log_pane)
            app.create_log_toggle_btn.config(text="▼ Hide Log")
            app.create_log_collapsed.set(False)
    else:
        # Currently expanded, collapse both logs
        app.monitor_paned.remove(app.monitor_log_pane)
        app.monitor_log_toggle_btn.config(text="▶ Show Log")
        app.monitor_log_collapsed.set(True)

        # Also collapse create log
        if hasattr(app, 'create_paned') and hasattr(app, 'create_log_pane'):
            app.create_paned.remove(app.create_log_pane)
            app.create_log_toggle_btn.config(text="▶ Show Log")
            app.create_log_collapsed.set(True)

        # Save UI state
        AppConfig.save_ui_state(app.monitor_log_collapsed.get())


# Settings management

def save_log_level_setting(app):
    """
    Save log level setting when changed in settings tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    new_level = app.log_level_combo.get()
    AppConfig.save_log_level(new_level)


def save_persistence_settings(app):
    """
    Save persistence settings when changed in settings tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    AppConfig.save_persistence_settings(
        auto_load=app.auto_load_var.get()
    )
