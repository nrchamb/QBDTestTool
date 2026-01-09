"""
Paste data parser for QuickBooks Desktop Test Tool.

Parses pasted customer data and maps fields to QuickBooks customer fields.
"""

import re
from typing import Dict, List, Tuple, Any, Optional


# Default field label mappings (label variations -> internal field name)
DEFAULT_FIELD_MAPPINGS = {
    # CID/Account Number
    'cid': 'account_number',
    'customer id': 'account_number',
    'account number': 'account_number',
    'account': 'account_number',
    'acct': 'account_number',

    # Company
    'company': 'company',
    'company name': 'company',
    'business': 'company',
    'business name': 'company',

    # Name fields
    'first name': 'first_name',
    'first': 'first_name',
    'firstname': 'first_name',
    'last name': 'last_name',
    'last': 'last_name',
    'lastname': 'last_name',
    'name': 'full_name',  # Will be split into first/last if possible

    # Contact
    'email': 'email',
    'email address': 'email',
    'e-mail': 'email',
    'phone': 'phone',
    'phone number': 'phone',
    'telephone': 'phone',
    'tel': 'phone',
    'mobile': 'phone',
    'cell': 'phone',
    'contact': 'phone',  # Often used for phone number

    # Address
    'address': 'bill_addr1',
    'address 1': 'bill_addr1',
    'addr': 'bill_addr1',
    'street': 'bill_addr1',
    'street address': 'bill_addr1',
    'city': 'bill_city',
    'state': 'bill_state',
    'st': 'bill_state',
    'zip': 'bill_zip',
    'zip code': 'bill_zip',
    'zipcode': 'bill_zip',
    'postal': 'bill_zip',
    'postal code': 'bill_zip',

    # Notes
    'notes': 'notes',
    'note': 'notes',
    'comments': 'notes',
    'comment': 'notes',

    # Fields to ignore (recognized but not mapped)
    'active': None,  # Status field - not needed
}


def parse_pasted_text(text: str, custom_mappings: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Parse pasted text and extract customer fields.

    Args:
        text: Raw pasted text
        custom_mappings: Optional user-defined label->field mappings

    Returns:
        Dictionary with:
            - success: bool - True if any fields were parsed
            - data: dict - Parsed field values {internal_field: value}
            - recognized: list - List of (label, field, value) tuples that were recognized
            - unrecognized: list - List of (label, value) tuples that weren't mapped
            - warnings: list - Warning messages
    """
    result = {
        'success': False,
        'data': {},
        'recognized': [],
        'unrecognized': [],
        'warnings': []
    }

    if not text or not text.strip():
        result['warnings'].append("No text provided")
        return result

    # Combine default mappings with custom mappings
    mappings = DEFAULT_FIELD_MAPPINGS.copy()
    if custom_mappings:
        mappings.update(custom_mappings)

    # Normalize input: convert tabs and other delimiters to newlines for single-line input
    normalized_text = _normalize_input(text)

    # Try line-based format first (most common)
    parsed_lines = _parse_line_format(normalized_text, mappings)

    if parsed_lines['recognized'] or parsed_lines['unrecognized']:
        # Line format worked
        result.update(parsed_lines)
    else:
        # Try mixed/inline format as fallback
        parsed_mixed = _parse_mixed_format(normalized_text, mappings)
        result.update(parsed_mixed)

    # Handle full_name -> first_name + last_name split
    if 'full_name' in result['data']:
        _split_full_name(result)

    # Set success flag
    result['success'] = bool(result['data'])

    return result


def _normalize_input(text: str) -> str:
    """
    Normalize input text by inserting newlines before known field labels.

    Handles single-line input where fields may have minimal or no spacing
    between them (e.g., "54321Company: Acme" or "John Last Name: Doe").

    Args:
        text: Raw input text

    Returns:
        Normalized text with fields on separate lines
    """
    # If text already has multiple lines with colons, assume it's already formatted
    lines = text.strip().split('\n')
    colon_lines = sum(1 for line in lines if ':' in line)
    if colon_lines >= 3:
        return text  # Already well-formatted multi-line

    # Build list of known labels to look for
    known_labels = list(DEFAULT_FIELD_MAPPINGS.keys())

    # Also add common labels that might appear but aren't mapped (for line splitting)
    extra_labels = ['iso', 'acct rep', 'region', 'status']
    all_labels = known_labels + [l for l in extra_labels if l not in known_labels]

    # Replace tabs and pipes first
    normalized = text.replace('\t', '\n').replace('|', '\n')

    # Find all label matches with their positions
    # Each match is (start_pos, end_pos, label_with_colon)
    matches = []
    for label in all_labels:
        escaped_label = re.escape(label)
        # Find label followed by optional space and colon
        # Use word boundary OR digit-to-letter boundary (for cases like "54321Company:")
        pattern = rf'(?i)(?:\b|(?<=\d)){escaped_label}\s*:'
        for m in re.finditer(pattern, normalized):
            matches.append((m.start(), m.end(), m.group()))

    # Sort by start position, then by length (longer first) to handle overlaps
    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    # Filter to keep only non-overlapping matches (prefer longer/earlier ones)
    filtered = []
    last_end = -1
    for start, end, label in matches:
        if start >= last_end:
            filtered.append(start)
            last_end = end
        elif start == filtered[-1] if filtered else False:
            # Same start position - keep the longer one (already sorted)
            pass

    # Insert newlines at the filtered positions (reverse order to preserve positions)
    result = list(normalized)
    for pos in sorted(filtered, reverse=True):
        if pos > 0:  # Don't insert at start
            result.insert(pos, '\n')

    normalized = ''.join(result)

    # Clean up: remove empty lines and excessive whitespace
    lines = [line.strip() for line in normalized.split('\n') if line.strip()]
    return '\n'.join(lines)


def _parse_line_format(text: str, mappings: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse text in "Label: Value" line format.

    Args:
        text: Raw text to parse
        mappings: Label to field mappings (lowercase label -> field name)

    Returns:
        Partial result dict with data, recognized, unrecognized
    """
    result = {
        'data': {},
        'recognized': [],
        'unrecognized': [],
        'warnings': []
    }

    # Split into lines and process each
    lines = text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Match "Label: Value" pattern
        # Use non-greedy match for label to handle colons in values
        match = re.match(r'^([^:]+?):\s*(.*)$', line)
        if not match:
            continue

        label = match.group(1).strip()
        value = match.group(2).strip()

        if not value:
            continue

        # Look up the field mapping (case-insensitive)
        label_lower = label.lower()
        field = mappings.get(label_lower)

        if field is None:
            # Explicitly ignored field (like 'active')
            continue
        elif field:
            # Recognized and mapped
            result['data'][field] = value
            result['recognized'].append((label, field, value))
        else:
            # Not in mappings - unrecognized
            result['unrecognized'].append((label, value))

    # Check for unrecognized labels not in mappings at all
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'^([^:]+?):\s*(.*)$', line)
        if match:
            label = match.group(1).strip()
            value = match.group(2).strip()
            label_lower = label.lower()

            # If label wasn't in mappings at all (not even as ignored)
            if label_lower not in mappings and value:
                # Check if already added to unrecognized
                if not any(u[0] == label for u in result['unrecognized']):
                    result['unrecognized'].append((label, value))

    return result


