"""
Splash screen for QBD Test Tool startup.

Provides immediate visual feedback while the application loads.
"""

import tkinter as tk


class SplashScreen:
    """Lightweight splash screen shown during app startup."""

    def __init__(self):
        """Create and display the splash screen."""
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # No window decorations

        # Window size
        width = 320
        height = 120

        # Center on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Style
        self.root.configure(bg='#2c3e50')

        # Add a subtle border effect
        border_frame = tk.Frame(self.root, bg='#34495e', padx=2, pady=2)
        border_frame.pack(fill='both', expand=True)

        content_frame = tk.Frame(border_frame, bg='#2c3e50')
        content_frame.pack(fill='both', expand=True)

        # App title
        title_label = tk.Label(
            content_frame,
            text="QBD Test Tool",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=(20, 10))

        # Status message
        self.status_label = tk.Label(
            content_frame,
            text="Loading...",
            font=('Segoe UI', 10),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        self.status_label.pack(pady=(0, 20))

        # Make sure window is on top
        self.root.attributes('-topmost', True)

        # Force display update
        self.root.update()

    def update_status(self, message: str):
        """
        Update the loading status message.

        Args:
            message: Status message to display
        """
        self.status_label.config(text=message)
        self.root.update()

    def close(self):
        """Close the splash screen and destroy the temporary root."""
        self.root.destroy()


def show_splash() -> SplashScreen:
    """
    Show the splash screen.

    Returns:
        SplashScreen instance (call .close() when done)
    """
    return SplashScreen()
