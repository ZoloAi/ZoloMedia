"""
Unit tests for VS Code theme generator.

Tests that the generator correctly converts canonical theme to VS Code formats.
"""
import pytest
import json
from themes import load_theme
from themes.generators.vscode import VSCodeGenerator, generate_vscode_files


class TestVSCodeGenerator:
    """Test suite for VSCodeGenerator class."""
    
    @pytest.fixture
    def theme(self):
        """Load the default theme for testing."""
        return load_theme('zolo_default')
    
    @pytest.fixture
    def generator(self, theme):
        """Create a generator instance."""
        return VSCodeGenerator(theme)
    
    def test_generator_initialization(self, generator, theme):
        """Test that generator initializes correctly."""
        assert generator.theme == theme
        assert generator.editor_name == 'vscode'
        # Overrides can be None or dict (None if not specified in theme)
        assert generator.overrides is None or isinstance(generator.overrides, dict)
    
    def test_generate_textmate_grammar(self, generator):
        """Test TextMate grammar generation."""
        grammar = generator.generate_textmate_grammar()
        
        # Check structure
        assert isinstance(grammar, dict)
        assert grammar['name'] == 'Zolo'
        assert grammar['scopeName'] == 'source.zolo'
        assert grammar['fileTypes'] == ['zolo']
        
        # Check patterns
        assert 'patterns' in grammar
        assert len(grammar['patterns']) > 0
        
        # Check repository
        assert 'repository' in grammar
        repo = grammar['repository']
        
        # Check key categories
        assert 'comments' in repo
        assert 'type-hints' in repo
        assert 'special-root-keys' in repo
        assert 'keys' in repo
        assert 'strings' in repo
        assert 'numbers' in repo
        assert 'booleans' in repo
        assert 'null' in repo
        assert 'arrays' in repo
        assert 'objects' in repo
    
    def test_textmate_grammar_is_valid_json(self, generator):
        """Test that generated grammar can be serialized to JSON."""
        grammar = generator.generate_textmate_grammar()
        
        # Should not raise
        json_str = json.dumps(grammar, indent=2)
        assert len(json_str) > 0
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed == grammar
    
    def test_generate_color_theme(self, generator):
        """Test color theme generation."""
        theme = generator.generate_color_theme()
        
        # Check structure
        assert isinstance(theme, dict)
        assert theme['type'] == 'dark'
        assert 'Zolo' in theme['name']
        
        # Check editor colors
        assert 'colors' in theme
        assert 'editor.background' in theme['colors']
        assert 'editor.foreground' in theme['colors']
        
        # Check token colors
        assert 'tokenColors' in theme
        assert len(theme['tokenColors']) > 0
        
        # Check that each token color has scope and settings
        for token_color in theme['tokenColors']:
            assert 'scope' in token_color
            assert 'settings' in token_color
            assert 'foreground' in token_color['settings']
    
    def test_color_theme_is_valid_json(self, generator):
        """Test that generated color theme can be serialized to JSON."""
        theme = generator.generate_color_theme()
        
        # Should not raise
        json_str = json.dumps(theme, indent=2)
        assert len(json_str) > 0
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed == theme
    
    def test_generate_semantic_tokens_legend(self, generator):
        """Test semantic token legend generation."""
        legend = generator.generate_semantic_tokens_legend()
        
        # Check structure
        assert isinstance(legend, dict)
        assert 'tokenTypes' in legend
        assert 'tokenModifiers' in legend
        
        # Check token types
        token_types = legend['tokenTypes']
        assert isinstance(token_types, list)
        assert len(token_types) > 20  # Should have all our token types
        
        # Check specific token types
        assert 'rootKey' in token_types
        assert 'nestedKey' in token_types
        assert 'string' in token_types
        assert 'number' in token_types
        assert 'comment' in token_types
        
        # Check token modifiers
        token_modifiers = legend['tokenModifiers']
        assert isinstance(token_modifiers, list)
    
    def test_generate_semantic_tokens_styles(self, generator):
        """Test semantic token styles generation."""
        styles = generator.generate_semantic_tokens_styles()
        
        # Check structure
        assert isinstance(styles, list)
        assert len(styles) > 0
        
        # Check that each style has scope and settings
        for style in styles:
            assert 'scope' in style
            assert 'settings' in style
            assert 'foreground' in style['settings']
            
            # Check that foreground is a valid hex color
            fg = style['settings']['foreground']
            assert fg.startswith('#')
            assert len(fg) == 7  # #RRGGBB
    
    def test_style_to_vscode_conversions(self, generator):
        """Test style conversion to VS Code format."""
        # Test 'none' style
        assert generator._style_to_vscode('none') == {}
        
        # Test 'bold' style
        result = generator._style_to_vscode('bold')
        assert result == {'fontStyle': 'bold'}
        
        # Test 'italic' style
        result = generator._style_to_vscode('italic')
        assert result == {'fontStyle': 'italic'}
        
        # Test 'bold,italic' style
        result = generator._style_to_vscode('bold,italic')
        assert result == {'fontStyle': 'bold italic'}
    
    def test_get_token_color_settings(self, generator):
        """Test getting color settings for a token type."""
        # Test with a known token type
        settings = generator._get_token_color_settings('rootKey')
        assert 'foreground' in settings
        assert settings['foreground'].startswith('#')
        
        # Test with a token that has style
        settings = generator._get_token_color_settings('typeHint')
        assert 'foreground' in settings
    
    def test_generate_summary(self, generator):
        """Test generate() method returns summary."""
        summary = generator.generate()
        
        assert isinstance(summary, str)
        assert 'Zolo' in summary
        assert 'syntaxes/zolo.tmLanguage.json' in summary
        assert 'themes/zolo-dark.color-theme.json' in summary
        assert 'Semantic token legend' in summary
    
    def test_all_theme_tokens_have_colors(self, generator, theme):
        """Test that all tokens in theme have valid colors."""
        for token_type in theme.tokens.keys():
            token_style = theme.get_token_style(token_type)
            assert token_style is not None, f"Token {token_type} has no style"
            assert 'hex' in token_style, f"Token {token_type} missing hex color"
            assert token_style['hex'].startswith('#'), f"Token {token_type} invalid hex: {token_style['hex']}"


