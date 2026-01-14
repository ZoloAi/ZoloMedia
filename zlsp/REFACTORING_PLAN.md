# zLSP Industry-Grade Refactoring Plan

**Status:** Draft v1.0  
**Target:** Bring zLSP to production quality before VS Code integration  
**Reference:** `~/Projects/Zolo/zKernel` architecture and standards

---

## 📊 Current State Analysis

### ✅ Strengths
- **Pure LSP architecture** - Parser as single source of truth
- **Comprehensive token coverage** - All special `.zolo` file types supported
- **Working Vim integration** - Full LSP features functional
- **Solid test foundation** - Unit, integration, and E2E tests
- **Clean separation** - `core/`, `bindings/`, `editors/`, `themes/`

### ⚠️ Issues Identified

#### 1. **Code Organization**
- `parser.py` is 3,419 lines (monolithic)
- `TokenEmitter` class has 17+ block tracking lists (DRY violation)
- Repeated detection logic across file types
- No version management (`version.py` missing)

#### 2. **Documentation Gaps**
- Missing AI Agent Guide (zKernel has this)
- No `mypy.ini` for type checking
- No `MANIFEST.in` for package data
- Incomplete docstrings in many functions

#### 3. **Testing & Quality**
- No linting configuration (ruff/pylint not configured)
- Missing coverage for all zSchema features
- No performance benchmarks
- Test files in examples/ (should be in tests/fixtures/)

#### 4. **Package Structure**
- `zlsp.egg-info/` committed (should be in `.gitignore`)
- `__pycache__/` directories visible
- No `uv.lock` for modern dependency management
- Mixed use of `setup.py` and `pyproject.toml`

#### 5. **Theme System**
- No CLI command for theme management
- Theme generator not exposed as entry point
- Missing theme validation

---

## 🎯 Refactoring Goals

1. **DRY Principle** - Eliminate repeated code patterns
2. **Modularity** - Break down monolithic `parser.py`
3. **Industry Standards** - Match zKernel's quality level
4. **Maintainability** - Clear structure for future contributors
5. **Performance** - Optimize hot paths in parser
6. **Documentation** - Complete guides for all audiences

---

## 📋 Refactoring Plan (Micro Steps)

### **Phase 1: Cleanup & Organization** (Priority: 🔥 Critical)

#### 1.1 Remove Debug/Test Files
- [x] Keep canonical examples (already cleaned up):
  - `advanced.zolo` - Comprehensive syntax test
  - `basic.zolo` - Simple example
  - `zSpark.example.zolo` - zSpark file type
  - `zEnv.example.zolo` - zEnv file type
  - `zUI.example.zolo` - zUI file type
  - `zConfig.machine.zolo` - zConfig file type
  - `zSchema.example.zolo` - zSchema file type
- [x] Removed comparison files (user deleted these)
- [x] Delete `zlsp/examples/usage.py` ✅

#### 1.2 Git Hygiene
- [x] Add `*.egg-info/` to `.gitignore` ✅ (already present)
- [x] Add `__pycache__/` to `.gitignore` ✅ (already present)
- [x] Add `*.pyc`, `*.pyo`, `*.pyd` to `.gitignore` ✅ (already present)
- [x] Add `.pytest_cache/`, `.coverage`, `htmlcov/` to `.gitignore` ✅
- [x] Add `.mypy_cache/`, `.ruff_cache/` to `.gitignore` ✅
- [x] Remove `.coverage` from git tracking ✅
- [x] `zlsp.egg-info/` not tracked ✅
- [x] `__pycache__/` not tracked ✅

#### 1.3 Package Configuration
- [ ] Create `zlsp/core/version.py` with `__version__ = "1.0.0"`
- [ ] Update `pyproject.toml` to use dynamic version: `version = {attr = "core.version.__version__"}`
- [ ] Create `MANIFEST.in` for non-Python files (themes, vim configs)
- [ ] Create `mypy.ini` for type checking configuration
- [ ] Add `uv.lock` support (optional, for modern dep management)
- [ ] Consolidate `setup.py` - move all config to `pyproject.toml`

