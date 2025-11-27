"""
Monitor worker for QuickBooks Desktop Test Tool.

Background worker for monitoring transactions and verifying payment posting.
"""

import time
from datetime import datetime
from qb import QBIPCClient
from qb.qbfc_connection import QBFCConnectionError
from store import (
    InvoiceRecord, SalesReceiptRecord, StatementChargeRecord,
    update_invoice, update_sales_receipt, update_statement_charge, add_verification_result
)
from app_logging import LOG_NORMAL, LOG_VERBOSE, LOG_DEBUG
from app_logging.logging_config import should_log
from config import AppConfig


def _format_query_debug(operation: str, txn_id: str, result: dict) -> str:
    """Format query operation debug info for logging."""
    if result.get('success'):
        data = result.get('data', {})
        # Count items in response
        for key in ['invoices', 'sales_receipts', 'charges']:
            if key in data and data[key]:
                item = data[key][0]
                status = 'paid' if item.get('is_paid') else 'open'
                balance = item.get('balance_remaining', item.get('amount', 'N/A'))
                return f"OK - status={status}, balance={balance}, txn_id={txn_id}"
        return f"OK - txn_id={txn_id} (no data returned)"
    else:
        return f"ERROR: {result.get('error', 'Unknown error')}"


def monitor_loop_worker(app):
    """
    Monitoring loop (runs in separate thread).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        interval = int(app.check_interval.get())

        while not app.monitoring_stop_flag:
            try:
                check_all_transactions(app)
            except Exception as e:
                app.root.after(0, lambda: app._log_monitor(f"✗ Error during check: {str(e)}"))

            # Wait for interval (check stop flag frequently)
            for _ in range(interval):
                if app.monitoring_stop_flag:
                    break
                time.sleep(1)
    finally:
        pass


def check_all_transactions(app):
    """
    Check all tracked transactions (invoices, sales receipts, charges).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    check_invoices(app)
    check_sales_receipts(app)
    check_statement_charges(app)


def check_invoices(app):
    """
    Check all tracked invoices for updates.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

    # Create QB client once for entire batch
    qb = QBIPCClient()

    for invoice in state.invoices:
        try:
            # Query invoice via QBFC
            parser_result = qb.execute_operation('query_invoice', {'txn_id': invoice.txn_id})

            # DEBUG: Log the operation (only if DEBUG is enabled)
            if should_log(LOG_DEBUG, AppConfig.get_log_level()):
                debug_str = _format_query_debug('query_invoice', invoice.txn_id, parser_result)
                app.root.after(0, lambda ref=invoice.ref_number, d=debug_str:
                              app._log_monitor(f"  [DEBUG Invoice {ref}] {d}", LOG_DEBUG))

            if parser_result['success'] and parser_result['data']['invoices']:
                qb_invoice = parser_result['data']['invoices'][0]

                # Determine status: closed, partial, or open
                balance_remaining = float(qb_invoice.get('balance_remaining', 0))
                linked_txns = qb_invoice.get('linked_transactions', [])

                if qb_invoice['is_paid'] or balance_remaining == 0:
                    new_status = 'closed'
                elif linked_txns and balance_remaining > 0 and balance_remaining < invoice.amount:
                    new_status = 'partial'
                else:
                    new_status = 'open'

                old_status = invoice.status

                if new_status != old_status:
                    app.root.after(0, lambda i=invoice, ns=new_status, os=old_status:
                                  app._log_monitor(f"Status change detected: {i.ref_number} ({os} → {ns})"))

                    # Verify transaction
                    verify_transaction(app, invoice, qb_invoice, 'Invoice')

                # Update invoice record
                updated_invoice = InvoiceRecord(
                    txn_id=invoice.txn_id,
                    ref_number=invoice.ref_number,
                    customer_name=invoice.customer_name,
                    amount=invoice.amount,
                    status=new_status,
                    created_at=invoice.created_at,
                    last_checked=datetime.now(),
                    deposit_account=qb_invoice.get('deposit_account', {}).get('full_name') if 'deposit_account' in qb_invoice else None,
                    payment_info=qb_invoice.get('linked_transactions', []),
                    balance_remaining=balance_remaining
                )

                app.store.dispatch(update_invoice(updated_invoice))
                app.root.after(0, lambda: update_invoice_tree(app))

        except Exception as e:
            app.root.after(0, lambda inv=invoice, err=str(e):
                          app._log_monitor(f"✗ Error checking {inv.ref_number}: {err}"))


def check_sales_receipts(app):
    """
    Check all tracked sales receipts for updates.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

    # Create QB client once for entire batch
    qb = QBIPCClient()

    for sr in state.sales_receipts:
        try:
            # Query sales receipt via QBFC
            parser_result = qb.execute_operation('query_sales_receipt', {'txn_id': sr.txn_id})

            # DEBUG: Log the operation (only if DEBUG is enabled)
            if should_log(LOG_DEBUG, AppConfig.get_log_level()):
                debug_str = _format_query_debug('query_sales_receipt', sr.txn_id, parser_result)
                app.root.after(0, lambda ref=sr.ref_number, d=debug_str:
                              app._log_monitor(f"  [DEBUG Receipt {ref}] {d}", LOG_DEBUG))

            if parser_result['success'] and parser_result['data']['sales_receipts']:
                qb_sr = parser_result['data']['sales_receipts'][0]

                # Sales receipts status is determined by payment method:
                # - If payment_method is set (Cash, Check, CC, etc.) -> "closed"
                # - If payment_method is NOT set -> "open"
                payment_method = qb_sr.get('payment_method')
                has_payment_method = payment_method is not None and payment_method.get('full_name')
                new_status = 'closed' if has_payment_method else 'open'
                old_status = sr.status

                if new_status != old_status:
                    app.root.after(0, lambda s=sr, ns=new_status, os=old_status:
                                  app._log_monitor(f"Status change detected: {s.ref_number} (Sales Receipt) ({os} → {ns})"))

                    # Verify transaction
                    verify_transaction(app, sr, qb_sr, 'Sales Receipt')

                # Get deposit account for record
                deposit_account = qb_sr.get('deposit_account')

                updated_sr = SalesReceiptRecord(
                    txn_id=sr.txn_id,
                    ref_number=sr.ref_number,
                    customer_name=sr.customer_name,
                    amount=sr.amount,
                    status=new_status,
                    created_at=sr.created_at,
                    last_checked=datetime.now(),
                    deposit_account=deposit_account.get('full_name') if deposit_account else None,
                    payment_info={'payment_method': payment_method.get('full_name') if payment_method else None}
                )

                app.store.dispatch(update_sales_receipt(updated_sr))
                app.root.after(0, lambda: update_invoice_tree(app))

        except Exception as e:
            app.root.after(0, lambda s=sr, err=str(e):
                          app._log_monitor(f"✗ Error checking {s.ref_number}: {err}"))


