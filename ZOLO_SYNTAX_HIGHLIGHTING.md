# .zolo Code Escape Syntax Highlighting

**Status:** ✅ Implemented (Terminal Mode)  
**Date:** 2026-01-19

## Overview

Implemented dynamic syntax highlighting for `.zolo` code blocks in Terminal mode using Pygments. This system uses a **generator pattern** (matching your VSCode extension build) where the lexer is dynamically generated from zlsp token patterns.

## Architecture

### Single Source of Truth (SSOT)
```
zlsp token patterns → Generator → Pygments Lexer → Terminal highlighting
```

This matches your existing pattern:
```
zlsp theme → vscode.py → TextMate grammar → VSCode highlighting
```

## Implementation

### 1. Generator Script
**File:** `zOS/core/zSys/syntax/generate_pygments_lexer.py`

- **Purpose:** Dynamically generates `zolo_lexer.py` from zlsp patterns
- **Run:** `python3 generate_pygments_lexer.py` (whenever zlsp patterns change)
- **Output:** `zolo_lexer.py` with auto-generated header and metadata

**Key Features:**
- Extracts token patterns from zlsp (ROOT_KEY, UI_ELEMENT_KEY, NESTED_KEY, etc.)
- Maps zlsp TokenType → Pygments Token classes
- Converts zlsp regexes → Pygments regex patterns
- Auto-registration with Pygments

### 2. Generated Lexer
**File:** `zOS/core/zSys/syntax/zolo_lexer.py` (AUTO-GENERATED)

**Token Mapping:**
```python
zlsp TokenType          → Pygments Token      → Terminal Color
─────────────────────────────────────────────────────────────────
ROOT_KEY                → Name.Class          → Green (bold)
UI_ELEMENT_KEY (z*)     → Name.Function       → Cyan/Blue (bright)
NESTED_KEY              → Name.Attribute      → Yellow
ESCAPE_SEQUENCE         → String.Escape       → Bright/distinct
COMMENT                 → Comment.Single      → Dim gray
TYPE_HINT               → Generic.Emph        → Italic
NUMBER                  → Number              → Magenta
STRING                  → String              → Default
BOOLEAN                 → Keyword.Constant    → Cyan
```

**Supported Patterns:**
- ✅ Root keys: `Page_Header:`, `Core_Concepts_Section:`
- ✅ Display events: `zH1:`, `zText:`, `zMD:`
- ✅ Metadata: `_zClass:`, `_zStyle:`, `_zId:`
- ✅ Properties: `label:`, `content:`, `color:`
- ✅ Modifiers: `*`, `!`, `^`, `~`
- ✅ Type hints: `(int)`, `(str)`, `(bool)`
- ✅ Escape sequences: `\uXXXX`, `\UXXXXXXXX`, `\n`, `\t`
- ✅ Comments: `# lines`
- ✅ Values: strings, numbers, booleans, arrays

### 3. Integration
**File:** `zOS/core/L2_Core/c_zDisplay/zDisplay_modules/c_basic/markdown_terminal_parser.py`

**Changes:**
```python
# Special handling for .zolo files - use custom lexer
if language and language.lower() == 'zolo':
    from zOS.core.zSys.syntax import ZoloLexer
    lexer = ZoloLexer(stripall=True)
else:
    lexer = get_lexer_by_name(language or 'text', stripall=True)
```

## Usage

### In .zolo Files

Use triple-backtick code blocks with `zolo` language tag:

````markdown
Here's a .zolo example:

```zolo
Visibility_Examples:
    _zClass: zD-flex zFlex-column zGap-3
    Always_Visible:
        _zClass: zCallout zCallout-secondary
        zMD:
            content: **Always Visible:** This box stays on all screen sizes
    Mobile_Only:
        _zClass: zCallout zCallout-danger zD-block zD-md-none
        zMD:
            content: **\U0001F4F1 Mobile Only:** Visible on screens <768px
```
````

### Testing

**Terminal Mode:**
```bash
cd zCloud
zolo shell --file UI/zProducts/zTheme/zUI.zBreakpoints.zolo
# Navigate to "Code Example" section to see highlighted .zolo syntax
```