---

### **Phase 2: Parser Refactoring** (Priority: 🔥 Critical)

#### 2.1 Extract Block Tracking System
**Problem:** 17+ block tracking lists in `TokenEmitter` (DRY violation)

**Solution:** Create `zlsp/core/parser/block_tracker.py`

```python
class BlockTracker:
    """Unified block tracking for context-aware parsing."""
    
    def __init__(self):
        self._blocks = {}  # {block_type: [(indent, line), ...]}
    
    def enter_block(self, block_type: str, indent: int, line: int):
        """Enter a new block context."""
        
    def exit_blocks(self, current_indent: int, current_line: int):
        """Exit blocks based on indentation."""
        
    def is_inside(self, block_type: str, current_indent: int) -> bool:
        """Check if we're inside a specific block type."""
        
    def is_first_level(self, block_type: str, current_indent: int) -> bool:
        """Check if we're at first nesting level under block."""
```

**Tasks:**
- [ ] Create `block_tracker.py` with `BlockTracker` class
- [ ] Migrate all 17+ block tracking lists to unified system
- [ ] Update `TokenEmitter` to use `BlockTracker`
- [ ] Add unit tests for `BlockTracker`
- [ ] Document block tracking patterns

**Estimated Impact:** -500 lines from `parser.py`, improved maintainability

#### 2.2 Extract File Type Detection
**Problem:** File type detection scattered across `TokenEmitter.__init__`

**Solution:** Create `zlsp/core/parser/file_types.py`

```python
class FileTypeDetector:
    """Detect and classify .zolo file types."""
    
    @staticmethod
    def detect(filename: str) -> FileType:
        """Detect file type from filename."""
        
    @staticmethod
    def extract_component_name(filename: str, file_type: FileType) -> Optional[str]:
        """Extract component name (e.g., 'zVaF' from 'zUI.zVaF.zolo')."""
```

**Tasks:**
- [ ] Create `file_types.py` with `FileType` enum
- [ ] Extract detection logic from `TokenEmitter`
- [ ] Add component name extraction
- [ ] Add unit tests for all file types
- [ ] Document file naming conventions

**Estimated Impact:** -100 lines from `parser.py`, clearer file type handling

#### 2.3 Extract Token Emission Logic
**Problem:** `_emit_value_tokens()` is 197 lines with complex branching

**Solution:** Create `zlsp/core/parser/token_emitters.py`

```python
class ValueTokenEmitter:
    """Specialized token emission for different value types."""
    
    def emit_string(self, value: str, line: int, pos: int, emitter: TokenEmitter):
        """Emit tokens for string values with escape sequences."""
        
    def emit_number(self, value: str, line: int, pos: int, emitter: TokenEmitter):
        """Emit tokens for numeric values."""
        
    def emit_boolean(self, value: str, line: int, pos: int, emitter: TokenEmitter):
        """Emit tokens for boolean values."""
        
    def emit_array(self, value: str, line: int, pos: int, emitter: TokenEmitter):
        """Emit tokens for array values."""
        
    def emit_object(self, value: str, line: int, pos: int, emitter: TokenEmitter):
        """Emit tokens for object values."""
```

**Tasks:**
- [ ] Create `token_emitters.py` with specialized emitters
- [ ] Refactor `_emit_value_tokens()` to use emitters
- [ ] Refactor `_emit_string_with_escapes()` to use emitters
- [ ] Refactor `_emit_array_tokens()` to use emitters
- [ ] Refactor `_emit_object_tokens()` to use emitters
- [ ] Add unit tests for each emitter
- [ ] Document token emission patterns

**Estimated Impact:** -400 lines from `parser.py`, better testability

#### 2.4 Extract Key Detection Logic
**Problem:** Repeated special key detection across file types

