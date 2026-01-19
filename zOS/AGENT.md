# AGENT.md - .zolo File Construction Patterns

> **Purpose:** Quick reference for building `.zolo` files correctly. Only verified patterns from working files.

## ✅ Verified Files:
- `zCloud/UI/zProducts/zTheme/zUI.zBreakpoints.zolo` (316 lines)
- `zCloud/UI/zProducts/zTheme/zUI.zContainers.zolo` (203 lines)

---

## 1. File Structure Pattern (CRITICAL ⚠️)

### ✅ CORRECT Structure (from verified files)
```zolo
zMeta:
    zNavBar: true
    _zScripts: []

zBreakpoints_Details:
    _zClass: zContainer zmt-5 zmb-2
    Page_Header:
        zH1:
            label: Breakpoints
            color: INFO
            _zClass: zms-1 zmb-0 zFont-kalam
        zText:
            content: Responsive breakpoints for different screen sizes
            _zClass: zLead zText-muted
    
    Core_Concepts_Section:
        _zClass: zCard zmb-5
        Content:
            zH2:
                label: Core Concepts
                color: PRIMARY
                _zClass: zms-2 zFont-kalam
            zMD:
                content: Your markdown here
```

**Key Points:**
- Two root-level keys: `zMeta` and `zBreakpoints_Details` (or `zContainers_Details`, etc.)
- Both at column 0 (same indentation)
- No parent wrapper block

### ❌ WRONG Structures
```zolo
# WRONG 1: Don't use ~zMeta prefix
Root_Block:
    ~zMeta:
        zPageTitle: Title
    Section_One:
        ...

# WRONG 2: Don't nest zMeta inside another block
MyPage:
    zMeta:
        zNavBar: true
    Content:
        ...

# WRONG 3: Don't wrap content in a parent block
zMyPage_Root:
    Section_One:
        ...
```

**Rules:**
- `zMeta` is at ROOT level (column 0), NOT nested
- `zMeta` is NOT prefixed with `~` or any other modifier
- Content blocks (like `Page_Details:`, `Containers_Details:`) are separate root-level keys
- Do NOT wrap everything in a single parent block
- Use `_zClass` for zTheme utility classes
- Use semantic section names (no spaces, use underscores)

---

## 2. Code Block Pattern (CRITICAL)

### ❌ WRONG - Inline Format
```zolo
zMD:
    content: ```css
        .my-class {
          color: red;
        }
        ```
```
**Problem:** Linter will check indentation INSIDE the code block (fails).

### ✅ CORRECT - Multi-line Format
```zolo
zMD:
    content: |
        ```css
        .my-class {
          color: red;
        }
        ```
```
**Why:** The `|` tells parser "everything after is content" - linter skips code blocks.

---

## 3. Multi-line Content Pattern

```zolo
zMD:
    content: **Title here:**

        * List item one
        * List item two

        More paragraph text here
```

**Rules:**
- No trailing whitespace on blank lines
- Blank lines for paragraph breaks
- Lists need blank line before/after

---

## 4. Emoji Pattern (Accessibility)

### ✅ Use Unicode Escapes
```zolo
zMD:
    content: \U0001F4D6 Documentation guide
```
**Converts to:**
- Terminal: `[open book] Documentation guide`
- Bifrost: `📖 Documentation guide` (with aria-label)

### Common Escapes
- `\U0001F4F1` = 📱 mobile phone
- `\U0001F4BB` = 💻 laptop
- `\U0001F4D6` = 📖 open book
- `\U0001F4A1` = 💡 light bulb
- `\U0001F527` = 🔧 wrench
- `\U0001F3AF` = 🎯 bullseye

---

## 5. Terminal Color Styling Pattern

```zolo
zMD:
    content: <span class="zText-error">**Important text**</span> and normal text
```

**Available Colors:**
- `zText-error` = Red (errors, warnings)
- `zText-info` = Blue (info, links)
- `zText-success` = Green (success, positive)
- `zText-warning` = Yellow (caution, attention)
- `zText-muted` = Gray (secondary info)

**Combine with Markdown:**
- `<span class="zText-error">**Bold Red**</span>` ✅
- `<span class="zText-error">`code block`</span>` ❌ (code overrides color, use `**` instead)

---

## 6. Card Section Pattern

```zolo
My_Section:
    _zClass: zCard zmb-5
    Content:
        zH2:
            label: Section Title
            color: INFO
            _zClass: zms-2 zFont-kalam
        zMD:
            content: Your content here
```

