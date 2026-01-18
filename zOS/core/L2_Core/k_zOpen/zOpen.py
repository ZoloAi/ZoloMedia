# zCLI/subsystems/zOpen/zOpen.py

"""
zOpen Subsystem - Main Facade

This module provides the main facade for the zOpen subsystem, handling file and URL
opening operations in a mode-agnostic manner. It serves as the primary entry point,
routing requests to specialized modules and executing optional hooks.

Architecture Position:
    - Tier 2 (Facade) of zOpen's 3-tier architecture
    - Delegates to Tier 1 foundation modules (open_paths, open_urls, open_files)
    - Exposed to zCLI via Tier 3 (package root)

3-Tier Architecture:
    Tier 1: Foundation Modules (open_modules/)
        - open_paths.py: zPath resolution (@ and ~ symbols)
        - open_urls.py: URL opening in browsers
        - open_files.py: File opening by extension (HTML, text)
        - __init__.py: Package aggregator

    Tier 2: Facade (THIS FILE)
        - zOpen class: Main entry point
        - handle() method: Request parsing, routing, and hook execution
        - Delegates all opening logic to Tier 1 modules

    Tier 3: Package Root (__init__.py)
        - Exports zOpen class to zCLI

Key Features:
    - Dual Format Support: Accepts both string ("zOpen(path)") and dict formats
    - Type Detection: Automatically detects URLs, zPaths, and local file paths
    - Modular Routing: Delegates to specialized handlers (paths, URLs, files)
    - Hook Execution: Supports onSuccess/onFail callbacks via zFunc
    - Mode-Agnostic: Works in both Terminal and Bifrost modes
    - Session Integration: Uses zConfig session for preferences

Input Formats:
    String Format (Legacy):
        "zOpen(/path/to/file.txt)"
        "zOpen(https://example.com)"
        "zOpen(@.README.md)"

    Dict Format (Modern):
        {
            "zOpen": {
                "path": "/path/to/file.txt",
                "onSuccess": "callback_function()",  # Optional
                "onFail": "error_handler()"          # Optional
            }
        }

Type Detection & Routing:
    URLs (http:// or https:// or www.):
        → open_url() from open_modules.open_urls
        → Opens in user's preferred or system default browser

    zPaths (@ or ~):
        → resolve_zpath() from open_modules.open_paths
        → Resolves to filesystem path
        → open_file() from open_modules.open_files

    Local Files (everything else):
        → os.path.abspath(os.path.expanduser(path))
        → open_file() from open_modules.open_files
        → Routes by extension (.html → browser, .txt → IDE)

Hook Execution (onSuccess/onFail):
    - Executed after opening attempt completes
    - onSuccess: Triggered if result == "zBack" (success)
    - onFail: Triggered if result == "stop" (failure)
    - Both callbacks executed via zFunc.handle()
    - Hook results replace original result

Integration Points:
    - zCLI.py: Initializes zOpen (line ~210)
    - zDispatch: Routes "zOpen(...)" commands via dispatch_launcher
    - zConfig: Session access for workspace, IDE, browser preferences
    - zDisplay: Output, breadcrumbs, status messages
    - zFunc: Hook callback execution
    - zDialog: Interactive prompts (file creation, IDE selection) via open_files

Dependencies:
    - os: Path operations (abspath, expanduser)
    - urlparse: URL parsing for type detection
    - open_modules: Foundation modules (paths, URLs, files)

Usage Example (from zDispatch):
    # String format
    result = zcli.open.handle("zOpen(/path/to/file.py)")

    # Dict format with hooks
    result = zcli.open.handle({
        "zOpen": {
            "path": "https://github.com",
            "onSuccess": "log_success()",
            "onFail": "log_error()"
        }
    })

    # zPath format
    result = zcli.open.handle("zOpen(@.README.md)")

Return Values:
    - "zBack": Opening successful, return to previous screen
    - "stop": Opening failed or user cancelled
    - Hook result: If hook executes, returns hook's result

Version History:
    - v1.5.4: Refactored from monolithic (369 lines) to modular facade (~150 lines)
    - v1.5.4: Extracted logic to open_modules (paths, URLs, files)
    - v1.5.4: Added industry-grade documentation and type hints
    - v1.5.4: Modernized session key access (SESSION_KEY_* constants)
    - v1.5.4: Verified zDispatch integration - handle() signature compatible

Author: zCLI Development Team
"""

