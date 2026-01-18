# zTheme Reference for BifrostClient Development

> **Critical**: This document is a reference for AI agents working on BifrostClient.  
> **Rule #1**: NEVER override zTheme classes with custom CSS.  
> **Rule #2**: Use zTheme utilities instead of writing custom styles.  
> **Rule #3**: When in doubt, grep the zTheme repo for existing classes.

---

## Core Philosophy

**zTheme Provides Everything You Need**

- **Reboot**: Consistent cross-browser baseline (reset margins, set fonts, normalize elements)
- **Native Font Stack**: System fonts optimized for each OS
- **Mobile-First**: Responsive by default
- **z-Prefix**: All classes start with `z` (e.g., `.zBtn`, `.zContainer`, `.zFlex-wrap`)
- **Utilities Over Custom CSS**: Use existing classes, don't invent styles

---

## Foundation: CSS Variables (Do NOT hardcode colors!)

zTheme uses CSS custom properties. **NEVER hardcode hex colors** - use the variables:

```css
/* Semantic Colors */
var(--color-primary)    /* Brand color */
var(--color-secondary)  /* Supporting brand */
var(--color-success)    /* Green - positive actions */
var(--color-danger)     /* Red - errors/critical */
var(--color-warning)    /* Yellow - caution */
var(--color-info)       /* Blue - informational */

/* Neutral Colors */
var(--color-body)       /* Default text color */
var(--color-muted)      /* Secondary/subdued text */
var(--color-light)      /* Light gray */
var(--color-dark)       /* Dark gray */
var(--color-white)      /* Pure white */
var(--color-black)      /* Pure black */

/* System */
var(--color-border)     /* Default border color */
```

---

## Spacing Scale (rem-based)

**CRITICAL**: All spacing uses `rem` units for accessibility.

| Class Suffix | Value | Pixels (@ 16px base) |
|--------------|-------|----------------------|
| `0` | `0` | 0px |
| `1` | `0.25rem` | 4px |
| `2` | `0.5rem` | 8px |
| `3` | `1rem` | 16px ⭐ **Base unit** |
| `4` | `1.5rem` | 24px |
| `5` | `3rem` | 48px |

**Examples**:
- `.zm-3` = margin all sides 1rem
- `.zp-2` = padding all sides 0.5rem
- `.zmt-4` = margin-top 1.5rem
- `.zmb-0` = margin-bottom 0 (remove)

---

## Layout Classes

### Containers

```html
<!-- Responsive container (recommended) -->
<div class="zContainer">
  <!-- Max-width adapts at breakpoints: 540px, 720px, 960px, 1140px -->
</div>

<!-- Full-width container -->
<div class="zContainer-fluid">
  <!-- Always 100% width -->
</div>
```

### Flexbox (Most Common)

```html
<!-- Basic flex container -->
<div class="zD-flex">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- Common flex patterns -->
<div class="zD-flex zFlex-wrap zGap-2">...</div>
<div class="zD-flex zFlex-column zGap-3">...</div>
<div class="zD-flex zFlex-between zFlex-items-center">...</div>
<div class="zD-flex zFlex-center zFlex-items-center">...</div>
```

**Flex Utilities**:
- `.zFlex-wrap` - wrap items
- `.zFlex-column` - vertical layout (flex-direction: column)
- `.zFlex-row` - horizontal layout (flex-direction: row)

**Horizontal Alignment (justify-content)**:
- `.zFlex-start` - items at start (default)
- `.zFlex-center` - items centered
- `.zFlex-end` - items at end
- `.zFlex-between` - space-between items
- `.zFlex-around` - space around items
- `.zFlex-evenly` - equal space between items

**Vertical Alignment (align-items)**:
- `.zFlex-items-start` - align to top
- `.zFlex-items-center` - align to center
- `.zFlex-items-end` - align to bottom
- `.zFlex-items-stretch` - stretch to fill (default)
- `.zFlex-items-baseline` - align to baseline

