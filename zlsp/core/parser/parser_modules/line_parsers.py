"""
Line Parsers - Core parsing logic

The heart of the Zolo parser - processes lines and builds AST.
This is the largest module due to the complexity of line-by-line parsing.
"""

from typing import Any, Tuple, List, Optional

from .type_hints import process_type_hints, TYPE_HINT_PATTERN
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
from .validators import validate_ascii_only
from .key_detector import KeyDetector

# Forward reference
TYPE_CHECKING = False
if TYPE_CHECKING:
    from .token_emitter import TokenEmitter

def check_indentation_consistency(lines: list[str]) -> None:
    """
    Check that indentation is consistent (Python-style).
    
    Allows either tabs OR spaces for indentation, but forbids mixing.
    This is superior to YAML's arbitrary "spaces only" rule because:
    - Tabs are semantic (1 tab = 1 level)
    - Spaces are flexible (user choice)
    - Mixing is chaos (forbidden!)
    
    Args:
        lines: List of lines to check
    
    Raises:
        ZoloParseError: If tabs and spaces are mixed in indentation
    
    Philosophy:
        Like Python, .zolo cares about CONSISTENCY, not character type.
        Choose tabs (semantic) OR spaces (traditional), but be consistent!
    """
    first_indent_type = None  # 'tab' or 'space'
    first_indent_line = None
    
    for line_num, line in enumerate(lines, 1):
        # Skip empty lines and lines with no indentation
        if not line.strip():
            continue
        
        # Get indentation characters
        stripped = line.lstrip()
        if len(stripped) == len(line):
            # No indentation
            continue
        
        indent_chars = line[:len(line) - len(stripped)]
        
        # Check what this line uses
        has_tab = '\t' in indent_chars
        has_space = ' ' in indent_chars
        
        # ERROR: Mixed tabs and spaces in SAME line
        if has_tab and has_space:
            raise ZoloParseError(
                f"Mixed tabs and spaces in indentation at line {line_num}.\n"
                f"Use either tabs OR spaces consistently (Python convention).\n"
                f"Hint: Configure your editor to use one type of indentation."
            )
        
        # Determine this line's indent type
        current_type = 'tab' if has_tab else 'space'
        
        # Track first indent type seen in file
        if first_indent_type is None:
            first_indent_type = current_type
            first_indent_line = line_num
        # ERROR: Different type than rest of file
        elif first_indent_type != current_type:
            indent_word = 'tabs' if first_indent_type == 'tab' else 'spaces'
            current_word = 'tabs' if current_type == 'tab' else 'spaces'
            raise ZoloParseError(
                f"Inconsistent indentation at line {line_num}.\n"
                f"File uses {indent_word} (first seen at line {first_indent_line}),\n"
                f"but this line uses {current_word}.\n"
                f"Use either tabs OR spaces consistently (Python convention)."
            )


