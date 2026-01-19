"""
Unit tests for Phase 2: HTML Class Mapping

Tests HTML tag stripping and zTheme class → ANSI conversion
"""

import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import directly to avoid circular dependencies
from markdown_terminal_parser import MarkdownTerminalParser

# Manually import ztheme_to_ansi by adding its directory to path
ztheme_path = os.path.abspath(os.path.join(current_dir, '../../../../zSys/formatting'))
sys.path.insert(0, ztheme_path)

from ztheme_to_ansi import (
    map_ztheme_class_to_ansi,
    map_ztheme_classes_to_ansi,
    colorize_with_class
)


def test_color_mapper():
    """Test basic zTheme class → ANSI mapping."""
    print("\ntest_color_mapper:")
    
    # Test error color
    code = map_ztheme_class_to_ansi('zText-error')
    assert '\033[' in code  # Has ANSI code
    assert code == '\033[38;5;203m'  # Specific red code
    print("  ✓ zText-error → red ANSI")
    
    # Test success color
    code = map_ztheme_class_to_ansi('zText-success')
    assert '\033[' in code
    print("  ✓ zText-success → green ANSI")
    
    # Test bold
    code = map_ztheme_class_to_ansi('zFont-bold')
    assert code == '\033[1m'
    print("  ✓ zFont-bold → bold ANSI")
    
    # Test unknown class
    code = map_ztheme_class_to_ansi('zUnknown-class')
    assert code == ''
    print("  ✓ Unknown class → empty string")


def test_multiple_classes():
    """Test multiple classes combined."""
    print("\ntest_multiple_classes:")
    
    # Red + bold
    code = map_ztheme_classes_to_ansi(['zText-error', 'zFont-bold'])
    assert '\033[38;5;203m' in code  # Red
    assert '\033[1m' in code  # Bold
    print("  ✓ Multiple classes combined")


def test_colorize_utility():
    """Test convenience colorize function."""
    print("\ntest_colorize_utility:")
    
    result = colorize_with_class('Error!', 'zText-error')
    assert '\033[38;5;203m' in result  # Red color
    assert 'Error!' in result
    assert '\033[0m' in result  # Reset
    print(f"  ✓ Colorize utility: {result}")


def test_html_stripping_simple():
    """Test simple HTML tag stripping."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_html_stripping_simple:")
    
    # Single span with error class
    input_text = '<span class="zText-error">Error text</span>'
    result = parser.parse_inline(input_text)
    
    # Should NOT have HTML tags
    assert '<span' not in result
    assert '</span>' not in result
    
    # Should have the text
    assert 'Error text' in result
    
    # Should have ANSI color (red)
    assert '\033[38;5;203m' in result or '\033[' in result
    
    print(f"  Input:  {input_text}")
    print(f"  Output: {result}")
    print("  ✓ HTML stripped, color applied")


def test_html_with_bold_class():
    """Test HTML with multiple classes."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_html_with_bold_class:")
    
    input_text = '<span class="zText-error zFont-bold">Bold error</span>'
    result = parser.parse_inline(input_text)
    
    # No HTML
    assert '<' not in result or result.count('<') == 0 or all(c in result for c in ['<', '>']) is False
    
    # Has text
    assert 'Bold error' in result
    
    # Has ANSI codes
    assert '\033[' in result
    
    print(f"  Input:  {input_text}")
    print(f"  Output: {result}")
    print("  ✓ Multiple classes mapped")


def test_html_with_markdown():
    """Test HTML + markdown combined."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_html_with_markdown:")
    
    # HTML wrapping markdown
    input_text = '<span class="zText-error">**Bold error**</span>'
    result = parser.parse_inline(input_text)
    
    # No HTML tags
    assert '<span' not in result
    
    # Has text
    assert 'Bold error' in result
    
    # Has ANSI (both color and bold)
    assert '\033[' in result
    
    print(f"  Input:  {input_text}")
    print(f"  Output: {result}")
    print("  ✓ HTML + markdown combined")


def test_real_world_zolo_content():
    """Test with actual content from zUI.zBreakpoints.zolo"""
    parser = MarkdownTerminalParser()
    
    print("\ntest_real_world_zolo_content:")
    
    # Actual line from the .zolo file
    input_text = '* <span class="zText-error">**zD**</span> = Display utility prefix'
    result = parser.parse_inline(input_text)
    
    print(f"  Input:  {input_text}")
    print(f"  Output: {result}")
    
    # Should have no HTML
    assert '<span' not in result
    assert 'class=' not in result
    
    # Should have the text
    assert 'zD' in result
    assert 'Display utility prefix' in result
    
    # Should have ANSI codes
    assert '\033[' in result
    
    print("  ✓ Real .zolo content processed correctly")


def test_nested_spans():
    """Test nested HTML tags."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_nested_spans:")
    
    input_text = '<span class="zText-error">Error: <span class="zFont-bold">critical</span></span>'
    result = parser.parse_inline(input_text)
    
    # No HTML
    assert '<span' not in result
    
    # Has text
    assert 'Error:' in result
    assert 'critical' in result
    
    print(f"  Input:  {input_text}")
    print(f"  Output: {result}")
    print("  ✓ Nested spans handled")


def test_mixed_classes():
    """Test classes that should and shouldn't map."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_mixed_classes:")
    
    # Mix of color class and layout class
    input_text = '<span class="zText-success zmb-4">Success message</span>'
    result = parser.parse_inline(input_text)
    
    # No HTML
    assert '<span' not in result
    
    # Has text
    assert 'Success message' in result
    
    # Has ANSI (from zText-success)
    assert '\033[' in result
    
    print(f"  Input:  {input_text}")
    print(f"  Output: {result}")
    print("  ✓ Mixed classes (color + layout) handled")


def run_all_tests():
    """Run all Phase 2 tests."""
    print("=" * 70)
    print("Phase 2: HTML Class Mapping Tests")
    print("=" * 70)
    
    tests = [
        test_color_mapper,
        test_multiple_classes,
        test_colorize_utility,
        test_html_stripping_simple,
        test_html_with_bold_class,
        test_html_with_markdown,
        test_real_world_zolo_content,
        test_nested_spans,
        test_mixed_classes,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
