"""
Statement charge data generator for QuickBooks test data.
"""

from faker import Faker
from typing import Dict, Any, Optional
from datetime import datetime
import random

fake = Faker()


class ChargeGenerator:
    """Generate randomized statement charge data for QuickBooks testing."""

    @staticmethod
    def generate_statement_charge_data(
        customer_ref: str,
        amount: float = None,
        item_ref: str = None,
        txn_date: str = None,
        class_ref: str = None,
        use_auto_numbering: bool = True
    ) -> Dict[str, Any]:
        """
        Generate statement charge data.

        Args:
            customer_ref: Customer ListID
            amount: Charge amount (will randomize if not specified)
            item_ref: Item ListID (optional - QB may use default if not provided)
            txn_date: Transaction date (defaults to today)
            class_ref: Class ListID (optional)
            use_auto_numbering: If True, let QB auto-assign ref_number (default). If False, generate random.

        Returns:
            Dict suitable for QBXMLBuilder.build_charge_add()
        """
        if amount is None:
            amount = round(random.uniform(50, 500), 2)

        charge_data = {
            'customer_ref': customer_ref,
            'txn_date': txn_date if txn_date else datetime.now().strftime('%Y-%m-%d'),
            'amount': amount,
            # Note: Don't set quantity - use amount directly to avoid item type conflicts
            'desc': f"Test statement charge - {fake.sentence()}"
        }

        # Only add ref_number if not using auto-numbering (let QB assign sequential numbers)
        if not use_auto_numbering:
            charge_data['ref_number'] = f"CHG-{random.randint(10000, 99999)}"

        # Add item reference if provided
        if item_ref:
            charge_data['item_ref'] = item_ref

        # Add class reference if provided
        if class_ref:
            charge_data['class_ref'] = class_ref

        return charge_data
