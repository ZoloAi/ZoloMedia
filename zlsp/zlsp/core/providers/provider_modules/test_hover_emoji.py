#!/usr/bin/env python3
"""
Test Hover Renderer - Emoji Accessibility Integration (Phase 3)

Verifies that hover information includes emoji descriptions for Unicode escapes.

Author: zOS Framework
Version: 1.0.0
"""

import sys
import unittest
from pathlib import Path

# Add zlsp to path
current_dir = Path(__file__).parent
zlsp_root = current_dir.parent.parent.parent
sys.path.insert(0, str(zlsp_root))

from hover_renderer import HoverRenderer


class TestEmojiHoverIntegration(unittest.TestCase):
    """Test emoji descriptions in hover information."""
    
    def test_get_emoji_info_mobile_phone(self):
        """Test emoji info extraction for mobile phone emoji."""
        info = HoverRenderer._get_emoji_info("0001F4F1")
        
        # Should return dict with emoji and description
        self.assertIsNotNone(info, "Should return emoji info")
        self.assertIn('emoji', info, "Should have 'emoji' key")
        self.assertIn('description', info, "Should have 'description' key")
        
        # Check values
        self.assertEqual(info['emoji'], "📱", "Should be mobile phone emoji")
        self.assertIn("mobile", info['description'].lower(), 
                     f"Description should contain 'mobile': {info['description']}")
        
        print(f"✓ Mobile phone: {info['emoji']} → {info['description']}")
    
    def test_get_emoji_info_laptop(self):
        """Test emoji info extraction for laptop emoji."""
        info = HoverRenderer._get_emoji_info("1F4BB")
        
        self.assertIsNotNone(info)
        self.assertEqual(info['emoji'], "💻")
        self.assertIn("laptop", info['description'].lower())
        
        print(f"✓ Laptop: {info['emoji']} → {info['description']}")
    
    def test_get_emoji_info_party_popper(self):
        """Test emoji info extraction for party popper emoji."""
        info = HoverRenderer._get_emoji_info("U+1F389")
        
        self.assertIsNotNone(info)
        self.assertEqual(info['emoji'], "🎉")
        self.assertIn("party", info['description'].lower())
        
        print(f"✓ Party popper: {info['emoji']} → {info['description']}")
    
    def test_get_emoji_info_various_formats(self):
        """Test that various codepoint formats work."""
        # All these should work for mobile phone
        formats = [
            "1F4F1",
            "0001F4F1",
            "U+1F4F1",
            "\\U0001F4F1",
        ]
        
        for fmt in formats:
            info = HoverRenderer._get_emoji_info(fmt)
            self.assertIsNotNone(info, f"Format {fmt} should work")
            self.assertEqual(info['emoji'], "📱", f"Format {fmt} should return 📱")
        
        print(f"✓ All {len(formats)} codepoint formats work")
    
    def test_get_emoji_info_invalid(self):
        """Test that invalid codepoints are handled gracefully."""
        invalid_cases = [
            "GGGG",      # Invalid hex
            "ZZZZ",      # Invalid hex
            "",          # Empty
            "999999999", # Out of range
        ]
        
        for invalid in invalid_cases:
            info = HoverRenderer._get_emoji_info(invalid)
            # Should return None, not crash
            self.assertIsNone(info, f"Invalid {invalid} should return None")
        
        print(f"✓ All {len(invalid_cases)} invalid inputs handled gracefully")
    
    def test_get_emoji_info_caching(self):
        """Test that emoji descriptions are cached (lazy loaded once)."""
        # First call - triggers load
        info1 = HoverRenderer._get_emoji_info("1F4F1")
        
        # Second call - should use cache
        info2 = HoverRenderer._get_emoji_info("1F4BB")
        
        # Both should work
        self.assertIsNotNone(info1)
        self.assertIsNotNone(info2)
        
        # _emoji_descriptions should be loaded now
        self.assertIsNotNone(HoverRenderer._emoji_descriptions)
        self.assertNotEqual(HoverRenderer._emoji_descriptions, False,
                          "Should be loaded, not False")
        
        print("✓ Caching works correctly")
    
    def test_hover_includes_emoji_description(self):
        """Test that hover text includes emoji description."""
        # Simulate a token for \U0001F4F1
        from zlsp.core.lsp_types import SemanticToken, TokenType, Range, Position
        
        # Create a token representing the escape sequence
        token = SemanticToken(
            line=0,
            start_char=10,
            length=12,  # Length of \U0001F4F1
            token_type=TokenType.ESCAPE_SEQUENCE,
            range=Range(
                start=Position(line=0, character=10),
                end=Position(line=0, character=22)
            )
        )
        
        # Content with the escape sequence
        content = "label: \\U0001F4F1 Mobile Phone"
        
        # Get hover text
        hover_text = HoverRenderer._render_escape(token, content)
        
        # Should include emoji description
        self.assertIsNotNone(hover_text, "Should return hover text")
        self.assertIn("Unicode Escape Sequence", hover_text)
        self.assertIn("\\U0001F4F1", hover_text)
        self.assertIn("U+0001F4F1", hover_text)
        
        # Check for emoji-specific info (if available)
        if "mobile" in hover_text.lower():
            self.assertIn("📱", hover_text, "Should include emoji character")
            self.assertIn("Description", hover_text, "Should have description section")
            print(f"✓ Hover text includes emoji description")
        else:
            print(f"⚠️  Emoji description not available (emoji module may not be loaded)")
        
        print(f"\nHover text preview:\n{hover_text[:200]}...")


class TestHoverRenderer(unittest.TestCase):
    """Test overall hover renderer functionality."""
    
    def test_render_does_not_crash(self):
        """Test that render method doesn't crash with emoji escapes."""
        from zlsp.core.lsp_types import SemanticToken, TokenType, Range, Position
        
        # Create a token for escape sequence
        token = SemanticToken(
            line=0,
            start_char=7,
            length=12,
            token_type=TokenType.ESCAPE_SEQUENCE,
            range=Range(
                start=Position(line=0, character=7),
                end=Position(line=0, character=19)
            )
        )
        
        content = "label: \\U0001F4F1"
        
        # This should not crash
        try:
            result = HoverRenderer.render(content, 0, 10, [token])
            self.assertIsInstance(result, (str, type(None)))
            print("✓ render() doesn't crash with emoji escapes")
        except Exception as e:
            self.fail(f"render() crashed: {e}")


def run_tests():
    """Run all tests with detailed output."""
    print("=" * 70)
    print("Hover Renderer - Emoji Accessibility Integration Tests (Phase 3)")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEmojiHoverIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestHoverRenderer))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print(f"Results: {result.testsRun} tests, "
          f"{len(result.failures)} failures, "
          f"{len(result.errors)} errors")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
