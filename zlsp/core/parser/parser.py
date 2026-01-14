"""
Zolo Parser - Public API and Orchestration

Main parser module with public API (load, loads, dump, dumps, tokenize).
All implementation delegated to modular components in parser_modules/.

This file is THIN - it only orchestrates, doesn't implement.
"""

import json
from pathlib import Path
from typing import Any, Union, Optional, IO

import yaml

# Import from modular components
from .parser_modules import (
    # Core classes
    TokenEmitter,
    process_type_hints,
    # Comment processing
    strip_comments_and_prepare_lines,
    strip_comments_and_prepare_lines_with_tokens,
    # Line parsing
    check_indentation_consistency,
    parse_lines,
    parse_lines_with_tokens,
)

# Import constants
from .constants import FILE_EXT_ZOLO, FILE_EXT_JSON

# Import exceptions
from ..exceptions import ZoloParseError, ZoloDumpError

# Import types
from ..lsp_types import ParseResult


# ============================================================================
# PUBLIC API - Entry points for users
# ============================================================================

def tokenize(content: str, filename: Optional[str] = None) -> ParseResult:
    """
    Parse .zolo content and return both parsed data and semantic tokens for LSP.

    This is the primary entry point for the Language Server Protocol to get
    semantic highlighting information along with parsed data.

    Args:
        content: Raw .zolo file content
        filename: Optional filename for context-aware tokenization (e.g., zUI files)

    Returns:
        ParseResult with data, tokens, and any errors

    Examples:
        >>> result = tokenize("port: 8080\\nhost: localhost")
        >>> result.data
        {'port': 8080.0, 'host': 'localhost'}
        >>> result.tokens
        [SemanticToken(...), SemanticToken(...), ...]
    """
    emitter = TokenEmitter(content, filename=filename)
    errors = []

    try:
        # Parse with token emission
        data = _parse_zolo_content_with_tokens(content, emitter)
        return ParseResult(
            data=data,
            tokens=emitter.get_tokens(),
            errors=errors,
            diagnostics=emitter.diagnostics
        )
    except ZoloParseError as e:
        # Still return tokens even if parse failed
        errors.append(str(e))
        return ParseResult(
            data=None,
            tokens=emitter.get_tokens(),
            errors=errors,
            diagnostics=emitter.diagnostics
        )


def load(fp: Union[str, Path, IO], file_extension: Optional[str] = None) -> Any:
    """
    Load data from a .zolo file (or compatible format).

    Args:
        fp: File path (str/Path) or file-like object
        file_extension: Optional file extension override (.zolo, .yaml, .json)
                       If None, will detect from file path or default to .zolo

    Returns:
        Parsed data (dict, list, or scalar)

    Raises:
        ZoloParseError: If parsing fails
        FileNotFoundError: If file doesn't exist

    Examples:
        >>> # Load .zolo file (string-first)
        >>> data = zolo.load('config.zolo')

        >>> # Load .yaml file (native types)
        >>> data = zolo.load('config.yaml')

        >>> # Load with explicit extension
        >>> data = zolo.load('config.txt', file_extension='.zolo')
    """
    # Handle file path vs file-like object
    if isinstance(fp, (str, Path)):
        file_path = Path(fp)

        # Detect file extension if not provided
        if file_extension is None:
            file_extension = file_path.suffix.lower()
            if not file_extension:
                file_extension = FILE_EXT_ZOLO  # Default to .zolo

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File not found: {file_path}") from exc
        except Exception as e:
            raise ZoloParseError(f"Error reading file {file_path}: {e}") from e
    else:
        # File-like object
        try:
            content = fp.read()
        except Exception as e:
            raise ZoloParseError(f"Error reading from file object: {e}") from e

        # Try to detect extension from file name
        if file_extension is None and hasattr(fp, 'name'):
            file_extension = Path(fp.name).suffix.lower()
        if not file_extension:
            file_extension = FILE_EXT_ZOLO  # Default to .zolo

    # Parse content
    return loads(content, file_extension=file_extension)


def loads(s: str, file_extension: Optional[str] = None) -> Any:
    """
    Load data from a .zolo string (or compatible format).

    Args:
        s: String content to parse
        file_extension: Optional file extension hint (.zolo, .yaml, .json)
                       Defaults to .zolo if not provided

    Returns:
        Parsed data (dict, list, or scalar)

    Raises:
        ZoloParseError: If parsing fails

    Examples:
        >>> # Parse .zolo string (string-first)
        >>> data = zolo.loads('port: 8080')
        {'port': '8080'}  # String by default

        >>> # Parse with type hint
        >>> data = zolo.loads('port(int): 8080')
        {'port': 8080}  # Integer via type hint

        >>> # Parse .yaml string (native types)
        >>> data = zolo.loads('port: 8080', file_extension='.yaml')
        {'port': 8080}  # Integer via YAML
    """
    if not s or not s.strip():
        return None

    # Default to .zolo if not specified
    if file_extension is None:
        file_extension = FILE_EXT_ZOLO

    # Normalize extension
    file_extension = file_extension.lower()
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension

    # Determine if string-first should be applied
    # .zolo files now use RFC 8259 type detection (like JSON)
    # string_first = False means: respect native types (int, float, bool, null)
    # Only YAML files (.yaml/.yml) would use string_first if we wanted that
    string_first = False

    # Parse based on format
    try:
        if file_extension == FILE_EXT_JSON:
            # Parse as JSON
            parsed = json.loads(s)
        elif file_extension == FILE_EXT_ZOLO:
            # Custom .zolo parser (no YAML quirks)
            parsed = _parse_zolo_content(s)
        else:
            # Parse as YAML (for .yaml, .yml files)
            parsed = yaml.safe_load(s)

        # Process type hints
        parsed = process_type_hints(parsed, string_first=string_first)

        return parsed

    except yaml.YAMLError as e:
        raise ZoloParseError(f"YAML parsing error: {e}") from e
    except json.JSONDecodeError as e:
        raise ZoloParseError(f"JSON parsing error: {e}") from e
    except Exception as e:
        raise ZoloParseError(f"Parsing error: {e}") from e


