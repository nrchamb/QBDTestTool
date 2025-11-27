"""
QuickBooks data loader module.

Handles QuickBooks data loading operations with pure business logic.
Separated from UI/threading concerns for better testability and maintainability.

Now uses QBFC operations instead of QBXML.
"""

from typing import Dict, List, Any
from .ipc_client import QBIPCClient
from .qbfc_connection import QBFCConnectionError


class DataLoader:
    """
    Handles QuickBooks data loading operations using QBFC.

    All methods return a standardized result dictionary:
    {
        'success': bool,
        'data': list,  # The loaded entities
        'count': int,  # Number of entities loaded
        'error': str or None,  # Error message if failed
        'request_xml': str,  # Operation details (for debug logging)
        'response_xml': str  # Response details (for debug logging)
    }
    """

    @staticmethod
    def load_items() -> Dict[str, Any]:
        """
        Load items from QuickBooks using QBFC.

        Returns:
            dict: Result with success status, data (list of items), count, error, and operation details
        """
        try:
            # Execute QB operation
            client = QBIPCClient()
            result = client.execute_operation('query_item', {})

            if not result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': result.get('error', 'Unknown error'),
                    'debug_request': {'operation': 'query_item', 'params': {}},
                    'debug_response': result
                }

            # Extract items
            items = result['data'].get('items', [])

            # Sample first few items for debug
            sample_items = items[:3] if items else []

            return {
                'success': True,
                'data': items,
                'count': len(items),
                'error': None,
                'debug_request': {'operation': 'query_item', 'params': {}},
                'debug_response': {
                    'total_count': len(items),
                    'sample': sample_items
                }
            }

        except QBFCConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'debug_request': {'operation': 'query_item', 'params': {}},
                'debug_response': {'error': str(e), 'type': 'QBFCConnectionError'}
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load items: {str(e)}",
                'debug_request': {'operation': 'query_item', 'params': {}},
                'debug_response': {'error': str(e), 'type': type(e).__name__}
            }

    @staticmethod
    def load_terms() -> Dict[str, Any]:
        """
        Load payment terms from QuickBooks using QBFC.

        Returns:
            dict: Result with success status, data (list of terms), count, error, and operation details
        """
        try:
            # Execute QB operation
            client = QBIPCClient()
            result = client.execute_operation('query_terms', {})

            if not result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': result.get('error', 'Unknown error'),
                    'debug_request': {'operation': 'query_terms', 'params': {}},
                    'debug_response': {'error': result.get('error'), 'raw': result}
                }

            # Extract terms
            terms = result['data'].get('terms', [])

            # Sample first few terms for debug
            sample_terms = terms[:3] if terms else []

            return {
                'success': True,
                'data': terms,
                'count': len(terms),
                'error': None,
                'debug_request': {'operation': 'query_terms', 'params': {}},
                'debug_response': {
                    'total_count': len(terms),
                    'sample': sample_terms
                }
            }

        except QBFCConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'debug_request': {'operation': 'query_terms', 'params': {}},
                'debug_response': {'error': str(e), 'type': 'QBFCConnectionError'}
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load terms: {str(e)}",
                'debug_request': {'operation': 'query_terms', 'params': {}},
                'debug_response': {'error': str(e), 'type': type(e).__name__}
            }

    @staticmethod
    def load_classes() -> Dict[str, Any]:
        """
        Load classes from QuickBooks using QBFC.

        Returns:
            dict: Result with success status, data (list of classes), count, error, and operation details
        """
        try:
            # Execute QB operation
            client = QBIPCClient()
            result = client.execute_operation('query_class', {})

            if not result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': result.get('error', 'Unknown error'),
                    'debug_request': {'operation': 'query_class', 'params': {}},
                    'debug_response': {'error': result.get('error'), 'raw': result}
                }

            # Extract classes
            classes = result['data'].get('classes', [])

            # Sample first few classes for debug
            sample_classes = classes[:3] if classes else []

            return {
                'success': True,
                'data': classes,
                'count': len(classes),
                'error': None,
                'debug_request': {'operation': 'query_class', 'params': {}},
                'debug_response': {
                    'total_count': len(classes),
                    'sample': sample_classes
                }
            }

        except QBFCConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'debug_request': {'operation': 'query_class', 'params': {}},
                'debug_response': {'error': str(e), 'type': 'QBFCConnectionError'}
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load classes: {str(e)}",
                'debug_request': {'operation': 'query_class', 'params': {}},
                'debug_response': {'error': str(e), 'type': type(e).__name__}
            }

    @staticmethod
    def load_accounts(filter_deposit_accounts: bool = True) -> Dict[str, Any]:
        """
        Load accounts from QuickBooks using QBFC.

        Args:
            filter_deposit_accounts: If True, filter to only Bank and OtherCurrentAsset types

        Returns:
            dict: Result with success status, data (list of accounts), count, error, and operation details
        """
        try:
            # Execute QB operation
            client = QBIPCClient()
            result = client.execute_operation('query_account', {})

            if not result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': result.get('error', 'Unknown error'),
                    'debug_request': {'operation': 'query_account', 'params': {'filter_deposit_accounts': filter_deposit_accounts}},
                    'debug_response': {'error': result.get('error'), 'raw': result}
                }

            # Extract accounts
            accounts = result['data'].get('accounts', [])
            total_from_qb = len(accounts)

            # Collect account types for debug
            unique_types = set(acc.get('account_type', 'None') for acc in accounts) if accounts else set()

            # Filter for deposit accounts if requested
            # Also filter for active accounts only (since we removed ActiveStatus filter from QBFC)
            if filter_deposit_accounts:
                # QBFC returns account types as enum strings (e.g., "atBank", "atOtherCurrentAsset")
                # or sometimes just the name ("Bank", "OtherCurrentAsset")
                DEPOSIT_ACCOUNT_TYPES = {
                    'Bank', 'atBank',
                    'OtherCurrentAsset', 'atOtherCurrentAsset'
                }
                accounts = [
                    acc for acc in accounts
                    if acc.get('account_type') in DEPOSIT_ACCOUNT_TYPES
                    and acc.get('is_active', True)  # Default to True if not present
                ]

            # Sample first few accounts for debug
            sample_accounts = accounts[:3] if accounts else []

            return {
                'success': True,
                'data': accounts,
                'count': len(accounts),
                'error': None,
                'debug_request': {'operation': 'query_account', 'params': {'filter_deposit_accounts': filter_deposit_accounts}},
                'debug_response': {
                    'total_from_qb': total_from_qb,
                    'account_types_found': list(unique_types),
                    'after_filter': len(accounts),
                    'sample': sample_accounts
                }
            }

        except QBFCConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'debug_request': {'operation': 'query_account', 'params': {'filter_deposit_accounts': filter_deposit_accounts}},
                'debug_response': {'error': str(e), 'type': 'QBFCConnectionError'}
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load accounts: {str(e)}",
                'debug_request': {'operation': 'query_account', 'params': {'filter_deposit_accounts': filter_deposit_accounts}},
                'debug_response': {'error': str(e), 'type': type(e).__name__}
            }

    @staticmethod
    def load_customers() -> Dict[str, Any]:
        """
        Load customers from QuickBooks using QBFC.

        Note: All loaded customers are marked with created_by_app = False
        to distinguish from app-created customers.

        Returns:
            dict: Result with success status, data (list of customers), count, error, and operation details
        """
        try:
            # Execute QB operation
            client = QBIPCClient()
            result = client.execute_operation('query_customer', {})

            if not result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': result.get('error', 'Unknown error'),
                    'debug_request': {'operation': 'query_customer', 'params': {}},
                    'debug_response': {'error': result.get('error'), 'raw': result}
                }

            # Extract customers
            loaded_customers = result['data'].get('customers', [])

            # Mark all loaded customers as not created by app
            for customer in loaded_customers:
                customer['created_by_app'] = False

            # Count jobs/subjobs for debug info
            jobs_count = sum(1 for c in loaded_customers if c.get('sublevel', 0) == 1)
            subjobs_count = sum(1 for c in loaded_customers if c.get('sublevel', 0) >= 2)
            top_level_count = sum(1 for c in loaded_customers if c.get('sublevel', 0) == 0)

            # Sample first few customers for debug
            sample_customers = loaded_customers[:3] if loaded_customers else []

            return {
                'success': True,
                'data': loaded_customers,
                'count': len(loaded_customers),
                'error': None,
                'debug_request': {'operation': 'query_customer', 'params': {}},
                'debug_response': {
                    'total_count': len(loaded_customers),
                    'top_level': top_level_count,
                    'jobs': jobs_count,
                    'subjobs': subjobs_count,
                    'sample': sample_customers
                }
            }

        except QBFCConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'debug_request': {'operation': 'query_customer', 'params': {}},
                'debug_response': {'error': str(e), 'type': 'QBFCConnectionError'}
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load customers: {str(e)}",
                'debug_request': {'operation': 'query_customer', 'params': {}},
                'debug_response': {'error': str(e), 'type': type(e).__name__}
            }
