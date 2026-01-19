# Bifrost `.zolo` Syntax Highlighting

**Status:** ✅ Implemented  
**Date:** 2026-01-19

## Overview

Implemented Prism.js syntax highlighting for `.zolo` code blocks in Bifrost (GUI mode), matching the Terminal implementation with the same **dynamic generator pattern**.

## Architecture

### Dual-Mode Syntax Highlighting
```
Terminal Mode:  zlsp → generate_pygments_lexer.py → zolo_lexer.py → ANSI 16 colors
Bifrost Mode:   zlsp → generate_prism_zolo.py → prism-zolo.js → Prism.js themes
```

Both modes share the same **SSOT (Single Source of Truth): zlsp token patterns**.

## Implementation

### 1. Generator Script
**File:** `zOS/bifrost/generators/generate_prism_zolo.py`

- **Purpose:** Dynamically generates `prism-zolo.js` from zlsp patterns
- **Run:** `python3 generate_prism_zolo.py` (whenever zlsp patterns change)
- **Output:** `prism-zolo.js` with Prism.js language definition

**Key Features:**
- Extracts token patterns from zlsp (ROOT_KEY, UI_ELEMENT_KEY, etc.)
- Maps zlsp TokenType → Prism.js token types
- Converts zlsp regexes → Prism.js regex patterns
- Auto-registered with Prism.js

### 2. Generated Language File
**Files:** 
- `zOS/bifrost/src/syntax/prism-zolo.js` (source)
- `zCloud/static/js/prism-zolo.js` (served)

**Token Mapping:**
```javascript
zlsp TokenType          → Prism Token         → Theme Color
─────────────────────────────────────────────────────────────────
ROOT_KEY                → 'class-name'        → Pink/Magenta
UI_ELEMENT_KEY (z*)     → 'function'          → Blue/Cyan
NESTED_KEY              → 'property'          → Green
METADATA (_z*)          → 'keyword'           → Yellow/Orange
ESCAPE_SEQUENCE         → 'string' + 'escape' → Bright
COMMENT                 → 'comment'           → Dim gray
TYPE_HINT               → 'type'              → Italic
NUMBER                  → 'number'            → Orange
BOOLEAN                 → 'boolean'           → Cyan
NULL                    → 'null'              → Purple
STRING                  → 'string'            → Default
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

### 3. Auto-Loading Integration
**File:** `zOS/bifrost/src/bifrost_client.js`

**Changes:**
- Added `_loadPrismZolo()` method to load custom `.zolo` language
- Integrated into Prism.js loading chain (loads after core + standard languages)
- Auto-loads from `/static/js/prism-zolo.js`

```javascript
// In bifrost_client.js
_loadPrismZolo() {
    const zoloLangPath = '/static/js/prism-zolo.js';
    
    // Check if already loaded
    if (document.querySelector(`script[src="${zoloLangPath}"]`)) {
        this.logger.log('✅ Prism .zolo language already loaded');
        return;
    }
    
    const script = document.createElement('script');
    script.src = zoloLangPath;
    script.onload = () => {
        this.logger.log('✅ Prism .zolo language loaded (generated from zlsp patterns)');
    };
    document.head.appendChild(script);
}
```

### 4. Text Renderer (Already Configured)
**File:** `zOS/bifrost/src/rendering/text_renderer.js`

No changes needed! The text renderer already applies Prism highlighting to all code blocks:
```javascript
// Existing code in text_renderer.js
if (window.Prism) {
    p.querySelectorAll('pre code[class*="language-"]').forEach((codeBlock) => {
        Prism.highlightElement(codeBlock);
    });
}
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
```
````

### HTML Output

Bifrost renders it as:
```html
<pre><code class="language-zolo">
Visibility_Examples:
    _zClass: zD-flex zFlex-column zGap-3
    ...
</code></pre>
```

Prism.js automatically highlights when:
1. Page loads → `bifrost_client.js` loads Prism core
2. Prism core loads → `_loadPrismZolo()` loads custom `.zolo` language
3. Content renders → `text_renderer.js` applies highlighting

## Testing

**Bifrost Mode:**
1. Start zCloud server
2. Open http://localhost:5000
3. Navigate to zUI.zBreakpoints.zolo
4. Scroll to "Code Examples" section
5. Verify `.zolo` code blocks have syntax highlighting

**Expected Colors (Prism Tomorrow theme):**
- **Root keys** (`Visibility_Examples:`) → Pink/Magenta
- **Display events** (`zMD:`) → Blue/Cyan
- **Metadata** (`_zClass:`) → Yellow/Orange
- **Properties** (`content:`) → Green
- **Comments** (`# text`) → Dim gray

