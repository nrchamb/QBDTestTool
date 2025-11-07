import tkinter as tk
from tkinter import ttk, scrolledtext

from actions.ui_utility_actions import toggle_create_log
from config import AppConfig
from .setup_subtab_setup import setup_setup_subtab
from .customer_subtab_setup import setup_customer_subtab
from .transaction_subtab_setup import setup_transaction_subtab
from .ui_constants import (
    SPACING_SM, SPACING_MD, SCROLLEDTEXT_HEIGHT, SCROLLEDTEXT_WIDTH
)
from app_logging import log_create


def setup_create_tab(app):
    """
    Setup the Create Data tab with nested subtabs.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Initialize list to track customer comboboxes
    app.customer_combos = []

    # Main container
    main_container = ttk.Frame(app.create_tab)
    main_container.pack(fill='both', expand=True)

    # Collapse button header - at bottom, always visible
    log_header_frame = ttk.Frame(main_container)
    log_header_frame.pack(side='bottom', fill='x', padx=SPACING_MD, pady=SPACING_SM)

    # PanedWindow for content and log - using tk.PanedWindow for sashrelief support
    app.create_paned = tk.PanedWindow(main_container, orient='vertical', sashrelief='raised', sashwidth=8, bg='#d9d9d9')
    app.create_paned.pack(fill='both', expand=True)

    # Top pane: Nested notebook with subtabs
    notebook_frame = ttk.Frame(app.create_paned)
    app.create_paned.add(notebook_frame)

    # Create nested notebook for subtabs
    app.create_notebook = ttk.Notebook(notebook_frame)
    app.create_notebook.pack(fill='both', expand=True, padx=SPACING_SM, pady=SPACING_SM)

    # Create subtab frames
    app.setup_subtab = ttk.Frame(app.create_notebook)
    app.customer_subtab = ttk.Frame(app.create_notebook)
    app.transaction_subtab = ttk.Frame(app.create_notebook)

    # Add subtabs to notebook
    app.create_notebook.add(app.setup_subtab, text='Setup')
    app.create_notebook.add(app.customer_subtab, text='Customer')
    app.create_notebook.add(app.transaction_subtab, text='Transactions')

    # Setup each subtab
    setup_setup_subtab(app)
    setup_customer_subtab(app)
    setup_transaction_subtab(app)

    # Bottom pane: Activity log
    app.create_log_pane = ttk.Frame(app.create_paned)
    app.create_paned.add(app.create_log_pane)

    # Log content
    log_content_frame = ttk.Frame(app.create_log_pane, relief='sunken', borderwidth=1)
    log_content_frame.pack(fill='both', expand=True, padx=SPACING_MD, pady=SPACING_MD)

    app.create_log = scrolledtext.ScrolledText(
        log_content_frame,
        height=SCROLLEDTEXT_HEIGHT,
        width=SCROLLEDTEXT_WIDTH
    )
    app.create_log.pack(fill='both', expand=True, padx=2, pady=2)

    # Setup collapse button (in header frame created earlier)
    ttk.Label(log_header_frame, text="Activity Log", font=('TkDefaultFont', 9, 'bold')).pack(side='left')

    # Load saved UI state
    ui_state = AppConfig.get_ui_state()
    activity_log_collapsed = ui_state.get('activity_log_collapsed', False)

    app.create_log_collapsed = tk.BooleanVar(value=activity_log_collapsed)

    # Set initial button text based on state
    initial_btn_text = "▶ Show Log" if activity_log_collapsed else "▼ Hide Log"

    app.create_log_toggle_btn = ttk.Button(
        log_header_frame,
        text=initial_btn_text,
        command=lambda: toggle_create_log(app),
        width=12
    )
    app.create_log_toggle_btn.pack(side='right', padx=SPACING_SM)

    # Apply collapsed state if needed
    if activity_log_collapsed:
        app.create_paned.remove(app.create_log_pane)
    else:
        # Restore saved sash position or use 70/30 default split
        saved_sash_pos = ui_state.get('create_log_sash_pos')

        def set_sash_position():
            try:
                paned_height = app.create_paned.winfo_height()
                # Only set if we have a valid height (>100 pixels)
                if paned_height > 100:
                    if saved_sash_pos is not None:
                        # Use saved position
                        app.create_paned.sash_place(0, 0, saved_sash_pos)
                        print(f"Restored create log sash: height={paned_height}, pos={saved_sash_pos}")
                    else:
                        # Use 70/30 default
                        default_pos = int(paned_height * 0.7)
                        app.create_paned.sash_place(0, 0, default_pos)
                        print(f"Set create log sash (default): height={paned_height}, pos={default_pos}")
                else:
                    print(f"Skipped create log sash: height too small ({paned_height})")
            except Exception as e:
                print(f"Error setting create log sash position: {e}")

        app.root.after(200, set_sash_position)

    # Add welcome message with instructions
    log_create(app, "=== QBD Test Tool Ready ===")
    log_create(app, "IMPORTANT: QuickBooks Desktop must be running with a company file open.")
    log_create(app, "You may be prompted to authorize this application on first connection.")
    log_create(app, "")
