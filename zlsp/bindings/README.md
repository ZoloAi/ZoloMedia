# zlsp Language Bindings

**SDKs for different programming languages**

Each language gets its own subfolder with a complete SDK that wraps the core zlsp implementation.

## Structure

```
bindings/
├── python/     # Python SDK ✅ COMPLETE
│   ├── zlsp/              # Python package
│   ├── setup.py           # Python build
│   └── README.md
│
├── cpp/        # C++ SDK (future)
│   ├── include/
│   ├── src/
│   └── CMakeLists.txt
│
├── java/       # Java SDK (future)
│   ├── src/
│   └── pom.xml
│
└── rust/       # Rust SDK (future)
    ├── src/
    └── Cargo.toml
```

## Current Status

### ✅ Python (Complete)
- Full parser API: `load()`, `loads()`, `dump()`, `dumps()`
- Type hint processing
- Exception handling
- Well-documented

### 🔜 C++ (Planned)
- C++ wrapper using Python C API
- CMake build system
- Header-only option

### 🔜 Java (Planned)
- JNI wrapper
- Maven/Gradle support
- Native feel

### 🔜 Rust (Planned)
- PyO3 bindings
- Cargo integration
- Zero-cost abstractions

## Design Philosophy

1. **Thin wrappers** - Each binding is a thin layer over core/
2. **Native feel** - Follow language idioms (snake_case vs camelCase, etc.)
3. **Build system** - Use standard tools (pip, CMake, Maven, Cargo)
4. **Extractable** - Each can become standalone repo

## Adding a New Language

1. Create `bindings/yourlang/` folder
2. Set up build system (setup.py, CMakeLists.txt, etc.)
3. Wrap core/ functions with language-native API
4. Add tests
5. Document in README.md

See `bindings/python/` as a reference implementation.
