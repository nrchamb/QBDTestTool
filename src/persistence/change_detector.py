"""
Change detection system for QuickBooks Desktop Test Tool.

Compares session data with current QuickBooks state to detect changes.
"""

from typing import Dict, List, Any
from datetime import datetime
from qb import QBIPCClient, QBXMLBuilder, QBXMLParser


class ChangeDetector:
    """Detects changes to transactions in QuickBooks."""

    @staticmethod
    def verify_invoices(invoices: List[Any]) -> List[Dict[str, Any]]:
        """
        Verify a list of invoices against current QB state.

        Args:
            invoices: List of InvoiceRecord objects from session

        Returns:
            List of change records with detected differences
        """
        changes = []
        qb = QBIPCClient()

        for invoice in invoices:
            try:
                # Query invoice by TxnID
                request = QBXMLBuilder.build_invoice_query(txn_id=invoice.txn_id)
                response_xml = qb.execute_request(request)
                parser_result = QBXMLParser.parse_response(response_xml)

                if not parser_result['success']:
                    changes.append({
                        'type': 'invoice',
                        'ref_number': invoice.ref_number,
                        'txn_id': invoice.txn_id,
                        'change_type': 'deleted',
                        'details': 'Invoice not found in QuickBooks (may have been deleted)',
                        'severity': 'error'
                    })
                    continue

                # Get current invoice data
                invoices_data = parser_result['data'].get('invoices', [])
                if not invoices_data:
                    changes.append({
                        'type': 'invoice',
                        'ref_number': invoice.ref_number,
                        'txn_id': invoice.txn_id,
                        'change_type': 'deleted',
                        'details': 'Invoice not found in QuickBooks',
                        'severity': 'error'
                    })
                    continue

                current_invoice = invoices_data[0]

                # Detect changes
                detected_changes = []

                # Check EditSequence (version token)
                current_edit_seq = current_invoice.get('edit_sequence')
                if invoice.edit_sequence and current_edit_seq != invoice.edit_sequence:
                    detected_changes.append(f"EditSequence changed from '{invoice.edit_sequence}' to '{current_edit_seq}'")

                # Check TimeModified
                current_time_mod = current_invoice.get('time_modified')
                if invoice.time_modified and current_time_mod != invoice.time_modified:
                    detected_changes.append(f"TimeModified changed from '{invoice.time_modified}' to '{current_time_mod}'")

                # Check balance/payment status
                current_balance = float(current_invoice.get('balance_remaining', 0))
                original_amount = invoice.amount
                if current_balance < original_amount:
                    payment_amount = original_amount - current_balance
                    detected_changes.append(f"Payment detected: ${payment_amount:.2f} (balance: ${current_balance:.2f})")

                # Check IsPaid status
                current_is_paid = current_invoice.get('is_paid', False)
                original_status = invoice.status
                if current_is_paid and original_status == 'open':
                    detected_changes.append("Invoice marked as PAID")
                elif not current_is_paid and original_status == 'closed':
                    detected_changes.append("Invoice marked as UNPAID (reopened)")

                # Check memo changes
                current_memo = current_invoice.get('memo', '')
                if invoice.initial_memo and current_memo != invoice.initial_memo:
                    detected_changes.append(f"Memo changed from '{invoice.initial_memo}' to '{current_memo}'")

                # Check deposit account
                deposit_account_ref = current_invoice.get('deposit_to_account_ref')
                if deposit_account_ref:
                    current_deposit_account = deposit_account_ref.get('full_name', '')
                    if invoice.deposit_account and current_deposit_account != invoice.deposit_account:
                        detected_changes.append(f"Deposit account changed from '{invoice.deposit_account}' to '{current_deposit_account}'")
                    elif not invoice.deposit_account:
                        detected_changes.append(f"Deposit account set to: {current_deposit_account}")

                # Record changes if any detected
                if detected_changes:
                    changes.append({
                        'type': 'invoice',
                        'ref_number': invoice.ref_number,
                        'txn_id': invoice.txn_id,
                        'customer_name': invoice.customer_name,
                        'change_type': 'modified',
                        'details': detected_changes,
                        'severity': 'info',
                        'current_data': {
                            'balance_remaining': current_balance,
                            'is_paid': current_is_paid,
                            'edit_sequence': current_edit_seq,
                            'time_modified': current_time_mod
                        }
                    })

            except Exception as e:
                changes.append({
                    'type': 'invoice',
                    'ref_number': invoice.ref_number,
                    'txn_id': invoice.txn_id,
                    'change_type': 'error',
                    'details': f"Error verifying: {str(e)}",
                    'severity': 'error'
                })

        return changes

    @staticmethod
    def verify_sales_receipts(sales_receipts: List[Any]) -> List[Dict[str, Any]]:
        """
        Verify a list of sales receipts against current QB state.

        Args:
            sales_receipts: List of SalesReceiptRecord objects from session

        Returns:
            List of change records with detected differences
        """
        changes = []
        qb = QBIPCClient()

        for receipt in sales_receipts:
            try:
                # Query sales receipt by TxnID
                request = QBXMLBuilder.build_sales_receipt_query(txn_id=receipt.txn_id)
                response_xml = qb.execute_request(request)
                parser_result = QBXMLParser.parse_response(response_xml)

                if not parser_result['success']:
                    changes.append({
                        'type': 'sales_receipt',
                        'ref_number': receipt.ref_number,
                        'txn_id': receipt.txn_id,
                        'change_type': 'deleted',
                        'details': 'Sales receipt not found in QuickBooks (may have been deleted)',
                        'severity': 'error'
                    })
                    continue

                # Get current sales receipt data
                receipts_data = parser_result['data'].get('sales_receipts', [])
                if not receipts_data:
                    changes.append({
                        'type': 'sales_receipt',
                        'ref_number': receipt.ref_number,
                        'txn_id': receipt.txn_id,
                        'change_type': 'deleted',
                        'details': 'Sales receipt not found in QuickBooks',
                        'severity': 'error'
                    })
                    continue

                current_receipt = receipts_data[0]

                # Detect changes
                detected_changes = []

                # Check EditSequence
                current_edit_seq = current_receipt.get('edit_sequence')
                if receipt.edit_sequence and current_edit_seq != receipt.edit_sequence:
                    detected_changes.append(f"EditSequence changed from '{receipt.edit_sequence}' to '{current_edit_seq}'")

                # Check TimeModified
                current_time_mod = current_receipt.get('time_modified')
                if receipt.time_modified and current_time_mod != receipt.time_modified:
                    detected_changes.append(f"TimeModified changed from '{receipt.time_modified}' to '{current_time_mod}'")

                # Check memo changes
                current_memo = current_receipt.get('memo', '')
                if receipt.initial_memo and current_memo != receipt.initial_memo:
                    detected_changes.append(f"Memo changed from '{receipt.initial_memo}' to '{current_memo}'")

                # Check deposit account
                deposit_account_ref = current_receipt.get('deposit_to_account_ref')
                if deposit_account_ref:
                    current_deposit_account = deposit_account_ref.get('full_name', '')
                    if receipt.deposit_account and current_deposit_account != receipt.deposit_account:
                        detected_changes.append(f"Deposit account changed from '{receipt.deposit_account}' to '{current_deposit_account}'")
                    elif not receipt.deposit_account:
                        detected_changes.append(f"Deposit account set to: {current_deposit_account}")

                # Record changes if any detected
                if detected_changes:
                    changes.append({
                        'type': 'sales_receipt',
                        'ref_number': receipt.ref_number,
                        'txn_id': receipt.txn_id,
                        'customer_name': receipt.customer_name,
                        'change_type': 'modified',
                        'details': detected_changes,
                        'severity': 'info',
                        'current_data': {
                            'edit_sequence': current_edit_seq,
                            'time_modified': current_time_mod
                        }
                    })

            except Exception as e:
                changes.append({
                    'type': 'sales_receipt',
                    'ref_number': receipt.ref_number,
                    'txn_id': receipt.txn_id,
                    'change_type': 'error',
                    'details': f"Error verifying: {str(e)}",
                    'severity': 'error'
                })

        return changes

    @staticmethod
    def verify_statement_charges(statement_charges: List[Any]) -> List[Dict[str, Any]]:
        """
        Verify a list of statement charges against current QB state.

        Args:
            statement_charges: List of StatementChargeRecord objects from session

        Returns:
            List of change records with detected differences
        """
        changes = []
        qb = QBIPCClient()

        for charge in statement_charges:
            try:
                # Query statement charge by TxnID
                request = QBXMLBuilder.build_charge_query(txn_id=charge.txn_id)
                response_xml = qb.execute_request(request)
                parser_result = QBXMLParser.parse_response(response_xml)

                if not parser_result['success']:
                    changes.append({
                        'type': 'statement_charge',
                        'ref_number': charge.ref_number,
                        'txn_id': charge.txn_id,
                        'change_type': 'deleted',
                        'details': 'Statement charge not found in QuickBooks (may have been deleted)',
                        'severity': 'error'
                    })
                    continue

                # Get current statement charge data
                charges_data = parser_result['data'].get('charges', [])
                if not charges_data:
                    changes.append({
                        'type': 'statement_charge',
                        'ref_number': charge.ref_number,
                        'txn_id': charge.txn_id,
                        'change_type': 'deleted',
                        'details': 'Statement charge not found in QuickBooks',
                        'severity': 'error'
                    })
                    continue

                current_charge = charges_data[0]

                # Detect changes
                detected_changes = []

                # Check EditSequence
                current_edit_seq = current_charge.get('edit_sequence')
                if charge.edit_sequence and current_edit_seq != charge.edit_sequence:
                    detected_changes.append(f"EditSequence changed from '{charge.edit_sequence}' to '{current_edit_seq}'")

                # Check TimeModified
                current_time_mod = current_charge.get('time_modified')
                if charge.time_modified and current_time_mod != charge.time_modified:
                    detected_changes.append(f"TimeModified changed from '{charge.time_modified}' to '{current_time_mod}'")

                # Record changes if any detected
                if detected_changes:
                    changes.append({
                        'type': 'statement_charge',
                        'ref_number': charge.ref_number,
                        'txn_id': charge.txn_id,
                        'customer_name': charge.customer_name,
                        'change_type': 'modified',
                        'details': detected_changes,
                        'severity': 'info',
                        'current_data': {
                            'edit_sequence': current_edit_seq,
                            'time_modified': current_time_mod
                        }
                    })

            except Exception as e:
                changes.append({
                    'type': 'statement_charge',
                    'ref_number': charge.ref_number,
                    'txn_id': charge.txn_id,
                    'change_type': 'error',
                    'details': f"Error verifying: {str(e)}",
                    'severity': 'error'
                })

        return changes

    @staticmethod
    def verify_all_transactions(state) -> Dict[str, Any]:
        """
        Verify all transactions in the state against QuickBooks.

        Args:
            state: AppState object with invoices, sales_receipts, statement_charges

        Returns:
            Dictionary with categorized changes
        """
        results = {
            'invoices': [],
            'sales_receipts': [],
            'statement_charges': [],
            'summary': {
                'total_verified': 0,
                'total_changed': 0,
                'total_deleted': 0,
                'total_errors': 0
            }
        }

        # Verify each transaction type
        if state.invoices:
            invoice_changes = ChangeDetector.verify_invoices(state.invoices)
            results['invoices'] = invoice_changes
            results['summary']['total_verified'] += len(state.invoices)

        if state.sales_receipts:
            receipt_changes = ChangeDetector.verify_sales_receipts(state.sales_receipts)
            results['sales_receipts'] = receipt_changes
            results['summary']['total_verified'] += len(state.sales_receipts)

        if state.statement_charges:
            charge_changes = ChangeDetector.verify_statement_charges(state.statement_charges)
            results['statement_charges'] = charge_changes
            results['summary']['total_verified'] += len(state.statement_charges)

        # Calculate summary statistics
        all_changes = results['invoices'] + results['sales_receipts'] + results['statement_charges']
        for change in all_changes:
            if change['change_type'] == 'modified':
                results['summary']['total_changed'] += 1
            elif change['change_type'] == 'deleted':
                results['summary']['total_deleted'] += 1
            elif change['change_type'] == 'error':
                results['summary']['total_errors'] += 1

        return results
