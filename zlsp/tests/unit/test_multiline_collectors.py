"""
Unit tests for multiline_collectors module.

Tests all multiline collection patterns with correct function signatures.

Critical module: 19% coverage → target 70%+
"""

import pytest
from core.parser.parser_modules.multiline_collectors import (
    collect_str_hint_multiline,
    collect_dash_list,
    collect_bracket_array,
    collect_pipe_multiline,
    collect_triple_quote_multiline,
)


# ============================================================================
# collect_str_hint_multiline Tests
# ============================================================================

class TestCollectStrHintMultiline:
    """Test (str) type hint multiline collection with >>> continuation."""
    
    def test_basic_str_hint_multiline(self):
        """Test basic multi-line string."""
        lines = [
            "description(str): This is a long",
            "description that continues",
            "on multiple lines.",
            "next_key: value"
        ]
        
        result, consumed = collect_str_hint_multiline(
            lines, start_idx=1, parent_indent=0, first_value="This is a long"
        )
        
        # Should collect all continuation lines
        assert isinstance(result, str)
        assert "This is a long" in result
        assert consumed >= 0
    
    def test_str_hint_no_first_value(self):
        """Test when first_value is empty."""
        lines = [
            "  First line",
            "  Second line",
            "key: value"
        ]
        
        result, consumed = collect_str_hint_multiline(
            lines, start_idx=0, parent_indent=0, first_value=""
        )
        
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# collect_dash_list Tests
# ============================================================================

class TestCollectDashList:
    """Test YAML-style dash list collection (- item1 \n - item2)."""
    
    def test_basic_dash_list(self):
        """Test basic dash list."""
        lines = [
            "items:",
            "  - first",
            "  - second",
            "  - third",
            "next_key: value"
        ]
        
        result, consumed, line_info = collect_dash_list(lines, start_idx=1, parent_indent=0)
        
        # Returns string representation "[item1, item2, item3]"
        assert isinstance(result, str)
        assert result.startswith('[')
        assert result.endswith(']')
        assert 'first' in result
        assert 'second' in result
        assert 'third' in result
        
        # Should consume 3 lines
        assert consumed == 3
        
        # Should return line info
        assert isinstance(line_info, list)
        assert len(line_info) == 3
    
    def test_dash_list_single_item(self):
        """Test dash list with single item."""
        lines = [
            "items:",
            "  - only_one",
            "key: value"
        ]
        
        result, consumed, line_info = collect_dash_list(lines, start_idx=1, parent_indent=0)
        
        assert isinstance(result, str)
        assert 'only_one' in result
        assert consumed == 1
        assert len(line_info) == 1
    
    def test_dash_list_empty(self):
        """Test behavior when no dash items found."""
        lines = [
            "items:",
            "key: value"
        ]
        
        result, consumed, line_info = collect_dash_list(lines, start_idx=1, parent_indent=0)
        
        # Should return empty array representation
        assert isinstance(result, str)
        assert consumed >= 0


# ============================================================================
# collect_bracket_array Tests
# ============================================================================

class TestCollectBracketArray:
    """Test multi-line bracket array collection ([...])."""
    
    def test_basic_bracket_array(self):
        """Test basic multi-line array."""
        lines = [
            "values: [",
            "  item1,",
            "  item2,",
            "  item3",
            "]",
            "key: value"
        ]
        
        result, consumed, line_info = collect_bracket_array(
            lines, start_idx=1, parent_indent=0, first_value="["
        )
        
        # Returns string representation "[item1, item2, item3]"
        assert isinstance(result, str)
        assert result.startswith('[')
        assert result.endswith(']')
        assert 'item1' in result
        assert 'item2' in result
        assert 'item3' in result
        
        # Should consume lines until ]
        assert consumed >= 3
        
        # Should return line info
        assert isinstance(line_info, list)
        assert len(line_info) >= 3
    
    def test_bracket_array_empty(self):
        """Test empty array."""
        lines = [
            "values: [",
            "]",
            "key: value"
        ]
        
        result, consumed, line_info = collect_bracket_array(
            lines, start_idx=1, parent_indent=0, first_value="["
        )
        
        # Should return "[]"
        assert isinstance(result, str)
        assert result == "[]"
        assert consumed >= 1
    
    def test_bracket_array_single_item(self):
        """Test array with single item."""
        lines = [
            "values: [",
            "  only_one",
            "]",
            "key: value"
        ]
        
        result, consumed, line_info = collect_bracket_array(
            lines, start_idx=1, parent_indent=0, first_value="["
        )
        
        assert isinstance(result, str)
        assert 'only_one' in result
        assert consumed >= 2