**Direct Test:**
```bash
cd zOS/core/zSys/syntax
python3 -c "
from zolo_lexer import ZoloLexer
from pygments import highlight
from pygments.formatters import TerminalFormatter

code = '''Page_Header:
    zH1:
        label: Hello World
        _zClass: zText-primary
'''

lexer = ZoloLexer()
print(highlight(code, lexer, TerminalFormatter()))
"
```

## Maintenance

### Updating the Lexer

When zlsp token patterns change:

1. **Update Generator** (if needed):
   ```bash
   vim zOS/core/zSys/syntax/generate_pygments_lexer.py
   ```

2. **Regenerate Lexer**:
   ```bash
   cd zOS/core/zSys/syntax
   python3 generate_pygments_lexer.py
   ```

3. **Verify Output**:
   ```bash
   # Check that zolo_lexer.py is updated
   head -20 zOS/core/zSys/syntax/zolo_lexer.py
   # Should show: "Generated: [current date/time]"
   ```

4. **Test**:
   ```bash
   # Run test file or full zolo shell
   ```

### Adding New Token Types

To add new zlsp token types to the lexer:

1. Edit `generate_pygments_lexer.py` → `generate_lexer_class()`
2. Add regex pattern matching zlsp parser
3. Map to appropriate Pygments Token class
4. Regenerate lexer

**Example:**
```python
# In generate_lexer_class():
# New pattern for custom tokens
(r'(\\s*)'                      # Indentation
 r'(~CustomToken)'              # Your pattern
 r'(:)',                        # Colon
 bygroups(Whitespace, Keyword.Reserved, Punctuation)),
```

## Benefits

### ✅ Maintainability
- **SSOT:** zlsp defines patterns, generator creates lexers
- **DRY:** No manual duplication of token patterns
- **Consistency:** Same patterns in LSP, VSCode, Terminal, and Bifrost

### ✅ Streamlined Workflow
- Update zlsp → Run generator → Automatic propagation
- Matches your existing VSCode extension build pattern
- Easy to extend with new token types

### ✅ Professional Output
- Syntax-aware Terminal rendering
- Proper color-coding for different .zolo constructs
- Clear visual hierarchy (keys vs values vs metadata)

## Future Enhancements

### Bifrost Integration (Next Step)
**File:** `zOS/bifrost/src/rendering/text_renderer.js`

Prism.js is already auto-loaded. Need to:
1. Create custom Prism.js language definition for `.zolo`
2. Add to Bifrost's Prism language loader
3. Test in GUI mode

### Additional Lexers
Following the same generator pattern:
- **Vim:** Generate `zolo.vim` syntax file
- **Sublime:** Generate `zolo.sublime-syntax`
- **Emacs:** Generate `zolo-mode.el`

## Files Modified/Created

### Created
- ✅ `zOS/core/zSys/syntax/__init__.py`
- ✅ `zOS/core/zSys/syntax/generate_pygments_lexer.py` (Generator)
- ✅ `zOS/core/zSys/syntax/zolo_lexer.py` (AUTO-GENERATED)
- ✅ `ZOLO_SYNTAX_HIGHLIGHTING.md` (This file)

### Modified
- ✅ `zOS/core/L2_Core/c_zDisplay/zDisplay_modules/c_basic/markdown_terminal_parser.py`
  - Added `.zolo` lexer detection
  - Integrated ZoloLexer for Terminal code blocks
- ✅ `zOS/pyproject.toml`
  - Added `Pygments>=2.17` dependency

## Dependencies

```toml
# In zOS/pyproject.toml
dependencies = [
    "Pygments>=2.17",  # Terminal syntax highlighting
    # ... other deps
]
```

## Notes

- **Raw Strings:** Generator uses `r'''` for regex patterns to avoid escaping issues
- **Auto-Registration:** Lexer registers itself with Pygments on import
- **Fallback:** If Pygments unavailable, falls back to mono-color cyan

---

**Next Step:** Bifrost Prism.js integration for GUI syntax highlighting.
