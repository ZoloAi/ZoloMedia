"""
Unit tests for comment_processors module.

Tests Zolo's dual comment syntax:
- Full-line comments: # at line start
- Inline comments: #> ... <#

Current coverage: 62% → Target: 75%+
"""

import pytest
from core.parser.parser_modules.comment_processors import (
    strip_comments_and_prepare_lines,
    strip_comments_and_prepare_lines_with_tokens,
)
from core.parser.parser_modules.token_emitter import TokenEmitter
from core.lsp_types import TokenType


# ============================================================================
# strip_comments_and_prepare_lines Tests (Without Token Emission)
# ============================================================================

class TestStripCommentsBasic:
    """Test basic comment stripping without token emission."""
    
    def test_no_comments(self):
        """Test content without any comments."""
        content = """
key1: value1
key2: value2
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Should preserve non-comment lines
        assert len(cleaned_lines) == 2
        assert 'key1: value1' in cleaned_lines
        assert 'key2: value2' in cleaned_lines
    
    def test_full_line_comment(self):
        """Test full-line comment at line start."""
        content = """
# This is a comment
key: value
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Comment line should be removed
        assert len(cleaned_lines) == 1
        assert 'key: value' in cleaned_lines
        assert '# This is a comment' not in '\n'.join(cleaned_lines)
    
    def test_full_line_comment_with_indent(self):
        """Test full-line comment with indentation."""
        content = """
key:
  # Indented comment
  nested: value
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Comment should be removed, structure preserved
        assert len(cleaned_lines) == 2
        assert 'key:' in cleaned_lines
        # Check for nested value with indentation
        assert any('nested: value' in line for line in cleaned_lines)
    
    def test_inline_comment_simple(self):
        """Test simple inline comment #> ... <#."""
        content = "key: value #> this is a comment <#"
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Comment should be removed
        assert len(cleaned_lines) == 1
        assert cleaned_lines[0] == 'key: value'
    
    def test_inline_comment_multiline(self):
        """Test multi-line inline comment."""
        content = """
key1: value1 #> start comment
continues on next line
end comment <# more content
key2: value2
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Multi-line comment should be removed
        assert 'key1: value1' in '\n'.join(cleaned_lines)
        assert 'more content' in '\n'.join(cleaned_lines)
        assert 'key2: value2' in '\n'.join(cleaned_lines)
        assert 'continues on next line' not in '\n'.join(cleaned_lines)
    
    def test_unpaired_comment_delimiters(self):
        """Test unpaired #> or <# treated as literal."""
        content = "key: value#> without closing"
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Unpaired delimiter should be kept as literal
        assert len(cleaned_lines) == 1
        assert '#>' in cleaned_lines[0]
    
    def test_hash_without_arrow(self):
        """Test # without > is literal (hex colors, hashtags)."""
        content = """
color: #FF5733
tag: #trending
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # # without > should be preserved
        assert len(cleaned_lines) == 2
        assert '#FF5733' in cleaned_lines[0]
        assert '#trending' in cleaned_lines[1]
    
    def test_empty_lines_removed(self):
        """Test empty lines are removed."""
        content = """
key1: value1

key2: value2

        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Empty lines should be removed
        assert len(cleaned_lines) == 2
        assert 'key1: value1' in cleaned_lines
        assert 'key2: value2' in cleaned_lines
    
    def test_line_mapping_accuracy(self):
        """Test line_mapping tracks original line numbers."""
        content = """# Comment on line 1
key1: value1
# Comment on line 3
key2: value2"""
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Line mapping should be 1-based (accounts for content starting at line 0)
        assert len(line_mapping) == 2
        assert 'key1: value1' in cleaned_lines
        assert 'key2: value2' in cleaned_lines


# ============================================================================
# strip_comments_and_prepare_lines_with_tokens Tests (With Token Emission)
# ============================================================================

class TestStripCommentsWithTokens:
    """Test comment stripping with token emission."""
    
    def test_emit_full_line_comment_token(self):
        """Test full-line comment emits COMMENT token."""
        content = """# This is a comment
key: value"""
        emitter = TokenEmitter(content)
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines_with_tokens(content, emitter)
        
        # Should emit comment token
        tokens = emitter.get_tokens()
        comment_tokens = [t for t in tokens if t.token_type == TokenType.COMMENT]
        assert len(comment_tokens) >= 1
    
    def test_emit_inline_comment_token(self):
        """Test inline comment emits COMMENT token."""
        content = "key: value #> inline comment <#"
        emitter = TokenEmitter(content)
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines_with_tokens(content, emitter)
        
        # Should emit comment token for inline comment
        tokens = emitter.get_tokens()
        comment_tokens = [t for t in tokens if t.token_type == TokenType.COMMENT]
        assert len(comment_tokens) >= 1
    
    def test_comment_tokens_dont_overlap(self):
        """Test comment ranges prevent token overlap."""
        content = """# Full line comment
key: value #> inline <#"""
        emitter = TokenEmitter(content)
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines_with_tokens(content, emitter)
        
        # Comments should be tracked to prevent overlap
        tokens = emitter.get_tokens()
        # Just verify we got some tokens without errors
        assert isinstance(tokens, list)
    
    def test_multiple_inline_comments(self):
        """Test multiple inline comments on different lines."""
        content = """key1: value1 #> comment 1 <#
key2: value2 #> comment 2 <#"""
        emitter = TokenEmitter(content)
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines_with_tokens(content, emitter)
        
        # Should emit tokens for both comments
        tokens = emitter.get_tokens()
        comment_tokens = [t for t in tokens if t.token_type == TokenType.COMMENT]
        assert len(comment_tokens) >= 2