def _parse_mixed_format(text: str, mappings: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse text in mixed/inline format as fallback.
    Attempts to find known field patterns in unstructured text.

    Args:
        text: Raw text to parse
        mappings: Label to field mappings

    Returns:
        Partial result dict with data, recognized, unrecognized
    """
    result = {
        'data': {},
        'recognized': [],
        'unrecognized': [],
        'warnings': ['Used fallback parser - some fields may be incorrectly matched']
    }

    # For each mapping, try to find "Label: Value" anywhere in text
    for label, field in mappings.items():
        if not field:  # Skip ignored fields
            continue

        # Create pattern that matches label followed by colon and value
        # Value continues until next known label or end of line
        pattern = rf'(?i)\b{re.escape(label)}:\s*([^\n]+?)(?=\s+\w+:|$)'
        match = re.search(pattern, text)

        if match:
            value = match.group(1).strip()
            if value and field not in result['data']:
                result['data'][field] = value
                result['recognized'].append((label.title(), field, value))

    return result


def _split_full_name(result: Dict[str, Any]) -> None:
    """
    Split full_name into first_name and last_name if they're not already set.

    Args:
        result: Result dict to modify in place
    """
    full_name = result['data'].pop('full_name', '')

    if not full_name:
        return

    # Don't overwrite if already set
    if 'first_name' in result['data'] or 'last_name' in result['data']:
        result['warnings'].append(f"Full name '{full_name}' ignored - first/last already set")
        return

    # Simple split on space
    parts = full_name.split(None, 1)  # Split on first whitespace

    if len(parts) == 1:
        # Single name - assume it's the first name
        result['data']['first_name'] = parts[0]
        result['warnings'].append("Only one name provided - using as first name")
    else:
        result['data']['first_name'] = parts[0]
        result['data']['last_name'] = parts[1]


def get_available_fields() -> List[Tuple[str, str]]:
    """
    Get list of available fields that can be mapped to.

    Returns:
        List of (field_name, display_name) tuples
    """
    return [
        ('account_number', 'CID / Account Number'),
        ('company', 'Company Name'),
        ('first_name', 'First Name'),
        ('last_name', 'Last Name'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('bill_addr1', 'Address'),
        ('bill_city', 'City'),
        ('bill_state', 'State'),
        ('bill_zip', 'Zip Code'),
        ('notes', 'Notes'),
    ]


def get_field_display_name(field: str) -> str:
    """
    Get display name for a field.

    Args:
        field: Internal field name

    Returns:
        Human-readable display name
    """
    field_names = dict(get_available_fields())
    return field_names.get(field, field.replace('_', ' ').title())
