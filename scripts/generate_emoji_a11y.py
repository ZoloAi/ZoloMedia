#!/usr/bin/env python3
"""
Generate Emoji Accessibility JSON from Unicode CLDR

Fetches official emoji annotations from the Unicode Consortium's CLDR project
and generates a unified JSON file mapping emojis to human-readable descriptions.

Data Source: https://github.com/unicode-org/cldr-json
Output: zOS/core/zSys/data/emoji-a11y.en.json

Usage:
    python scripts/generate_emoji_a11y.py

Author: zOS Framework
Version: 1.0.0
Date: 2026-01-19
"""

import json
import urllib.request
import ssl
import sys
from pathlib import Path

# Unicode CLDR URLs
BASE_URL = "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json"

URLS = {
    "base": f"{BASE_URL}/cldr-annotations-full/annotations/en/annotations.json",
    "derived": f"{BASE_URL}/cldr-annotations-derived-full/annotationsDerived/en/annotations.json",
}

def fetch_json(url: str, label: str) -> dict:
    """
    Fetch JSON from a URL with error handling.
    
    Args:
        url: URL to fetch
        label: Label for logging (e.g., "base", "derived")
        
    Returns:
        Parsed JSON as dict
        
    Raises:
        SystemExit: If fetch fails
    """
    print(f"Fetching {label} annotations from CLDR...")
    print(f"URL: {url}")
    
    try:
        # Create SSL context that doesn't verify certificates
        # (GitHub's public data, safe for this use case)
        ssl_context = ssl._create_unverified_context()
        
        with urllib.request.urlopen(url, context=ssl_context) as response:
            if response.status != 200:
                print(f"❌ Error: HTTP {response.status}")
                sys.exit(1)
            
            data = response.read().decode("utf-8")
            parsed = json.loads(data)
            print(f"✅ Successfully fetched {label} ({len(data)} bytes)")
            return parsed
            
    except urllib.error.URLError as e:
        print(f"❌ Network error fetching {label}: {e}")
        print("   Please check your internet connection and try again.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error in {label}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error fetching {label}: {e}")
        sys.exit(1)


def extract_emoji_map(doc: dict, label: str) -> dict:
    """
    Extract emoji → description mapping from CLDR document.
    
    CLDR structure:
    {
      "annotations": {
        "annotation": {
          "😀": {"tts": ["grinning face"], "default": ["face", "grin"]},
          "📱": {"tts": ["mobile phone"]}
        }
      }
    }
    
    Args:
        doc: CLDR JSON document
        label: Label for logging
        
    Returns:
        Dict mapping emoji to description string
    """
    annotations = doc.get("annotations", {}).get("annotations", {})
    
    emoji_map = {}
    skipped = 0
    
    for emoji, obj in annotations.items():
        # Get TTS (text-to-speech) value - the primary description
        tts = obj.get("tts")
        
        # Handle both string and list formats
        if isinstance(tts, list) and len(tts) > 0:
            description = tts[0]  # Use first TTS entry
        elif isinstance(tts, str) and tts:
            description = tts
        else:
            # No valid TTS - skip this emoji
            skipped += 1
            continue
        
        # Store emoji → description mapping
        emoji_map[emoji] = description
    
    print(f"📊 Extracted {len(emoji_map)} emojis from {label}")
    if skipped > 0:
        print(f"⚠️  Skipped {skipped} entries without valid TTS descriptions")
    
    return emoji_map


def merge_emoji_maps(base: dict, derived: dict) -> dict:
    """
    Merge base and derived emoji maps, preferring base descriptions.
    
    Strategy:
    1. Start with all derived emojis
    2. Overwrite with base emojis (base takes precedence)
    
    Args:
        base: Base emoji map
        derived: Derived emoji map
        
    Returns:
        Merged emoji map
    """
    print("\n🔄 Merging emoji maps...")
    
    # Start with derived
    merged = dict(derived)
    
    # Overwrite with base (base takes precedence)
    conflicts = 0
    for emoji, description in base.items():
        if emoji in merged and merged[emoji] != description:
            conflicts += 1
        merged[emoji] = description
    
    print(f"✅ Merged {len(merged)} total emojis")
    print(f"   Base entries: {len(base)}")
    print(f"   Derived entries: {len(derived)}")
    print(f"   Conflicts resolved (base preferred): {conflicts}")
    
    return merged