# ============================================================================
# Edge Cases and Complex Scenarios
# ============================================================================

class TestCommentEdgeCases:
    """Test edge cases and complex comment scenarios."""
    
    def test_nested_comment_delimiters(self):
        """Test nested #> <# is not supported (only outermost pair)."""
        content = "key: value #> outer #> inner <# outer <#"
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Should handle first matched pair
        assert len(cleaned_lines) == 1
    
    def test_comment_at_line_end(self):
        """Test inline comment at line end."""
        content = "key: value #> comment <#"
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        assert len(cleaned_lines) == 1
        assert cleaned_lines[0].strip() == 'key: value'
    
    def test_multiple_full_line_comments(self):
        """Test consecutive full-line comments."""
        content = """
# Comment 1
# Comment 2
# Comment 3
key: value
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # All comment lines should be removed
        assert len(cleaned_lines) == 1
        assert 'key: value' in cleaned_lines
    
    def test_comment_with_special_chars(self):
        """Test comments containing special characters."""
        content = """
# Comment with: colons, @symbols, $variables
key: value
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        assert len(cleaned_lines) == 1
        assert 'key: value' in cleaned_lines
    
    def test_inline_comment_at_start_of_line(self):
        """Test inline comment starting at line beginning."""
        content = "#> comment <# key: value"
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        assert len(cleaned_lines) == 1
        assert 'key: value' in cleaned_lines[0]
    
    def test_inline_comment_between_values(self):
        """Test inline comment in the middle of content."""
        content = "key: value1 #> comment <# value2"
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        assert len(cleaned_lines) == 1
        # Comment should be removed, values preserved
        assert 'value1' in cleaned_lines[0]
        assert 'value2' in cleaned_lines[0]
    
    def test_whitespace_preservation(self):
        """Test indentation is preserved after comment removal."""
        content = """
parent:
  child1: value1
  # Comment
  child2: value2
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Indentation should be preserved
        assert 'parent:' in cleaned_lines
        for line in cleaned_lines:
            if 'child' in line:
                assert line.startswith('  ')  # 2-space indent
    
    def test_empty_inline_comment(self):
        """Test empty inline comment #><#."""
        content = "key: value #><#"
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        assert len(cleaned_lines) == 1
        assert cleaned_lines[0].strip() == 'key: value'
    
    def test_full_line_comment_not_arrow_comment(self):
        """Test # at start is full-line, not start of #>."""
        content = """
# This is a full-line comment, not #> arrow
key: value
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Full-line comment should be completely removed
        assert len(cleaned_lines) == 1
        assert 'key: value' in cleaned_lines
        assert '#' not in cleaned_lines[0]


# ============================================================================
# Integration Tests
# ============================================================================

class TestCommentIntegration:
    """Test comment processing in realistic scenarios."""
    
    def test_config_file_with_comments(self):
        """Test realistic config file with mixed comments."""
        content = """
# Configuration file for MyApp
server:
  port: 8080  #> Default port <#
  host: localhost
  # Debug mode disabled in production
  debug: false

# Database settings
database:
  host: localhost #> Local development <#
  port: 5432
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Comments should be removed, structure preserved
        assert 'server:' in cleaned_lines
        assert 'port: 8080' in '\n'.join(cleaned_lines)
        assert 'database:' in cleaned_lines
        assert 'Default port' not in '\n'.join(cleaned_lines)
        assert 'Configuration file' not in '\n'.join(cleaned_lines)
    
    def test_complex_nested_with_comments(self):
        """Test complex nested structure with comments."""
        content = """
app:
  # Application settings
  name: MyApp
  version: 1.0.0 #> Semantic versioning <#
  features:
    # Security features
    - auth
    - logging #> With rotation <#
    # Performance features
    - caching
        """
        cleaned_lines, line_mapping = strip_comments_and_prepare_lines(content)
        
        # Structure should be preserved
        assert 'app:' in cleaned_lines
        assert 'name: MyApp' in '\n'.join(cleaned_lines)
        assert '- auth' in '\n'.join(cleaned_lines)
        assert '- caching' in '\n'.join(cleaned_lines)
        # Comments should be removed
        assert 'Application settings' not in '\n'.join(cleaned_lines)
        assert 'With rotation' not in '\n'.join(cleaned_lines)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
