# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_comm.py

"""
zComm and Service Management Commands

This module provides shell commands for managing services and communication channels
through the zComm subsystem. It supports service lifecycle management (start, stop,
restart), status monitoring, connection information retrieval, and OS-specific
installation guidance.

Purpose:
    - Service management (PostgreSQL, Bifrost, custom services)
    - Service lifecycle control (start, stop, restart)
    - Service status monitoring and connection info
    - OS-specific installation guidance with auto-install support (macOS)
    - Bifrost WebSocket bridge management

Commands:
    1. comm status [service]           # Show all services or specific service status
    2. comm start <service>            # Start a service
    3. comm stop <service>             # Stop a service
    4. comm restart <service>          # Restart a service
    5. comm info <service>             # Show connection information
    6. comm install <service> [--auto] # Installation guide with optional auto-install

Supported Services:
    - PostgreSQL: Relational database (zData backend)
    - Bifrost: WebSocket bridge for Terminal ↔ Web communication
    - Custom: Any service registered with zComm

Architecture:
    - Delegates all service operations to zComm subsystem
    - Lazy initialization of zComm (created on first command)
    - OS-specific installation instructions (macOS, Linux, Windows)
    - Auto-install support for macOS (Homebrew-based)
    - Mode-agnostic output (Terminal + Bifrost via zDisplay)
    - UI Adapter Pattern: All handlers return None, use zDisplay for output

Installation Flow:
    1. User runs: comm install postgresql
    2. Detects OS (macOS, Linux, Windows)
    3. Shows OS-specific installation commands
    4. Option: --auto flag (macOS only) for unattended install
    5. Uses zDisplay.spinner() for long-running operations
    6. Shows driver installation info (psycopg2, etc.)

Constants:
    Actions: ACTION_STATUS, ACTION_START, ACTION_STOP, ACTION_RESTART, ACTION_INFO, ACTION_INSTALL
    Services: SERVICE_POSTGRESQL, SERVICE_BIFROST
    Messages: ERROR_*, MSG_*, USAGE_*
    Display: HEADER_*, LABEL_*, STATUS_*
    Installation: INSTALL_*, URL_*

Dependencies:
    - zComm (Week 6.3): Service management subsystem
    - zDisplay: Mode-agnostic UI output
    - platform: OS detection
    - subprocess: Auto-install execution (macOS)

Example Usage:
    # Check all services
    >>> comm status
    zComm Service Status
      POSTGRESQL: Running
        Port: 5432
        URL: postgresql://localhost:5432
      BIFROST: Stopped

    # Start PostgreSQL
    >>> comm start postgresql
    [SUCCESS] postgresql started successfully
    Connection Info:
      host: localhost
      port: 5432
      database: postgres

    # Get connection info
    >>> comm info postgresql
    POSTGRESQL Connection Information:
      host                : localhost
      port                : 5432
      user                : postgres

    # Install PostgreSQL (macOS)
    >>> comm install postgresql
    PostgreSQL Installation Helper
    Installation command for macOS (Homebrew):
      brew install postgresql@14
    ...

    # Auto-install (macOS only)
    >>> comm install postgresql --auto
    Installing PostgreSQL (this may take a few minutes)...
    [SUCCESS] PostgreSQL installed successfully!
    Starting PostgreSQL service...
    [SUCCESS] PostgreSQL started!

Notes:
    - Auto-install requires Homebrew (macOS) or manual sudo (Linux)
    - Windows installation requires manual download from postgresql.org
    - All service operations log to zCLI logger
    - Connection info only available for running services
    - Service names are case-insensitive
    - Install command provides guidance only (except macOS --auto)

Author: zCLI Development Team
Version: 1.5.4+
Last Updated: Week 6.13
"""

# Type hints (centralized import from zCLI)
from zOS import Any, Dict, List, Optional

# =============================================================================
# Module Constants
# =============================================================================

