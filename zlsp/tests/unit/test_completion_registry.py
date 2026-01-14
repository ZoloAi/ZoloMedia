"""
Tests for CompletionRegistry - Context-Aware Completions

Tests smart completions based on file type and cursor context.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lsprotocol import types as lsp_types

from core.providers.provider_modules.completion_registry import (
    CompletionContext,
    CompletionRegistry
)
from core.parser.parser_modules.file_type_detector import FileType


class TestCompletionContext:
    """Test CompletionContext - cursor position detection."""
    
    def test_detect_in_parentheses(self):
        """Test detecting cursor inside type hint parentheses."""
        content = "port(int): 8080"
        context = CompletionContext(content, line=0, character=5)
        
        assert context.in_parentheses is True
    
    def test_not_in_parentheses(self):
        """Test detecting cursor NOT in parentheses."""
        content = "port: 8080"
        context = CompletionContext(content, line=0, character=5)
        
        assert context.in_parentheses is False
    
    def test_after_closing_paren(self):
        """Test cursor after closing parenthesis."""
        content = "port(int): 8080"
        context = CompletionContext(content, line=0, character=10)
        
        assert context.in_parentheses is False
    
    def test_detect_after_colon(self):
        """Test detecting cursor after colon (value position)."""
        content = "port: "
        context = CompletionContext(content, line=0, character=6)
        
        assert context.after_colon is True
    
    def test_not_after_colon(self):
        """Test cursor NOT after colon."""
        content = "port"
        context = CompletionContext(content, line=0, character=4)
        
        assert context.after_colon is False
    
    def test_detect_at_line_start(self):
        """Test detecting cursor at line start (key position)."""
        content = "  "
        context = CompletionContext(content, line=0, character=2)
        
        assert context.at_line_start is True
    
    def test_not_at_line_start(self):
        """Test cursor NOT at line start."""
        content = "  port"
        context = CompletionContext(content, line=0, character=6)
        
        assert context.at_line_start is False
    
    def test_detect_current_key(self):
        """Test extracting current key name."""
        content = "port: 8080"
        context = CompletionContext(content, line=0, character=5)
        
        assert context.current_key == "port"
    
    def test_detect_key_with_type_hint(self):
        """Test extracting key with type hint."""
        content = "port(int): 8080"
        context = CompletionContext(content, line=0, character=10)
        
        assert context.current_key == "port"
    
    def test_detect_key_with_modifiers(self):
        """Test extracting key with modifiers."""
        content = "^port!: 8080"
        context = CompletionContext(content, line=0, character=7)
        
        assert context.current_key == "port"
    
    def test_no_current_key(self):
        """Test when there's no key."""
        content = "port"
        context = CompletionContext(content, line=0, character=4)
        
        assert context.current_key is None
    
    def test_file_type_detection(self):
        """Test that file type is detected."""
        content = "zSpark: MyApp"
        context = CompletionContext(content, line=0, character=7, filename="zSpark.myapp.zolo")
        
        assert context.file_type == FileType.ZSPARK
    
    def test_generic_file_type(self):
        """Test generic file type for unknown files."""
        content = "key: value"
        context = CompletionContext(content, line=0, character=5)
        
        assert context.file_type == FileType.GENERIC


