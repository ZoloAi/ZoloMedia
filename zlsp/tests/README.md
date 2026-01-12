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

## Running Tests

### Run All Tests
```bash
zlsp test
```

### Run Specific Test Level
```bash
zlsp test --unit           # Fast unit tests only
zlsp test --integration    # Integration tests only
zlsp test --e2e            # End-to-end tests only
```

### Run with Coverage
```bash
zlsp test --coverage       # Shows coverage report
```

### Run Specific Test
```bash
zlsp test -k test_parser   # Run tests matching "test_parser"
zlsp test -k "test_type"   # Run tests matching "test_type"
```

### Verbose Output
```bash
zlsp test -v               # Verbose output
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
@pytest.mark.slow
def test_slow_operation():
    """Mark tests that are slow."""
    pass

@pytest.mark.unit
def test_unit_test():
    """Mark as unit test."""
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

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [LSP specification](https://microsoft.github.io/language-server-protocol/)
- [zlsp architecture](../Documentation/ARCHITECTURE.md)