def parse_lines_with_tokens(lines: list[str], line_mapping: dict, emitter: 'TokenEmitter') -> dict:
    r"""
    Parse lines with token emission for LSP.
    
    Similar to _parse_lines() but emits semantic tokens for all syntax elements.
    """
    if not lines:
        return {}
    
    structured_lines = []
    i = 0
    line_number = 0
    
    while i < len(lines):
        line = lines[i]
        original_line_num = line_mapping.get(i, i)
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()
            
            # Find key position in original line
            key_start = line.find(key)
            
            # Emit colon token
            colon_pos = line.find(':', key_start)
            emitter.emit(original_line_num, colon_pos, 1, TokenType.COLON)
            
            # Check for type hint
            match = TYPE_HINT_PATTERN.match(key)
            if match:
                clean_key = match.group(1)
                type_hint = match.group(2)
                
                # Emit root or nested key token
                if indent == 0:
                    # Clear ZNAVBAR and zMeta block tracking when we encounter a new root-level key
                    emitter.znavbar_blocks = []
                    emitter.zmeta_blocks = []
                    
                    # Split modifiers from clean_key (key without type hint)
                    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(clean_key)
                    current_pos = key_start
                    
                    # Emit prefix modifiers (purple in zEnv/zUI only)
                    for mod in prefix_mods:
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                    
                    # ====== ROOT KEY DETECTION (using KeyDetector) ======
                    # Detect token type using KeyDetector (replaces 58 lines of conditionals)
                    token_type = KeyDetector.detect_root_key(core_key, emitter, indent)
                    emitter.emit(original_line_num, current_pos, len(core_key), token_type)
                    
                    # Check for block entry and emit diagnostics for invalid root keys
                    if core_key == 'zSub':
                        # zSub at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"'zSub' cannot be at root level. It must be nested under a parent key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                    elif core_key == 'zRBAC':
                        # zRBAC at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"'zRBAC' cannot be at root level. It must be nested under a parent key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                    else:
                        # Check for block entry
                        block_type = KeyDetector.should_enter_block(core_key, emitter)
                        if block_type == 'zmeta':
                            emitter.enter_zmeta_block(indent, original_line_num)
                        elif block_type == 'znavbar':
                            emitter.enter_znavbar_block(indent, original_line_num)
                        elif core_key == 'zMachine':
                            emitter.enter_zmachine_block(indent, original_line_num)
                    
                    current_pos += len(core_key)
                    
                    # Emit suffix modifiers (purple in zEnv/zUI only)
                    for mod in suffix_mods:
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                else:
                    # Update block tracking (exit blocks we've left based on indentation)
                    emitter.update_zrbac_blocks(indent, original_line_num)
                    emitter.update_zimage_blocks(indent, original_line_num)
                    emitter.update_ztext_blocks(indent, original_line_num)
                    emitter.update_zmd_blocks(indent, original_line_num)
                    emitter.update_zurl_blocks(indent, original_line_num)
                    emitter.update_header_blocks(indent, original_line_num)
                    emitter.update_zmachine_blocks(indent, original_line_num)
                    emitter.update_znavbar_blocks(indent, original_line_num)
                    emitter.update_zmeta_blocks(indent, original_line_num)
                    
                    # Split modifiers from clean_key (key without type hint)
                    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(clean_key)
                    current_pos = key_start
                    
                    # Emit prefix modifiers (purple in zEnv/zUI only)
                    for mod in prefix_mods:
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                    
                    # Determine token type for core key and emit
                    # Check for zRBAC key (tomato red in zEnv/zUI files only)
                    if core_key == 'zRBAC':
                        # zRBAC gets tomato red (196) only in zEnv/zUI files
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                        # Mark that we're entering a zRBAC block
                        emitter.enter_zrbac_block(indent, original_line_num)
                    # Check for zSpark nested keys (purple 98 in zSpark files only)
                    elif emitter.is_zspark_file:
                        # ALL nested keys under zSpark root get purple color
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSPARK_NESTED_KEY)
                    # Check for ZNAVBAR first-level nested keys (ANSI 222 in zEnv files only)
                    elif emitter.is_znavbar_first_level(indent) and emitter.is_zenv_file:
                        # First-level nested keys under ZNAVBAR (not grandchildren)
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZNAVBAR_NESTED_KEY)
                    # Check for zKernel zData keys under zMeta in zSchema files (PURPLE 98)
                    elif emitter.is_inside_zmeta(indent) and emitter.is_zschema_file:
                        ZKERNEL_DATA_KEYS = {'Data_Type', 'Data_Label', 'Data_Source', 'Schema_Name', 'zMigration', 'zMigrationVersion'}
                        if core_key in ZKERNEL_DATA_KEYS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZKERNEL_DATA_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zSchema property keys (field properties and validation rules) - PURPLE 98
                    elif emitter.is_zschema_file and indent >= 4:
                        # Field-level properties (type, pk, unique, etc.) and validation properties (format, min_length, etc.)
                        ZSCHEMA_FIELD_PROPERTIES = {'type', 'pk', 'auto_increment', 'unique', 'required', 'default', 'rules', 'zHash', 'comment'}
                        ZSCHEMA_VALIDATION_PROPERTIES = {'format', 'min_length', 'max_length', 'pattern', 'min', 'max'}
                        if core_key in ZSCHEMA_FIELD_PROPERTIES or core_key in ZSCHEMA_VALIDATION_PROPERTIES:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSCHEMA_PROPERTY_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zRBAC option keys (PURPLE in zUI and zEnv files only)
                    elif emitter.is_in_zrbac_block(indent) and (emitter.is_zui_file or emitter.is_zenv_file):
                        ZRBAC_OPTIONS = {'zGuest', 'authenticated', 'require_role', 'require_auth', 'require_permission'}
                        if core_key in ZRBAC_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zMachine nested section keys in zConfig files
                    elif emitter.is_in_zmachine_block(indent) and emitter.is_zconfig_file:
                        # Define editable sections (blue/cyan - INFO level)
                        ZMACHINE_EDITABLE_SECTIONS = {
                            'user_preferences', 'time_date_formatting', 'launch_commands', 'custom'
                        }
                        # Define locked/auto-detected sections (red/orange - ERROR level)
                        ZMACHINE_LOCKED_SECTIONS = {
                            'machine_identity', 'python_runtime', 'cpu', 'memory', 'gpu', 'network', 'user_paths'
                        }
                        
                        if core_key in ZMACHINE_EDITABLE_SECTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMACHINE_EDITABLE_KEY)
                        elif core_key in ZMACHINE_LOCKED_SECTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMACHINE_LOCKED_KEY)
                        else:
                            # Unknown key - default to nested key
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zImage key (GOLD in zUI files) and enter block
                    elif core_key == 'zImage' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zImage block
                        emitter.enter_zimage_block(indent, original_line_num)
                    # Check for zImage option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zimage_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZIMAGE_OPTIONS = {'src', 'alt_text', 'caption', 'open_prompt', 'indent', 'color'}
                        if core_key in ZIMAGE_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zText key (GOLD in zUI files) and enter block
                    elif core_key == 'zText' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zText block
                        emitter.enter_ztext_block(indent, original_line_num)
                    # Check for zText option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_ztext_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZTEXT_OPTIONS = {'content', 'indent', 'color', 'break_after'}
                        if core_key in ZTEXT_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zMD key (GOLD in zUI files) and enter block
                    elif core_key == 'zMD' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zMD block
                        emitter.enter_zmd_block(indent, original_line_num)
                    # Check for zMD option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zmd_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZMD_OPTIONS = {'content', 'indent', 'pause', 'break_message', 'format'}
                        if core_key in ZMD_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zURL key (GOLD in zUI files) and enter block
                    elif core_key == 'zURL' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zURL block
                        emitter.enter_zurl_block(indent, original_line_num)
                    # Check for zURL option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zurl_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZURL_OPTIONS = {'label', 'href', 'target', 'color', 'rel', 'window'}
                        if core_key in ZURL_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zH1-zH6 keys (GOLD in zUI files) and enter block
                    elif core_key in {'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'} and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a header block
                        emitter.enter_header_block(indent, original_line_num)
                    # Check for header option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_header_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        HEADER_OPTIONS = {'label', 'color', 'style', 'semantic', 'indent'}
                        if core_key in HEADER_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for plural shorthand option keys (PURPLE in zUI files, 2+ levels deep, excluding Bifrost)
                    elif not core_key.startswith('_') and emitter.is_zui_file:
                        plural_context = emitter.get_plural_shorthand_context(indent)
                        if plural_context:
                            # Define valid options for each plural shorthand type
                            PLURAL_OPTIONS = {
                                'zURLs': {'label', 'href', 'target', 'rel', 'color', 'window'},
                                'zTexts': {'content', 'indent', 'color'},
                                'zImages': {'src', 'alt_text', 'caption', 'open_prompt', 'indent', 'color'},
                                'zH1s': {'label', 'color', 'indent'},
                                'zH2s': {'label', 'color', 'indent'},
                                'zH3s': {'label', 'color', 'indent'},
                                'zH4s': {'label', 'color', 'indent'},
                                'zH5s': {'label', 'color', 'indent'},
                                'zH6s': {'label', 'color', 'indent'},
                                'zMDs': {'content', 'indent', 'color'},
                            }
                            if plural_context in PLURAL_OPTIONS and core_key in PLURAL_OPTIONS[plural_context]:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                            else:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                        else:
                            # Check if this IS a plural shorthand container itself
                            PLURAL_SHORTHANDS = {'zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 
                                               'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs'}
                            if core_key in PLURAL_SHORTHANDS:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                                emitter.enter_plural_shorthand_block(indent, original_line_num, core_key)
                            # Check for zSub key (purple 98 when grandchild+ in zEnv/zUI files)
                            elif core_key == 'zSub':
                                # zSub in zEnv/zUI at grandchild+ level (indent >= 4) gets purple
                                if (emitter.is_zenv_file or emitter.is_zui_file) and indent >= 4:
                                    emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSUB_KEY)
                                else:
                                    emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                            # Check for specific shorthand display event keys (strict whitelist)
                            elif core_key in {'zNavBar', 'zImage', 'zUL', 'zOL', 'zURL', 'zURLs', 'zText', 'zMD', 'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'}:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                            else:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zSub key (purple 98 when grandchild+ in zEnv/zUI files)
                    elif core_key == 'zSub':
                        # zSub in zEnv/zUI at grandchild+ level (indent >= 4) gets purple
                        if (emitter.is_zenv_file or emitter.is_zui_file) and indent >= 4:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSUB_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                    # Check for underscore-prefixed keys (Bifrost keys)
                    elif core_key.startswith('_'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.BIFROST_KEY)
                    # Check for specific shorthand display event keys (strict whitelist)
                    elif emitter.is_zui_file and core_key in {'zNavBar', 'zImage', 'zUL', 'zOL', 'zURL', 'zURLs', 'zText', 'zMD'}:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                    else:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    
                    current_pos += len(core_key)
                    
                    # Emit suffix modifiers (purple in zEnv/zUI only)
                    for mod in suffix_mods:
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                
                # Emit type hint token (after modifiers and core key)
                hint_start = key_start + len(clean_key) + 1  # +1 for opening paren
                emitter.emit(original_line_num, hint_start, len(type_hint), TokenType.TYPE_HINT)
                
                has_str_hint = type_hint.lower() == 'str'
            else:
                # No type hint
                if indent == 0:
                    # Clear ZNAVBAR and zMeta block tracking when we encounter a new root-level key
                    emitter.znavbar_blocks = []
                    emitter.zmeta_blocks = []
                    
                    # Split modifiers from key name
                    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(key)
                    current_pos = key_start
                    
                    # Emit prefix modifiers (purple in zEnv/zUI only)
                    for mod in prefix_mods:
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                    
                    # Determine token type for core key and emit
                    # Special handling for zMeta, zVaF, and component name in zUI files
                    # Special handling for zMeta in zSchema files
                    if (emitter.is_zui_file and (core_key == 'zMeta' or core_key == 'zVaF' or core_key == emitter.zui_component_name)) or \
                       (emitter.is_zschema_file and core_key == 'zMeta'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMETA_KEY)
                        # If this is zMeta in a zSchema file, enter the block for zKernel data key tracking
                        if emitter.is_zschema_file and core_key == 'zMeta':
                            emitter.enter_zmeta_block(indent, original_line_num)
                    # Special handling for zSpark root key in zSpark files (LIGHT GREEN - ANSI 114)
                    elif emitter.is_zspark_file and core_key == 'zSpark':
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSPARK_KEY)
                    # Special handling for config root keys in zEnv files (PURPLE - ANSI 98)
                    elif emitter.is_zenv_file and core_key in ('DEPLOYMENT', 'DEBUG', 'LOG_LEVEL'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZENV_CONFIG_KEY)
                    # Special handling for uppercase Z-prefixed config keys in zEnv files (GREEN)
                    elif emitter.is_zenv_file and core_key.isupper() and core_key.startswith('Z'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZCONFIG_KEY)
                        # If this is ZNAVBAR, enter the block for first-level nested key tracking
                        if core_key == 'ZNAVBAR':
                            emitter.enter_znavbar_block(indent, original_line_num)
                    # Special handling for z-prefixed root keys in zConfig files (GREEN) - e.g., zMachine
                    elif emitter.is_zconfig_file and core_key.startswith('z') and len(core_key) > 1 and core_key[1].isupper():
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZCONFIG_KEY)
                        # If this is zMachine, enter the block for nested key tracking
                        if core_key == 'zMachine':
                            emitter.enter_zmachine_block(indent, original_line_num)
                    # Check for zSub at root level (ERROR - zSub must always be nested)
                    elif core_key == 'zSub':
                        # zSub at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"'zSub' cannot be at root level. It must be nested under a parent key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                        # Still emit as ROOT_KEY token for highlighting
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    # Check for zRBAC at root level (ERROR - zRBAC must always be nested)
                    elif core_key == 'zRBAC':
                        # zRBAC at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"'zRBAC' cannot be at root level. It must be nested under a parent key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                        # Still emit as ROOT_KEY token for highlighting
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    else:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    
                    current_pos += len(core_key)
                    
                    # Emit suffix modifiers (purple in zEnv/zUI only)
                    for mod in suffix_mods:
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                else:
                    # Update block tracking (exit blocks we've left based on indentation)
                    emitter.update_zrbac_blocks(indent, original_line_num)
                    emitter.update_zimage_blocks(indent, original_line_num)
                    emitter.update_ztext_blocks(indent, original_line_num)
                    emitter.update_zmd_blocks(indent, original_line_num)
                    emitter.update_zurl_blocks(indent, original_line_num)
                    emitter.update_header_blocks(indent, original_line_num)
                    emitter.update_zmachine_blocks(indent, original_line_num)
                    emitter.update_znavbar_blocks(indent, original_line_num)
                    emitter.update_zmeta_blocks(indent, original_line_num)
                    emitter.update_plural_shorthand_blocks(indent, original_line_num)
                    
                    # Split modifiers from key name
                    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(key)
                    current_pos = key_start
                    
                    # Emit prefix modifiers (purple in zEnv/zUI only)
                    for mod in prefix_mods:
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                    
                    # Determine token type for core key and emit
                    # Check for zRBAC key (tomato red in zEnv/zUI files only)
                    if core_key == 'zRBAC':
                        # zRBAC gets tomato red (196) only in zEnv/zUI files
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                        # Mark that we're entering a zRBAC block
                        emitter.enter_zrbac_block(indent, original_line_num)
                    # Check for zSpark nested keys (purple 98 in zSpark files only)
                    elif emitter.is_zspark_file:
                        # ALL nested keys under zSpark root get purple color
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSPARK_NESTED_KEY)
                    # Check for ZNAVBAR first-level nested keys (ANSI 222 in zEnv files only)
                    elif emitter.is_znavbar_first_level(indent) and emitter.is_zenv_file:
                        # First-level nested keys under ZNAVBAR (not grandchildren)
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZNAVBAR_NESTED_KEY)
                    # Check for zKernel zData keys under zMeta in zSchema files (PURPLE 98)
                    elif emitter.is_inside_zmeta(indent) and emitter.is_zschema_file:
                        ZKERNEL_DATA_KEYS = {'Data_Type', 'Data_Label', 'Data_Source', 'Schema_Name', 'zMigration', 'zMigrationVersion'}
                        if core_key in ZKERNEL_DATA_KEYS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZKERNEL_DATA_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zSchema property keys (field properties and validation rules) - PURPLE 98
                    elif emitter.is_zschema_file and indent >= 4:
                        # Field-level properties (type, pk, unique, etc.) and validation properties (format, min_length, etc.)
                        ZSCHEMA_FIELD_PROPERTIES = {'type', 'pk', 'auto_increment', 'unique', 'required', 'default', 'rules', 'zHash', 'comment'}
                        ZSCHEMA_VALIDATION_PROPERTIES = {'format', 'min_length', 'max_length', 'pattern', 'min', 'max'}
                        if core_key in ZSCHEMA_FIELD_PROPERTIES or core_key in ZSCHEMA_VALIDATION_PROPERTIES:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSCHEMA_PROPERTY_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zRBAC option keys (PURPLE in zUI and zEnv files only)
                    elif emitter.is_in_zrbac_block(indent) and (emitter.is_zui_file or emitter.is_zenv_file):
                        ZRBAC_OPTIONS = {'zGuest', 'authenticated', 'require_role', 'require_auth', 'require_permission'}
                        if core_key in ZRBAC_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zMachine nested section keys in zConfig files
                    elif emitter.is_in_zmachine_block(indent) and emitter.is_zconfig_file:
                        # Define editable sections (blue/cyan - INFO level)
                        ZMACHINE_EDITABLE_SECTIONS = {
                            'user_preferences', 'time_date_formatting', 'launch_commands', 'custom'
                        }
                        # Define locked/auto-detected sections (red/orange - ERROR level)
                        ZMACHINE_LOCKED_SECTIONS = {
                            'machine_identity', 'python_runtime', 'cpu', 'memory', 'gpu', 'network', 'user_paths'
                        }
                        
                        if core_key in ZMACHINE_EDITABLE_SECTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMACHINE_EDITABLE_KEY)
                        elif core_key in ZMACHINE_LOCKED_SECTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMACHINE_LOCKED_KEY)
                        else:
                            # Unknown key - default to nested key
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zImage key (GOLD in zUI files) and enter block
                    elif core_key == 'zImage' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zImage block
                        emitter.enter_zimage_block(indent, original_line_num)
                    # Check for zImage option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zimage_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZIMAGE_OPTIONS = {'src', 'alt_text', 'caption', 'open_prompt', 'indent', 'color'}
                        if core_key in ZIMAGE_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zText key (GOLD in zUI files) and enter block
                    elif core_key == 'zText' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zText block
                        emitter.enter_ztext_block(indent, original_line_num)
                    # Check for zText option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_ztext_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZTEXT_OPTIONS = {'content', 'indent', 'color', 'break_after'}
                        if core_key in ZTEXT_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zMD key (GOLD in zUI files) and enter block
                    elif core_key == 'zMD' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zMD block
                        emitter.enter_zmd_block(indent, original_line_num)
                    # Check for zMD option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zmd_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZMD_OPTIONS = {'content', 'indent', 'pause', 'break_message', 'format'}
                        if core_key in ZMD_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zURL key (GOLD in zUI files) and enter block
                    elif core_key == 'zURL' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zURL block
                        emitter.enter_zurl_block(indent, original_line_num)
                    # Check for zURL option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zurl_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZURL_OPTIONS = {'label', 'href', 'target', 'color', 'rel', 'window'}
                        if core_key in ZURL_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zH1-zH6 keys (GOLD in zUI files) and enter block
                    elif core_key in {'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'} and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a header block
                        emitter.enter_header_block(indent, original_line_num)
                    # Check for header option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_header_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        HEADER_OPTIONS = {'label', 'color', 'style', 'semantic', 'indent'}
                        if core_key in HEADER_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for plural shorthand option keys (PURPLE in zUI files, 2+ levels deep, excluding Bifrost)
                    elif not core_key.startswith('_') and emitter.is_zui_file:
                        plural_context = emitter.get_plural_shorthand_context(indent)
                        if plural_context:
                            # Define valid options for each plural shorthand type
                            PLURAL_OPTIONS = {
                                'zURLs': {'label', 'href', 'target', 'rel', 'color', 'window'},
                                'zTexts': {'content', 'indent', 'color'},
                                'zImages': {'src', 'alt_text', 'caption', 'open_prompt', 'indent', 'color'},
                                'zH1s': {'label', 'color', 'indent'},
                                'zH2s': {'label', 'color', 'indent'},
                                'zH3s': {'label', 'color', 'indent'},
                                'zH4s': {'label', 'color', 'indent'},
                                'zH5s': {'label', 'color', 'indent'},
                                'zH6s': {'label', 'color', 'indent'},
                                'zMDs': {'content', 'indent', 'color'},
                            }
                            if plural_context in PLURAL_OPTIONS and core_key in PLURAL_OPTIONS[plural_context]:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                            else:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                        else:
                            # Check if this IS a plural shorthand container itself
                            PLURAL_SHORTHANDS = {'zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 
                                               'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs'}
                            if core_key in PLURAL_SHORTHANDS:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                                emitter.enter_plural_shorthand_block(indent, original_line_num, core_key)
                            # Check for zSub key (purple 98 when grandchild+ in zEnv/zUI files)
                            elif core_key == 'zSub':
                                # zSub in zEnv/zUI at grandchild+ level (indent >= 4) gets purple
                                if (emitter.is_zenv_file or emitter.is_zui_file) and indent >= 4:
                                    emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSUB_KEY)
                                else:
                                    emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                            # Check for specific shorthand display event keys (strict whitelist)
                            elif core_key in {'zNavBar', 'zImage', 'zUL', 'zOL', 'zURL', 'zURLs', 'zText', 'zMD', 'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'}:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                            else:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zSub key (purple 98 when grandchild+ in zEnv/zUI files)
                    elif core_key == 'zSub':
                        # zSub in zEnv/zUI at grandchild+ level (indent >= 4) gets purple
                        if (emitter.is_zenv_file or emitter.is_zui_file) and indent >= 4:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSUB_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                    # Check for underscore-prefixed keys (Bifrost keys)
                    elif core_key.startswith('_'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.BIFROST_KEY)
                    # Check for specific shorthand display event keys (strict whitelist)
                    elif emitter.is_zui_file and core_key in {'zNavBar', 'zImage', 'zUL', 'zOL', 'zURL', 'zURLs', 'zText', 'zMD'}:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                    else:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    
                    current_pos += len(core_key)
                    
                    # Emit suffix modifiers (purple in zEnv/zUI only)
                    for mod in suffix_mods:
                        if emitter.is_zenv_file or emitter.is_zui_file:
                            emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                has_str_hint = False
            
            # Handle (str) multi-line values
            if has_str_hint:
                # Emit value token for first line if present
                if value:
                    value_start = colon_pos + 1
                    # Skip whitespace after colon
                    while value_start < len(line) and line[value_start] == ' ':
                        value_start += 1
                    # For (str) values, always emit as STRING (even if it starts with #)
                    emitter.emit(original_line_num, value_start, len(value), TokenType.STRING)
                
                # Collect and emit tokens for continuation lines
                lines_consumed = 0
                for j in range(i + 1, len(lines)):
                    cont_line = lines[j]
                    cont_original_line = line_mapping.get(j, j)
                    cont_indent = len(cont_line) - len(cont_line.lstrip())
                    cont_stripped = cont_line.strip()
                    
                    # Stop if line is at same or less indent than parent (unless empty)
                    if cont_stripped and cont_indent <= indent:
                        break
                    
                    # Stop if this looks like a new key
                    if cont_stripped and ':' in cont_stripped and cont_indent <= indent:
                        break
                    
                    # Emit STRING token for this continuation line
                    if cont_stripped:
                        # Find where content starts (after indentation)
                        content_start = len(cont_line) - len(cont_line.lstrip())
                        emitter.emit(cont_original_line, content_start, len(cont_stripped), TokenType.STRING)
                    
                    lines_consumed += 1
                
                # Store structured line info
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': value,
                    'line': line,
                    'line_number': original_line_num,
                    'is_multiline': True
                })
                i += lines_consumed + 1
                line_number += lines_consumed + 1
            # Handle multi-line arrays (value == '[')
            elif value == '[':
                # Find opening bracket position
                value_start = colon_pos + 1
                while value_start < len(line) and line[value_start] == ' ':
                    value_start += 1
                bracket_pos = value_start
                
                # Emit opening bracket
                emitter.emit(original_line_num, bracket_pos, 1, TokenType.BRACKET_STRUCTURAL)
                
                # Collect multi-line array content
                reconstructed, lines_consumed, item_line_info = collect_bracket_array(
                    lines, i + 1, indent, value
                )
                
                # Emit tokens for each array item line
                for item_line_idx, item_content, has_comma in item_line_info:
                    item_original_line = line_mapping.get(item_line_idx, item_line_idx)
                    item_line = lines[item_line_idx]
                    item_indent = len(item_line) - len(item_line.lstrip())
                    
                    # Find where item content starts
                    content_start = item_indent
                    
                    # Emit token for the item content
                    emit_value_tokens(item_content, item_original_line, content_start, emitter)
                    
                    # Emit comma if present
                    if has_comma:
                        comma_pos = item_indent + len(item_content)
                        emitter.emit(item_original_line, comma_pos, 1, TokenType.COMMA)
                
                # Find and emit closing bracket
                closing_line_idx = i + lines_consumed
                if closing_line_idx < len(lines):
                    closing_line = lines[closing_line_idx]
                    closing_original_line = line_mapping.get(closing_line_idx, closing_line_idx)
                    closing_bracket_pos = closing_line.find(']')
                    if closing_bracket_pos >= 0:
                        emitter.emit(closing_original_line, closing_bracket_pos, 1, TokenType.BRACKET_STRUCTURAL)
                
                # Store structured line info with reconstructed value
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': reconstructed,
                    'line': line,
                    'line_number': original_line_num,
                    'is_multiline': True,
                    'multiline_type': 'array'  # Mark as array for type detection
                })
                i += lines_consumed + 1
                line_number += lines_consumed + 1
            # Handle dash lists (YAML-style: key:\n  - item1\n  - item2)
            elif not value and i + 1 < len(lines):
                # Check if next line starts with dash at child indent
                next_line = lines[i + 1]
                next_indent = len(next_line) - len(next_line.lstrip())
                next_stripped = next_line.strip()
                
                if next_stripped.startswith('- ') and next_indent > indent:
                    # Collect dash list items
                    reconstructed, lines_consumed, item_line_info = collect_dash_list(lines, i + 1, indent)
                    
                    # Emit tokens for each dash list item line
                    for item_line_idx, dash_pos, item_content in item_line_info:
                        item_original_line = line_mapping.get(item_line_idx, item_line_idx)
                        
                        # Emit dash as BRACKET_STRUCTURAL (same color as [ ])
                        emitter.emit(item_original_line, dash_pos, 1, TokenType.BRACKET_STRUCTURAL)
                        
                        # Emit token for the item content (after "- ")
                        content_start = dash_pos + 2  # After "- "
                        emit_value_tokens(item_content, item_original_line, content_start, emitter)
                    
                    # Store structured line info with reconstructed value
                    structured_lines.append({
                        'indent': indent,
                        'key': key,
                        'value': reconstructed,
                        'line': line,
                        'line_number': original_line_num,
                        'is_multiline': True,
                        'multiline_type': 'dash_list'  # Mark as dash list for type detection
                })
                    i += lines_consumed + 1
                    line_number += lines_consumed + 1
                else:
                    # Empty value (no dash list)
                    structured_lines.append({
                        'indent': indent,
                        'key': key,
                        'value': value,
                        'line': line,
                        'line_number': original_line_num,
                        'is_multiline': False
                    })
                    i += 1
                    line_number += 1
            else:
                # Regular value (not multi-line)
                if value:
                    value_start = colon_pos + 1
                    # Skip whitespace after colon
                    while value_start < len(line) and line[value_start] == ' ':
                        value_start += 1
                    # Extract core key (without modifiers and type hints) for context-aware coloring
                    clean_key = TYPE_HINT_PATTERN.match(key).group(1) if TYPE_HINT_PATTERN.match(key) else key
                    _, core_key, _ = emitter.split_modifiers(clean_key)
                    emit_value_tokens(value, original_line_num, value_start, emitter, key=core_key)
                
                # Store structured line info
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': value,
                    'line': line,
                    'line_number': original_line_num,
                    'is_multiline': False
                })
                i += 1
                line_number += 1
        else:
            i += 1
            line_number += 1
    
    # Build nested structure (without token emission, as tokens already emitted)
    return build_nested_dict(structured_lines, 0, 0)


