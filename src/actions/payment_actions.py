"""
Payment actions for QuickBooks Desktop Test Tool.

TEMPORARY: For testing verification logic only - remove before shipping.
"""

import threading
from datetime import datetime
from tkinter import messagebox
from qb import QBIPCClient


def apply_test_payments(app, pay_percentage: float = 1.0, selected_refs: list = None):
    """
    Apply test payments to selected invoices and statement charges.

    TEMPORARY: For testing verification logic - remove before shipping.

    Posts memo to locations based on "Memo Change Detection" checkbox settings:
    - If "Check Transaction Memo" is enabled: updates transaction memo
    - If "Check Payment Memo" is enabled: sets payment memo

    Args:
        app: Reference to the main QBDTestToolApp instance
        pay_percentage: 1.0 for full payment, 0.5 for 50%
        selected_refs: List of ref_numbers to pay (required - must select items)
    """
    # Require selection - don't process all if nothing selected
    if not selected_refs:
        messagebox.showwarning("No Selection",
            "Please select one or more transactions in the table to pay.")
        return

    state = app.store.get_state()

    # Get checkbox settings for where to post memo
    post_to_transaction = app.check_transaction_memo_var.get()
    post_to_payment = app.check_payment_memo_var.get()

    # Collect transactions matching selection
    # Include 'partial' status for invoices/charges (can receive additional payments)
    open_invoices = [inv for inv in state.invoices
                    if inv.status in ('open', 'partial') and inv.ref_number in selected_refs]
    open_charges = [chg for chg in state.statement_charges
                   if chg.status in ('open', 'partial') and chg.ref_number in selected_refs]
    # Sales receipts are already paid - we just update memo/payment method if selected
    selected_receipts = [sr for sr in state.sales_receipts
                        if sr.ref_number in selected_refs]

    total_count = len(open_invoices) + len(open_charges) + len(selected_receipts)
    if total_count == 0:
        messagebox.showinfo("No Matching Transactions",
            "Selected items are either already closed or not found.")
        return

    # Get expected deposit account ListID
    deposit_account_name = state.expected_deposit_account
    deposit_account_id = None
    if deposit_account_name:
        for account in state.accounts:
            if account.get('full_name') == deposit_account_name:
                deposit_account_id = account.get('list_id')
                break

    if not deposit_account_id and deposit_account_name:
        app._log_monitor(f"Warning: Could not find deposit account '{deposit_account_name}'")

    pay_label = "100%" if pay_percentage == 1.0 else f"{int(pay_percentage * 100)}%"
    memo_targets = []
    if post_to_transaction:
        memo_targets.append("txn")
    if post_to_payment:
        memo_targets.append("pmt")
    memo_info = f" (memo: {'+'.join(memo_targets)})" if memo_targets else " (no memo)"

    app._log_monitor(f"[DEV] Applying {pay_label} payments to {total_count} transaction(s){memo_info}...")

    # Run in background thread
    def payment_worker():
        qb = QBIPCClient()
        success_count = 0
        error_count = 0

        # Process invoices
        for invoice in open_invoices:
            try:
                # Find customer ListID
                customer_id = _find_customer_id(state.customers, invoice.customer_name)
                if not customer_id:
                    app.root.after(0, lambda ref=invoice.ref_number:
                        app._log_monitor(f"  [DEV] Skip {ref}: customer not found"))
                    error_count += 1
                    continue

                # Calculate payment amount (round to 2 decimals for QBFC)
                payment_amount = round(invoice.amount * pay_percentage, 2)

                # Generate memo (simulates what external tool posts back)
                memo = f"Paid {datetime.now().strftime('%Y-%m-%d %H:%M')} - {invoice.ref_number}"

                # Step 1: Update transaction memo if checkbox is enabled
                if post_to_transaction:
                    # Query invoice to get current edit_sequence
                    query_result = qb.execute_operation('query_invoice', {'txn_id': invoice.txn_id})
                    if query_result.get('success') and query_result.get('data', {}).get('invoices'):
                        qb_invoice = query_result['data']['invoices'][0]
                        edit_seq = qb_invoice.get('edit_sequence')

                        if edit_seq:
                            mod_result = qb.execute_operation('modify_invoice', {
                                'invoice_mod_data': {
                                    'txn_id': invoice.txn_id,
                                    'edit_sequence': edit_seq,
                                    'memo': memo
                                }
                            })
                            if mod_result.get('success'):
                                app.root.after(0, lambda ref=invoice.ref_number, m=memo:
                                    app._log_monitor(f"  [DEV] Updated txn memo for {ref}: {m}"))
                            else:
                                app.root.after(0, lambda ref=invoice.ref_number, err=mod_result.get('error'):
                                    app._log_monitor(f"  [DEV] Warning: txn memo update failed for {ref}: {err}"))
                        else:
                            app.root.after(0, lambda ref=invoice.ref_number:
                                app._log_monitor(f"  [DEV] Warning: no edit_sequence for {ref}"))
                    else:
                        app.root.after(0, lambda ref=invoice.ref_number:
                            app._log_monitor(f"  [DEV] Warning: could not query {ref} for memo update"))

                # Step 2: Create payment
                payment_data = {
                    'customer_ref': customer_id,
                    'txn_date': datetime.now().strftime('%Y-%m-%d'),
                    'applied_to_txn': [{
                        'txn_id': invoice.txn_id,
                        'payment_amount': payment_amount
                    }]
                }

                # Only set payment memo if checkbox is enabled
                if post_to_payment:
                    payment_data['memo'] = memo

                if deposit_account_id:
                    payment_data['deposit_to_account_ref'] = deposit_account_id

                result = qb.execute_operation('receive_payment', {'payment_data': payment_data})

                if result.get('success'):
                    pmt_memo_msg = f" (pmt memo set)" if post_to_payment else ""
                    app.root.after(0, lambda ref=invoice.ref_number, amt=payment_amount, pmm=pmt_memo_msg:
                        app._log_monitor(f"  [DEV] Paid {ref}: ${amt:.2f}{pmm}"))
                    success_count += 1
                else:
                    error_msg = result.get('error', 'Unknown error')
                    app.root.after(0, lambda ref=invoice.ref_number, err=error_msg:
                        app._log_monitor(f"  [DEV] Failed {ref}: {err}"))
                    error_count += 1

            except Exception as e:
                app.root.after(0, lambda ref=invoice.ref_number, err=str(e):
                    app._log_monitor(f"  [DEV] Error {ref}: {err}"))
                error_count += 1

        # Process statement charges
        for charge in open_charges:
            try:
                # Find customer ListID
                customer_id = _find_customer_id(state.customers, charge.customer_name)
                if not customer_id:
                    app.root.after(0, lambda ref=charge.ref_number:
                        app._log_monitor(f"  [DEV] Skip {ref}: customer not found"))
                    error_count += 1
                    continue

                # Calculate payment amount (round to 2 decimals for QBFC)
                payment_amount = round(charge.amount * pay_percentage, 2)

                # Generate memo (simulates what external tool posts back)
                memo = f"Paid {datetime.now().strftime('%Y-%m-%d %H:%M')} - {charge.ref_number}"

                # Note: Statement charges don't have a memo field - the memo goes on the payment only
                if post_to_transaction:
                    app.root.after(0, lambda ref=charge.ref_number:
                        app._log_monitor(f"  [DEV] Skipping txn memo for {ref} (charges use payment memo only)"))

                # Create payment
                payment_data = {
                    'customer_ref': customer_id,
                    'txn_date': datetime.now().strftime('%Y-%m-%d'),
                    'applied_to_txn': [{
                        'txn_id': charge.txn_id,
                        'payment_amount': payment_amount
                    }]
                }

                # Only set payment memo if checkbox is enabled
                if post_to_payment:
                    payment_data['memo'] = memo

                if deposit_account_id:
                    payment_data['deposit_to_account_ref'] = deposit_account_id

                result = qb.execute_operation('receive_payment', {'payment_data': payment_data})

                if result.get('success'):
                    pmt_memo_msg = f" (pmt memo set)" if post_to_payment else ""
                    app.root.after(0, lambda ref=charge.ref_number, amt=payment_amount, pmm=pmt_memo_msg:
                        app._log_monitor(f"  [DEV] Paid {ref}: ${amt:.2f}{pmm}"))
                    success_count += 1
                else:
                    error_msg = result.get('error', 'Unknown error')
                    app.root.after(0, lambda ref=charge.ref_number, err=error_msg:
                        app._log_monitor(f"  [DEV] Failed {ref}: {err}"))
                    error_count += 1

            except Exception as e:
                app.root.after(0, lambda ref=charge.ref_number, err=str(e):
                    app._log_monitor(f"  [DEV] Error {ref}: {err}"))
                error_count += 1

        # Process sales receipts (already paid - update memo and/or payment method)
        for receipt in selected_receipts:
            try:
                # Generate memo (simulates what external tool posts back)
                memo = f"Paid {datetime.now().strftime('%Y-%m-%d %H:%M')} - {receipt.ref_number}"

                # Query sales receipt to get current edit_sequence and payment method status
                query_result = qb.execute_operation('query_sales_receipt', {'txn_id': receipt.txn_id})
                if query_result.get('success') and query_result.get('data', {}).get('sales_receipts'):
                    qb_receipt = query_result['data']['sales_receipts'][0]
                    edit_seq = qb_receipt.get('edit_sequence')
                    current_payment_method = qb_receipt.get('payment_method', {}).get('full_name')

                    if edit_seq:
                        # Build modification data
                        mod_data = {
                            'txn_id': receipt.txn_id,
                            'edit_sequence': edit_seq
                        }

                        # Add memo if checkbox is enabled
                        if post_to_transaction:
                            mod_data['memo'] = memo

                        # Set payment method if not already set (simulates card payment)
                        if not current_payment_method:
                            mod_data['payment_method_ref'] = 'Visa'

                        # Only modify if we have something to change
                        if 'memo' in mod_data or 'payment_method_ref' in mod_data:
                            mod_result = qb.execute_operation('modify_sales_receipt', {
                                'sales_receipt_mod_data': mod_data
                            })
                            if mod_result.get('success'):
                                changes = []
                                if 'memo' in mod_data:
                                    changes.append(f"memo")
                                if 'payment_method_ref' in mod_data:
                                    changes.append(f"payment=Visa")
                                app.root.after(0, lambda ref=receipt.ref_number, c=', '.join(changes):
                                    app._log_monitor(f"  [DEV] Updated sales receipt {ref}: {c}"))
                                success_count += 1
                            else:
                                app.root.after(0, lambda ref=receipt.ref_number, err=mod_result.get('error'):
                                    app._log_monitor(f"  [DEV] Warning: sales receipt update failed for {ref}: {err}"))
                                error_count += 1
                        else:
                            # Nothing to change
                            app.root.after(0, lambda ref=receipt.ref_number, pm=current_payment_method:
                                app._log_monitor(f"  [DEV] Sales receipt {ref}: already has payment method ({pm})"))
                            success_count += 1
                    else:
                        app.root.after(0, lambda ref=receipt.ref_number:
                            app._log_monitor(f"  [DEV] Warning: no edit_sequence for {ref}"))
                        error_count += 1
                else:
                    app.root.after(0, lambda ref=receipt.ref_number:
                        app._log_monitor(f"  [DEV] Warning: could not query {ref}"))
                    error_count += 1

            except Exception as e:
                app.root.after(0, lambda ref=receipt.ref_number, err=str(e):
                    app._log_monitor(f"  [DEV] Error {ref}: {err}"))
                error_count += 1

        # Summary
        app.root.after(0, lambda s=success_count, e=error_count:
            app._log_monitor(f"[DEV] Payment complete: {s} success, {e} errors"))

    thread = threading.Thread(target=payment_worker, daemon=True)
    thread.start()


def _find_customer_id(customers: list, customer_name: str) -> str:
    """Find customer ListID by name (full_name or name)."""
    for customer in customers:
        if customer.get('full_name') == customer_name or customer.get('name') == customer_name:
            return customer.get('list_id')
    return None
