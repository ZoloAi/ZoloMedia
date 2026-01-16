"""
@temp_zKernel/errors/exceptions.py

Framework exceptions extracted from zOS (OS primitives layer).

ORIGIN: zOS/errors/exceptions.py
STATUS: Staging for merge when zKernel joins monorepo
ACTION: DO NOT touch ~/Projects/Zolo/zKernel directly

This file contains 12+ framework-specific exceptions that depend on zKernel
framework components (zSchema, zUI, zData, zAuth, zDisplay, etc.).

These exceptions have hard dependencies on zKernel.zCLI and should NOT be
in the OS primitives layer.

TO MERGE LATER:
- Copy this file → ~/Projects/Zolo/zKernel/errors/exceptions.py (when copying zKernel to monorepo)
- These exceptions belong in the framework layer, not OS layer
"""


class zKernelException(Exception):
    """Base exception for all zKernel errors with actionable messages.
    
    Auto-registers with zTraceback when raised (Week 6.1.1).
    """

    def __init__(self, message: str, hint: str = None, context: dict = None):
        """Initialize with message, hint, and debug context."""
        self.hint = hint
        self.context = context or {}

        # Build full message with hint
        full_message = message
        if hint:
            full_message += f"\nHINT: {hint}"

        # Auto-register with zTraceback (Week 6.1.1)
        self._register_with_traceback(message)

        super().__init__(full_message)

    def _register_with_traceback(self, message: str):
        """Auto-register this exception with zTraceback for interactive handling.
        
        Uses thread-local context to get current zKernel instance (if available).
        Fails silently if no context - don't break exception raising!
        
        Args:
            message: Exception message for logging
        """
        try:
            # Import here to avoid circular dependency (zKernel.zCLI imports zExceptions)
            from zKernel.zCLI import get_current_zcli

            # Get current zKernel instance (thread-safe)
            zcli = get_current_zcli()

            # Register if zKernel context available and zTraceback initialized
            if zcli and hasattr(zcli, 'zTraceback') and zcli.zTraceback:
                zcli.zTraceback.log_exception(
                    self,
                    message=f"{self.__class__.__name__}: {message}",
                    context=self.context
                )
        except Exception:
            # Fail silently - don't let registration break exception raising
            # This ensures exceptions work even without zKernel context
            pass


class SchemaNotFoundError(zKernelException):
    """Raised when a schema file or loaded schema cannot be found."""

    def __init__(self, schema_name: str, context_type: str = "python", zpath: str = None):
        if context_type == "python":
            hint = (
                f"Load it first: z.loader.handle('@.zSchema.{schema_name}')\n"
                f"   Expected file: zSchema.{schema_name}.yaml in workspace"
            )
        elif context_type == "yaml_zdata":
            hint = (
                f"In zUI files, use zPath syntax WITHOUT .yaml extension:\n"
                f"   zData:\n"
                f"     model: '@.zSchema.{schema_name}'  # NO .yaml!\n"
                f"     action: read\n"
                f"     table: your_table"
            )
        elif context_type == "yaml_zdialog":
            hint = (
                f"Ensure the schema is loaded AND the form model is defined:\n"
                f"   1. Load: z.loader.handle('@.zSchema.{schema_name}')\n"
                f"   2. Define in zSchema.{schema_name}.yaml:\n"
                f"      Models:\n"
                f"        YourFormName:\n"
                f"          fields:\n"
                f"            field1: {{type: string}}"
            )
        else:
            hint = f"Load the schema: z.loader.handle('@.zSchema.{schema_name}')"

        message = f"Schema '{schema_name}' not found"
        if zpath:
            message += f" (attempted: {zpath})"

        super().__init__(
            message,
            hint=hint,
            context={"schema": schema_name, "context_type": context_type, "zpath": zpath}
        )