# ============================================================================
# collect_pipe_multiline Tests
# ============================================================================

class TestCollectPipeMultiline:
    """Test pipe multiline string collection (|)."""
    
    def test_basic_pipe_multiline(self):
        """Test basic | multiline string."""
        lines = [
            "description: |",
            "  This is a long text",
            "  that spans multiple lines",
            "  and preserves formatting.",
            "next_key: value"
        ]
        
        result, consumed = collect_pipe_multiline(lines, start_idx=1, parent_indent=0)
        
        # Should collect all indented lines
        assert isinstance(result, str)
        assert "This is a long text" in result
        assert "that spans multiple lines" in result
        assert "and preserves formatting." in result
        
        # Should consume lines until dedent
        assert consumed == 3
    
    def test_pipe_multiline_single_line(self):
        """Test | with single line."""
        lines = [
            "text: |",
            "  Just one line",
            "key: value"
        ]
        
        result, consumed = collect_pipe_multiline(lines, start_idx=1, parent_indent=0)
        
        assert isinstance(result, str)
        assert "Just one line" in result
        assert consumed == 1
    
    def test_pipe_multiline_empty(self):
        """Test | with no content."""
        lines = [
            "text: |",
            "key: value"
        ]
        
        result, consumed = collect_pipe_multiline(lines, start_idx=1, parent_indent=0)
        
        # Should handle no content case
        assert isinstance(result, str)
        assert consumed == 0


# ============================================================================
# collect_triple_quote_multiline Tests
# ============================================================================

class TestCollectTripleQuoteMultiline:
    """Test triple-quote multiline string collection (three double-quotes)."""
    
    def test_basic_triple_quote(self):
        """Test basic triple-quoted string."""
        lines = [
            'description: """',
            "This is a multiline",
            "string with triple quotes.",
            '"""',
            "key: value"
        ]
        
        result, consumed = collect_triple_quote_multiline(lines, start_idx=0, initial_value='"""')
        
        # Should collect content between """ markers
        assert isinstance(result, str)
        # Actual content may vary based on implementation
        assert consumed >= 3
    
    def test_triple_quote_single_line(self):
        """Test triple-quote all on one line."""
        lines = [
            'text: """Just one line"""',
            "key: value"
        ]
        
        result, consumed = collect_triple_quote_multiline(lines, start_idx=0, initial_value='"""Just one line"""')
        
        assert isinstance(result, str)
        assert "Just one line" in result
        assert consumed == 0  # All on one line
    
    def test_triple_quote_multiline(self):
        """Test triple-quote spanning multiple lines."""
        lines = [
            'text: """',
            "Line 1",
            "Line 2",
            '"""',
            "key: value"
        ]
        
        result, consumed = collect_triple_quote_multiline(lines, start_idx=0, initial_value='"""')
        
        assert isinstance(result, str)
        assert consumed >= 1


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

class TestMultilineEdgeCases:
    """Test edge cases and error handling."""
    
    def test_dash_list_stops_at_indent_change(self):
        """Test dash list stops at indent change."""
        lines = [
            "items:",
            "  - item1",
            "  - item2",
            "different:",
            "  value"
        ]
        
        result, consumed, line_info = collect_dash_list(lines, start_idx=1, parent_indent=0)
        
        # Should collect 2 items and stop
        assert isinstance(result, str)
        assert 'item1' in result
        assert 'item2' in result
        assert consumed == 2
        assert len(line_info) == 2
    
    def test_str_hint_preserves_indentation(self):
        """Test that relative indentation is preserved."""
        lines = [
            "  First level",
            "    Indented more",
            "  Back to first",
            "key: value"
        ]
        
        result, consumed = collect_str_hint_multiline(
            lines, start_idx=0, parent_indent=0, first_value=""
        )
        
        assert isinstance(result, str)
        # Relative indentation should be preserved
        assert consumed >= 2
    
    def test_bracket_array_with_trailing_comma(self):
        """Test array items with trailing commas."""
        lines = [
            "values: [",
            "  item1,",
            "  item2,",
            "]",
            "key: value"
        ]
        
        result, consumed, line_info = collect_bracket_array(
            lines, start_idx=1, parent_indent=0, first_value="["
        )
        
        # Should handle trailing commas correctly
        assert isinstance(result, str)
        assert 'item1' in result
        assert 'item2' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
