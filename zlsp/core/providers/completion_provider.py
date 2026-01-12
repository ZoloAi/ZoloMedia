"""
Completion Provider for .zolo Language Server

Provides smart autocomplete for:
- Type hints when typing inside ()
- Common values (true, false, null)
- zKernel shorthands (zImage, zURL, etc.)
"""

from typing import List
from lsprotocol import types as lsp_types


# Type hint completions
TYPE_HINT_COMPLETIONS = [
    {
        "label": "int",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Integer number",
        "documentation": "Convert value to integer.\n\nExample: `port(int): 8080`",
        "insert_text": "int"
    },
    {
        "label": "float",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Floating point number",
        "documentation": "Convert value to float.\n\nExample: `pi(float): 3.14159`",
        "insert_text": "float"
    },
    {
        "label": "bool",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Boolean",
        "documentation": "Convert value to boolean.\n\nExample: `enabled(bool): true`",
        "insert_text": "bool"
    },
    {
        "label": "str",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "String",
        "documentation": "Explicitly mark as string. Enables multi-line content.\n\nExample: `description(str): Long text...`",
        "insert_text": "str"
    },
    {
        "label": "list",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "List/Array",
        "documentation": "Ensure value is a list.\n\nExample: `items(list): [1, 2, 3]`",
        "insert_text": "list"
    },
    {
        "label": "dict",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Dictionary/Object",
        "documentation": "Ensure value is a dictionary.\n\nExample: `config(dict): {key: value}`",
        "insert_text": "dict"
    },
    {
        "label": "null",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Null value",
        "documentation": "Set value to null/None.\n\nExample: `optional(null):`",
        "insert_text": "null"
    },
    {
        "label": "raw",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Raw string",
        "documentation": "String without escape processing.\n\nExample: `regex(raw): \\d+`",
        "insert_text": "raw"
    },
    {
        "label": "date",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Date string",
        "documentation": "Date value (semantic).\n\nExample: `created(date): 2024-01-06`",
        "insert_text": "date"
    },
    {
        "label": "time",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Time string",
        "documentation": "Time value (semantic).\n\nExample: `starts(time): 14:30:00`",
        "insert_text": "time"
    },
    {
        "label": "url",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "URL string",
        "documentation": "URL value (semantic).\n\nExample: `homepage(url): https://example.com`",
        "insert_text": "url"
    },
    {
        "label": "path",
        "kind": lsp_types.CompletionItemKind.TypeParameter,
        "detail": "Path string",
        "documentation": "File path (semantic).\n\nExample: `config(path): /etc/app/config.zolo`",
        "insert_text": "path"
    },
]


# Value completions (after colon)
VALUE_COMPLETIONS = [
    {
        "label": "true",
        "kind": lsp_types.CompletionItemKind.Value,
        "detail": "Boolean true",
        "documentation": "Use with `(bool)` type hint for boolean.\n\nExample: `enabled(bool): true`",
        "insert_text": "true"
    },
    {
        "label": "false",
        "kind": lsp_types.CompletionItemKind.Value,
        "detail": "Boolean false",
        "documentation": "Use with `(bool)` type hint for boolean.\n\nExample: `enabled(bool): false`",
        "insert_text": "false"
    },
    {
        "label": "null",
        "kind": lsp_types.CompletionItemKind.Value,
        "detail": "Null value",
        "documentation": "Represents absence of value.\n\nExample: `optional: null`",
        "insert_text": "null"
    },
]


