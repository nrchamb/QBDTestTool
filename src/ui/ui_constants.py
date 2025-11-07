"""
UI Constants for QuickBooks Desktop Test Tool

Centralized constants for spacing, fonts, widget sizing, and layout
to ensure visual consistency across the application.
"""

# ============================================================================
# SPACING CONSTANTS
# ============================================================================

# Padding and margin sizes
SPACING_XS = 2   # Extra-small: Tight spacing for sub-elements (e.g., address fields)
SPACING_SM = 5   # Small: Standard element spacing, button separation
SPACING_MD = 10  # Medium: Section spacing, button frame padding
SPACING_LG = 15  # Large: Major section dividers, content separation
SPACING_XL = 20  # Extra-large: Page/content padding, main container padding

# Common asymmetric padding patterns
PADDING_LABEL_RIGHT = (0, SPACING_MD)  # Label to entry field spacing
PADDING_SECTION_BOTTOM = (0, SPACING_LG)  # Bottom spacing for sections
PADDING_SECTION_TOP = (SPACING_LG, 0)  # Top spacing for sections


# ============================================================================
# FONT CONSTANTS
# ============================================================================

# Font family (using Tkinter default)
FONT_FAMILY = 'TkDefaultFont'

# Font specifications with semantic naming
FONT_BODY = (FONT_FAMILY, 9)  # Standard body text
FONT_BOLD = (FONT_FAMILY, 9, 'bold')  # Bold emphasis, section headers
FONT_HEADING = (FONT_FAMILY, 10, 'bold')  # Page titles, major headings
FONT_CAPTION = (FONT_FAMILY, 8)  # Help text, secondary information
FONT_CAPTION_BOLD = (FONT_FAMILY, 8, 'bold')  # Important captions, warnings


# ============================================================================
# WIDGET SIZING CONSTANTS
# ============================================================================

# Entry field widths
ENTRY_WIDTH_SHORT = 12   # Short inputs (e.g., zip code, quantity)
ENTRY_WIDTH_MEDIUM = 25  # Medium inputs (e.g., names, dates)
ENTRY_WIDTH_LONG = 50    # Long inputs (e.g., email, descriptions)

# Combobox widths
COMBOBOX_WIDTH_SHORT = 12   # Short dropdowns
COMBOBOX_WIDTH_MEDIUM = 30  # Medium dropdowns (e.g., customer selection)
COMBOBOX_WIDTH_LONG = 50    # Long dropdowns

# Spinbox widths
SPINBOX_WIDTH_SHORT = 5   # Narrow spinners (e.g., count, quantity)
SPINBOX_WIDTH_MEDIUM = 10  # Standard spinners

# Text widget dimensions
TEXT_WRAPLENGTH = 600  # Text wrapping width for labels
TEXT_HEIGHT_SHORT = 10  # Short text areas
TEXT_HEIGHT_MEDIUM = 20  # Medium text areas

# TreeView dimensions
TREEVIEW_HEIGHT_SHORT = 10  # Compact tree views
TREEVIEW_HEIGHT_TALL = 20   # Full-height tree views

# ScrolledText dimensions
SCROLLEDTEXT_HEIGHT = 10  # Log display height
SCROLLEDTEXT_WIDTH = 80   # Log display width


# ============================================================================
# TREEVIEW COLUMN WIDTHS
# ============================================================================

# Standard column width sizes
COLUMN_WIDTH_XS = 60   # Extra-small columns (icons, status)
COLUMN_WIDTH_SM = 80   # Small columns (IDs, counts)
COLUMN_WIDTH_MD = 100  # Medium columns (short text, numbers)
COLUMN_WIDTH_LG = 120  # Large columns (names, dates)
COLUMN_WIDTH_XL = 150  # Extra-large columns (long text)
COLUMN_WIDTH_XXL = 600  # Very wide columns (descriptions, details)


# ============================================================================
# LAYOUT PATTERNS
# ============================================================================

# Standard pack/grid configurations
PACK_FILL_EXPAND = {'fill': 'both', 'expand': True}  # Full container fill
PACK_FILL_X = {'fill': 'x'}  # Horizontal fill only
PACK_FILL_Y = {'fill': 'y'}  # Vertical fill only

# Grid sticky patterns
GRID_STICKY_W = 'w'  # Left-aligned
GRID_STICKY_E = 'e'  # Right-aligned
GRID_STICKY_EW = 'ew'  # Horizontal stretch
GRID_STICKY_NSEW = 'nsew'  # Full stretch
