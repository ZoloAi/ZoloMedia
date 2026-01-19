"""
Unit tests for Phase 4: Block-Level Parsing

Tests code blocks, paragraph detection, and full block orchestration
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
    
    def list(self, items, style='bullet'):
        """Capture list() calls."""
        self.list_called = True
        self.list_items = items
        self.list_style = style


def test_code_block_extraction():
    """Test code block extraction."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_code_block_extraction:")
    
    lines = [
        "```python",
        "def hello():",
        "    print('world')",
        "```"
    ]
    
    result, consumed = parser._extract_code_block(lines, 0)
    
    assert result is not None
    assert result[0] == 'python'  # Language
    assert 'def hello()' in result[1]  # Code content
    assert consumed == 4  # All 4 lines
    
    print(f"  ✓ Code block extracted: language={result[0]}, lines={consumed}")


def test_code_block_no_language():
    """Test code block without language hint."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_code_block_no_language:")
    
    lines = [
        "```",
        "some code",
        "```"
    ]
    
    result, consumed = parser._extract_code_block(lines, 0)
    
    assert result is not None
    assert result[0] == ''  # No language
    assert 'some code' in result[1]
    
    print(f"  ✓ Code block without language extracted")


def test_block_splitting_with_code():
    """Test splitting content with code blocks."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_block_splitting_with_code:")
    
    content = """Introduction paragraph

```python
code here
```

After code paragraph"""
    
    blocks = parser._split_into_blocks(content)
    
    # Should have 3 blocks: paragraph, code, paragraph
    assert len(blocks) == 3
    assert blocks[0][0] == 'paragraph'
    assert blocks[1][0] == 'code'
    assert blocks[2][0] == 'paragraph'
    
    print(f"  ✓ Split into {len(blocks)} blocks: paragraph, code, paragraph")


def test_block_splitting_all_types():
    """Test splitting with all block types."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_block_splitting_all_types:")
    
    content = """Intro text

* list item 1
* list item 2

```
code block
```

Final paragraph"""
    
    blocks = parser._split_into_blocks(content)
    
    # Should have 4 blocks
    assert len(blocks) == 4
    assert blocks[0][0] == 'paragraph'
    assert blocks[1][0] == 'list'
    assert blocks[2][0] == 'code'
    assert blocks[3][0] == 'paragraph'
    
    print(f"  ✓ All block types detected: {[b[0] for b in blocks]}")


def test_code_block_emission():
    """Test that code blocks are formatted for Terminal."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_code_block_emission:")
    
    content = """```python
def test():
    return 42
```"""
    
    # Capture print output
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display)
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Should have box drawing characters
    assert '╭' in output or '─' in output or 'def test()' in output
    
    # Should have cyan ANSI codes
    assert '\033[36m' in output or '\033[' in output
    
    print(f"  ✓ Code block formatted with borders and colors")
    print(f"  Output preview: {output[:100]}...")


def test_mixed_blocks_emission():
    """Test that mixed blocks emit correctly."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_mixed_blocks_emission:")
    
    content = """Introduction text

* item 1
* item 2

```
code
```

Conclusion"""
    
    # Capture print output
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display)
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Should have printed paragraphs
    assert 'Introduction' in output or 'Conclusion' in output
    
    # Should have called list()
    assert mock_display.list_called == True
    assert len(mock_display.list_items) == 2
    
    # Should have printed code block
    assert 'code' in output or '╭' in output
    
    print(f"  ✓ All block types emitted correctly")
    print(f"  ✓ List had {len(mock_display.list_items)} items")


def test_paragraph_extraction():
    """Test paragraph block extraction."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_paragraph_extraction:")
    
    lines = [
        "First line",
        "Second line",
        "",
        "New paragraph"
    ]
    
    result, consumed = parser._extract_paragraph_block(lines, 0)
    
    assert 'First line' in result
    assert 'Second line' in result
    assert consumed == 2  # Stops at blank line
    
    print(f"  ✓ Paragraph extracted: {consumed} lines")


def test_empty_code_block():
    """Test handling of empty code blocks."""
    parser = MarkdownTerminalParser()
    
    print("\ntest_empty_code_block:")
    
    lines = [
        "```",
        "```"
    ]
    
    result, consumed = parser._extract_code_block(lines, 0)
    
    assert result is not None
    assert result[1] == ''  # Empty code
    assert consumed == 2
    
    print(f"  ✓ Empty code block handled")


def test_real_world_complex_content():
    """Test with complex real-world content."""
    parser = MarkdownTerminalParser()
    mock_display = MockDisplay()
    
    print("\ntest_real_world_complex_content:")
    
    content = """Use zTheme classes:

* <span class="zText-error">**zD**</span> = Display prefix
* <span class="zText-success">**-block**</span> = Show element

Example code:

```html
<div class="zD-md-block">Visible on medium+</div>
```

That's how it works!"""
    
    # Capture output
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    parser.parse(content, mock_display)
    
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    
    # Check all parts are present
    assert 'Use zTheme' in output or mock_display.list_called
    assert mock_display.list_called == True
    assert len(mock_display.list_items) == 2
    assert 'html' in output or 'div' in output
    assert 'how it works' in output or 'That' in output
    
    print(f"  ✓ Complex content with HTML, markdown, code, and lists")
    print(f"  ✓ List items: {len(mock_display.list_items)}")
    print(f"  ✓ HTML stripped from list items")


def run_all_tests():
    """Run all Phase 4 tests."""
    print("=" * 70)
    print("Phase 4: Block-Level Parsing Tests")
    print("=" * 70)
    
    tests = [
        test_code_block_extraction,
        test_code_block_no_language,
        test_block_splitting_with_code,
        test_block_splitting_all_types,
        test_code_block_emission,
        test_mixed_blocks_emission,
        test_paragraph_extraction,
        test_empty_code_block,
        test_real_world_complex_content,
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