**Spacing**:
- `.zGap-{0-5}` - gap between items (0.25rem to 3rem)

---

## Button Classes

### ✅ CORRECT Usage

```javascript
// Solid buttons
const classes = ['zBtn', 'zBtn-primary'];    // Blue solid
const classes = ['zBtn', 'zBtn-success'];    // Green solid
const classes = ['zBtn', 'zBtn-danger'];     // Red solid

// Outline buttons
const classes = ['zBtn', 'zBtn-outline-primary'];
const classes = ['zBtn', 'zBtn-outline-secondary'];

// Link style
const classes = ['zBtn', 'zBtn-link'];

// Sizes
const classes = ['zBtn', 'zBtn-primary', 'zBtn-sm'];
const classes = ['zBtn', 'zBtn-primary', 'zBtn-lg'];
```

### ❌ WRONG - Do NOT Do This

```javascript
// WRONG: camelCase (zTheme uses kebab-case)
const classes = ['zBtn', 'zBtnPrimary']; // ❌ NO!

// WRONG: custom base class
const classes = ['zoloButton', 'primary']; // ❌ NO!

// WRONG: hardcoded colors
button.style.backgroundColor = '#007bff'; // ❌ NO!
```

### Button Color Classes

| zCLI Color | Solid Class | Outline Class |
|------------|-------------|---------------|
| `primary` | `.zBtn-primary` | `.zBtn-outline-primary` |
| `secondary` | `.zBtn-secondary` | `.zBtn-outline-secondary` |
| `success` | `.zBtn-success` | `.zBtn-outline-success` |
| `danger` | `.zBtn-danger` | `.zBtn-outline-danger` |
| `warning` | `.zBtn-warning` | `.zBtn-outline-warning` |
| `info` | `.zBtn-info` | `.zBtn-outline-info` |
| `light` | `.zBtn-light` | `.zBtn-outline-light` |
| `dark` | `.zBtn-dark` | `.zBtn-outline-dark` |
| `link` | `.zBtn-link` | N/A |

### Button Sizes

| Size | Class |
|------|-------|
| Small | `.zBtn-sm` |
| Default | (no class) |
| Large | `.zBtn-lg` |

---

## Cards & Sections

```html
<!-- Card component -->
<div class="zCard">
  <div class="zCard-body">
    <h2 class="zCard-title">Title</h2>
    <p class="zCard-text">Content here</p>
  </div>
</div>

<!-- Simple section with border -->
<div class="zP-3 zBg-light zBorder zRounded">
  Content here
</div>
```

---

## Typography

```html
<!-- Text colors (semantic) -->
<p class="zText-primary">Primary text</p>
<p class="zText-success">Success message</p>
<p class="zText-danger">Error message</p>
<p class="zText-muted">Secondary text</p>

<!-- Text sizes -->
<p class="zFs-1">Largest</p>
<p class="zFs-2">Large</p>
<p class="zFs-3">Medium</p>
<p class="zFs-4">Small</p>

<!-- Text utilities -->
<p class="zText-center">Centered</p>
<p class="zText-uppercase">UPPERCASE</p>
<p class="zFw-bold">Bold text</p>
<p class="zLead">Lead paragraph (larger)</p>
```

---

## Background & Borders

```html
<!-- Background colors -->
<div class="zBg-primary">...</div>
<div class="zBg-light">...</div>
<div class="zBg-white">...</div>

<!-- Borders -->
<div class="zBorder">All sides</div>
<div class="zBorder-top">Top only</div>
<div class="zBorder-0">Remove border</div>

<!-- Border radius -->
<div class="zRounded">Default radius</div>
<div class="zRounded-circle">Circle</div>
<div class="zRounded-0">No radius</div>
```

---

## Display & Visibility

