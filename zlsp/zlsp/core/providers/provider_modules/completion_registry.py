"""
Completion Registry - Smart Context-Aware Completions

Generates completions based on:
- Cursor position (in parentheses, after colon, etc.)
- File type (zSpark, zUI, zSchema, etc.)
- Current key context (inside zRBAC, etc.)

Leverages FileTypeDetector from Phase 2.2!
"""

from typing import List, Optional
from lsprotocol import types as lsp_types

from .documentation_registry import DocumentationRegistry, DocumentationType
from ...parser.parser_modules.file_type_detector import FileType, detect_file_type


# Block-level keys that should NOT offer value completions
# These keys expect nested properties, not inline values
BLOCK_KEYS = {
    # UI Elements
    'zImage', 'zText', 'zMD', 'zURL', 'zUL', 'zOL', 'zDL', 'zTable',
    'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6',
    'zRBAC', 'zNavBar', 'zMeta', 'zInput',
    # Organizational blocks
    'zSpark', 'zMachine', 'zServer', 'zCLI',
    'zData', 'zRead', 'zCreate', 'zUpdate', 'zDelete', 'zSelect',
    'zSchema', 'zFields',
    # UI Element child blocks
    'items', 'window', 'columns', 'rows',
}


class CompletionContext:
    """
    Detected context for intelligent completions.
    
    Analyzes cursor position and file type to provide smart completions.
    """
    
    def __init__(
        self,
        content: str,
        line: int,
        character: int,
        filename: Optional[str] = None
    ):
        self.content = content
        self.line = line
        self.character = character
        self.filename = filename
        self.file_type = detect_file_type(filename) if filename else FileType.GENERIC
        
        # Detect context from cursor position
        self.in_parentheses = self._detect_in_parentheses()
        self.after_colon = self._detect_after_colon()
        self.at_line_start = self._detect_at_line_start()
        self.current_key = self._detect_current_key()
    
    def _detect_in_parentheses(self) -> bool:
        """Check if cursor is inside type hint parentheses."""
        lines = self.content.splitlines()
        if self.line >= len(lines):
            return False
        
        prefix = lines[self.line][:self.character]
        
        # Check if we're between ( and )
        open_count = prefix.count('(')
        close_count = prefix.count(')')
        
        return open_count > close_count
    
    def _detect_after_colon(self) -> bool:
        """Check if cursor is after a colon (value position)."""
        lines = self.content.splitlines()
        if self.line >= len(lines):
            return False
        
        prefix = lines[self.line][:self.character]
        
        # Check if there's a : before cursor
        return ':' in prefix and prefix.strip().endswith(':')
    
    def _detect_at_line_start(self) -> bool:
        """Check if cursor is at the start of a line (key position)."""
        lines = self.content.splitlines()
        
        # Empty content or beyond last line → consider as line start
        if not lines or self.line >= len(lines):
            return True
        
        line_content = lines[self.line]
        prefix = line_content[:self.character]
        
        # At start if only whitespace before cursor
        if prefix.strip() == '':
            return True
        
        # Also consider "at line start" if we're typing a key (no colon yet)
        # This allows completions while typing "zS" → "zSpark:"
        if ':' not in line_content:
            return True
        
        return False
    
    def _detect_current_key(self) -> Optional[str]:
        """Extract the key name at the current line."""
        lines = self.content.splitlines()
        if self.line >= len(lines):
            return None
        
        line_content = lines[self.line]
        
        # Extract key before colon
        if ':' in line_content:
            key_part = line_content.split(':')[0].strip()
            
            # Remove type hint if present
            if '(' in key_part:
                key_part = key_part.split('(')[0].strip()
            
            # Remove modifiers (^, ~, !, *)
            key_part = key_part.lstrip('^~').rstrip('!*')
            
            return key_part if key_part else None
        
        return None