# Actions
ACTION_STATUS = "status"
ACTION_START = "start"
ACTION_STOP = "stop"
ACTION_RESTART = "restart"
ACTION_INFO = "info"
ACTION_INSTALL = "install"

# Services
SERVICE_POSTGRESQL = "postgresql"
SERVICE_BIFROST = "bifrost"

# Error Messages
ERROR_NO_SERVICE_NAME = "Service name required"
ERROR_SERVICE_START_FAILED = "Failed to start"
ERROR_SERVICE_STOP_FAILED = "Failed to stop"
ERROR_SERVICE_RESTART_FAILED = "Failed to restart"
ERROR_SERVICE_NOT_FOUND = "Service not found or not running"
ERROR_UNKNOWN_SERVICE = "Unknown service"
ERROR_UNKNOWN_ACTION = "Unknown comm action"
ERROR_ZCOMM_NOT_AVAILABLE = "zComm subsystem not available"
ERROR_INSTALL_TIMEOUT = "Installation timed out"
ERROR_INSTALL_FAILED = "Installation failed"

# Success Messages
MSG_SERVICE_STARTED = "started successfully"
MSG_SERVICE_STOPPED = "stopped successfully"
MSG_SERVICE_RESTARTED = "restarted successfully"
MSG_INSTALL_SUCCESS = "installed successfully"
MSG_INSTALL_INSTRUCTIONS = "Installation instructions provided"

# Usage Messages
USAGE_START = "Usage: comm start <service>"
USAGE_STOP = "Usage: comm stop <service>"
USAGE_RESTART = "Usage: comm restart <service>"
USAGE_INFO = "Usage: comm info <service>"
USAGE_INSTALL = "Usage: comm install <service> [--auto]"

# Display Strings
HEADER_STATUS = "zComm Service Status"
HEADER_CONNECTION_INFO = "Connection Information"
HEADER_INSTALL = "PostgreSQL Installation Helper"
LABEL_PORT = "Port"
LABEL_URL = "URL"
LABEL_NOTE = "Note"
LABEL_CONNECTION_INFO = "Connection Info"
STATUS_RUNNING = "Running"
STATUS_STOPPED = "Stopped"

# Installation Strings
INSTALL_MACOS_BREW_CMD = "brew install postgresql@14"
INSTALL_MACOS_START_CMD = "brew services start postgresql@14"
INSTALL_LINUX_APT_UPDATE = "sudo apt update"
INSTALL_LINUX_APT_INSTALL = "sudo apt install postgresql postgresql-contrib"
INSTALL_LINUX_YUM_INSTALL = "sudo yum install postgresql-server postgresql-contrib"
INSTALL_LINUX_INITDB = "sudo postgresql-setup --initdb"
INSTALL_LINUX_START = "sudo systemctl start postgresql"
INSTALL_LINUX_ENABLE = "sudo systemctl enable postgresql"
INSTALL_WINDOWS_DOWNLOAD = "Download installer from:"
INSTALL_DRIVER_PIP = "pip install zolo-zcli[postgresql]"
INSTALL_DRIVER_ALL = "pip install zolo-zcli[all]"
INSTALL_AUTO_CMD = "comm install postgresql --auto"
INSTALL_ALT_CMD = "comm start postgresql"

# URLs
URL_POSTGRESQL_WINDOWS = "https://www.postgresql.org/download/windows/"

# Spinner Messages
SPINNER_INSTALLING = "Installing PostgreSQL (this may take a few minutes)"
SPINNER_STARTING = "Starting PostgreSQL service"

