"""
Unit tests for MarkdownTerminalParser - Phase 1

Tests inline markdown parsing: bold, italic, code
"""

import sys
from markdown_terminal_parser import MarkdownTerminalParser, parse_markdown_inline


def test_bold_conversion():
    """Test **bold** and __bold__ conversion."""
    parser = MarkdownTerminalParser()
    
    # Test ** style
    result = parser.parse_inline("This is **bold** text")
    assert '\033[1m' in result  # ANSI bold present
    assert 'bold\033[0m' in result  # Reset after bold
    print("✓ Bold (**) test passed")
    
    # Test __ style
    result = parser.parse_inline("This is __bold__ text")
    assert '\033[1m' in result
    print("✓ Bold (__) test passed")
    
    # Test multiple bold sections
    result = parser.parse_inline("**first** and **second** bold")
    assert result.count('\033[1m') == 2
    print("✓ Multiple bold test passed")


def test_italic_conversion():
    """Test *italic* and _italic_ conversion."""
    parser = MarkdownTerminalParser()
    
    # Test * style
    result = parser.parse_inline("This is *italic* text")
    assert '\033[2m' in result  # ANSI dim present (italic fallback)
    assert 'italic\033[0m' in result
    print("✓ Italic (*) test passed")
    
    # Test _ style
    result = parser.parse_inline("This is _italic_ text")
    assert '\033[2m' in result
    print("✓ Italic (_) test passed")


def test_code_conversion():
    """Test `code` conversion."""
    parser = MarkdownTerminalParser()
    
    result = parser.parse_inline("This is `code` text")
    assert '\033[36m' in result  # ANSI cyan present
    assert 'code\033[0m' in result
    print("✓ Code test passed")
    
    # Test multiple code blocks
    result = parser.parse_inline("`first` and `second` code")
    assert result.count('\033[36m') == 2
    print("✓ Multiple code test passed")


def test_nested_patterns():
    """Test nested markdown patterns."""
    parser = MarkdownTerminalParser()
    
    # Bold with code inside
    result = parser.parse_inline("**bold `code` text**")
    assert '\033[1m' in result  # Bold
    assert '\033[36m' in result  # Code (cyan)
    print("✓ Nested bold+code test passed")
    
    # All three together
    result = parser.parse_inline("This is **bold**, *italic*, and `code`")
    assert '\033[1m' in result  # Bold
    assert '\033[2m' in result  # Italic/dim
    assert '\033[36m' in result  # Code
    print("✓ Combined patterns test passed")


def test_no_false_matches():
    """Test that patterns don't match incorrectly."""
    parser = MarkdownTerminalParser()
    
    # Single asterisk shouldn't trigger bold
    result = parser.parse_inline("2 * 3 = 6")
    # Should not have bold ANSI codes
    assert result.count('\033[1m') == 0
    print("✓ No false bold match test passed")
    
    # Single backtick at end shouldn't crash
    result = parser.parse_inline("This ends with `")
    # Should not crash and should not have code formatting
    assert '\033[36m' not in result or result.count('`') > 0
    print("✓ Incomplete backtick test passed")


def test_utility_function():
    """Test convenience function."""
    result = parse_markdown_inline("**bold** and `code`")
    assert '\033[1m' in result
    assert '\033[36m' in result
    print("✓ Utility function test passed")


def test_real_world_example():
    """Test with real content from zUI.zBreakpoints.zolo"""
    parser = MarkdownTerminalParser()
    
    # Actual content from the zolo file
    content = "* <span class=\"zText-error\">**zD**</span> = Display utility prefix"
    result = parser.parse_inline(content)
    
    # Bold should be converted
    assert '\033[1m' in result
    assert 'zD\033[0m' in result
    
    # HTML tags still present (Phase 2 will handle those)
    assert '<span' in result
    
    print("✓ Real-world example test passed")
    print(f"  Input:  {content}")
    print(f"  Output: {result}")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Phase 1: Inline Markdown Parser Tests")
    print("=" * 60)
    
    tests = [
        test_bold_conversion,
        test_italic_conversion,
        test_code_conversion,
        test_nested_patterns,
        test_no_false_matches,
        test_utility_function,
        test_real_world_example,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n{test.__name__}:")
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
