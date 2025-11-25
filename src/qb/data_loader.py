"""
QuickBooks data loader module.

Handles QuickBooks data loading operations with pure business logic.
Separated from UI/threading concerns for better testability and maintainability.
"""

from typing import Dict, List, Any
from .ipc_client import QBIPCClient
from .connection import QBConnectionError
from .xml_builder import QBXMLBuilder
from .xml_parser import QBXMLParser


class DataLoader:
    """
    Handles QuickBooks data loading operations.

    All methods return a standardized result dictionary:
    {
        'success': bool,
        'data': list,  # The loaded entities
        'count': int,  # Number of entities loaded
        'error': str or None,  # Error message if failed
        'request_xml': str,  # QBXML request (for debug logging)
        'response_xml': str  # QBXML response (for debug logging)
    }
    """

    @staticmethod
    def load_items() -> Dict[str, Any]:
        """
        Load items from QuickBooks.

        Returns:
            dict: Result with success status, data (list of items), count, error, and XML
        """
        try:
            # Build request
            request = QBXMLBuilder.build_item_query()

            # Execute QB call
            client = QBIPCClient()
            response_xml = client.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if not parser_result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': parser_result.get('error', 'Unknown parsing error'),
                    'request_xml': request,
                    'response_xml': response_xml
                }

            # Extract items
            items = parser_result['data'].get('items', [])

            return {
                'success': True,
                'data': items,
                'count': len(items),
                'error': None,
                'request_xml': request,
                'response_xml': response_xml
            }

        except QBConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load items: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }

    @staticmethod
    def load_terms() -> Dict[str, Any]:
        """
        Load payment terms from QuickBooks.

        Returns:
            dict: Result with success status, data (list of terms), count, error, and XML
        """
        try:
            # Build request
            request = QBXMLBuilder.build_terms_query()

            # Execute QB call
            client = QBIPCClient()
            response_xml = client.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if not parser_result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': parser_result.get('error', 'Unknown parsing error'),
                    'request_xml': request,
                    'response_xml': response_xml
                }

            # Extract terms
            terms = parser_result['data'].get('terms', [])

            return {
                'success': True,
                'data': terms,
                'count': len(terms),
                'error': None,
                'request_xml': request,
                'response_xml': response_xml
            }

        except QBConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load terms: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }

    @staticmethod
    def load_classes() -> Dict[str, Any]:
        """
        Load classes from QuickBooks.

        Returns:
            dict: Result with success status, data (list of classes), count, error, and XML
        """
        try:
            # Build request
            request = QBXMLBuilder.build_class_query()

            # Execute QB call
            client = QBIPCClient()
            response_xml = client.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if not parser_result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': parser_result.get('error', 'Unknown parsing error'),
                    'request_xml': request,
                    'response_xml': response_xml
                }

            # Extract classes
            classes = parser_result['data'].get('classes', [])

            return {
                'success': True,
                'data': classes,
                'count': len(classes),
                'error': None,
                'request_xml': request,
                'response_xml': response_xml
            }

        except QBConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load classes: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }

    @staticmethod
    def load_accounts(filter_deposit_accounts: bool = True) -> Dict[str, Any]:
        """
        Load accounts from QuickBooks.

        Args:
            filter_deposit_accounts: If True, filter to only Bank and OtherCurrentAsset types

        Returns:
            dict: Result with success status, data (list of accounts), count, error, and XML
        """
        try:
            # Build request
            request = QBXMLBuilder.build_account_query()

            # Execute QB call
            client = QBIPCClient()
            response_xml = client.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if not parser_result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': parser_result.get('error', 'Unknown parsing error'),
                    'request_xml': request,
                    'response_xml': response_xml
                }

            # Extract accounts
            accounts = parser_result['data'].get('accounts', [])

            # Filter for deposit accounts if requested
            if filter_deposit_accounts:
                accounts = [
                    acc for acc in accounts
                    if acc.get('account_type') in ['Bank', 'OtherCurrentAsset']
                ]

            return {
                'success': True,
                'data': accounts,
                'count': len(accounts),
                'error': None,
                'request_xml': request,
                'response_xml': response_xml
            }

        except QBConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load accounts: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }

    @staticmethod
    def load_customers() -> Dict[str, Any]:
        """
        Load customers from QuickBooks.

        Note: All loaded customers are marked with created_by_app = False
        to distinguish from app-created customers.

        Returns:
            dict: Result with success status, data (list of customers), count, error, and XML
        """
        try:
            # Build request
            request = QBXMLBuilder.build_customer_query()

            # Execute QB call
            client = QBIPCClient()
            response_xml = client.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if not parser_result['success']:
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': parser_result.get('error', 'Unknown parsing error'),
                    'request_xml': request,
                    'response_xml': response_xml
                }

            # Extract customers
            loaded_customers = parser_result['data'].get('customers', [])

            # Mark all loaded customers as not created by app
            for customer in loaded_customers:
                customer['created_by_app'] = False

            return {
                'success': True,
                'data': loaded_customers,
                'count': len(loaded_customers),
                'error': None,
                'request_xml': request,
                'response_xml': response_xml
            }

        except QBConnectionError as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"QuickBooks connection error: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': f"Failed to load customers: {str(e)}",
                'request_xml': '',
                'response_xml': ''
            }
