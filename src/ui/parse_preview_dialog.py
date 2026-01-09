"""
Parse Preview Dialog for customer data paste feature.

Shows recognized and unrecognized fields with ability to map new labels.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, List, Tuple

from actions.paste_parser import get_available_fields, get_field_display_name
from config import AppConfig


class ParsePreviewDialog:
    """Dialog for previewing parsed customer data and mapping unknown fields."""

    def __init__(self, parent, parse_result: Dict[str, Any]):
        """
        Create parse preview dialog.

        Args:
            parent: Parent tkinter window
            parse_result: Result from paste_parser.parse_pasted_text()
        """
        self.parent = parent
        self.parse_result = parse_result
        self.result_data = None  # Will hold final data if user clicks Apply
        self.mappings_to_save = {}  # New mappings to save {label: field}

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Parse Preview")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self.dialog.geometry("700x500")
        self._center_dialog()

        # Build UI
        self._build_ui()

        # Handle close button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()

        dialog_w = 700
        dialog_h = 500

        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2

        self.dialog.geometry(f"{dialog_w}x{dialog_h}+{x}+{y}")

    def _build_ui(self):
        """Build dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill='both', expand=True)

        # Two-column layout
        columns_frame = ttk.Frame(main_frame)
        columns_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Left column: Recognized fields
        left_frame = ttk.LabelFrame(columns_frame, text="Recognized Fields", padding=5)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        self.recognized_tree = ttk.Treeview(
            left_frame,
            columns=('field', 'value'),
            show='headings',
            height=12
        )
        self.recognized_tree.heading('field', text='Field')
        self.recognized_tree.heading('value', text='Value')
        self.recognized_tree.column('field', width=120)
        self.recognized_tree.column('value', width=180)
        self.recognized_tree.pack(fill='both', expand=True)

        # Populate recognized fields
        for label, field, value in self.parse_result.get('recognized', []):
            display_name = get_field_display_name(field)
            self.recognized_tree.insert('', 'end', values=(display_name, value))

        # Show count in frame title
        recognized_count = len(self.parse_result.get('recognized', []))
        left_frame.config(text=f"Recognized Fields ({recognized_count})")

        # Right column: Unrecognized fields
        right_frame = ttk.LabelFrame(columns_frame, text="Unrecognized Fields", padding=5)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Get available fields for dropdown
        self.available_fields = get_available_fields()
        field_options = ['(Ignore)'] + [name for _, name in self.available_fields]

        # Create mapping widgets for each unrecognized field
        self.mapping_vars = {}  # {label: StringVar}
        unrecognized = self.parse_result.get('unrecognized', [])

        # Use a simple scrollable frame
        canvas = tk.Canvas(right_frame, highlightthickness=0, width=280)
        scrollbar = ttk.Scrollbar(right_frame, orient='vertical', command=canvas.yview)
        self.unrecognized_inner = ttk.Frame(canvas)

        self.unrecognized_inner.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas_window = canvas.create_window((0, 0), window=self.unrecognized_inner, anchor='nw', width=270)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        for label, value in unrecognized:
            row_frame = ttk.Frame(self.unrecognized_inner)
            row_frame.pack(fill='x', pady=3, padx=2)

            # Label (top)
            ttk.Label(row_frame, text=f"{label}:", font=('TkDefaultFont', 9, 'bold')).pack(anchor='w')

            # Value (middle)
            value_display = value[:40] + ('...' if len(value) > 40 else '')
            ttk.Label(row_frame, text=value_display, foreground='gray').pack(anchor='w')

            # Mapping dropdown (bottom)
            var = tk.StringVar(value='(Ignore)')
            self.mapping_vars[label] = var
            combo = ttk.Combobox(row_frame, textvariable=var, values=field_options, width=22, state='readonly')
            combo.pack(anchor='w', pady=(2, 5))

        # Show count
        unrecognized_count = len(unrecognized)
        right_frame.config(text=f"Unrecognized Fields ({unrecognized_count})")

        # Warnings section (if any)
        warnings = self.parse_result.get('warnings', [])
        if warnings:
            warnings_frame = ttk.LabelFrame(main_frame, text="Warnings", padding=5)
            warnings_frame.pack(fill='x', pady=(0, 10))
            for warning in warnings:
                ttk.Label(warnings_frame, text=f"  {warning}", foreground='orange').pack(anchor='w')

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')

        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side='left')

        # Save Mapping button (only show if there are unrecognized fields)
        if unrecognized:
            ttk.Button(
                button_frame,
                text="Save Mappings",
                command=self._on_save_mappings
            ).pack(side='left', padx=10)

        ttk.Button(
            button_frame,
            text="Apply to Form",
            command=self._on_apply
        ).pack(side='right')

    def _on_cancel(self):
        """Handle cancel/close."""
        self.result_data = None
        self.dialog.destroy()

    def _on_save_mappings(self):
        """Save user-defined mappings to config."""
        saved_count = 0

        for label, var in self.mapping_vars.items():
            selected = var.get()
            if selected and selected != '(Ignore)':
                # Find field name from display name
                field_name = None
                for field, display in self.available_fields:
                    if display == selected:
                        field_name = field
                        break

                if field_name:
                    AppConfig.save_custom_field_mapping(label, field_name)
                    self.mappings_to_save[label] = field_name
                    saved_count += 1

        if saved_count > 0:
            # Show confirmation
            from tkinter import messagebox
            messagebox.showinfo(
                "Mappings Saved",
                f"Saved {saved_count} custom mapping(s).\n\nThese will be used automatically for future pastes."
            )

    def _on_apply(self):
        """Apply parsed data and close dialog."""
        # Start with recognized data
        self.result_data = self.parse_result.get('data', {}).copy()

        # Add any newly mapped fields
        unrecognized = self.parse_result.get('unrecognized', [])
        unrecognized_dict = {label: value for label, value in unrecognized}

        for label, var in self.mapping_vars.items():
            selected = var.get()
            if selected and selected != '(Ignore)':
                # Find field name from display name
                field_name = None
                for field, display in self.available_fields:
                    if display == selected:
                        field_name = field
                        break

                if field_name and label in unrecognized_dict:
                    self.result_data[field_name] = unrecognized_dict[label]

        self.dialog.destroy()

    def show(self) -> Optional[Dict[str, Any]]:
        """
        Show dialog and wait for user action.

        Returns:
            Parsed data dict if user clicked Apply, None if cancelled
        """
        self.dialog.wait_window()
        return self.result_data