# Info Messages
INFO_INSTALLATION_CMD = "Installation command for macOS (Homebrew):"
INFO_START_AFTER_INSTALL = "To start PostgreSQL after installation:"
INFO_LINUX_COMMANDS = "Installation commands for Linux:"
INFO_UBUNTU_DEBIAN = "Ubuntu/Debian:"
INFO_RHEL_CENTOS = "RHEL/CentOS/Fedora:"
INFO_WINDOWS_INSTALL = "Installation for Windows:"
INFO_DRIVER_INFO = "Python Driver (psycopg2):"
INFO_DRIVER_DESC = "The Python library for PostgreSQL is installed with:"
INFO_DRIVER_ALL_DESC = "Or to install all backend support:"
INFO_AUTO_INSTALL = "To install automatically, run:"
INFO_WINDOWS_AUTOSTART = "PostgreSQL will start automatically as a Windows service"

# Warning Messages
WARN_LINUX_SUDO = "Auto-installation on Linux requires sudo permissions."
WARN_LINUX_MANUAL = "Please run the commands above manually."

# Available Services
AVAILABLE_SERVICES = [SERVICE_POSTGRESQL]


# =============================================================================
# Main Command Handler
# =============================================================================

def execute_comm(zcli: Any, parsed: Dict[str, Any]) -> None:
    """
    Execute comm commands (start, stop, status, info, install).

    Main entry point for all service management commands. Routes to appropriate
    handler based on action. Lazily initializes zComm subsystem if not available.

    Args:
        zcli: The zCLI instance
        parsed: Parsed command dictionary with keys:
            - action (str): The command action (status, start, stop, etc.)
            - args (List[str]): Command arguments (e.g., service name)
            - options (Dict[str, Any]): Command options (e.g., --auto)

    Returns:
        None (UI Adapter Pattern - uses zDisplay for all output)

    Examples:
        >>> execute_comm(zcli, {"action": "status", "args": [], "options": {}})
        # Shows all service statuses

        >>> execute_comm(zcli, {"action": "start", "args": ["postgresql"], "options": {}})
        # Starts PostgreSQL service

        >>> execute_comm(zcli, {"action": "install", "args": ["postgresql"], "options": {"auto": True}})
        # Auto-installs PostgreSQL (macOS only)

    Notes:
        - Lazy initialization: Creates zComm instance if not exists
        - All handlers return None (UI adapter pattern)
        - Unknown actions display error via zDisplay
        - Logs all operations via zcli.logger
    """
    action = parsed.get("action", "")
    args = parsed.get("args", [])
    options = parsed.get("options", {})

    # Lazy initialization of zComm subsystem
    if not hasattr(zcli, 'comm') or zcli.comm is None:
        try:
            from zOS.L1_Foundation.b_zComm import zComm
            zcli.comm = zComm(zcli)
        except Exception as e:
            zcli.display.error(f"{ERROR_ZCOMM_NOT_AVAILABLE}: {e}")
            zcli.logger.error("Failed to initialize zComm: %s", e)
            return None

    # Action routing
    action_map = {
        ACTION_STATUS: _handle_status,
        ACTION_START: _handle_start,
        ACTION_STOP: _handle_stop,
        ACTION_RESTART: _handle_restart,
        ACTION_INFO: _handle_info,
        ACTION_INSTALL: _handle_install,
    }

    handler = action_map.get(action)
    if handler:
        handler(zcli, args, options)
        return None

    # Unknown action
    zcli.display.error(f"{ERROR_UNKNOWN_ACTION}: {action}")
    zcli.logger.warning("Unknown comm action: %s", action)
    return None


# =============================================================================
# Service Operation Handlers
# =============================================================================

