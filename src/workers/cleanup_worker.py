"""
Cleanup worker for QuickBooks Desktop Test Tool.

Background workers for archiving, deleting, and removing transactions.
"""

from tkinter import messagebox
from qb import QBIPCClient, disconnect_qb, QBXMLBuilder, QBXMLParser
from store.actions import archive_closed_transactions, archive_all_transactions, remove_all_archived
from app_logging import LOG_NORMAL


def archive_closed_worker(app):
    """
    Background worker to mark closed/paid transactions as archived.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        app.root.after(0, lambda: app._log_create("Checking for closed transactions..."))

        # Get current state
        state = app.store.get_state()

        # Count what will be archived
        closed_invoices = [inv for inv in state.invoices if inv.status == 'closed' and not inv.archived]
        closed_receipts = [sr for sr in state.sales_receipts if sr.status == 'closed' and not sr.archived]
        # Statement charges are always completed
        unarchived_charges = [sc for sc in state.statement_charges if not sc.archived]

        total = len(closed_invoices) + len(closed_receipts) + len(unarchived_charges)

        if total == 0:
            app.root.after(0, lambda: app._log_create("No closed transactions to archive"))
            app.root.after(0, lambda: messagebox.showinfo("Archive", "No closed transactions to archive."))
            return

        # Build confirmation message
        msg = f"Archive {total} closed/paid transactions?\n\n"
        msg += f"• {len(closed_invoices)} Invoices\n"
        msg += f"• {len(closed_receipts)} Sales Receipts\n"
        msg += f"• {len(unarchived_charges)} Statement Charges\n\n"
        msg += "This will mark them as archived but NOT delete them from QuickBooks."

        # Ask for confirmation
        if not messagebox.askyesno("Confirm Archive", msg):
            app.root.after(0, lambda: app._log_create("Archive cancelled by user"))
            return

        # Dispatch archive action
        app.store.dispatch(archive_closed_transactions())

        # Log success
        app.root.after(0, lambda: app._log_create(f"✓ Archived {total} transactions"))

        # Update archival status label
        if hasattr(app, 'archival_status_label'):
            app.root.after(0, lambda: app.archival_status_label.config(
                text=f"Archived {total} transactions",
                foreground='green'
            ))

        # Auto-save session
        app.root.after(0, lambda: app._auto_save_session())

        # Show completion message
        app.root.after(0, lambda: messagebox.showinfo("Archive Complete", f"Archived {total} transactions successfully!"))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error archiving transactions: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", f"Failed to archive transactions: {error_str}"))


def archive_all_worker(app):
    """
    Background worker to mark ALL transactions as archived (regardless of status).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        app.root.after(0, lambda: app._log_create("Checking for transactions..."))

        # Get current state
        state = app.store.get_state()

        # Count what will be archived (all non-archived transactions)
        unarchived_invoices = [inv for inv in state.invoices if not inv.archived]
        unarchived_receipts = [sr for sr in state.sales_receipts if not sr.archived]
        unarchived_charges = [sc for sc in state.statement_charges if not sc.archived]

        total = len(unarchived_invoices) + len(unarchived_receipts) + len(unarchived_charges)

        if total == 0:
            app.root.after(0, lambda: app._log_create("No transactions to archive"))
            app.root.after(0, lambda: messagebox.showinfo("Archive", "No transactions to archive."))
            return

        # Build confirmation message
        msg = f"Archive ALL {total} transactions (open and closed)?\n\n"
        msg += f"• {len(unarchived_invoices)} Invoices\n"
        msg += f"• {len(unarchived_receipts)} Sales Receipts\n"
        msg += f"• {len(unarchived_charges)} Statement Charges\n\n"
        msg += "This will mark them as archived but NOT delete them from QuickBooks.\n"
        msg += "This includes OPEN invoices and receipts!"

        # Ask for confirmation
        if not messagebox.askyesno("Confirm Archive All", msg, icon='warning'):
            app.root.after(0, lambda: app._log_create("Archive cancelled by user"))
            return

        # Dispatch archive action
        app.store.dispatch(archive_all_transactions())

        # Log success
        app.root.after(0, lambda: app._log_create(f"✓ Archived {total} transactions"))

        # Update archival status label
        if hasattr(app, 'archival_status_label'):
            app.root.after(0, lambda: app.archival_status_label.config(
                text=f"Archived {total} transactions (all)",
                foreground='green'
            ))

        # Auto-save session
        app.root.after(0, lambda: app._auto_save_session())

        # Show completion message
        app.root.after(0, lambda: messagebox.showinfo("Archive Complete", f"Archived {total} transactions successfully!"))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error archiving transactions: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", f"Failed to archive transactions: {error_str}"))


