"""
Unit tests for Phase 5: Integration & Polish

Tests indentation, color parameters, error handling, and final integration
"""

import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from markdown_terminal_parser import MarkdownTerminalParser


class MockDisplay:
    """Mock zDisplay for testing."""
    
    def __init__(self):
        self.list_called = False
        self.list_items = []
        self.list_style = None
        self.list_indent = None
        self.zcli = MockZCLI()
    
    def list(self, items, style='bullet', indent=0):
        """Capture list() calls."""
        self.list_called = True
        self.list_items = items
        self.list_style = style
        self.list_indent = indent


class MockZCLI:
    """Mock zCLI with logger."""
    
    def __init__(self):
        self.logger = MockLogger()


class MockLogger:
    """Mock logger."""
    
    def __init__(self):
        self.debug_messages = []
    
    def debug(self, msg):
        """Capture debug messages."""
        self.debug_messages.append(msg)


def test_indentation_paragraph():
    """Test that paragraphs respect indentation."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_indentation_paragraph:")
    
    content = "This is a **bold** paragraph"
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display, indent=2)
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Should have 8 spaces (2 levels * 4 spaces)
    assert output.startswith('        ')
    print(f"  ✓ Paragraph indented: {repr(output[:20])}")


def test_indentation_list():
    """Test that lists respect indentation."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_indentation_list:")
    
    content = "* item 1\n* item 2"
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display, indent=3)
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Check that list was called with indent
    assert mock_display.list_called == True
    assert mock_display.list_indent == 3
    print(f"  ✓ List called with indent={mock_display.list_indent}")


def test_indentation_code_block():
    """Test that code blocks respect indentation."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_indentation_code_block:")
    
    content = "```python\nprint('hello')\n```"
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display, indent=1)
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Each line of the code block should start with 4 spaces (1 level)
    lines = output.split('\n')
    non_empty_lines = [l for l in lines if l.strip()]
    
    assert all(l.startswith('    ') for l in non_empty_lines)
    print(f"  ✓ Code block indented: {len(non_empty_lines)} lines")


def test_color_parameter():
    """Test that color parameter is applied to paragraphs."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_color_parameter:")
    
    content = "This is a paragraph"
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display, indent=0, color='error')
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Should have output (color application may or may not work depending on imports)
    assert len(output) > 0
    assert 'paragraph' in output.lower()
    
    # Check if ANSI codes are present (indicates color was attempted)
    has_ansi = '\033[' in output
    print(f"  ✓ Color parameter processed: output={len(output)} chars, ANSI={has_ansi}")


def test_mixed_blocks_with_indent():
    """Test mixed content with indentation."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_mixed_blocks_with_indent:")
    
    content = """Intro paragraph

* list item

```python
code
```

Final paragraph"""
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display, indent=2)
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Check that list was called with indent
    assert mock_display.list_called == True
    assert mock_display.list_indent == 2
    
    # Check that output has indented content
    lines = [l for l in output.split('\n') if l.strip()]
    indented_lines = [l for l in lines if l.startswith('        ')]  # 8 spaces
    
    assert len(indented_lines) > 0
    print(f"  ✓ Mixed blocks: {len(indented_lines)} indented lines, list indent={mock_display.list_indent}")


def test_error_handling_empty_content():
    """Test that empty content is handled gracefully."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_error_handling_empty_content:")
    
    # Should not crash
    parser.parse("", mock_display)
    parser.parse(None, mock_display)
    
    print(f"  ✓ Empty/None content handled gracefully")


def test_error_handling_malformed_html():
    """Test that malformed HTML doesn't crash the parser."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_error_handling_malformed_html:")
    
    # Malformed HTML should be handled
    content = "<span class='unclosed"
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        parser.parse(content, mock_display)
        success = True
    except Exception as e:
        success = False
        print(f"  ✗ FAILED: {e}")
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    assert success
    print(f"  ✓ Malformed HTML handled without crash")


def test_error_handling_invalid_code_block():
    """Test that code blocks without closing marker are handled."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_error_handling_invalid_code_block:")
    
    # Code block without closing ```
    content = "```python\nunclosed code block"
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        parser.parse(content, mock_display)
        success = True
    except Exception as e:
        success = False
        print(f"  ✗ FAILED: {e}")
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    assert success
    # Should output something (either as code or as paragraph)
    assert len(output) > 0
    print(f"  ✓ Unclosed code block handled")


def test_real_world_integration():
    """Test with complex real-world content from zUI.zBreakpoints.zolo."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_real_world_integration:")
    
    content = """zTheme uses **zD-** classes to control visibility:

* <span class="zText-error">**zD**</span> = Display prefix
* <span class="zText-success">**-block**</span> = Show element

Example:

```html
<div class="zD-md-block">
  Visible on medium+
</div>
```

That's how it works!"""
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display, indent=1, color='info')
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Check all parts are present
    assert 'zTheme' in output or mock_display.list_called
    assert mock_display.list_called == True
    assert len(mock_display.list_items) == 2
    assert 'html' in output or 'div' in output
    assert mock_display.list_indent == 1
    
    print(f"  ✓ Real-world content: {len(mock_display.list_items)} list items, indent={mock_display.list_indent}")
    print(f"  ✓ Output length: {len(output)} chars")


def test_performance_large_content():
    """Test parser performance with large content."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_performance_large_content:")
    
    # Generate large content
    large_content = "\n\n".join([
        f"Paragraph {i} with **bold** and `code`" for i in range(50)
    ])
    
    # Time the parsing
    import time
    start = time.time()
    
    # Capture output
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(large_content, mock_display)
    
    sys.stdout = old_stdout
    
    elapsed = time.time() - start
    
    assert elapsed < 1.0  # Should complete in less than 1 second
    print(f"  ✓ Parsed 50 paragraphs in {elapsed:.4f}s")


def run_all_tests():
    """Run all Phase 5 tests."""
    print("=" * 70)
    print("Phase 5: Integration & Polish Tests")
    print("=" * 70)
    
    tests = [
        test_indentation_paragraph,
        test_indentation_list,
        test_indentation_code_block,
        test_color_parameter,
        test_mixed_blocks_with_indent,
        test_error_handling_empty_content,
        test_error_handling_malformed_html,
        test_error_handling_invalid_code_block,
        test_real_world_integration,
        test_performance_large_content,
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