**Pattern:**
- Outer block: `_zClass: zCard zmb-5` (card with bottom margin)
- Inner `Content:` wrapper
- Header with `zms-2` (margin start) and `zFont-kalam` (font)

---

## 7. Callout Pattern

```zolo
My_Callout:
    _zClass: zCallout zCallout-info zmy-4
    zMD:
        content: **\U0001F4A1 Pro tip:**
            Your callout content here
```

**Callout Types:**
- `zCallout-info` = Blue (information)
- `zCallout-success` = Green (success)
- `zCallout-warning` = Yellow (warning)
- `zCallout-danger` = Red (error/danger)
- `zCallout-secondary` = Gray (neutral)

---

## 8. Responsive Example Pattern

```zolo
Demo_Section:
    _zClass: zD-flex zFlex-column zGap-3
    
    Always_Visible:
        _zClass: zCallout zCallout-secondary
        zMD:
            content: Always visible content
    
    Mobile_Only:
        _zClass: zCallout zCallout-danger zD-block zD-md-none
        zMD:
            content: Mobile only (< 768px)
    
    Desktop_Only:
        _zClass: zCallout zCallout-success zD-none zD-lg-block
        zMD:
            content: Desktop only (≥ 992px)
```

**Pattern:**
- Parent: `zD-flex zFlex-column zGap-3` (vertical stack with gaps)
- Mobile-only: `zD-block zD-md-none` (show → hide at 768px)
- Desktop-only: `zD-none zD-lg-block` (hide → show at 992px)

---

## 8a. Responsive Flex Layout Pattern

For layouts that stack on mobile, go horizontal on desktop:

```zolo
Visual_Demo:
    _zClass: zD-flex zFlex-column zFlex-md-row zGap-2 zFlex-items-stretch
    Box_One:
        _zClass: zBg-info zRounded zD-flex zFlex-items-center zFlex-center
        _zStyle: flex: 1; height: 50px;
        zText:
            content: First Box
    Box_Two:
        _zClass: zBg-success zRounded zD-flex zFlex-items-center zFlex-center
        _zStyle: flex: 2; height: 70px;
        zText:
            content: Second Box (2x bigger)
```

**Pattern:**
- `zFlex-column` = Stack vertically on mobile (default)
- `zFlex-md-row` = Side by side at ≥768px
- `zFlex-items-stretch` = Items stretch to same height
- `flex: 1` vs `flex: 2` = Control relative sizing (1:2 ratio)
- Use inline `_zStyle: flex: N;` for custom ratios (zTheme only has `zFlex-grow-0` and `zFlex-grow-1`)

**Result:**
- **Mobile (< 768px):** Boxes stack vertically, full width
- **Desktop (≥ 768px):** Boxes side by side with 1:2 ratio (second box is 2x bigger)

---

## 9. Table Pattern

```zolo
zTable:
    headers: [Name, Value, Description]
    rows:
        - [Extra small, xs, "< 576px"]
        - [Small, sm, ">= 576px"]
        - [Medium, md, ">= 768px"]
```

**Rules:**
- Use `headers:` for column names
- Use `rows:` for data (array of arrays)
- Quote strings with special chars

---

## 10. List Pattern

```zolo
zUL:
    items:
        - First item
        - Second item
        - Third item
```

**Simple and direct.**

---

## 11. Code Example Section Pattern

```zolo
Code_Example_Section:
    _zClass: zCard zmb-5
    Content:
        zH2:
            label: Code Examples
            color: INFO
            _zClass: zms-2 zFont-kalam
        
        zMD:
            content: Intro text explaining the examples:
        
        Zolo_Example:
            zH3:
                label: zolo Syntax
                color: INFO
                _zClass: zms-4
            zMD:
                content:
                    ```zolo
                    Your_Code_Here:
                        _zClass: zD-flex zGap-3
                    ```
        
        HTML_Example:
            zH3:
                label: HTML Output
                color: WARNING
                _zClass: zms-4
            zMD:
                content:
                    ```html
                    <div class="zD-flex zGap-3">
                      <!-- Your HTML here -->
                    </div>
                    ```
```

**Pattern for side-by-side examples:**
- Show `.zolo` syntax first
- Show equivalent HTML second
- Use `zH3` with `_zClass: zms-4` for sub-headers

---

## 12. Terminal Suppression Pattern