## Maintenance

### Updating the Language

When zlsp token patterns change:

1. **Update Generator** (if needed):
   ```bash
   vim zOS/bifrost/generators/generate_prism_zolo.py
   ```

2. **Regenerate Language**:
   ```bash
   cd zOS/bifrost/generators
   python3 generate_prism_zolo.py
   ```

3. **Copy to Static**:
   ```bash
   cp zOS/bifrost/src/syntax/prism-zolo.js zCloud/static/js/prism-zolo.js
   ```

4. **Restart Server**:
   ```bash
   cd zCloud
   zolo server restart
   ```

5. **Test in Browser**: Hard refresh (Cmd+Shift+R) to clear cached JS

### Adding New Token Types

To add new zlsp token types to the Prism language:

1. Edit `generate_prism_zolo.py` → `generate_prism_language()`
2. Add regex pattern matching zlsp parser
3. Map to appropriate Prism token type
4. Regenerate language file
5. Copy to static directory

**Example:**
```python
# In generate_prism_language():
# New pattern for custom tokens
'custom-token': {
    pattern: /\b~CustomToken\b/,
    alias: 'builtin',  # Purple/Magenta
},
```

## Benefits

### ✅ Consistency
- **Same patterns** across Terminal, Bifrost, and IDE (VSCode)
- **SSOT:** zlsp defines tokens → Generators create highlighters
- **DRY:** No manual duplication of regex patterns

### ✅ Maintainability
- **Generator pattern:** Update zlsp → Regenerate → Automatic propagation
- **Auto-loading:** No manual script tags in HTML templates
- **Clear ownership:** Each file has auto-generated header with instructions

### ✅ Professional Output
- **Syntax-aware rendering** in both Terminal (ANSI 16) and GUI (Prism.js)
- **Theme compatibility:** Works with any Prism theme (Tomorrow, Monokai, etc.)
- **Accessible:** Clear visual hierarchy for different `.zolo` constructs

## Comparison: Terminal vs Bifrost

| Feature | Terminal Mode | Bifrost Mode |
|---------|--------------|--------------|
| **Technology** | Python + ANSI codes | JavaScript + Prism.js |
| **Colors** | ANSI 16 (16 colors) | Theme-based (24-bit RGB) |
| **Performance** | Instant (regex) | Instant (Prism.js) |
| **Generator** | `generate_pygments_lexer.py` | `generate_prism_zolo.py` |
| **Output** | `zolo_lexer.py` | `prism-zolo.js` |
| **Loading** | Python import | Auto-load via `<script>` |
| **Themes** | ANSI 16 palette | Prism themes (Tomorrow, Monokai, etc.) |

Both share the **same zlsp token patterns** as their source of truth!

## Files Created/Modified

### Created
- ✅ `zOS/bifrost/generators/generate_prism_zolo.py` (Generator)
- ✅ `zOS/bifrost/src/syntax/prism-zolo.js` (Source - AUTO-GENERATED)
- ✅ `zCloud/static/js/prism-zolo.js` (Served - AUTO-GENERATED)
- ✅ `BIFROST_ZOLO_SYNTAX.md` (This file)

### Modified
- ✅ `zOS/bifrost/src/bifrost_client.js`
  - Added `_loadPrismZolo()` method
  - Integrated into Prism.js loading chain

## Dependencies

Already installed:
- ✅ Prism.js core (auto-loaded by `bifrost_client.js`)
- ✅ Prism Tomorrow theme (auto-loaded)
- ✅ Standard Prism languages (markup, css, javascript, python, yaml)

New:
- ✅ `prism-zolo.js` (auto-loaded custom language)

## Notes

- **Theme Compatibility:** The `.zolo` language uses standard Prism token types (`class-name`, `function`, `keyword`, etc.), so it works with any Prism theme
- **No Breaking Changes:** Existing code blocks continue to work normally
- **Fallback:** If `prism-zolo.js` fails to load, code blocks render without highlighting (graceful degradation)
- **SSOT Philosophy:** zlsp is the single source of truth for all `.zolo` syntax definitions

---

**Next Steps:** Test in browser with zUI.zBreakpoints.zolo to verify highlighting! 🎨
