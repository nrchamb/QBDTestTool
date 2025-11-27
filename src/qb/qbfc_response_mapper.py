"""
QBFC 13.0 Response Mapper - Maps QBFC COM objects to Python dicts.

Replaces QBXMLParser with QBFC-based response mapping that maintains the exact same dict structure.
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

# Import pywintypes for datetime conversion
try:
    import pywintypes
    HAS_PYWINTYPES = True
except ImportError:
    HAS_PYWINTYPES = False

logger = logging.getLogger(__name__)


class QBFCResponseMapper:
    """Maps QBFC response objects to Python dicts matching QBXMLParser output."""

    @staticmethod
    def map_response(response_set):
        """
        Map QBFC response set to structured data dict.

        Args:
            response_set: QBFC ResponseMsgSet COM object

        Returns:
            Dict with 'success' (bool), 'data' (parsed content), 'error' (if failed)
        """
        try:
            # Get first response from set
            if response_set.ResponseList.Count == 0:
                return {'success': False, 'error': 'No responses in response set'}

            response = response_set.ResponseList.GetAt(0)

            # Check status code
            status_code = response.StatusCode
            if status_code != 0:
                return {
                    'success': False,
                    'error': response.StatusMessage,
                    'status_code': str(status_code)
                }

            # Get response type
            response_type = response.Type.GetAsString()

            # Map to appropriate parser based on type
            if 'CustomerAdd' in response_type:
                return QBFCResponseMapper._map_customer_add(response)
            elif 'CustomerQuery' in response_type:
                return QBFCResponseMapper._map_customer_query(response_set)
            elif 'InvoiceAdd' in response_type:
                return QBFCResponseMapper._map_invoice_add(response)
            elif 'InvoiceQuery' in response_type:
                return QBFCResponseMapper._map_invoice_query(response_set)
            elif 'InvoiceMod' in response_type:
                return QBFCResponseMapper._map_invoice_mod(response)
            elif 'SalesReceiptAdd' in response_type:
                return QBFCResponseMapper._map_sales_receipt_add(response)
            elif 'SalesReceiptQuery' in response_type:
                return QBFCResponseMapper._map_sales_receipt_query(response_set)
            elif 'SalesReceiptMod' in response_type:
                return QBFCResponseMapper._map_sales_receipt_mod(response)
            elif 'ChargeAdd' in response_type:
                return QBFCResponseMapper._map_charge_add(response)
            elif 'ChargeQuery' in response_type:
                return QBFCResponseMapper._map_charge_query(response_set)
            elif 'ChargeMod' in response_type:
                return QBFCResponseMapper._map_charge_mod(response)
            elif 'AccountQuery' in response_type:
                return QBFCResponseMapper._map_account_query(response_set)
            elif 'ItemQuery' in response_type:
                return QBFCResponseMapper._map_item_query(response_set)
            elif 'StandardTermsQuery' in response_type:
                return QBFCResponseMapper._map_terms_query(response_set)
            elif 'ClassQuery' in response_type:
                return QBFCResponseMapper._map_class_query(response_set)
            elif 'TxnDel' in response_type:
                return QBFCResponseMapper._map_txn_del(response)
            elif 'ReceivePaymentAdd' in response_type:
                return QBFCResponseMapper._map_receive_payment_add(response)
            elif 'ReceivePaymentQuery' in response_type:
                return QBFCResponseMapper._map_receive_payment_query(response_set)
            else:
                return {'success': True, 'data': {'response_type': response_type}}

        except Exception as e:
            logger.error(f"Error mapping QBFC response: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _safe_get_value(obj, allow_none=False):
        """Safely get value from QBFC object, returning None or empty string if not set.

        Converts pywintypes.datetime objects to ISO format strings to ensure
        the response can be pickled for multiprocessing.
        """
        try:
            if obj is None:
                return None if allow_none else ''
            # Check if value is set before getting it
            if hasattr(obj, 'GetValue'):
                value = obj.GetValue()
                # Convert pywintypes.datetime to string for pickle compatibility
                if HAS_PYWINTYPES and isinstance(value, pywintypes.TimeType):
                    # Convert to ISO format string
                    return value.strftime('%Y-%m-%dT%H:%M:%S')
                elif isinstance(value, datetime):
                    return value.strftime('%Y-%m-%dT%H:%M:%S')
                return value
            return None if allow_none else ''
        except:
            return None if allow_none else ''

    @staticmethod
    def _map_customer_add(response):
        """Map CustomerAddRs response."""
        customer_ret = response.Detail

        return {
            'success': True,
            'data': {
                'list_id': QBFCResponseMapper._safe_get_value(customer_ret.ListID),
                'name': QBFCResponseMapper._safe_get_value(customer_ret.Name),
                'full_name': QBFCResponseMapper._safe_get_value(customer_ret.FullName),
                'edit_sequence': QBFCResponseMapper._safe_get_value(customer_ret.EditSequence)
            }
        }

    @staticmethod
    def _map_customer_query(response_set):
        """Map CustomerQueryRs response."""
        customer_list = []

        # Get the first response
        response = response_set.ResponseList.GetAt(0)
        if response.StatusCode != 0:
            return {'success': False, 'error': response.StatusMessage}

        # Detail is a CustomerRetList - iterate through it
        customer_ret_list = response.Detail
        if customer_ret_list is None:
            return {'success': True, 'data': {'customers': []}}

        for i in range(customer_ret_list.Count):
            customer_ret = customer_ret_list.GetAt(i)

            # Get sublevel (0 = parent, 1+ = job/sub-customer)
            sublevel = QBFCResponseMapper._safe_get_value(customer_ret.Sublevel)
            if sublevel == '':
                sublevel = 0
            else:
                sublevel = int(sublevel)

            # Get balance
            balance_str = QBFCResponseMapper._safe_get_value(customer_ret.Balance)
            balance = float(balance_str) if balance_str else 0.0

            customer_list.append({
                'list_id': QBFCResponseMapper._safe_get_value(customer_ret.ListID),
                'name': QBFCResponseMapper._safe_get_value(customer_ret.Name),
                'full_name': QBFCResponseMapper._safe_get_value(customer_ret.FullName),
                'sublevel': sublevel,
                'email': QBFCResponseMapper._safe_get_value(customer_ret.Email),
                'is_active': QBFCResponseMapper._safe_get_value(customer_ret.IsActive) in (True, 'true'),
                'balance': balance
            })

        return {'success': True, 'data': {'customers': customer_list}}

    @staticmethod
    def _map_invoice_add(response):
        """Map InvoiceAddRs response."""
        invoice_ret = response.Detail

        return {
            'success': True,
            'data': {
                'txn_id': QBFCResponseMapper._safe_get_value(invoice_ret.TxnID),
                'ref_number': QBFCResponseMapper._safe_get_value(invoice_ret.RefNumber),
                'txn_date': QBFCResponseMapper._safe_get_value(invoice_ret.TxnDate),
                'customer_ref': {
                    'list_id': QBFCResponseMapper._safe_get_value(invoice_ret.CustomerRef.ListID),
                    'full_name': QBFCResponseMapper._safe_get_value(invoice_ret.CustomerRef.FullName)
                },
                'subtotal': QBFCResponseMapper._safe_get_value(invoice_ret.Subtotal),
                'balance_remaining': QBFCResponseMapper._safe_get_value(invoice_ret.BalanceRemaining),
                'is_paid': QBFCResponseMapper._safe_get_value(invoice_ret.IsPaid) in (True, 'true'),
                'edit_sequence': QBFCResponseMapper._safe_get_value(invoice_ret.EditSequence)
            }
        }

    @staticmethod
    def _map_invoice_query(response_set):
        """Map InvoiceQueryRs response."""
        invoice_list = []

        # Get the first response
        response = response_set.ResponseList.GetAt(0)
        if response.StatusCode != 0:
            return {'success': False, 'error': response.StatusMessage}

        # Detail is an InvoiceRetList - iterate through it
        invoice_ret_list = response.Detail
        if invoice_ret_list is None:
            return {'success': True, 'data': {'invoices': []}}

        for i in range(invoice_ret_list.Count):
            invoice_ret = invoice_ret_list.GetAt(i)

            invoice_data = {
                'txn_id': QBFCResponseMapper._safe_get_value(invoice_ret.TxnID),
                'ref_number': QBFCResponseMapper._safe_get_value(invoice_ret.RefNumber),
                'txn_date': QBFCResponseMapper._safe_get_value(invoice_ret.TxnDate),
                'customer_ref': {
                    'list_id': QBFCResponseMapper._safe_get_value(invoice_ret.CustomerRef.ListID),
                    'full_name': QBFCResponseMapper._safe_get_value(invoice_ret.CustomerRef.FullName)
                },
                'subtotal': float(QBFCResponseMapper._safe_get_value(invoice_ret.Subtotal) or '0'),
                'balance_remaining': float(QBFCResponseMapper._safe_get_value(invoice_ret.BalanceRemaining) or '0'),
                'is_paid': QBFCResponseMapper._safe_get_value(invoice_ret.IsPaid) in (True, 'true'),
                'is_pending': QBFCResponseMapper._safe_get_value(invoice_ret.IsPending) in (True, 'true'),
                'edit_sequence': QBFCResponseMapper._safe_get_value(invoice_ret.EditSequence),
                'time_modified': QBFCResponseMapper._safe_get_value(invoice_ret.TimeModified),
                'memo': QBFCResponseMapper._safe_get_value(invoice_ret.Memo) or ''
            }

            # Parse deposit/payment account info if present
            try:
                if invoice_ret.DepositToAccountRef is not None:
                    invoice_data['deposit_account'] = {
                        'list_id': QBFCResponseMapper._safe_get_value(invoice_ret.DepositToAccountRef.ListID),
                        'full_name': QBFCResponseMapper._safe_get_value(invoice_ret.DepositToAccountRef.FullName)
                    }
            except:
                pass

            # Parse linked transactions (payments)
            try:
                if invoice_ret.LinkedTxnList and invoice_ret.LinkedTxnList.Count > 0:
                    invoice_data['linked_transactions'] = []
                    for j in range(invoice_ret.LinkedTxnList.Count):
                        linked = invoice_ret.LinkedTxnList.GetAt(j)
                        linked_data = {
                            'txn_id': QBFCResponseMapper._safe_get_value(linked.TxnID),
                            'txn_type': QBFCResponseMapper._safe_get_value(linked.TxnType),
                            'txn_date': QBFCResponseMapper._safe_get_value(linked.TxnDate),
                            'ref_number': QBFCResponseMapper._safe_get_value(linked.RefNumber),
                            'amount': QBFCResponseMapper._safe_get_value(linked.Amount)
                        }
                        invoice_data['linked_transactions'].append(linked_data)
            except:
                pass

            invoice_list.append(invoice_data)

        return {'success': True, 'data': {'invoices': invoice_list}}

    @staticmethod
    def _map_invoice_mod(response):
        """Map InvoiceModRs response."""
        invoice_ret = response.Detail

        return {
            'success': True,
            'data': {
                'txn_id': QBFCResponseMapper._safe_get_value(invoice_ret.TxnID),
                'ref_number': QBFCResponseMapper._safe_get_value(invoice_ret.RefNumber),
                'is_pending': QBFCResponseMapper._safe_get_value(invoice_ret.IsPending) in (True, 'true'),
                'edit_sequence': QBFCResponseMapper._safe_get_value(invoice_ret.EditSequence)
            }
        }

    @staticmethod
    def _map_sales_receipt_add(response):
        """Map SalesReceiptAddRs response."""
        receipt_ret = response.Detail

        # Build response data with safe property access
        # Note: SalesReceiptRet doesn't have BalanceRemaining (unlike InvoiceRet)
        # because sales receipts are paid in full at time of sale
        data = {
            'txn_id': QBFCResponseMapper._safe_get_value(receipt_ret.TxnID),
            'ref_number': QBFCResponseMapper._safe_get_value(receipt_ret.RefNumber),
            'txn_date': QBFCResponseMapper._safe_get_value(receipt_ret.TxnDate),
            'edit_sequence': QBFCResponseMapper._safe_get_value(receipt_ret.EditSequence)
        }

        # Safe access for optional properties
        try:
            data['customer_ref'] = {
                'list_id': QBFCResponseMapper._safe_get_value(receipt_ret.CustomerRef.ListID),
                'full_name': QBFCResponseMapper._safe_get_value(receipt_ret.CustomerRef.FullName)
            }
        except:
            data['customer_ref'] = {'list_id': '', 'full_name': ''}

        try:
            data['subtotal'] = QBFCResponseMapper._safe_get_value(receipt_ret.Subtotal)
        except:
            data['subtotal'] = ''

        try:
            data['total_amount'] = QBFCResponseMapper._safe_get_value(receipt_ret.TotalAmount)
        except:
            data['total_amount'] = ''

        try:
            data['is_pending'] = QBFCResponseMapper._safe_get_value(receipt_ret.IsPending) in (True, 'true')
        except:
            data['is_pending'] = False

        # Sales receipts are paid in full, so balance is always 0
        data['balance_remaining'] = '0'

        return {'success': True, 'data': data}

    @staticmethod
    def _map_sales_receipt_query(response_set):
        """Map SalesReceiptQueryRs response."""
        receipt_list = []

        # Get the first response
        response = response_set.ResponseList.GetAt(0)
        if response.StatusCode != 0:
            error_msg = f"StatusCode {response.StatusCode}: {response.StatusMessage}"
            print(f"[SalesReceiptQuery] Error: {error_msg}")
            return {'success': False, 'error': error_msg}

        # Detail is a SalesReceiptRetList - iterate through it
        receipt_ret_list = response.Detail
        if receipt_ret_list is None:
            return {'success': True, 'data': {'sales_receipts': []}}

        for i in range(receipt_ret_list.Count):
            receipt_ret = receipt_ret_list.GetAt(i)

            receipt_data = {
                'txn_id': QBFCResponseMapper._safe_get_value(receipt_ret.TxnID),
                'ref_number': QBFCResponseMapper._safe_get_value(receipt_ret.RefNumber),
                'txn_date': QBFCResponseMapper._safe_get_value(receipt_ret.TxnDate),
                'txn_number': QBFCResponseMapper._safe_get_value(receipt_ret.TxnNumber),
                'customer_ref': {
                    'list_id': QBFCResponseMapper._safe_get_value(receipt_ret.CustomerRef.ListID),
                    'full_name': QBFCResponseMapper._safe_get_value(receipt_ret.CustomerRef.FullName)
                },
                'subtotal': float(QBFCResponseMapper._safe_get_value(receipt_ret.Subtotal) or '0'),
                'total_amount': float(QBFCResponseMapper._safe_get_value(receipt_ret.TotalAmount) or '0'),
                # Sales receipts don't have BalanceRemaining - they're immediate cash sales
                # Balance is always 0 (fully paid at time of sale)
                'balance_remaining': 0,
                'is_pending': QBFCResponseMapper._safe_get_value(receipt_ret.IsPending) in (True, 'true'),
                'is_to_be_printed': QBFCResponseMapper._safe_get_value(receipt_ret.IsToBePrinted) in (True, 'true'),
                'is_to_be_emailed': QBFCResponseMapper._safe_get_value(receipt_ret.IsToBeEmailed) in (True, 'true'),
                'edit_sequence': QBFCResponseMapper._safe_get_value(receipt_ret.EditSequence),
                'time_modified': QBFCResponseMapper._safe_get_value(receipt_ret.TimeModified),
                'time_created': QBFCResponseMapper._safe_get_value(receipt_ret.TimeCreated),
                'memo': QBFCResponseMapper._safe_get_value(receipt_ret.Memo) or ''
            }

            # Parse payment method if present
            try:
                if receipt_ret.PaymentMethodRef is not None:
                    receipt_data['payment_method'] = {
                        'list_id': QBFCResponseMapper._safe_get_value(receipt_ret.PaymentMethodRef.ListID),
                        'full_name': QBFCResponseMapper._safe_get_value(receipt_ret.PaymentMethodRef.FullName)
                    }
            except:
                pass

            # Parse deposit account if present
            try:
                if receipt_ret.DepositToAccountRef is not None:
                    receipt_data['deposit_account'] = {
                        'list_id': QBFCResponseMapper._safe_get_value(receipt_ret.DepositToAccountRef.ListID),
                        'full_name': QBFCResponseMapper._safe_get_value(receipt_ret.DepositToAccountRef.FullName)
                    }
            except:
                pass

            # Parse linked transactions (payments - cash, CC, check, etc.)
            try:
                if receipt_ret.LinkedTxnList and receipt_ret.LinkedTxnList.Count > 0:
                    receipt_data['linked_transactions'] = []
                    for j in range(receipt_ret.LinkedTxnList.Count):
                        linked = receipt_ret.LinkedTxnList.GetAt(j)
                        linked_data = {
                            'txn_id': QBFCResponseMapper._safe_get_value(linked.TxnID),
                            'txn_type': QBFCResponseMapper._safe_get_value(linked.TxnType),
                            'txn_date': QBFCResponseMapper._safe_get_value(linked.TxnDate),
                            'ref_number': QBFCResponseMapper._safe_get_value(linked.RefNumber),
                            'amount': QBFCResponseMapper._safe_get_value(linked.Amount)
                        }
                        receipt_data['linked_transactions'].append(linked_data)
            except:
                pass

            receipt_list.append(receipt_data)

        return {'success': True, 'data': {'sales_receipts': receipt_list}}

    @staticmethod
    def _map_sales_receipt_mod(response):
        """Map SalesReceiptModRs response."""
        receipt_ret = response.Detail

        return {
            'success': True,
            'data': {
                'txn_id': QBFCResponseMapper._safe_get_value(receipt_ret.TxnID),
                'ref_number': QBFCResponseMapper._safe_get_value(receipt_ret.RefNumber),
                'edit_sequence': QBFCResponseMapper._safe_get_value(receipt_ret.EditSequence)
            }
        }

    @staticmethod
    def _map_charge_add(response):
        """Map ChargeAddRs response."""
        charge_ret = response.Detail

        # Build response data with safe property access
        data = {
            'txn_id': QBFCResponseMapper._safe_get_value(charge_ret.TxnID),
            'txn_date': QBFCResponseMapper._safe_get_value(charge_ret.TxnDate),
            'edit_sequence': QBFCResponseMapper._safe_get_value(charge_ret.EditSequence)
        }

        # Safe access for optional properties
        try:
            data['customer_ref'] = {
                'list_id': QBFCResponseMapper._safe_get_value(charge_ret.CustomerRef.ListID),
                'full_name': QBFCResponseMapper._safe_get_value(charge_ret.CustomerRef.FullName)
            }
        except:
            data['customer_ref'] = {'list_id': '', 'full_name': ''}

        try:
            data['amount'] = QBFCResponseMapper._safe_get_value(charge_ret.Amount)
        except:
            data['amount'] = ''

        try:
            data['quantity'] = QBFCResponseMapper._safe_get_value(charge_ret.Quantity)
        except:
            data['quantity'] = ''

        # Note: ChargeRet may not have Memo property - use Desc instead if available
        try:
            data['memo'] = QBFCResponseMapper._safe_get_value(charge_ret.Desc)
        except:
            data['memo'] = ''

        return {'success': True, 'data': data}

    @staticmethod
    def _map_charge_query(response_set):
        """Map ChargeQueryRs response."""
        charges_list = []

        # Get the first response
        response = response_set.ResponseList.GetAt(0)
        if response.StatusCode != 0:
            return {'success': False, 'error': response.StatusMessage}

        # Detail is a ChargeRetList - iterate through it
        charge_ret_list = response.Detail
        if charge_ret_list is None:
            return {'success': True, 'data': {'charges': []}}

        for i in range(charge_ret_list.Count):
            charge_ret = charge_ret_list.GetAt(i)

            # Build charge data with safe property access
            charge_data = {
                'txn_id': QBFCResponseMapper._safe_get_value(charge_ret.TxnID),
                'edit_sequence': QBFCResponseMapper._safe_get_value(charge_ret.EditSequence)
            }

            try:
                charge_data['ref_number'] = QBFCResponseMapper._safe_get_value(charge_ret.RefNumber)
            except:
                charge_data['ref_number'] = ''

            try:
                charge_data['txn_date'] = QBFCResponseMapper._safe_get_value(charge_ret.TxnDate)
            except:
                charge_data['txn_date'] = ''

            try:
                charge_data['customer_ref'] = {
                    'list_id': QBFCResponseMapper._safe_get_value(charge_ret.CustomerRef.ListID),
                    'full_name': QBFCResponseMapper._safe_get_value(charge_ret.CustomerRef.FullName)
                }
            except:
                charge_data['customer_ref'] = {'list_id': '', 'full_name': ''}

            try:
                charge_data['amount'] = float(QBFCResponseMapper._safe_get_value(charge_ret.Amount) or '0')
            except:
                charge_data['amount'] = 0.0

            try:
                charge_data['balance_remaining'] = float(QBFCResponseMapper._safe_get_value(charge_ret.BalanceRemaining) or '0')
            except:
                charge_data['balance_remaining'] = 0.0

            try:
                charge_data['is_paid'] = QBFCResponseMapper._safe_get_value(charge_ret.IsPaid) in (True, 'true')
            except:
                charge_data['is_paid'] = False

            try:
                charge_data['quantity'] = QBFCResponseMapper._safe_get_value(charge_ret.Quantity)
            except:
                charge_data['quantity'] = ''

            try:
                charge_data['desc'] = QBFCResponseMapper._safe_get_value(charge_ret.Desc)
                # Charges use Desc instead of Memo - alias it for verification
                charge_data['memo'] = charge_data['desc']
            except:
                charge_data['desc'] = ''
                charge_data['memo'] = ''

            # Parse linked transactions (payments)
            try:
                if charge_ret.LinkedTxnList and charge_ret.LinkedTxnList.Count > 0:
                    charge_data['linked_transactions'] = []
                    for j in range(charge_ret.LinkedTxnList.Count):
                        linked = charge_ret.LinkedTxnList.GetAt(j)
                        linked_data = {
                            'txn_id': QBFCResponseMapper._safe_get_value(linked.TxnID),
                            'txn_type': QBFCResponseMapper._safe_get_value(linked.TxnType),
                            'txn_date': QBFCResponseMapper._safe_get_value(linked.TxnDate),
                            'ref_number': QBFCResponseMapper._safe_get_value(linked.RefNumber),
                            'amount': QBFCResponseMapper._safe_get_value(linked.Amount)
                        }
                        charge_data['linked_transactions'].append(linked_data)
            except:
                pass

            charges_list.append(charge_data)

        return {'success': True, 'data': {'charges': charges_list}}

    @staticmethod
    def _map_charge_mod(response):
        """Map ChargeModRs response."""
        charge_ret = response.Detail

        return {
            'success': True,
            'data': {
                'txn_id': QBFCResponseMapper._safe_get_value(charge_ret.TxnID),
                'ref_number': QBFCResponseMapper._safe_get_value(charge_ret.RefNumber),
                'edit_sequence': QBFCResponseMapper._safe_get_value(charge_ret.EditSequence)
            }
        }

    @staticmethod
    def _map_account_query(response_set):
        """Map AccountQueryRs response."""
        account_list = []

        # Get the first response
        response = response_set.ResponseList.GetAt(0)
        if response.StatusCode != 0:
            return {'success': False, 'error': response.StatusMessage}

        # Detail is an AccountRetList - iterate through it
        account_ret_list = response.Detail
        if account_ret_list is None:
            return {'success': True, 'data': {'accounts': []}}

        for i in range(account_ret_list.Count):
            account_ret = account_ret_list.GetAt(i)

            balance_str = QBFCResponseMapper._safe_get_value(account_ret.Balance)
            balance = float(balance_str) if balance_str else 0.0

            # AccountType is an enum - use GetAsString() to get the readable name
            try:
                account_type = account_ret.AccountType.GetAsString() if account_ret.AccountType else ''
            except:
                account_type = ''

            # IsActive can return bool, string 'true'/'false', or None
            try:
                is_active_val = account_ret.IsActive.GetValue() if account_ret.IsActive else True
                is_active = is_active_val in (True, 'true', 1)
            except:
                is_active = True  # Default to active if we can't determine

            account_list.append({
                'list_id': QBFCResponseMapper._safe_get_value(account_ret.ListID),
                'name': QBFCResponseMapper._safe_get_value(account_ret.Name),
                'full_name': QBFCResponseMapper._safe_get_value(account_ret.FullName),
                'account_type': account_type,
                'balance': balance,
                'account_number': QBFCResponseMapper._safe_get_value(account_ret.AccountNumber),
                'is_active': is_active
            })

        return {'success': True, 'data': {'accounts': account_list}}

    @staticmethod
    def _map_item_query(response_set):
        """Map ItemQueryRs response using QBFC OR type pattern."""
        items = []

        response = response_set.ResponseList.GetAt(0)
        if response.StatusCode != 0:
            return {'success': False, 'error': response.StatusMessage}

        # Detail is an IORItemRetList - each element is an IORItemRet wrapper
        or_item_ret_list = response.Detail
        if or_item_ret_list is None:
            return {'success': True, 'data': {'items': []}}

        for i in range(or_item_ret_list.Count):
            or_item_ret = or_item_ret_list.GetAt(i)

            # Check which item type property is non-null (QBFC OR type pattern)
            item_ret = None
            item_type = ''

            try:
                if or_item_ret.ItemServiceRet is not None:
                    item_ret = or_item_ret.ItemServiceRet
                    item_type = 'Service'
                elif or_item_ret.ItemInventoryRet is not None:
                    item_ret = or_item_ret.ItemInventoryRet
                    item_type = 'Inventory'
                elif or_item_ret.ItemNonInventoryRet is not None:
                    item_ret = or_item_ret.ItemNonInventoryRet
                    item_type = 'NonInventory'
                elif or_item_ret.ItemOtherChargeRet is not None:
                    item_ret = or_item_ret.ItemOtherChargeRet
                    item_type = 'OtherCharge'
                elif or_item_ret.ItemDiscountRet is not None:
                    item_ret = or_item_ret.ItemDiscountRet
                    item_type = 'Discount'
                elif or_item_ret.ItemFixedAssetRet is not None:
                    item_ret = or_item_ret.ItemFixedAssetRet
                    item_type = 'FixedAsset'
                elif or_item_ret.ItemPaymentRet is not None:
                    item_ret = or_item_ret.ItemPaymentRet
                    item_type = 'Payment'
                elif or_item_ret.ItemSalesTaxRet is not None:
                    item_ret = or_item_ret.ItemSalesTaxRet
                    item_type = 'SalesTax'
                elif or_item_ret.ItemSalesTaxGroupRet is not None:
                    item_ret = or_item_ret.ItemSalesTaxGroupRet
                    item_type = 'SalesTaxGroup'
                elif or_item_ret.ItemGroupRet is not None:
                    item_ret = or_item_ret.ItemGroupRet
                    item_type = 'Group'
                elif or_item_ret.ItemSubtotalRet is not None:
                    item_ret = or_item_ret.ItemSubtotalRet
                    item_type = 'Subtotal'
            except Exception as e:
                logger.debug(f"Error checking item type: {e}")
                continue

            if item_ret is None:
                continue

            # Now access properties from the actual item object
            # Wrap each property access since not all item types have all properties
            try:
                list_id = QBFCResponseMapper._safe_get_value(item_ret.ListID)
            except:
                list_id = ''

            try:
                name = QBFCResponseMapper._safe_get_value(item_ret.Name)
            except:
                name = ''

            try:
                full_name = QBFCResponseMapper._safe_get_value(item_ret.FullName)
            except:
                full_name = name  # Fall back to Name if FullName not available

            try:
                is_active = QBFCResponseMapper._safe_get_value(item_ret.IsActive) in (True, 'true')
            except:
                is_active = True

            items.append({
                'list_id': list_id,
                'name': name,
                'full_name': full_name,
                'type': item_type,
                'is_active': is_active
            })

        return {'success': True, 'data': {'items': items}}

    @staticmethod
    def _map_terms_query(response_set):
        """Map StandardTermsQueryRs response."""
        terms = []

        # Get the first response
        response = response_set.ResponseList.GetAt(0)
        if response.StatusCode != 0:
            return {'success': False, 'error': response.StatusMessage}

        # Detail is a StandardTermsRetList - iterate through it
        terms_ret_list = response.Detail
        if terms_ret_list is None:
            return {'success': True, 'data': {'terms': []}}

        for i in range(terms_ret_list.Count):
            terms_ret = terms_ret_list.GetAt(i)

            terms.append({
                'list_id': QBFCResponseMapper._safe_get_value(terms_ret.ListID),
                'name': QBFCResponseMapper._safe_get_value(terms_ret.Name),
                'is_active': QBFCResponseMapper._safe_get_value(terms_ret.IsActive) in (True, 'true'),
                'std_due_days': QBFCResponseMapper._safe_get_value(terms_ret.StdDueDays),
                'std_discount_days': QBFCResponseMapper._safe_get_value(terms_ret.StdDiscountDays),
                'discount_pct': QBFCResponseMapper._safe_get_value(terms_ret.DiscountPct)
            })

        return {'success': True, 'data': {'terms': terms}}

    @staticmethod
    def _map_class_query(response_set):
        """Map ClassQueryRs response."""
        classes = []

        # Get the first response
        response = response_set.ResponseList.GetAt(0)
        if response.StatusCode != 0:
            return {'success': False, 'error': response.StatusMessage}

        # Detail is a ClassRetList - iterate through it
        class_ret_list = response.Detail
        if class_ret_list is None:
            return {'success': True, 'data': {'classes': []}}

        for i in range(class_ret_list.Count):
            class_ret = class_ret_list.GetAt(i)

            classes.append({
                'list_id': QBFCResponseMapper._safe_get_value(class_ret.ListID),
                'name': QBFCResponseMapper._safe_get_value(class_ret.Name),
                'full_name': QBFCResponseMapper._safe_get_value(class_ret.FullName),
                'is_active': QBFCResponseMapper._safe_get_value(class_ret.IsActive) in (True, 'true')
            })

        return {'success': True, 'data': {'classes': classes}}

    @staticmethod
    def _map_txn_del(response):
        """Map TxnDelRs response."""
        # TxnDelRs doesn't have much detail - just confirmation
        return {
            'success': True,
            'data': {
                'deleted': True,
                'txn_del_type': '',  # Not available in response
                'txn_id': '',  # Not available in response
                'message': 'Transaction deleted successfully'
            }
        }

    @staticmethod
    def _map_receive_payment_add(response):
        """Map ReceivePaymentAddRs response."""
        payment_ret = response.Detail

        data = {
            'txn_id': QBFCResponseMapper._safe_get_value(payment_ret.TxnID),
            'txn_date': QBFCResponseMapper._safe_get_value(payment_ret.TxnDate),
            'edit_sequence': QBFCResponseMapper._safe_get_value(payment_ret.EditSequence)
        }

        try:
            data['ref_number'] = QBFCResponseMapper._safe_get_value(payment_ret.RefNumber)
        except:
            data['ref_number'] = ''

        try:
            data['total_amount'] = float(QBFCResponseMapper._safe_get_value(payment_ret.TotalAmount) or '0')
        except:
            data['total_amount'] = 0.0

        try:
            data['customer_ref'] = {
                'list_id': QBFCResponseMapper._safe_get_value(payment_ret.CustomerRef.ListID),
                'full_name': QBFCResponseMapper._safe_get_value(payment_ret.CustomerRef.FullName)
            }
        except:
            data['customer_ref'] = {'list_id': '', 'full_name': ''}

        return {'success': True, 'data': data}

    @staticmethod
    def _map_receive_payment_query(response_set):
        """Map ReceivePaymentQueryRs response."""
        payments_list = []

        for i in range(response_set.ResponseList.Count):
            response = response_set.ResponseList.GetAt(i)
            if response.StatusCode != 0:
                continue

            ret_list = response.Detail
            if ret_list is None:
                continue

            for j in range(ret_list.Count):
                payment_ret = ret_list.GetAt(j)

                payment_data = {
                    'txn_id': QBFCResponseMapper._safe_get_value(payment_ret.TxnID),
                    'txn_date': QBFCResponseMapper._safe_get_value(payment_ret.TxnDate),
                    'edit_sequence': QBFCResponseMapper._safe_get_value(payment_ret.EditSequence),
                    'ref_number': QBFCResponseMapper._safe_get_value(payment_ret.RefNumber) or '',
                    'total_amount': float(QBFCResponseMapper._safe_get_value(payment_ret.TotalAmount) or '0'),
                    'memo': QBFCResponseMapper._safe_get_value(payment_ret.Memo) or ''
                }

                # Customer reference
                try:
                    payment_data['customer_ref'] = {
                        'list_id': QBFCResponseMapper._safe_get_value(payment_ret.CustomerRef.ListID),
                        'full_name': QBFCResponseMapper._safe_get_value(payment_ret.CustomerRef.FullName)
                    }
                except:
                    payment_data['customer_ref'] = {'list_id': '', 'full_name': ''}

                # Deposit account
                try:
                    if payment_ret.DepositToAccountRef is not None:
                        payment_data['deposit_account'] = {
                            'list_id': QBFCResponseMapper._safe_get_value(payment_ret.DepositToAccountRef.ListID),
                            'full_name': QBFCResponseMapper._safe_get_value(payment_ret.DepositToAccountRef.FullName)
                        }
                except:
                    pass

                payments_list.append(payment_data)

        return {'success': True, 'data': {'payments': payments_list}}