def _handle_status(zcli: Any, args: List[str], options: Dict[str, Any]) -> None:  # pylint: disable=unused-argument
    """
    Handle status command - Display service status information.

    Shows status for all services or a specific service. Displays running state,
    port, and connection information.

    Args:
        zcli: The zCLI instance
        args: Command arguments (optional service name)
        options: Command options (unused)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_status(zcli, [], {})
        # Shows all services
        zComm Service Status
          POSTGRESQL: Running
            Port: 5432

        >>> _handle_status(zcli, ["postgresql"], {})
        # Shows specific service
        POSTGRESQL: Running
          Port: 5432
          URL: postgresql://localhost:5432

    Notes:
        - No args = show all services
        - With args[0] = show specific service
        - Delegates to zComm.service_status()
        - Handles error responses from zComm
    """
    service_name = args[0] if args else None

    try:
        status = zcli.comm.service_status(service_name)

        if service_name:
            # Single service status
            _display_service_status(zcli, service_name, status)
        else:
            # All services status
            zcli.display.zDeclare(HEADER_STATUS, color="INFO", indent=0, style="full")
            for name, info in status.items():
                _display_service_status(zcli, name, info)

    except Exception as e:
        zcli.display.error(f"{ERROR_ZCOMM_NOT_AVAILABLE}: {e}")
        zcli.logger.error("Failed to get service status: %s", e)

    return None


def _handle_start(zcli: Any, args: List[str], options: Dict[str, Any]) -> None:
    """
    Handle start command - Start a service.

    Starts the specified service and displays connection information on success.

    Args:
        zcli: The zCLI instance
        args: Command arguments [service_name]
        options: Command options (passed to zComm.start_service)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_start(zcli, ["postgresql"], {})
        [SUCCESS] postgresql started successfully
        Connection Info:
          host: localhost
          port: 5432

    Notes:
        - Requires service name argument
        - Logs operation to zcli.logger
        - Displays connection info on success
        - Delegates to zComm.start_service()
    """
    service_name = _validate_service_arg(zcli, args, USAGE_START)
    if not service_name:
        return None

    zcli.logger.info("Starting service: %s", service_name)

    try:
        success = zcli.comm.start_service(service_name, **options)

        if success:
            zcli.display.success(f"{service_name} {MSG_SERVICE_STARTED}")

            # Display connection info if available
            try:
                conn_info = zcli.comm.get_service_connection_info(service_name)
                if conn_info:
                    zcli.display.info(f"{LABEL_CONNECTION_INFO}:", indent=1)
                    for key, value in conn_info.items():
                        zcli.display.text(f"{key}: {value}", indent=2)
            except Exception as e:
                zcli.logger.warning("Failed to get connection info: %s", e)
        else:
            zcli.display.error(f"{ERROR_SERVICE_START_FAILED} {service_name}")

    except Exception as e:
        zcli.display.error(f"{ERROR_SERVICE_START_FAILED} {service_name}: {e}")
        zcli.logger.error("Failed to start service %s: %s", service_name, e)

    return None


def _handle_stop(zcli: Any, args: List[str], options: Dict[str, Any]) -> None:  # pylint: disable=unused-argument
    """
    Handle stop command - Stop a service.

    Stops the specified service and displays success/error message.

    Args:
        zcli: The zCLI instance
        args: Command arguments [service_name]
        options: Command options (unused)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_stop(zcli, ["postgresql"], {})
        [SUCCESS] postgresql stopped successfully

    Notes:
        - Requires service name argument
        - Logs operation to zcli.logger
        - Delegates to zComm.stop_service()
    """
    service_name = _validate_service_arg(zcli, args, USAGE_STOP)
    if not service_name:
        return None

    zcli.logger.info("Stopping service: %s", service_name)

    try:
        success = zcli.comm.stop_service(service_name)

        if success:
            zcli.display.success(f"{service_name} {MSG_SERVICE_STOPPED}")
        else:
            zcli.display.error(f"{ERROR_SERVICE_STOP_FAILED} {service_name}")

    except Exception as e:
        zcli.display.error(f"{ERROR_SERVICE_STOP_FAILED} {service_name}: {e}")
        zcli.logger.error("Failed to stop service %s: %s", service_name, e)

    return None


