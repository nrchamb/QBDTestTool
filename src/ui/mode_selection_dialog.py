"""
Mode Selection Dialog for QBD Test Tool.

Displays on startup to let user choose between Testing and Accounting modes.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class ModeSelectionDialog:
    """Startup dialog for selecting application mode."""

    def __init__(self, parent: Optional[tk.Tk] = None):
        """
        Create mode selection dialog.

        Args:
            parent: Optional parent window. If None, creates temporary root.
        """
        self.selected_mode: Optional[str] = None

        # Create dialog window
        if parent:
            self.dialog = tk.Toplevel(parent)
            self.dialog.transient(parent)
        else:
            # Create as standalone window
            self.dialog = tk.Tk()

        self.dialog.title("QBD Test Tool")
        self.dialog.resizable(False, False)

        # Set size and center on screen
        dialog_width = 450
        dialog_height = 280
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Build UI
        self._build_ui()

        # Handle close button (X)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

        # Make modal
        self.dialog.grab_set()

    def _build_ui(self):
        """Build dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="QBD Test Tool",
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack(pady=(0, 5))

        # Subtitle
        subtitle_label = ttk.Label(
            main_frame,
            text="Select your workflow mode:",
            font=('Segoe UI', 10)
        )
        subtitle_label.pack(pady=(0, 20))

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', expand=True)

        # Testing Mode button
        testing_frame = ttk.Frame(buttons_frame, relief='ridge', borderwidth=2)
        testing_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        testing_btn = tk.Frame(testing_frame, bg='#e8f4f8', cursor='hand2')
        testing_btn.pack(fill='both', expand=True, padx=2, pady=2)

        tk.Label(
            testing_btn,
            text="Testing Mode",
            font=('Segoe UI', 12, 'bold'),
            bg='#e8f4f8',
            fg='#1a5276'
        ).pack(pady=(15, 5))

        tk.Label(
            testing_btn,
            text="Generate random\ntest data for\nQuickBooks",
            font=('Segoe UI', 9),
            bg='#e8f4f8',
            fg='#2c3e50',
            justify='center'
        ).pack(pady=(0, 15))

        # Bind click events for testing button
        for widget in [testing_frame, testing_btn] + list(testing_btn.winfo_children()):
            widget.bind('<Button-1>', lambda e: self._select_mode('testing'))

        # Hover effects for testing
        def testing_enter(e):
            testing_btn.configure(bg='#d4edfc')
            for child in testing_btn.winfo_children():
                child.configure(bg='#d4edfc')

        def testing_leave(e):
            testing_btn.configure(bg='#e8f4f8')
            for child in testing_btn.winfo_children():
                child.configure(bg='#e8f4f8')

        testing_btn.bind('<Enter>', testing_enter)
        testing_btn.bind('<Leave>', testing_leave)

        # Accounting Mode button
        accounting_frame = ttk.Frame(buttons_frame, relief='ridge', borderwidth=2)
        accounting_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))

        accounting_btn = tk.Frame(accounting_frame, bg='#fef9e7', cursor='hand2')
        accounting_btn.pack(fill='both', expand=True, padx=2, pady=2)

        tk.Label(
            accounting_btn,
            text="Accounting Mode",
            font=('Segoe UI', 12, 'bold'),
            bg='#fef9e7',
            fg='#7d6608'
        ).pack(pady=(15, 5))

        tk.Label(
            accounting_btn,
            text="Paste customer\ndata and create\nin QuickBooks",
            font=('Segoe UI', 9),
            bg='#fef9e7',
            fg='#2c3e50',
            justify='center'
        ).pack(pady=(0, 15))

        # Bind click events for accounting button
        for widget in [accounting_frame, accounting_btn] + list(accounting_btn.winfo_children()):
            widget.bind('<Button-1>', lambda e: self._select_mode('accounting'))

        # Hover effects for accounting
        def accounting_enter(e):
            accounting_btn.configure(bg='#fcf3cf')
            for child in accounting_btn.winfo_children():
                child.configure(bg='#fcf3cf')

        def accounting_leave(e):
            accounting_btn.configure(bg='#fef9e7')
            for child in accounting_btn.winfo_children():
                child.configure(bg='#fef9e7')

        accounting_btn.bind('<Enter>', accounting_enter)
        accounting_btn.bind('<Leave>', accounting_leave)

    def _select_mode(self, mode: str):
        """Handle mode selection."""
        self.selected_mode = mode
        self.dialog.destroy()

    def _on_close(self):
        """Handle dialog close (X button)."""
        self.selected_mode = None
        self.dialog.destroy()

    def show(self) -> Optional[str]:
        """
        Show dialog and wait for user selection.

        Returns:
            Selected mode string ("testing" or "accounting"), or None if cancelled
        """
        self.dialog.wait_window()
        return self.selected_mode


def show_mode_selection() -> Optional[str]:
    """
    Convenience function to show mode selection dialog.

    Returns:
        Selected mode string ("testing" or "accounting"), or None if cancelled
    """
    dialog = ModeSelectionDialog()
    return dialog.show()