def check_statement_charges(app):
    """
    Check all tracked statement charges for updates.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

    # Create QB client once for entire batch
    qb = QBIPCClient()

    for charge in state.statement_charges:
        try:
            # Query statement charge via QBFC
            parser_result = qb.execute_operation('query_charge', {'txn_id': charge.txn_id})

            # DEBUG: Log the operation (only if DEBUG is enabled)
            if should_log(LOG_DEBUG, AppConfig.get_log_level()):
                debug_str = _format_query_debug('query_charge', charge.txn_id, parser_result)
                app.root.after(0, lambda ref=charge.ref_number, d=debug_str:
                              app._log_monitor(f"  [DEBUG Charge {ref}] {d}", LOG_DEBUG))

            if parser_result['success'] and parser_result['data']['charges']:
                qb_charge = parser_result['data']['charges'][0]

                # Determine status: closed, partial, or open
                balance_remaining = float(qb_charge.get('balance_remaining', 0))
                linked_txns = qb_charge.get('linked_transactions', [])

                if qb_charge['is_paid'] or balance_remaining == 0:
                    new_status = 'closed'
                elif linked_txns and balance_remaining > 0 and balance_remaining < charge.amount:
                    new_status = 'partial'
                else:
                    new_status = 'open'

                old_status = charge.status

                if new_status != old_status:
                    app.root.after(0, lambda c=charge, ns=new_status, os=old_status:
                                  app._log_monitor(f"Status change detected: {c.ref_number} (Statement Charge) ({os} → {ns})"))

                    # Verify transaction
                    verify_transaction(app, charge, qb_charge, 'Statement Charge')

                updated_charge = StatementChargeRecord(
                    txn_id=charge.txn_id,
                    ref_number=qb_charge.get('ref_number', charge.ref_number),
                    customer_name=charge.customer_name,
                    amount=charge.amount,
                    status=new_status,
                    created_at=charge.created_at,
                    last_checked=datetime.now(),
                    deposit_account=qb_charge.get('deposit_account', {}).get('full_name') if 'deposit_account' in qb_charge else None,
                    payment_info=qb_charge.get('linked_transactions', []),
                    balance_remaining=balance_remaining
                )

                app.store.dispatch(update_statement_charge(updated_charge))
                app.root.after(0, lambda: update_invoice_tree(app))

        except Exception as e:
            app.root.after(0, lambda c=charge, err=str(e):
                          app._log_monitor(f"✗ Error checking {c.ref_number}: {err}"))


def verify_transaction(app, transaction, qb_data: dict, txn_type: str):
    """
    Verify transaction payment posting and related fields.

    Args:
        app: Reference to the main QBDTestToolApp instance
        transaction: InvoiceRecord, SalesReceiptRecord, or StatementChargeRecord
        qb_data: QuickBooks data from query response
        txn_type: 'Invoice', 'Sales Receipt', or 'Statement Charge'
    """
    state = app.store.get_state()
    verification = {
        'timestamp': datetime.now(),
        'txn_type': txn_type,
        'txn_ref': transaction.ref_number,
        'result': 'PASS',
        'details': []
    }

    def add_detail(check: str, status: str, result: str, text: str):
        """Helper to add a detail entry."""
        verification['details'].append({
            'check': check,
            'status': status,
            'result': result,
            'text': text
        })
        # Update overall result based on individual check results
        if result == 'FAIL' and verification['result'] != 'FAIL':
            verification['result'] = 'FAIL'
        elif result == 'WARN' and verification['result'] == 'PASS':
            verification['result'] = 'WARN'

    # Get transaction total and balance
    txn_total = transaction.amount
    balance_remaining = qb_data.get('balance_remaining', 0)

    # --- Payment Transactions Check ---
    linked_txns = qb_data.get('linked_transactions', [])

    # Detect if any payment is cash (case-insensitive check)
    has_cash_payment = any(
        'payment_method' in txn and
        txn.get('payment_method', '').lower() in ['cash', 'check']
        for txn in linked_txns
    )

    if not linked_txns:
        # No payments found
        if balance_remaining == 0:
            add_detail('Payment Transactions', 'Tested', 'PASS',
                      'No linked payments (may be direct cash payment or sales receipt)')
        else:
            add_detail('Payment Transactions', 'Tested', 'FAIL',
                      f'No payment transactions found, balance: ${balance_remaining:.2f}')
    else:
        # Calculate total payment amount
        total_payment = sum(abs(float(txn.get('amount', 0))) for txn in linked_txns)
        payment_summary = f"Found {len(linked_txns)} payment(s), Total: ${total_payment:.2f}"
        if has_cash_payment:
            payment_summary += " (includes Cash/Check)"
        add_detail('Payment Transactions', 'Tested', 'PASS', payment_summary)

    # Get memo values for comparison
    txn_memo = qb_data.get('memo', '')

    # Query actual payment records to get their memos
    # (LinkedTxn objects don't include memo - just basic reference data)
    payment_memos = []
    qb = QBIPCClient()
    for payment_txn in linked_txns:
        # Only query ReceivePayment transactions
        if payment_txn.get('txn_type') == 'ReceivePayment':
            payment_txn_id = payment_txn.get('txn_id')
            if payment_txn_id:
                try:
                    result = qb.execute_operation('query_receive_payment', {'txn_id': payment_txn_id})
                    if result.get('success') and result.get('data', {}).get('payments'):
                        actual_payment = result['data']['payments'][0]
                        payment_memos.append(actual_payment.get('memo', ''))
                    else:
                        payment_memos.append('')  # Couldn't get memo
                except:
                    payment_memos.append('')  # Error querying
            else:
                payment_memos.append('')
        else:
            # For other linked transaction types, use whatever memo is available
            payment_memos.append(payment_txn.get('memo', ''))

    # --- Transaction Memo Check ---
    if app.check_transaction_memo_var.get():
        if txn_memo:
            add_detail('Transaction Memo', 'Tested', 'PASS', f"'{txn_memo}'")
        else:
            add_detail('Transaction Memo', 'Tested', 'WARN', '(empty)')
    else:
        add_detail('Transaction Memo', 'Skipped', '', 'Check disabled in settings')

    # --- Payment Memo Check ---
    if app.check_payment_memo_var.get():
        if linked_txns:
            # Show each payment memo
            for i, payment_memo in enumerate(payment_memos):
                if payment_memo:
                    add_detail(f'Payment #{i+1} Memo', 'Tested', 'PASS', f"'{payment_memo}'")
                else:
                    add_detail(f'Payment #{i+1} Memo', 'Tested', 'WARN', '(empty)')
        else:
            add_detail('Payment Memo', 'Tested', 'INFO', 'No payment transactions')
    else:
        add_detail('Payment Memo', 'Skipped', '', 'Check disabled in settings')

    # --- Memo Match Check (if both memo checks are enabled) ---
    if app.check_transaction_memo_var.get() and app.check_payment_memo_var.get() and linked_txns:
        # Verify transaction memo matches payment memo(s)
        all_match = True
        match_details = []

        for i, payment_memo in enumerate(payment_memos):
            if not payment_memo and not txn_memo:
                match_details.append(f"#{i+1}: both empty")
            elif payment_memo and txn_memo:
                # Check if transaction memo contains the payment memo (since it may be appended)
                if payment_memo in txn_memo or txn_memo == payment_memo:
                    match_details.append(f"#{i+1}: match")
                else:
                    match_details.append(f"#{i+1}: MISMATCH")
                    all_match = False
            elif payment_memo and not txn_memo:
                match_details.append(f"#{i+1}: payment has memo, txn empty")
                all_match = False
            else:
                match_details.append(f"#{i+1}: txn has memo, payment empty")
                all_match = False

        if all_match:
            add_detail('Memo Match', 'Tested', 'PASS', '; '.join(match_details))
        else:
            add_detail('Memo Match', 'Tested', 'FAIL', '; '.join(match_details))

    # --- Payment Amount Validation ---
    if linked_txns:
        total_payment = sum(abs(float(txn.get('amount', 0))) for txn in linked_txns)

        if abs(total_payment - txn_total) < 0.01:
            # Fully paid
            if balance_remaining == 0:
                add_detail('Payment Amount', 'Tested', 'PASS',
                          f'Matches total: ${txn_total:.2f}, Status: CLOSED')
            else:
                add_detail('Payment Amount', 'Tested', 'FAIL',
                          f'Matches total but balance is ${balance_remaining:.2f}')
        elif total_payment < txn_total:
            # Partial payment
            expected_balance = txn_total - total_payment
            if abs(balance_remaining - expected_balance) < 0.01:
                add_detail('Payment Amount', 'Tested', 'PASS',
                          f'Partial: ${total_payment:.2f} of ${txn_total:.2f}, Balance: ${balance_remaining:.2f}')
            else:
                add_detail('Payment Amount', 'Tested', 'FAIL',
                          f'${total_payment:.2f} paid, expected balance: ${expected_balance:.2f}, actual: ${balance_remaining:.2f}')
        else:
            # Overpayment
            add_detail('Payment Amount', 'Tested', 'WARN',
                      f'Overpayment: ${total_payment:.2f} > ${txn_total:.2f}')
    else:
        add_detail('Payment Amount', 'Tested', 'INFO', 'No payment transactions')

    # --- Deposit Account Check ---
    if 'deposit_account' in qb_data and qb_data['deposit_account']:
        actual_deposit = qb_data['deposit_account'].get('full_name', 'Unknown')
        expected_deposit = state.expected_deposit_account

        if expected_deposit:
            if actual_deposit == expected_deposit:
                add_detail('Deposit Account', 'Tested', 'PASS', f'Matches: {actual_deposit}')
            else:
                add_detail('Deposit Account', 'Tested', 'FAIL',
                          f'Expected: {expected_deposit}, Actual: {actual_deposit}')
        else:
            add_detail('Deposit Account', 'Tested', 'INFO',
                      f'{actual_deposit} (no expected account set)')
    else:
        add_detail('Deposit Account', 'Tested', 'INFO', 'No deposit account information')

    app.store.dispatch(add_verification_result(verification))
    app.root.after(0, lambda: update_verify_tree(app))


def update_invoice_tree(app):
    """
    Update invoice tree view with all transaction types.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Clear tree
    for item in app.invoice_tree.get_children():
        app.invoice_tree.delete(item)

    state = app.store.get_state()

    # Collect all transactions with type info
    all_transactions = []

    # Add invoices
    for invoice in state.invoices:
        last_checked = invoice.last_checked.strftime('%H:%M:%S') if invoice.last_checked else 'Never'
        # Show balance remaining for partial payments
        if invoice.status == 'partial' and invoice.balance_remaining is not None:
            amount_display = f"${invoice.amount:.2f} (${invoice.balance_remaining:.2f} left)"
        else:
            amount_display = f"${invoice.amount:.2f}"
        all_transactions.append({
            'type': 'Invoice',
            'ref_number': invoice.ref_number,
            'customer_name': invoice.customer_name,
            'amount': invoice.amount,
            'amount_display': amount_display,
            'status': invoice.status.upper(),
            'last_checked': last_checked,
            'created_at': invoice.created_at
        })

    # Add sales receipts (no partial payments - they're paid at creation)
    for sr in state.sales_receipts:
        last_checked = sr.last_checked.strftime('%H:%M:%S') if sr.last_checked else 'Never'
        all_transactions.append({
            'type': 'Sales Receipt',
            'ref_number': sr.ref_number,
            'customer_name': sr.customer_name,
            'amount': sr.amount,
            'amount_display': f"${sr.amount:.2f}",
            'status': sr.status.upper(),
            'last_checked': last_checked,
            'created_at': sr.created_at
        })

    # Add statement charges
    for charge in state.statement_charges:
        last_checked = charge.last_checked.strftime('%H:%M:%S') if charge.last_checked else 'Never'
        # Show balance remaining for partial payments
        if charge.status == 'partial' and charge.balance_remaining is not None:
            amount_display = f"${charge.amount:.2f} (${charge.balance_remaining:.2f} left)"
        else:
            amount_display = f"${charge.amount:.2f}"
        all_transactions.append({
            'type': 'Statement Charge',
            'ref_number': charge.ref_number,
            'customer_name': charge.customer_name,
            'amount': charge.amount,
            'amount_display': amount_display,
            'status': charge.status.upper(),
            'last_checked': last_checked,
            'created_at': charge.created_at
        })

    # Sort by created_at (most recent first)
    all_transactions.sort(key=lambda x: x['created_at'], reverse=True)

    # Insert all transactions into tree with status-based coloring
    for txn in all_transactions:
        # Determine tag based on status (OPEN/PARTIAL/CLOSED)
        status_tag = txn['status'].lower()

        app.invoice_tree.insert('', 'end', values=(
            txn['type'],
            txn['ref_number'],
            txn['customer_name'],
            txn['amount_display'],
            txn['status'],
            txn['last_checked']
        ), tags=(status_tag,))


