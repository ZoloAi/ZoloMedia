"""
Zolo Constants

Defines constants used throughout the Zolo parser.
"""

# File extensions
FILE_EXT_ZOLO = ".zolo"
FILE_EXT_YAML = ".yaml"
FILE_EXT_YML = ".yml"
FILE_EXT_JSON = ".json"

# Type hint identifiers
TYPE_INT = "int"
TYPE_FLOAT = "float"
TYPE_BOOL = "bool"
TYPE_STR = "str"
TYPE_LIST = "list"
TYPE_DICT = "dict"
# TYPE_NULL removed - null now auto-detects (RFC 8259 primitive)
TYPE_RAW = "raw"
TYPE_DATE = "date"
TYPE_TIME = "time"
TYPE_URL = "url"
TYPE_PATH = "path"

# All supported type hints
SUPPORTED_TYPES = [
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_BOOL,
    TYPE_STR,
    TYPE_LIST,
    TYPE_DICT,
    # TYPE_NULL removed - null is now an auto-detected primitive
    TYPE_RAW,
    TYPE_DATE,
    TYPE_TIME,
    TYPE_URL,
    TYPE_PATH,
]

# Boolean true values
BOOL_TRUE_VALUES = ('true', 'yes', '1', 'on')

# Boolean false values
BOOL_FALSE_VALUES = ('false', 'no', '0', 'off')
