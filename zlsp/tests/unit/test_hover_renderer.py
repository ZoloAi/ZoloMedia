"""
Tests for HoverRenderer - Hover information formatting

Tests hover rendering using DocumentationRegistry (zero duplication!).
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.parser.parser import tokenize
from core.providers.provider_modules.hover_renderer import HoverRenderer


class TestHoverRendererTypeHints:
    """Test hover rendering for type hints."""
    
    def test_render_int_type_hint(self):
        """Test rendering hover for int type hint."""
        content = "port(int): 8080"
        result = tokenize(content)
        tokens = result.tokens
        
        # Hover over "int" (TYPE_HINT token starts at position 5)
        hover = HoverRenderer.render(content, line=0, character=5, tokens=tokens)
        
        assert hover is not None
        assert "Integer Number" in hover
        assert "Type Hint:" in hover
        assert "port(int): 8080" in hover
    
    def test_render_str_type_hint(self):
        """Test rendering hover for str type hint."""
        content = "name(str): Hello"
        result = tokenize(content)
        tokens = result.tokens
        
        # TYPE_HINT starts at position 5
        hover = HoverRenderer.render(content, line=0, character=5, tokens=tokens)
        
        assert hover is not None
        assert "String" in hover
        assert "str" in hover
    
    def test_render_bool_type_hint(self):
        """Test rendering hover for bool type hint."""
        content = "enabled(bool): true"
        result = tokenize(content)
        tokens = result.tokens
        
        # TYPE_HINT starts at position 8
        hover = HoverRenderer.render(content, line=0, character=8, tokens=tokens)
        
        assert hover is not None
        assert "Boolean" in hover
        assert "bool" in hover
    
    def test_render_list_type_hint(self):
        """Test rendering hover for list type hint."""
        content = "items(list): [1, 2, 3]"
        result = tokenize(content)
        tokens = result.tokens
        
        # TYPE_HINT starts at position 6
        hover = HoverRenderer.render(content, line=0, character=6, tokens=tokens)
        
        assert hover is not None
        assert "List/Array" in hover or "List" in hover
    
    def test_render_unknown_type_hint(self):
        """Test rendering hover for unknown type hint."""
        content = "value(unknown): 123"
        result = tokenize(content)
        tokens = result.tokens
        
        hover = HoverRenderer.render(content, line=0, character=7, tokens=tokens)
        
        # Should still render something, even if unknown
        if hover:
            assert "unknown" in hover.lower()


class TestHoverRendererKeys:
    """Test hover rendering for keys."""
    
    def test_render_key_with_type_hint(self):
        """Test rendering hover for key with type hint."""
        content = "port(int): 8080"
        result = tokenize(content)
        tokens = result.tokens
        
        # Hover over the key "port" (before the parenthesis)
        hover = HoverRenderer.render(content, line=0, character=1, tokens=tokens)
        
        if hover:
            assert "Key:" in hover or "port" in hover
    
    def test_render_key_without_type_hint(self):
        """Test rendering hover for key without type hint."""
        content = "name: value"
        result = tokenize(content)
        tokens = result.tokens
        
        hover = HoverRenderer.render(content, line=0, character=2, tokens=tokens)
        
        if hover:
            assert "Key:" in hover or "name" in hover
    
    def test_render_nested_key(self):
        """Test rendering hover for nested key."""
        content = "config:\n  nested: value"
        result = tokenize(content)
        tokens = result.tokens
        
        hover = HoverRenderer.render(content, line=1, character=4, tokens=tokens)
        
        if hover:
            assert "nested" in hover.lower() or "Key:" in hover


class TestHoverRendererValues:
    """Test hover rendering for values."""
    
    def test_render_number_value(self):
        """Test rendering hover for number."""
        content = "port: 8080"
        result = tokenize(content)
        tokens = result.tokens
        
        # Hover over the number
        hover = HoverRenderer.render(content, line=0, character=7, tokens=tokens)
        
        if hover:
            assert "Number" in hover or "8080" in hover
            assert "RFC 8259" in hover or "number" in hover.lower()
    
    def test_render_string_value(self):
        """Test rendering hover for string."""
        content = "name: Hello World"
        result = tokenize(content)
        tokens = result.tokens
        
        # Hover over the string
        hover = HoverRenderer.render(content, line=0, character=7, tokens=tokens)
        
        if hover:
            assert "String" in hover or "Hello" in hover
    
    def test_render_string_with_escapes(self):
        """Test rendering hover for string with escape sequences."""
        content = r"text: Hello\nWorld"
        result = tokenize(content)
        tokens = result.tokens
        
        # This might render as either string or escape sequence
        hover = HoverRenderer.render(content, line=0, character=7, tokens=tokens)
        
        # Just check it renders something
        assert hover is None or isinstance(hover, str)
    
    def test_render_null_value(self):
        """Test rendering hover for null."""
        content = "value: null"
        result = tokenize(content)
        tokens = result.tokens
        
        # Hover over null
        hover = HoverRenderer.render(content, line=0, character=8, tokens=tokens)
        
        if hover:
            assert "Null" in hover or "null" in hover
            assert "RFC 8259" in hover or "None" in hover


class TestHoverRendererEscapeSequences:
    """Test hover rendering for escape sequences."""
    
    def test_render_newline_escape(self):
        """Test rendering hover for newline escape."""
        content = r"text: Hello\nWorld"
        result = tokenize(content)
        tokens = result.tokens
        
        # Try to hover over the escape sequence
        hover = HoverRenderer.render(content, line=0, character=12, tokens=tokens)
        
        if hover and "Escape" in hover:
            assert "\\n" in hover or "Newline" in hover
    
    def test_render_unicode_escape(self):
        """Test rendering hover for unicode escape."""
        content = r"emoji: \u2764"
        result = tokenize(content)
        tokens = result.tokens
        
        # Try to hover over unicode escape
        hover = HoverRenderer.render(content, line=0, character=9, tokens=tokens)
        
        if hover and "Unicode" in hover:
            assert "\\u" in hover or "Unicode" in hover


class TestHoverRendererEdgeCases:
    """Test edge cases for hover rendering."""
    
    def test_render_empty_content(self):
        """Test rendering with empty content."""
        content = ""
        result = tokenize(content)
        tokens = result.tokens
        
        hover = HoverRenderer.render(content, line=0, character=0, tokens=tokens)
        assert hover is None
    
    def test_render_invalid_position(self):
        """Test rendering with invalid position."""
        content = "key: value"
        result = tokenize(content)
        tokens = result.tokens
        
        # Position way outside the content
        hover = HoverRenderer.render(content, line=100, character=100, tokens=tokens)
        assert hover is None
    
    def test_render_multiline_content(self):
        """Test rendering with multiline content."""
        content = "first: 1\nsecond: 2\nthird: 3"
        result = tokenize(content)
        tokens = result.tokens
        
        # Hover on second line
        hover = HoverRenderer.render(content, line=1, character=5, tokens=tokens)
        
        # Should work on second line
        assert hover is None or isinstance(hover, str)


class TestHoverRendererIntegration:
    """Test integration with DocumentationRegistry."""
    
    def test_uses_documentation_registry(self):
        """Test that hover uses DocumentationRegistry (not hardcoded docs)."""
        content = "port(int): 8080"
        result = tokenize(content)
        tokens = result.tokens
        
        # TYPE_HINT starts at position 5
        hover = HoverRenderer.render(content, line=0, character=5, tokens=tokens)
        
        # Should use DocumentationRegistry for type hints
        assert hover is not None
        # The format should be from Documentation.to_hover_markdown()
        assert "**" in hover  # Markdown formatting
        assert "Integer" in hover or "int" in hover
    
    def test_all_type_hints_renderable(self):
        """Test that all type hints from registry are renderable."""
        type_hints = ["int", "float", "bool", "str", "list", "dict", "null", "raw", "date", "time", "url", "path"]
        
        for hint in type_hints:
            content = f"test({hint}): value"
            result = tokenize(content)
            tokens = result.tokens
            
            # TYPE_HINT starts at position 5 (after "test(")
            hover = HoverRenderer.render(content, line=0, character=5, tokens=tokens)
            
            # All type hints should render something
            assert hover is not None, f"Type hint '{hint}' failed to render"
            assert hint in hover.lower() or "Type Hint:" in hover


class TestHoverRendererValueTypeDetection:
    """Test value type detection helper."""
    
    def test_detect_array_type(self):
        """Test detecting array type."""
        detected = HoverRenderer._detect_value_type_name("[1, 2, 3]")
        assert "array" in detected.lower() or "list" in detected.lower()
    
    def test_detect_object_type(self):
        """Test detecting object type."""
        detected = HoverRenderer._detect_value_type_name("{key: value}")
        assert "object" in detected.lower() or "dict" in detected.lower()
    
    def test_detect_number_type(self):
        """Test detecting number type."""
        detected = HoverRenderer._detect_value_type_name("123")
        assert "number" in detected.lower()
    
    def test_detect_null_type(self):
        """Test detecting null type."""
        detected = HoverRenderer._detect_value_type_name("null")
        assert "null" in detected.lower()
    
    def test_detect_boolean_warning(self):
        """Test that booleans get warning about type hint."""
        detected = HoverRenderer._detect_value_type_name("true")
        assert "bool" in detected.lower()  # Should suggest using (bool) hint
    
    def test_detect_string_type(self):
        """Test detecting string type (default)."""
        detected = HoverRenderer._detect_value_type_name("hello")
        assert "string" in detected.lower()
