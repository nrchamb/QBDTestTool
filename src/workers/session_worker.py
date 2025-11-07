"""
Session worker for QuickBooks Desktop Test Tool.

Background worker for session save/load/clear operations.
"""

from tkinter import messagebox
from persistence import SessionManager
from app_logging import LOG_NORMAL


def save_session_worker(app, silent=False):
    """
    Background worker to save current session.

    Args:
        app: Reference to the main QBDTestToolApp instance
        silent: If True, suppress log messages and error dialogs (for auto-save)
    """
    try:
        if not silent:
            app.root.after(0, lambda: app._log_create("Saving session..."))

        # Get current state
        state = app.store.get_state()

        # Save to JSON
        success = SessionManager.save_session(state)

        if success:
            # Get session info for status message
            info = SessionManager.get_session_info()
            if info:
                count = info['total_items']
                if not silent:
                    app.root.after(0, lambda: app._log_create(f"✓ Session saved: {count} items"))
                app.root.after(0, lambda: update_session_status(
                    app, f"Session saved ({count} items) - {info['last_saved'][:19]}"
                ))
            else:
                if not silent:
                    app.root.after(0, lambda: app._log_create("✓ Session saved"))
                app.root.after(0, lambda: update_session_status(app, "Session saved"))
        else:
            if not silent:
                app.root.after(0, lambda: app._log_create("✗ Failed to save session"))
                app.root.after(0, lambda: update_session_status(app, "Failed to save session"))
                app.root.after(0, lambda: messagebox.showerror("Save Failed", "Could not save session to file"))

    except Exception as e:
        error_str = str(e)
        if not silent:
            app.root.after(0, lambda: app._log_create(f"✗ Error saving session: {error_str}"))
            app.root.after(0, lambda: update_session_status(app, f"Error: {error_str}"))
            app.root.after(0, lambda: messagebox.showerror("Save Error", error_str))


def load_session_worker(app, verify_changes=False):
    """
    Background worker to load previous session.

    Args:
        app: Reference to the main QBDTestToolApp instance
        verify_changes: Whether to verify transactions against QB (future feature)
    """
    try:
        app.root.after(0, lambda: app._log_create("Loading session..."))

        # Load session data
        session_data = SessionManager.load_session()

        if not session_data:
            app.root.after(0, lambda: app._log_create("✗ No session found"))
            app.root.after(0, lambda: update_session_status(app, "No session found"))
            app.root.after(0, lambda: messagebox.showinfo("No Session", "No previous session data found"))
            return

        # Restore customers
        customers = session_data.get('customers', [])
        for customer_data in customers:
            # Add 'created_by_app' flag if not present
            if 'created_by_app' not in customer_data:
                customer_data['created_by_app'] = True
            app.store.dispatch({'type': 'ADD_CUSTOMER', 'payload': customer_data})

        # Restore invoices
        from store.state import InvoiceRecord
        from datetime import datetime

        invoices = session_data.get('invoices', [])
        for inv_data in invoices:
            invoice = InvoiceRecord(
                txn_id=inv_data['txn_id'],
                ref_number=inv_data['ref_number'],
                customer_name=inv_data['customer_name'],
                amount=inv_data['amount'],
                status=inv_data.get('status', 'open'),
                created_at=datetime.fromisoformat(inv_data['created_at']) if inv_data.get('created_at') else datetime.now(),
                edit_sequence=inv_data.get('edit_sequence'),
                time_modified=inv_data.get('time_modified'),
                initial_memo=inv_data.get('initial_memo'),
                deposit_account=inv_data.get('deposit_account'),
                payment_info=inv_data.get('payment_info', {})
            )
            app.store.dispatch({'type': 'ADD_INVOICE', 'payload': invoice})

        # Restore sales receipts
        from store.state import SalesReceiptRecord

        sales_receipts = session_data.get('sales_receipts', [])
        for sr_data in sales_receipts:
            sales_receipt = SalesReceiptRecord(
                txn_id=sr_data['txn_id'],
                ref_number=sr_data['ref_number'],
                customer_name=sr_data['customer_name'],
                amount=sr_data['amount'],
                status=sr_data.get('status', 'open'),
                created_at=datetime.fromisoformat(sr_data['created_at']) if sr_data.get('created_at') else datetime.now(),
                edit_sequence=sr_data.get('edit_sequence'),
                time_modified=sr_data.get('time_modified'),
                initial_memo=sr_data.get('initial_memo'),
                deposit_account=sr_data.get('deposit_account'),
                payment_info=sr_data.get('payment_info', {})
            )
            app.store.dispatch({'type': 'ADD_SALES_RECEIPT', 'payload': sales_receipt})

        # Restore statement charges
        from store.state import StatementChargeRecord

        statement_charges = session_data.get('statement_charges', [])
        for sc_data in statement_charges:
            statement_charge = StatementChargeRecord(
                txn_id=sc_data['txn_id'],
                ref_number=sc_data['ref_number'],
                customer_name=sc_data['customer_name'],
                amount=sc_data['amount'],
                status=sc_data.get('status', 'completed'),
                created_at=datetime.fromisoformat(sc_data['created_at']) if sc_data.get('created_at') else datetime.now(),
                edit_sequence=sc_data.get('edit_sequence'),
                time_modified=sc_data.get('time_modified')
            )
            app.store.dispatch({'type': 'ADD_STATEMENT_CHARGE', 'payload': statement_charge})

        # Update UI
        app.root.after(0, app._update_customer_combo)

        # Calculate total count
        total_count = len(customers) + len(invoices) + len(sales_receipts) + len(statement_charges)

        app.root.after(0, lambda: app._log_create(f"✓ Session loaded: {total_count} items ({len(customers)} customers, {len(invoices)} invoices, {len(sales_receipts)} sales receipts, {len(statement_charges)} statement charges)"))
        app.root.after(0, lambda: update_session_status(app, f"Session loaded ({total_count} items)"))

        # Verify changes if requested
        if verify_changes:
            app.root.after(0, lambda: app._log_create("Verifying transactions against QuickBooks..."))

            from persistence import ChangeDetector
            state = app.store.get_state()
            verification_results = ChangeDetector.verify_all_transactions(state)

            # Store results in state for display
            app.store.dispatch({
                'type': 'SET_VERIFICATION_RESULTS',
                'payload': verification_results
            })

            # Log summary
            summary = verification_results['summary']
            app.root.after(0, lambda: app._log_create(
                f"✓ Verification complete: {summary['total_verified']} verified, "
                f"{summary['total_changed']} changed, {summary['total_deleted']} deleted, "
                f"{summary['total_errors']} errors"
            ))

            # Show changes in activity log
            all_changes = (verification_results['invoices'] +
                          verification_results['sales_receipts'] +
                          verification_results['statement_charges'])

            for change in all_changes:
                if change['change_type'] == 'modified':
                    details_str = '; '.join(change['details']) if isinstance(change['details'], list) else change['details']
                    app.root.after(0, lambda ref=change['ref_number'], details=details_str:
                                  app._log_create(f"  ⚠ {ref}: {details}", LOG_NORMAL))
                elif change['change_type'] == 'deleted':
                    app.root.after(0, lambda ref=change['ref_number'], details=change['details']:
                                  app._log_create(f"  ✗ {ref}: {details}", LOG_NORMAL))
                elif change['change_type'] == 'error':
                    app.root.after(0, lambda ref=change['ref_number'], details=change['details']:
                                  app._log_create(f"  ✗ {ref}: {details}", LOG_NORMAL))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error loading session: {error_str}"))
        app.root.after(0, lambda: update_session_status(app, f"Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Load Error", error_str))


