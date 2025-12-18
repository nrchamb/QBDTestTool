"""
QuickBooks Connection Manager Process

Runs as a separate process to manage QuickBooks connections.
Provides isolation so that main app crashes don't orphan QB connections.
Monitors main app health via heartbeat and exits gracefully if main app dies.
"""

import time
import pythoncom
from multiprocessing import Queue
from typing import Optional, Dict, Any
from datetime import datetime
from .qbfc_connection import QBFCConnection
from .qbfc_operations import QBFCOperations, QBXMLRP2Fallback, _is_encoding_error
from .qbfc_response_mapper import QBFCResponseMapper


class QBConnectionManager:
    """Connection manager that runs in separate process."""

    def __init__(self, request_queue: Queue, response_queue: Queue):
        """
        Initialize connection manager.

        Args:
            request_queue: Queue to receive requests from main app
            response_queue: Queue to send responses to main app
        """
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.running = True
        self.last_heartbeat = time.time()
        self.heartbeat_timeout = 15.0  # Exit if no heartbeat for 15 seconds
        self.qb_connection = None
        self.connection_active = False  # Track if QB connection is currently active
        self.last_request_time = None  # Track last request for idle timeout
        self.idle_timeout = 30.0  # Disconnect after 30 seconds of inactivity

    def run(self):
        """Main event loop for connection manager."""
        # Initialize COM for this process
        pythoncom.CoInitialize()

        try:
            print("[QB Manager] Connection manager started")
            self.last_heartbeat = time.time()

            while self.running:
                # Check for requests with timeout
                try:
                    # Wait for request with 1 second timeout to check heartbeat
                    if not self.request_queue.empty():
                        message = self.request_queue.get(timeout=1.0)
                        self._handle_message(message)
                    else:
                        # No message, just check heartbeat and idle timeout
                        time.sleep(0.1)

                    # Check if main app is still alive
                    if time.time() - self.last_heartbeat > self.heartbeat_timeout:
                        print("[QB Manager] No heartbeat detected, main app appears dead")
                        print("[QB Manager] Initiating graceful shutdown...")
                        self.running = False
                        break

                    # Check for idle timeout - disconnect if no requests for idle_timeout seconds
                    if self.qb_connection and self.last_request_time:
                        idle_time = time.time() - self.last_request_time
                        if idle_time > self.idle_timeout:
                            print(f"[QB Manager] Idle timeout ({idle_time:.1f}s) - disconnecting from QuickBooks")
                            try:
                                self.qb_connection.disconnect()
                                self.connection_active = False
                                self.qb_connection = None
                                self.last_request_time = None
                                print("[QB Manager] Disconnected due to inactivity")
                            except Exception as e:
                                print(f"[QB Manager] Error during idle disconnect: {e}")

                except Exception as e:
                    print(f"[QB Manager] Error in main loop: {e}")
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("[QB Manager] Received interrupt signal")
        finally:
            self._cleanup()
            pythoncom.CoUninitialize()
            print("[QB Manager] Connection manager stopped")

    def _handle_message(self, message: Dict[str, Any]):
        """
        Handle incoming message from main app.

        Args:
            message: Message dict with type and data
        """
        match message.get('type'):
            case 'heartbeat':
                # Update last heartbeat timestamp
                self.last_heartbeat = time.time()

            case 'shutdown':
                # Graceful shutdown requested
                print("[QB Manager] Shutdown requested by main app")
                self.running = False

            case 'disconnect':
                # Explicit disconnect request
                if self.qb_connection:
                    print("[QB Manager] Explicit disconnect requested")
                    try:
                        self.qb_connection.disconnect()
                        self.connection_active = False
                        self.qb_connection = None
                        self.last_request_time = None
                        print("[QB Manager] Disconnected successfully")
                    except Exception as e:
                        print(f"[QB Manager] Error during disconnect: {e}")

            case 'request':
                # QB request to execute
                self._handle_request(message)

            case unknown:
                print(f"[QB Manager] Unknown message type: {unknown}")

    def _handle_request(self, message: Dict[str, Any]):
        """
        Handle QuickBooks request using persistent QBFC connection.

        Args:
            message: Request message with request_id, operation, params, company_file
        """
        request_id = message.get('request_id')
        operation = message.get('operation')
        params = message.get('params', {})
        company_file = message.get('company_file')

        response = {
            'request_id': request_id,
            'success': False,
            'response': None,
            'error': None
        }

        try:
            # Create persistent connection if it doesn't exist
            if not self.qb_connection:
                print(f"[QB Manager] Creating new QBFC connection")
                self.qb_connection = QBFCConnection()
                self.qb_connection.connect(company_file)
                self.connection_active = True

            # Update last request time for idle timeout tracking
            self.last_request_time = time.time()

            # Get session manager
            session_manager = self.qb_connection.get_session_manager()

            # Execute operation based on type
            match operation:
                case 'add_customer':
                    response_set = QBFCOperations.add_customer(session_manager, params['customer_data'])
                case 'add_invoice':
                    response_set = QBFCOperations.add_invoice(session_manager, params['invoice_data'])
                case 'query_invoice':
                    response_set = QBFCOperations.query_invoice(session_manager, **params)
                case 'modify_invoice':
                    response_set = QBFCOperations.modify_invoice(session_manager, params['invoice_mod_data'])
                case 'add_sales_receipt':
                    response_set = QBFCOperations.add_sales_receipt(session_manager, params['sales_receipt_data'])
                case 'query_sales_receipt':
                    response_set = QBFCOperations.query_sales_receipt(session_manager, **params)
                case 'add_charge':
                    response_set = QBFCOperations.add_charge(session_manager, params['charge_data'])
                case 'query_charge':
                    response_set = QBFCOperations.query_charge(session_manager)
                case 'modify_charge':
                    response_set = QBFCOperations.modify_charge(session_manager, params['charge_mod_data'])
                case 'query_account':
                    response_set = QBFCOperations.query_account(session_manager, params.get('account_type'))
                case 'query_customer':
                    try:
                        response_set = QBFCOperations.query_customer(session_manager)
                    except Exception as qbfc_error:
                        if _is_encoding_error(qbfc_error):
                            # Fallback to QBXMLRP2 with sanitization for encoding issues
                            print(f"[QB Manager] QBFC encoding error, using QBXMLRP2 fallback")
                            fallback_response = QBXMLRP2Fallback.query_customers_raw()
                            response['success'] = True
                            response['response'] = fallback_response
                            self.response_queue.put(response, timeout=5.0)
                            return
                        raise
                case 'query_item':
                    response_set = QBFCOperations.query_item(session_manager, params.get('item_type'))
                case 'query_terms':
                    response_set = QBFCOperations.query_terms(session_manager)
                case 'query_class':
                    response_set = QBFCOperations.query_class(session_manager)
                case 'delete_transaction':
                    response_set = QBFCOperations.delete_transaction(session_manager, params['txn_del_type'], params['txn_id'])
                case 'receive_payment':
                    response_set = QBFCOperations.receive_payment(session_manager, params['payment_data'])
                case 'query_receive_payment':
                    response_set = QBFCOperations.query_receive_payment(session_manager, params.get('txn_id'))
                case 'modify_sales_receipt':
                    response_set = QBFCOperations.modify_sales_receipt(session_manager, params['sales_receipt_mod_data'])
                # Batch query operations
                case 'query_invoices_batch':
                    response_set = QBFCOperations.query_invoices_batch(session_manager, params['txn_ids'])
                case 'query_sales_receipts_batch':
                    response_set = QBFCOperations.query_sales_receipts_batch(session_manager, params['txn_ids'])
                case 'query_receive_payments_batch':
                    response_set = QBFCOperations.query_receive_payments_batch(session_manager, params['txn_ids'])
                # Batch add operations
                case 'add_invoices_batch':
                    response_set = QBFCOperations.add_invoices_batch(session_manager, params['invoice_data_list'])
                case 'add_sales_receipts_batch':
                    response_set = QBFCOperations.add_sales_receipts_batch(session_manager, params['sales_receipt_data_list'])
                case 'add_charges_batch':
                    response_set = QBFCOperations.add_charges_batch(session_manager, params['charge_data_list'])
                case _:
                    raise Exception(f"Unknown operation: {operation}")

            # Map QBFC response to dict
            qb_response = QBFCResponseMapper.map_response(response_set)

            # Special handling for query_charge: filter by txn_id in Python
            # (ChargeQuery doesn't support TxnID filtering in QBFC)
            if operation == 'query_charge' and 'txn_id' in params and params['txn_id']:
                target_txn_id = params['txn_id']
                if qb_response.get('success') and 'charges' in qb_response.get('data', {}):
                    charges = qb_response['data']['charges']
                    filtered = [c for c in charges if c.get('txn_id') == target_txn_id]
                    # Keep the same structure but with only the filtered results
                    qb_response['data']['charges'] = filtered

            response['success'] = True
            response['response'] = qb_response

        except Exception as e:
            response['success'] = False
            response['error'] = str(e)
            print(f"[QB Manager] Error executing request {request_id}: {e}")

            # On error, disconnect and cleanup connection for next request
            if self.qb_connection:
                try:
                    self.qb_connection.disconnect()
                except:
                    pass
                self.qb_connection = None
                self.connection_active = False

        # Send response back to main app
        try:
            self.response_queue.put(response, timeout=5.0)
        except Exception as e:
            print(f"[QB Manager] Error sending response: {e}")

    def _cleanup(self):
        """Clean up resources before exit."""
        print("[QB Manager] Cleaning up resources...")

        # Close persistent QB connection
        if self.qb_connection:
            try:
                print("[QB Manager] Disconnecting from QuickBooks...")
                self.qb_connection.disconnect()
                self.connection_active = False
                self.qb_connection = None
                print("[QB Manager] Disconnected successfully")
            except Exception as e:
                print(f"[QB Manager] Error disconnecting: {e}")

        print("[QB Manager] Cleanup complete")


def run_connection_manager(request_queue: Queue, response_queue: Queue):
    """
    Entry point for connection manager process.

    Args:
        request_queue: Queue to receive requests
        response_queue: Queue to send responses
    """
    manager = QBConnectionManager(request_queue, response_queue)
    manager.run()


if __name__ == '__main__':
    # For testing purposes only
    print("Connection manager should not be run directly")
    print("It will be started by the main application")
