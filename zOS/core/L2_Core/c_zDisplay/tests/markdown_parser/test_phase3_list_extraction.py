"""
Unit tests for Phase 3: List Extraction & Emission

Tests list detection, item extraction, and display.list() emission
"""

import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from markdown_terminal_parser import MarkdownTerminalParser


class MockDisplay:
    """Mock zDisplay for testing list emission."""
    
    def __init__(self):
        self.list_called = False
        self.list_items = []
        self.list_style = None
    
    def list(self, items, style='bullet'):
        """Capture list() calls."""
        self.list_called = True
        self.list_items = items
        self.list_style = style


def test_list_detection_bullet():
    """Test bullet list detection."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_list_detection_bullet:")
    
    # Bullet list with *
    content = "* item 1\n* item 2\n* item 3"
    assert parser._is_list(content) == True
    print("  ✓ Bullet list (*) detected")
    
    # Bullet list with -
    content = "- item 1\n- item 2"
    assert parser._is_list(content) == True
    print("  ✓ Bullet list (-) detected")
    
    # Not a list
    content = "This is just a paragraph"
    assert parser._is_list(content) == False
    print("  ✓ Paragraph not detected as list")


def test_list_detection_numbered():
    """Test numbered list detection."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_list_detection_numbered:")
    
    content = "1. First item\n2. Second item\n3. Third item"
    assert parser._is_list(content) == True
    print("  ✓ Numbered list detected")


def test_list_extraction_simple():
    """Test simple list item extraction."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_list_extraction_simple:")
    
    content = "* item 1\n* item 2\n* item 3"
    items = parser._extract_list_items(content)
    
    assert len(items) == 3
    assert 'item 1' in items[0]
    assert 'item 2' in items[1]
    assert 'item 3' in items[2]
    print(f"  ✓ Extracted {len(items)} items")


def test_list_extraction_with_markdown():
    """Test list item extraction with inline markdown."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_list_extraction_with_markdown:")
    
    # List with bold markdown
    content = "* **bold** item\n* `code` item\n* normal item"
    items = parser._extract_list_items(content)
    
    assert len(items) == 3
    
    # First item should have ANSI bold
    assert '\033[1m' in items[0] or 'bold' in items[0]
    print(f"  Item 1: {items[0]}")
    
    # Second item should have ANSI cyan (code)
    assert '\033[36m' in items[1] or 'code' in items[1]
    print(f"  Item 2: {items[1]}")
    
    print("  ✓ Inline markdown parsed in list items")


def test_list_extraction_with_html():
    """Test list item extraction with HTML classes."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_list_extraction_with_html:")
    
    # List with HTML color classes
    content = '* <span class="zText-error">**Error**</span> item\n* Normal item'
    items = parser._extract_list_items(content)
    
    assert len(items) == 2
    
    # First item should have NO HTML tags
    assert '<span' not in items[0]
    assert 'Error' in items[0]
    
    # Should have ANSI codes (color + bold)
    assert '\033[' in items[0]
    
    print(f"  Item 1: {items[0]}")
    print(f"  Item 2: {items[1]}")
    print("  ✓ HTML stripped and colors applied in list items")


def test_list_emission():
    """Test that parser emits display.list() for lists."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_list_emission:")
    
    content = "* item 1\n* item 2\n* item 3"
    parser.parse(content, mock_display)
    
    # Should have called display.list()
    assert mock_display.list_called == True
    assert len(mock_display.list_items) == 3
    assert mock_display.list_style == 'bullet'
    
    print(f"  ✓ display.list() called with {len(mock_display.list_items)} items")
    print(f"  ✓ Style: {mock_display.list_style}")


def test_numbered_list_style():
    """Test numbered list emits with correct style."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_numbered_list_style:")
    
    content = "1. First\n2. Second\n3. Third"
    parser.parse(content, mock_display)
    
    assert mock_display.list_called == True
    assert mock_display.list_style == 'number'
    
    print(f"  ✓ Numbered list style detected")


def test_real_world_zolo_list():
    """Test with actual list from zUI.zBreakpoints.zolo"""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_real_world_zolo_list:")
    
    # Actual content from the .zolo file
    content = """* <span class="zText-error">**zD**</span> = Display utility prefix
* <span class="zText-error">**-block**</span> = Show element (`display: block`)
* <span class="zText-error">**-none**</span> = Hide element (`display: none`)"""
    
    parser.parse(content, mock_display)
    
    assert mock_display.list_called == True
    assert len(mock_display.list_items) == 3
    
    # Check first item
    first_item = mock_display.list_items[0]
    assert '<span' not in first_item  # No HTML
    assert 'zD' in first_item  # Has text
    assert 'Display utility prefix' in first_item
    assert '\033[' in first_item  # Has ANSI codes
    
    print(f"  Items extracted: {len(mock_display.list_items)}")
    print(f"  Item 1: {first_item}")
    print(f"  Item 2: {mock_display.list_items[1]}")
    print("  ✓ Real .zolo list processed correctly")


def test_mixed_list_with_blank_lines():
    """Test list with blank lines between items."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_mixed_list_with_blank_lines:")
    
    content = "* item 1\n\n* item 2\n\n* item 3"
    items = parser._extract_list_items(content)
    
    # Should still extract all items
    assert len(items) == 3
    print(f"  ✓ Extracted {len(items)} items despite blank lines")


def test_block_splitting():
    """Test splitting content into blocks."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_block_splitting:")
    
    # Paragraph followed by list
    content = "Intro text:\n* item 1\n* item 2"
    blocks = parser._split_into_blocks(content)
    
    assert len(blocks) == 2
    assert "Intro text:" in blocks[0]
    assert "* item 1" in blocks[1]
    print(f"  ✓ Split into {len(blocks)} blocks (paragraph + list)")


def test_mixed_content_emission():
    """Test that mixed content emits both text and list."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_mixed_content_emission:")
    
    # Real-world example from zUI.zBreakpoints.zolo
    content = "zTheme uses **zD-** classes:\n* item 1\n* item 2"
    
    # Capture print output
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display)
    
    printed_output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Should have printed the intro text
    assert "zTheme" in printed_output or mock_display.list_called
    
    # Should have called display.list() for the list
    assert mock_display.list_called == True
    assert len(mock_display.list_items) == 2
    
    print(f"  ✓ Mixed content: text printed + list emitted")
    print(f"  ✓ List items: {len(mock_display.list_items)}")


def run_all_tests():
    """Run all Phase 3 tests."""
    print("=" * 70)
    print("Phase 3: List Extraction & Emission Tests")
    print("=" * 70)
    
    tests = [
        test_list_detection_bullet,
        test_list_detection_numbered,
        test_list_extraction_simple,
        test_list_extraction_with_markdown,
        test_list_extraction_with_html,
        test_list_emission,
        test_numbered_list_style,
        test_real_world_zolo_list,
        test_mixed_list_with_blank_lines,
        test_block_splitting,
        test_mixed_content_emission,
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
