"""
QuickBooks connection status checking.

Provides lightweight methods to check if QuickBooks is available before
attempting data operations.

Now uses QBFC operations instead of QBXML.
"""

from typing import Tuple
from .qbfc_connection import QBFCConnectionError


def is_quickbooks_available() -> Tuple[bool, str]:
    """
    Check if QuickBooks Desktop is available and connected using QBFC.

    This performs a lightweight connection check without making data requests.
    Returns immediately with status - does not throw exceptions.

    Returns:
        Tuple of (is_available: bool, message: str)
            - is_available: True if QB is running and connected
            - message: Success message or error description
    """
    try:
        from .ipc_client import QBIPCClient

        # Execute a minimal customer query (lightweight connection check)
        # Just checks if we can communicate with QB
        result = QBIPCClient.execute_operation('query_customer', {})

        # If we got here and operation succeeded, connection is working
        if result and result.get('success'):
            return (True, "QuickBooks Desktop is connected and ready")
        else:
            error_msg = result.get('error', 'Unknown error')
            return (False, f"QuickBooks responded with error: {error_msg}")

    except QBFCConnectionError as e:
        # Known QB connection error
        return (False, str(e))

    except Exception as e:
        # Any other error (connection manager not started, etc.)
        return (False, f"Cannot connect to QuickBooks: {str(e)}")