class CompletionRegistry:
    """
    Generate context-aware completions.
    
    Uses DocumentationRegistry as SSOT and FileTypeDetector for file-specific completions.
    """
    
    @staticmethod
    def get_completions(context: CompletionContext) -> List[lsp_types.CompletionItem]:
        """
        Get completions based on context.
        
        Args:
            context: CompletionContext with cursor position and file info
        
        Returns:
            List of completion items
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🎯 Completion Context Detection:")
        logger.info(f"   File: {context.filename}")
        logger.info(f"   File type: {context.file_type}")
        logger.info(f"   Line {context.line}, char {context.character}")
        logger.info(f"   in_parentheses: {context.in_parentheses}")
        logger.info(f"   after_colon: {context.after_colon}")
        logger.info(f"   at_line_start: {context.at_line_start}")
        logger.info(f"   current_key: {context.current_key}")
        
        # Context 1: Type hints (inside parentheses)
        if context.in_parentheses:
            logger.info("➡️  Using type hint completions")
            return CompletionRegistry._type_hint_completions()
        
        # Context 2: File-type-specific value completions (after colon)
        if context.after_colon and context.current_key:
            # Skip completions for block-level keys (they expect nested properties, not values)
            if context.current_key in BLOCK_KEYS:
                logger.info(f"➡️  Skipping value completions for block key '{context.current_key}'")
                return []
            
            logger.info(f"➡️  Using file-specific value completions for key '{context.current_key}'")
            file_completions = CompletionRegistry._file_specific_completions(
                context.file_type,
                context.current_key
            )
            if file_completions:
                return file_completions
        
        # Context 3: General value completions (after colon)
        if context.after_colon:
            # Skip completions if current key is a block key
            if context.current_key and context.current_key in BLOCK_KEYS:
                logger.info(f"➡️  Skipping general value completions for block key '{context.current_key}'")
                return []
            
            logger.info("➡️  Using general value completions")
            return CompletionRegistry._value_completions()
        
        # Context 4: File-type-specific key completions (at line start) - YAML-DRIVEN!
        if context.at_line_start:
            logger.info("➡️  Using YAML-driven key completions")
            return CompletionRegistry._get_key_completions_from_yaml(context)
        
        logger.info("❌ No matching context - returning empty completions")
        return []
    
    @staticmethod
    def _type_hint_completions() -> List[lsp_types.CompletionItem]:
        """Generate type hint completions from DocumentationRegistry."""
        docs = DocumentationRegistry.get_by_type(DocumentationType.TYPE_HINT)
        
        items = []
        for doc in docs:
            items.append(
                lsp_types.CompletionItem(
                    label=doc.label,
                    kind=lsp_types.CompletionItemKind.TypeParameter,
                    detail=doc.to_completion_detail(),
                    documentation=lsp_types.MarkupContent(
                        kind=lsp_types.MarkupKind.Markdown,
                        value=doc.to_completion_documentation()
                    ),
                    insert_text=doc.label,
                    sort_text=f"0{doc.label}"  # Sort type hints first
                )
            )
        
        return items
    
    @staticmethod
    def _value_completions() -> List[lsp_types.CompletionItem]:
        """Generate common value completions (true, false, null)."""
        docs = DocumentationRegistry.get_by_type(DocumentationType.VALUE)
        
        items = []
        for doc in docs:
            items.append(
                lsp_types.CompletionItem(
                    label=doc.label,
                    kind=lsp_types.CompletionItemKind.Value,
                    detail=doc.to_completion_detail(),
                    documentation=lsp_types.MarkupContent(
                        kind=lsp_types.MarkupKind.Markdown,
                        value=doc.to_completion_documentation()
                    ),
                    insert_text=doc.label,
                    sort_text=f"1{doc.label}"
                )
            )
        
        return items
    
    @staticmethod
    def _file_specific_completions(
        file_type: FileType,
        key: str
    ) -> Optional[List[lsp_types.CompletionItem]]:
        """
        Generate file-type and key-specific completions.
        
        Args:
            file_type: Type of .zolo file (ZSPARK, ZUI, etc.)
            key: Current key name
        
        Returns:
            List of completion items, or None if no specific completions
        """
        
        # zSpark.*.zolo completions
        if file_type == FileType.ZSPARK:
            if key == "deployment":
                return CompletionRegistry._create_simple_completions(
                    ["Production", "Development"],
                    lsp_types.CompletionItemKind.EnumMember,
                    "Deployment environment"
                )
            elif key == "logger":
                return CompletionRegistry._create_simple_completions(
                    ["DEBUG", "SESSION", "INFO", "WARNING", "ERROR", "CRITICAL", "PROD"],
                    lsp_types.CompletionItemKind.EnumMember,
                    "Logger level"
                )
            elif key == "zMode":
                return CompletionRegistry._create_simple_completions(
                    ["Terminal", "zBifrost"],
                    lsp_types.CompletionItemKind.EnumMember,
                    "Execution mode"
                )
        
        # zUI.*.zolo completions
        elif file_type == FileType.ZUI:
            if key == "zVaFile":
                return CompletionRegistry._create_simple_completions(
                    ["zTerminal", "zWeb", "zMobile"],
                    lsp_types.CompletionItemKind.EnumMember,
                    "zVaFile type"
                )
            elif key == "zBlock":
                return CompletionRegistry._create_simple_completions(
                    ["zTerminal", "zHTML", "zJSON"],
                    lsp_types.CompletionItemKind.EnumMember,
                    "zBlock type"
                )
        
        # zSchema.*.zolo completions
        elif file_type == FileType.ZSCHEMA:
            if key == "type":
                return CompletionRegistry._create_simple_completions(
                    ["string", "integer", "float", "boolean", "date", "datetime"],
                    lsp_types.CompletionItemKind.EnumMember,
                    "Field type"
                )
        
        return None
    
    @staticmethod
    def _create_simple_completions(
        values: List[str],
        kind: lsp_types.CompletionItemKind,
        detail: str
    ) -> List[lsp_types.CompletionItem]:
        """Helper to create simple completion items from a list of values."""
        items = []
        for value in values:
            items.append(
                lsp_types.CompletionItem(
                    label=value,
                    kind=kind,
                    detail=detail,
                    insert_text=value,
                    sort_text=f"0{value}"
                )
            )
        return items
    
    @staticmethod
    def _get_key_completions_from_yaml(context: CompletionContext) -> List[lsp_types.CompletionItem]:
        """
        Get file-type-specific key completions from YAML theme (SSOT approach).
        
        This is the new modular, YAML-driven completion system.
        Each file type has its completions defined in themes/zolo_default.yaml.
        
        Args:
            context: Completion context with file type and cursor position
        
        Returns:
            List of LSP completion items generated from YAML
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from themes import load_theme, CompletionRegistry as ThemeCompletionRegistry
            
            # Load theme and get completions for this file type
            theme = load_theme('zolo_default')
            registry = ThemeCompletionRegistry(theme)
            
            if not registry.is_enabled():
                logger.info("❌ YAML completions disabled in theme config")
                return []
            
            # Detect indentation level and parent key
            indent_level = CompletionRegistry._get_indent_level(context)
            parent_key = CompletionRegistry._get_parent_key(context)
            
            logger.info(f"🔍 YAML Completion Context:")
            logger.info(f"   File type: {context.file_type} ({context.file_type.value})")
            logger.info(f"   Indent level: {indent_level}")
            logger.info(f"   Parent key: {parent_key}")
            logger.info(f"   Line {context.line}, char {context.character}")
            
            # Get completions from YAML for this context
            file_type_key = context.file_type.value  # 'zspark', 'zschema', etc.
            yaml_completions = registry.get_completions_for_context(
                file_type_key,
                indent_level,
                parent_key
            )
            
            logger.info(f"📦 YAML returned {len(yaml_completions)} completions")
            if yaml_completions:
                for comp in yaml_completions[:3]:  # Log first 3
                    logger.info(f"   - {comp.get('label')}")
            
            # Convert YAML definitions to LSP CompletionItems
            lsp_items = CompletionRegistry._yaml_to_lsp_completions(yaml_completions)
            logger.info(f"✅ Converted to {len(lsp_items)} LSP items")
            return lsp_items
        
        except Exception as e:
            # Fallback to empty list if theme loading fails
            logger.error(f"❌ Failed to load YAML completions: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _get_indent_level(context: CompletionContext) -> int:
        """
        Get the indentation level at current cursor position.
        
        Returns:
            Indentation level in spaces (0, 2, 4, etc.)
        """
        lines = context.content.splitlines()
        if context.line >= len(lines):
            return 0
        
        current_line = lines[context.line]
        leading_space = current_line[:len(current_line) - len(current_line.lstrip())]
        return len(leading_space)
    
    @staticmethod
    def _get_parent_key(context: CompletionContext) -> Optional[str]:
        """
        Find the parent key for the current indentation level.
        
        Searches backwards for a less-indented line with a key.
        
        Returns:
            Parent key name or None if at root level
        """
        lines = context.content.splitlines()
        if context.line <= 0 or context.line >= len(lines):
            return None
        
        current_indent = CompletionRegistry._get_indent_level(context)
        
        # Search backwards for parent
        for i in range(context.line - 1, -1, -1):
            line = lines[i].strip()
            if not line or line.startswith('#'):
                continue
            
            line_indent = len(lines[i]) - len(lines[i].lstrip())
            
            # Found parent (less indented line with a key)
            if line_indent < current_indent and ':' in line:
                key = line.split(':')[0].strip()
                return key
        
        return None
    
    @staticmethod
    def _yaml_to_lsp_completions(yaml_completions: List[dict]) -> List[lsp_types.CompletionItem]:
        """
        Convert YAML completion definitions to LSP CompletionItems.
        
        Args:
            yaml_completions: List of completion dicts from YAML
        
        Returns:
            List of LSP CompletionItems
        """
        items = []
        
        kind_map = {
            'class': lsp_types.CompletionItemKind.Class,
            'property': lsp_types.CompletionItemKind.Property,
            'value': lsp_types.CompletionItemKind.Value,
            'keyword': lsp_types.CompletionItemKind.Keyword,
            'snippet': lsp_types.CompletionItemKind.Snippet,
        }
        
        for yaml_item in yaml_completions:
            label = yaml_item.get('label', '')
            if not label:
                continue
            
            kind_str = yaml_item.get('kind', 'property')
            kind = kind_map.get(kind_str, lsp_types.CompletionItemKind.Property)
            
            detail = yaml_item.get('detail', '')
            documentation = yaml_item.get('documentation', '')
            insert_text = yaml_item.get('insert_text', label + ': ')
            priority = yaml_item.get('priority', 1)
            preselect = yaml_item.get('preselect', False)
            
            # Check if this is a snippet with placeholder support
            insert_text_format_str = yaml_item.get('insert_text_format', 'plaintext')
            insert_text_format = (
                lsp_types.InsertTextFormat.Snippet 
                if insert_text_format_str == 'snippet' 
                else lsp_types.InsertTextFormat.PlainText
            )
            
            items.append(
                lsp_types.CompletionItem(
                    label=label,
                    kind=kind,
                    detail=detail,
                    documentation=lsp_types.MarkupContent(
                        kind=lsp_types.MarkupKind.Markdown,
                        value=documentation
                    ) if documentation else None,
                    insert_text=insert_text,
                    insert_text_format=insert_text_format,
                    sort_text=f"{priority}_{label}",
                    preselect=preselect
                )
            )
        
        return items
    
    @staticmethod
    def _ui_element_completions() -> List[lsp_types.CompletionItem]:
        """Generate UI element key completions (zImage, zText, zURL, etc.)."""
        ui_elements = [
            ("zImage", "Image element", "Display an image", "zImage: "),
            ("zURL", "URL/Link", "Single URL link", "zURL: "),
            ("zURLs", "Multiple URLs", "List of URL links", "zURLs: "),
            ("zText", "Text element", "Display text", "zText: "),
            ("zTexts", "Multiple texts", "List of text items", "zTexts: "),
            ("zH1", "Heading 1", "Large heading", "zH1: "),
            ("zH2", "Heading 2", "Medium heading", "zH2: "),
            ("zH3", "Heading 3", "Small heading", "zH3: "),
            ("zH4", "Heading 4", "Small heading", "zH4: "),
            ("zH5", "Heading 5", "Tiny heading", "zH5: "),
            ("zH6", "Heading 6", "Tiny heading", "zH6: "),
            ("zUL", "Unordered list", "Bullet list", "zUL: "),
            ("zOL", "Ordered list", "Numbered list", "zOL: "),
            ("zDL", "Description list", "Term-definition list", "zDL: "),
            ("zMD", "Markdown", "Markdown content", "zMD: "),
            ("zTable", "Table", "Data table", "zTable: "),
            ("zNavBar", "Navigation bar", "Enable/disable navbar", "zNavBar: "),
        ]
        
        items = []
        for label, detail, doc, insert_text in ui_elements:
            items.append(
                lsp_types.CompletionItem(
                    label=label,
                    kind=lsp_types.CompletionItemKind.Class,
                    detail=detail,
                    documentation=lsp_types.MarkupContent(
                        kind=lsp_types.MarkupKind.Markdown,
                        value=f"{doc}\n\nExample: `{insert_text}value`"
                    ),
                    insert_text=insert_text,
                    sort_text=f"0{label}"
                )
            )
        
        return items