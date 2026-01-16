# zOS PyPI Publishing Plan

**Status**: 🚧 Pre-Publishing Cleanup  
**Current Version**: 1.0.0  
**Target**: PyPI Publication + zlsp Update (1.0.1 → 1.0.3)

---

## 📋 **Phase 1: Code Cleanup & Organization**

### **1.1 Remove Build Artifacts**
- [ ] Remove all `__pycache__` directories
- [ ] Remove `.pyc` files
- [ ] Remove `zOS.egg-info` directory
- [ ] Remove `.DS_Store` files (macOS)
- [ ] Add comprehensive `.gitignore`

**Commands:**
```bash
cd zOS
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name ".DS_Store" -delete
rm -rf zOS.egg-info/
```

### **1.2 Fix Package Structure**
Current Issues:
- `pyproject.toml` line 44: `package-dir = {"zOS" = "."}` ← Flat structure
- `pyproject.toml` line 45: Manually listed packages (should use find)
- Missing `zOS.utils.open` in package list

**Fix:**
```toml
[tool.setuptools]
package-dir = {"zOS" = "."}
packages = [
    "zOS",
    "zOS.cli",
    "zOS.errors",
    "zOS.formatting",
    "zOS.install",
    "zOS.logger",
    "zOS.machine",
    "zOS.machine.detectors",
    "zOS.utils",
    "zOS.utils.open",
]
```

Or use automatic discovery:
```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["zOS*"]
exclude = ["tests*", "docs*"]
```

### **1.3 Update Dependencies**
Current in `pyproject.toml`:
```toml
dependencies = [
    "platformdirs>=3.0.0",
    "PyYAML>=6.0",
]
```

**Action**: ✅ Dependencies are correct (no zlsp dependency!)

### **1.4 Fix Entry Points**
Current:
```toml
[project.scripts]
zolo = "zOS.cli.main:main"
zTests = "zOS.cli.main:ztests_main"
```

**Issue**: `ztests_main` doesn't exist (zKernel feature)

**Fix:**
```toml
[project.scripts]
zolo = "zOS.cli.main:main"
```

---

## 📋 **Phase 2: Documentation & Metadata**

### **2.1 Update README.md**
Current README needs:
- [ ] Installation instructions (`pip install zOS`)
- [ ] Quick start examples
- [ ] Link to ZoloMedia monorepo
- [ ] Feature highlights (machine detection, zolo open, etc.)
- [ ] License information

### **2.2 Add CHANGELOG.md**
Create `CHANGELOG.md`:
```markdown
# Changelog

## [1.0.0] - 2026-01-17

### Added
- Initial release of zOS (Zolo Operating System)
- Machine detection and configuration generation
- `zolo` CLI with machine config display
- `zolo open` command for files and URLs
- Cross-platform support (macOS, Linux, Windows)
- Auto-generates `zConfig.machine.zolo` on first run
- Logger ecosystem with bootstrap support
- Error handling and formatting utilities
```

### **2.3 Add LICENSE File**
- [ ] Create `LICENSE` file (MIT)
- [ ] Ensure all source files have license headers

### **2.4 Update pyproject.toml Metadata**
```toml
[project]
name = "zOS"
version = "1.0.0"
description = "Operating System primitives for the Zolo ecosystem - machine detection, file opening, and CLI utilities"
authors = [
    {name = "Gal Nachshon", email = "gal@zolo.media"}
]
maintainers = [
    {name = "Gal Nachshon", email = "gal@zolo.media"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
keywords = [
    "zOS",
    "zolo",
    "operating-system",
    "machine-detection",
    "cli",
    "utilities",
    "cross-platform",
    "configuration",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Shells",
    "Topic :: Utilities",
    "Operating System :: OS Independent",
    "Operating System :: MacOS",
    "Operating System :: POSIX :: Linux",
    "Operating System :: Microsoft :: Windows",
    "Environment :: Console",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/ZoloAi/ZoloMedia"
Documentation = "https://github.com/ZoloAi/ZoloMedia/tree/main/zOS"
Repository = "https://github.com/ZoloAi/ZoloMedia"
"Bug Tracker" = "https://github.com/ZoloAi/ZoloMedia/issues"
```

---

## 📋 **Phase 3: Testing & Validation**

### **3.1 Local Build Test**
```bash
cd zOS
python -m build
# Should create:
# - dist/zOS-1.0.0.tar.gz
# - dist/zOS-1.0.0-py3-none-any.whl
```

### **3.2 Local Install Test**
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows

# Install from wheel
pip install dist/zOS-1.0.0-py3-none-any.whl

# Test commands
zolo
zolo --version
zolo machine
zolo open --help

# Test import
python -c "from zOS.utils.open import open_file, open_url; print('Import OK')"

# Cleanup
deactivate
rm -rf test_env
```

### **3.3 Check Package Contents**
```bash
tar -tzf dist/zOS-1.0.0.tar.gz | head -50
# Verify all necessary files are included
```

---

## 📋 **Phase 4: PyPI Publishing (zOS)**

### **4.1 Test PyPI Upload (Recommended First)**
```bash
# Install twine if needed
pip install twine

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ zOS