def delete_archived_from_qb_worker(app):
    """
    Background worker to permanently delete archived transactions from QuickBooks.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        state = app.store.get_state()

        # Get archived transactions
        archived_invoices = [inv for inv in state.invoices if inv.archived]
        archived_receipts = [sr for sr in state.sales_receipts if sr.archived]
        archived_charges = [sc for sc in state.statement_charges if sc.archived]

        total = len(archived_invoices) + len(archived_receipts) + len(archived_charges)

        if total == 0:
            app.root.after(0, lambda: app._log_create("No archived transactions to delete"))
            app.root.after(0, lambda: messagebox.showinfo("Delete", "No archived transactions to delete."))
            return

        # Strong warning - first confirmation
        msg = f"⚠ PERMANENT DELETION WARNING ⚠\n\n"
        msg += f"This will PERMANENTLY DELETE {total} transactions from QuickBooks:\n\n"
        msg += f"• {len(archived_invoices)} Invoices\n"
        msg += f"• {len(archived_receipts)} Sales Receipts\n"
        msg += f"• {len(archived_charges)} Statement Charges\n\n"
        msg += "This action CANNOT be undone!\n\n"
        msg += "Are you absolutely sure?"

        if not messagebox.askyesno("⚠ CONFIRM DELETION", msg, icon='warning'):
            app.root.after(0, lambda: app._log_create("Deletion cancelled by user"))
            return

        # Second confirmation
        if not messagebox.askyesno("Final Confirmation", "Last chance! Delete these transactions from QuickBooks?", icon='warning'):
            app.root.after(0, lambda: app._log_create("Deletion cancelled by user"))
            return

        app.root.after(0, lambda: app._log_create(f"Deleting {total} archived transactions from QuickBooks..."))

        # Perform deletions
        qb = QBIPCClient()
        deleted_count = 0
        failed_count = 0
        errors = []

        # Delete invoices
        for inv in archived_invoices:
            try:
                app.root.after(0, lambda ref=inv.ref_number:
                              app._log_create(f"  Deleting invoice {ref}...", LOG_NORMAL))

                request = QBXMLBuilder.build_txn_del('Invoice', inv.txn_id)
                response_xml = qb.execute_request(request)
                result = QBXMLParser.parse_response(response_xml)

                if result['success']:
                    deleted_count += 1
                    app.root.after(0, lambda ref=inv.ref_number:
                                  app._log_create(f"  ✓ Deleted invoice {ref}", LOG_NORMAL))
                else:
                    failed_count += 1
                    error = result.get('error', 'Unknown error')
                    errors.append(f"Invoice {inv.ref_number}: {error}")
                    app.root.after(0, lambda ref=inv.ref_number, err=error:
                                  app._log_create(f"  ✗ Failed to delete invoice {ref}: {err}", LOG_NORMAL))

            except Exception as e:
                failed_count += 1
                error_str = str(e)
                errors.append(f"Invoice {inv.ref_number}: {error_str}")
                app.root.after(0, lambda ref=inv.ref_number, err=error_str:
                              app._log_create(f"  ✗ Error deleting invoice {ref}: {err}", LOG_NORMAL))

        # Delete sales receipts
        for sr in archived_receipts:
            try:
                app.root.after(0, lambda ref=sr.ref_number:
                              app._log_create(f"  Deleting sales receipt {ref}...", LOG_NORMAL))

                request = QBXMLBuilder.build_txn_del('SalesReceipt', sr.txn_id)
                response_xml = qb.execute_request(request)
                result = QBXMLParser.parse_response(response_xml)

                if result['success']:
                    deleted_count += 1
                    app.root.after(0, lambda ref=sr.ref_number:
                                  app._log_create(f"  ✓ Deleted sales receipt {ref}", LOG_NORMAL))
                else:
                    failed_count += 1
                    error = result.get('error', 'Unknown error')
                    errors.append(f"Sales Receipt {sr.ref_number}: {error}")
                    app.root.after(0, lambda ref=sr.ref_number, err=error:
                                  app._log_create(f"  ✗ Failed to delete sales receipt {ref}: {err}", LOG_NORMAL))

            except Exception as e:
                failed_count += 1
                error_str = str(e)
                errors.append(f"Sales Receipt {sr.ref_number}: {error_str}")
                app.root.after(0, lambda ref=sr.ref_number, err=error_str:
                              app._log_create(f"  ✗ Error deleting sales receipt {ref}: {err}", LOG_NORMAL))

        # Delete statement charges
        for sc in archived_charges:
            try:
                app.root.after(0, lambda ref=sc.ref_number:
                              app._log_create(f"  Deleting statement charge {ref}...", LOG_NORMAL))

                request = QBXMLBuilder.build_txn_del('Charge', sc.txn_id)
                response_xml = qb.execute_request(request)
                result = QBXMLParser.parse_response(response_xml)

                if result['success']:
                    deleted_count += 1
                    app.root.after(0, lambda ref=sc.ref_number:
                                  app._log_create(f"  ✓ Deleted statement charge {ref}", LOG_NORMAL))
                else:
                    failed_count += 1
                    error = result.get('error', 'Unknown error')
                    errors.append(f"Statement Charge {sc.ref_number}: {error}")
                    app.root.after(0, lambda ref=sc.ref_number, err=error:
                                  app._log_create(f"  ✗ Failed to delete statement charge {ref}: {err}", LOG_NORMAL))

            except Exception as e:
                failed_count += 1
                error_str = str(e)
                errors.append(f"Statement Charge {sc.ref_number}: {error_str}")
                app.root.after(0, lambda ref=sc.ref_number, err=error_str:
                              app._log_create(f"  ✗ Error deleting statement charge {ref}: {err}", LOG_NORMAL))

        # Show results
        result_msg = f"Deletion complete:\n\n"
        result_msg += f"✓ Successfully deleted: {deleted_count}\n"
        result_msg += f"✗ Failed: {failed_count}\n"

        if errors:
            result_msg += f"\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                result_msg += f"\n... and {len(errors) - 5} more errors"

        app.root.after(0, lambda msg=result_msg: app._log_create(f"\n{msg}"))

        # Update archival status label
        if hasattr(app, 'archival_status_label'):
            status_text = f"Deleted {deleted_count} transactions from QB"
            if failed_count > 0:
                status_text += f" ({failed_count} failed)"
            app.root.after(0, lambda txt=status_text: app.archival_status_label.config(
                text=txt,
                foreground='red' if failed_count > 0 else 'green'
            ))

        # Show message box
        if failed_count > 0:
            app.root.after(0, lambda msg=result_msg: messagebox.showwarning("Deletion Results", msg))
        else:
            app.root.after(0, lambda msg=result_msg: messagebox.showinfo("Deletion Complete", msg))

        # Now remove the successfully deleted ones from session
        if deleted_count > 0:
            app.root.after(0, lambda: app._log_create("Removing deleted transactions from session..."))
            remove_archived_worker(app)

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error deleting transactions: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", f"Failed to delete transactions: {error_str}"))
    finally:
        # Disconnect from QuickBooks after operation
        disconnect_qb()


def remove_archived_worker(app):
    """
    Background worker to remove archived transactions from local session (doesn't touch QuickBooks).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        state = app.store.get_state()

        # Count archived
        archived_invoices = sum(1 for inv in state.invoices if inv.archived)
        archived_receipts = sum(1 for sr in state.sales_receipts if sr.archived)
        archived_charges = sum(1 for sc in state.statement_charges if sc.archived)
        archived_count = archived_invoices + archived_receipts + archived_charges

        if archived_count == 0:
            app.root.after(0, lambda: app._log_create("No archived transactions in session"))
            app.root.after(0, lambda: messagebox.showinfo("Remove", "No archived transactions in session."))
            return

        # Confirm
        msg = f"Remove {archived_count} archived transactions from session?\n\n"
        msg += f"• {archived_invoices} Invoices\n"
        msg += f"• {archived_receipts} Sales Receipts\n"
        msg += f"• {archived_charges} Statement Charges\n\n"
        msg += "This will NOT delete them from QuickBooks.\n"
        msg += "You will no longer track these transactions in this session."

        if not messagebox.askyesno("Confirm Remove", msg):
            app.root.after(0, lambda: app._log_create("Remove cancelled by user"))
            return

        # Dispatch remove action
        app.store.dispatch(remove_all_archived())

        # Log success
        app.root.after(0, lambda: app._log_create(f"✓ Removed {archived_count} archived transactions from session"))

        # Update archival status label
        if hasattr(app, 'archival_status_label'):
            app.root.after(0, lambda: app.archival_status_label.config(
                text=f"Removed {archived_count} archived transactions from session",
                foreground='green'
            ))

        # Auto-save session
        app.root.after(0, lambda: app._auto_save_session())

        # Show completion message
        app.root.after(0, lambda: messagebox.showinfo("Remove Complete", f"Removed {archived_count} transactions from session!"))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error removing archived: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", f"Failed to remove archived: {error_str}"))