**Solution:** Create `zlsp/core/parser/key_detectors.py`

```python
class KeyDetectorRegistry:
    """Registry of key detectors for different file types."""
    
    def __init__(self):
        self._detectors = {
            FileType.ZSPARK: ZSparkKeyDetector(),
            FileType.ZENV: ZEnvKeyDetector(),
            FileType.ZUI: ZUIKeyDetector(),
            FileType.ZCONFIG: ZConfigKeyDetector(),
            FileType.ZSCHEMA: ZSchemaKeyDetector(),
        }
    
    def detect_token_type(self, key: str, context: ParsingContext) -> TokenType:
        """Detect token type for a key based on file type and context."""
```

**Tasks:**
- [ ] Create `key_detectors.py` with detector classes
- [ ] Extract zSpark key detection logic
- [ ] Extract zEnv key detection logic
- [ ] Extract zUI key detection logic
- [ ] Extract zConfig key detection logic
- [ ] Extract zSchema key detection logic
- [ ] Add unit tests for each detector
- [ ] Document key detection patterns

**Estimated Impact:** -600 lines from `parser.py`, extensible architecture

#### 2.5 Extract Validation Logic
**Problem:** Validation scattered across parser and diagnostics engine

**Solution:** Create `zlsp/core/parser/validators.py`

```python
class ValidatorRegistry:
    """Registry of validators for different value types."""
    
    def validate_deployment_value(self, value: str) -> Optional[Diagnostic]:
        """Validate deployment values (Production/Development)."""
        
    def validate_log_level_value(self, value: str) -> Optional[Diagnostic]:
        """Validate log level values (DEBUG/INFO/WARNING/etc.)."""
        
    def validate_zmode_value(self, value: str) -> Optional[Diagnostic]:
        """Validate zMode values (Terminal/zBifrost)."""
```

**Tasks:**
- [ ] Create `validators.py` with validator classes
- [ ] Extract deployment validation
- [ ] Extract log level validation
- [ ] Extract zMode validation
- [ ] Extract zVaFile validation
- [ ] Add unit tests for each validator
- [ ] Document validation rules

**Estimated Impact:** -200 lines from `parser.py`, centralized validation

---

### **Phase 3: Theme System Enhancement** (Priority: 🔶 High)

#### 3.1 Theme CLI Commands
**Problem:** No CLI for theme management

**Tasks:**
- [ ] Create `zlsp/themes/cli.py` with theme commands
- [ ] Add `zlsptheme` entry point to `pyproject.toml`
- [ ] Implement `zlsptheme list` - List available themes
- [ ] Implement `zlsptheme install <editor>` - Install theme for editor
- [ ] Implement `zlsptheme validate` - Validate theme YAML
- [ ] Implement `zlsptheme generate <editor>` - Generate editor config
- [ ] Add help text and examples
- [ ] Document theme CLI in README

#### 3.2 Theme Validation
**Problem:** No validation for theme YAML files

**Tasks:**
- [ ] Create `zlsp/themes/validator.py`
- [ ] Validate color palette (hex, ansi, rgb consistency)
- [ ] Validate token mappings (all tokens defined)
- [ ] Validate editor overrides
- [ ] Add schema validation (optional: JSON Schema)
- [ ] Add unit tests for validation
- [ ] Document theme schema

---

### **Phase 4: Documentation** (Priority: 🔶 High)

#### 4.1 Core Documentation
- [ ] Create `zlsp/Documentation/AI_AGENT_GUIDE.md` (like zKernel)
- [ ] Update `zlsp/README.md` with new structure
- [ ] Create `zlsp/Documentation/CONTRIBUTING.md`
- [ ] Create `zlsp/Documentation/CHANGELOG.md`
- [ ] Update `zlsp/Documentation/ARCHITECTURE.md` with refactored structure
- [ ] Add docstrings to all public functions (Google style)
- [ ] Add type hints to all functions (PEP 484)

