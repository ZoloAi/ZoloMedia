# zTheme Build Process

## Directory Structure ✅ CLEAN

```
zTheme/
├── src/                    # Source CSS files (edit these)
│   ├── css/               # 64 modular CSS files
│   │   ├── zGrid.css     # 12-column grid system
│   │   ├── zButtons.css  # Button styles
│   │   └── ...
│   └── js/
├── dist/                   # Compiled distribution files (auto-generated)
│   ├── ztheme.css         # ⭐ Main compiled CSS (346 KB, 14,161 lines)
│   ├── ztheme.js          # JavaScript utilities
│   ├── icons.svg          # SVG icon sprite
│   └── fonts/             # Font files
├── Manual/                 # Documentation HTML files
├── build.py               # Build script
└── package.json           # Package metadata
```

## Building zTheme

### When to Rebuild
Rebuild when you:
- ✅ Edit any file in `src/css/`
- ✅ Add new CSS modules
- ✅ Update `src/css/zTheme.css` imports

### How to Build

```bash
cd zTheme
python3 build.py
```

**Output:**
- Concatenates all CSS files from `src/css/` in the correct order
- Generates `dist/ztheme.css` (~346 KB)
- Includes all grid system classes (`.zRow`, `.zCol-*`, `.zCol-md-*`, `.zCol-lg-*`, etc.)

### Verified Grid Classes ✅

The compiled `dist/ztheme.css` includes:
- `.zRow` - Flexbox row container
- `.zCol-1` through `.zCol-12` - Mobile-first columns
- `.zCol-sm-*` - Small breakpoint (≥576px)
- `.zCol-md-*` - Medium/Tablet (≥768px)
- `.zCol-lg-*` - Large/Desktop (≥992px)
- `.zCol-xl-*` - Extra large (≥1200px)
- `.zCol-xxl-*` - 2XL (≥1400px)

### Recent Cleanup (2026-01-04)

**Removed:**
- ❌ `zTheme/zTheme/` - Nested duplicate directory (untracked, safe to delete)
- ❌ `zTheme/dist/css/` - Empty subdirectory

**Current State:**
- ✅ Single clean directory structure
- ✅ Grid system fully integrated
- ✅ All source files in `src/`
- ✅ All distribution files in `dist/`

## Integration with zCloud

zCloud loads zTheme from the **local** path:

```yaml
# In zCloud/zEnv.base.yaml:
ZMOUNTS:
  "/ztheme/": "/Users/galnachshon/Projects/zolo-zcli/zTheme/"
```

```html
<!-- In zCloud/templates/base.html -->
<link rel="stylesheet" href="/ztheme/dist/ztheme.css">
```

## Important Notes

1. **NEVER edit `dist/ztheme.css` directly** - Your changes will be overwritten on rebuild
2. **Always edit source files** in `src/css/`
3. **Run `build.py` after editing** source files
4. **The grid system is now included** - No need for custom CSS Grid hacks
5. **346 KB is the expected size** for the full compiled CSS