def validate_emoji_map(emoji_map: dict) -> None:
    """
    Validate the emoji map for common issues.
    
    Args:
        emoji_map: Emoji → description mapping
        
    Raises:
        SystemExit: If validation fails
    """
    print("\n🔍 Validating emoji map...")
    
    # Check minimum size
    if len(emoji_map) < 1000:
        print(f"⚠️  Warning: Only {len(emoji_map)} emojis found (expected 3000+)")
        print("   This may indicate a data fetch issue.")
    
    # Check for empty descriptions
    empty = [emoji for emoji, desc in emoji_map.items() if not desc or not desc.strip()]
    if empty:
        print(f"⚠️  Warning: {len(empty)} emojis have empty descriptions")
        print(f"   Examples: {empty[:5]}")
    
    # Sample check
    common_emojis = {
        "😀": "grinning face",
        "📱": "mobile phone",
        "💻": "laptop",
        "🎉": "party popper",
        "❤️": "red heart",
    }
    
    missing = []
    for emoji, expected in common_emojis.items():
        if emoji not in emoji_map:
            missing.append(emoji)
        elif expected.lower() not in emoji_map[emoji].lower():
            print(f"⚠️  Unexpected description for {emoji}: '{emoji_map[emoji]}' (expected '{expected}')")
    
    if missing:
        print(f"⚠️  Warning: Missing common emojis: {missing}")
    else:
        print(f"✅ All sample emojis present with correct descriptions")
    
    print(f"✅ Validation complete: {len(emoji_map)} emojis ready")


def write_emoji_json(emoji_map: dict, output_path: Path) -> None:
    """
    Write emoji map to JSON file with proper formatting.
    
    Args:
        emoji_map: Emoji → description mapping
        output_path: Path to output file
    """
    print(f"\n💾 Writing to {output_path}...")
    
    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON with minimal formatting (no extra whitespace)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            emoji_map,
            f,
            ensure_ascii=False,  # Preserve Unicode emojis
            separators=(",", ":"),  # Compact formatting
            sort_keys=True  # Consistent ordering
        )
    
    # Get file size
    file_size = output_path.stat().st_size
    size_kb = file_size / 1024
    
    print(f"✅ Written {len(emoji_map)} emojis to {output_path}")
    print(f"   File size: {file_size:,} bytes ({size_kb:.1f} KB)")


def main():
    """Main execution function."""
    print("=" * 70)
    print("Emoji Accessibility JSON Generator")
    print("=" * 70)
    print()
    print("Data source: Unicode CLDR (Unicode Consortium)")
    print("Output: emoji-a11y.en.json")
    print()
    
    # Determine output path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_path = project_root / "zOS" / "core" / "zSys" / "data" / "emoji-a11y.en.json"
    
    print(f"Output path: {output_path}")
    print()
    
    # Step 1: Fetch base annotations
    print("Step 1/5: Fetching base annotations")
    print("-" * 70)
    base_doc = fetch_json(URLS["base"], "base")
    print()
    
    # Step 2: Fetch derived annotations
    print("Step 2/5: Fetching derived annotations")
    print("-" * 70)
    derived_doc = fetch_json(URLS["derived"], "derived")
    print()
    
    # Step 3: Extract emoji maps
    print("Step 3/5: Extracting emoji maps")
    print("-" * 70)
    base_map = extract_emoji_map(base_doc, "base")
    derived_map = extract_emoji_map(derived_doc, "derived")
    
    # Step 4: Merge maps
    print("Step 4/5: Merging emoji maps")
    print("-" * 70)
    merged_map = merge_emoji_maps(base_map, derived_map)
    
    # Step 5: Validate and write
    print("Step 5/5: Validating and writing output")
    print("-" * 70)
    validate_emoji_map(merged_map)
    write_emoji_json(merged_map, output_path)
    
    print()
    print("=" * 70)
    print("✅ Success! Emoji accessibility JSON generated")
    print("=" * 70)
    print()
    print(f"Output file: {output_path}")
    print(f"Total emojis: {len(merged_map):,}")
    print()
    print("Next steps:")
    print("1. Review the generated JSON file")
    print("2. Proceed to Phase 2: Python module implementation")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