```html
<!-- Display utilities -->
<div class="zD-none">Hidden</div>
<div class="zD-block">Block</div>
<div class="zD-flex">Flex</div>
<div class="zD-inline">Inline</div>
<div class="zD-inline-block">Inline-block</div>

<!-- Visibility -->
<div class="zVisible">Visible</div>
<div class="zInvisible">Invisible (takes space)</div>
```

---

## Margin & Padding Quick Reference

### Margin

**⚠️ CRITICAL: All spacing classes are LOWERCASE (`zm`, `zp`, NOT `zM`, `zP`)!**

```html
<!-- All sides -->
<div class="zm-3">margin: 1rem</div>

<!-- Specific sides -->
<div class="zmt-2">margin-top: 0.5rem</div>
<div class="zmb-4">margin-bottom: 1.5rem</div>
<div class="zms-3">margin-left: 1rem (RTL: margin-right)</div>
<div class="zme-3">margin-right: 1rem (RTL: margin-left)</div>

<!-- Axes -->
<div class="zmx-2">margin-left & margin-right: 0.5rem</div>
<div class="zmy-4">margin-top & margin-bottom: 1.5rem</div>

<!-- Auto centering -->
<div class="zmx-auto">Centered horizontally</div>

<!-- Negative margins (use sparingly!) -->
<div class="zmt-n2">margin-top: -0.5rem</div>
```

### Padding

```html
<!-- All sides -->
<div class="zp-3">padding: 1rem</div>

<!-- Specific sides -->
<div class="zpt-2">padding-top: 0.5rem</div>
<div class="zpb-4">padding-bottom: 1.5rem</div>
<div class="zps-3">padding-left: 1rem</div>
<div class="zpe-3">padding-right: 1rem</div>

<!-- Axes -->
<div class="zpx-2">padding-left & padding-right: 0.5rem</div>
<div class="zpy-4">padding-top & padding-bottom: 1.5rem</div>
```

---

## Navigation Components

```html
<!-- Nav pills (tabs/buttons) -->
<ul class="zNav zNav-pills">
  <li class="zNav-item">
    <a href="#" class="zNav-link zActive">Active</a>
  </li>
  <li class="zNav-item">
    <a href="#" class="zNav-link">Link</a>
  </li>
</ul>

<!-- Vertical nav -->
<ul class="zNav zNav-pills zFlex-column">
  <li class="zNav-item">
    <a href="#" class="zNav-link">Item</a>
  </li>
</ul>
```

---

## Common Patterns for BifrostClient

### Pattern: Modal/Dialog Content

```html
<div class="zModal-content">
  <div class="zModal-header">
    <h2 class="zModal-title">Title</h2>
  </div>
  <div class="zModal-body zP-4">
    Content here
  </div>
  <div class="zModal-footer zD-flex zGap-2">
    <button class="zBtn zBtn-primary">Confirm</button>
    <button class="zBtn zBtn-outline-secondary">Cancel</button>
  </div>
</div>
```

### Pattern: Form Groups

```html
<div class="zmb-3">
  <label class="zForm-label">Username</label>
  <input type="text" class="zInput" placeholder="Enter username">
</div>
```

### Pattern: Alert Messages

```html
<div class="zAlert zAlert-success">Success message</div>
<div class="zAlert zAlert-danger">Error message</div>
<div class="zAlert zAlert-warning">Warning message</div>
```

### Pattern: List Groups

```html
<ul class="zList-group">
  <li class="zList-group-item">Item 1</li>
  <li class="zList-group-item zActive">Active Item</li>
  <li class="zList-group-item">Item 3</li>
</ul>
```

---

## Testing Guidelines

### ✅ Correct Test HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Test</title>
  
  <!-- ✅ Load zTheme from CDN -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/ZoloAi/zTheme@main/dist/ztheme.css">
  
  <!-- ✅ Minimal page style ONLY -->
  <style>
    body {
      background: #f8f9fa;
      min-height: 100vh;
    }
    /* ONLY non-zTheme component styles here (e.g., syntax highlighting) */
  </style>