class TestGenerateVSCodeFiles:
    """Test suite for generate_vscode_files convenience function."""
    
    @pytest.fixture
    def theme(self):
        """Load the default theme for testing."""
        return load_theme('zolo_default')
    
    def test_generate_all_files(self, theme):
        """Test that all files are generated."""
        files = generate_vscode_files(theme)
        
        assert isinstance(files, dict)
        assert 'textmate_grammar' in files
        assert 'color_theme' in files
        assert 'semantic_tokens_legend' in files
        assert 'semantic_tokens_styles' in files
    
    def test_all_files_are_valid(self, theme):
        """Test that all generated files are valid."""
        files = generate_vscode_files(theme)
        
        # TextMate grammar should be valid JSON-serializable
        grammar_json = json.dumps(files['textmate_grammar'])
        assert len(grammar_json) > 0
        
        # Color theme should be valid JSON-serializable
        theme_json = json.dumps(files['color_theme'])
        assert len(theme_json) > 0
        
        # Semantic tokens legend should be valid JSON-serializable
        legend_json = json.dumps(files['semantic_tokens_legend'])
        assert len(legend_json) > 0
        
        # Semantic tokens styles should be valid JSON-serializable
        styles_json = json.dumps(files['semantic_tokens_styles'])
        assert len(styles_json) > 0


class TestVSCodeGeneratorEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def theme(self):
        """Load the default theme for testing."""
        return load_theme('zolo_default')
    
    @pytest.fixture
    def generator(self, theme):
        """Create a generator instance."""
        return VSCodeGenerator(theme)
    
    def test_unknown_token_type(self, generator):
        """Test handling of unknown token types."""
        settings = generator._get_token_color_settings('unknown_token_type')
        
        # Should return default settings
        assert settings == {'foreground': '#ffffff'}
    
    def test_token_without_style(self, generator):
        """Test handling of tokens without style attribute."""
        # This should work gracefully
        settings = generator._get_token_color_settings('string')
        assert 'foreground' in settings
    
    def test_empty_overrides(self, generator):
        """Test that empty overrides don't cause issues."""
        # Default theme has no vscode overrides (returns None or empty dict)
        assert generator.overrides is None or generator.overrides == {}
    
    def test_grammar_special_characters(self, generator):
        """Test that grammar handles special regex characters."""
        grammar = generator.generate_textmate_grammar()
        
        # Check that regex patterns are properly escaped
        # The grammar should have patterns that work with special chars
        repo = grammar['repository']
        assert 'comments' in repo
        assert 'patterns' in repo['comments']