def parse_lines(lines: list[str], line_mapping: dict = None) -> dict:
    r"""
    Phase 2, Step 2.3 + Phase 3: Parse lines with nested object and multi-line string support.
    
    Uses indentation to build nested dictionary structure:
    - Track indent level for each line
    - Build parent-child relationships
    - Support nested objects at any depth
    - Support multi-line strings: pipe, triple-quotes, escape sequences
    
    Args:
        lines: Cleaned lines (from Step 1.1)
        line_mapping: Optional dict mapping cleaned line index to original line number (1-based)
    
    Returns:
        Nested dictionary structure
    
    Examples:
        >>> _parse_lines(["name: MyApp", "port: 5000"])
        {'name': 'MyApp', 'port': 5000.0}
        
        >>> _parse_lines(["server:", "  host: localhost", "  port: 5000"])
        {'server': {'host': 'localhost', 'port': 5000.0}}
    """
    if not lines:
        return {}
    
    # Default line mapping if not provided (for backwards compatibility)
    if line_mapping is None:
        line_mapping = {i: i + 1 for i in range(len(lines))}
    
    # Parse lines into structured data with indentation info and multi-line handling
    structured_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Get original line number from mapping
        original_line_number = line_mapping.get(i, i + 1)
        
        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()
            
            # Validate key is ASCII-only (RFC 8259 compliance)
            validate_ascii_only(key, original_line_number)
            
            # Check if key has (str) type hint for multi-line collection
            match = TYPE_HINT_PATTERN.match(key)
            has_str_hint = match and match.group(2).lower() == 'str'
            
            # Multi-line ONLY enabled with (str) hint
            # | and """ are now literal characters (bread and butter!)
            if has_str_hint:
                # (str) type hint: collect YAML-style indented multi-line
                multiline_value, lines_consumed = collect_str_hint_multiline(lines, i + 1, indent, value)
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': multiline_value,
                    'line': line,
                    'line_number': original_line_number,
                    'is_multiline': True
                })
                i += lines_consumed + 1
            # Handle multi-line arrays (value == '[')
            elif value == '[':
                # Collect multi-line array content
                reconstructed, lines_consumed, _ = collect_bracket_array(lines, i + 1, indent, value)
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': reconstructed,
                    'line': line,
                    'line_number': original_line_number,
                    'is_multiline': True,
                    'multiline_type': 'array'  # Mark as array for type detection
                })
                i += lines_consumed + 1
            # Handle dash lists (YAML-style: key:\n  - item1\n  - item2)
            elif not value and i + 1 < len(lines):
                # Check if next line starts with dash at child indent
                next_line = lines[i + 1]
                next_indent = len(next_line) - len(next_line.lstrip())
                next_stripped = next_line.strip()
                
                if next_stripped.startswith('- ') and next_indent > indent:
                    # Collect dash list items
                    reconstructed, lines_consumed, _ = collect_dash_list(lines, i + 1, indent)
                    structured_lines.append({
                        'indent': indent,
                        'key': key,
                        'value': reconstructed,
                        'line': line,
                        'line_number': original_line_number,
                        'is_multiline': True,
                        'multiline_type': 'dash_list'  # Mark as dash list for type detection
                    })
                    i += lines_consumed + 1
                else:
                    # Empty value (no dash list)
                    structured_lines.append({
                        'indent': indent,
                        'key': key,
                        'value': value,
                        'line': line,
                        'line_number': original_line_number,
                        'is_multiline': False
                    })
                    i += 1
            else:
                # Regular value - | and """ are literal characters
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': value,
                    'line': line,
                    'line_number': original_line_number,
                    'is_multiline': False
                })
                i += 1
        else:
            i += 1
    
    # Build nested structure
    return build_nested_dict(structured_lines, 0, 0)


