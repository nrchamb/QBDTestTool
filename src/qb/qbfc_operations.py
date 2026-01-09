"""
QBFC 13.0 Operations - High-level QB operations using QBFC COM objects.

Replaces QBXMLBuilder with QBFC-based operations that maintain the same interface.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
import pywintypes
import win32com.client
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def _sanitize_qb_xml_response(response_xml: str) -> str:
    """
    Sanitize QuickBooks XML response to handle encoding issues.

    QuickBooks may return special characters (em dashes, curly quotes, etc.)
    that cause XML parsing issues. This function normalizes them.

    Args:
        response_xml: Raw XML response string from QuickBooks

    Returns:
        Sanitized XML string safe for parsing
    """
    if not response_xml:
        return response_xml

    # Common Windows-1252 special characters that cause issues
    # Map to ASCII-safe equivalents
    replacements = {
        '\u2014': '-',   # em dash (—)
        '\u2013': '-',   # en dash (–)
        '\u2018': "'",   # left single quote (')
        '\u2019': "'",   # right single quote (')
        '\u201c': '"',   # left double quote (")
        '\u201d': '"',   # right double quote (")
        '\u2026': '...', # ellipsis (…)
        '\u2022': '*',   # bullet (•)
        '\u00a0': ' ',   # non-breaking space
        '\u00ae': '(R)', # registered trademark (®)
        '\u00a9': '(C)', # copyright (©)
        '\u2122': 'TM',  # trademark (™)
    }

    for old, new in replacements.items():
        response_xml = response_xml.replace(old, new)

    # For any remaining non-ASCII, encode to ASCII with replacement
    # This handles edge cases we haven't explicitly mapped
    try:
        response_xml = response_xml.encode('ascii', 'replace').decode('ascii')
    except Exception:
        pass  # Keep original if encoding fails

    return response_xml


def _is_encoding_error(error: Exception) -> bool:
    """Check if an exception is related to XML/UTF encoding issues."""
    error_str = str(error).lower()
    return any(keyword in error_str for keyword in [
        'utfdataformat',
        'utf',
        'encoding',
        'invalid byte',
        'saxparse',
        'xml',
    ])


class QBXMLRP2Fallback:
    """
    Fallback query handler using QBXMLRP2 for when QBFC fails due to encoding issues.

    QBXMLRP2 gives us access to raw XML responses which we can sanitize
    before parsing, avoiding encoding errors from special characters.
    """

    @staticmethod
    def query_customers_raw(app_name: str = "QBDTestTool") -> Dict[str, Any]:
        """
        Query customers using QBXMLRP2 with XML sanitization.

        Args:
            app_name: Application name for QB connection

        Returns:
            Dict matching QBFCResponseMapper.map_customer_query output format
        """
        rp = None
        ticket = None

        try:
            # Create QBXMLRP2 request processor
            rp = win32com.client.Dispatch("QBXMLRP2.RequestProcessor")
            rp.OpenConnection("", app_name)
            ticket = rp.BeginSession("", 0)  # Empty = currently open company

            # Build CustomerQuery request XML
            request_xml = '''<?xml version="1.0" encoding="utf-8"?>
<?qbxml version="13.0"?>
<QBXML>
    <QBXMLMsgsRq onError="stopOnError">
        <CustomerQueryRq>
            <ActiveStatus>ActiveOnly</ActiveStatus>
        </CustomerQueryRq>
    </QBXMLMsgsRq>
</QBXML>'''

            # Send request and get raw response
            response_xml = rp.ProcessRequest(ticket, request_xml)

            # Sanitize the response to handle encoding issues
            response_xml = _sanitize_qb_xml_response(response_xml)

            # Parse the sanitized XML
            return QBXMLRP2Fallback._parse_customer_response(response_xml)

        except Exception as e:
            logger.error(f"QBXMLRP2 fallback failed: {e}")
            return {'success': False, 'error': f"Fallback query failed: {e}"}

        finally:
            # Clean up connection
            if ticket and rp:
                try:
                    rp.EndSession(ticket)
                except Exception:
                    pass
            if rp:
                try:
                    rp.CloseConnection()
                except Exception:
                    pass

    @staticmethod
    def _parse_customer_response(response_xml: str) -> Dict[str, Any]:
        """
        Parse customer query XML response into dict format.

        Args:
            response_xml: Sanitized XML response string

        Returns:
            Dict with 'success', 'data' containing 'customers' list
        """
        try:
            root = ET.fromstring(response_xml)

            # Find CustomerQueryRs
            customer_rs = root.find('.//CustomerQueryRs')
            if customer_rs is None:
                return {'success': False, 'error': 'No CustomerQueryRs in response'}

            # Check status
            status_code = customer_rs.get('statusCode', '0')
            if status_code != '0':
                status_msg = customer_rs.get('statusMessage', 'Unknown error')
                return {'success': False, 'error': status_msg, 'status_code': status_code}

            # Parse customers
            customers = []
            for cust_ret in customer_rs.findall('CustomerRet'):
                customer = QBXMLRP2Fallback._parse_customer_ret(cust_ret)
                customers.append(customer)

            return {
                'success': True,
                'data': {'customers': customers}
            }

        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return {'success': False, 'error': f"XML parse error: {e}"}

    @staticmethod
    def _parse_customer_ret(cust_ret) -> Dict[str, Any]:
        """Parse a single CustomerRet element into a dict."""
        def get_text(element, path, default=''):
            el = element.find(path)
            return el.text if el is not None and el.text else default

        customer = {
            'list_id': get_text(cust_ret, 'ListID'),
            'name': get_text(cust_ret, 'Name'),
            'full_name': get_text(cust_ret, 'FullName'),
            'is_active': get_text(cust_ret, 'IsActive', 'true').lower() == 'true',
            'company_name': get_text(cust_ret, 'CompanyName'),
            'first_name': get_text(cust_ret, 'FirstName'),
            'last_name': get_text(cust_ret, 'LastName'),
            'email': get_text(cust_ret, 'Email'),
            'phone': get_text(cust_ret, 'Phone'),
            'balance': get_text(cust_ret, 'Balance', '0'),
        }

        # Parse billing address if present
        bill_addr = cust_ret.find('BillAddress')
        if bill_addr is not None:
            customer['billing_address'] = {
                'addr1': get_text(bill_addr, 'Addr1'),
                'addr2': get_text(bill_addr, 'Addr2'),
                'city': get_text(bill_addr, 'City'),
                'state': get_text(bill_addr, 'State'),
                'postal_code': get_text(bill_addr, 'PostalCode'),
                'country': get_text(bill_addr, 'Country'),
            }

        # Parse shipping address if present
        ship_addr = cust_ret.find('ShipAddress')
        if ship_addr is not None:
            customer['shipping_address'] = {
                'addr1': get_text(ship_addr, 'Addr1'),
                'addr2': get_text(ship_addr, 'Addr2'),
                'city': get_text(ship_addr, 'City'),
                'state': get_text(ship_addr, 'State'),
                'postal_code': get_text(ship_addr, 'PostalCode'),
                'country': get_text(ship_addr, 'Country'),
            }

        # Parse parent ref if present
        parent_ref = cust_ret.find('ParentRef')
        if parent_ref is not None:
            customer['parent_ref'] = {
                'list_id': get_text(parent_ref, 'ListID'),
                'full_name': get_text(parent_ref, 'FullName'),
            }

        return customer


# QBFC ENJobStatus enum values
JOB_STATUS_MAP = {
    'None': 0,       # jsNone
    'Pending': 1,    # jsPending
    'Awarded': 2,    # jsAwarded
    'InProgress': 3, # jsInProgress
    'Closed': 4,     # jsClosed
    'NotAwarded': 5  # jsNotAwarded
}


def _to_pywintypes_time(date_value):
    """Convert date string or datetime to pywintypes.Time for QBFC."""
    if date_value is None:
        return None
    if isinstance(date_value, pywintypes.TimeType):
        return date_value
    if isinstance(date_value, datetime):
        return pywintypes.Time(date_value)
    if isinstance(date_value, str):
        # Try common date formats
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']:
            try:
                dt = datetime.strptime(date_value, fmt)
                return pywintypes.Time(dt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date string: {date_value}")
    raise TypeError(f"Unexpected date type: {type(date_value)}")


class QBFCOperations:
    """High-level QBFC operations matching the current QBXMLBuilder interface."""

    @staticmethod
    def add_customer(session_manager, customer_data: Dict[str, Any]):
        """
        Add customer using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            customer_data: Dict with keys: name, email, first_name, last_name,
                          company, phone, billing_address, shipping_address, parent_ref

        Returns:
            QBFC response set object
        """
        # Create message set request
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        customer_add_rq = msg_set_rq.AppendCustomerAddRq()

        # Set required fields
        customer_add_rq.Name.SetValue(customer_data['name'])

        # Set optional parent ref (for jobs/sub-customers)
        if 'parent_ref' in customer_data:
            customer_add_rq.ParentRef.ListID.SetValue(customer_data['parent_ref'])

        # Set optional fields (check ORSet flag for each)
        if 'company' in customer_data:
            customer_add_rq.CompanyName.SetValue(customer_data['company'])

        if 'first_name' in customer_data:
            customer_add_rq.FirstName.SetValue(customer_data['first_name'])

        if 'last_name' in customer_data:
            customer_add_rq.LastName.SetValue(customer_data['last_name'])

        # Billing address
        if 'billing_address' in customer_data:
            addr = customer_data['billing_address']
            if 'addr1' in addr:
                customer_add_rq.BillAddress.Addr1.SetValue(addr['addr1'])
            if 'addr2' in addr:
                customer_add_rq.BillAddress.Addr2.SetValue(addr['addr2'])
            if 'city' in addr:
                customer_add_rq.BillAddress.City.SetValue(addr['city'])
            if 'state' in addr:
                customer_add_rq.BillAddress.State.SetValue(addr['state'])
            if 'postal_code' in addr:
                customer_add_rq.BillAddress.PostalCode.SetValue(addr['postal_code'])

        # Shipping address
        if 'shipping_address' in customer_data:
            addr = customer_data['shipping_address']
            if 'addr1' in addr:
                customer_add_rq.ShipAddress.Addr1.SetValue(addr['addr1'])
            if 'addr2' in addr:
                customer_add_rq.ShipAddress.Addr2.SetValue(addr['addr2'])
            if 'city' in addr:
                customer_add_rq.ShipAddress.City.SetValue(addr['city'])
            if 'state' in addr:
                customer_add_rq.ShipAddress.State.SetValue(addr['state'])
            if 'postal_code' in addr:
                customer_add_rq.ShipAddress.PostalCode.SetValue(addr['postal_code'])

        # Phone
        if 'phone' in customer_data:
            customer_add_rq.Phone.SetValue(customer_data['phone'])

        # Email
        if 'email' in customer_data:
            customer_add_rq.Email.SetValue(customer_data['email'])

        # Account Number (CID)
        if 'account_number' in customer_data:
            customer_add_rq.AccountNumber.SetValue(customer_data['account_number'])

        # Notes
        if 'notes' in customer_data:
            customer_add_rq.Notes.SetValue(customer_data['notes'])

        # Job status (for jobs only) - ENJobStatus enum
        if 'job_status' in customer_data:
            status_str = customer_data['job_status']
            status_int = JOB_STATUS_MAP.get(status_str, 0)
            customer_add_rq.JobStatus.SetValue(status_int)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def add_invoice(session_manager, invoice_data: Dict[str, Any]):
        """
        Add invoice using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            invoice_data: Dict with keys: customer_ref, txn_date, ref_number, terms_ref,
                         due_date, memo, deposit_to_account_ref, line_items

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        invoice_add_rq = msg_set_rq.AppendInvoiceAddRq()

        # Required: Customer reference
        invoice_add_rq.CustomerRef.ListID.SetValue(invoice_data['customer_ref'])

        # Optional: Transaction date (convert to pywintypes.Time)
        if 'txn_date' in invoice_data:
            invoice_add_rq.TxnDate.SetValue(_to_pywintypes_time(invoice_data['txn_date']))

        # Optional: Reference number
        if 'ref_number' in invoice_data:
            invoice_add_rq.RefNumber.SetValue(invoice_data['ref_number'])

        # Optional: Terms
        if 'terms_ref' in invoice_data:
            invoice_add_rq.TermsRef.ListID.SetValue(invoice_data['terms_ref'])

        # Optional: Due date (convert to pywintypes.Time)
        if 'due_date' in invoice_data:
            invoice_add_rq.DueDate.SetValue(_to_pywintypes_time(invoice_data['due_date']))

        # Optional: Memo
        if 'memo' in invoice_data:
            invoice_add_rq.Memo.SetValue(invoice_data['memo'])

        # Optional: Deposit to account
        if 'deposit_to_account_ref' in invoice_data:
            invoice_add_rq.DepositToAccountRef.ListID.SetValue(invoice_data['deposit_to_account_ref'])

        # Add line items
        if 'line_items' in invoice_data:
            for line in invoice_data['line_items']:
                line_add = invoice_add_rq.ORInvoiceLineAddList.Append().InvoiceLineAdd

                # Item reference
                if 'item_ref' in line:
                    line_add.ItemRef.ListID.SetValue(line['item_ref'])

                # Description
                if 'desc' in line:
                    line_add.Desc.SetValue(line['desc'])

                # Quantity
                if 'quantity' in line:
                    line_add.Quantity.SetValue(line['quantity'])

                # Amount takes precedence (works for all item types including sales tax)
                if 'amount' in line:
                    line_add.Amount.SetValue(float(line['amount']))
                # Rate only if no amount (doesn't work for sales tax items)
                elif 'rate' in line:
                    try:
                        line_add.ORRatePriceLevel.Rate.SetValue(float(line['rate']))
                    except:
                        # Fall back to calculating amount if rate fails
                        qty = line.get('quantity', 1)
                        line_add.Amount.SetValue(float(line['rate']) * float(qty))

                # Class
                if 'class_ref' in line:
                    line_add.ClassRef.FullName.SetValue(line['class_ref'])

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_invoice(session_manager, txn_id: Optional[str] = None,
                     ref_number: Optional[str] = None,
                     from_modified_date: Optional[str] = None,
                     date_range: Optional[tuple] = None):
        """
        Query invoices using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            txn_id: Optional transaction ID
            ref_number: Optional reference number
            from_modified_date: Optional - query invoices modified since this datetime
            date_range: Optional tuple of (from_date, to_date)

        Returns:
            QBFC response set object

        Note:
            For batch queries by TxnID, use query_invoices_batch() instead.
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        invoice_query_rq = msg_set_rq.AppendInvoiceQueryRq()

        # Filter by TxnID
        if txn_id:
            invoice_query_rq.ORInvoiceQuery.TxnIDList.Add(txn_id)

        # Filter by RefNumber
        elif ref_number:
            invoice_query_rq.ORInvoiceQuery.RefNumberFilter.ORRefNumberFilter.RefNumberList.Add(ref_number)

        # Filter by modified date (invoices changed since this datetime)
        # Note: QBFC SetValue for dates requires TWO parameters: (date, useClientTimeZone)
        elif from_modified_date:
            date_filter = invoice_query_rq.ORInvoiceQuery.InvoiceFilter.ORDateRangeFilter.ModifiedDateRangeFilter
            date_filter.FromModifiedDate.SetValue(_to_pywintypes_time(from_modified_date), False)

        # Filter by transaction date range
        elif date_range:
            from_date, to_date = date_range
            txn_filter = invoice_query_rq.ORInvoiceQuery.InvoiceFilter.ORDateRangeFilter.TxnDateRangeFilter.ORTxnDateRangeFilter.TxnDateFilter
            txn_filter.FromTxnDate.SetValue(_to_pywintypes_time(from_date), False)
            txn_filter.ToTxnDate.SetValue(_to_pywintypes_time(to_date), False)

        # Include line items and linked transactions
        invoice_query_rq.IncludeLineItems.SetValue(True)
        invoice_query_rq.IncludeLinkedTxns.SetValue(True)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def modify_invoice(session_manager, invoice_mod_data: Dict[str, Any]):
        """
        Modify invoice using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            invoice_mod_data: Dict with keys: txn_id, edit_sequence, and optionally:
                             is_pending, memo

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        invoice_mod_rq = msg_set_rq.AppendInvoiceModRq()

        # Required: TxnID and EditSequence
        invoice_mod_rq.TxnID.SetValue(invoice_mod_data['txn_id'])
        invoice_mod_rq.EditSequence.SetValue(invoice_mod_data['edit_sequence'])

        # Optional: IsPending (to reopen/close invoice)
        if 'is_pending' in invoice_mod_data:
            invoice_mod_rq.IsPending.SetValue(invoice_mod_data['is_pending'])

        # Optional: Memo
        if 'memo' in invoice_mod_data:
            invoice_mod_rq.Memo.SetValue(invoice_mod_data['memo'])

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def add_sales_receipt(session_manager, sales_receipt_data: Dict[str, Any]):
        """
        Add sales receipt using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            sales_receipt_data: Dict with keys: customer_ref, txn_date, ref_number,
                               memo, deposit_to_account_ref, line_items

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        sales_receipt_add_rq = msg_set_rq.AppendSalesReceiptAddRq()

        # Required: Customer reference
        sales_receipt_add_rq.CustomerRef.ListID.SetValue(sales_receipt_data['customer_ref'])

        # Optional: Transaction date (convert to pywintypes.Time)
        if 'txn_date' in sales_receipt_data:
            sales_receipt_add_rq.TxnDate.SetValue(_to_pywintypes_time(sales_receipt_data['txn_date']))

        # Optional: Reference number
        if 'ref_number' in sales_receipt_data:
            sales_receipt_add_rq.RefNumber.SetValue(sales_receipt_data['ref_number'])

        # Optional: Memo
        if 'memo' in sales_receipt_data:
            sales_receipt_add_rq.Memo.SetValue(sales_receipt_data['memo'])

        # Required: Deposit to account
        if 'deposit_to_account_ref' in sales_receipt_data:
            sales_receipt_add_rq.DepositToAccountRef.ListID.SetValue(sales_receipt_data['deposit_to_account_ref'])

        # Add line items
        if 'line_items' in sales_receipt_data:
            for line in sales_receipt_data['line_items']:
                line_add = sales_receipt_add_rq.ORSalesReceiptLineAddList.Append().SalesReceiptLineAdd

                # Item reference
                if 'item_ref' in line:
                    line_add.ItemRef.ListID.SetValue(line['item_ref'])

                # Description
                if 'desc' in line:
                    line_add.Desc.SetValue(line['desc'])

                # Quantity
                if 'quantity' in line:
                    line_add.Quantity.SetValue(line['quantity'])

                # For Sales Receipts, use Rate only - QB calculates Amount
                # (Unlike invoices, sales receipts throw "Invalid Amount format" if you set Amount directly)
                if 'rate' in line:
                    line_add.ORRatePriceLevel.Rate.SetValue(float(line['rate']))

                # Class
                if 'class_ref' in line:
                    line_add.ClassRef.FullName.SetValue(line['class_ref'])

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_sales_receipt(session_manager, txn_id: Optional[str] = None,
                           ref_number: Optional[str] = None,
                           from_modified_date: Optional[str] = None,
                           date_range: Optional[tuple] = None):
        """
        Query sales receipts using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            txn_id: Optional transaction ID
            ref_number: Optional reference number
            from_modified_date: Optional - query sales receipts modified since this datetime
            date_range: Optional tuple of (from_date, to_date)

        Returns:
            QBFC response set object

        Note:
            For batch queries by TxnID, use query_sales_receipts_batch() instead.
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        sales_receipt_query_rq = msg_set_rq.AppendSalesReceiptQueryRq()

        # Filter by TxnID (ORTxnQuery is the correct path for SalesReceiptQueryRq)
        if txn_id:
            sales_receipt_query_rq.ORTxnQuery.TxnIDList.Add(txn_id)

        # Filter by RefNumber
        elif ref_number:
            sales_receipt_query_rq.ORTxnQuery.RefNumberFilter.ORRefNumberFilter.RefNumberList.Add(ref_number)

        # Filter by modified date (sales receipts changed since this datetime)
        # Note: QBFC SetValue for dates requires TWO parameters: (date, useClientTimeZone)
        elif from_modified_date:
            date_filter = sales_receipt_query_rq.ORTxnQuery.TxnFilter.ORDateRangeFilter.ModifiedDateRangeFilter
            date_filter.FromModifiedDate.SetValue(_to_pywintypes_time(from_modified_date), False)

        # Filter by transaction date range
        elif date_range:
            from_date, to_date = date_range
            txn_filter = sales_receipt_query_rq.ORTxnQuery.TxnFilter.ORDateRangeFilter.TxnDateRangeFilter.ORTxnDateRangeFilter.TxnDateFilter
            txn_filter.FromTxnDate.SetValue(_to_pywintypes_time(from_date), False)
            txn_filter.ToTxnDate.SetValue(_to_pywintypes_time(to_date), False)

        # Include line items
        # Note: SalesReceiptQueryRq doesn't have IncludeLinkedTxns (unlike InvoiceQueryRq)
        # Sales receipts are immediate cash sales - payment is implicit in the receipt itself
        sales_receipt_query_rq.IncludeLineItems.SetValue(True)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def modify_sales_receipt(session_manager, sales_receipt_mod_data: Dict[str, Any]):
        """
        Modify sales receipt using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            sales_receipt_mod_data: Dict with keys: txn_id, edit_sequence, and optionally:
                                   memo, payment_method_ref (name like "Visa", "Cash", etc.)

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        sales_receipt_mod_rq = msg_set_rq.AppendSalesReceiptModRq()

        # Required: TxnID and EditSequence
        sales_receipt_mod_rq.TxnID.SetValue(sales_receipt_mod_data['txn_id'])
        sales_receipt_mod_rq.EditSequence.SetValue(sales_receipt_mod_data['edit_sequence'])

        # Optional: Memo
        if 'memo' in sales_receipt_mod_data:
            sales_receipt_mod_rq.Memo.SetValue(sales_receipt_mod_data['memo'])

        # Optional: Payment Method (by name - QB will look it up)
        if 'payment_method_ref' in sales_receipt_mod_data:
            sales_receipt_mod_rq.PaymentMethodRef.FullName.SetValue(sales_receipt_mod_data['payment_method_ref'])

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def add_charge(session_manager, charge_data: Dict[str, Any]):
        """
        Add statement charge using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            charge_data: Dict with keys: customer_ref, txn_date, ref_number,
                        item_ref, desc, amount, class_ref

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        charge_add_rq = msg_set_rq.AppendChargeAddRq()

        # Required: Customer reference
        charge_add_rq.CustomerRef.ListID.SetValue(charge_data['customer_ref'])

        # Optional: Transaction date (convert to pywintypes.Time)
        if 'txn_date' in charge_data:
            charge_add_rq.TxnDate.SetValue(_to_pywintypes_time(charge_data['txn_date']))

        # Optional: Reference number
        if 'ref_number' in charge_data:
            charge_add_rq.RefNumber.SetValue(charge_data['ref_number'])

        # Required: Item reference
        if 'item_ref' in charge_data:
            charge_add_rq.ItemRef.ListID.SetValue(charge_data['item_ref'])

        # Optional: Description
        if 'desc' in charge_data:
            charge_add_rq.Desc.SetValue(charge_data['desc'])

        # Optional: Quantity (defaults to 1)
        if 'quantity' in charge_data:
            charge_add_rq.Quantity.SetValue(charge_data['quantity'])

        # Optional: Rate (through ORRate)
        if 'rate' in charge_data:
            charge_add_rq.ORRate.Rate.SetValue(float(charge_data['rate']))

        # Optional: Amount
        if 'amount' in charge_data:
            charge_add_rq.Amount.SetValue(float(charge_data['amount']))

        # Optional: Class
        if 'class_ref' in charge_data:
            charge_add_rq.ClassRef.FullName.SetValue(charge_data['class_ref'])

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_charge(session_manager):
        """
        Query all statement charges using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object

        Returns:
            QBFC response set object

        Note:
            ChargeQueryRq doesn't support TxnID, RefNumber, or date filtering in QBFC.
            All charges are returned and must be filtered in Python.
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        charge_query_rq = msg_set_rq.AppendChargeQueryRq()

        # Include linked transactions (payments)
        charge_query_rq.IncludeLinkedTxns.SetValue(True)

        # Execute request without filters
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def modify_charge(session_manager, charge_mod_data: Dict[str, Any]):
        """
        Modify statement charge using QBFC.

        Note: Statement charges use Desc (Description) instead of Memo.

        Args:
            session_manager: QBFC SessionManager COM object
            charge_mod_data: Dict with keys: txn_id, edit_sequence, and optionally: desc

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        charge_mod_rq = msg_set_rq.AppendChargeModRq()

        # Required: TxnID and EditSequence
        charge_mod_rq.TxnID.SetValue(charge_mod_data['txn_id'])
        charge_mod_rq.EditSequence.SetValue(charge_mod_data['edit_sequence'])

        # Optional: Desc (statement charges use Desc instead of Memo)
        if 'desc' in charge_mod_data:
            charge_mod_rq.Desc.SetValue(charge_mod_data['desc'])

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_account(session_manager, account_type: Optional[str] = None):
        """
        Query accounts using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            account_type: Optional account type filter

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        account_query_rq = msg_set_rq.AppendAccountQueryRq()

        # NOTE: In QBFC, when using ORAccountListQuery you must choose ONE path:
        # - ListIDList: query specific accounts by ListID
        # - FullNameList: query specific accounts by name
        # - AccountListFilter: filter accounts by criteria
        #
        # When querying all accounts, don't use any filter - just execute the query.
        # The ActiveStatus filter seems to cause issues when not combined with
        # a proper account type filter, so we filter for active accounts in Python instead.

        # Filter by account type if specified
        if account_type:
            account_query_rq.ORAccountListQuery.AccountListFilter.ORAccountTypeFilter.AccountTypeList.Add(account_type)
            # Only active accounts when filtering (ENActiveStatus: 0=ActiveOnly)
            account_query_rq.ORAccountListQuery.AccountListFilter.ActiveStatus.SetValue(0)
        # else: Query all accounts without filter, filter in Python

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_customer(session_manager):
        """
        Query all active customers using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        customer_query_rq = msg_set_rq.AppendCustomerQueryRq()

        # Only active customers (ENActiveStatus: 0=ActiveOnly)
        customer_query_rq.ORCustomerListQuery.CustomerListFilter.ActiveStatus.SetValue(0)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_item(session_manager, item_type: Optional[str] = None):
        """
        Query items using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            item_type: Optional item type filter

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        item_query_rq = msg_set_rq.AppendItemQueryRq()

        # Note: ItemQueryRq doesn't support ActiveStatus filter directly
        # Active filtering is done in response mapping

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_terms(session_manager):
        """
        Query standard terms using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        terms_query_rq = msg_set_rq.AppendStandardTermsQueryRq()

        # Only active terms (ENActiveStatus: 0=ActiveOnly)
        terms_query_rq.ORListQuery.ListFilter.ActiveStatus.SetValue(0)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_class(session_manager):
        """
        Query classes using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        class_query_rq = msg_set_rq.AppendClassQueryRq()

        # Only active classes (ENActiveStatus: 0=ActiveOnly)
        class_query_rq.ORListQuery.ListFilter.ActiveStatus.SetValue(0)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def delete_transaction(session_manager, txn_del_type: str, txn_id: str):
        """
        Delete a transaction using QBFC.

        Args:
            session_manager: QBFC SessionManager COM object
            txn_del_type: Transaction type ("Invoice", "SalesReceipt", "Charge")
            txn_id: Transaction ID to delete

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        txn_del_rq = msg_set_rq.AppendTxnDelRq()

        # Set transaction type and ID
        txn_del_rq.TxnDelType.SetValue(txn_del_type)
        txn_del_rq.TxnID.SetValue(txn_id)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def receive_payment(session_manager, payment_data: Dict[str, Any]):
        """
        Create a ReceivePayment to apply against invoices/charges.

        TEMPORARY: For testing verification logic only - remove before shipping.

        Args:
            session_manager: QBFC SessionManager COM object
            payment_data: Dict with keys:
                - customer_ref: Customer ListID (required)
                - txn_date: Payment date
                - deposit_to_account_ref: Deposit account ListID
                - memo: Payment memo
                - applied_to_txn: List of {txn_id, payment_amount}

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        payment_rq = msg_set_rq.AppendReceivePaymentAddRq()

        # Required: Customer reference
        payment_rq.CustomerRef.ListID.SetValue(payment_data['customer_ref'])

        # Optional: Transaction date
        if 'txn_date' in payment_data:
            payment_rq.TxnDate.SetValue(_to_pywintypes_time(payment_data['txn_date']))

        # Optional: Deposit to account
        if 'deposit_to_account_ref' in payment_data:
            payment_rq.DepositToAccountRef.ListID.SetValue(payment_data['deposit_to_account_ref'])

        # Optional: Memo
        if 'memo' in payment_data:
            payment_rq.Memo.SetValue(payment_data['memo'])

        # Required: TotalAmount (sum of all applied payments)
        total_amount = sum(float(txn['payment_amount']) for txn in payment_data.get('applied_to_txn', []))
        payment_rq.TotalAmount.SetValue(total_amount)

        # Apply to transactions (invoices/charges)
        for txn in payment_data.get('applied_to_txn', []):
            applied = payment_rq.ORApplyPayment.AppliedToTxnAddList.Append()
            applied.TxnID.SetValue(txn['txn_id'])
            applied.PaymentAmount.SetValue(float(txn['payment_amount']))

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_receive_payment(session_manager, txn_id: str = None):
        """
        Query ReceivePayment transactions.

        Args:
            session_manager: QBFC SessionManager COM object
            txn_id: Optional TxnID to query specific payment

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        query_rq = msg_set_rq.AppendReceivePaymentQueryRq()

        if txn_id:
            query_rq.ORTxnQuery.TxnIDList.Add(txn_id)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    # =========================================================================
    # BATCH OPERATIONS - Query multiple items in a single request
    # =========================================================================

    @staticmethod
    def query_invoices_batch(session_manager, txn_ids: list):
        """
        Query multiple invoices in a single request.

        Args:
            session_manager: QBFC SessionManager COM object
            txn_ids: List of transaction IDs to query

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        invoice_query_rq = msg_set_rq.AppendInvoiceQueryRq()

        # Add all TxnIDs to the query
        for txn_id in txn_ids:
            invoice_query_rq.ORInvoiceQuery.TxnIDList.Add(txn_id)

        # Include line items and linked transactions
        invoice_query_rq.IncludeLineItems.SetValue(True)
        invoice_query_rq.IncludeLinkedTxns.SetValue(True)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_sales_receipts_batch(session_manager, txn_ids: list):
        """
        Query multiple sales receipts in a single request.

        Args:
            session_manager: QBFC SessionManager COM object
            txn_ids: List of transaction IDs to query

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        sales_receipt_query_rq = msg_set_rq.AppendSalesReceiptQueryRq()

        # Add all TxnIDs to the query
        for txn_id in txn_ids:
            sales_receipt_query_rq.ORTxnQuery.TxnIDList.Add(txn_id)

        # Include line items
        sales_receipt_query_rq.IncludeLineItems.SetValue(True)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def query_receive_payments_batch(session_manager, txn_ids: list):
        """
        Query multiple ReceivePayment transactions in a single request.

        Args:
            session_manager: QBFC SessionManager COM object
            txn_ids: List of transaction IDs to query

        Returns:
            QBFC response set object
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        query_rq = msg_set_rq.AppendReceivePaymentQueryRq()

        # Add all TxnIDs to the query
        for txn_id in txn_ids:
            query_rq.ORTxnQuery.TxnIDList.Add(txn_id)

        # Execute request
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    # =========================================================================
    # BATCH ADD OPERATIONS - Create multiple items in a single request
    # =========================================================================

    @staticmethod
    def add_invoices_batch(session_manager, invoice_data_list: list):
        """
        Add multiple invoices in a single request.

        Args:
            session_manager: QBFC SessionManager COM object
            invoice_data_list: List of invoice_data dicts (same format as add_invoice)

        Returns:
            QBFC response set object with one response per invoice
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        # Set OnError attribute for batch operations (1 = continue on error)
        msg_set_rq.Attributes.OnError = 1

        for invoice_data in invoice_data_list:
            invoice_add_rq = msg_set_rq.AppendInvoiceAddRq()

            # Required: Customer reference
            invoice_add_rq.CustomerRef.ListID.SetValue(invoice_data['customer_ref'])

            # Optional: Transaction date
            if 'txn_date' in invoice_data:
                invoice_add_rq.TxnDate.SetValue(_to_pywintypes_time(invoice_data['txn_date']))

            # Optional: Reference number
            if 'ref_number' in invoice_data:
                invoice_add_rq.RefNumber.SetValue(invoice_data['ref_number'])

            # Optional: Terms
            if 'terms_ref' in invoice_data:
                invoice_add_rq.TermsRef.ListID.SetValue(invoice_data['terms_ref'])

            # Optional: Due date
            if 'due_date' in invoice_data:
                invoice_add_rq.DueDate.SetValue(_to_pywintypes_time(invoice_data['due_date']))

            # Optional: Memo
            if 'memo' in invoice_data:
                invoice_add_rq.Memo.SetValue(invoice_data['memo'])

            # Optional: Deposit to account
            if 'deposit_to_account_ref' in invoice_data:
                invoice_add_rq.DepositToAccountRef.ListID.SetValue(invoice_data['deposit_to_account_ref'])

            # Optional: Class reference (transaction level)
            if 'class_ref' in invoice_data:
                invoice_add_rq.ClassRef.FullName.SetValue(invoice_data['class_ref'])

            # Add line items
            if 'line_items' in invoice_data:
                for line in invoice_data['line_items']:
                    line_add = invoice_add_rq.ORInvoiceLineAddList.Append().InvoiceLineAdd

                    if 'item_ref' in line:
                        line_add.ItemRef.ListID.SetValue(line['item_ref'])
                    if 'desc' in line:
                        line_add.Desc.SetValue(line['desc'])
                    if 'quantity' in line:
                        line_add.Quantity.SetValue(line['quantity'])
                    if 'amount' in line:
                        line_add.Amount.SetValue(float(line['amount']))
                    elif 'rate' in line:
                        try:
                            line_add.ORRatePriceLevel.Rate.SetValue(float(line['rate']))
                        except:
                            qty = line.get('quantity', 1)
                            line_add.Amount.SetValue(float(line['rate']) * float(qty))

        # Execute all requests
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def add_sales_receipts_batch(session_manager, sales_receipt_data_list: list):
        """
        Add multiple sales receipts in a single request.

        Args:
            session_manager: QBFC SessionManager COM object
            sales_receipt_data_list: List of sales_receipt_data dicts

        Returns:
            QBFC response set object with one response per sales receipt
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        # Set OnError attribute for batch operations (1 = continue on error)
        msg_set_rq.Attributes.OnError = 1

        for sales_receipt_data in sales_receipt_data_list:
            sales_receipt_add_rq = msg_set_rq.AppendSalesReceiptAddRq()

            # Required: Customer reference
            sales_receipt_add_rq.CustomerRef.ListID.SetValue(sales_receipt_data['customer_ref'])

            # Optional: Transaction date
            if 'txn_date' in sales_receipt_data:
                sales_receipt_add_rq.TxnDate.SetValue(_to_pywintypes_time(sales_receipt_data['txn_date']))

            # Optional: Reference number
            if 'ref_number' in sales_receipt_data:
                sales_receipt_add_rq.RefNumber.SetValue(sales_receipt_data['ref_number'])

            # Optional: Memo
            if 'memo' in sales_receipt_data:
                sales_receipt_add_rq.Memo.SetValue(sales_receipt_data['memo'])

            # Optional: Deposit to account
            if 'deposit_to_account_ref' in sales_receipt_data:
                sales_receipt_add_rq.DepositToAccountRef.ListID.SetValue(sales_receipt_data['deposit_to_account_ref'])

            # Optional: Class reference (transaction level)
            if 'class_ref' in sales_receipt_data:
                sales_receipt_add_rq.ClassRef.FullName.SetValue(sales_receipt_data['class_ref'])

            # Add line items
            if 'line_items' in sales_receipt_data:
                for line in sales_receipt_data['line_items']:
                    line_add = sales_receipt_add_rq.ORSalesReceiptLineAddList.Append().SalesReceiptLineAdd

                    if 'item_ref' in line:
                        line_add.ItemRef.ListID.SetValue(line['item_ref'])
                    if 'desc' in line:
                        line_add.Desc.SetValue(line['desc'])
                    if 'quantity' in line:
                        line_add.Quantity.SetValue(line['quantity'])
                    if 'rate' in line:
                        line_add.ORRatePriceLevel.Rate.SetValue(float(line['rate']))

        # Execute all requests
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set

    @staticmethod
    def add_charges_batch(session_manager, charge_data_list: list):
        """
        Add multiple statement charges in a single request.

        Args:
            session_manager: QBFC SessionManager COM object
            charge_data_list: List of charge_data dicts

        Returns:
            QBFC response set object with one response per charge
        """
        msg_set_rq = session_manager.CreateMsgSetRequest("US", 13, 0)
        # Set OnError attribute for batch operations (1 = continue on error)
        msg_set_rq.Attributes.OnError = 1

        for charge_data in charge_data_list:
            charge_add_rq = msg_set_rq.AppendChargeAddRq()

            # Required: Customer reference
            charge_add_rq.CustomerRef.ListID.SetValue(charge_data['customer_ref'])

            # Optional: Transaction date
            if 'txn_date' in charge_data:
                charge_add_rq.TxnDate.SetValue(_to_pywintypes_time(charge_data['txn_date']))

            # Optional: Reference number
            if 'ref_number' in charge_data:
                charge_add_rq.RefNumber.SetValue(charge_data['ref_number'])

            # Required: Item reference
            if 'item_ref' in charge_data:
                charge_add_rq.ItemRef.ListID.SetValue(charge_data['item_ref'])

            # Optional: Description
            if 'desc' in charge_data:
                charge_add_rq.Desc.SetValue(charge_data['desc'])

            # Optional: Quantity
            if 'quantity' in charge_data:
                charge_add_rq.Quantity.SetValue(charge_data['quantity'])

            # Optional: Rate
            if 'rate' in charge_data:
                charge_add_rq.ORRate.Rate.SetValue(float(charge_data['rate']))

            # Optional: Amount
            if 'amount' in charge_data:
                charge_add_rq.Amount.SetValue(float(charge_data['amount']))

            # Optional: Class
            if 'class_ref' in charge_data:
                charge_add_rq.ClassRef.FullName.SetValue(charge_data['class_ref'])

        # Execute all requests
        response_set = session_manager.DoRequests(msg_set_rq)
        return response_set
