# Error Messages & Recovery Guide

This guide explains Zolo LSP error messages and how to fix them.

## 🎯 Error Message Philosophy

Zolo LSP error messages are designed to be:
- **Clear**: Plain English, no technical jargon
- **Specific**: Include line numbers and context
- **Actionable**: Suggest fixes and show examples
- **Educational**: Help you learn the Zolo format

---

## Common Errors & Solutions

### 1. Duplicate Key Error

**Error:**
```
Duplicate key 'port' at line 15.
This key already exists at line 10: 'port'

Keys must be unique at each level. To fix this:
  1. Rename one of the keys (e.g., 'port_2' or 'port_alt')
  2. Move the duplicate under a different parent
  3. Remove the duplicate if it's unintentional
```

**Cause:** You've defined the same key twice at the same nesting level.

**Solution:**
```zolo
# ❌ Wrong:
server:
  port: 8080
  host: localhost
  port: 9000  # Duplicate!

# ✅ Correct (different names):
server:
  port: 8080
  backup_port: 9000
  host: localhost

# ✅ Correct (different levels):
server:
  port: 8080
  backup:
    port: 9000
```

---

### 2. Inconsistent Indentation

**Error:**
```
Inconsistent indentation at line 12.
This file uses spaces (first seen at line 5), but this line uses tabs.

To fix this:
  1. Use spaces for all indentation in this file
  2. Configure your editor to insert spaces when you press Tab

Editor config examples:
  • Vim: set expandtab
  • VS Code: "editor.insertSpaces": true
```

**Cause:** Mixing tabs and spaces for indentation.

**Solution:** Choose one and stick with it (spaces recommended):

```zolo
# ✅ All spaces (recommended):
server:
  port: 8080
  database:
    host: localhost

# ❌ Mixed (tabs + spaces) - will cause errors:
server:
→→port: 8080           # Tab
  database:            # Spaces
    host: localhost
```

**Editor Setup:**
- **Vim/Neovim**: Add to `.vimrc`: `set expandtab tabstop=2 shiftwidth=2`
- **VS Code**: Set `"editor.insertSpaces": true` and `"editor.tabSize": 2`

---

### 3. Invalid Value Error (with "Did you mean?")

**Error:**
```
Invalid value for 'zMode' at line 8: 'Termina'
Valid options: Terminal, zBifrost

Did you mean: 'Terminal'?
```

**Cause:** Typo in a special value (zMode, deployment, logger, etc.).

**Solution:** Use one of the valid values:

```zolo
# ❌ Wrong (typo):
zMode: Termina

# ✅ Correct:
zMode: Terminal
```

**Special Values:**
- **zMode**: `Terminal` or `zBifrost`
- **deployment**: `Production` or `Development`
- **logger**: `DEBUG`, `SESSION`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `PROD`

---

### 4. Non-ASCII Character Error

**Error:**
```
Non-ASCII character '♥' detected at line 5.
Unicode: U+2764 (HEAVY BLACK HEART)

RFC 8259 requires ASCII-only. Use Unicode escape instead:
  \u2764

Hint: Copy the escape sequence above and replace the character.
      This teaches you the RFC 8259 compliant format!
```

**Cause:** Using emojis, accented letters, or other non-ASCII characters directly.

**Solution:** Use Unicode escape sequences:

```zolo
# ❌ Wrong (direct emoji):
icon: ♥️

# ✅ Correct (Unicode escape):
icon: \u2764\uFE0F

# ❌ Wrong (accented character):
name: café

# ✅ Correct (Unicode escapes):
name: caf\u00E9
```

---

### 5. Type Mismatch Error

**Error:**
```
Type mismatch for key 'port' at line 10.
Expected int, got: 'abc123'

Hint: Integer values should be whole numbers without quotes.
  Example: port: 8080
```

**Cause:** Wrong data type for a type-hinted value.

**Solution:** Provide the correct type:

```zolo
# ❌ Wrong types:
port(int): abc123         # Not a number
timeout(float): yes       # Not a float
enabled(bool): 1          # Should be true/false

# ✅ Correct types:
port(int): 8080
timeout(float): 30.5
enabled(bool): true
```

---

### 6. Parsing Error