# zKernel shorthand completions
ZCLI_SHORTHAND_COMPLETIONS = [
    {
        "label": "zImage",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Image shorthand",
        "documentation": "Display an image in zKernel.\n\nExample: `zImage: /path/to/image.png`",
        "insert_text": "zImage: "
    },
    {
        "label": "zURL",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "URL/Link shorthand",
        "documentation": "Single URL link.\n\nExample: `zURL: https://example.com`",
        "insert_text": "zURL: "
    },
    {
        "label": "zURLs",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Multiple URLs",
        "documentation": "List of URL links.\n\nExample: `zURLs: [url1, url2]`",
        "insert_text": "zURLs: "
    },
    {
        "label": "zText",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Text shorthand",
        "documentation": "Display text in zKernel.\n\nExample: `zText: Hello World`",
        "insert_text": "zText: "
    },
    {
        "label": "zTexts",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Multiple texts",
        "documentation": "List of text items.\n\nExample: `zTexts: [text1, text2]`",
        "insert_text": "zTexts: "
    },
    {
        "label": "zH1",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Heading 1",
        "documentation": "Large heading.\n\nExample: `zH1: Main Title`",
        "insert_text": "zH1: "
    },
    {
        "label": "zH2",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Heading 2",
        "documentation": "Medium heading.\n\nExample: `zH2: Section Title`",
        "insert_text": "zH2: "
    },
    {
        "label": "zH3",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Heading 3",
        "documentation": "Small heading.\n\nExample: `zH3: Subsection Title`",
        "insert_text": "zH3: "
    },
    {
        "label": "zUL",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Unordered list",
        "documentation": "Bullet list.\n\nExample: `zUL: [item1, item2]`",
        "insert_text": "zUL: "
    },
    {
        "label": "zOL",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Ordered list",
        "documentation": "Numbered list.\n\nExample: `zOL: [item1, item2]`",
        "insert_text": "zOL: "
    },
    {
        "label": "zMD",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Markdown",
        "documentation": "Markdown content.\n\nExample: `zMD: # Markdown text`",
        "insert_text": "zMD: "
    },
    {
        "label": "zTable",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Table",
        "documentation": "Data table.\n\nExample: `zTable: [[row1], [row2]]`",
        "insert_text": "zTable: "
    },
    {
        "label": "zNavBar",
        "kind": lsp_types.CompletionItemKind.Class,
        "detail": "Navigation bar",
        "documentation": "Enable/disable navbar.\n\nExample: `zNavBar: false`",
        "insert_text": "zNavBar: "
    },
]


def get_completions(content: str, line: int, character: int) -> List[lsp_types.CompletionItem]:
    """
    Get completion items at a specific position.
    
    Detects context and provides appropriate completions:
    1. Inside () → type hint completions
    2. After : → value completions
    3. Start of line with 'z' → zKernel shorthand completions
    
    Args:
        content: Full .zolo file content
        line: Line number (0-based)
        character: Character position (0-based)
    
    Returns:
        List of completion items
    """
    lines = content.splitlines()
    if line >= len(lines):
        return []
    
    line_content = lines[line]
    prefix = line_content[:character]
    
    # Context 1: Inside type hint parentheses
    # Pattern: keyName( or keyName(str
    if '(' in prefix and not ')' in prefix.split('(')[-1]:
        return _create_completion_items(TYPE_HINT_COMPLETIONS)
    
    # Context 2: After colon (value position)
    # Pattern: key: |
    if ':' in prefix and not prefix.rstrip().endswith(':'):
        # Already have some text after colon, offer values
        after_colon = prefix.split(':')[-1].strip()
        if len(after_colon) < 5:  # Only offer for short prefixes
            return _create_completion_items(VALUE_COMPLETIONS)
    
    # Context 3: Start of line with 'z'
    # Pattern: ^\s*z[A-Z]?
    stripped = prefix.lstrip()
    if stripped.startswith('z') and len(stripped) <= 10:
        # Filter to matching shorthands
        matching = [
            item for item in ZCLI_SHORTHAND_COMPLETIONS
            if item["label"].lower().startswith(stripped.lower())
        ]
        if matching:
            return _create_completion_items(matching)
    
    # Context 4: Empty line or start of key
    # Offer zKernel shorthands
    if not stripped or len(stripped) == 1:
        return _create_completion_items(ZCLI_SHORTHAND_COMPLETIONS)
    
    return []


def _create_completion_items(completion_specs: List[dict]) -> List[lsp_types.CompletionItem]:
    """Convert completion specifications to LSP CompletionItem objects."""
    items = []
    
    for spec in completion_specs:
        item = lsp_types.CompletionItem(
            label=spec["label"],
            kind=spec.get("kind", lsp_types.CompletionItemKind.Text),
            detail=spec.get("detail"),
            documentation=lsp_types.MarkupContent(
                kind=lsp_types.MarkupKind.Markdown,
                value=spec.get("documentation", "")
            ) if spec.get("documentation") else None,
            insert_text=spec.get("insert_text", spec["label"]),
            sort_text=f"0{spec['label']}"  # Priority sorting
        )
        items.append(item)
    
    return items
