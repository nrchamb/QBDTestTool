"""
Sales Receipt creation worker for QuickBooks Desktop Test Tool.

Background worker for creating batch sales receipts in QuickBooks.
"""

import json
from datetime import datetime
from tkinter import messagebox
from qb import QBIPCClient, disconnect_qb
from qb.qbfc_connection import QBFCConnectionError
from mock_generation import SalesReceiptGenerator
from store.state import SalesReceiptRecord
from store.actions import add_sales_receipt
from app_logging import LOG_NORMAL, LOG_VERBOSE, LOG_DEBUG
from app_logging.logging_config import should_log
from config import AppConfig


def _format_receipt_debug(receipt_data: dict, result: dict) -> tuple:
    """Format sales receipt operation debug info for logging."""
    # Request info: show ALL data being sent
    request_str = json.dumps(receipt_data, indent=2, default=str)

    # Response info
    if result.get('success'):
        data = result.get('data', {})
        total = data.get('total_amount') or data.get('balance_remaining') or 0
        response_str = f"txn_id={data.get('txn_id')}, ref_number={data.get('ref_number')}, total=${float(total):.2f}"
    else:
        response_str = f"ERROR: {result.get('error', 'Unknown error')}"

    return request_str, response_str


def create_sales_receipt_worker(app, customer: dict, num_receipts: int,
                                 line_items_min: int, line_items_max: int,
                                 amount_min: float, amount_max: float, date_range: str, items: list,
                                 class_ref: str = None, allow_item_reuse: bool = False):
    """Worker function to create batch sales receipts using batch QBFC operation."""
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

        app.root.after(0, lambda: app._log_create(f"Starting batch creation of {num_receipts} sales receipt(s) for {customer['name']} ({date_range})..."))

        # Filter to only item types valid for line items
        VALID_LINE_ITEM_TYPES = {'Service', 'Inventory', 'NonInventory', 'OtherCharge'}
        valid_items = [item for item in items if item.get('type') in VALID_LINE_ITEM_TYPES]

        # Phase 1: Generate all sales receipt data
        app.root.after(0, lambda: app._log_create(f"Generating {num_receipts} sales receipt(s)..."))
        receipt_data_list = []
        receipt_amounts = []  # Track amounts for logging

        for i in range(num_receipts):
            # Randomize parameters within specified ranges
            num_lines = random.randint(line_items_min, line_items_max)
            amount = round(random.uniform(amount_min, amount_max), 2)
            receipt_amounts.append(amount)

            # Randomize transaction date within range
            if days_back > 0:
                random_days = random.randint(0, days_back)
                txn_date = (today - timedelta(days=random_days)).strftime('%Y-%m-%d')
            else:
                txn_date = today.strftime('%Y-%m-%d')

            # Select random items for sales receipt line items
            if allow_item_reuse:
                # Allow same item multiple times (for large invoices with limited items)
                selected_items = random.choices(valid_items, k=num_lines) if valid_items else []
            else:
                # No duplicates within same receipt (caps at available items)
                selected_items = random.sample(valid_items, min(num_lines, len(valid_items)))
            item_refs = [item['list_id'] for item in selected_items]

            # Generate sales receipt data
            receipt_data = SalesReceiptGenerator.generate_sales_receipt_data(
                customer_ref=customer['list_id'],
                num_line_items=num_lines,
                total_amount=amount,
                item_refs=item_refs,
                txn_date=txn_date,
                class_ref=class_ref
            )
            receipt_data_list.append(receipt_data)

            # DEBUG: Log generated values
            if should_log(LOG_DEBUG, AppConfig.get_log_level()):
                item_names = [item['name'] for item in selected_items]
                app.root.after(0, lambda n=i+1, amt=amount, dt=txn_date, lines=num_lines, items=item_names:
                              app._log_create(f"  [DEBUG {n}] Amount=${amt:.2f}, Date={dt}, Lines={lines}, Items={items}", LOG_DEBUG))

        # Phase 2: Send batch to QuickBooks
        app.root.after(0, lambda: app._log_create(f"Sending batch of {num_receipts} sales receipt(s) to QuickBooks..."))
        qb = QBIPCClient()
        parser_result = qb.execute_operation('add_sales_receipts_batch', {'sales_receipt_data_list': receipt_data_list})

        # Phase 3: Process responses
        # Handle both batch format (multiple items) and single format (1 item)
        if parser_result['success']:
            # Check for batch format first
            if 'sales_receipts' in parser_result.get('data', {}):
                results = parser_result['data']['sales_receipts']
            else:
                # Single item format - wrap in list for uniform processing
                results = [{'success': True, 'data': parser_result['data']}]

            for i, result in enumerate(results):
                receipt_num = i + 1
                if result.get('success'):
                    receipt_info = result['data']

                    # Safely extract amounts
                    total_amount_str = receipt_info.get('total_amount')
                    total_amt = float(total_amount_str) if total_amount_str else receipt_amounts[i]

                    # Sales receipts start as open (no payment method set)
                    status = 'open'

                    receipt_record = SalesReceiptRecord(
                        txn_id=receipt_info['txn_id'],
                        ref_number=receipt_info['ref_number'],
                        customer_name=customer.get('full_name', customer['name']),
                        amount=total_amt,
                        status=status,
                        created_at=datetime.now()
                    )

                    app.store.dispatch(add_sales_receipt(receipt_record))
                    app.root.after(0, lambda n=receipt_num, ref=receipt_info['ref_number'], tid=receipt_info['txn_id']:
                                  app._log_create(f"  ✓ [{n}/{num_receipts}] Sales receipt created: {ref} (ID: {tid})", LOG_VERBOSE))
                    successful_count += 1
                else:
                    error_msg = result.get('error', 'Unknown error')
                    app.root.after(0, lambda n=receipt_num, msg=error_msg:
                                  app._log_create(f"  ✗ [{n}/{num_receipts}] Error: {msg}"))
                    failed_count += 1

            # Update tree once after all records added
            from workers.monitor_worker import update_invoice_tree
            app.root.after(0, lambda: update_invoice_tree(app))
        else:
            # Batch operation failed entirely
            error_msg = parser_result.get('error', 'Batch operation failed')
            app.root.after(0, lambda msg=error_msg: app._log_create(f"✗ Batch error: {msg}"))
            failed_count = num_receipts

        # Final summary
        summary = f"Batch complete: {successful_count} succeeded, {failed_count} failed out of {num_receipts} total"
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
        # Auto-save session after creating sales receipts
        app.root.after(0, lambda: app._auto_save_session())
        # Re-enable button and update status
        app.root.after(0, lambda: app.create_transaction_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))