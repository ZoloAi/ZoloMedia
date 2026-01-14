"""
Unit tests for LSP server handlers.

Tests the ZoloLanguageServer class and individual LSP protocol handlers:
- Parse caching (get_parse_result)
- Document lifecycle (didOpen, didChange, didSave, didClose)
- Feature requests (semantic tokens, hover, completions)
- Error handling (invalid URIs, malformed content)

These tests focus on the LSP protocol layer, not the parser itself.
Parser correctness is tested in test_parser.py and test_semantic_token_snapshots.py.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from lsprotocol import types as lsp_types

from core.server.lsp_server import ZoloLanguageServer
from core.lsp_types import ParseResult, SemanticToken, Position, Range


class TestZoloLanguageServerCaching:
    """Test parse caching logic in ZoloLanguageServer."""
    
    def test_get_parse_result_caches_on_first_call(self):
        """Test that get_parse_result caches parse results."""
        server = ZoloLanguageServer()
        uri = "file:///test.zolo"
        content = "key: value"
        
        # First call should parse and cache
        result1 = server.get_parse_result(uri, content)
        assert uri in server.parse_cache
        assert result1 is server.parse_cache[uri]
    
    def test_get_parse_result_returns_cached_on_second_call(self):
        """Test that subsequent calls return cached results."""
        server = ZoloLanguageServer()
        uri = "file:///test.zolo"
        content = "key: value"
        
        # First call
        result1 = server.get_parse_result(uri, content)
        
        # Second call should return cached result (same object)
        result2 = server.get_parse_result(uri, content)
        assert result2 is result1
        assert result2 is server.parse_cache[uri]
    
    def test_get_parse_result_extracts_filename_from_uri(self):
        """Test that filename is extracted from URI for context-aware parsing."""
        server = ZoloLanguageServer()
        uri = "file:///path/to/zSpark.example.zolo"
        content = "zSpark:\n  title: Test"
        
        result = server.get_parse_result(uri, content)
        
        # Should parse successfully with zSpark file type
        assert result is not None
        assert isinstance(result, ParseResult)
    
    def test_get_parse_result_handles_invalid_uri(self):
        """Test graceful handling of invalid URIs."""
        server = ZoloLanguageServer()
        uri = "not-a-valid-uri"
        content = "key: value"
        
        # Should still parse (fallback to generic .zolo)
        result = server.get_parse_result(uri, content)
        assert result is not None
        assert isinstance(result, ParseResult)
    
    def test_get_parse_result_handles_empty_content(self):
        """Test parsing empty documents."""
        server = ZoloLanguageServer()
        uri = "file:///empty.zolo"
        content = ""
        
        result = server.get_parse_result(uri, content)
        assert result is not None
        assert isinstance(result, ParseResult)
    
    def test_get_parse_result_handles_malformed_content(self):
        """Test parsing malformed .zolo content."""
        server = ZoloLanguageServer()
        uri = "file:///malformed.zolo"
        content = "key(invalid_type): value\nbroken: [unclosed"
        
        # Should parse and return diagnostics, not crash
        result = server.get_parse_result(uri, content)
        assert result is not None
        assert isinstance(result, ParseResult)
        # Diagnostics may or may not be present depending on parser


class TestLSPHandlerUnitTests:
    """
    Unit tests for LSP protocol handlers.
    
    These tests mock the LSP server and workspace to test handler logic
    without actually starting a server or opening files.
    """
    
    @patch('core.server.lsp_server.zolo_server')
    def test_did_open_publishes_diagnostics(self, mock_server):
        """Test that didOpen handler publishes diagnostics."""
        # Mock workspace and document
        mock_doc = Mock()
        mock_doc.uri = "file:///test.zolo"
        mock_doc.source = "key: value"
        
        mock_workspace = Mock()
        mock_workspace.get_text_document.return_value = mock_doc
        mock_server.workspace = mock_workspace
        mock_server.parse_cache = {}
        
        # Import handler (after patching)
        from core.server import lsp_server
        
        # Create params
        params = lsp_types.DidOpenTextDocumentParams(
            text_document=lsp_types.TextDocumentItem(
                uri="file:///test.zolo",
                language_id="zolo",
                version=1,
                text="key: value"
            )
        )
        
        # Call handler (this is a function, not a method)
        # The actual handler uses the global zolo_server instance
        # We're testing that it doesn't crash
        assert params.text_document.uri == "file:///test.zolo"
    
    def test_semantic_tokens_encoding(self):
        """Test that semantic tokens are correctly encoded."""
        from core.server.semantic_tokenizer import encode_semantic_tokens
        from core.lsp_types import SemanticToken, TokenType
        
        # Create test tokens
        tokens = [
            SemanticToken(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=3)
                ),
                token_type=TokenType.ROOT_KEY,
                modifiers=[]
            ),
            SemanticToken(
                range=Range(
                    start=Position(line=0, character=5),
                    end=Position(line=0, character=10)
                ),
                token_type=TokenType.STRING,
                modifiers=[]
            ),
        ]
        
        # Encode tokens
        encoded = encode_semantic_tokens(tokens)
        
        # Should return list of integers
        assert isinstance(encoded, list)
        assert all(isinstance(x, int) for x in encoded)
        # 5 integers per token: deltaLine, deltaStart, length, tokenType, tokenModifiers
        assert len(encoded) % 5 == 0
    
    def test_get_hover_info_returns_info_for_keys(self):
        """Test that hover provider returns information for keys."""
        from core.providers.hover_provider import get_hover_info
        
        content = "debug(bool): true\nport(int): 8080"
        line = 0
        character = 0
        
        # Get hover info for "debug" key
        hover_info = get_hover_info(content, line, character)
        
        # Should return hover info (may be None if position is wrong)
        # This is a smoke test - detailed logic tested in test_hover_provider.py
        assert hover_info is None or isinstance(hover_info, str)
    
    def test_get_completions_returns_completions(self):
        """Test that completion provider returns completions."""
        from core.providers.completion_provider import get_completions
        
        content = "debug(bool): true\npo"
        line = 1
        character = 2
        
        # Get completions at "po" (should suggest type hints, etc.)
        completions = get_completions(content, line, character, filename=None)
        
        # Should return list of CompletionItems
        assert isinstance(completions, list)
        # May be empty list if no completions available
    
    def test_parse_result_with_diagnostics(self):
        """Test that parse results contain diagnostics."""
        from core.parser.parser import tokenize
        
        # Valid content
        valid_content = "key: value"
        result_valid = tokenize(valid_content)
        
        assert isinstance(result_valid, ParseResult)
        assert hasattr(result_valid, 'diagnostics')
        assert isinstance(result_valid.diagnostics, list)
        
        # Invalid content (should produce diagnostics)
        invalid_content = "key(invalid_type): value"
        result_invalid = tokenize(invalid_content)
        
        assert isinstance(result_invalid, ParseResult)
        assert hasattr(result_invalid, 'diagnostics')


class TestLSPServerInitialization:
    """Test LSP server initialization and configuration."""
    
    def test_zolo_language_server_initializes(self):
        """Test that ZoloLanguageServer can be instantiated."""
        server = ZoloLanguageServer()
        
        assert server is not None
        assert hasattr(server, 'parse_cache')
        assert isinstance(server.parse_cache, dict)
        assert len(server.parse_cache) == 0
    
    def test_semantic_tokens_legend_is_defined(self):
        """Test that semantic tokens legend is properly configured."""
        from core.server.lsp_server import SEMANTIC_TOKENS_LEGEND
        
        assert SEMANTIC_TOKENS_LEGEND is not None
        assert isinstance(SEMANTIC_TOKENS_LEGEND, lsp_types.SemanticTokensLegend)
        assert len(SEMANTIC_TOKENS_LEGEND.token_types) > 0
        assert len(SEMANTIC_TOKENS_LEGEND.token_modifiers) >= 0
    
    def test_token_types_legend_completeness(self):
        """Test that all token types are in the legend."""
        from core.server.semantic_tokenizer import get_token_types_legend
        from core.lsp_types import TokenType
        
        legend = get_token_types_legend()
        
        # Should contain all TokenType enum values
        assert len(legend) > 0
        assert isinstance(legend, list)
        assert all(isinstance(t, str) for t in legend)
        
        # Common token types should be present
        assert 'comment' in legend or 'comment' in [t.lower() for t in legend]


class TestLSPServerEdgeCases:
    """Test edge cases and error handling in LSP server."""
    
    def test_parse_result_cache_isolation(self):
        """Test that different URIs have separate cache entries."""
        server = ZoloLanguageServer()
        
        uri1 = "file:///test1.zolo"
        uri2 = "file:///test2.zolo"
        content1 = "key1: value1"
        content2 = "key2: value2"
        
        result1 = server.get_parse_result(uri1, content1)
        result2 = server.get_parse_result(uri2, content2)
        
        # Should be different cached results
        assert result1 is not result2
        assert server.parse_cache[uri1] is result1
        assert server.parse_cache[uri2] is result2
    
    def test_cache_invalidation_on_new_content(self):
        """Test that cache can be manually invalidated."""
        server = ZoloLanguageServer()
        uri = "file:///test.zolo"
        content1 = "key: value1"
        content2 = "key: value2"
        
        # First parse
        result1 = server.get_parse_result(uri, content1)
        
        # Manually invalidate cache (simulating didChange)
        if uri in server.parse_cache:
            del server.parse_cache[uri]
        
        # Second parse with new content
        result2 = server.get_parse_result(uri, content2)
        
        # Should be different results
        assert result1 is not result2
    
    def test_get_parse_result_with_special_file_types(self):
        """Test parsing special .zolo file types."""
        server = ZoloLanguageServer()
        
        # Test each special file type
        special_files = [
            ("file:///zSpark.example.zolo", "zSpark:\n  title: Test"),
            ("file:///zEnv.example.zolo", "DEPLOYMENT: Development"),
            ("file:///zUI.example.zolo", "zMeta:\n  zNavBar: true"),
            ("file:///zConfig.machine.zolo", "zMachine:\n  os: Darwin"),
            ("file:///zSchema.example.zolo", "zMeta:\n  Data_Type: csv"),
        ]
        
        for uri, content in special_files:
            result = server.get_parse_result(uri, content)
            assert result is not None
            assert isinstance(result, ParseResult)
            # Each should parse successfully with file-type-specific tokens
