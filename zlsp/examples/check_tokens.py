#!/usr/bin/env python3
"""
ZLSP Tokenizer Test with Visual Highlighting
Shows token types with colors for easy verification
"""
import sys
import os

# Add zlsp to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from zlsp.core.parser.parser_modules.line_parsers import parse_lines_with_tokens
from zlsp.core.parser.parser_modules.token_emitter import TokenEmitter
from collections import Counter

# ANSI color codes for terminal output
class Color:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Token type colors (matching VSCode semantic highlighting)
    COMMENT = '\033[90m'        # Bright black (gray)
    KEY = '\033[94m'            # Bright blue
    STRING = '\033[32m'         # Green
    NUMBER = '\033[35m'         # Magenta
    BOOLEAN = '\033[36m'        # Cyan
    BRACKET = '\033[33m'        # Yellow
    BRACE = '\033[33m'          # Yellow
    COLON = '\033[37m'          # White
    COMMA = '\033[37m'          # White
    ESCAPE = '\033[91m'         # Bright red

def colorize_token(text, token_type):
    """Apply color based on token type"""
    colors = {
        'COMMENT': Color.COMMENT,
        'ROOT_KEY': Color.KEY,
        'NESTED_KEY': Color.KEY,
        'STRING': Color.STRING,
        'NUMBER': Color.NUMBER,
        'BOOLEAN': Color.BOOLEAN,
        'NULL': Color.DIM,
        'BRACKET_STRUCTURAL': Color.BRACKET,
        'BRACE_STRUCTURAL': Color.BRACE,
        'COLON': Color.COLON,
        'COMMA': Color.COMMA,
        'ESCAPE_SEQUENCE': Color.ESCAPE,
    }
    color = colors.get(token_type, Color.RESET)
    return f'{color}{text}{Color.RESET}'

def show_line_with_highlights(line_num, line_text, tokens):
    """Show a line with its tokens highlighted in color"""
    if not tokens:
        print(f'  {Color.DIM}{line_num:4d}│ {line_text.rstrip()}{Color.RESET}')
        return
    
    # Build highlighted version of the line
    result = []
    last_pos = 0
    
    for token in sorted(tokens, key=lambda t: t.start_char):
        # Add unhighlighted text before token
        if token.start_char > last_pos:
            result.append(line_text[last_pos:token.start_char])
        
        # Add highlighted token
        token_text = line_text[token.start_char:token.start_char + token.length]
        result.append(colorize_token(token_text, token.token_type.name))
        last_pos = token.start_char + token.length
    
    # Add remaining text
    if last_pos < len(line_text):
        result.append(line_text[last_pos:])
    
    print(f'  {line_num:4d}│ {"".join(result).rstrip()}')

def check_file_tokens(filepath):
    """Parse file and show visual highlighting"""
    # Parse file
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    content = ''.join(lines)
    emitter = TokenEmitter(content, filepath)
    line_mapping = {i: i for i in range(len(lines))}

    parsed = parse_lines_with_tokens(lines, line_mapping, emitter)
    tokens = emitter.tokens

    print(f'\n{Color.BOLD}{"="*80}{Color.RESET}')
    print(f'{Color.BOLD}ZLSP TOKENIZER TEST - Visual Highlighting Verification{Color.RESET}')
    print(f'{Color.BOLD}{"="*80}{Color.RESET}\n')

    # Test specific sections with visual output
    test_sections = [
        (686, 692, 'Test 26: First DL item - multiline desc'),
        (693, 705, 'Test 26: Second DL item - desc: [multiline]'),
        (706, 713, 'Test 26: Third DL item - multiline desc'),
    ]

    for start, end, description in test_sections:
        print(f'\n{Color.BOLD}{description}{Color.RESET} (lines {start+1}-{end})')
        print(f'{Color.DIM}{"─"*80}{Color.RESET}')
        
        # Show each line with highlighting
        for line_num in range(start, min(end, start + 8)):  # Show up to 8 lines
            line_tokens = [t for t in tokens if t.line == line_num]
            show_line_with_highlights(line_num + 1, lines[line_num], line_tokens)
        
        # Count token types in this section
        section_tokens = [t for t in tokens if start <= t.line < end]
        token_types = Counter(t.token_type.name for t in section_tokens)
        
        print(f'\n  {Color.BOLD}Token Summary:{Color.RESET}')
        for ttype, count in token_types.most_common(5):
            print(f'    • {ttype}: {count}')
        
        # Check for STRING tokens
        string_tokens = [t for t in section_tokens if t.token_type.name == 'STRING']
        if string_tokens:
            print(f'  {Color.BOLD}✅ {len(string_tokens)} STRING tokens{Color.RESET} (multiline content highlighted)')
        else:
            print(f'  {Color.BOLD}⚠️  NO STRING tokens!{Color.RESET}')

    print(f'\n{Color.BOLD}{"="*80}{Color.RESET}')
    print(f'{Color.BOLD}File Statistics{Color.RESET}')
    print(f'{Color.BOLD}{"="*80}{Color.RESET}')
    print(f'Total tokens: {len(tokens)}')
    print(f'Total lines: {len(lines)}')
    print(f'STRING tokens: {sum(1 for t in tokens if t.token_type.name == "STRING")}')
    print(f'{Color.BOLD}{"="*80}{Color.RESET}\n')

if __name__ == "__main__":
    filepath = os.path.join(os.path.dirname(__file__), "advanced.zolo")
    check_file_tokens(filepath)
