"""
Verification Results tab setup for QuickBooks Desktop Test Tool.
"""

from tkinter import ttk
from .ui_constants import (
    SPACING_MD, TREEVIEW_HEIGHT_TALL,
    COLUMN_WIDTH_SM, COLUMN_WIDTH_MD, COLUMN_WIDTH_LG, COLUMN_WIDTH_XL, COLUMN_WIDTH_XXL
)

# Color constants for result tags
COLOR_PASS = '#d4edda'      # Light green
COLOR_FAIL = '#f8d7da'      # Light red
COLOR_WARN = '#fff3cd'      # Light yellow
COLOR_INFO = '#d1ecf1'      # Light blue
COLOR_SKIPPED = '#e9ecef'   # Light grey


def setup_verify_tab(app):
    """
    Setup the Verification Results tab.

    Uses a hierarchical treeview where:
    - Parent rows: Transactions (Type, Ref#, Overall Result, Timestamp)
    - Child rows: Individual validation checks

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Results tree - hierarchical with tree column
    tree_frame = ttk.Frame(app.verify_tab, padding=SPACING_MD)
    tree_frame.pack(fill='both', expand=True)

    columns = ('Type', 'Ref#', 'Status', 'Result', 'Detail')
    app.verify_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=TREEVIEW_HEIGHT_TALL)

    # Tree column (for expand/collapse and check names)
    app.verify_tree.heading('#0', text='Check')
    app.verify_tree.column('#0', width=COLUMN_WIDTH_XL, stretch=False)

    # Set column widths
    app.verify_tree.heading('Type', text='Type')
    app.verify_tree.column('Type', width=COLUMN_WIDTH_MD, stretch=False)

    app.verify_tree.heading('Ref#', text='Ref#')
    app.verify_tree.column('Ref#', width=COLUMN_WIDTH_SM, stretch=False)

    app.verify_tree.heading('Status', text='Status')
    app.verify_tree.column('Status', width=COLUMN_WIDTH_SM, stretch=False)

    app.verify_tree.heading('Result', text='Result')
    app.verify_tree.column('Result', width=COLUMN_WIDTH_SM, stretch=False)

    app.verify_tree.heading('Detail', text='Detail')
    app.verify_tree.column('Detail', width=COLUMN_WIDTH_XXL, stretch=True)

    # Configure color tags for result rows
    app.verify_tree.tag_configure('pass', background=COLOR_PASS)
    app.verify_tree.tag_configure('fail', background=COLOR_FAIL)
    app.verify_tree.tag_configure('warn', background=COLOR_WARN)
    app.verify_tree.tag_configure('info', background=COLOR_INFO)
    app.verify_tree.tag_configure('skipped', background=COLOR_SKIPPED)
    app.verify_tree.tag_configure('tested', background='#ffffff')  # White for tested (neutral)

    app.verify_tree.pack(side='left', fill='both', expand=True)

    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=app.verify_tree.yview)
    scrollbar.pack(side='right', fill='y')
    app.verify_tree.configure(yscrollcommand=scrollbar.set)
