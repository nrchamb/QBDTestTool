"""
Session manager for QBD Test Tool.

Handles saving and loading session data to/from JSON files.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from config import AppConfig


class SessionManager:
    """Manages session data persistence."""

    SESSION_FILE = Path.home() / ".qbd_test_tool" / "session_data.json"

    @staticmethod
    def save_session(state) -> bool:
        """
        Save current application state to session file.

        Args:
            state: Current AppState from Redux store

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure config directory exists
            AppConfig.ensure_config_dir()

            # Convert state to JSON-serializable format
            session_data = {
                'version': '1.0',
                'last_saved': datetime.now().isoformat(),
                'customers': [
                    SessionManager._serialize_customer(c)
                    for c in state.customers
                    if c.get('created_by_app', True)  # Only save app-created customers
                ],
                'invoices': [
                    SessionManager._serialize_invoice(inv)
                    for inv in state.invoices
                ],
                'sales_receipts': [
                    SessionManager._serialize_sales_receipt(sr)
                    for sr in state.sales_receipts
                ],
                'statement_charges': [
                    SessionManager._serialize_statement_charge(sc)
                    for sc in state.statement_charges
                ]
            }

            # Write to file
            with open(SessionManager.SESSION_FILE, 'w') as f:
                json.dump(session_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    @staticmethod
    def load_session() -> Optional[Dict[str, Any]]:
        """
        Load session data from file.

        Returns:
            Session data dict, or None if file doesn't exist
        """
        try:
            if not SessionManager.SESSION_FILE.exists():
                return None

            with open(SessionManager.SESSION_FILE, 'r') as f:
                session_data = json.load(f)

            return session_data

        except Exception as e:
            print(f"Error loading session: {e}")
            # Backup corrupt file
            if SessionManager.SESSION_FILE.exists():
                backup_name = f"session_data_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = SessionManager.SESSION_FILE.parent / backup_name
                SessionManager.SESSION_FILE.rename(backup_path)
                print(f"Corrupt session backed up to: {backup_path}")
            return None

    @staticmethod
    def clear_session() -> bool:
        """
        Delete session file.

        Returns:
            True if successful
        """
        try:
            if SessionManager.SESSION_FILE.exists():
                SessionManager.SESSION_FILE.unlink()
            return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False

    @staticmethod
    def session_exists() -> bool:
        """
        Check if session file exists.

        Returns:
            True if session file exists
        """
        return SessionManager.SESSION_FILE.exists()

    @staticmethod
    def get_session_info() -> Optional[Dict[str, Any]]:
        """
        Get session metadata without loading full data.

        Returns:
            Dict with 'last_saved', 'count', etc., or None if no session
        """
        try:
            if not SessionManager.session_exists():
                return None

            session_data = SessionManager.load_session()
            if not session_data:
                return None

            count = (
                len(session_data.get('customers', [])) +
                len(session_data.get('invoices', [])) +
                len(session_data.get('sales_receipts', [])) +
                len(session_data.get('statement_charges', []))
            )

            return {
                'last_saved': session_data.get('last_saved'),
                'total_items': count,
                'customers': len(session_data.get('customers', [])),
                'invoices': len(session_data.get('invoices', [])),
                'sales_receipts': len(session_data.get('sales_receipts', [])),
                'statement_charges': len(session_data.get('statement_charges', []))
            }

        except Exception as e:
            print(f"Error getting session info: {e}")
            return None

    # Serialization helpers

    @staticmethod
    def _serialize_customer(customer: Dict[str, Any]) -> Dict[str, Any]:
        """Convert customer dict to JSON-serializable format."""
        return {
            'list_id': customer.get('list_id'),
            'name': customer.get('name'),
            'full_name': customer.get('full_name'),
            'email': customer.get('email'),
            'created_by_app': customer.get('created_by_app', True),
            'created_at': customer.get('created_at').isoformat() if customer.get('created_at') else None
        }

    @staticmethod
    def _serialize_invoice(invoice) -> Dict[str, Any]:
        """Convert InvoiceRecord to JSON-serializable format."""
        return {
            'txn_id': invoice.txn_id,
            'ref_number': invoice.ref_number,
            'customer_name': invoice.customer_name,
            'amount': float(invoice.amount),
            'balance_remaining': float(invoice.amount),  # Initial balance
            'status': invoice.status,
            'initial_memo': getattr(invoice, 'initial_memo', None),
            'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
            'edit_sequence': getattr(invoice, 'edit_sequence', None),
            'time_modified': getattr(invoice, 'time_modified', None),
            'deposit_account': getattr(invoice, 'deposit_account', None),
            'payment_info': getattr(invoice, 'payment_info', {})
        }

    @staticmethod
    def _serialize_sales_receipt(sr) -> Dict[str, Any]:
        """Convert SalesReceiptRecord to JSON-serializable format."""
        return {
            'txn_id': sr.txn_id,
            'ref_number': sr.ref_number,
            'customer_name': sr.customer_name,
            'amount': float(sr.amount),
            'balance_remaining': float(getattr(sr, 'balance_remaining', 0)),
            'status': sr.status,
            'initial_memo': getattr(sr, 'initial_memo', None),
            'created_at': sr.created_at.isoformat() if sr.created_at else None,
            'edit_sequence': getattr(sr, 'edit_sequence', None),
            'time_modified': getattr(sr, 'time_modified', None),
            'deposit_account': getattr(sr, 'deposit_account', None),
            'payment_info': getattr(sr, 'payment_info', {})
        }

    @staticmethod
    def _serialize_statement_charge(sc) -> Dict[str, Any]:
        """Convert StatementChargeRecord to JSON-serializable format."""
        return {
            'txn_id': sc.txn_id,
            'ref_number': sc.ref_number,
            'customer_name': sc.customer_name,
            'amount': float(sc.amount),
            'status': sc.status,
            'created_at': sc.created_at.isoformat() if sc.created_at else None,
            'edit_sequence': getattr(sc, 'edit_sequence', None),
            'time_modified': getattr(sc, 'time_modified', None)
        }
