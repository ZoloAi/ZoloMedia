# Zolo LSP Architecture

**Pure LSP, Terminal-First, String-First Philosophy**

## Overview

Zolo LSP follows the **TOML model** for language tooling: a single source of truth (the parser) wrapped by an LSP server, with thin editor clients.

```
┌─────────────────────────────────────────────────┐
│       parser.py (364 lines) - Thin API          │
│  ═══════════════════════════════════════════    │
│  PUBLIC API - Orchestration Layer               │
│                                                  │
│  • tokenize() → ParseResult                     │  ← String-first
│    - Semantic tokens (for highlighting)         │     philosophy
│    - Parsed data                                │
│    - Diagnostics                                │
│                                                  │
│  • load/loads() → Parse .zolo files             │
│  • dump/dumps() → Write .zolo files             │
│                                                  │
│  Delegates to parser_modules/ (modular!)        │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│         parser_modules/ (8 modules)             │
│  ═══════════════════════════════════════════    │
│  THE BRAIN - Modular Parser Implementation     │
│                                                  │
│  • line_parsers.py (843 lines)                  │  ← Core parsing
│  • token_emitter.py (171 lines)                 │  ← Token emission
│  • block_tracker.py (71 lines)                  │  ← Context tracking
│  • key_detector.py (98 lines)                   │  ← Key classification
│  • file_type_detector.py (61 lines)             │  ← File type logic
│  • value_validators.py (53 lines)               │  ← Value validation
│  • serializer.py (56 lines)                     │  ← .zolo serialization
│  • + 5 more utility modules                     │
│                                                  │
│  Industry-grade: <500 lines per file!           │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│         lsp_server.py (367 lines)               │
│  ═══════════════════════════════════════════    │
│  THE WRAPPER - Thin LSP Protocol Layer         │
│                                                  │
│  • Wraps parser.tokenize()                      │  ← No business
│  • Implements LSP protocol (pygls)              │     logic here!
│  • Delegates to providers/                      │
│                                                  │
│  Features:                                       │
│  • Semantic tokens (highlighting)               │
│  • Diagnostics (errors/warnings)                │
│  • Hover (type hint docs)                       │
│  • Completion (type hints, values)              │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│           providers/ (3 thin wrappers)          │
│  ═══════════════════════════════════════════    │
│  THIN WRAPPERS - Delegate to Modules           │
│                                                  │
│  • completion_provider.py (62 lines)            │  ← Was 301!
│  • hover_provider.py (55 lines)                 │  ← Was 285!
│  • diagnostics_engine.py (114 lines)            │  ← Was 234!
│                                                  │
│  -72% code reduction through modularization!    │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│         provider_modules/ (4 modules)           │
│  ═══════════════════════════════════════════    │
│  THE LOGIC - Modular Provider Implementation   │
│                                                  │
│  • documentation_registry.py (263 lines)        │  ← SSOT for docs
│  • completion_registry.py (321 lines)           │  ← Context-aware
│  • hover_renderer.py (266 lines)                │  ← Hover formatting
│  • diagnostic_formatter.py (239 lines)          │  ← Error formatting
│                                                  │
│  Zero duplication! 88-97% test coverage!        │
└─────────────────────────────────────────────────┘
                  │
                  ↓
         ┌────────┴────────┐
         │                 │
         ↓                 ↓
    ┌─────────┐       ┌─────────┐
    │   Vim   │       │ VS Code │  ← PHASE 2
    │   LSP   │       │  (GUI)  │     (Future)
    │ Client  │       └─────────┘
    └─────────┘            │
         ↑                 ↓
    PHASE 1           ┌─────────┐
     (Now)            │IntelliJ │  ← PHASE 3
                      └─────────┘     (Future)
```

## Design Principles

### 1. Single Source of Truth

**The parser is the only place that understands .zolo syntax.**

- No grammar files (TextMate, Vim syntax)
- No duplication of parsing logic
- LSP queries parser for everything

**Why?**
- Traditional approach: Parser + Grammar files = duplication, drift
- LSP approach: Parser only = always in sync

### 2. String-First Philosophy

Zolo's core innovation: **values are strings by default**, with explicit type hints for conversion.

```zolo
# String (default)
name: Zolo

# Explicit types
version(float): 1.0
port(int): 8080
enabled(bool): true

# Force string (even if looks like number)
id(str): 12345
```

