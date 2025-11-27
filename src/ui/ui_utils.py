"""
UI utility functions for QuickBooks Desktop Test Tool.

Common UI helpers used across multiple tabs.
"""

import tkinter as tk
from tkinter import ttk


class SearchableCombobox(ttk.Frame):
    """
    An autocomplete widget with Entry for typing and dropdown Listbox for selection.

    Usage:
        combo = SearchableCombobox(parent, width=30)
        combo.set_values(['Option 1', 'Option 2', 'Option 3'])
        combo.pack()
    """

    def __init__(self, parent, width=30, **kwargs):
        """Initialize searchable combobox."""
        super().__init__(parent)
        self._all_values = []
        self._filtered_values = []
        self._last_valid_value = ""
        self._listbox_visible = False
        self._user_is_typing = False  # Track if user started typing after focus

        # Entry for typing
        self._entry = ttk.Entry(self, width=width)
        self._entry.pack(fill='x')

        # Bind entry events
        self._entry.bind('<KeyRelease>', self._on_keyrelease)
        self._entry.bind('<FocusIn>', self._show_listbox)
        self._entry.bind('<FocusOut>', self._on_focus_out)
        self._entry.bind('<Return>', self._select_current)
        self._entry.bind('<Down>', self._move_down)
        self._entry.bind('<Up>', self._move_up)
        self._entry.bind('<Escape>', self._hide_listbox)

        # Toplevel for dropdown listbox (appears below entry)
        self._popup = None
        self._listbox = None

    def _create_popup(self):
        """Create the dropdown popup with listbox."""
        if self._popup is not None:
            return

        self._popup = tk.Toplevel(self)
        self._popup.wm_overrideredirect(True)
        self._popup.wm_attributes('-topmost', True)

        # Listbox with scrollbar
        frame = ttk.Frame(self._popup)
        frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self._listbox = tk.Listbox(frame, height=8, exportselection=False,
                                    yscrollcommand=scrollbar.set)
        self._listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self._listbox.yview)

        self._listbox.bind('<ButtonRelease-1>', self._on_listbox_select)
        self._listbox.bind('<Double-Button-1>', self._on_listbox_select)

        # Bind global click to close dropdown when clicking outside
        self.winfo_toplevel().bind('<Button-1>', self._on_global_click, add='+')

        self._popup.withdraw()

    def _show_listbox(self, event=None):
        """Show the dropdown listbox with all values (filtering starts on typing)."""
        self._create_popup()

        # Only reset to all values if user hasn't started typing yet
        # (event=None means called programmatically, event present means FocusIn)
        if event is not None:
            # FocusIn event - reset to show all values
            self._user_is_typing = False
            self._filtered_values = self._all_values.copy()
            if self._listbox:
                self._listbox.delete(0, tk.END)
                for value in self._filtered_values[:50]:  # Limit to 50 items
                    self._listbox.insert(tk.END, value)

        if not self._filtered_values:
            self._hide_listbox()
            return

        # Position popup below entry
        x = self._entry.winfo_rootx()
        y = self._entry.winfo_rooty() + self._entry.winfo_height()
        width = self._entry.winfo_width()

        self._popup.wm_geometry(f"{width}x150+{x}+{y}")
        self._popup.deiconify()
        self._listbox_visible = True

    def _hide_listbox(self, event=None):
        """Hide the dropdown listbox."""
        if self._popup:
            self._popup.withdraw()
        self._listbox_visible = False

    def _on_global_click(self, event):
        """Handle clicks anywhere - hide dropdown if click is outside."""
        if not self._listbox_visible:
            return

        # Check if click is inside entry
        try:
            entry_x = self._entry.winfo_rootx()
            entry_y = self._entry.winfo_rooty()
            entry_w = self._entry.winfo_width()
            entry_h = self._entry.winfo_height()

            if (entry_x <= event.x_root <= entry_x + entry_w and
                entry_y <= event.y_root <= entry_y + entry_h):
                return  # Click inside entry

            # Check if click is inside popup
            if self._popup and self._popup.winfo_viewable():
                popup_x = self._popup.winfo_rootx()
                popup_y = self._popup.winfo_rooty()
                popup_w = self._popup.winfo_width()
                popup_h = self._popup.winfo_height()

                if (popup_x <= event.x_root <= popup_x + popup_w and
                    popup_y <= event.y_root <= popup_y + popup_h):
                    return  # Click inside popup

            # Click outside - hide dropdown
            self._hide_listbox()
        except tk.TclError:
            # Widget destroyed or other error
            pass

    def _update_listbox(self):
        """Update listbox with filtered values."""
        typed = self._entry.get().lower()

        if not typed:
            self._filtered_values = self._all_values.copy()
        else:
            self._filtered_values = [v for v in self._all_values if typed in v.lower()]

        if self._listbox:
            self._listbox.delete(0, tk.END)
            for value in self._filtered_values[:50]:  # Limit to 50 items
                self._listbox.insert(tk.END, value)

    def _on_keyrelease(self, event):
        """Handle key release in entry - start filtering when user types."""
        if event.keysym in ('Up', 'Down', 'Return', 'Escape', 'Tab',
                           'Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                           'Alt_L', 'Alt_R'):
            return

        # User started typing - now we filter
        self._user_is_typing = True
        self._update_listbox()
        if self._filtered_values and not self._listbox_visible:
            self._show_listbox()
        elif not self._filtered_values:
            self._hide_listbox()

    def _on_focus_out(self, event):
        """Handle focus leaving entry."""
        # Delay hide to allow listbox click to register
        self.after(150, self._check_focus_and_validate)

    def _check_focus_and_validate(self):
        """Check if focus moved outside widget and validate."""
        try:
            focused = self.focus_get()
        except (KeyError, tk.TclError):
            # Focus is on a widget we can't resolve - assume outside
            focused = None

        # Hide if focus is not on entry or listbox
        if focused != self._entry and (self._listbox is None or focused != self._listbox):
            self._hide_listbox()
            # Validate selection
            current = self._entry.get()
            if current in self._all_values:
                self._last_valid_value = current
            elif self._last_valid_value:
                self._entry.delete(0, tk.END)
                self._entry.insert(0, self._last_valid_value)

    def _move_down(self, event):
        """Move selection down in listbox."""
        if not self._listbox_visible:
            self._show_listbox()
            return
        if self._listbox:
            cur = self._listbox.curselection()
            if cur:
                idx = cur[0] + 1
                if idx < self._listbox.size():
                    self._listbox.selection_clear(0, tk.END)
                    self._listbox.selection_set(idx)
                    self._listbox.see(idx)
            elif self._listbox.size() > 0:
                self._listbox.selection_set(0)
        return 'break'

    def _move_up(self, event):
        """Move selection up in listbox."""
        if self._listbox and self._listbox_visible:
            cur = self._listbox.curselection()
            if cur and cur[0] > 0:
                idx = cur[0] - 1
                self._listbox.selection_clear(0, tk.END)
                self._listbox.selection_set(idx)
                self._listbox.see(idx)
        return 'break'

    def _select_current(self, event=None):
        """Select current listbox item."""
        if self._listbox and self._listbox_visible:
            cur = self._listbox.curselection()
            if cur:
                value = self._listbox.get(cur[0])
                self._entry.delete(0, tk.END)
                self._entry.insert(0, value)
                self._last_valid_value = value
        self._hide_listbox()
        return 'break'

    def _on_listbox_select(self, event):
        """Handle listbox item selection."""
        cur = self._listbox.curselection()
        if cur:
            value = self._listbox.get(cur[0])
            self._entry.delete(0, tk.END)
            self._entry.insert(0, value)
            self._last_valid_value = value
        self._hide_listbox()

    # Public interface (compatible with old Combobox API)
    def set_values(self, values):
        """Set the list of all available values."""
        self._all_values = values
        self._filtered_values = values.copy()

    def get(self):
        """Get current entry value."""
        return self._entry.get()

    def set(self, value):
        """Set entry value."""
        self._entry.delete(0, tk.END)
        self._entry.insert(0, value)
        if value in self._all_values:
            self._last_valid_value = value

    def current(self, index=None):
        """Get or set current selection by index."""
        if index is not None:
            if 0 <= index < len(self._all_values):
                value = self._all_values[index]
                self.set(value)
        else:
            try:
                return self._all_values.index(self.get())
            except ValueError:
                return -1

    def get_all_values(self):
        """Get the complete list of all values."""
        return self._all_values.copy()

    def config(self, **kwargs):
        """Configure widget."""
        if 'state' in kwargs:
            self._entry.config(state=kwargs['state'])
        super().config(**kwargs)

    def configure(self, **kwargs):
        """Configure widget (alias)."""
        self.config(**kwargs)


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
