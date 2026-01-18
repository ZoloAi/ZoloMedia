"""
Escape Processors - Handle escape sequences

No dependencies, pure string processing.
"""


def decode_unicode_escapes(value: str) -> str:
    r"""
    Decode Unicode escape sequences to actual characters.
    
    Supports:
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
        Copyright: escape code to symbol
        Café: escape code to accented e
        Emoji: surrogate pair to emoji character
    """
    # Use Python's unicode_escape codec to decode
    # This handles both basic Unicode and surrogate pairs correctly
    try:
        # Encode as bytes, then decode using unicode_escape codec
        # This properly handles surrogate pairs for emoji
        result = value.encode('utf-8').decode('unicode_escape')
        # Re-encode and decode to handle any remaining issues
        result = result.encode('utf-16', 'surrogatepass').decode('utf-16')
        return result
    except Exception:
        # If decoding fails, return original value
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
        \uXXXX Unicode escapes are handled by decode_unicode_escapes()
        before this function is called.
    """
    # Replace escape sequences (order matters - \\ must be after others)
    value = value.replace('\\n', '\n')
    value = value.replace('\\t', '\t')
    value = value.replace('\\r', '\r')
    value = value.replace('\\\\', '\\')
    value = value.replace('\\"', '"')
    value = value.replace("\\'", "'")
    
    # Unknown escapes already preserved as-is (string-first!)
    return value