def _handle_restart(zcli: Any, args: List[str], options: Dict[str, Any]) -> None:  # pylint: disable=unused-argument
    """
    Handle restart command - Restart a service.

    Restarts the specified service (stops then starts).

    Args:
        zcli: The zCLI instance
        args: Command arguments [service_name]
        options: Command options (unused)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_restart(zcli, ["postgresql"], {})
        [SUCCESS] postgresql restarted successfully

    Notes:
        - Requires service name argument
        - Logs operation to zcli.logger
        - Delegates to zComm.restart_service()
    """
    service_name = _validate_service_arg(zcli, args, USAGE_RESTART)
    if not service_name:
        return None

    zcli.logger.info("Restarting service: %s", service_name)

    try:
        success = zcli.comm.restart_service(service_name)

        if success:
            zcli.display.success(f"{service_name} {MSG_SERVICE_RESTARTED}")
        else:
            zcli.display.error(f"{ERROR_SERVICE_RESTART_FAILED} {service_name}")

    except Exception as e:
        zcli.display.error(f"{ERROR_SERVICE_RESTART_FAILED} {service_name}: {e}")
        zcli.logger.error("Failed to restart service %s: %s", service_name, e)

    return None


def _handle_info(zcli: Any, args: List[str], options: Dict[str, Any]) -> None:  # pylint: disable=unused-argument
    """
    Handle info command - Display service connection information.

    Shows detailed connection information for a running service (host, port,
    database, user, connection strings, etc.).

    Args:
        zcli: The zCLI instance
        args: Command arguments [service_name]
        options: Command options (unused)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_info(zcli, ["postgresql"], {})
        POSTGRESQL Connection Information:
          host                : localhost
          port                : 5432
          user                : postgres
          database            : postgres

    Notes:
        - Requires service name argument
        - Only available for running services
        - Delegates to zComm.get_service_connection_info()
    """
    service_name = _validate_service_arg(zcli, args, USAGE_INFO)
    if not service_name:
        return None

    try:
        conn_info = zcli.comm.get_service_connection_info(service_name)

        if conn_info:
            header = f"{service_name.upper()} {HEADER_CONNECTION_INFO}:"
            zcli.display.zDeclare(header, color="INFO", indent=0, style="full")
            for key, value in conn_info.items():
                zcli.display.text(f"{key:20}: {value}", indent=1)
        else:
            zcli.display.error(f"No connection info available for {service_name}")

    except Exception as e:
        zcli.display.error(f"{ERROR_SERVICE_NOT_FOUND}: {e}")
        zcli.logger.error("Failed to get connection info for %s: %s", service_name, e)

    return None


def _handle_install(zcli: Any, args: List[str], options: Dict[str, Any]) -> None:
    """
    Handle install command - Provide OS-specific installation instructions.

    Displays installation instructions for the specified service, with optional
    auto-install support for macOS (Homebrew).

    Args:
        zcli: The zCLI instance
        args: Command arguments [service_name]
        options: Command options (e.g., {"auto": True} for auto-install)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _handle_install(zcli, ["postgresql"], {})
        # Shows manual installation instructions

        >>> _handle_install(zcli, ["postgresql"], {"auto": True})
        # Executes auto-install (macOS only)

    Notes:
        - Currently supports: postgresql
        - Auto-install only on macOS (requires Homebrew)
        - Linux requires manual sudo commands
        - Windows requires manual download
        - Includes Python driver (psycopg2) installation info
    """
    service_name = _validate_service_arg(zcli, args, USAGE_INSTALL)
    if not service_name:
        return None

    _install_service_helper(zcli, service_name, options)
    return None


# =============================================================================
# Display Helper Functions
# =============================================================================