def build_nested_dict(structured_lines: list[dict], start_idx: int, current_indent: int) -> dict:
    """
    Recursively build nested dictionary from structured lines.
    
    Args:
        structured_lines: List of parsed line dictionaries
        start_idx: Index to start parsing from
        current_indent: Current indentation level we're parsing at
    
    Returns:
        Nested dictionary
    
    Raises:
        ZoloParseError: If duplicate keys are found at the same nesting level
    """
    result = {}
    seen_keys = {}  # Track: {clean_key: (line_number, original_key)}
    i = start_idx
    
    while i < len(structured_lines):
        line_info = structured_lines[i]
        indent = line_info['indent']
        key = line_info['key']
        value = line_info['value']
        line_number = line_info.get('line_number', '?')
        
        # If we've moved to a different indent level, stop
        if indent != current_indent:
            break
        
        # Strip type hint from key for duplicate checking
        # Example: "port(int)" → "port"
        match = TYPE_HINT_PATTERN.match(key)
        clean_key = match.group(1) if match else key
        
        # UI event shorthands are exempt from duplicate key checks
        # These represent sequential UI elements, not dictionary keys
        is_ui_event_shorthand = (
            clean_key in ['zText', 'zImage', 'zMD', 'zURL', 'zUL', 'zOL', 'zTable'] or
            (clean_key.startswith('zH') and len(clean_key) == 3 and clean_key[2].isdigit())
        )
        
        # Check for duplicate keys (STRICT MODE - Phase 4.7)
        # Exempt UI event shorthands (they represent sequences, not dict keys)
        if not is_ui_event_shorthand and clean_key in seen_keys:
            first_line, first_key = seen_keys[clean_key]
            raise ZoloParseError(
                f"Duplicate key '{clean_key}' found at line {line_number}.\n"
                f"First occurrence: '{first_key}' at line {first_line}.\n"
                f"Keys must be unique within the same level.\n"
                f"Hint: Did you mean to use a different key name?"
            )
        
        # Track seen keys (even UI shorthands, for consistency)
        seen_keys[clean_key] = (line_number, key)
        
        # Check if next line is a child (more indented)
        has_children = False
        child_indent = None
        if i + 1 < len(structured_lines):
            next_indent = structured_lines[i + 1]['indent']
            if next_indent > indent:
                has_children = True
                child_indent = next_indent
        
        if has_children:
            # Recursively parse children
            child_dict = build_nested_dict(structured_lines, i + 1, child_indent)
            
            # Override Python dict behavior: Use suffix for duplicate UI event keys
            # This preserves both the values AND their interleaved position
            if is_ui_event_shorthand and key in result:
                # Key already exists - add numeric suffix to preserve order
                counter = 2
                suffixed_key = f"{key}__dup{counter}"
                while suffixed_key in result:
                    counter += 1
                    suffixed_key = f"{key}__dup{counter}"
                result[suffixed_key] = child_dict
            else:
                # Normal case - set/overwrite key
                result[key] = child_dict
            
            # Skip all child lines (find next line at current indent or less)
            i += 1
            while i < len(structured_lines) and structured_lines[i]['indent'] > indent:
                i += 1
        else:
            # Leaf node - detect value type or use multi-line string
            if line_info.get('is_multiline', False):
                # Check if it's a multi-line array/dash list (needs type detection) or string (use as-is)
                if line_info.get('multiline_type') in ('array', 'dash_list'):
                    # Multi-line array or dash list: run type detection on reconstructed value
                    typed_value = detect_value_type(value) if value else ''
                else:
                    # Multi-line string: already processed, use as-is
                    typed_value = value
            else:
                # Detect value type (including \n escape sequences)
                typed_value = detect_value_type(value) if value else ''
            
            # Override Python dict behavior: Use suffix for duplicate UI event keys
            # This preserves both the values AND their interleaved position
            if is_ui_event_shorthand and key in result:
                # Key already exists - add numeric suffix to preserve order
                counter = 2
                suffixed_key = f"{key}__dup{counter}"
                while suffixed_key in result:
                    counter += 1
                    suffixed_key = f"{key}__dup{counter}"
                result[suffixed_key] = typed_value
            else:
                # Normal case - set/overwrite key
                result[key] = typed_value
            i += 1
    
    return result