</head>
<body>
  <!-- ✅ Use zTheme classes exclusively -->
  <div class="zContainer zmy-5">
    <h1 class="zText-primary">Test Page</h1>
    <div class="zCard">
      <div class="zCard-body">
        <button class="zBtn zBtn-primary">Test Button</button>
      </div>
    </div>
  </div>
</body>
</html>
```

### ❌ What NOT to Do in Tests

```html
<style>
  /* ❌ NEVER override zTheme classes */
  button {
    padding: 10px 20px;
    background: blue;
  }
  
  /* ❌ NEVER create custom button styles */
  .custom-button {
    border: 2px solid red;
  }
  
  /* ❌ NEVER hardcode spacing that conflicts with zTheme */
  .test-section {
    padding: 20px;
    margin: 15px;
  }
</style>
```

---

## Debugging Checklist

When buttons/components don't look right:

1. ✅ **Is zTheme CSS loaded?** (Check browser DevTools Network tab)
2. ✅ **Are you using kebab-case?** (`.zBtn-primary` not `.zBtnPrimary`)
3. ✅ **Is there custom CSS overriding zTheme?** (Check `<style>` tags)
4. ✅ **Are classes applied correctly?** (Check browser DevTools Elements tab)
5. ✅ **Are you using the correct base class?** (`.zBtn` for buttons, not `.button`)

---

## Quick Reference: Class Name Patterns

| Category | Pattern | Examples |
|----------|---------|----------|
| Margin | `.zm{side}-{size}` | `.zmt-3`, `.zmx-2`, `.zm-0` |
| Padding | `.zp{side}-{size}` | `.zpt-3`, `.zpx-2`, `.zp-4` |
| Display | `.zD-{value}` | `.zD-flex`, `.zD-none`, `.zD-block` |
| Flex | `.zFlex-{prop}` | `.zFlex-wrap`, `.zFlex-column`, `.zFlex-between` |
| Text | `.zText-{prop}` | `.zText-primary`, `.zText-center`, `.zText-uppercase` |
| Background | `.zBg-{color}` | `.zBg-primary`, `.zBg-light`, `.zBg-white` |
| Border | `.zBorder-{side}` | `.zBorder`, `.zBorder-top`, `.zBorder-0` |
| Rounded | `.zRounded-{size}` | `.zRounded`, `.zRounded-circle`, `.zRounded-0` |
| Button | `.zBtn-{variant}` | `.zBtn-primary`, `.zBtn-outline-success`, `.zBtn-lg` |

---

## Resources

- **zTheme Repo**: `/Users/galnachshon/Projects/zTheme`
- **zTheme Manual**: `/Users/galnachshon/Projects/zTheme/Manual/`
- **zTheme CSS**: `/Users/galnachshon/Projects/zTheme/dist/ztheme.css`

### Quick Commands

```bash
# Search for zTheme classes
grep -r "\.zBtn" /Users/galnachshon/Projects/zTheme/dist/ztheme.css

# List available button classes
grep "\.zBtn-" /Users/galnachshon/Projects/zTheme/dist/ztheme.css

# Check spacing utilities
grep "\.zm-\|\.zp-" /Users/galnachshon/Projects/zTheme/dist/ztheme.css
```

---

## Final Reminders for AI Agents

1. **Always check zTheme first** before writing custom CSS
2. **Use CSS variables** (`var(--color-primary)`) not hex codes
3. **Respect the spacing scale** (0, 1, 2, 3, 4, 5)
4. **Test in isolation** with minimal custom CSS
5. **When stuck, grep zTheme** to find the right class
6. **Follow the manual examples** - they use ONLY zTheme classes
7. **Keep test files clean** - body background only, no component styles

---

**Last Updated**: Dec 18, 2025  
**For**: BifrostClient Refactoring (zCLI Sprint 2: Button Renderer)

