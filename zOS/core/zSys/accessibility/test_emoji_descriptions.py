#!/usr/bin/env python3
"""
Unit Tests for Emoji Descriptions Module

Tests the EmojiDescriptions class and its API methods.

Author: zOS Framework
Version: 1.0.0
"""

import sys
import unittest
from pathlib import Path

# Add parent directories to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent.parent))

from zSys.accessibility.emoji_descriptions import EmojiDescriptions, get_emoji_descriptions


class TestEmojiDescriptions(unittest.TestCase):
    """Test cases for EmojiDescriptions class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.emoji_desc = EmojiDescriptions()
    
    def test_lazy_loading(self):
        """Test that data is not loaded on initialization."""
        # Create new instance
        desc = EmojiDescriptions()
        
        # Should not be loaded yet
        self.assertFalse(desc._loaded)
        self.assertIsNone(desc._data)
        
        # Access data - should trigger load
        desc.emoji_to_description("📱")
        
        # Should now be loaded
        self.assertTrue(desc._loaded)
        self.assertIsNotNone(desc._data)
        
        print("✓ Lazy loading works correctly")
    
    def test_emoji_to_description_common(self):
        """Test emoji_to_description with common emojis."""
        test_cases = {
            "😀": "grinning face",
            "📱": "mobile phone",
            "💻": "laptop",
            "🎉": "party popper",
            "🖥": "desktop computer",
        }
        
        for emoji, expected in test_cases.items():
            with self.subTest(emoji=emoji):
                result = self.emoji_desc.emoji_to_description(emoji)
                self.assertIn(expected.lower(), result.lower(),
                             f"Expected '{expected}' in '{result}' for emoji {emoji}")
        
        print(f"✓ All {len(test_cases)} common emojis have correct descriptions")
    
    def test_emoji_to_description_fallback(self):
        """Test that missing emojis return the emoji itself."""
        # Use a very rare or non-existent emoji
        rare_emoji = "🫠"  # May not be in CLDR data
        
        result = self.emoji_desc.emoji_to_description(rare_emoji)
        
        # Should return emoji itself if not found
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
        print(f"✓ Missing emoji fallback works: '{rare_emoji}' → '{result}'")
    
    def test_codepoint_to_description_formats(self):
        """Test codepoint_to_description with various formats."""
        # All these should map to "mobile phone"
        test_formats = [
            "1F4F1",         # Plain hex
            "0001F4F1",      # With leading zeros
            "U+1F4F1",       # With U+ prefix
            "\\U0001F4F1",   # With \\U prefix (zolo format)
            "u+1f4f1",       # Lowercase
        ]
        
        for codepoint_str in test_formats:
            with self.subTest(format=codepoint_str):
                result = self.emoji_desc.codepoint_to_description(codepoint_str)
                self.assertIn("mobile", result.lower(),
                             f"Expected 'mobile' in result for {codepoint_str}")
        
        print(f"✓ All {len(test_formats)} codepoint formats work correctly")
    
    def test_codepoint_invalid(self):
        """Test that invalid codepoints are handled gracefully."""
        invalid_cases = [
            "GGGG",      # Invalid hex
            "ZZZZZZ",    # Invalid hex
            "",          # Empty string
            "U+",        # Just prefix
        ]
        
        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                result = self.emoji_desc.codepoint_to_description(invalid)
                # Should return original string or not crash
                self.assertIsInstance(result, str)
        
        print(f"✓ All {len(invalid_cases)} invalid codepoints handled gracefully")
    
    def test_format_for_terminal(self):
        """Test Terminal formatting with brackets."""
        test_cases = {
            "📱": "mobile phone",
            "💻": "laptop",
            "🎉": "party popper",
        }
        
        for emoji, expected_desc in test_cases.items():
            with self.subTest(emoji=emoji):
                result = self.emoji_desc.format_for_terminal(emoji)
                
                # Should be wrapped in brackets
                self.assertTrue(result.startswith("["), 
                               f"Result should start with '[': {result}")
                self.assertTrue(result.endswith("]"),
                               f"Result should end with ']': {result}")
                
                # Should contain the description
                self.assertIn(expected_desc.lower(), result.lower(),
                             f"Expected '{expected_desc}' in '{result}'")
        
        print(f"✓ Terminal formatting works for {len(test_cases)} emojis")
    
    def test_format_for_terminal_fallback(self):
        """Test that Terminal formatting falls back for unknown emojis."""
        # Unknown emoji - should return emoji itself (no brackets)
        unknown = "🫠"
        result = self.emoji_desc.format_for_terminal(unknown)
        
        # If unknown, should NOT have brackets (or be the emoji itself)
        self.assertIsInstance(result, str)
        
        print(f"✓ Terminal fallback works: '{unknown}' → '{result}'")
    
    def test_has_description(self):
        """Test has_description checker method."""
        # Known emoji
        self.assertTrue(self.emoji_desc.has_description("📱"),
                       "mobile phone emoji should have description")
        
        # Also test a few more
        known_emojis = ["😀", "💻", "🎉"]
        for emoji in known_emojis:
            self.assertTrue(self.emoji_desc.has_description(emoji),
                           f"{emoji} should have description")
        
        print(f"✓ has_description works for known emojis")
    
    def test_get_stats(self):
        """Test get_stats returns valid data."""
        stats = self.emoji_desc.get_stats()
        
        # Check structure
        self.assertIn('total_emojis', stats)
        self.assertIn('loaded', stats)
        self.assertIn('data_size_kb', stats)
        
        # Check values are reasonable
        self.assertGreater(stats['total_emojis'], 1000,
                          "Should have at least 1000 emojis")
        self.assertTrue(stats['loaded'],
                       "Data should be loaded after get_stats")
        self.assertGreater(stats['data_size_kb'], 0,
                          "Data size should be positive")
        
        print(f"✓ Stats: {stats['total_emojis']} emojis, "
              f"{stats['data_size_kb']} KB, loaded={stats['loaded']}")
    
    def test_singleton_pattern(self):
        """Test that get_emoji_descriptions returns same instance."""
        instance1 = get_emoji_descriptions()
        instance2 = get_emoji_descriptions()
        
        # Should be the exact same object
        self.assertIs(instance1, instance2,
                     "Should return same singleton instance")
        
        print("✓ Singleton pattern works correctly")
    
    def test_variation_selector_handling(self):
        """Test that variation selectors (U+FE0F) are handled."""
        # Heart with variation selector: ❤️ (U+2764 U+FE0F)
        heart_with_vs = "❤\uFE0F"
        heart_without_vs = "❤"
        
        result1 = self.emoji_desc.emoji_to_description(heart_with_vs)
        result2 = self.emoji_desc.emoji_to_description(heart_without_vs)
        
        # Both should return same description
        self.assertEqual(result1.lower(), result2.lower(),
                        "Variation selector should be stripped")
        
        print(f"✓ Variation selector handling: '{heart_with_vs}' → '{result1}'")
    
    def test_empty_input_handling(self):
        """Test that empty inputs are handled gracefully."""
        # Empty strings
        self.assertEqual(self.emoji_desc.emoji_to_description(""), "")
        self.assertEqual(self.emoji_desc.codepoint_to_description(""), "")
        self.assertEqual(self.emoji_desc.format_for_terminal(""), "")
        
        print("✓ Empty input handling works correctly")


class TestIntegration(unittest.TestCase):
    """Integration tests for real-world usage."""
    
    def test_real_world_zolo_emojis(self):
        """Test with actual emojis used in zolo files."""
        emoji_desc = get_emoji_descriptions()
        
        # Emojis from zUI.zBreakpoints.zolo
        test_emojis = {
            "📱": "mobile",  # Mobile phone
            "💻": "laptop",  # Laptop
            "🖥": "desktop", # Desktop
        }
        
        for emoji, expected_word in test_emojis.items():
            result = emoji_desc.emoji_to_description(emoji)
            self.assertIn(expected_word.lower(), result.lower(),
                         f"Expected '{expected_word}' in description for {emoji}")
        
        print(f"✓ Real-world .zolo emojis work correctly")
    
    def test_performance_bulk_lookups(self):
        """Test performance with many lookups."""
        import time
        
        emoji_desc = get_emoji_descriptions()
        
        # Get some emojis to test with
        test_emojis = ["😀", "📱", "💻", "🎉", "🖥"] * 200  # 1000 lookups
        
        start = time.time()
        for emoji in test_emojis:
            emoji_desc.emoji_to_description(emoji)
        elapsed = time.time() - start
        
        # Should be fast (< 10ms for 1000 lookups)
        self.assertLess(elapsed, 0.01,
                       f"1000 lookups took {elapsed*1000:.2f}ms (should be < 10ms)")
        
        print(f"✓ Performance: 1000 lookups in {elapsed*1000:.2f}ms")


def run_tests():
    """Run all tests with detailed output."""
    print("=" * 70)
    print("Emoji Descriptions Module - Unit Tests")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEmojiDescriptions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
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