from zOS import os, urlparse, Any, subprocess
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZMACHINE

# Import from foundation modules (Tier 1)
from .open_modules import resolve_zpath, open_url, open_file
from .open_modules.open_constants import (
    COLOR_INFO,
    COLOR_ZOPEN,
    DICT_KEY_ON_FAIL,
    DICT_KEY_ON_SUCCESS,
    DICT_KEY_PATH,
    DICT_KEY_ZOPEN,
    RETURN_STOP,
    RETURN_ZBACK,
    URL_PREFIX_WWW,
    URL_SCHEME_HTTP,
    URL_SCHEME_HTTPS,
    URL_SCHEME_HTTPS_DEFAULT,
    ZPATH_SYMBOL_ABSOLUTE,
    ZPATH_SYMBOL_WORKSPACE,
    _CMD_PREFIX,
    _INDENT_HANDLE,
    _INDENT_HOOK,
    _INDENT_INIT,
    _LOG_EXEC_FAIL_HOOK,
    _LOG_EXEC_SUCCESS_HOOK,
    _LOG_INCOMING_REQUEST,
    _LOG_PARSED_PATH,
    _MSG_HANDLE_ZOPEN,
    _MSG_HOOK_FAIL,
    _MSG_HOOK_SUCCESS,
    _MSG_ZOPEN_READY,
    _STYLE_FULL,
    _STYLE_SINGLE,
)

# ═══════════════════════════════════════════════════════════════
# Module-Level Constants
# ═══════════════════════════════════════════════════════════════

# Command Prefix

# Dict Keys

# URL Schemes (for detection)

# zPath Symbols (for detection)

# Return Codes (zCLI standard)

# Display Colors

# Display Styles

# Display Messages

# Display Indents

# Log Messages


# ═══════════════════════════════════════════════════════════════
# Main Facade Class
# ═══════════════════════════════════════════════════════════════

