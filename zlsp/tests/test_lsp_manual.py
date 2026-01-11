#!/usr/bin/env python3
"""
Manual test of LSP semantic tokens.
This bypasses VSCode to verify the server logic is working.
"""

import sys
sys.path.insert(0, '.')

from zolo.parser import tokenize
from zolo.semantic_tokenizer import encode_semantic_tokens

test_content = """# STRING-FIRST PHILOSOPHY
# Only numbers auto-detect → float
name: MyApp
port: 5000
debug_string: true
"""

print("=== PARSING TEST ===")
result = tokenize(test_content)

print(f"\n✅ Parsed {len(result.tokens)} tokens")
print(f"✅ Found {len(result.errors)} errors")

print("\n=== TOKEN DETAILS ===")
for token in result.tokens:
    lines = test_content.split('\n')
    if token.range.start.line < len(lines):
        char_content = lines[token.range.start.line][token.range.start.character:token.range.end.character]
        if len(char_content) > 40:
            char_content = char_content[:37] + "..."
        print(f"{token.range.start.line}:{token.range.start.character:2d}-{token.range.end.character:2d} | {token.token_type.value:20s} | \"{char_content}\"")

print("\n=== LSP ENCODING ===")
encoded = encode_semantic_tokens(result.tokens)
print(f"✅ Encoded to {len(encoded)} integers (array of {len(encoded)//5} * 5)")
print(f"First 30 integers: {encoded[:30]}")

print("\n=== VERIFICATION ===")
print(f"✅ Comments should be green: tokens {result.tokens[0].token_type.value}, {result.tokens[1].token_type.value}")
print(f"✅ Keys should be tan/blue: tokens {result.tokens[2].token_type.value}, {result.tokens[5].token_type.value}")
print(f"✅ 'true' should be STRING (purple): token {result.tokens[11].token_type.value}")