def update_verify_tree(app):
    """
    Update verification results tree with hierarchical display.

    Parent rows: Transactions (timestamp as text, Type, Ref#, Overall Result)
    Child rows: Individual validation checks with Status column

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Clear tree
    for item in app.verify_tree.get_children():
        app.verify_tree.delete(item)

    # Add results hierarchically
    state = app.store.get_state()
    for result in state.verification_results:
        timestamp = result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        txn_type = result.get('txn_type', 'Invoice')
        txn_ref = result.get('txn_ref', result.get('invoice_ref', 'N/A'))
        overall_result = result['result']
        details = result['details']

        # Determine parent row tag based on overall result
        parent_tag = overall_result.lower() if overall_result else ''

        # Insert parent row (transaction) - Status column empty for parent
        parent_id = app.verify_tree.insert('', 'end',
            text=timestamp,
            values=(txn_type, txn_ref, '', overall_result, ''),
            open=True,  # Expand by default
            tags=(parent_tag,) if parent_tag else ()
        )

        # Insert child rows (individual checks)
        for detail in details:
            # Handle both old string format and new dict format
            if isinstance(detail, dict):
                check_name = detail.get('check', '')
                check_status = detail.get('status', '')
                check_result = detail.get('result', '')
                check_text = detail.get('text', '')
            else:
                # Legacy string format (backwards compatibility)
                check_name = ''
                check_status = 'Tested'
                if detail.startswith('✓'):
                    check_result = 'PASS'
                    check_text = detail[2:].strip()
                elif detail.startswith('✗'):
                    check_result = 'FAIL'
                    check_text = detail[2:].strip()
                elif detail.startswith('⚠'):
                    check_result = 'WARN'
                    check_text = detail[2:].strip()
                elif detail.startswith('ℹ'):
                    check_result = 'INFO'
                    check_text = detail[2:].strip()
                else:
                    check_result = ''
                    check_text = detail

            # Determine tag for row coloring
            # Priority: result > status (skipped)
            if check_status == 'Skipped':
                row_tag = 'skipped'
            elif check_result:
                row_tag = check_result.lower()
            else:
                row_tag = ''

            app.verify_tree.insert(parent_id, 'end',
                text=check_name,
                values=('', '', check_status, check_result, check_text),
                tags=(row_tag,) if row_tag else ()
            )