# Verify it works
zolo --version
```

### **4.2 Production PyPI Upload**
```bash
# Upload to PyPI
python -m twine upload dist/*

# Test install from PyPI
pip install zOS

# Verify
zolo --version
```

---

## 📋 **Phase 5: zlsp Update (1.0.1 → 1.0.3)**

### **5.1 Verify zlsp Version**
```bash
cd zlsp
grep "__version__" core/version.py
# Should show: __version__ = "1.0.3"
```

### **5.2 Clean zlsp Build Artifacts**
```bash
cd zlsp
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name ".DS_Store" -delete
rm -rf dist/ build/ zlsp.egg-info/
```

### **5.3 Build zlsp**
```bash
cd zlsp
python -m build
# Creates:
# - dist/zlsp-1.0.3.tar.gz
# - dist/zlsp-1.0.3-py3-none-any.whl
```

### **5.4 Test zlsp Locally**
```bash
# Create test environment
python -m venv test_zlsp
source test_zlsp/bin/activate

# Install
pip install dist/zlsp-1.0.3-py3-none-any.whl

# Test
zlsp --version
zolo-lsp --help
python -c "from core.parser import ZoloParser; print('zlsp OK')"

# Cleanup
deactivate
rm -rf test_zlsp
```

### **5.5 Upload zlsp to PyPI**
```bash
cd zlsp
python -m twine upload dist/*
# This will update the existing zlsp package from 1.0.1 to 1.0.3
```

---

## 📋 **Phase 6: Post-Publishing**

### **6.1 Update Documentation**
- [ ] Update main README.md with PyPI install instructions
- [ ] Update zlsp README with version 1.0.3 notes
- [ ] Create release notes on GitHub

### **6.2 Test Installation**
```bash
# Fresh environment test
python -m venv fresh_test
source fresh_test/bin/activate

# Install both packages
pip install zlsp zOS

# Verify versions
pip list | grep -E "zlsp|zOS"
# Should show:
# zlsp    1.0.3
# zOS     1.0.0

# Test both
zolo --version
zlsp --version

# Cleanup
deactivate
rm -rf fresh_test
```

### **6.3 Tag Releases**
```bash
cd /Users/galnachshon/Projects/ZoloMedia

# Tag zOS release
git tag -a zOS-v1.0.0 -m "zOS v1.0.0: Initial PyPI release"

# Tag zlsp update
git tag -a zlsp-v1.0.3 -m "zlsp v1.0.3: PyPI update"

# Push tags
git push origin --tags
```

---

## 📋 **Phase 7: GitHub Release Notes**

### **7.1 Create zOS Release**
Create GitHub release with:
- Tag: `zOS-v1.0.0`
- Title: "zOS v1.0.0 - Initial Release"
- Body: Features, installation, usage examples
- Attach: `dist/zOS-1.0.0-py3-none-any.whl`

### **7.2 Create zlsp Release**
Create GitHub release with:
- Tag: `zlsp-v1.0.3`
- Title: "zlsp v1.0.3 - PyPI Update"
- Body: Changelog, bug fixes, improvements
- Attach: `dist/zlsp-1.0.3-py3-none-any.whl`

---

## ✅ **Checklist Summary**

### **Pre-Publishing (zOS)**
- [ ] Clean build artifacts
- [ ] Fix package discovery in pyproject.toml
- [ ] Remove invalid entry points (zTests)
- [ ] Add missing packages (zOS.utils.open, zOS.machine.detectors)
- [ ] Update README.md
- [ ] Add CHANGELOG.md
- [ ] Add LICENSE file
- [ ] Update metadata in pyproject.toml

### **Publishing (zOS)**
- [ ] Build package (`python -m build`)
- [ ] Test local install
- [ ] Upload to TestPyPI (optional but recommended)
- [ ] Upload to PyPI

### **zlsp Update**
- [ ] Verify version is 1.0.3
- [ ] Clean build artifacts
- [ ] Build package
- [ ] Test local install
- [ ] Upload to PyPI (updates from 1.0.1)

### **Post-Publishing**
- [ ] Test fresh install of both packages
- [ ] Create Git tags
- [ ] Create GitHub releases
- [ ] Update main README

---

## 🚨 **Common Issues & Solutions**

### **Issue 1: Package Not Found After Install**
**Cause**: Incorrect package structure in pyproject.toml  
**Fix**: Use `packages.find` instead of manual list

### **Issue 2: Module Import Errors**
**Cause**: Missing `__init__.py` files  
**Fix**: Ensure all directories have `__init__.py`

### **Issue 3: Version Mismatch**
**Cause**: Cached builds  
**Fix**: `rm -rf dist/ build/ *.egg-info/` before rebuilding

### **Issue 4: Twine Upload Fails**
**Cause**: Missing credentials or network issues  
**Fix**: Configure `~/.pypirc` or use `--repository` flag

---

## 📝 **Notes**

1. **zOS has NO dependency on zlsp** - They are independent packages ✅
2. **zlsp has NO dependency on zOS** - They are independent packages ✅
3. **Both can be installed separately** - Monorepo != single package
4. **Version numbers are independent** - zOS 1.0.0, zlsp 1.0.3

---

## 🎯 **Success Criteria**

✅ Users can `pip install zOS` and get working `zolo` CLI  
✅ Users can `pip install zlsp` and get v1.0.3 (updated from 1.0.1)  
✅ Both packages installable independently  
✅ Both packages work together in monorepo development  
✅ Clean, professional PyPI presence  

---

**Next Step**: Begin Phase 1 cleanup! 🚀