class zOpen:
    """
    Main facade class for file and URL opening operations.

    This class provides the primary interface for the zOpen subsystem, handling
    initialization, request parsing, type detection, routing to specialized modules,
    and optional hook execution.

    Attributes:
        zcli: Reference to main zCLI instance
        session: zCLI session dictionary (from zcli.session)
        logger: Logger instance (from zcli.logger)
        display: zDisplay instance (from zcli.display)
        zfunc: zFunc instance (from zcli.zfunc) for hook execution
        dialog: zDialog instance (from zcli.dialog) for interactive prompts
        mycolor: Display color identifier ("ZOPEN")

    Public Methods:
        handle(zHorizontal: str | dict) → str:
            Main entry point for opening operations

    Facade Pattern:
        This class delegates all complex logic to specialized modules:
        - zPath resolution → open_modules.open_paths
        - URL opening → open_modules.open_urls
        - File opening → open_modules.open_files

        The facade only handles:
        - Request parsing (string vs dict format)
        - Type detection (URL vs zPath vs file)
        - Routing to appropriate module
        - Hook execution (onSuccess/onFail)

    Integration with zCLI:
        Initialized in zCLI.__init__() (line ~210):
            self.open = zOpen(self)

        Called from zDispatch (dispatch_launcher.py):
            return self.zcli.open.handle(zHorizontal)

    Version: v1.5.4
    """

    def __init__(self, zcli: Any) -> None:
        """
        Initialize zOpen with zCLI instance.

        Args:
            zcli: Main zCLI instance

        Raises:
            ValueError: If zcli is None or missing required attributes

        Initialization Flow:
            1. Validate zcli instance
            2. Store references to required subsystems
            3. Display initialization message via zDisplay

        Required zCLI Attributes:
            - session: Session dictionary
            - logger: Logging instance
            - display: zDisplay instance
            - zfunc: zFunc instance (for hooks)
            - dialog: zDialog instance (for prompts)

        Example:
            >>> zcli = zCLI()
            >>> zopen = zOpen(zcli)
            # Displays: "zOpen Ready"

        Version: v1.5.4
        """
        if zcli is None:
            raise ValueError("zOpen requires a zCLI instance")

        if not hasattr(zcli, 'session'):
            raise ValueError("Invalid zCLI instance: missing 'session' attribute")

        # Store references to zCLI subsystems
        self.zcli = zcli
        self.session = zcli.session
        self.logger = zcli.logger
        self.display = zcli.display
        self.zfunc = zcli.zfunc
        self.dialog = zcli.dialog
        self.mycolor = COLOR_ZOPEN

        # Display initialization message
        self.display.zDeclare(
            _MSG_ZOPEN_READY,
            color=self.mycolor,
            indent=_INDENT_INIT,
            style=_STYLE_FULL
        )

    def handle(self, zHorizontal: str | dict[str, Any]) -> str:
        """
        Handle zOpen operations with optional hooks.

        This is the main entry point for all opening operations. It parses the input,
        detects the type (URL/zPath/file), routes to the appropriate handler module,
        and executes optional hooks based on the result.

        Args:
            zHorizontal: Opening request in string or dict format

        Returns:
            "zBack" if successful, "stop" if failed, or hook result if hook executes

        Input Formats:
            String: "zOpen(path_or_url)"
                - Example: "zOpen(/path/to/file.txt)"
                - Example: "zOpen(https://example.com)"
                - No hooks supported in string format

            Dict: {"zOpen": {"path": "...", "onSuccess": "...", "onFail": "..."}}
                - path: Required, path or URL to open
                - onSuccess: Optional, zFunc callback on success
                - onFail: Optional, zFunc callback on failure

        Processing Flow:
            1. Display "Handle zOpen" message and breadcrumbs
            2. Parse input format (string vs dict)
            3. Extract path/URL and optional hooks
            4. Detect type and route:
                - http/https/www → open_url() (open_modules.open_urls)
                - @ or ~ → resolve_zpath() + open_file() (open_modules)
                - Other → open_file() (open_modules.open_files)
            5. Execute hooks if present:
                - onSuccess if result == "zBack"
                - onFail if result == "stop"
            6. Return result or hook result

        Type Detection:
            URLs: parsed.scheme in ("http", "https") or path.startswith("www.")
                → open_url(url, session, display, logger)

            zPaths: path.startswith("@") or path.startswith("~")
                → resolve_zpath(path, session, logger)
                → open_file(resolved_path, session, display, dialog, logger)

            Local Files: Everything else
                → os.path.abspath(os.path.expanduser(path))
                → open_file(path, session, display, dialog, logger)

        Hook Execution:
            onSuccess Hook:
                - Triggered when result == "zBack"
                - Displays: "[HOOK] onSuccess"
                - Executes: self.zfunc.handle(on_success)
                - Returns: Hook result (replaces original result)

            onFail Hook:
                - Triggered when result == "stop"
                - Displays: "[HOOK] onFail"
                - Executes: self.zfunc.handle(on_fail)
                - Returns: Hook result (replaces original result)

        Example Usage:
            # String format (no hooks)
            >>> result = zopen.handle("zOpen(/path/to/file.txt)")
            "zBack"

            # Dict format (with hooks)
            >>> result = zopen.handle({
                "zOpen": {
                    "path": "https://github.com",
                    "onSuccess": "log_success()",
                    "onFail": "log_error()"
                }
            })
            "zBack"  # Or hook result if hook executes

            # zPath format
            >>> result = zopen.handle("zOpen(@.README.md)")
            "zBack"

        Integration Notes:
            - Called by zDispatch.dispatch_launcher (line ~428)
            - Uses zDisplay for output (mode-agnostic)
            - Uses zFunc for hook callbacks
            - Delegates to open_modules for all opening logic
            - Session modernization: Uses constants from zConfig

        See Also:
            - open_modules.open_url(): URL opening
            - open_modules.resolve_zpath(): zPath resolution
            - open_modules.open_file(): File opening by extension

        Version: v1.5.4
        """
        # Display handle message and breadcrumbs
        self.display.zDeclare(
            _MSG_HANDLE_ZOPEN,
            color=self.mycolor,
            indent=_INDENT_HANDLE,
            style=_STYLE_FULL
        )
        self.display.zCrumbs(self.session)

        self.logger.debug(_LOG_INCOMING_REQUEST, zHorizontal)

        # Parse input - support both string and dict formats
        if isinstance(zHorizontal, dict):
            # Dict format: {"zOpen": {"path": "...", "onSuccess": "...", "onFail": "..."}}
            zopen_obj = zHorizontal.get(DICT_KEY_ZOPEN, {})
            raw_path = zopen_obj.get(DICT_KEY_PATH, "")
            on_success = zopen_obj.get(DICT_KEY_ON_SUCCESS)
            on_fail = zopen_obj.get(DICT_KEY_ON_FAIL)
        else:
            # String format: "zOpen(path)"
            raw_path = zHorizontal[len(_CMD_PREFIX):-1].strip().strip('"').strip("'")
            on_success = None
            on_fail = None

        self.logger.debug(_LOG_PARSED_PATH, raw_path)

        # Determine type and route to appropriate handler
        parsed = urlparse(raw_path)

        if parsed.scheme in (URL_SCHEME_HTTP, URL_SCHEME_HTTPS) or raw_path.startswith(URL_PREFIX_WWW):
            # URL handling → open_modules.open_urls
            url = raw_path if parsed.scheme else f"{URL_SCHEME_HTTPS_DEFAULT}{raw_path}"
            result = open_url(url, self.session, self.display, self.logger)

        elif raw_path.startswith(ZPATH_SYMBOL_WORKSPACE) or raw_path.startswith(ZPATH_SYMBOL_ABSOLUTE):
            # zPath handling → open_modules.open_paths + open_modules.open_files
            resolved_path = resolve_zpath(raw_path, self.session, self.logger)
            if not resolved_path:
                # Resolution failed
                result = RETURN_STOP
            else:
                # Open resolved file
                result = open_file(resolved_path, self.session, self.display, self.dialog, self.logger)

        else:
            # Local file handling → open_modules.open_files
            path = os.path.abspath(os.path.expanduser(raw_path))
            result = open_file(path, self.session, self.display, self.dialog, self.logger)

        # Execute hooks based on result
        if result == RETURN_ZBACK and on_success:
            self.logger.info(_LOG_EXEC_SUCCESS_HOOK, on_success)
            self.display.zDeclare(
                _MSG_HOOK_SUCCESS,
                color=self.mycolor,
                indent=_INDENT_HOOK,
                style=_STYLE_SINGLE
            )
            return self.zfunc.handle(on_success)

        if result == RETURN_STOP and on_fail:
            self.logger.info(_LOG_EXEC_FAIL_HOOK, on_fail)
            self.display.zDeclare(
                _MSG_HOOK_FAIL,
                color=self.mycolor,
                indent=_INDENT_HOOK,
                style=_STYLE_SINGLE
            )
            return self.zfunc.handle(on_fail)

        return result

    def _launch_media_player(
        self,
        media_path: str,
        player_type: str,
        get_launch_cmd_func,
        media_type_display: str
    ) -> str:
        """
        Internal helper to launch media players with common error handling.
        
        Consolidates shared logic for open_image/video/audio methods, eliminating
        ~250 lines of duplication across 3 methods.
        
        Args:
            media_path: Path to the media file (relative or absolute)
            player_type: Key in zMachine dict ("image_viewer", "video_player", "audio_player")
            get_launch_cmd_func: Function to get platform-specific launch command
            media_type_display: Display name for media type ("image", "video", "audio")
            
        Returns:
            "zBack" if successfully opened, "stop" if failed
            
        Version: v1.6.1 (DRY Refactoring - extracted from open_image/video/audio)
        """
        # Get player/viewer from session
        zmachine = self.session.get(SESSION_KEY_ZMACHINE, {})
        player_name = zmachine.get(player_type, "unknown")
        
        # Handle special cases
        if player_name in ("none", "unknown"):
            self.logger.warning(f"No {media_type_display} player available (player: {player_name})")
            self.display.warning(
                f"No {media_type_display} {'viewer' if media_type_display == 'image' else 'player'} detected. "
                f"Cannot {'open' if media_type_display == 'image' else 'play'} {media_type_display}s in this environment.",
                indent=1
            )
            return RETURN_STOP
        
        # Get platform-specific launch command
        cmd, args = get_launch_cmd_func(player_name)
        
        if cmd is None:
            self.logger.error(f"Failed to get launch command for {media_type_display} player: {player_name}")
            self.display.error(
                f"{media_type_display.capitalize()} {'viewer' if media_type_display == 'image' else 'player'} "
                f"'{player_name}' is not supported on this platform.",
                indent=1
            )
            return RETURN_STOP
        
        # Resolve absolute path
        absolute_path = os.path.abspath(os.path.expanduser(media_path))
        
        # Check if file exists
        if not os.path.exists(absolute_path):
            self.logger.error(f"{media_type_display.capitalize()} file not found: {absolute_path}")
            self.display.error(
                f"{media_type_display.capitalize()} file not found: {media_path}",
                indent=1
            )
            return RETURN_STOP
        
        # Launch media player
        try:
            full_command = [cmd] + args + [absolute_path]
            self.logger.info(f"Launching {media_type_display} player: {' '.join(full_command)}")
            
            subprocess.Popen(
                full_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.logger.info(f"Successfully opened {media_type_display} in {player_name}")
            self.display.success(
                f"Opened {media_type_display} in {player_name}",
                indent=1
            )
            return RETURN_ZBACK
            
        except Exception as e:
            self.logger.error(f"Failed to open {media_type_display} with {player_name}: {e}")
            self.display.error(
                f"Failed to open {media_type_display}: {e}",
                indent=1
            )
            return RETURN_STOP

    def open_image(self, image_path: str) -> str:
        """
        Open an image file in the system's default image viewer or browser (for URLs).
        
        Terminal-First Design:
        - Detects if image_path is a URL (http/https/www)
        - Detects if image_path is a server path (/static/, /media/, etc.)
        - URLs/server paths → Opens in browser
        - Local paths → Opens in image viewer app
        
        Uses zMachine's detected image viewer and platform-specific launch commands.
        Falls back gracefully if viewer is not available or headless environment.
        
        Args:
            image_path: Path to the image file (local path, URL, or server path)
            
        Returns:
            "zBack" if successfully opened, "stop" if failed
            
        Detection Flow:
            1. Check if image_path is a URL → open in browser
            2. Check if image_path is a server path → construct URL and open in browser
            3. Otherwise, get image_viewer from session[zMachine]
            4. Get platform-specific launch command
            5. Resolve image path (absolute)
            6. Check if file exists
            7. Launch viewer with subprocess
            8. Handle errors gracefully
            
        Examples:
            >>> zcli.open.open_image("screenshot.png")
            # macOS: open -a Preview screenshot.png
            # Linux: eog screenshot.png
            # Windows: start screenshot.png
            
            >>> zcli.open.open_image("https://picsum.photos/200/300")
            # Opens in browser (correct for web images)
            
            >>> zcli.open.open_image("/static/brand/logo.png")
            # Opens http://127.0.0.1:8080/static/brand/logo.png in browser
            
        Version: v1.6.0 (Server Path Detection)
        """
        # Detect if it's a URL → open in browser
        parsed = urlparse(image_path)
        if parsed.scheme in (URL_SCHEME_HTTP, URL_SCHEME_HTTPS) or image_path.startswith(URL_PREFIX_WWW):
            self.logger.info(f"Detected web image URL: {image_path}")
            url = image_path if parsed.scheme else f"{URL_SCHEME_HTTPS_DEFAULT}{image_path}"
            return open_url(url, self.session, self.display, self.logger)
        
        # Detect if it's an absolute filesystem path that should be served by zServer
        # Use zParser to convert absolute path to web-relative path
        if image_path.startswith('/'):
            # Get server config from zCLI instance (zServer subsystem)
            http_config = getattr(self.zcli.config, 'http_server', None)
            
            if http_config and http_config.enabled:
                # Use zParser to convert absolute filesystem path to web-relative path
                web_path = self.zcli.zparser.absolute_path_to_web_path(image_path)
                
                # If zParser converted the path (it's under serve_path), construct URL
                if web_path != image_path or web_path.startswith('/') and not web_path.startswith('/Users') and not web_path.startswith('/home'):
                    host = http_config.host
                    port = http_config.port
                    ssl_enabled = getattr(http_config, 'ssl_enabled', False)
                    scheme = 'https' if ssl_enabled else 'http'
                    
                    # Construct full URL
                    server_url = f"{scheme}://{host}:{port}{web_path}"
                    self.logger.info(f"Detected server path: {image_path} → {server_url}")
                    self.display.info(
                        f"Opening server image: {image_path}",
                        indent=1
                    )
                    return open_url(server_url, self.session, self.display, self.logger)
                else:
                    self.logger.warning(f"Path not under zServer serve_path: {image_path}")
                    # Fall through to local file handling
            else:
                self.logger.warning(f"Absolute path detected but zServer not enabled: {image_path}")
                # Fall through to local file handling (will fail if not a real local path)
        
        # Local file handling (consolidated via helper)
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.helpers import get_image_viewer_launch_command
        return self._launch_media_player(
            image_path,
            "image_viewer",
            get_image_viewer_launch_command,
            "image"
        )

    def open_video(self, video_path: str) -> str:
        """
        Open a video file in the system's default video player.
        
        Uses zMachine's detected video player and platform-specific launch commands.
        Falls back gracefully if player is not available or headless environment.
        
        Args:
            video_path: Path to the video file (relative or absolute)
            
        Returns:
            "zBack" if successfully opened, "stop" if failed
            
        Detection Flow:
            1. Get video_player from session[zMachine]
            2. Get platform-specific launch command
            3. Resolve video path (absolute)
            4. Check if file exists
            5. Launch player with subprocess
            6. Handle errors gracefully
            
        Examples:
            >>> zcli.open.open_video("movie.mp4")
            # macOS: open -a "QuickTime Player" movie.mp4
            # Linux: vlc movie.mp4
            # Windows: start movie.mp4
            
        Version: v1.5.8 (Video Support)
        """
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.helpers import get_video_player_launch_command
        return self._launch_media_player(
            video_path,
            "video_player",
            get_video_player_launch_command,
            "video"
        )

    def open_audio(self, audio_path: str) -> str:
        """
        Open an audio file in the system's default audio player.
        
        Uses zMachine's detected audio player and platform-specific launch commands.
        Falls back gracefully if player is not available or headless environment.
        
        Args:
            audio_path: Path to the audio file (relative or absolute)
            
        Returns:
            "zBack" if successfully opened, "stop" if failed
            
        Detection Flow:
            1. Get audio_player from session[zMachine]
            2. Get platform-specific launch command
            3. Resolve audio path (absolute)
            4. Check if file exists
            5. Launch player with subprocess
            6. Handle errors gracefully
            
        Examples:
            >>> zcli.open.open_audio("song.mp3")
            # macOS: open -a Music song.mp3
            # Linux: vlc song.mp3
            # Windows: start song.mp3
            
        Version: v1.5.8 (Audio Support)
        """
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.helpers import get_audio_player_launch_command
        return self._launch_media_player(
            audio_path,
            "audio_player",
            get_audio_player_launch_command,
            "audio"
        )


# ═══════════════════════════════════════════════════════════════
# Module Exports
# ═══════════════════════════════════════════════════════════════

__all__ = ["zOpen"]