def clear_session_worker(app):
    """
    Background worker to clear session data.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        # Confirm with user first
        confirm = messagebox.askyesno(
            "Clear Session",
            "This will permanently delete the saved session file.\n\nAre you sure?",
            icon='warning'
        )

        if not confirm:
            return

        app.root.after(0, lambda: app._log_create("Clearing session..."))

        # Clear session file
        success = SessionManager.clear_session()

        if success:
            app.root.after(0, lambda: app._log_create("✓ Session cleared"))
            app.root.after(0, lambda: update_session_status(app, "No session"))
        else:
            app.root.after(0, lambda: app._log_create("✗ Failed to clear session"))
            app.root.after(0, lambda: update_session_status(app, "Failed to clear session"))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error clearing session: {error_str}"))
        app.root.after(0, lambda: update_session_status(app, f"Error: {error_str}"))


def update_session_status(app, message: str):
    """
    Update session status label in UI.

    Args:
        app: Reference to the main QBDTestToolApp instance
        message: Status message to display
    """
    if hasattr(app, 'session_status_label'):
        app.session_status_label.config(text=message)


def verify_session_worker(app):
    """
    Background worker to verify session transactions against QuickBooks.

    This function only performs verification - it does not load session data.
    Session must already be loaded before calling this function.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        app.root.after(0, lambda: app._log_create("Verifying session transactions against QuickBooks..."))

        # Get current state from store
        state = app.store.get_state()

        # Count total transactions
        total_transactions = len(state.invoices) + len(state.sales_receipts) + len(state.statement_charges)

        if total_transactions == 0:
            app.root.after(0, lambda: app._log_create("No transactions to verify"))
            return

        # Verify all transactions
        from persistence import ChangeDetector
        verification_results = ChangeDetector.verify_all_transactions(state)

        # Check for connection error
        if 'error' in verification_results:
            error_msg = verification_results.get('message', 'Unknown error')
            app.root.after(0, lambda: app._log_create(f"✗ Verification failed: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Verification Failed", error_msg))
            return

        # Store results in state for Verification Results tab
        app.store.dispatch({
            'type': 'SET_VERIFICATION_RESULTS',
            'payload': verification_results
        })

        # Log summary
        summary = verification_results['summary']
        total_changed = summary['total_changed']
        total_deleted = summary['total_deleted']
        total_unchanged = summary['total_verified'] - total_changed - total_deleted

        app.root.after(0, lambda: app._log_create(
            f"✓ Verification complete: {total_unchanged} unchanged, "
            f"{total_changed} modified, {total_deleted} deleted"
        ))

        # Log individual changes if any
        if total_changed > 0 or total_deleted > 0:
            all_changes = (
                verification_results['invoices'] +
                verification_results['sales_receipts'] +
                verification_results['statement_charges']
            )

            for change in all_changes:
                if change['change_type'] in ['modified', 'deleted']:
                    txn_type = change['type'].replace('_', ' ').title()
                    ref_num = change.get('ref_number', 'Unknown')
                    change_type = change['change_type'].title()

                    changes_list = []
                    if 'changes' in change:
                        for key, value in change['changes'].items():
                            changes_list.append(f"{key}: {value['old']} → {value['new']}")

                    change_details = '; '.join(changes_list) if changes_list else ''
                    msg = f"  • {txn_type} #{ref_num}: {change_type}"
                    if change_details:
                        msg += f" ({change_details})"

                    app.root.after(0, lambda m=msg: app._log_create(m))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error during verification: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Verification Error", error_str))
    finally:
        # Disconnect from QuickBooks after verification completes
        from qb import disconnect_qb
        disconnect_qb()
