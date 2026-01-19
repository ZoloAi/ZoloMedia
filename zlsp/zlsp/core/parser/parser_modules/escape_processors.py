"""
Escape Processors - Handle escape sequences

No dependencies, pure string processing.
"""


def decode_unicode_escapes(value: str) -> str:
    r"""
    Decode Unicode escape sequences to actual characters.
    
    Supports:
    - \uXXXX: 4-digit Unicode (BMP characters, U+0000 to U+FFFF)
    - \UXXXXXXXX: 4-8 digit Unicode (Supplementary planes, emojis, U+10000 to U+10FFFF)
    - Basic Unicode: copyright symbol, accented characters
    - Emoji (surrogate pairs): multi-byte emoji
    - Multiple escapes in one string
    
    This is the RFC 8259 compliant way to represent Unicode in .zolo files.
    The VSCode extension provides a zEmoji helper to make writing these easier.
    
    Args:
        value: String that may contain Unicode escape sequences
    
    Returns:
        String with Unicode escapes decoded to actual characters
    
    Examples:
        Copyright: \u00A9 → ©
        Café: \u00E9 → é
        Greater than: \u2265 → ≥
        Emoji: \U0001F4F1 → 📱
    """
    import re
    
    # First handle \UXXXXXXXX format (4-8 hex digits) for supplementary planes
    def replace_extended_unicode(match):
        hex_code = match.group(1)
        codepoint = int(hex_code, 16)
        try:
            return chr(codepoint)
        except (ValueError, OverflowError):
            return match.group(0)  # Return original if invalid
    
    value = re.sub(r'\\U([0-9A-Fa-f]{4,8})', replace_extended_unicode, value)
    
    # Then handle standard \uXXXX format (4 hex digits, BMP characters only)
    def replace_basic_unicode(match):
        hex_code = match.group(1)
        codepoint = int(hex_code, 16)
        try:
            return chr(codepoint)
        except (ValueError, OverflowError):
            return match.group(0)  # Return original if invalid
    
    value = re.sub(r'\\u([0-9A-Fa-f]{4})', replace_basic_unicode, value)
    
    # Handle remaining escape sequences (quotes, backslashes)
    # AFTER Unicode escapes to avoid breaking already-decoded characters
    value = value.replace('\\n', '\n')
    value = value.replace('\\t', '\t')
    value = value.replace('\\r', '\r')
    value = value.replace('\\\\', '\\')
    value = value.replace('\\"', '"')
    value = value.replace("\\'", "'")
    
    return value


def process_escape_sequences(value: str) -> str:
    r"""
    Process escape sequences in strings - PERMISSIVE approach.
    
    Known escapes (processed):
    - \n → newline
    - \t → tab
    - \r → carriage return (zDisplay terminal control!)
    - \\ → backslash
    - \" → double quote
    - \' → single quote
    
    Unknown escapes (preserved as-is):
    - \d, \w, \x → Kept literal for regex, Windows paths
    - Example: "C:\Windows" → "C:\\Windows" (works!)
    
    Args:
        value: String that may contain escape sequences
    
    Returns:
        String with escape sequences processed
    
    Note:
        \uXXXX and \UXXXXXXXX Unicode escapes are handled by decode_unicode_escapes()
        before this function is called. This function is now only used for
        non-Unicode escape sequences that weren't handled by decode_unicode_escapes.
    """
    # Note: Basic escapes (\n, \t, etc.) are now handled in decode_unicode_escapes()
    # This function is kept for backward compatibility and potential future use
    # Unknown escapes already preserved as-is (string-first!)
    return value
