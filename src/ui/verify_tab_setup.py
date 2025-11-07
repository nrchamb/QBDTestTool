"""
Verification Results tab setup for QuickBooks Desktop Test Tool.
"""

from tkinter import ttk
from .ui_constants import (
    SPACING_MD, TREEVIEW_HEIGHT_TALL,
    COLUMN_WIDTH_SM, COLUMN_WIDTH_MD, COLUMN_WIDTH_LG, COLUMN_WIDTH_XL, COLUMN_WIDTH_XXL
)


def setup_verify_tab(app):
    """
    Setup the Verification Results tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Results tree
    tree_frame = ttk.Frame(app.verify_tab, padding=SPACING_MD)
    tree_frame.pack(fill='both', expand=True)

    columns = ('Timestamp', 'Type', 'Txn Ref#', 'Result', 'Details')
    app.verify_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=TREEVIEW_HEIGHT_TALL)

    # Set column widths
    app.verify_tree.heading('Timestamp', text='Timestamp')
    app.verify_tree.column('Timestamp', width=COLUMN_WIDTH_XL)

    app.verify_tree.heading('Type', text='Type')
    app.verify_tree.column('Type', width=COLUMN_WIDTH_LG)

    app.verify_tree.heading('Txn Ref#', text='Txn Ref#')
    app.verify_tree.column('Txn Ref#', width=COLUMN_WIDTH_MD)

    app.verify_tree.heading('Result', text='Result')
    app.verify_tree.column('Result', width=COLUMN_WIDTH_SM)

    app.verify_tree.heading('Details', text='Details')
    app.verify_tree.column('Details', width=COLUMN_WIDTH_XXL)

    app.verify_tree.pack(fill='both', expand=True)

    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=app.verify_tree.yview)
    scrollbar.pack(side='right', fill='y')
    app.verify_tree.configure(yscrollcommand=scrollbar.set)
