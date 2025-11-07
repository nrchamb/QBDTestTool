"""
QuickBooks connection status checking.

Provides lightweight methods to check if QuickBooks is available before
attempting data operations.
"""

from typing import Tuple
from .connection import QBConnectionError


def is_quickbooks_available() -> Tuple[bool, str]:
    """
    Check if QuickBooks Desktop is available and connected.

    This performs a lightweight connection check without making data requests.
    Returns immediately with status - does not throw exceptions.

    Returns:
        Tuple of (is_available: bool, message: str)
            - is_available: True if QB is running and connected
            - message: Success message or error description
    """
    try:
        from .ipc_client import QBIPCClient
        from .xml_builder import QBXMLBuilder
        from .xml_parser import QBXMLParser

        # Build a minimal customer query request (lightweight connection check)
        # Just checks if we can communicate with QB, doesn't return data
        request_xml = QBXMLBuilder.build_customer_query()

        # Try to execute the request (IPC client handles connection automatically)
        response_xml = QBIPCClient.execute_request(request_xml)

        # Parse response to verify success
        parse_result = QBXMLParser.parse_response(response_xml)

        # If we got here and parsing succeeded, connection is working
        if parse_result and parse_result.get('success'):
            return (True, "QuickBooks Desktop is connected and ready")
        else:
            error_msg = parse_result.get('error', 'Unknown error')
            return (False, f"QuickBooks responded with error: {error_msg}")

    except QBConnectionError as e:
        # Known QB connection error
        return (False, str(e))

    except Exception as e:
        # Any other error (connection manager not started, etc.)
        return (False, f"Cannot connect to QuickBooks: {str(e)}")