#### 4.2 API Documentation
- [ ] Create `zlsp/Documentation/API_REFERENCE.md`
- [ ] Document `load()`, `loads()`, `dump()`, `dumps()` API
- [ ] Document `tokenize()` API
- [ ] Document theme system API
- [ ] Add code examples for each API

#### 4.3 Developer Guides
- [ ] Create `zlsp/Documentation/PARSER_GUIDE.md`
- [ ] Create `zlsp/Documentation/THEME_GUIDE.md`
- [ ] Create `zlsp/Documentation/TESTING_GUIDE.md`
- [ ] Document adding new file types
- [ ] Document adding new token types

---

### **Phase 5: Testing & Quality** (Priority: 🔶 High)

#### 5.1 Test Coverage
- [ ] Add tests for all zSchema features
- [ ] Add tests for all zUI features
- [ ] Add tests for all zEnv features
- [ ] Add tests for all zSpark features
- [ ] Add tests for all zConfig features
- [ ] Move example files to `tests/fixtures/`
- [ ] Achieve 90%+ code coverage

#### 5.2 Linting & Type Checking
- [ ] Configure `ruff` in `pyproject.toml`
- [ ] Configure `mypy` in `mypy.ini`
- [ ] Configure `black` formatting
- [ ] Add pre-commit hooks (optional)
- [ ] Fix all linting errors
- [ ] Fix all type checking errors
- [ ] Add CI/CD linting checks (future)

#### 5.3 Performance
- [ ] Add benchmark tests for large files
- [ ] Profile `tokenize()` hot paths
- [ ] Optimize block tracking lookups
- [ ] Optimize token emission
- [ ] Document performance characteristics

---

### **Phase 6: Package Quality** (Priority: 🟡 Medium)

#### 6.1 Dependency Management
- [ ] Review all dependencies (minimize)
- [ ] Add optional dependencies for dev tools
- [ ] Create `requirements.txt` for pip users
- [ ] Add `uv.lock` for modern users
- [ ] Document dependency rationale

#### 6.2 Build & Distribution
- [ ] Test `pip install -e .` (editable install)
- [ ] Test `pip install .` (normal install)
- [ ] Test `pip install git+https://...` (GitHub install)
- [ ] Verify all entry points work
- [ ] Verify all package data included
- [ ] Test on Python 3.8, 3.9, 3.10, 3.11, 3.12

#### 6.3 Error Handling
- [ ] Review all exception types
- [ ] Add context to error messages
- [ ] Add error recovery where possible
- [ ] Document error handling patterns
- [ ] Add error examples to docs

---

### **Phase 7: Advanced Features** (Priority: 🟢 Low - Post-Refactor)

#### 7.1 LSP Features
- [ ] Implement go-to-definition
- [ ] Implement find references
- [ ] Implement rename refactoring
- [ ] Implement code actions
- [ ] Implement formatting

#### 7.2 Parser Features
- [ ] Add incremental parsing (for large files)
- [ ] Add syntax tree caching
- [ ] Add partial error recovery
- [ ] Add better multiline support

---

## 🎯 Success Metrics

### Code Quality
- [ ] `parser.py` < 2,000 lines (from 3,419)
- [ ] No function > 100 lines
- [ ] No class > 500 lines
- [ ] 90%+ test coverage
- [ ] 0 linting errors
- [ ] 0 type checking errors

### Documentation
- [ ] All public APIs documented
- [ ] All guides complete
- [ ] AI Agent Guide created
- [ ] Examples for all features

### Performance
- [ ] Parse 1,000 line file < 100ms
- [ ] Tokenize 1,000 line file < 50ms
- [ ] LSP response time < 100ms

### Package
- [ ] Clean install on all Python versions
- [ ] All entry points functional
- [ ] No unnecessary dependencies
- [ ] Clear error messages

---

## 📅 Estimated Timeline