```zolo
_Live_Demo_Section:
    _zClass: zCard zmb-5
    Content:
        # Content here
```

**Prefix with `_` to suppress in Terminal, show in Bifrost.**

**Do NOT use `_` for:**
- `_zClass` (metadata)
- `_zStyle` (metadata)
- `_zId` (metadata)

---

## 13. Visual Demo Pattern (Bifrost-Only)

For visual elements that don't make sense in Terminal (charts, bars, graphics):

```zolo
Responsive_Container:
    _zClass: zCallout zCallout-info
    Title:
        zMD:
            content: **1. `.zContainer`** - Responsive (recommended)
    Subtitle:
        zText:
            content: Max-width changes at each breakpoint
            _zClass: zmt-2
    
    _Visual_Progression:
        _zClass: zD-flex zGap-2 zFlex-items-end zmt-3
        _Box_540:
            _zClass: zBg-info zRounded zD-flex zFlex-items-center zFlex-center zText-white
            _zStyle: width: 40%; height: 40px; font-size: 0.75rem;
            zText:
                content: 540px
        _Box_720:
            _zClass: zBg-info zRounded zD-flex zFlex-items-center zFlex-center zText-white
            _zStyle: width: 55%; height: 50px; font-size: 0.75rem;
            zText:
                content: 720px
    
    _Visual_Caption:
        zText:
            content: \U0001F4F1 sm \u2192 \U0001F4BB md \u2192 \U0001F5A5 lg (adapts to screen)
            _zClass: zmt-3 zSmall zText-muted
    
    Terminal_List:
        zMD:
            content: |
                Breakpoint widths:
                
                * <span class="zText-info">**540px**</span> at sm (≥576px) \U0001F4F1
                * <span class="zText-info">**720px**</span> at md (≥768px) \U0001F4BB
```

**Pattern:**
- Prefix visual demo blocks with `_` (e.g., `_Visual_Progression`, `_Box_540`)
- Provide Terminal-friendly alternative (e.g., `Terminal_List` with bullets)
- Visual demos render in Bifrost, text alternatives show in Terminal
- Use `_zStyle` for inline CSS when zTheme classes aren't enough

**Result:**
- **Terminal:** Clean bulleted list with emoji descriptions
- **Bifrost:** Visual chart/bars/graphics with full CSS styling

---

## Common Linter Fixes

1. **Code blocks:** Use `content: |` not `content:`
2. **Trailing whitespace:** Remove all trailing spaces
3. **Indentation:** Always 4-space multiples
4. **Blank lines:** No spaces on empty lines

---

## zTheme Utility Classes (Quick Ref)

### Spacing
- `zmy-3` = margin Y-axis (top + bottom)
- `zmb-5` = margin bottom
- `zms-2` = margin start (left in LTR)
- `zGap-3` = gap between flex/grid children

### Display
- `zD-block` = display: block
- `zD-none` = display: none
- `zD-flex` = display: flex
- `zD-grid` = display: grid

### Flexbox (⚠️ Note: ALL use `zFlex-` prefix)
- `zFlex-column` = flex-direction: column
- `zFlex-row` = flex-direction: row
- `zFlex-center` = justify-content: center
- `zFlex-between` = justify-content: space-between
- `zFlex-items-start` = align-items: flex-start
- `zFlex-items-center` = align-items: center
- `zFlex-items-end` = align-items: flex-end
- `zFlex-items-stretch` = align-items: stretch
- `zFlex-grow-1` = flex-grow: 1 (fills available space)
- **Responsive:** `zFlex-md-row`, `zFlex-lg-column`, etc.
- ❌ **WRONG:** `zAlign-items-*`, `zJustify-content-*` (don't exist!)

### Breakpoints
- `zD-md-block` = show at ≥768px
- `zD-lg-none` = hide at ≥992px
- `zD-md-none` = hide at ≥768px

### Typography
- `zFont-kalam` = Kalam font family
- `zText-error` = error color (red)
- `zText-info` = info color (blue)
- `zText-success` = success color (green)
- `zText-warning` = warning color (yellow)
- `zText-muted` = muted color (gray)

---

## Next Steps

As more `.zolo` files are verified, add patterns here:
- Forms (when `zUI.zForms.zolo` is built)
- Buttons (when `zUI.zButtons.zolo` is built)
- Modals (when `zUI.zModals.zolo` is built)

**Keep it simple. Only add VERIFIED patterns.**
