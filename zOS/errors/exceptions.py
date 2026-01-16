"""
zOS/errors/exceptions.py

OS-level exceptions for Zolo applications.

This file contains ONLY OS-level exceptions that are independent of the zKernel framework.
Framework-specific exceptions have been extracted to @temp_zKernel/errors/exceptions.py.

These exceptions do NOT depend on zKernel framework components and can be used
by any Zolo application (zlsp, zOS tools, standalone utilities, etc.).
"""


class zMachinePathError(Exception):
    """Raised when zMachine path resolution fails or file not found (OS-level)."""

    def __init__(self, zpath: str, resolved_path: str, context_type: str = "file"):
        """
        Initialize zMachine path error.
        
        Args:
            zpath: The zMachine path that failed
            resolved_path: The OS-level resolved path
            context_type: "file" or "syntax"
        """
        # Import inline to avoid loading unless needed (not in centralized imports)
        import platform
        os_name = platform.system()

        if context_type == "file":
            hint = (
                f"File not found at zMachine path.\n\n"
                f"Resolution on {os_name}:\n"
                f"   {zpath}\n"
                f"   -> {resolved_path}\n\n"
                f"Options:\n"
                f"   1. Create the file at the resolved path\n"
                f"   2. Use workspace path instead: '@.zSchema.users'\n"
                f"   3. Use absolute path: '~./path/to/file'\n\n"
                f"Platform-Specific Paths:\n"
                f"   - macOS: ~/Library/Application Support/zolo-zcli/...\n"
                f"   - Linux: ~/.local/share/zolo-zcli/...\n"
                f"   - Windows: %LOCALAPPDATA%\\zolo-zcli\\...\n\n"
                f"When to use zMachine:\n"
                f"   YES: User data that should persist across projects\n"
                f"   YES: Global configuration files\n"
                f"   YES: Cross-platform compatible storage\n"
                f"   NO: Project-specific data (use '@' instead)"
            )
        else:  # syntax error
            hint = (
                f"zMachine syntax depends on context:\n\n"
                f"In zSchema Data_Path (NO dot):\n"
                f"   Meta:\n"
                f"     Data_Path: \"zMachine\"  # Correct\n"
                f"     # NOT: \"zMachine.\" (wrong)\n\n"
                f"In zVaFile references (WITH dot):\n"
                f"   zVaFile: \"zMachine.zSchema.users\"  # Correct\n"
                f"   # Also valid: \"~.zMachine.zSchema.users\"\n\n"
                f"Your OS resolves zMachine to:\n"
                f"   {resolved_path}"
            )
        
        message = f"zMachine path error: {zpath}\nHINT: {hint}"
        super().__init__(message)
        
        # Store context for programmatic access
        self.zpath = zpath
        self.resolved_path = resolved_path
        self.os_name = os_name
        self.context_type = context_type


class UnsupportedOSError(Exception):
    """Raised when Zolo applications are run on an unsupported operating system."""

    def __init__(self, os_type: str, valid_types: tuple = ("Linux", "Darwin", "Windows")):
        """
        Initialize unsupported OS error.
        
        Args:
            os_type: The detected OS type (from platform.system())
            valid_types: Tuple of supported OS types
        """
        hint = (
            f"Zolo applications only support Linux, macOS (Darwin), and Windows.\n\n"
            f"Your OS: {os_type}\n"
            f"Supported: {', '.join(valid_types)}\n\n"
            f"What to do:\n"
            f"   1. If you're on a compatible OS but seeing this, it may be a detection issue\n"
            f"   2. Check that platform.system() returns the correct value\n"
            f"   3. Report this issue: https://github.com/zolo-ai/issues\n"
            f"   4. Consider contributing OS support for your platform"
        )

        message = f"Unsupported operating system: {os_type}\nHINT: {hint}"
        super().__init__(message)
        
        # Store context for programmatic access
        self.os_type = os_type
        self.valid_types = valid_types