class FormModelNotFoundError(zKernelException):
    """Raised when a form model is not defined in the loaded schema."""

    def __init__(self, model_name: str, schema_name: str = None, available_models: list = None):
        available = ", ".join(available_models) if available_models else "None"

        schema_hint = f"zSchema.{schema_name}.yaml" if schema_name else "your schema file"
        hint = (
            f"Available models: {available}\n"
            f"   Define it in {schema_hint}:\n"
            f"   Models:\n"
            f"     {model_name}:\n"
            f"       fields:\n"
            f"         field1: {{type: string}}\n"
            f"         field2: {{type: integer}}"
        )

        super().__init__(
            f"Form model '{model_name}' not found in loaded schema",
            hint=hint,
            context={"model": model_name, "schema": schema_name, "available": available_models}
        )


class InvalidzPathError(zKernelException):
    """Raised when a zPath is malformed or cannot be resolved."""

    def __init__(self, zpath: str, reason: str = None):
        hint = (
            "zPath syntax:\n"
            "   '@.zSchema.name' - workspace-relative (NO .yaml extension)\n"
            "   '@.Schemas.zSchema.name' - subdirectory path\n"
            "   '~.zConfig.settings' - user config directory\n"
            "   'zMachine.zSchema.global' - platformdirs data directory\n\n"
            "Common mistakes:\n"
            "   WRONG: '@.zSchema.users.yaml' - Don't include .yaml!\n"
            "   RIGHT: '@.zSchema.users' - Correct"
        )

        message = f"Invalid zPath: '{zpath}'"
        if reason:
            message += f" ({reason})"

        super().__init__(
            message,
            hint=hint,
            context={"zpath": zpath, "reason": reason}
        )


class DatabaseNotInitializedError(zKernelException):
    """Raised when attempting database operations without initialization."""

    def __init__(self, operation: str = None, table: str = None):
        op_context = f" for operation '{operation}'" if operation else ""
        table_context = f" on table '{table}'" if table else ""

        hint = (
            "Initialize the database first:\n"
            "   Step 1: Create table structure\n"
            "   z.data.handle({\n"
            "       'action': 'create',\n"
            "       'model': '@.zSchema.your_schema'\n"
            "   })\n\n"
            "   Step 2: Then perform operations\n"
            "   z.data.handle({\n"
            "       'action': 'insert',\n"
            "       'table': 'your_table',\n"
            "       'data': {'field': 'value'}\n"
            "   })\n\n"
            "WARNING: Common mistake is INSERT before CREATE!"
        )

        super().__init__(
            f"Database not initialized{op_context}{table_context}",
            hint=hint,
            context={"operation": operation, "table": table}
        )


class TableNotFoundError(zKernelException):
    """Raised when a table doesn't exist in the database."""

    def __init__(self, table_name: str, schema_name: str = None):
        schema_hint = f" in schema '{schema_name}'" if schema_name else ""
        hint = (
            f"Create the table first using zData 'create' action:\n"
            f"   z.data.handle({{\n"
            f"       'action': 'create',\n"
            f"       'model': '@.zSchema.{schema_name or 'your_schema'}'\n"
            f"   }})\n\n"
            f"Or check your schema file for table definitions."
        )

        super().__init__(
            f"Table '{table_name}' not found{schema_hint}",
            hint=hint,
            context={"table": table_name, "schema": schema_name}
        )


class zUIParseError(zKernelException):
    """Raised when a zUI file has syntax or structural errors."""

    def __init__(self, file_path: str, issue: str, suggestion: str = None):
        hint = suggestion or (
            "Check your zUI file structure:\n"
            "   zVaF:\n"
            "     ~Root*: ['Option 1', 'Option 2']\n"
            "     \n"
            "     'Option 1':\n"
            "       zDisplay:\n"
            "         event: text\n"
            "         content: 'Hello!'\n"
            "     \n"
            "     'Option 2':\n"
            "       zData:\n"
            "         model: '@.zSchema.users'\n"
            "         action: read\n\n"
            "See: Documentation/zUI_GUIDE.md for examples"
        )

        super().__init__(
            f"Error parsing zUI file '{file_path}': {issue}",
            hint=hint,
            context={"file": file_path, "issue": issue}
        )