**Error:**
```
Parsing error at line 12, column 5: Missing colon after key

Problematic content:
  database

Common causes:
  • Missing colon after key name
  • Unmatched brackets or braces
  • Invalid characters in key names
  • Incorrect indentation
```

**Cause:** Syntax error in `.zolo` file.

**Solution:** Check for common issues:

```zolo
# ❌ Missing colon:
server
  port: 8080

# ✅ Correct:
server:
  port: 8080

# ❌ Unmatched brackets:
items: [1, 2, 3

# ✅ Correct:
items: [1, 2, 3]

# ❌ Invalid key characters:
my-key!: value

# ✅ Correct (use underscores):
my_key: value
```

---

### 7. File Not Found

**Error:**
```
File not found: /path/to/config.zolo

Please check:
  1. The file path is correct
  2. The file exists at this location
  3. You have permission to read the file
  4. The file extension is .zolo or .json
```

**Solution:**
- Verify the file path is correct
- Check file permissions
- Ensure the file has the correct extension (`.zolo` or `.json`)

---

### 8. Unsupported File Extension

**Error:**
```
Unsupported file extension: .txt
Supported formats: .zolo, .json

To use your file:
  1. Save it with a supported extension (e.g., .zolo)
  2. Or convert the file to a supported format
```

**Solution:** Save your file with a `.zolo` or `.json` extension:

```bash
# Rename file:
mv config.txt config.zolo

# Or create new file:
touch myconfig.zolo
```

---

## 💡 General Tips

### 1. Start Simple
When you get an error, simplify your file to find the issue:
```zolo
# Start with this:
key: value

# Then gradually add complexity:
key: value
nested:
  child: value
```

### 2. Check Indentation Visually
Enable visible whitespace in your editor:
- **Vim**: `:set list listchars=tab:→\ ,space:·`
- **VS Code**: View → Toggle Render Whitespace

### 3. Use Type Hints for Clarity
Type hints prevent ambiguity:
```zolo
port(int): 8080          # Clearly an integer
version(str): 1.2.3      # Clearly a string
enabled(bool): true      # Clearly a boolean
```

### 4. Validate Early, Validate Often
Run the LSP or parser frequently to catch errors early:
```bash
# Test your file:
python -m zlsp.core.parser your_file.zolo
```

### 5. Read the Full Error Message
Error messages include:
- **Location**: Line and column numbers
- **Cause**: What went wrong
- **Solution**: How to fix it
- **Examples**: Correct usage

---

## 🚀 Error Prevention

### Best Practices

1. **Consistent Formatting**
   - Use 2-space indentation
   - No tabs
   - No trailing whitespace

2. **Clear Key Names**
   - Use snake_case: `my_key` not `my-key` or `myKey`
   - Avoid special characters
   - Keep names descriptive

3. **Type Everything Important**
   - Add type hints to critical values
   - Prevents ambiguity
   - Self-documenting

4. **Test Incrementally**
   - Add a few lines
   - Test
   - Repeat

5. **Use Comments for Clarity**
   ```zolo
   # Full-line comment
   key: value  #> inline comment <#
   ```

---

## 🛠️ Debugging Tips

### When You're Stuck

1. **Isolate the Problem**
   - Comment out sections to find the error
   - Test each section independently

2. **Check the Basics**
   - Missing colons?
   - Correct indentation?
   - Valid characters?
   - Proper nesting?

3. **Compare with Examples**
   - Look at `zlsp/examples/` for correct syntax
   - Copy working examples and modify them

4. **Read Error Messages Carefully**
   - Line numbers are 1-based
   - Error messages show the exact problem
   - Suggestions are usually correct

---

## 📚 Additional Resources

- **Examples**: See `zlsp/examples/` for working `.zolo` files
- **Syntax Guide**: See `zlsp/Documentation/QUICKSTART.md`
- **Architecture**: See `zlsp/Documentation/ARCHITECTURE.md`
- **Integration**: See `zlsp/Documentation/INTEGRATION_GUIDE.md`

---

## 💬 Need Help?

If you're still stuck:
1. Check the error message again (really read it!)
2. Look at similar examples in `zlsp/examples/`
3. Simplify your file to the minimal case that fails
4. Check your editor's indentation settings

Remember: Error messages are here to help! They include everything you need to fix the problem.