| Phase | Priority | Estimated Time | Dependencies |
|-------|----------|----------------|--------------|
| Phase 1 | 🔥 Critical | 2-3 hours | None |
| Phase 2 | 🔥 Critical | 8-12 hours | Phase 1 |
| Phase 3 | 🔶 High | 4-6 hours | Phase 1 |
| Phase 4 | 🔶 High | 6-8 hours | Phase 2 |
| Phase 5 | 🔶 High | 6-8 hours | Phase 2 |
| Phase 6 | 🟡 Medium | 4-6 hours | Phase 1-5 |
| Phase 7 | 🟢 Low | Future | All above |

**Total Estimated Time:** 30-43 hours (excluding Phase 7)

---

## 🚀 Execution Strategy

### Approach: **Incremental Refactoring**
- ✅ Each phase can be committed independently
- ✅ Tests pass after each phase
- ✅ No breaking changes to public API
- ✅ Backward compatibility maintained

### Order of Execution:
1. **Phase 1** (Cleanup) - Quick wins, sets foundation
2. **Phase 2** (Parser) - Core refactoring, biggest impact
3. **Phase 3** (Themes) - Enhance existing system
4. **Phase 4** (Docs) - Document refactored code
5. **Phase 5** (Tests) - Validate everything works
6. **Phase 6** (Package) - Polish for distribution
7. **Phase 7** (Advanced) - Future enhancements

### Commit Strategy:
- Commit after each sub-phase (e.g., 2.1, 2.2, etc.)
- Use conventional commits: `refactor(parser): extract block tracking system`
- Tag major milestones: `v1.1.0-refactor-phase2`

---

## 🔍 Key Refactoring Patterns

### 1. **Strategy Pattern** (Key Detectors)
```python
# Before: Giant if-elif chain
if is_zspark_file and key == 'zSpark':
    return TokenType.ZSPARK_KEY
elif is_zenv_file and key in ('DEPLOYMENT', 'DEBUG'):
    return TokenType.ZENV_CONFIG_KEY
# ... 50+ more conditions

# After: Strategy pattern
detector = key_detector_registry.get_detector(file_type)
return detector.detect_token_type(key, context)
```

### 2. **Registry Pattern** (Block Tracking)
```python
# Before: 17+ separate lists
self.zrbac_blocks = []
self.zimage_blocks = []
self.ztext_blocks = []
# ... 14 more

# After: Unified registry
self.block_tracker = BlockTracker()
self.block_tracker.enter_block('zRBAC', indent, line)
```

### 3. **Command Pattern** (Token Emission)
```python
# Before: 197-line function with complex branching
def _emit_value_tokens(value, line, pos, emitter, type_hint, key):
    if is_number(value):
        # ... 30 lines
    elif is_boolean(value):
        # ... 20 lines
    # ... 10+ more branches

# After: Command pattern
emitter = value_token_emitter_factory.create(value_type)
emitter.emit(value, line, pos, context)
```

---

## 📚 References

### Industry Standards (from zKernel)
- ✅ Layer-based architecture (L0-L4)
- ✅ Comprehensive documentation (20+ guides)
- ✅ AI Agent Guide for LLM assistants
- ✅ `version.py` for version management
- ✅ `mypy.ini` for type checking
- ✅ Clean package structure
- ✅ Extensive test coverage

### Best Practices
- **Single Responsibility Principle** - Each module does one thing
- **Open/Closed Principle** - Open for extension, closed for modification
- **DRY Principle** - Don't Repeat Yourself
- **KISS Principle** - Keep It Simple, Stupid
- **YAGNI Principle** - You Aren't Gonna Need It

---

## ✅ Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize phases** based on immediate needs
3. **Start with Phase 1** (quick cleanup)
4. **Commit incrementally** after each sub-phase
5. **Document as you go** (don't defer docs)

---

**Status:** Ready for execution  
**Last Updated:** 2026-01-13  
**Version:** 1.0
