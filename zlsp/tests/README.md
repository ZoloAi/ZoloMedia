# zlsp Test Suite

Comprehensive testing for the Zolo Language Server Protocol implementation.

## Test Structure

```
tests/
├── unit/           # Unit tests (fast, isolated)
├── integration/    # Integration tests (components together)
├── e2e/            # End-to-end tests (full workflows)
├── conftest.py     # Pytest configuration & fixtures
└── README.md       # This file
```

## Test Levels

### 🧪 Unit Tests (`tests/unit/`)

**Purpose:** Test individual components in isolation  
**Speed:** Very fast (~1-5ms per test)  
**Coverage Goal:** 90%+

**What to test:**
- Parser functions (`load`, `loads`, `dump`, `dumps`)
- Type hint processing
- Token encoding/decoding
- Individual providers

**Example:**
```python
def test_parse_simple_key_value():
    """Test parsing a single key-value pair."""
    data = loads("name: John")
    assert data == {"name": "John"}
```

### 🔗 Integration Tests (`tests/integration/`)

**Purpose:** Test multiple components working together  
**Speed:** Medium (~10-100ms per test)

**What to test:**
- Parser → Semantic tokenizer flow
- LSP protocol request/response
- Providers using parser output
- Error handling across components

**Example:**
```python
def test_parser_to_semantic_tokens_flow():
    """Test complete flow from parsing to semantic tokens."""
    result = tokenize(content)
    encoded = encode_semantic_tokens(result.tokens)
    assert len(encoded) % 5 == 0  # LSP format
```

### 🎯 End-to-End Tests (`tests/e2e/`)

**Purpose:** Test complete user workflows  
**Speed:** Slower (~100ms-1s per test)

**What to test:**
- Complete LSP server lifecycle
- Real file I/O
- Full semantic token workflow
- Diagnostics workflow
- Round-trip parsing

**Example:**
```python
def test_semantic_tokens_full_workflow():
    """Test complete semantic tokens workflow from user perspective."""
    # Parse file
    # Generate tokens
    # Encode for LSP
    # Verify output
```

### 🖼️ Visual Regression Tests (`tests/visual/`)

**Purpose:** Test cross-editor visual consistency  
**Speed:** Very slow (~2min for all 7 files)

**What to test:**
- Vim vs VS Code pixel-perfect rendering
- Semantic token color consistency
- LSP highlight accuracy
- Editor adapter correctness

**Example:**
```python
@pytest.mark.visual
@pytest.mark.slow
def test_vscode_matches_vim_baseline():
    """Test that VS Code renders identically to Vim."""
    # Capture Vim golden baseline
    # Capture VS Code screenshot
    # Compare pixel-by-pixel
    # Generate diff report if mismatch
```

**Running Visual Tests:**
```bash
# Capture golden baselines (first time)
pytest tests/visual/ --capture-golden

# Run visual tests
zlsp test --visual

# Update baselines after theme changes
pytest tests/visual/ --update-golden

# Skip visual tests
zlsp test --quick  # or pytest -m "not visual"
```

**See:** [tests/visual/README.md](visual/README.md) for detailed documentation

## Running Tests

### Run All Tests
```bash
zlsp test                  # Full suite (unit + integration + e2e + visual)
```

### Run Specific Test Level
```bash
zlsp test --quick          # Quick tests (unit + integration, skip slow)
zlsp test --unit           # Unit tests only (fastest)
zlsp test --integration    # Integration tests only
zlsp test --e2e            # End-to-end tests only
zlsp test --visual         # Visual regression tests only (slowest)
```

### Run with Coverage
```bash
zlsp test --coverage       # Coverage report (terminal + HTML)
zlsp test --quick --coverage  # Coverage for quick tests only
```

### Run Specific Test
```bash
zlsp test -k test_parser   # Run tests matching "test_parser"
zlsp test -k "test_type"   # Run tests matching "test_type"
zlsp test -x               # Stop on first failure (fail-fast)
```

### Verbose Output
```bash
zlsp test -v               # Verbose output
zlsp test -vv              # Very verbose output
```

### Skip Visual Tests
```bash
# Run all except visual (for CI or quick validation)
pytest tests -m "not visual" -v
```

## Writing Tests

