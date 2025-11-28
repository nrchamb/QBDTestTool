"""
Sales receipt data generator for QuickBooks test data.
"""

from faker import Faker
from typing import Dict, Any, Optional
from datetime import datetime
import random

fake = Faker()


class SalesReceiptGenerator:
    """Generate randomized sales receipt data for QuickBooks testing."""

    @staticmethod
    def generate_sales_receipt_data(
        customer_ref: str,
        num_line_items: int = None,
        item_refs: list = None,
        total_amount: float = None,
        txn_date: str = None,
        class_ref: str = None,
        use_auto_numbering: bool = True
    ) -> Dict[str, Any]:
        """
        Generate sales receipt data.

        Args:
            customer_ref: Customer ListID
            num_line_items: Number of line items (random 1-5 if not specified)
            item_refs: List of item ListIDs to use (will use placeholders if not provided)
            total_amount: Target total amount (will randomize if not specified)
            txn_date: Transaction date (defaults to today)
            class_ref: Class ListID (optional, applied to all line items)
            use_auto_numbering: If True, let QB auto-assign ref_number (default). If False, generate random.

        Returns:
            Dict suitable for QBXMLBuilder.build_sales_receipt_add()

        Note:
            If item_refs is None, you'll need to query items from QB first,
            or use service items that exist in the test company file.
        """
        if num_line_items is None:
            num_line_items = random.randint(1, 5)

        if total_amount is None:
            total_amount = round(random.uniform(100, 5000), 2)

        # Generate line items
        line_items = []
        remaining_amount = total_amount

        for i in range(num_line_items):
            # Last item gets remaining amount, others get random portion
            if i == num_line_items - 1:
                line_amount = round(remaining_amount, 2)  # Ensure proper rounding
            else:
                line_amount = round(remaining_amount * random.uniform(0.2, 0.5), 2)
                remaining_amount -= line_amount

            quantity = random.randint(1, 10)
            rate = round(line_amount / quantity, 2)

            # Use rate only - let QB calculate amount (avoids "Invalid Amount format" errors)
            line_item = {
                'desc': fake.catch_phrase(),
                'quantity': quantity,
                'rate': rate
            }

            # Add item reference if provided
            if item_refs and i < len(item_refs):
                line_item['item_ref'] = item_refs[i]

            line_items.append(line_item)

        sales_receipt_data = {
            'customer_ref': customer_ref,
            'txn_date': txn_date if txn_date else datetime.now().strftime('%Y-%m-%d'),
            'line_items': line_items,
            'memo': f"Test sales receipt - {fake.sentence()}"
        }

        # Only add ref_number if not using auto-numbering (let QB assign sequential numbers)
        if not use_auto_numbering:
            sales_receipt_data['ref_number'] = f"SR-{random.randint(10000, 99999)}"

        # Add optional class reference (transaction level)
        if class_ref:
            sales_receipt_data['class_ref'] = class_ref

        return sales_receipt_data