def _display_service_status(zcli: Any, service_name: str, status_info: Dict[str, Any]) -> None:
    """
    Display service status information using zDisplay.

    Formats and displays service status including running state, port, message,
    and connection information.

    Args:
        zcli: The zCLI instance
        service_name: The service name
        status_info: Status dictionary from zComm with keys:
            - running (bool): Service running state
            - port (int): Service port (optional)
            - message (str): Status message (optional)
            - connection_info (dict): Connection details (optional)
            - error (str): Error message (optional)

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _display_service_status(zcli, "postgresql", {"running": True, "port": 5432})
        POSTGRESQL: Running
          Port: 5432

    Notes:
        - Handles error responses from zComm
        - Displays connection URL if available
        - Indented output (service = 1, details = 2)
    """
    # Handle error responses
    if isinstance(status_info, dict) and "error" in status_info:
        zcli.display.text(f"{service_name}: {status_info['error']}", indent=1)
        return None

    # Display running status
    running = status_info.get("running", False)
    status_text = STATUS_RUNNING if running else STATUS_STOPPED
    zcli.display.text(f"{service_name.upper()}: {status_text}", indent=1)

    # Display port if available
    if "port" in status_info:
        zcli.display.text(f"{LABEL_PORT}: {status_info['port']}", indent=2)

    # Display message/note if available
    if "message" in status_info:
        zcli.display.text(f"{LABEL_NOTE}: {status_info['message']}", indent=2)

    # Display connection URL if running
    if running and "connection_info" in status_info:
        conn = status_info["connection_info"]
        if "connection_string" in conn:
            zcli.display.text(f"{LABEL_URL}: {conn['connection_string']}", indent=2)

    return None


# =============================================================================
# Installation Helper Functions
# =============================================================================

def _install_service_helper(zcli: Any, service_name: str, options: Dict[str, Any]) -> None:
    """
    Guide user through service installation with OS-specific instructions.

    Routes to appropriate OS-specific installation function based on service name.
    Currently supports PostgreSQL only.

    Args:
        zcli: The zCLI instance
        service_name: The service to install
        options: Installation options (e.g., {"auto": True})

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _install_service_helper(zcli, "postgresql", {})
        # Shows OS-specific PostgreSQL installation instructions

    Notes:
        - Currently only PostgreSQL is supported
        - Unknown services display error with available list
        - Routes to _install_postgresql()
    """
    if service_name == SERVICE_POSTGRESQL:
        _install_postgresql(zcli, options)
        return None

    # Unknown service
    zcli.display.error(f"{ERROR_UNKNOWN_SERVICE}: {service_name}")
    zcli.display.info(f"Available services: {', '.join(AVAILABLE_SERVICES)}")
    return None


def _install_postgresql(zcli: Any, options: Dict[str, Any]) -> None:
    """
    Install PostgreSQL with OS-specific instructions.

    Detects OS and routes to appropriate installation function. Shows header
    with OS-specific instructions and driver installation info.

    Args:
        zcli: The zCLI instance
        options: Installation options (e.g., {"auto": True})

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _install_postgresql(zcli, {})
        PostgreSQL Installation Helper
        Installation command for macOS (Homebrew):
          brew install postgresql@14
        ...

    Notes:
        - Detects OS with platform.system()
        - macOS: Homebrew-based installation
        - Linux: apt/yum commands
        - Windows: Manual download instructions
        - Shows driver installation info for all platforms
    """
    from zOS import platform

    os_type = platform.system()
    auto_install = options.get("auto", False) or options.get("y", False)

    # Display header
    zcli.display.header(HEADER_INSTALL)

    # Route to OS-specific installation
    if os_type == "Darwin":
        _install_postgresql_macos(zcli, auto_install)
    elif os_type == "Linux":
        _install_postgresql_linux(zcli, auto_install)
    elif os_type == "Windows":
        _install_postgresql_windows(zcli)
    else:
        # Unknown OS - show driver info only
        _display_postgresql_driver_info(zcli)

    return None


