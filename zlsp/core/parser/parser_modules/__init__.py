"""
Parser Modules - Modular Parser Components

This package contains the modularized components of the Zolo parser.
Breaking the 3,420 line monolithic parser into focused, maintainable modules.

Architecture inspired by zKernel subsystem structure.
"""

# Re-export key components for easy imports
from .block_tracker import BlockTracker
from .type_hints import process_type_hints, TYPE_HINT_PATTERN
from .token_emitter import TokenEmitter
from .serializer import dumps as serialize_zolo
from .file_type_detector import (
    FileType,
    FileTypeDetector,
    detect_file_type,
    extract_component_name,
    get_file_info,
)
from .value_validators import ValueValidator, validate_special_value
from .validators import (
    validate_ascii_only,
    is_zpath_value,
    is_env_config_value,
    is_valid_number,
)
from .escape_processors import (
    decode_unicode_escapes,
    process_escape_sequences,
)
from .value_processors import (
    detect_value_type,
    parse_brace_object,
    parse_bracket_array,
    split_on_comma,
)
from .multiline_collectors import (
    collect_str_hint_multiline,
    collect_dash_list,
    collect_bracket_array,
    collect_pipe_multiline,
    collect_triple_quote_multiline,
)
from .comment_processors import (
    strip_comments_and_prepare_lines,
    strip_comments_and_prepare_lines_with_tokens,
)
from .token_emitters import (
    emit_value_tokens,
    emit_string_with_escapes,
    emit_array_tokens,
    emit_object_tokens,
)
from .line_parsers import (
    parse_lines_with_tokens,
    parse_lines,
    build_nested_dict,
    parse_root_key_value_pairs,
    check_indentation_consistency,
)

__all__ = [
    # Core class
    'TokenEmitter',
    # Validators
    'validate_ascii_only',
    'is_zpath_value',
    'is_env_config_value',
    'is_valid_number',
    # Escape processors
    'decode_unicode_escapes',
    'process_escape_sequences',
    # Value processors
    'detect_value_type',
    'parse_brace_object',
    'parse_bracket_array',
    'split_on_comma',
    # Multi-line collectors
    'collect_str_hint_multiline',
    'collect_dash_list',
    'collect_bracket_array',
    'collect_pipe_multiline',
    'collect_triple_quote_multiline',
    # Comment processors
    'strip_comments_and_prepare_lines',
    'strip_comments_and_prepare_lines_with_tokens',
    # Token emitters
    'emit_value_tokens',
    'emit_string_with_escapes',
    'emit_array_tokens',
    'emit_object_tokens',
    # Line parsers
    'parse_lines_with_tokens',
    'parse_lines',
    'build_nested_dict',
    'parse_root_key_value_pairs',
    'check_indentation_consistency',
]

# Comment processors
from .comment_processors import (
    strip_comments_and_prepare_lines,
    strip_comments_and_prepare_lines_with_tokens,
)

# Token emitters
from .token_emitters import (
    emit_value_tokens,
    emit_string_with_escapes,
    emit_array_tokens,
    emit_object_tokens,
)

# Line parsers
from .line_parsers import (
    check_indentation_consistency,
    parse_lines_with_tokens,
    parse_lines,
    build_nested_dict,
    parse_root_key_value_pairs,
)

# Update __all__
__all__ = [
    # Core classes and utilities
    'BlockTracker',
    'TokenEmitter',
    'process_type_hints',
    'TYPE_HINT_PATTERN',
    'serialize_zolo',
    # File type detection
    'FileType',
    'FileTypeDetector',
    'detect_file_type',
    'extract_component_name',
    'get_file_info',
    # Validators
    'validate_ascii_only',
    'is_zpath_value',
    'is_env_config_value',
    'is_valid_number',
    # Escape processors
    'decode_unicode_escapes',
    'process_escape_sequences',
    # Value processors
    'detect_value_type',
    'parse_brace_object',
    'parse_bracket_array',
    'split_on_comma',
    # Multi-line collectors
    'collect_str_hint_multiline',
    'collect_dash_list',
    'collect_bracket_array',
    'collect_pipe_multiline',
    'collect_triple_quote_multiline',
    # Comment processors
    'strip_comments_and_prepare_lines',
    'strip_comments_and_prepare_lines_with_tokens',
    # Token emitters
    'emit_value_tokens',
    'emit_string_with_escapes',
    'emit_array_tokens',
    'emit_object_tokens',
    # Line parsers
    'check_indentation_consistency',
    'parse_lines_with_tokens',
    'parse_lines',
    'build_nested_dict',
    'parse_root_key_value_pairs',
]
