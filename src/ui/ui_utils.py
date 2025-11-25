"""
UI utility functions for QuickBooks Desktop Test Tool.

Common UI helpers used across multiple tabs.
"""

import tkinter as tk
from tkinter import ttk


class SearchableCombobox(ttk.Combobox):
    """
    A Combobox that filters its values based on user input.

    Usage:
        combo = SearchableCombobox(parent, width=30)
        combo.set_values(['Option 1', 'Option 2', 'Option 3'])
        combo.pack()
    """

    def __init__(self, parent, **kwargs):
        """Initialize searchable combobox."""
        super().__init__(parent, **kwargs)
        self._all_values = []
        self._last_valid_value = ""

        # Bind events for filtering
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<<ComboboxSelected>>', self._on_select)

    def set_values(self, values):
        """Set the list of all available values."""
        self._all_values = values
        self['values'] = values

    def _on_keyrelease(self, event):
        """Filter combobox values based on current input."""
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Tab',
                           'Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                           'Alt_L', 'Alt_R', 'Escape'):
            return

        typed_value = self.get().lower()
        if not typed_value:
            self['values'] = self._all_values
        else:
            filtered = [v for v in self._all_values if typed_value in v.lower()]
            self['values'] = filtered

        if filtered:
            self.event_generate('<Down>')

    def _on_focus_out(self, event):
        """Validate selection when focus leaves the combobox."""
        current = self.get()
        if current in self._all_values:
            self._last_valid_value = current
        else:
            self.set(self._last_valid_value if self._last_valid_value else '')

    def _on_select(self, event):
        """Handle selection from dropdown."""
        self._last_valid_value = self.get()
        self['values'] = self._all_values

    def current(self, index=None):
        """Get or set current selection by index."""
        if index is not None:
            if 0 <= index < len(self._all_values):
                value = self._all_values[index]
                self.set(value)
                self._last_valid_value = value
        else:
            try:
                return self._all_values.index(self.get())
            except ValueError:
                return -1

    def get_all_values(self):
        """Get the complete list of all values."""
        return self._all_values.copy()


def create_scrollable_frame(parent):
    """
    Create a scrollable frame with canvas and scrollbar.

    Args:
        parent: Parent widget

    Returns:
        Tuple of (canvas, scrollbar, scrollable_frame)
    """
    # Create canvas and scrollbar
    canvas = tk.Canvas(parent, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    # Configure scrolling
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Mousewheel binding for smooth scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # Bind mousewheel only when mouse is over this canvas
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    return canvas, scrollbar, scrollable_frame