def dump(data: Any, fp: Union[str, Path, IO], file_extension: Optional[str] = None, **kwargs) -> None:
    """
    Dump data to a .zolo file (or compatible format).

    Args:
        data: Data to serialize (dict, list, or scalar)
        fp: File path (str/Path) or file-like object
        file_extension: Optional file extension override (.zolo, .yaml, .json)
        **kwargs: Format-specific options (indent, etc.)

    Raises:
        ZoloDumpError: If serialization fails

    Examples:
        >>> data = {'port': 8080, 'host': 'localhost'}
        >>> zolo.dump(data, 'config.zolo')
    """
    # Serialize to string
    content = dumps(data, file_extension=file_extension, **kwargs)

    # Write to file
    if isinstance(fp, (str, Path)):
        file_path = Path(fp)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise ZoloDumpError(f"Error writing file {file_path}: {e}") from e
    else:
        # File-like object
        try:
            fp.write(content)
        except Exception as e:
            raise ZoloDumpError(f"Error writing to file object: {e}") from e


def dumps(data: Any, file_extension: Optional[str] = None, **kwargs) -> str:
    """
    Dump data to a .zolo string (or compatible format).

    Args:
        data: Data to serialize (dict, list, or scalar)
        file_extension: Optional file extension hint (.zolo, .yaml, .json)
        **kwargs: Format-specific options (indent, etc.)

    Returns:
        Serialized string

    Raises:
        ZoloDumpError: If serialization fails

    Examples:
        >>> data = {'port': 8080, 'host': 'localhost'}
        >>> zolo.dumps(data)
        'port: 8080\\nhost: localhost'

        >>> zolo.dumps(data, file_extension='.json', indent=2)
        '{\\n  "port": 8080,\\n  "host": "localhost"\\n}'
    """
    # Default to .zolo if not specified
    if file_extension is None:
        file_extension = FILE_EXT_ZOLO

    # Normalize extension
    file_extension = file_extension.lower()
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension

    # Serialize based on format
    try:
        if file_extension == FILE_EXT_JSON:
            # Serialize as JSON
            indent = kwargs.get('indent', 2)
            return json.dumps(data, indent=indent, ensure_ascii=False)
        elif file_extension == FILE_EXT_ZOLO:
            # Serialize as YAML (for now - custom serializer TODO)
            return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        else:
            # Serialize as YAML
            return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)

    except Exception as e:
        raise ZoloDumpError(f"Serialization error: {e}") from e


# ============================================================================
# PRIVATE ORCHESTRATION - Internal coordination functions
# ============================================================================

def _parse_zolo_content(content: str) -> Any:
    """
    Custom .zolo parser without YAML quirks.

    Orchestrates the parsing pipeline:
    1. Strip comments and prepare lines
    2. Check indentation consistency
    3. Parse lines into nested structure

    Implementation follows ZOLO_PARSER_IMPLEMENTATION_PLAN.md
    Current: Phase 1-2 Complete (Comments, Types, Arrays, Nested Objects)
    """
    # Step 1: Strip comments and prepare lines
    lines, line_mapping = strip_comments_and_prepare_lines(content)

    # Step 2: Check indentation consistency (Python-style)
    check_indentation_consistency(lines)

    # Step 3: Parse with nested object support
    result = parse_lines(lines, line_mapping)

    return result


def _parse_zolo_content_with_tokens(content: str, emitter: TokenEmitter) -> Any:
    """
    Custom .zolo parser with token emission for LSP.

    This version tracks positions and emits semantic tokens during parsing.

    Orchestrates the parsing pipeline with tokenization:
    1. Strip comments and prepare lines (emit comment tokens)
    2. Check indentation consistency
    3. Parse lines with token emission
    """
    # Step 1: Strip comments and prepare lines (with token emission)
    lines, line_mapping = strip_comments_and_prepare_lines_with_tokens(content, emitter)

    # Step 2: Check indentation consistency
    check_indentation_consistency(lines)

    # Step 3: Parse with token emission
    result = parse_lines_with_tokens(lines, line_mapping, emitter)

    return result
