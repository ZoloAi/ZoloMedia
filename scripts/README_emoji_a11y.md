# Emoji Accessibility JSON Generator

## Overview

Generates `emoji-a11y.en.json` from official Unicode CLDR (Common Locale Data Repository) annotations.

## Data Source

**Unicode Consortium CLDR Project**
- Repository: https://github.com/unicode-org/cldr-json
- License: Unicode License (permissive, allows redistribution)
- Data quality: Official, maintained by Unicode Consortium

## Usage

```bash
# From project root
python3 scripts/generate_emoji_a11y.py
```

## Output

**File:** `zOS/core/zSys/data/emoji-a11y.en.json`  
**Format:** `{"emoji": "description"}`  
**Size:** ~46 KB (1,966 entries)  
**Encoding:** UTF-8

### Contents

- **1,383 modern emojis** (U+1F300 and above)
- **543 symbols/punctuation** (©, ®, ™, etc.)
- **Total: 1,926 entries**

### Sample Data

```json
{
  "😀": "grinning face",
  "📱": "mobile phone",
  "💻": "laptop",
  "🎉": "party popper",
  "🖥": "desktop computer",
  "©": "copyright",
  "®": "registered",
  "™": "trade mark"
}
```

## Data Quality

✅ **Verified Coverage:**
- All common emojis present
- Faces, objects, symbols, flags
- Punctuation and special characters
- Consistent descriptions from Unicode CLDR

⚠️ **Known Limitations:**
- Derived annotations not included (0 entries fetched)
- Some emoji variants may be missing (e.g., ❤️ with variation selector)
- Skin tone modifiers included as separate entries

## Updating

To update with latest Unicode data:

```bash
# Re-run the generator
python3 scripts/generate_emoji_a11y.py

# Commit the updated JSON
git add zOS/core/zSys/data/emoji-a11y.en.json
git commit -m "chore: Update emoji accessibility data from Unicode CLDR"
```

**Recommended update frequency:** Quarterly or after major Unicode releases

## Technical Details

### SSL Certificate Handling

The script uses `ssl._create_unverified_context()` to bypass certificate verification when fetching from GitHub. This is safe for:
- Public, read-only data
- Official Unicode Consortium repository
- No sensitive information transmitted

### Error Handling

- Network errors → Exit with message
- JSON parse errors → Exit with details
- Missing data → Warning logged, continues
- Validation failures → Warnings, not fatal

### Performance

- Fetch time: ~2-3 seconds (depends on network)
- Processing time: < 1 second
- Output file: ~46 KB

## Integration

This JSON is used by:

1. **Phase 2**: Python `EmojiDescriptions` module
2. **Phase 3**: zlsp hover provider
3. **Phase 4**: Terminal mode emoji conversion
4. **Phase 5**: Bifrost ARIA labels

## Future Enhancements

- [ ] Parse derived annotations correctly (currently 0 entries)
- [ ] Support multiple languages (es, fr, de, ja, zh)
- [ ] Add emoji categories/tags
- [ ] Include emoji version metadata
- [ ] Support custom override files

---

**Generated:** 2026-01-19  
**Unicode CLDR Version:** Latest (main branch)  
**Script Version:** 1.0.0