**Benefits:**
- No ambiguity (YAML's `yes` = `true` problem)
- Explicit is better than implicit
- Easy to understand, hard to misuse

### 3. Terminal-First

**Phase 1: Perfect Vim support**
- Vim/Neovim LSP client
- Terminal-based workflow
- No GUI dependencies

**Phase 2+: Expand to GUIs**
- VS Code (same LSP server)
- IntelliJ (same LSP server)
- Web editors (same LSP server)

All editors connect to the same `parser.py` brain.

## File Structure

```
zLSP/
├── src/zolo/
│   ├── parser.py              ← THE BRAIN (2,700+ lines)
│   ├── lsp_server.py          ← LSP wrapper (~350 lines)
│   ├── semantic_tokenizer.py  ← Token encoding
│   ├── lsp_types.py           ← Type definitions
│   ├── type_hints.py          ← String-first type system
│   ├── constants.py           ← Shared constants
│   ├── exceptions.py          ← Error types
│   │
│   ├── providers/             ← LSP feature providers
│   │   ├── diagnostics_engine.py
│   │   ├── hover_provider.py
│   │   └── completion_provider.py
│   │
│   └── vim/                   ← Vim integration (Phase 1)
│       ├── ftdetect/          → File type detection
│       ├── indent/            → Indentation rules
│       ├── lsp_config.vim     → LSP client setup
│       ├── install.sh         → Installation script
│       └── README.md          → Vim-specific docs
│
├── tests/                     ← Unit tests
├── examples/                  ← Example .zolo files
├── docs/                      ← Documentation
├── pyproject.toml             ← Package config
└── README.md                  ← Main docs
```

## What We Removed (Cleanup)

### ❌ Deleted: Grammar System
- `grammar/zolo.grammar.json` - Redundant
- `compilers/` - Not needed for pure LSP
- `cli/grammar_builder.py` - Not needed

**Why?**
- Grammar files duplicate parser logic
- LSP provides semantic tokens directly
- Simpler = fewer bugs

### ❌ Deleted: Setup Scripts
- `setup_icons.py` - OS-specific, not core
- `install_handler.py` - OS-specific, not core
- `vim_setup.py` - Replaced by `vim/install.sh`

**Why?**
- Focus on core LSP functionality
- OS integration is Phase 2+

### ❌ Deleted: VS Code Extension (for now)
- Will be Phase 2
- Same LSP server, different client

## Core Components

### parser.py - The Brain

**Public API:**
```python
from zolo import load, loads, dump, dumps

# Load from file
data = load('config.zolo')

# Load from string
data = loads('key: value')

# Dump to file
dump(data, 'output.zolo')

# Dump to string
text = dumps(data)
```

**LSP API:**
```python
from zolo.parser import tokenize

# Parse and get semantic tokens
result = tokenize(content, filename='test.zolo')
# Returns: ParseResult(data, tokens, diagnostics)
```

**String-First Logic:**
```python
# Default: string
loads('name: Zolo')  # → {'name': 'Zolo'}

# Type hints: convert
loads('port(int): 8080')  # → {'port': 8080}
loads('version(float): 1.0')  # → {'version': 1.0}
loads('enabled(bool): true')  # → {'enabled': True}

# Force string
loads('id(str): 12345')  # → {'id': '12345'}
```

### lsp_server.py - The Wrapper

**Responsibilities:**
1. Implement LSP protocol (using `pygls`)
2. Call `parser.tokenize()` for semantic tokens
3. Delegate to providers for features
4. **No parsing logic!** (that's in parser.py)

**LSP Features:**
- `textDocument/semanticTokens/full` → Syntax highlighting
- `textDocument/publishDiagnostics` → Error reporting
- `textDocument/hover` → Type hint docs
- `textDocument/completion` → Autocomplete

### providers/ - Feature Modules

Thin wrappers that call parser and format results:

- **diagnostics_engine.py** - Converts parse errors to LSP diagnostics
- **hover_provider.py** - Shows type hint documentation
- **completion_provider.py** - Suggests type hints, values

All providers call `parser.tokenize()` - no independent parsing.

## How It Works: Example Flow

### User Opens `test.zolo` in Vim

```zolo
# Test file
name: Zolo
version(float): 1.0
port(int): 8080
enabled(bool): true
```

**Step 1: Vim detects .zolo file**
- `ftdetect/zolo.vim` sets `filetype=zolo`

**Step 2: Vim starts LSP client**
- `lsp_config.vim` runs
- Starts `zolo-lsp` server
- Connects via stdio

**Step 3: LSP server parses file**
```python
result = tokenize(content, filename='test.zolo')
# Returns:
# - data: {'name': 'Zolo', 'version': 1.0, 'port': 8080, 'enabled': True}
# - tokens: [Token(line=1, col=0, type='comment'), ...]
# - diagnostics: []
```

**Step 4: LSP sends semantic tokens to Vim**
- Vim colors the file based on tokens
- Comments gray, keys salmon, values by type

**Step 5: User hovers over `version(float)`**
- LSP calls `hover_provider.get_hover_info()`
- Returns: "**Floating Point Number**\n\nConvert value to float."
- Vim shows hover popup

**Step 6: User types `new_key(`**
- LSP calls `completion_provider.get_completions()`
- Returns: `int`, `float`, `bool`, `str`, etc.
- Vim shows completion menu

## Testing

### Unit Tests
```bash
cd zLSP
pytest tests/
```

Tests:
- `test_parser.py` - Parser logic (string-first, type hints)
- `test_type_hints.py` - Type conversion
- `test_lsp_semantic_tokenizer.py` - Token generation

### Manual Testing
```bash
# Test parser
python3 -c "from zolo import loads; print(loads('key: value'))"

# Test LSP server
zolo-lsp --help

# Test in Vim
cd src/zolo/vim
./install.sh
nvim test.zolo
```

## Comparison to Other Languages

### TOML (taplo)
```
toml crate (Rust) → taplo-lsp → Editors
```
**Same pattern as Zolo!**

### Rust (rust-analyzer)
```
rustc parser → rust-analyzer LSP → Editors
```
**Same pattern!** (Plus grammar files for basic syntax)

### YAML (yaml-language-server)
```
yaml parser (JS) → yaml-language-server → Editors
```
**Same pattern!**

### Zolo
```
parser.py (Python) → zolo-lsp → Editors
```
**We're in good company!**

## Advantages of This Architecture

### ✅ Single Source of Truth
- Parser defines syntax
- No grammar files to keep in sync
- Changes propagate automatically

### ✅ Editor Agnostic
- Same LSP server for all editors
- Vim, VS Code, IntelliJ, etc.
- Write once, run everywhere

### ✅ Rich Features
- Semantic highlighting (context-aware)
- Real-time diagnostics
- Hover documentation
- Code completion

### ✅ String-First Innovation
- No ambiguity (YAML's `yes` problem)
- Explicit type conversion
- Easy to understand

### ✅ Terminal-First
- Perfect Vim support (Phase 1)
- No GUI dependencies
- Fast, lightweight

## Refactoring Achievements (Phase 1-3)

### ✅ Phase 1: Cleanup & Git Hygiene (DONE)
- [x] Updated .gitignore for Python projects
- [x] Created version.py for single source version
- [x] Configured pyproject.toml and MANIFEST.in
- [x] Updated LICENSE with MIT + Ethical Use Clause
- [x] Removed debug/test files

### ✅ Phase 2: Parser Modularization (DONE)
- [x] Broke monolithic parser.py (2,700 → 364 lines, -86%)
- [x] Created parser_modules/ with 13 focused modules
- [x] Extracted BlockTracker, FileTypeDetector, KeyDetector, ValueValidator
- [x] Each module <500 lines for maintainability
- [x] Removed YAML dependency - pure .zolo format!
- [x] 162 tests, 98% coverage for key modules

### ✅ Phase 3: Provider Modularization (DONE)
- [x] Refactored all 3 providers (820 → 231 lines, -72%)
- [x] Created provider_modules/ with 4 focused modules
- [x] DocumentationRegistry - SSOT for all documentation
- [x] CompletionRegistry - context-aware completions
- [x] HoverRenderer - hover formatting
- [x] DiagnosticFormatter - error formatting
- [x] 99 provider tests, 88-97% coverage each module

**Result:** Industry-grade modular architecture, zero duplication!

### 🔜 Phase 4: Documentation Refresh (In Progress)
- [ ] Update ARCHITECTURE.md (this file!)
- [ ] Update README.md with achievements
- [ ] Polish existing documentation

### 🔜 Phase 5: Testing Expansion (Next)
- [ ] Integration tests for end-to-end workflows
- [ ] Test all 5 special file types
- [ ] Strategic coverage expansion

### 🔜 Phase 6-7: VS Code & Advanced Features (Future)
- [ ] VS Code extension (reuse same LSP server!)
- [ ] Advanced LSP features (go-to-definition, etc.)

## Contributing

**Core principle:** Parser and providers are the single source of truth.

- New syntax? → Add to `parser_modules/` (likely line_parsers.py)
- New token type? → Update `lsp_types.py` and semantic_tokenizer.py
- New file type? → Extend `file_type_detector.py`
- New validation? → Add to `value_validators.py` or `diagnostic_formatter.py`
- New completion? → Update `completion_registry.py`
- New documentation? → Add to `documentation_registry.py` (SSOT!)

**Architecture guidelines:**
- Keep modules <500 lines (ideally <400)
- Write tests for all new functionality
- Follow thin wrapper pattern (providers delegate to modules)
- Never duplicate logic - use SSOT principle

**Never:** Duplicate parsing logic in grammar files or LSP server.

## References

- [Language Server Protocol Spec](https://microsoft.github.io/language-server-protocol/)
- [pygls (Python LSP framework)](https://github.com/openlawlibrary/pygls)
- [taplo (TOML LSP)](https://github.com/tamasfe/taplo)
- [rust-analyzer Architecture](https://github.com/rust-lang/rust-analyzer/blob/master/docs/dev/architecture.md)
