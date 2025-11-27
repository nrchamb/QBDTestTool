"""
QuickBooks integration module.

Provides connection management, QBFC operations, and data loaders.
Now uses QBFC 13.0 instead of QBXML.
"""

from .qbfc_connection import QBFCConnection, QBFCConnectionError
from .ipc_client import QBIPCClient, start_manager, stop_manager, disconnect_qb
from .data_loader import DataLoader
from .qbfc_operations import QBFCOperations
from .qbfc_response_mapper import QBFCResponseMapper

__all__ = [
    'QBFCConnection',
    'QBFCConnectionError',
    'QBIPCClient',
    'start_manager',
    'stop_manager',
    'disconnect_qb',
    'DataLoader',
    'QBFCOperations',
    'QBFCResponseMapper',
]
