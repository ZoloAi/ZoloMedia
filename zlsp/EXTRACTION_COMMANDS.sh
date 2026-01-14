#!/bin/bash
# Fast Completion: Extract remaining parser modules
# Run from: /Users/galnachshon/Projects/ZoloMedia/zlsp

set -e  # Exit on error

echo "🚀 Parser Modularization - Final Extraction"
echo "============================================"

PARSER_FILE="core/parser/parser.py"
MODULES_DIR="core/parser/parser_modules"

# ============================================================================
# STEP 1: Extract token_emitters.py (Lines 2441-2812 = 372 lines)
# ============================================================================
echo "📝 Step 1: Creating token_emitters.py..."

cat > "$MODULES_DIR/token_emitters.py" << 'EOMODULE'
"""
Token Emitters - Emit semantic tokens for values

Handles token emission for strings, arrays, objects, and special values.
"""

import re
from typing import Optional

from .validators import is_zpath_value, is_env_config_value, is_valid_number

# Forward reference for TokenEmitter type hints
TYPE_CHECKING = False
if TYPE_CHECKING:
    from .token_emitter import TokenEmitter

EOMODULE

# Extract emit_value_tokens, emit_string_with_escapes, emit_array_tokens, emit_object_tokens
sed -n '2441,2812p' "$PARSER_FILE" | sed 's/^def _/def /g' >> "$MODULES_DIR/token_emitters.py"

echo "✅ token_emitters.py created (372 lines)"

# ============================================================================
# STEP 2: Extract line_parsers.py (Multiple sections = ~1,200 lines total)
# ============================================================================
echo "📝 Step 2: Creating line_parsers.py..."

cat > "$MODULES_DIR/line_parsers.py" << 'EOMODULE'
"""
Line Parsers - Core parsing logic

The heart of the Zolo parser - processes lines and builds AST.
This is the largest module due to the complexity of line-by-line parsing.
"""

from typing import Any, Tuple, List, Optional

from ..type_hints import process_type_hints, TYPE_HINT_PATTERN
from ...exceptions import ZoloParseError
from ...lsp_types import TokenType, Diagnostic, Range, Position
from .multiline_collectors import (
    collect_str_hint_multiline,
    collect_dash_list,
    collect_bracket_array,
    collect_pipe_multiline,
    collect_triple_quote_multiline,
)
from .value_processors import detect_value_type
from .token_emitters import emit_value_tokens

# Forward reference
TYPE_CHECKING = False
if TYPE_CHECKING:
    from .token_emitter import TokenEmitter

EOMODULE

# Extract check_indentation_consistency (lines 659-725)
echo "  - Extracting check_indentation_consistency..."
sed -n '659,725p' "$PARSER_FILE" | sed 's/^def _/def /g' >> "$MODULES_DIR/line_parsers.py"

# Extract parse_lines_with_tokens (lines 1015-1812) - THE BEAST!
echo "  - Extracting parse_lines_with_tokens (798 lines)..."
sed -n '1015,1812p' "$PARSER_FILE" | sed 's/^def _/def /g' >> "$MODULES_DIR/line_parsers.py"

# Extract parse_lines (lines 1813-1944)
echo "  - Extracting parse_lines..."
sed -n '1813,1944p' "$PARSER_FILE" | sed 's/^def _/def /g' >> "$MODULES_DIR/line_parsers.py"

# Extract build_nested_dict (lines 2276-2394)
echo "  - Extracting build_nested_dict..."
sed -n '2276,2394p' "$PARSER_FILE" | sed 's/^def _/def /g' >> "$MODULES_DIR/line_parsers.py"

# Extract parse_root_key_value_pairs (lines 2395-2440)
echo "  - Extracting parse_root_key_value_pairs..."
sed -n '2395,2440p' "$PARSER_FILE" | sed 's/^def _/def /g' >> "$MODULES_DIR/line_parsers.py"

echo "✅ line_parsers.py created (~1,200 lines)"

# ============================================================================
# STEP 3: Update __init__.py with new exports
# ============================================================================
echo "📝 Step 3: Updating __init__.py..."

cat >> "$MODULES_DIR/__init__.py" << 'EOIMPORTS'

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
    'check_indentation_consistency',
    'parse_lines_with_tokens',
    'parse_lines',
    'build_nested_dict',
    'parse_root_key_value_pairs',
]
EOIMPORTS

echo "✅ __init__.py updated"

# ============================================================================
# STEP 4: Summary
# ============================================================================
echo ""
echo "✅ EXTRACTION COMPLETE!"
echo "======================"
echo ""
echo "Created modules:"
echo "  ✅ validators.py (190 lines)"
echo "  ✅ escape_processors.py (85 lines)"
echo "  ✅ value_processors.py (280 lines)"
echo "  ✅ multiline_collectors.py (400 lines)"
echo "  ✅ token_emitter.py (500 lines) - WITH BlockTracker!"
echo "  ✅ comment_processors.py (300 lines)"
echo "  ✅ token_emitters.py (372 lines)"
echo "  ✅ line_parsers.py (~1,200 lines)"
echo ""
echo "📊 Total: ~3,327 lines extracted into 8 focused modules"
echo ""
echo "🔄 Next Steps:"
echo "  1. Update main parser.py to import from parser_modules"
echo "  2. Remove extracted code from parser.py"
echo "  3. Run tests: python3 -m pytest tests/"
echo "  4. Fix any import issues"
echo "  5. Commit: git add -A && git commit -m 'refactor(parser): Complete modularization'"
echo ""
echo "📁 Check: ls -lh $MODULES_DIR"
echo ""
ls -lh "$MODULES_DIR"
