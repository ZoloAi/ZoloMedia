"""
Vim theme generator - Converts canonical theme to Vim highlight commands.
"""
from typing import Dict, Any
from . import BaseGenerator
from .. import Theme


class VimGenerator(BaseGenerator):
    """Generates Vim highlight commands from a theme."""
    
    def _get_editor_name(self) -> str:
        return 'vim'
    
    def _style_to_vim(self, style: str) -> str:
        """
        Convert generic style to Vim style attributes.
        
        Args:
            style: Style string ('none', 'bold', 'italic', 'bold,italic')
        
        Returns:
            Vim style string (e.g., 'cterm=NONE', 'cterm=bold')
        """
        if style == 'none':
            return 'cterm=NONE gui=NONE'
        elif style == 'bold':
            return 'cterm=bold gui=bold'
        elif style == 'italic':
            return 'cterm=italic gui=italic'
        elif style == 'bold,italic':
            return 'cterm=bold,italic gui=bold,italic'
        else:
            return 'cterm=NONE gui=NONE'
    
    def _generate_highlight(self, group_name: str, token_style: Dict[str, Any]) -> str:
        """
        Generate a single Vim highlight command.
        
        Args:
            group_name: Vim highlight group name (e.g., 'LspSemanticRootKey')
            token_style: Token style dict from theme
        
        Returns:
            Vim highlight command string
        """
        ansi = token_style.get('ansi', 7)
        hex_color = token_style.get('hex', '#ffffff')
        style = token_style.get('style', 'none')
        vim_style = self._style_to_vim(style)
        
        return f"highlight! {group_name} ctermfg={ansi} guifg={hex_color} {vim_style} term=NONE"
    
    def generate(self) -> str:
        """
        Generate complete Vim color scheme script.
        
        Returns:
            Vim script with all highlight commands
        """
        lines = []
        
        # Header
        lines.append('" ═══════════════════════════════════════════════════════════════')
        lines.append(f'" {self.theme.name} - Vim Color Scheme')
        lines.append('" ═══════════════════════════════════════════════════════════════')
        lines.append(f'" {self.theme.description}')
        lines.append(f'" Version: {self.theme.version}')
        lines.append(f'" Author: {self.theme.author}')
        lines.append('" Generated automatically from zlsp/themes/zolo_default.yaml')
        lines.append('" DO NOT EDIT - Changes will be overwritten!')
        lines.append('" ═══════════════════════════════════════════════════════════════')
        lines.append('')
        
        # Clear conflicting groups (if specified in overrides)
        clear_groups = self.overrides.get('clearGroups', [])
        if clear_groups:
            lines.append('" Clear conflicting default syntax groups')
            for group in clear_groups:
                lines.append(f'highlight! {group} gui=NONE cterm=NONE')
            lines.append('')
        
        # Generate highlights for each token type
        lines.append('" Semantic token highlights')
        
        # Map token types to Vim LSP semantic token names
        token_mapping = {
            'rootKey': 'LspSemanticRootKey',
            'nestedKey': 'LspSemanticNestedKey',
            'zsparkKey': 'LspSemanticZsparkKey',
            'string': 'LspSemanticString',
            'versionString': 'LspSemanticVersionString',
            'timeString': 'LspSemanticTimeString',
            'timestampString': 'LspSemanticTimestampString',
            'ratioString': 'LspSemanticRatioString',
            'number': 'LspSemanticNumber',
            'escapeSequence': 'LspSemanticEscapeSequence',
            'typeHint': 'LspSemanticTypeHint',
            'typeHintParen': 'LspSemanticTypeHintParen',
            'bracketStructural': 'LspSemanticBracketStructural',
            'braceStructural': 'LspSemanticBraceStructural',
            'stringBracket': 'LspSemanticStringBracket',
            'stringBrace': 'LspSemanticStringBrace',
            'boolean': 'LspSemanticBoolean',
            'null': 'LspSemanticNull',
            'zpathValue': 'LspSemanticZpathValue',
            'comment': 'LspSemanticComment',
        }
        
        for token_type, vim_group in token_mapping.items():
            token_style = self.theme.get_token_style(token_type)
            if token_style:
                description = token_style.get('description', '')
                lines.append(f'" {description}')
                lines.append(self._generate_highlight(vim_group, token_style))
                lines.append('')
        
        # Footer
        lines.append('" ═══════════════════════════════════════════════════════════════')
        lines.append('" Color Palette Reference')
        lines.append('" ═══════════════════════════════════════════════════════════════')
        
        for color_name, color_data in self.theme.palette.items():
            name = color_data.get('name', color_name)
            ansi = color_data.get('ansi', '?')
            hex_color = color_data.get('hex', '#??????')
            desc = color_data.get('description', '')
            lines.append(f'" {ansi:3} - {hex_color} - {name:20} {desc}')
        
        lines.append('" ═══════════════════════════════════════════════════════════════')
        
        return '\n'.join(lines)


def generate_vim_colors(theme: Theme) -> str:
    """
    Convenience function to generate Vim colors from a theme.
    
    Args:
        theme: Theme object
    
    Returns:
        Vim script string
    """
    generator = VimGenerator(theme)
    return generator.generate()


__all__ = ['VimGenerator', 'generate_vim_colors']
