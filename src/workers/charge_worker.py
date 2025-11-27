"""
Statement Charge creation worker for QuickBooks Desktop Test Tool.

Background worker for creating batch statement charges in QuickBooks.
"""

import json
from datetime import datetime
from tkinter import messagebox
from qb import QBIPCClient, disconnect_qb
from qb.qbfc_connection import QBFCConnectionError
from mock_generation import ChargeGenerator
from store.state import StatementChargeRecord
from store.actions import add_statement_charge
from workers.monitor_worker import update_invoice_tree
from app_logging import LOG_NORMAL, LOG_VERBOSE, LOG_DEBUG
from app_logging.logging_config import should_log
from config import AppConfig


def _format_charge_debug(charge_data: dict, result: dict) -> tuple:
    """Format statement charge operation debug info for logging."""
    # Request info: show ALL data being sent
    request_str = json.dumps(charge_data, indent=2, default=str)

    # Response info
    if result.get('success'):
        data = result.get('data', {})
        response_str = f"txn_id={data.get('txn_id')}, amount=${float(data.get('amount', 0)):.2f}"
    else:
        response_str = f"ERROR: {result.get('error', 'Unknown error')}"

    return request_str, response_str


def create_charge_worker(app, customer: dict, num_charges: int,
                         amount_min: float, amount_max: float, date_range: str, items: list,
                         class_ref: str = None):
    """Worker function to create batch statement charges in background."""
    successful_count = 0
    failed_count = 0

    try:
        import random
        from datetime import timedelta

        # Calculate date range based on selection
        today = datetime.now()
        if date_range == 'Today Only':
            days_back = 0
        elif date_range == 'Last 7 Days':
            days_back = 7
        elif date_range == 'Last 30 Days':
            days_back = 30
        else:
            days_back = 0  # Default to today

        app.root.after(0, lambda: app._log_create(f"Starting batch creation of {num_charges} statement charge(s) for {customer['name']} ({date_range})..."))

        # Filter to only item types valid for charges (same as invoices/sales receipts)
        VALID_LINE_ITEM_TYPES = {'Service', 'Inventory', 'NonInventory', 'OtherCharge'}
        valid_items = [item for item in items if item.get('type') in VALID_LINE_ITEM_TYPES]

        # Select a random item to use for all charges
        # For statement charges, we typically use a generic service item
        charge_item = random.choice(valid_items) if valid_items else None

        # Create QB client once for entire batch
        qb = QBIPCClient()

        # Create multiple statement charges
        for i in range(num_charges):
            try:
                # Randomize amount within specified range
                amount = round(random.uniform(amount_min, amount_max), 2)

                # Randomize transaction date within range
                if days_back > 0:
                    random_days = random.randint(0, days_back)
                    txn_date = (today - timedelta(days=random_days)).strftime('%Y-%m-%d')
                else:
                    txn_date = today.strftime('%Y-%m-%d')

                # Generate charge data
                charge_data = ChargeGenerator.generate_statement_charge_data(
                    customer_ref=customer['list_id'],
                    amount=amount,
                    item_ref=charge_item['list_id'] if charge_item else None,
                    txn_date=txn_date,
                    class_ref=class_ref
                )

                # Log current progress
                charge_num = i + 1
                app.root.after(0, lambda n=charge_num, amt=amount:
                              app._log_create(f"[{n}/{num_charges}] Creating statement charge: Amount: ${amt:.2f}", LOG_VERBOSE))

                # Send to QuickBooks via QBFC
                parser_result = qb.execute_operation('add_charge', {'charge_data': charge_data})

                # DEBUG: Log request and response (only if DEBUG is enabled)
                if should_log(LOG_DEBUG, AppConfig.get_log_level()):
                    req_str, resp_str = _format_charge_debug(charge_data, parser_result)
                    app.root.after(0, lambda n=charge_num, r=req_str:
                                  app._log_create(f"  [DEBUG {n}] Request: {r}", LOG_DEBUG))
                    app.root.after(0, lambda n=charge_num, r=resp_str:
                                  app._log_create(f"  [DEBUG {n}] Response: {r}", LOG_DEBUG))

                if parser_result['success']:
                    charge_info = parser_result['data']

                    # Create statement charge record
                    # Note: ChargeAddRs doesn't return ref_number, use txn_id as placeholder
                    # The real ref_number will be populated when monitoring queries the charge
                    charge_record = StatementChargeRecord(
                        txn_id=charge_info['txn_id'],
                        ref_number=charge_info.get('ref_number', charge_info['txn_id']),
                        customer_name=customer.get('full_name', customer['name']),
                        amount=float(charge_info.get('amount', amount)),
                        status='open',
                        created_at=datetime.now()
                    )

                    app.store.dispatch(add_statement_charge(charge_record))
                    app.root.after(0, lambda: update_invoice_tree(app))

                    app.root.after(0, lambda n=charge_num, tid=charge_info['txn_id'], amt=charge_info.get('amount', amount):
                                  app._log_create(f"  ✓ [{n}/{num_charges}] Statement charge created: ${amt} (ID: {tid})", LOG_VERBOSE))
                    successful_count += 1

                else:
                    error_msg = parser_result.get('error', 'Unknown error')
                    app.root.after(0, lambda n=charge_num, msg=error_msg:
                                  app._log_create(f"  ✗ [{n}/{num_charges}] Error: {msg}"))
                    failed_count += 1

            except Exception as e:
                error_str = str(e)
                charge_num = i + 1
                app.root.after(0, lambda n=charge_num, msg=error_str:
                              app._log_create(f"  ✗ [{n}/{num_charges}] Error: {msg}"))
                failed_count += 1

        # Final summary
        summary = f"Batch complete: {successful_count} succeeded, {failed_count} failed out of {num_charges} total"
        app.root.after(0, lambda s=summary: app._log_create(f"\n{s}"))

        if failed_count > 0 and successful_count > 0:
            app.root.after(0, lambda: messagebox.showwarning("Batch Complete", summary))
        elif failed_count > 0:
            app.root.after(0, lambda: messagebox.showerror("Batch Failed", summary))
        else:
            app.root.after(0, lambda: messagebox.showinfo("Batch Complete", summary))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Batch error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        # Disconnect from QuickBooks after batch operation completes
        disconnect_qb()
        # Auto-save session after creating statement charges
        app.root.after(0, lambda: app._auto_save_session())
        # Re-enable button and update status
        app.root.after(0, lambda: app.create_transaction_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))