def _install_postgresql_macos(zcli: Any, auto_install: bool) -> None:
    """
    Install PostgreSQL on macOS using Homebrew.

    Shows manual installation commands or executes auto-install if --auto flag
    is provided.

    Args:
        zcli: The zCLI instance
        auto_install: If True, execute auto-install; if False, show instructions

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _install_postgresql_macos(zcli, False)
        # Shows manual instructions

        >>> _install_postgresql_macos(zcli, True)
        Installing PostgreSQL (this may take a few minutes)...
        [SUCCESS] PostgreSQL installed successfully!

    Notes:
        - Requires Homebrew (brew command)
        - Auto-install uses subprocess.run()
        - Uses zDisplay.spinner() for long operations
        - 5-minute timeout for installation
        - Starts service after successful install
    """
    import subprocess

    # Show manual instructions
    zcli.display.info(INFO_INSTALLATION_CMD)
    install_items = [
        f"  {INSTALL_MACOS_BREW_CMD}"
    ]
    zcli.display.list(install_items, style="none")

    zcli.display.info(INFO_START_AFTER_INSTALL)
    start_items = [
        f"  {INSTALL_MACOS_START_CMD}",
        "  OR",
        f"  {INSTALL_ALT_CMD}"
    ]
    zcli.display.list(start_items, style="none")

    # Execute auto-install if requested
    if auto_install:
        try:
            # Install PostgreSQL with spinner
            with zcli.display.spinner(SPINNER_INSTALLING, style="dots"):
                result = subprocess.run(
                    ["brew", "install", "postgresql@14"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False
                )
        except subprocess.TimeoutExpired:
            zcli.display.error(ERROR_INSTALL_TIMEOUT)
            zcli.logger.error("PostgreSQL installation timed out")
            return None
        except Exception as e:
            zcli.display.error(f"{ERROR_INSTALL_FAILED}: {e}")
            zcli.logger.error("PostgreSQL installation error: %s", e)
            return None

        # Check install result
        if result.returncode == 0:
            zcli.display.success(f"PostgreSQL {MSG_INSTALL_SUCCESS}")

            # Start service
            try:
                with zcli.display.spinner(SPINNER_STARTING, style="arc"):
                    subprocess.run(
                        ["brew", "services", "start", "postgresql@14"],
                        check=False,
                        capture_output=True
                    )
                zcli.display.success("PostgreSQL started!")
            except Exception as e:
                zcli.logger.warning("Failed to start PostgreSQL: %s", e)

            _display_postgresql_driver_info(zcli)
        else:
            zcli.display.error(f"{ERROR_INSTALL_FAILED}: {result.stderr}")
            zcli.logger.error("Installation failed: %s", result.stderr)

        return None

    # Manual install - show auto-install option
    zcli.display.info(INFO_AUTO_INSTALL)
    zcli.display.list([f"  {INSTALL_AUTO_CMD}"], style="none")
    _display_postgresql_driver_info(zcli)

    return None


def _install_postgresql_linux(zcli: Any, auto_install: bool) -> None:
    """
    Install PostgreSQL on Linux with distro-specific commands.

    Shows installation commands for Ubuntu/Debian and RHEL/CentOS/Fedora.

    Args:
        zcli: The zCLI instance
        auto_install: If True, show sudo warning; if False, show instructions only

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _install_postgresql_linux(zcli, False)
        Installation commands for Linux:
        Ubuntu/Debian:
          sudo apt update
          sudo apt install postgresql postgresql-contrib
        ...

    Notes:
        - No auto-install support (requires sudo)
        - Shows commands for apt (Ubuntu/Debian) and yum (RHEL/CentOS)
        - Includes systemctl commands for service management
        - Shows zCLI alternative: comm start postgresql
    """
    zcli.display.info(INFO_LINUX_COMMANDS)

    # Ubuntu/Debian
    zcli.display.info(INFO_UBUNTU_DEBIAN)
    ubuntu_items = [
        f"  {INSTALL_LINUX_APT_UPDATE}",
        f"  {INSTALL_LINUX_APT_INSTALL}"
    ]
    zcli.display.list(ubuntu_items, style="none")

    # RHEL/CentOS/Fedora
    zcli.display.info(INFO_RHEL_CENTOS)
    rhel_items = [
        f"  {INSTALL_LINUX_YUM_INSTALL}",
        f"  {INSTALL_LINUX_INITDB}"
    ]
    zcli.display.list(rhel_items, style="none")

    # Start commands
    zcli.display.info(INFO_START_AFTER_INSTALL)
    start_items = [
        f"  {INSTALL_LINUX_START}",
        f"  {INSTALL_LINUX_ENABLE}",
        "  OR",
        f"  {INSTALL_ALT_CMD}"
    ]
    zcli.display.list(start_items, style="none")

    # Warn about auto-install
    if auto_install:
        zcli.display.warning(WARN_LINUX_SUDO)
        zcli.display.warning(WARN_LINUX_MANUAL)

    _display_postgresql_driver_info(zcli)

    return None


def _install_postgresql_windows(zcli: Any) -> None:
    """
    Install PostgreSQL on Windows with manual download instructions.

    Shows download URL and installation wizard steps.

    Args:
        zcli: The zCLI instance

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _install_postgresql_windows(zcli)
        Installation for Windows:
          1. Download installer from:
             https://www.postgresql.org/download/windows/
          2. Run the installer (EDB PostgreSQL)
          3. Follow the installation wizard
        ...

    Notes:
        - No auto-install support (manual download required)
        - Service starts automatically after installation
        - Shows driver installation info
    """
    zcli.display.info(INFO_WINDOWS_INSTALL)
    windows_items = [
        f"  1. {INSTALL_WINDOWS_DOWNLOAD}",
        f"     {URL_POSTGRESQL_WINDOWS}",
        "  2. Run the installer (EDB PostgreSQL)",
        "  3. Follow the installation wizard"
    ]
    zcli.display.list(windows_items, style="none")

    zcli.display.info(INFO_WINDOWS_AUTOSTART)

    _display_postgresql_driver_info(zcli)

    return None


def _display_postgresql_driver_info(zcli: Any) -> None:
    """
    Display PostgreSQL Python driver (psycopg2) installation information.

    Shows pip install commands for psycopg2 and zolo-zcli[postgresql].

    Args:
        zcli: The zCLI instance

    Returns:
        None (uses zDisplay for output)

    Examples:
        >>> _display_postgresql_driver_info(zcli)
        Python Driver (psycopg2):
          The Python library for PostgreSQL is installed with:
            pip install zolo-zcli[postgresql]
          Or to install all backend support:
            pip install zolo-zcli[all]

    Notes:
        - Shows two install options: postgresql only or all backends
        - Uses zDisplay.info() and zDisplay.list()
    """
    zcli.display.info(INFO_DRIVER_INFO)
    zcli.display.text(f"  {INFO_DRIVER_DESC}")
    zcli.display.list([f"    {INSTALL_DRIVER_PIP}"], style="none")

    zcli.display.text(f"  {INFO_DRIVER_ALL_DESC}")
    zcli.display.list([f"    {INSTALL_DRIVER_ALL}"], style="none")

    return None


# =============================================================================
# DRY Helper Functions
# =============================================================================

def _validate_service_arg(zcli: Any, args: List[str], usage: str) -> Optional[str]:
    """
    Validate that service name argument is provided.

    Checks if args list contains at least one element (service name). Displays
    error with usage message if missing.

    Args:
        zcli: The zCLI instance
        args: Command arguments list
        usage: Usage message to display on error

    Returns:
        str: Service name if valid
        None: If no service name provided

    Examples:
        >>> _validate_service_arg(zcli, ["postgresql"], "Usage: comm start <service>")
        "postgresql"

        >>> _validate_service_arg(zcli, [], "Usage: comm start <service>")
        None
        # Displays error: "Service name required. Usage: comm start <service>"

    Notes:
        - Displays error via zDisplay
        - Returns None if validation fails
        - Returns lowercase service name for consistency
    """
    if not args:
        zcli.display.error(f"{ERROR_NO_SERVICE_NAME}. {usage}")
        return None

    return args[0].lower()
