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
        prefix = lines[self.line][:self.character]
        
        # At start if only whitespace before cursor
        return prefix.strip() == ''
    
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
        
        # Context 1: Type hints (inside parentheses)
        if context.in_parentheses:
            return CompletionRegistry._type_hint_completions()
        
        # Context 2: File-type-specific value completions (after colon)
        if context.after_colon and context.current_key:
            file_completions = CompletionRegistry._file_specific_completions(
                context.file_type,
                context.current_key
            )
            if file_completions:
                return file_completions
        
        # Context 3: General value completions (after colon)
        if context.after_colon:
            return CompletionRegistry._value_completions()
        
        # Context 4: UI element key completions (at line start)
        if context.at_line_start or context.file_type == FileType.ZUI:
            return CompletionRegistry._ui_element_completions()
        
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