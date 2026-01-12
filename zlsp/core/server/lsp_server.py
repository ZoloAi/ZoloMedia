"""
Zolo Language Server Protocol Implementation

Full-featured LSP server for .zolo files providing:
- Semantic highlighting
- Diagnostics (error detection)
- Hover information
- Code completion
- Go-to-definition
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List
from pygls.lsp.server import LanguageServer
from lsprotocol import types as lsp_types

# Use relative imports within core package
from ..parser.parser import tokenize
from .semantic_tokenizer import (
    encode_semantic_tokens,
    get_token_types_legend,
    get_token_modifiers_legend
)
from ..lsp_types import ParseResult
from ..providers.diagnostics_engine import get_all_diagnostics
from ..providers.hover_provider import get_hover_info
from ..providers.completion_provider import get_completions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("zolo.zLSP.server")

# Build semantic tokens legend ONCE at module level
# Per pygls 2.0 convention: pass legend as keyword arg to @feature decorator
SEMANTIC_TOKENS_LEGEND = lsp_types.SemanticTokensLegend(
    token_types=get_token_types_legend(),
    token_modifiers=get_token_modifiers_legend()
)


class ZoloLanguageServer(LanguageServer):
    """Language Server for .zolo files."""
    
    def __init__(self):
        super().__init__("zolo-lsp", "v1.0")
        self.parse_cache = {}  # Cache parsed results by URI
    
    def get_parse_result(self, uri: str, content: str) -> ParseResult:
        """Get cached parse result or parse content."""
        # Simple cache - in production, should check document version
        if uri not in self.parse_cache:
            try:
                # Extract filename from URI for context-aware tokenization
                from urllib.parse import urlparse, unquote
                parsed_uri = urlparse(uri)
                filename = Path(unquote(parsed_uri.path)).name if parsed_uri.path else None
                
                result = tokenize(content, filename=filename)
                self.parse_cache[uri] = result
            except Exception as e:
                logger.error(f"Parse error for {uri}: {e}")
                # Return empty result on error
                result = ParseResult(data=None, tokens=[], errors=[str(e)])
                self.parse_cache[uri] = result
        return self.parse_cache[uri]
    
    def invalidate_cache(self, uri: str):
        """Invalidate cached parse result."""
        if uri in self.parse_cache:
            del self.parse_cache[uri]


# Initialize server
zolo_server = ZoloLanguageServer()

# Create semantic tokens legend and options at MODULE LEVEL
# This allows pygls to serialize them when auto-generating capabilities
token_types_list = get_token_types_legend()
token_modifiers_list = get_token_modifiers_legend()

SEMANTIC_LEGEND = lsp_types.SemanticTokensLegend(
    token_types=token_types_list,
    token_modifiers=token_modifiers_list
)

SEMANTIC_OPTIONS = lsp_types.SemanticTokensRegistrationOptions(
    legend=SEMANTIC_LEGEND,
    full=True,
    document_selector=[{"language": "zolo"}]  # Required for registration options
)


@zolo_server.feature(lsp_types.INITIALIZE)
def initialize(params: lsp_types.InitializeParams):
    """
    Initialize the language server.
    """
    logger.info("Initializing Zolo Language Server")
    logger.info(f"Client: {params.client_info.name if params.client_info else 'Unknown'}")
    logger.info(f"Workspace: {params.root_uri}")
    logger.info(f"Semantic tokens configured with {len(token_types_list)} token types")
    logger.info(f"Token types: {token_types_list}")
    
    # Let pygls auto-generate capabilities from @feature decorators
    return None


@zolo_server.feature(lsp_types.TEXT_DOCUMENT_DID_OPEN)
async def did_open(params: lsp_types.DidOpenTextDocumentParams):
    """
    Handle document opened event.
    
    Parse document and publish diagnostics.
    """
    uri = params.text_document.uri
    logger.info(f"========== DOCUMENT OPENED ==========")
    logger.info(f"URI: {uri}")
    logger.info(f"Language ID: {params.text_document.language_id}")
    
    document = zolo_server.workspace.get_text_document(uri)
    content = document.source
    
    logger.info(f"Content length: {len(content)} characters")
    
    # Parse and cache
    parse_result = zolo_server.get_parse_result(uri, content)
    
    logger.info(f"Parsed {len(parse_result.tokens)} tokens")
    
    # Publish diagnostics
    await publish_diagnostics(uri, parse_result)
    
    logger.info(f"========== END DOCUMENT OPENED ==========")  


@zolo_server.feature(lsp_types.TEXT_DOCUMENT_DID_CHANGE)
async def did_change(params: lsp_types.DidChangeTextDocumentParams):
    """
    Handle document changed event.
    
    Re-parse document and update diagnostics.
    """
    uri = params.text_document.uri
    logger.info(f"Document changed: {uri}")
    
    # Invalidate cache
    zolo_server.invalidate_cache(uri)
    
    document = zolo_server.workspace.get_text_document(uri)
    content = document.source
    
    # Parse and cache
    parse_result = zolo_server.get_parse_result(uri, content)
    
    # Publish diagnostics
    await publish_diagnostics(uri, parse_result)


@zolo_server.feature(lsp_types.TEXT_DOCUMENT_DID_SAVE)
async def did_save(params: lsp_types.DidSaveTextDocumentParams):
    """
    Handle document saved event.
    
    Re-validate document.
    """
    uri = params.text_document.uri
    logger.info(f"Document saved: {uri}")
    
    # Invalidate cache and re-parse
    zolo_server.invalidate_cache(uri)
    
    document = zolo_server.workspace.get_text_document(uri)
    content = document.source
    
    parse_result = zolo_server.get_parse_result(uri, content)
    await publish_diagnostics(uri, parse_result)


@zolo_server.feature(lsp_types.TEXT_DOCUMENT_DID_CLOSE)
def did_close(params: lsp_types.DidCloseTextDocumentParams):
    """
    Handle document closed event.
    
    Clear cache and diagnostics.
    """
    uri = params.text_document.uri
    logger.info(f"Document closed: {uri}")
    
    # Clear cache
    zolo_server.invalidate_cache(uri)
    
    # Clear diagnostics
    zolo_server.text_document_publish_diagnostics(
        lsp_types.PublishDiagnosticsParams(uri=uri, diagnostics=[])
    )


@zolo_server.feature(lsp_types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL, SEMANTIC_OPTIONS)
def semantic_tokens_full(params: lsp_types.SemanticTokensParams):
    """
    Provide semantic tokens for the entire document.
    
    This enables accurate syntax highlighting based on semantic understanding.
    """
    uri = params.text_document.uri
    logger.info(f"========== SEMANTIC TOKENS REQUEST ==========")
    logger.info(f"URI: {uri}")
    
    try:
        document = zolo_server.workspace.get_text_document(uri)
        content = document.source
        
        logger.info(f"Document length: {len(content)} characters")
        logger.info(f"First 100 chars: {content[:100]!r}")
        
        # Get parse result with tokens
        parse_result = zolo_server.get_parse_result(uri, content)
        
        logger.info(f"Parser generated {len(parse_result.tokens)} tokens")
        
        # Log first few tokens for debugging
        lines = content.splitlines()
        if parse_result.tokens:
            for i, token in enumerate(parse_result.tokens[:20]):
                # Extract actual text
                if token.line < len(lines):
                    line_text = lines[token.line]
                    token_text = line_text[token.start_char:token.start_char + token.length] if token.start_char + token.length <= len(line_text) else "???"
                else:
                    token_text = "???"
                logger.info(f"  Token {i}: line={token.line}, start={token.start_char}, len={token.length}, type={token.token_type.name}, text={token_text!r}")
        
        # Encode tokens for LSP
        encoded = encode_semantic_tokens(parse_result.tokens)
        
        logger.info(f"Encoded to {len(encoded)} integers")
        logger.info(f"First 25 encoded values: {encoded[:25]}")
        logger.info(f"Returning SemanticTokens with {len(encoded)} data elements")
        
        result = lsp_types.SemanticTokens(data=encoded)
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result.data length: {len(result.data)}")
        logger.info(f"========== END SEMANTIC TOKENS REQUEST ==========")
        
        return result
    
    except Exception as e:
        logger.error(f"Error providing semantic tokens: {e}")
        # Return empty tokens on error
        return lsp_types.SemanticTokens(data=[])


@zolo_server.feature(lsp_types.TEXT_DOCUMENT_HOVER)
def hover(params: lsp_types.HoverParams):
    """
    Provide hover information at a specific position.
    
    Shows type hints, value types, and documentation.
    """
    uri = params.text_document.uri
    line = params.position.line
    character = params.position.character
    
    logger.info(f"Hover requested for: {uri} at {line}:{character}")
    
    try:
        document = zolo_server.workspace.get_text_document(uri)
        content = document.source
        
        # Get hover info
        hover_text = get_hover_info(content, line, character)
        
        if hover_text:
            return lsp_types.Hover(
                contents=lsp_types.MarkupContent(
                    kind=lsp_types.MarkupKind.Markdown,
                    value=hover_text
                )
            )
        
        return None
    
    except Exception as e:
        logger.error(f"Error providing hover: {e}")
        return None


@zolo_server.feature(
    lsp_types.TEXT_DOCUMENT_COMPLETION,
    lsp_types.CompletionOptions(trigger_characters=["(", ":", "z"])
)
def completions(params: lsp_types.CompletionParams):
    """
    Provide completion items at a specific position.
    
    Offers context-aware completions for:
    - Type hints (inside parentheses)
    - Common values (after colon)
    - zKernel shorthands (at line start)
    """
    uri = params.text_document.uri
    line = params.position.line
    character = params.position.character
    
    logger.info(f"Completions requested for: {uri} at {line}:{character}")
    
    try:
        document = zolo_server.workspace.get_text_document(uri)
        content = document.source
        
        # Get completion items
        items = get_completions(content, line, character)
        
        return lsp_types.CompletionList(
            is_incomplete=False,
            items=items
        )
    
    except Exception as e:
        logger.error(f"Error providing completions: {e}")
        return lsp_types.CompletionList(is_incomplete=False, items=[])


async def publish_diagnostics(uri: str, parse_result: ParseResult):
    """
    Publish diagnostics for a document.
    
    Uses diagnostics engine to convert parse errors to LSP diagnostics.
    """
    # Get document content
    document = zolo_server.workspace.get_text_document(uri)
    content = document.source
    
    # Extract filename from URI for context-aware diagnostics
    from urllib.parse import urlparse, unquote
    parsed_uri = urlparse(uri)
    filename = Path(unquote(parsed_uri.path)).name if parsed_uri.path else None
    
    # Get diagnostics from engine (includes parsing and validation)
    diagnostics = get_all_diagnostics(content, include_style=True, filename=filename)
    
    zolo_server.text_document_publish_diagnostics(
        lsp_types.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
    )


def main():
    """Main entry point for the LSP server."""
    logger.info("Starting Zolo Language Server")
    
    try:
        # Start server on stdio
        zolo_server.start_io()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
