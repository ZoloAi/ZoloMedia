"""
VS Code theme generator - Converts canonical theme to VS Code formats.

Generates:
1. TextMate grammar (syntaxes/zolo.tmLanguage.json)
2. Color theme (themes/zolo-dark.color-theme.json)
3. Semantic token legend (for package.json)
"""
import json
from typing import Dict, Any, List
from . import BaseGenerator
from .. import Theme


class VSCodeGenerator(BaseGenerator):
    """Generates VS Code extension files from a theme."""
    
    def _get_editor_name(self) -> str:
        return 'vscode'
    
    def _style_to_vscode(self, style: str) -> Dict[str, Any]:
        """
        Convert generic style to VS Code fontStyle.
        
        Args:
            style: Style string ('none', 'bold', 'italic', 'bold,italic')
        
        Returns:
            Dictionary with VS Code fontStyle
        """
        if style == 'none':
            return {}
        elif style == 'bold':
            return {'fontStyle': 'bold'}
        elif style == 'italic':
            return {'fontStyle': 'italic'}
        elif style == 'bold,italic':
            return {'fontStyle': 'bold italic'}
        else:
            return {}
    
    def generate_textmate_grammar(self) -> Dict[str, Any]:
        """
        Generate TextMate grammar from theme.
        
        Returns:
            Dictionary representing zolo.tmLanguage.json
        """
        grammar = {
            "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
            "name": "Zolo",
            "scopeName": "source.zolo",
            "fileTypes": ["zolo"],
            "patterns": [
                {"include": "#comments"},
                {"include": "#type-hints"},
                {"include": "#special-root-keys"},
                {"include": "#keys"},
                {"include": "#triple-quoted-strings"},
                {"include": "#pipe-multiline"},
                {"include": "#strings"},
                {"include": "#numbers"},
                {"include": "#booleans"},
                {"include": "#null"},
                {"include": "#arrays"},
                {"include": "#objects"},
                {"include": "#dash-lists"}
            ],
            "repository": {
                "comments": {
                    "patterns": [
                        {
                            "name": "comment.line.number-sign.zolo",
                            "match": "#.*$"
                        }
                    ]
                },
                "type-hints": {
                    "patterns": [
                        {
                            "name": "storage.type.zolo",
                            "match": "@(str|int|float|bool|list|dict|null)\\b"
                        }
                    ]
                },
                "special-root-keys": {
                    "comment": "Special Zolo root keys (zSpark, ZNAVBAR, zMeta, etc.)",
                    "patterns": [
                        {
                            "name": "entity.name.tag.zolo",
                            "match": "^\\s*(zSpark|ZNAVBAR|zMeta|zVaF|zRBAC|zSub|BIFROST)(?=:)"
                        }
                    ]
                },
                "keys": {
                    "patterns": [
                        {
                            "name": "entity.name.function.zolo",
                            "match": "^\\s*[^#:\\s][^:]*(?=:)"
                        },
                        {
                            "name": "variable.other.property.zolo",
                            "match": "(?<=\\s)[^#:\\s][^:]*(?=:)"
                        }
                    ]
                },
                "triple-quoted-strings": {
                    "comment": "Triple-quoted multiline strings",
                    "patterns": [
                        {
                            "name": "string.quoted.triple.zolo",
                            "begin": "\"\"\"",
                            "end": "\"\"\"",
                            "patterns": [
                                {
                                    "name": "constant.character.escape.zolo",
                                    "match": "\\\\."
                                }
                            ]
                        },
                        {
                            "name": "string.quoted.triple.zolo",
                            "begin": "'''",
                            "end": "'''",
                            "patterns": [
                                {
                                    "name": "constant.character.escape.zolo",
                                    "match": "\\\\."
                                }
                            ]
                        }
                    ]
                },
                "pipe-multiline": {
                    "comment": "Pipe multiline strings (|)",
                    "patterns": [
                        {
                            "name": "string.unquoted.pipe.zolo",
                            "match": "^\\s*\\|.*$"
                        }
                    ]
                },
                "strings": {
                    "patterns": [
                        {
                            "name": "string.quoted.double.zolo",
                            "begin": "\"",
                            "end": "\"",
                            "patterns": [
                                {
                                    "name": "constant.character.escape.zolo",
                                    "match": "\\\\([\"\\\\/bfnrt]|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2})"
                                }
                            ]
                        },
                        {
                            "name": "string.quoted.single.zolo",
                            "begin": "'",
                            "end": "'",
                            "patterns": [
                                {
                                    "name": "constant.character.escape.zolo",
                                    "match": "\\\\(['\\\\/bfnrt]|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2})"
                                }
                            ]
                        },
                        {
                            "comment": "Unquoted strings (Zolo's string-first philosophy)",
                            "name": "string.unquoted.zolo",
                            "match": "(?<=:\\s)[^#\\[\\{\\n][^\\n]*"
                        }
                    ]
                },
                "numbers": {
                    "patterns": [
                        {
                            "name": "constant.numeric.zolo",
                            "match": "(?<=:\\s)-?[0-9]+(\\.[0-9]+)?([eE][+-]?[0-9]+)?\\b"
                        }
                    ]
                },
                "booleans": {
                    "patterns": [
                        {
                            "name": "constant.language.boolean.zolo",
                            "match": "(?<=:\\s)(true|false|True|False)\\b"
                        }
                    ]
                },
                "null": {
                    "patterns": [
                        {
                            "name": "constant.language.null.zolo",
                            "match": "(?<=:\\s)(null|None)\\b"
                        }
                    ]
                },
                "arrays": {
                    "patterns": [
                        {
                            "name": "meta.structure.array.zolo",
                            "begin": "\\[",
                            "end": "\\]",
                            "patterns": [
                                {"include": "#comments"},
                                {"include": "#strings"},
                                {"include": "#numbers"},
                                {"include": "#booleans"},
                                {"include": "#null"},
                                {
                                    "name": "punctuation.separator.array.zolo",
                                    "match": ","
                                }
                            ]
                        }
                    ]
                },
                "objects": {
                    "patterns": [
                        {
                            "name": "meta.structure.dictionary.zolo",
                            "begin": "\\{",
                            "end": "\\}",
                            "patterns": [
                                {"include": "#comments"},
                                {"include": "#keys"},
                                {"include": "#strings"},
                                {"include": "#numbers"},
                                {"include": "#booleans"},
                                {"include": "#null"},
                                {
                                    "name": "punctuation.separator.dictionary.zolo",
                                    "match": ","
                                }
                            ]
                        }
                    ]
                },
                "dash-lists": {
                    "comment": "Dash list items (- item)",
                    "patterns": [
                        {
                            "name": "markup.list.unnumbered.zolo",
                            "match": "^\\s*-\\s+.*$"
                        }
                    ]
                }
            }
        }
        
        return grammar
    
    def generate_color_theme(self) -> Dict[str, Any]:
        """
        Generate VS Code color theme JSON (standalone Zolo Dark theme).
        
        Returns:
            Dictionary representing zolo-dark.color-theme.json
        """
        theme = {
            "$schema": "vscode://schemas/color-theme",
            "name": f"{self.theme.name} (Dark)",
            "type": "dark",
            "colors": {
                "editor.background": "#1e1e1e",
                "editor.foreground": "#d4d4d4",
                "editorLineNumber.foreground": "#858585",
                "editorCursor.foreground": "#aeafad",
                "editor.selectionBackground": "#264f78",
                "editor.inactiveSelectionBackground": "#3a3d41"
            },
            "tokenColors": []
        }
        
        # Add TextMate scope mappings (fallback when LSP is not running)
        scope_mappings = [
            {
                "scope": ["comment.line.number-sign.zolo"],
                "settings": self._get_token_color_settings('comment')
            },
            {
                "scope": ["storage.type.zolo"],
                "settings": self._get_token_color_settings('typeHint')
            },
            {
                "scope": ["entity.name.tag.zolo"],
                "settings": self._get_token_color_settings('rootKey')
            },
            {
                "scope": ["entity.name.function.zolo"],
                "settings": self._get_token_color_settings('rootKey')
            },
            {
                "scope": ["variable.other.property.zolo"],
                "settings": self._get_token_color_settings('nestedKey')
            },
            {
                "scope": ["string.quoted.double.zolo", "string.quoted.single.zolo", "string.unquoted.zolo"],
                "settings": self._get_token_color_settings('string')
            },
            {
                "scope": ["constant.numeric.zolo"],
                "settings": self._get_token_color_settings('number')
            },
            {
                "scope": ["constant.language.boolean.zolo"],
                "settings": self._get_token_color_settings('boolean')
            },
            {
                "scope": ["constant.language.null.zolo"],
                "settings": self._get_token_color_settings('null')
            },
            {
                "scope": ["constant.character.escape.zolo"],
                "settings": self._get_token_color_settings('escapeSequence')
            }
        ]
        
        theme["tokenColors"] = scope_mappings
        
        return theme
    
    def _get_token_color_settings(self, token_type: str) -> Dict[str, Any]:
        """
        Get VS Code color settings for a token type.
        
        Args:
            token_type: Token type from theme
        
        Returns:
            Dictionary with foreground color and fontStyle
        """
        token_style = self.theme.get_token_style(token_type)
        if not token_style:
            return {"foreground": "#ffffff"}
        
        settings = {"foreground": token_style.get('hex', '#ffffff')}
        
        # Add font style if not 'none'
        style = token_style.get('style', 'none')
        if style != 'none':
            font_style = self._style_to_vscode(style).get('fontStyle')
            if font_style:
                settings['fontStyle'] = font_style
        
        return settings
    
    def generate_semantic_tokens_legend(self) -> Dict[str, Any]:
        """
        Generate semantic token legend for package.json.
        
        CRITICAL: This order MUST match semantic_tokenizer.py's TOKEN_TYPES_LEGEND
        exactly, or else token indices will be misinterpreted!
        
        Returns:
            Dictionary with tokenTypes and tokenModifiers arrays
        """
        # MUST match semantic_tokenizer.py:TOKEN_TYPES_LEGEND (lines 56-97)
        # DO NOT REORDER! LSP server encodes tokens using these indices!
        token_types = [
            "comment",              # 0  - MUST be first!
            "rootKey",              # 1
            "nestedKey",            # 2
            "zmetaKey",             # 3
            "zkernelDataKey",       # 4
            "zschemaPropertyKey",   # 5
            "bifrostKey",           # 6
            "uiElementKey",         # 7
            "zconfigKey",           # 8
            "zsparkKey",            # 9
            "zenvConfigKey",        # 10
            "znavbarNestedKey",     # 11
            "zsubKey",              # 12
            "zsparkNestedKey",      # 13
            "zsparkModeValue",      # 14
            "zsparkVaFileValue",    # 15
            "zsparkSpecialValue",   # 16
            "envConfigValue",       # 17
            "zrbacKey",             # 18
            "zrbacOptionKey",       # 19
            "typeHint",             # 20
            "number",               # 21
            "string",               # 22
            "boolean",              # 23
            "null",                 # 24
            "bracketStructural",    # 25
            "braceStructural",      # 26
            "stringBracket",        # 27
            "stringBrace",          # 28
            "colon",                # 29
            "comma",                # 30
            "escapeSequence",       # 31
            "versionString",        # 32
            "timestampString",      # 33
            "timeString",           # 34
            "ratioString",          # 35
            "zpathValue",           # 36
            "zmachineEditableKey",  # 37
            "zmachineLockedKey",    # 38
            "typeHintParen",        # 39
        ]
        
        # Token modifiers (currently not used, but can be added later)
        token_modifiers = [
            "declaration",
            "definition",
            "readonly",
            "deprecated"
        ]
        
        return {
            "tokenTypes": token_types,
            "tokenModifiers": token_modifiers
        }
    
    def generate_semantic_tokens_styles(self) -> List[Dict[str, Any]]:
        """
        Generate semantic token styles for package.json.
        
        Returns:
            List of style rules mapping token types to colors
        """
        styles = []
        
        # Map all token types from theme to semantic token scopes
        # MUST include ALL types from TOKEN_TYPES_LEGEND
        token_mapping = {
            'comment': 'comment',
            'rootKey': 'rootKey',
            'nestedKey': 'nestedKey',
            'zmetaKey': 'zmetaKey',
            'zkernelDataKey': 'zkernelDataKey',
            'zschemaPropertyKey': 'zschemaPropertyKey',
            'bifrostKey': 'bifrostKey',
            'uiElementKey': 'uiElementKey',
            'zconfigKey': 'zconfigKey',
            'zsparkKey': 'zsparkKey',
            'zenvConfigKey': 'zenvConfigKey',
            'znavbarNestedKey': 'znavbarNestedKey',
            'zsubKey': 'zsubKey',
            'zsparkNestedKey': 'zsparkNestedKey',
            'zsparkModeValue': 'zsparkModeValue',
            'zsparkVaFileValue': 'zsparkVaFileValue',
            'zsparkSpecialValue': 'zsparkSpecialValue',
            'envConfigValue': 'envConfigValue',
            'zrbacKey': 'zrbacKey',
            'zrbacOptionKey': 'zrbacOptionKey',
            'typeHint': 'typeHint',
            'number': 'number',
            'string': 'string',
            'boolean': 'boolean',
            'null': 'null',
            'bracketStructural': 'bracketStructural',
            'braceStructural': 'braceStructural',
            'stringBracket': 'stringBracket',
            'stringBrace': 'stringBrace',
            'colon': 'colon',
            'comma': 'comma',
            'escapeSequence': 'escapeSequence',
            'versionString': 'versionString',
            'timestampString': 'timestampString',
            'timeString': 'timeString',
            'ratioString': 'ratioString',
            'zpathValue': 'zpathValue',
            'zmachineEditableKey': 'zmachineEditableKey',
            'zmachineLockedKey': 'zmachineLockedKey',
            'typeHintParen': 'typeHintParen',
        }
        
        for theme_token_type, semantic_token_type in token_mapping.items():
            token_style = self.theme.get_token_style(theme_token_type)
            if token_style:
                style_rule = {
                    "scope": semantic_token_type,
                    "settings": {
                        "foreground": token_style.get('hex', '#ffffff')
                    }
                }
                
                # Add font style if present
                style = token_style.get('style', 'none')
                if style != 'none':
                    font_style_dict = self._style_to_vscode(style)
                    if font_style_dict:
                        style_rule["settings"].update(font_style_dict)
                
                styles.append(style_rule)
        
        return styles
    
    def generate(self) -> str:
        """
        Generate a summary of what would be created.
        
        For actual file generation, use the specific generate_* methods.
        
        Returns:
            Summary string
        """
        lines = []
        
        lines.append("# " + "=" * 70)
        lines.append(f"# {self.theme.name} - VS Code Extension Files")
        lines.append("# " + "=" * 70)
        lines.append(f"# {self.theme.description}")
        lines.append(f"# Version: {self.theme.version}")
        lines.append(f"# Author: {self.theme.author}")
        lines.append("# Generated automatically from zlsp/themes/zolo_default.yaml")
        lines.append("# DO NOT EDIT - Changes will be overwritten!")
        lines.append("# " + "=" * 70)
        lines.append("")
        
        lines.append("Files to generate:")
        lines.append("  1. syntaxes/zolo.tmLanguage.json - TextMate grammar")
        lines.append("  2. themes/zolo-dark.color-theme.json - Color theme")
        lines.append("  3. Semantic token legend (for package.json)")
        lines.append("  4. Semantic token styles (for package.json)")
        lines.append("")
        
        lines.append(f"Token types: {len(self.theme.tokens)}")
        lines.append(f"Palette colors: {len(self.theme.palette)}")
        lines.append("")
        
        lines.append("Use specific methods to generate files:")
        lines.append("  - generate_textmate_grammar() -> dict")
        lines.append("  - generate_color_theme() -> dict")
        lines.append("  - generate_semantic_tokens_legend() -> dict")
        lines.append("  - generate_semantic_tokens_styles() -> list")
        
        return '\n'.join(lines)


def generate_vscode_files(theme: Theme) -> Dict[str, Any]:
    """
    Convenience function to generate all VS Code files from a theme.
    
    Args:
        theme: Theme object
    
    Returns:
        Dictionary with all generated content
    """
    generator = VSCodeGenerator(theme)
    return {
        'textmate_grammar': generator.generate_textmate_grammar(),
        'color_theme': generator.generate_color_theme(),
        'semantic_tokens_legend': generator.generate_semantic_tokens_legend(),
        'semantic_tokens_styles': generator.generate_semantic_tokens_styles(),
    }


__all__ = ['VSCodeGenerator', 'generate_vscode_files']