def parse_root_key_value_pairs(lines: list[str]) -> dict:
    """
    Phase 1, Steps 1.2-1.3: Parse basic key-value pairs with type detection.
    
    Rules:
    - Only parse lines at root level (no leading whitespace)
    - Split on first `:` occurrence
    - Trim whitespace from key and value
    - Apply RFC 8259 type detection (Step 1.3)
    - Skip nested lines (will be handled in Phase 2)
    
    Args:
        lines: Cleaned lines (from Step 1.1)
    
    Returns:
        Dictionary with root-level key-value pairs (typed values)
    
    Examples:
        >>> _parse_root_key_value_pairs(["name: MyApp", "port: 5000"])
        {'name': 'MyApp', 'port': 5000.0}
        
        >>> _parse_root_key_value_pairs(["debug: true", "db: null"])
        {'debug': True, 'db': None}
    """
    result = {}
    
    for line in lines:
        # Check if this is a root-level line (no leading whitespace)
        if line and line[0] not in (' ', '\t'):
            # Check if line contains a colon (key: value pattern)
            if ':' in line:
                # Split on first colon only
                key, _, value = line.partition(':')
                
                # Trim whitespace
                key = key.strip()
                value = value.strip()
                
                # Step 1.3: Detect and convert value type
                typed_value = detect_value_type(value)
                
                result[key] = typed_value
    
    return result