### Test File Naming
- `test_*.py` - Test files must start with `test_`
- `*_test.py` - Or end with `_test.py`
- Test functions: `def test_*():`

### Using Fixtures

```python
def test_with_fixture(sample_zolo_content):
    """Use shared fixtures from conftest.py"""
    result = loads(sample_zolo_content)
    assert result is not None
```

### Available Fixtures
- `temp_zolo_file` - Creates temporary .zolo file
- `sample_zolo_content` - Sample valid content
- `invalid_zolo_content` - Sample invalid content

### Test Markers

```python
@pytest.mark.unit
def test_unit_test():
    """Mark as unit test."""
    pass

@pytest.mark.integration
def test_integration_test():
    """Mark as integration test."""
    pass

@pytest.mark.e2e
def test_e2e_test():
    """Mark as end-to-end test."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Mark tests that are slow."""
    pass

@pytest.mark.visual
@pytest.mark.slow  # Visual tests are always slow
def test_visual_regression():
    """Mark as visual regression test."""
    pass
```

## Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Parser | 95%+ |
| Type Hints | 90%+ |
| Semantic Tokenizer | 90%+ |
| Providers | 85%+ |
| LSP Server | 80%+ |

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run unit tests
  run: zlsp test --unit

- name: Run integration tests
  run: zlsp test --integration

- name: Run e2e tests
  run: zlsp test --e2e --coverage
```

## Test Philosophy

1. **Fast feedback** - Unit tests should be very fast
2. **Isolated** - Tests should not depend on each other
3. **Clear names** - Test names describe what they test
4. **Arrange-Act-Assert** - Standard test structure
5. **One assertion per test** - When possible

## Debugging Tests

### Run single test with output
```bash
zlsp test -k test_parser -v -s
```

### Use pytest directly for more control
```bash
cd tests
pytest unit/test_parser.py::test_loads_string_first -vv
```

### Add breakpoints
```python
def test_something():
    result = function_under_test()
    breakpoint()  # Drops into debugger
    assert result == expected
```

## Contributing

When adding new features:
1. Write unit tests first (TDD)
2. Add integration tests for component interaction
3. Add e2e test for user-facing workflow
4. Ensure all tests pass: `zlsp test`
5. Check coverage: `zlsp test --coverage`

## Test Execution Matrix

| Command | Unit | Integration | E2E | Visual | Time | Use Case |
|---------|------|-------------|-----|--------|------|----------|
| `zlsp test --quick` | ✅ | ✅ | ❌ | ❌ | ~5s | Dev loop |
| `zlsp test --unit` | ✅ | ❌ | ❌ | ❌ | <1s | TDD |
| `pytest -m "not visual"` | ✅ | ✅ | ✅ | ❌ | ~15s | Pre-commit |
| `zlsp test` | ✅ | ✅ | ✅ | ✅ | ~3min | Full validation |
| `zlsp test --visual` | ❌ | ❌ | ❌ | ✅ | ~2min | Theme changes |

## Future Test Enhancements

### ✅ Editor Integration Testing (IMPLEMENTED)

**Visual Regression Testing** - Pixel-perfect cross-editor consistency:
- ✅ **Implemented**: `tests/visual/` directory
- ✅ **Vim Driver**: Real Terminal.app screenshot capture
- ✅ **VS Code Driver**: Window screenshot capture
- ✅ **Image Comparison**: Pixel-by-pixel diff with visual reports
- ✅ **Golden Baselines**: Vim as single source of visual truth
- ✅ **Commands**: `zlsp test --visual`

**See:** [tests/visual/README.md](visual/README.md) for detailed documentation

### Future Enhancements

**Additional Editor Support**:
- [ ] Emacs visual regression tests
- [ ] Neovim visual regression tests (separate from Vim)
- [ ] Sublime Text visual regression tests
- [ ] IntelliJ IDEA visual regression tests

**Advanced Visual Testing**:
- [ ] Semantic token animation testing (colors update during typing)
- [ ] Performance profiling (LSP latency impact)
- [ ] Color accessibility testing (WCAG contrast ratios)
- [ ] Visual fuzzing (random .zolo files)

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [LSP specification](https://microsoft.github.io/language-server-protocol/)
- [zlsp architecture](../Documentation/ARCHITECTURE.md)
- [Vim testing approaches](https://vimways.org/2019/writing-vim-plugin-tests/)