class TestCompletionRegistry:
    """Test CompletionRegistry - smart completion generation."""
    
    def test_type_hint_completions(self):
        """Test type hint completions (inside parentheses)."""
        content = "port(int"
        context = CompletionContext(content, line=0, character=5)
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return type hint completions
        assert len(completions) == 12  # All 12 type hints
        
        labels = [item.label for item in completions]
        assert "int" in labels
        assert "str" in labels
        assert "bool" in labels
    
    def test_type_hint_completion_format(self):
        """Test that type hint completions have correct format."""
        content = "port("
        context = CompletionContext(content, line=0, character=5)
        
        completions = CompletionRegistry.get_completions(context)
        
        # Check first completion
        int_item = next(item for item in completions if item.label == "int")
        
        assert int_item.kind == lsp_types.CompletionItemKind.TypeParameter
        assert int_item.detail == "Integer Number"
        assert "integer" in int_item.documentation.value.lower()
        assert int_item.insert_text == "int"
    
    def test_value_completions(self):
        """Test value completions (after colon)."""
        content = "enabled: "
        context = CompletionContext(content, line=0, character=9)
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return value completions (true, false - null is a type hint)
        assert len(completions) == 2
        
        labels = [item.label for item in completions]
        assert "true" in labels
        assert "false" in labels
    
    def test_zspark_deployment_completions(self):
        """Test zSpark deployment-specific completions."""
        content = "deployment: "
        context = CompletionContext(
            content,
            line=0,
            character=12,
            filename="zSpark.myapp.zolo"
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return deployment-specific completions
        labels = [item.label for item in completions]
        assert "Production" in labels
        assert "Development" in labels
    
    def test_zspark_logger_completions(self):
        """Test zSpark logger-specific completions."""
        content = "logger: "
        context = CompletionContext(
            content,
            line=0,
            character=8,
            filename="zSpark.myapp.zolo"
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return logger-specific completions
        labels = [item.label for item in completions]
        assert "DEBUG" in labels
        assert "INFO" in labels
        assert "WARNING" in labels
        assert "ERROR" in labels
        assert "CRITICAL" in labels
        assert "SESSION" in labels
        assert "PROD" in labels
    
    def test_zspark_zmode_completions(self):
        """Test zSpark zMode-specific completions."""
        content = "zMode: "
        context = CompletionContext(
            content,
            line=0,
            character=7,
            filename="zSpark.config.zolo"
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return zMode-specific completions
        labels = [item.label for item in completions]
        assert "Terminal" in labels
        assert "zBifrost" in labels
    
    def test_zui_zvafile_completions(self):
        """Test zUI zVaFile-specific completions."""
        content = "zVaFile: "
        context = CompletionContext(
            content,
            line=0,
            character=9,
            filename="zUI.example.zolo"
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return zVaFile-specific completions
        labels = [item.label for item in completions]
        assert "zTerminal" in labels
        assert "zWeb" in labels
        assert "zMobile" in labels
    
    def test_zui_zblock_completions(self):
        """Test zUI zBlock-specific completions."""
        content = "zBlock: "
        context = CompletionContext(
            content,
            line=0,
            character=8,
            filename="zUI.component.zolo"
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return zBlock-specific completions
        labels = [item.label for item in completions]
        assert "zTerminal" in labels
        assert "zHTML" in labels
        assert "zJSON" in labels
    
    def test_zschema_type_completions(self):
        """Test zSchema field type completions."""
        content = "  type: "
        context = CompletionContext(
            content,
            line=0,
            character=8,
            filename="zSchema.users.zolo"
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return field type completions
        labels = [item.label for item in completions]
        assert "string" in labels
        assert "integer" in labels
        assert "float" in labels
        assert "boolean" in labels
    
    def test_no_completions_without_context(self):
        """Test that no completions are returned without clear context."""
        content = "random text"
        context = CompletionContext(content, line=0, character=5)
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return empty list
        assert completions == []
    
    def test_generic_file_no_specific_completions(self):
        """Test that generic files don't get file-specific completions."""
        content = "deployment: "
        context = CompletionContext(
            content,
            line=0,
            character=12,
            filename="config.zolo"  # Generic, not zSpark
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return generic value completions, not deployment-specific
        labels = [item.label for item in completions]
        assert "Production" not in labels  # File-specific should not appear
        assert "true" in labels or "false" in labels  # Generic values should appear
    
    def test_ui_element_completions_at_line_start(self):
        """Test that UI element completions appear at line start."""
        content = ""
        context = CompletionContext(
            content,
            line=0,
            character=0
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return UI element completions
        labels = [item.label for item in completions]
        assert "zImage" in labels
        assert "zText" in labels
        assert "zH1" in labels
        assert "zTable" in labels
        assert len(completions) == 16  # All UI elements
    
    def test_ui_element_completions_in_zui_file(self):
        """Test that UI element completions appear in zUI files."""
        content = "zMeta:\n  "
        context = CompletionContext(
            content,
            line=1,
            character=2,
            filename="zUI.component.zolo"
        )
        
        completions = CompletionRegistry.get_completions(context)
        
        # Should return UI element completions
        labels = [item.label for item in completions]
        assert "zImage" in labels
        assert "zNavBar" in labels
    
    def test_ui_element_completion_format(self):
        """Test that UI element completions have correct format."""
        content = ""
        context = CompletionContext(content, line=0, character=0)
        
        completions = CompletionRegistry.get_completions(context)
        zimage = next((c for c in completions if c.label == "zImage"), None)
        
        assert zimage is not None
        assert zimage.kind == lsp_types.CompletionItemKind.Class
        assert zimage.detail == "Image element"
        assert zimage.insert_text == "zImage: "
        assert "Display an image" in zimage.documentation.value


class TestCompletionContextIntegration:
    """Test CompletionContext with FileTypeDetector integration."""
    
    def test_zspark_file_detection(self):
        """Test that zSpark files are detected."""
        content = "zSpark: MyApp"
        context = CompletionContext(
            content,
            line=0,
            character=7,
            filename="zSpark.myapp.zolo"
        )
        
        assert context.file_type == FileType.ZSPARK
    
    def test_zui_file_detection(self):
        """Test that zUI files are detected."""
        content = "zMeta:"
        context = CompletionContext(
            content,
            line=0,
            character=6,
            filename="zUI.component.zolo"
        )
        
        assert context.file_type == FileType.ZUI
    
    def test_zschema_file_detection(self):
        """Test that zSchema files are detected."""
        content = "users:"
        context = CompletionContext(
            content,
            line=0,
            character=6,
            filename="zSchema.users.zolo"
        )
        
        assert context.file_type == FileType.ZSCHEMA