class AuthenticationRequiredError(zKernelException):
    """Raised when attempting to access protected resources without authentication."""

    def __init__(self, resource: str = None, required_role: str = None, required_permission: str = None):
        resource_msg = f" for '{resource}'" if resource else ""
        role_msg = f" (requires role: {required_role})" if required_role else ""
        perm_msg = f" (requires permission: {required_permission})" if required_permission else ""

        hint = (
            "Authenticate first:\n"
            "   Python: z.auth.login(username='user', password='pass')\n\n"
            "   Or in zUI:\n"
            "   'Login':\n"
            "     zDialog:\n"
            "       model: LoginForm\n"
            "       fields: [username, password]\n"
            "       onSubmit:\n"
            "         zFunc: '&auth_plugin.login(username=zConv.username, password=zConv.password)'"
        )

        super().__init__(
            f"Authentication required{resource_msg}{role_msg}{perm_msg}",
            hint=hint,
            context={
                "resource": resource,
                "required_role": required_role,
                "required_permission": required_permission
            }
        )


class PermissionDeniedError(zKernelException):
    """Raised when an authenticated user lacks required permissions."""

    def __init__(self, resource: str = None, user: str = None, required_role: str = None):
        user_msg = f" User '{user}'" if user else "Current user"
        resource_msg = f" to '{resource}'" if resource else ""
        role_msg = f" (requires: {required_role})" if required_role else ""

        hint = (
            f"Contact an administrator to grant permissions.\n\n"
            f"Admins can grant permissions using:\n"
            f"   z.auth.grant_permission(user_id, permission='resource.action')\n"
            f"   z.auth.set_role(user_id, role='{required_role or 'admin'}')"
        )

        super().__init__(
            f"{user_msg} does not have permission{resource_msg}{role_msg}",
            hint=hint,
            context={"resource": resource, "user": user, "required_role": required_role}
        )


class ConfigurationError(zKernelException):
    """Raised when zKernel or subsystem configuration is invalid."""

    def __init__(self, setting: str, issue: str, example: str = None):
        hint_msg = f"Correct configuration:\n{example}" if example else (
            "Check your zSpark initialization:\n"
            "   z = zKernel({\n"
            "       'zSpace': '/path/to/project',\n"
            "       'zMode': 'Terminal',  # or 'zBifrost'\n"
            "       'zVerbose': True\n"
            "   })"
        )

        super().__init__(
            f"Configuration error for '{setting}': {issue}",
            hint=hint_msg,
            context={"setting": setting, "issue": issue}
        )


class PluginNotFoundError(zKernelException):
    """Raised when a plugin cannot be loaded or found."""

    def __init__(self, plugin_name: str, search_paths: list = None):
        paths_msg = ""
        if search_paths:
            paths_msg = f"\nSearched in: {', '.join(search_paths)}"

        hint = (
            f"Ensure plugin file exists:\n"
            f"   1. Create: {plugin_name}.py in workspace or utils/ directory\n"
            f"   2. Define functions with 'zcli' parameter:\n"
            f"      def my_function(zcli):\n"
            f"          zcli.display.text('Hello!')\n\n"
            f"   3. Call from zUI:\n"
            f"      zFunc: '&{plugin_name}.my_function()'"
        )

        super().__init__(
            f"Plugin '{plugin_name}' not found{paths_msg}",
            hint=hint,
            context={"plugin": plugin_name, "search_paths": search_paths}
        )


class ValidationError(zKernelException):
    """Raised when data validation fails."""

    def __init__(self, field: str, value: any, constraint: str, schema_name: str = None):
        schema_msg = f" in schema '{schema_name}'" if schema_name else ""
        hint = (
            f"Update the value to match constraints:\n"
            f"   Field '{field}' must satisfy: {constraint}\n\n"
            f"Check your schema definition for field constraints."
        )

        super().__init__(
            f"Validation failed for field '{field}'{schema_msg}: {constraint}",
            hint=hint,
            context={"field": field, "value": value, "constraint": constraint, "schema": schema_name}
        )
