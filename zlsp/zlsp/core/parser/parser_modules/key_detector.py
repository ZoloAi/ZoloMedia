"""
Key Detector - Context-aware key type detection

Detects special keys and determines their token types based on file type,
indentation, and block context. Centralizes key detection logic that was
previously scattered across line_parsers.py.
"""

from typing import Optional, TYPE_CHECKING
from ...lsp_types import TokenType

if TYPE_CHECKING:
    from .token_emitter import TokenEmitter


class KeyDetector:
    """
    Context-aware key detector for special .zolo file types.
    
    Detects special keys and determines their semantic token types based on:
    - File type (zSpark, zEnv, zUI, zConfig, zSchema)
    - Key name and patterns
    - Indentation level
    - Block nesting context
    - Key modifiers (^, ~, !, *)
    
    Provides a single source of truth for key classification across all file types.
    """
    
    # Special key sets for different file types
    ZKERNEL_DATA_KEYS = {
        'Data_Type', 'Data_Label', 'Data_Source', 'Schema_Name', 
        'zMigration', 'zMigrationVersion'
    }
    
    ZSCHEMA_PROPERTY_KEYS = {
        'type', 'pk', 'auto_increment', 'unique', 'required', 
        'default', 'rules', 'format', 'min_length', 'max_length',
        'pattern', 'min', 'max', 'zHash', 'comment'
    }
    
    UI_ELEMENT_KEYS = {
        'zImage', 'zText', 'zMD', 'zURL', 'zNavBar', 'zUL', 'zOL', 'zTable',
        'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'
    }
    
    UI_ELEMENT_PROPERTY_KEYS = {
        'src', 'alt_text', 'caption', 'color', 'open_prompt', 'indent',
        'label', 'style', 'semantic',
        'href', 'target', 'rel', 'window',
        'content', 'pause', 'break_message',
        'items',
        'title', 'columns', 'rows', 'limit', 'offset', 'show_header', 'interactive'
    }
    
    # UI Element Schemas - Define valid properties per element type
    UI_ELEMENT_SCHEMAS = {
        'zimage': {
            'required': ['src'],
            'optional': ['alt_text', 'caption', '_zClass', '_id', 'color', 'open_prompt', 'indent'],
        },
        'header': {  # Covers zH1-zH6
            'required': [],
            'optional': ['label', 'color', 'style', 'indent', 'semantic', '_zClass', '_id'],
        },
        'zurl': {
            'required': ['label', 'href'],
            'optional': ['target', 'rel', 'window', 'color', '_zClass', '_id'],
        },
        'ztext': {
            'required': ['content'],
            'optional': ['indent', 'pause', 'break_message', 'semantic', '_zClass', '_id'],
        },
        'zul': {
            'required': ['items'],
            'optional': ['style', 'indent', '_zClass', '_id'],
        },
        'ztable': {
            'required': ['title', 'columns', 'rows'],
            'optional': ['limit', 'offset', 'show_header', 'interactive', 'indent', '_zClass', '_id'],
        },
        # More elements to be added as needed
    }
    
    ZENV_CONFIG_ROOT_KEYS = {'DEPLOYMENT', 'DEBUG', 'LOG_LEVEL'}
    
    # zMachine section headers (first-level keys under zMachine:)
    ZMACHINE_LOCKED_SECTIONS = {
        'machine_identity', 'python_runtime', 'cpu', 'memory', 'gpu', 
        'network', 'storage', 'user_paths', 'display', 'launch_commands',
    }
    
    ZMACHINE_EDITABLE_SECTIONS = {
        'user_preferences', 'time_date_formatting', 'custom',
    }
    
    
    @staticmethod
    def detect_root_key(
        key: str,
        emitter: 'TokenEmitter',
        indent: int
    ) -> TokenType:
        """
        Detect token type for root-level keys.
        
        Args:
            key: The key name (without modifiers)
            emitter: TokenEmitter with file type context
            indent: Current indentation level
            
        Returns:
            Appropriate TokenType for the key
        """
        # zMeta in zUI or zSchema files (GREEN)
        if (emitter.is_zui_file and (key == 'zMeta' or key == 'zVaF' or key == emitter.zui_component_name)) or \
           (emitter.is_zschema_file and key == 'zMeta'):
            return TokenType.ZMETA_KEY
        
        # zSpark root key in zSpark files (LIGHT GREEN - ANSI 114)
        if emitter.is_zspark_file and key == 'zSpark':
            return TokenType.ZSPARK_KEY
        
        # Config root keys in zEnv files (PURPLE - ANSI 98)
        if emitter.is_zenv_file and key in KeyDetector.ZENV_CONFIG_ROOT_KEYS:
            return TokenType.ZENV_CONFIG_KEY
        
        # Uppercase Z-prefixed config keys in zEnv files (GREEN)
        if emitter.is_zenv_file and key.isupper() and key.startswith('Z'):
            return TokenType.ZCONFIG_KEY
        
        # zMachine root key in zConfig files (LIGHT GREEN - ANSI 114)
        if emitter.is_zconfig_file and key == 'zMachine':
            return TokenType.ZCONFIG_KEY
        
        # Uppercase Z-prefixed keys in zConfig files (e.g., ZPREFERENCES)
        if emitter.is_zconfig_file and key.isupper() and key.startswith('Z'):
            return TokenType.ZCONFIG_KEY
        
        # zConfig root key from filename (e.g., zMachine) in zConfig files (GREEN)
        if emitter.is_zconfig_file and key == emitter.zconfig_component_name:
            return TokenType.ZCONFIG_KEY
        
        # Default root key
        return TokenType.ROOT_KEY
    
    @staticmethod
    def detect_nested_key(
        key: str,
        emitter: 'TokenEmitter',
        indent: int
    ) -> TokenType:
        """
        Detect token type for nested keys.
        
        Args:
            key: The key name (without modifiers)
            emitter: TokenEmitter with file type and block context
            indent: Current indentation level
            
        Returns:
            Appropriate TokenType for the key
        """
        # zSpark nested keys (in zSpark files) - all nested keys under zSpark: root (LAVENDER)
        if emitter.is_zspark_file and emitter.is_in_zspark_block(indent):
            # All keys under zSpark: should be lavender (title, deployment, logger, zMode, etc.)
            return TokenType.ZSPARK_NESTED_KEY
        
        # zConfig hierarchical keys (in zConfig files)
        if emitter.is_zconfig_file and emitter.is_in_zmachine_block(indent):
            # Level 1 (indent == 1): Section headers (machine_identity, user_preferences, etc.)
            # Note: Parser counts indent levels, not spaces/tabs (1 tab = 1 level, 4 spaces = 1 level)
            if indent == 1:
                if key in KeyDetector.ZMACHINE_LOCKED_SECTIONS:
                    return TokenType.ZMACHINE_LOCKED_KEY  # RED
                elif key in KeyDetector.ZMACHINE_EDITABLE_SECTIONS:
                    return TokenType.ZMACHINE_EDITABLE_KEY  # BLUE
                # Default to NESTED_KEY if not in either set
                return TokenType.NESTED_KEY
            
            # Level 2+ (indent >= 2): Property keys under sections (os, browser, etc.)
            elif indent >= 2:
                return TokenType.ZCONFIG_NESTED_KEY  # LAVENDER
        
        # zRBAC key (TOMATO RED - ANSI 196)
        if key == 'zRBAC' and (emitter.is_zenv_file or emitter.is_zui_file):
            return TokenType.ZRBAC_KEY
        
        # zRBAC option keys (PURPLE 98)
        if emitter.is_in_zrbac_block(indent):
            ZRBAC_OPTION_KEYS = {'access', 'role', 'permissions', 'owner', 'public', 'private'}
            if key in ZRBAC_OPTION_KEYS:
                return TokenType.ZRBAC_OPTION_KEY
        
        # ZNAVBAR first-level nested keys (ANSI 208 in zEnv files)
        if emitter.is_znavbar_first_level(indent) and emitter.is_zenv_file:
            return TokenType.ZNAVBAR_NESTED_KEY
        
        # zKernel zData keys under zMeta in zSchema files (PURPLE 98)
        if emitter.is_inside_zmeta(indent) and emitter.is_zschema_file:
            if key in KeyDetector.ZKERNEL_DATA_KEYS:
                return TokenType.ZKERNEL_DATA_KEY
        
        # zSchema property keys (PURPLE 98)
        if emitter.is_zschema_file and not emitter.is_inside_zmeta(indent):
            # Check if we're inside a field definition (grandchild+ level)
            if indent >= 4 and key in KeyDetector.ZSCHEMA_PROPERTY_KEYS:
                return TokenType.ZSCHEMA_PROPERTY_KEY
        
        # zImage key and enter block
        if key == 'zImage' and emitter.is_zui_file:
            return TokenType.UI_ELEMENT_KEY
        
        # zText key
        if key == 'zText' and emitter.is_zui_file:
            return TokenType.UI_ELEMENT_KEY
        
        # zMD key
        if key == 'zMD' and emitter.is_zui_file:
            return TokenType.UI_ELEMENT_KEY
        
        # zURL key
        if key == 'zURL' and emitter.is_zui_file:
            return TokenType.UI_ELEMENT_KEY
        
        # zH1-zH6 keys
        if key in {'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'} and emitter.is_zui_file:
            return TokenType.UI_ELEMENT_KEY
        
        
        # zSub key (purple 98 when grandchild+ in zEnv/zUI files)
        if key == 'zSub':
            if (emitter.is_zenv_file or emitter.is_zui_file) and indent >= 4:
                return TokenType.ZSUB_KEY
            else:
                return TokenType.UI_ELEMENT_KEY
        
        # Bifrost keys (underscore-prefixed)
        if key.startswith('_'):
            return TokenType.BIFROST_KEY
        
        # Specific UI element keys
        if emitter.is_zui_file and key in KeyDetector.UI_ELEMENT_KEYS:
            return TokenType.UI_ELEMENT_KEY
        
        # UI element property keys (src, etc.) inside UI elements
        if emitter.is_zui_file and key in KeyDetector.UI_ELEMENT_PROPERTY_KEYS:
            # Check if we're inside any UI element block
            ui_block_types = ['zimage', 'ztext', 'zmd', 'zurl', 'zul', 'ztable', 'header']
            for block_type in ui_block_types:
                if emitter.is_inside_block(block_type, indent):
                    return TokenType.UI_ELEMENT_PROPERTY_KEY
        
        # Default nested key
        return TokenType.NESTED_KEY
    
    @staticmethod
    def extract_modifiers(key: str) -> tuple[str, Optional[str], Optional[str]]:
        """
        Extract key modifiers (^, ~, !, *) from a key name.
        
        Args:
            key: The full key name with potential modifiers
            
        Returns:
            Tuple of (core_key, prefix_modifier, suffix_modifier)
            
        Examples:
            >>> extract_modifiers('^locked')
            ('locked', '^', None)
            >>> extract_modifiers('editable!')
            ('editable', None, '!')
            >>> extract_modifiers('~default*')
            ('default', '~', '*')
        """
        prefix_modifier = None
        suffix_modifier = None
        core_key = key
        
        # Check prefix modifiers (^ or ~)
        if key and key[0] in ('^', '~'):
            prefix_modifier = key[0]
            core_key = key[1:]
        
        # Check suffix modifiers (! or *)
        if core_key and core_key[-1] in ('!', '*'):
            suffix_modifier = core_key[-1]
            core_key = core_key[:-1]
        
        return core_key, prefix_modifier, suffix_modifier
    
    @staticmethod
    def should_enter_block(key: str, emitter: 'TokenEmitter') -> Optional[str]:
        """
        Determine if a key should trigger entering a block context.
        
        Args:
            key: The key name (without modifiers)
            emitter: TokenEmitter with file type context
            
        Returns:
            Block type name if should enter, None otherwise
        """
        # zRBAC block
        if key == 'zRBAC':
            return 'zrbac'
        
        # zMeta block in zSchema files
        if key == 'zMeta' and emitter.is_zschema_file:
            return 'zmeta'
        
        # ZNAVBAR block
        if key == 'ZNAVBAR':
            return 'znavbar'
        
        # UI element blocks
        if emitter.is_zui_file:
            if key == 'zImage':
                return 'zimage'
            elif key == 'zText':
                return 'ztext'
            elif key == 'zMD':
                return 'zmd'
            elif key == 'zURL':
                return 'zurl'
            elif key == 'zUL':
                return 'zul'
            elif key == 'zTable':
                return 'ztable'
            elif key in {'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'}:
                return 'header'
        
        return None


# Helper functions for backward compatibility
def detect_key_type(
    key: str,
    emitter: 'TokenEmitter',
    indent: int,
    is_root: bool = False
) -> TokenType:
    """
    Convenience function to detect key type.
    
    Args:
        key: The key name (without modifiers)
        emitter: TokenEmitter with file type and block context
        indent: Current indentation level
        is_root: Whether this is a root-level key
        
    Returns:
        Appropriate TokenType for the key
    """
    if is_root:
        return KeyDetector.detect_root_key(key, emitter, indent)
    else:
        return KeyDetector.detect_nested_key(key, emitter, indent)
