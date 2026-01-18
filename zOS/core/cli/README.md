# CLI Module - Modular Argument Parsing

This directory contains the modular CLI argument parsing system for zOS. Each command has its own file, making it easy to add, modify, or maintain commands independently.

## Architecture

```
cli/
├── __init__.py           # Main parser factory & coordination
├── README.md             # This file
├── shell_args.py         # 'shell' command arguments
├── config_args.py        # 'config' command arguments
├── ztests_args.py        # 'ztests' command arguments
├── migrate_args.py       # 'migrate' command arguments
└── uninstall_args.py     # 'uninstall' command arguments
```

## Design Philosophy

### Modular by Command
Each command is defined in its own file with a consistent interface. This:
- **Scales** - Easy to add new commands without bloating a single file
- **Clear ownership** - Each command's arguments are self-contained
- **Easy maintenance** - Changes to one command don't affect others
- **Team-friendly** - Multiple devs can work on different commands simultaneously

### Consistent Interface
Every command module exports a single function:

```python
def add_subparser(subparsers) -> argparse.ArgumentParser:
    """Add this command's subparser to the main parser."""
    parser = subparsers.add_parser("command_name", ...)
    # Add command-specific arguments
    return parser
```

## Adding a New Command

1. **Create a new file**: `cli/my_command_args.py`

```python
"""
My Command Arguments

Defines CLI arguments for the 'my-command' command.
"""

import argparse


def add_subparser(subparsers) -> argparse.ArgumentParser:
    """
    Add the 'my-command' subcommand to the parser.
    
    Args:
        subparsers: The subparsers object from ArgumentParser
        
    Returns:
        The created my-command subparser
    """
    parser = subparsers.add_parser(
        "my-command",
        help="Short help text",
        description="Longer description of what this command does"
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "--my-flag",
        action="store_true",
        help="Description of my flag"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show bootstrap process and detailed initialization"
    )
    
    return parser
```

2. **Register the module** in `cli/__init__.py`:

```python
# Add import at the top
from . import my_command_args

# Add to create_parser() function
def create_parser(version: str) -> argparse.ArgumentParser:
    # ... existing code ...
    
    # Add to subparser registration
    my_command_args.add_subparser(subparsers)  # ← Add this line
    
    return parser
```

3. **Add command handler** in `zSys/cli/cli_commands.py`

4. **Register handler** in `main.py`:

```python
handlers = {
    # ... existing handlers ...
    "my-command": lambda: cli_commands.handle_my_command(boot_logger, verbose=verbose),
}
```

## Best Practices

### 1. Always Include --verbose
Every command should support the `--verbose` flag for debugging:

```python
parser.add_argument(
    "--verbose", "-v",
    action="store_true",
    help="Show bootstrap process and detailed initialization"
)
```

### 2. Clear Help Text
- **help**: Short one-line summary (appears in main help)
- **description**: Longer explanation (appears in command-specific help)

```python
parser = subparsers.add_parser(
    "migrate",
    help="Run schema migrations",  # Short - for main help
    description="Execute database schema migrations for zOS applications"  # Long - for 'zolo migrate --help'
)
```

### 3. Argument Naming Conventions
- Use `--kebab-case` for multi-word options
- Provide short forms for common options: `-v` for `--verbose`
- Use `action="store_true"` for boolean flags
- Use meaningful argument names that match their purpose

### 4. Organize Arguments Logically
Group related arguments together and add comments:

```python
# Required arguments
parser.add_argument("app_file", help="...")

# Migration control
parser.add_argument("--dry-run", ...)
parser.add_argument("--auto-approve", ...)

# Debug options
parser.add_argument("--verbose", ...)
```

### 5. Future-Proof Design
Add comments for future arguments that might be added:

```python
# Future test-specific arguments:
# parser.add_argument("--suite", help="Specific test suite to run")
# parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
```

## Testing Your Changes

After modifying or adding commands, test thoroughly:

```bash
# Test main help
zolo --help

# Test command-specific help
zolo my-command --help

# Test actual command execution
zolo my-command --my-flag --verbose
```

## Migration from Monolithic Parser

**Before** (old approach in main.py):
- Single `_create_parser()` function with 100+ lines
- All commands mixed together
- Hard to navigate and maintain

**After** (current modular approach):
- Separate file per command (~30-40 lines each)
- Clear structure and ownership
- Easy to find and modify specific commands

## Benefits for zOS Growth

As zOS adds more commands (data operations, deployment, testing, monitoring, etc.), this structure ensures:

1. **Scalability**: Can have 50+ commands without chaos
2. **Team collaboration**: No merge conflicts on a single huge file
3. **Discoverability**: New devs can find command definitions easily
4. **Maintainability**: Changes are isolated and testable
5. **Documentation**: Each file is self-documenting

## Examples in the Wild

This pattern is used by major CLI tools:
- **AWS CLI**: Hundreds of commands, all modular
- **kubectl**: ~70 commands, separate definitions
- **cargo**: Modular command system with plugins
- **poetry**: Clean separation of command concerns

---

**Last Updated**: 2026-01-18  
**Architecture Version**: 1.0  
**Maintainer**: zOS Core Team
