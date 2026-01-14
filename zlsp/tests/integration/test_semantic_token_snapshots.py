"""
Semantic Token Snapshot Tests

These tests capture the EXACT token output from the LSP server
for all example files. This is the single source of truth that
proves our parser/tokenizer works correctly.

The golden baselines were verified by manual inspection of Vim
rendering. Any editor that receives these tokens MUST render
identically (per LSP spec).

File Type Detection:
- basic.zolo → generic .zolo file
- advanced.zolo → generic .zolo file  
- zSpark.example.zolo → zSpark file type
- zEnv.example.zolo → zEnv file type
- zUI.example.zolo → zUI file type
- zConfig.machine.zolo → zConfig file type
- zSchema.example.zolo → zSchema file type
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List

import pytest

from core.parser.parser import tokenize
from core.parser.parser_modules.file_type_detector import detect_file_type, FileType


# Paths
GOLDEN_DIR = Path(__file__).parent / "golden_tokens"
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"

# Example files to test (all 7 files)
EXAMPLE_FILES = [
    "basic.zolo",
    "advanced.zolo",
    "zSpark.example.zolo",
    "zEnv.example.zolo",
    "zUI.example.zolo",
    "zConfig.machine.zolo",
    "zSchema.example.zolo",
]


def capture_semantic_tokens(file_path: Path) -> Dict[str, Any]:
    """
    Capture semantic token output from parser/tokenizer.
    
    This is the EXACT output that the LSP server sends to editors.
    
    Args:
        file_path: Path to .zolo file
        
    Returns:
        Dictionary containing:
        - file: filename
        - file_type: detected file type (e.g., "zSpark", "zEnv", None for generic)
        - line_count: number of lines in file
        - token_count: number of semantic tokens
        - tokens: list of token dictionaries with all details
    """
    # Read file content
    with open(file_path) as f:
        content = f.read()
    
    # Detect file type
    file_type_enum = detect_file_type(str(file_path))
    # Convert FileType enum to string value (e.g., FileType.ZSPARK -> "zspark")
    # For GENERIC files, use None to indicate no special file type
    file_type = file_type_enum.value if file_type_enum != FileType.GENERIC else None
    
    # Parse file and get semantic tokens
    result = tokenize(content, filename=str(file_path))
    
    # Extract token details
    tokens_list = []
    for token in result.tokens:
        # Get text from content using token range
        lines = content.splitlines()
        if token.line < len(lines):
            line_text = lines[token.line]
            start_char = token.range.start.character
            end_char = token.range.end.character
            token_text = line_text[start_char:end_char] if start_char < len(line_text) else ""
        else:
            token_text = ""
        
        tokens_list.append({
            "line": token.line,
            "start": token.range.start.character,
            "end": token.range.end.character,
            "length": end_char - start_char,
            "type": str(token.token_type),  # Convert TokenType to string for JSON serialization
            "modifiers": token.modifiers,
            "text": token_text,
        })
    
    return {
        "file": file_path.name,
        "file_type": file_type,
        "line_count": len(content.splitlines()),
        "token_count": len(result.tokens),
        "tokens": tokens_list,
    }


def get_golden_path(filename: str) -> Path:
    """Get path to golden baseline file for a given example filename."""
    return GOLDEN_DIR / f"{filename}.tokens.json"


@pytest.mark.integration
@pytest.mark.parametrize("filename", EXAMPLE_FILES)
def test_semantic_token_snapshots(filename: str):
    """
    Test that semantic token output matches golden baseline.
    
    Run with UPDATE_GOLDEN_TOKENS=1 environment variable to regenerate baselines.
    
    This test ensures:
    1. File type detection works correctly (zSpark, zEnv, zUI, zConfig, zSchema)
    2. Token types are correct for each file type
    3. Token positions are accurate
    4. Token output is deterministic (same every time)
    5. All editors receive identical tokens
    """
    file_path = EXAMPLES_DIR / filename
    golden_path = get_golden_path(filename)
    
    # Capture current token output
    current_tokens = capture_semantic_tokens(file_path)
    
    # Check if we should update golden baselines
    update_golden = os.environ.get("UPDATE_GOLDEN_TOKENS", "0") == "1"
    
    if update_golden:
        # Update golden baseline
        golden_path.parent.mkdir(exist_ok=True, parents=True)
        with open(golden_path, "w") as f:
            json.dump(current_tokens, f, indent=2, sort_keys=True)
        print(f"✅ Updated golden baseline: {filename}")
    else:
        # Compare to golden baseline
        assert golden_path.exists(), (
            f"Golden baseline not found: {golden_path}\n"
            f"Run with UPDATE_GOLDEN_TOKENS=1 to create it."
        )
        
        with open(golden_path) as f:
            golden_tokens = json.load(f)
        
        # Compare token output
        if current_tokens != golden_tokens:
            # Provide detailed diff information
            diff_info = []
            
            if current_tokens["file_type"] != golden_tokens["file_type"]:
                diff_info.append(
                    f"  File type mismatch: "
                    f"{current_tokens['file_type']} != {golden_tokens['file_type']}"
                )
            
            if current_tokens["token_count"] != golden_tokens["token_count"]:
                diff_info.append(
                    f"  Token count mismatch: "
                    f"{current_tokens['token_count']} != {golden_tokens['token_count']}"
                )
            
            if current_tokens["tokens"] != golden_tokens["tokens"]:
                diff_info.append("  Token details differ")
                
                # Find first differing token
                for i, (curr, gold) in enumerate(zip(
                    current_tokens["tokens"],
                    golden_tokens["tokens"]
                )):
                    if curr != gold:
                        diff_info.append(f"  First difference at token #{i}:")
                        diff_info.append(f"    Current: {curr}")
                        diff_info.append(f"    Golden:  {gold}")
                        break
            
            diff_message = "\n".join(diff_info)
            pytest.fail(
                f"Semantic token mismatch in {filename}:\n{diff_message}\n\n"
                f"Run with UPDATE_GOLDEN_TOKENS=1 to update golden baseline."
            )
        
        print(f"✅ Tokens match golden baseline: {filename}")


@pytest.mark.integration
def test_all_example_files_covered():
    """
    Ensure all example files have golden baselines.
    
    This test verifies that we're testing all 7 example files,
    including all special file types.
    """
    expected_files = set(EXAMPLE_FILES)
    golden_files = set()
    
    if GOLDEN_DIR.exists():
        for golden_file in GOLDEN_DIR.glob("*.tokens.json"):
            # Extract original filename from golden filename
            original = golden_file.name.replace(".tokens.json", "")
            golden_files.add(original)
    
    missing = expected_files - golden_files
    if missing:
        pytest.fail(
            f"Missing golden baselines for: {missing}\n"
            f"Run with UPDATE_GOLDEN_TOKENS=1 to create them."
        )


@pytest.mark.integration
@pytest.mark.parametrize("filename,expected_type", [
    ("zSpark.example.zolo", FileType.ZSPARK),
    ("zEnv.example.zolo", FileType.ZENV),
    ("zUI.example.zolo", FileType.ZUI),
    ("zConfig.machine.zolo", FileType.ZCONFIG),
    ("zSchema.example.zolo", FileType.ZSCHEMA),
    ("basic.zolo", FileType.GENERIC),  # Generic .zolo file
    ("advanced.zolo", FileType.GENERIC),  # Generic .zolo file
])
def test_file_type_detection(filename: str, expected_type: FileType):
    """
    Test that file type detector correctly identifies special zolo files.
    
    This is critical because different file types emit different token types
    (e.g., zsparkKey vs rootKey).
    """
    file_path = EXAMPLES_DIR / filename
    detected_type = detect_file_type(str(file_path))
    
    assert detected_type == expected_type, (
        f"File type detection failed for {filename}: "
        f"expected {expected_type}, got {detected_type}"
    )
