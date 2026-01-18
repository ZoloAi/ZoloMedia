# zCLI/subsystems/zOpen/open_modules/open_urls.py

"""
URL Opening Module

This module provides URL opening functionality for the zOpen subsystem, handling
http/https URLs in the user's preferred or system default browser.

Architecture Position:
    - Tier 1b (Foundation Module) of zOpen's 3-tier architecture
    - Provides URL opening services for the facade layer

Key Features:
    - Browser Preference: Uses zMachine.browser from session if available
    - Fallback Strategy: Falls back to system default browser if preferred unavailable
    - Display Integration: Shows URL info via zDisplay.json_data()
    - Error Handling: Graceful fallback to URL display if browser fails
    - Cross-Platform: Works on Windows, macOS, Linux

URL Handling Flow:
    1. Display URL info (scheme, domain, path) via zDisplay
    2. Get browser preference from session (zMachine.browser)
    3. Try preferred browser if available (subprocess)
    4. Fallback to system default (webbrowser module)
    5. Final fallback: Display URL info for manual copy-paste

Integration Points:
    - zConfig: Session access for browser preference
    - zDisplay: json_data() for URL info, zDeclare() for status messages
    - zOpen facade: Primary entry point via handle()

Dependencies:
    - subprocess: Launch specific browser applications
    - webbrowser: System default browser fallback
    - urlparse: Parse and validate URL components
    - shutil: Check browser availability (shutil.which)
    - zConfig constants: SESSION_KEY_ZMACHINE for session dict keys

Usage Example:
    from zOS.L2_Core.k_zOpen.open_modules.open_urls import open_url

    session = {"zMachine": {"browser": "firefox"}}
    display = zcli.display
    logger = zcli.logger

    result = open_url("https://example.com", session, display, logger)
    # Returns: "zBack" on success, "stop" on failure

Version History:
    - v1.5.4: Extracted from monolithic zOpen.py, added industry-grade documentation
    - v1.5.4: Added type hints, constants, and session modernization
    - v1.5.4: Enhanced error handling and fallback strategies

Author: zCLI Development Team
"""

from zOS import subprocess, webbrowser, urlparse, Any

# Import centralized session constants
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
    SESSION_KEY_ZMACHINE,
    SESSION_KEY_BROWSER,
)

# Import platform-specific browser launch command helper from zConfig
from zOS.L1_Foundation.a_zConfig.zConfig_modules.helpers import get_browser_launch_command
from .open_constants import (
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_SUCCESS,
    RETURN_STOP,
    RETURN_ZBACK,
    URL_SCHEMES_SUPPORTED,
    URL_SCHEME_HTTP,
    URL_SCHEME_HTTPS,
    ZMACHINE_KEY_BROWSER,
    _BROWSERS_SKIP,
    _ERR_BROWSER_FAILED_URL,
    _ERR_URL_OPEN_FAILED,
    _INDENT_URL_INFO,
    _LOG_BROWSER_ERROR,
    _LOG_BROWSER_FAILED,
    _LOG_OPENING_URL,
    _LOG_SUCCESS_DEFAULT,
    _LOG_SUCCESS_SPECIFIC,
    _LOG_USING_BROWSER,
    _MSG_BROWSER_ERROR,
    _MSG_BROWSER_FAILED_URL,
    _MSG_OPENED_BROWSER_URL,
    _MSG_OPENED_DEFAULT,
    _MSG_URL_INFO_TITLE,
    _MSG_URL_MANUAL,
    _STYLE_SECTION,
    _STYLE_SINGLE,
)

# ═══════════════════════════════════════════════════════════════
# Module-Level Constants
# ═══════════════════════════════════════════════════════════════

# URL Schemes

# Return Codes (zCLI standard)

# Session Keys (zMachine sub-keys)

# Browsers to skip (use system default instead)

# Display Colors

# Display Styles

# Display Messages

# Error Messages

# Log Messages

# Display Indents


# ═══════════════════════════════════════════════════════════════
# Public API Functions
# ═══════════════════════════════════════════════════════════════

def open_url(
    url: str,
    session: dict[str, Any],
    display: Any,
    logger: Any
) -> str:
    """
    Handle URL opening using user's preferred or system default browser.

    This function displays URL information via zDisplay, retrieves the user's
    browser preference from session, and attempts to open the URL in the
    preferred browser or falls back to the system default.

    Args:
        url: Full URL to open (must include scheme: http:// or https://)
        session: zCLI session dictionary containing machine configuration
        display: zDisplay instance for output and status messages
        logger: Logger instance for debug/error output

    Returns:
        "zBack" if URL opened successfully, "stop" if all attempts failed

    Opening Flow:
        1. Display URL info (scheme, domain, path) via zDisplay.json_data()
        2. Get browser preference from session[zMachine][browser]
        3. Attempt to open with preferred browser (if available)
        4. Fallback to system default browser (webbrowser module)
        5. Final fallback: Display URL info for manual copy-paste

    Browser Selection Logic:
        - Preferred: session[SESSION_KEY_ZMACHINE][ZMACHINE_KEY_BROWSER]
        - Skip browsers: "unknown", "Safari", "Edge" (not CLI-invokable)
        - Check availability: shutil.which(browser)
        - Default fallback: webbrowser.open(url)

    URL Info Display:
        Displays JSON structure via zDisplay.json_data():
        {
            "url": "https://example.com/path",
            "scheme": "https",
            "domain": "example.com",
            "path": "/path"
        }

    Return Values:
        - "zBack": URL opened successfully (browser launched)
        - "stop": All opening attempts failed (displayed fallback info)

    Error Handling:
        - Browser not found: Falls back to system default
        - Browser launch fails: Falls back to system default
        - System default fails: Displays URL info for manual opening
        - All exceptions caught and logged

    Integration Notes:
        - Called by zOpen facade after URL detection
        - Uses zDisplay for all output (mode-agnostic)
        - Uses centralized SESSION_KEY_ZMACHINE constant
        - Delegates to _open_url_browser() for actual opening
        - Delegates to _display_url_fallback() on failure

    Example Usage:
        >>> session = {SESSION_KEY_ZMACHINE: {ZMACHINE_KEY_BROWSER: "firefox"}}
        >>> result = open_url("https://github.com", session, display, logger)
        "zBack"  # Success

        >>> session = {SESSION_KEY_ZMACHINE: {}}  # No browser preference
        >>> result = open_url("https://example.com", session, display, logger)
        "zBack"  # Opened in system default

    See Also:
        - _open_url_browser(): Actual browser launching logic
        - _display_url_fallback(): Final fallback display
        - zDisplay.json_data(): Mode-agnostic JSON output

    Version: v1.5.4
    """
    logger.info(_LOG_OPENING_URL, url)

    # Enhanced display: Show URL info as JSON
    parsed = urlparse(url)
    url_info = {
        "url": url,
        "scheme": parsed.scheme,
        "domain": parsed.netloc,
        "path": parsed.path
    }
    display.json_data(url_info, color=True, indent=_INDENT_URL_INFO)

    # Get browser preference (priority: session["browser"] → session["zMachine"]["browser"])
    browser = session.get(SESSION_KEY_BROWSER) or session.get(SESSION_KEY_ZMACHINE, {}).get(ZMACHINE_KEY_BROWSER)

    if browser:
        logger.info(_LOG_USING_BROWSER, browser)

    # Try to open with user's preferred browser or default
    return _open_url_browser(url, browser, display, logger)


# ═══════════════════════════════════════════════════════════════
# Private Helper Functions
# ═══════════════════════════════════════════════════════════════

def _open_url_browser(
    url: str,
    browser: str | None,
    display: Any,
    logger: Any
) -> str:
    """
    Open URL in specified or default browser.

    Internal function that attempts to launch the URL in the preferred browser,
    falling back to system default if preferred is unavailable.

    Args:
        url: Full URL to open
        browser: Preferred browser name (e.g., "firefox", "chrome") or None
        display: zDisplay instance for status messages
        logger: Logger instance for debug/error output

    Returns:
        "zBack" if opened successfully, result of _display_url_fallback() on failure

    Browser Launch Logic:
        1. If browser specified and not in skip list:
            - Check availability with shutil.which(browser)
            - If available: subprocess.run([browser, url])
            - If successful: Return "zBack"
        2. Fallback to webbrowser.open(url)
        3. If webbrowser succeeds: Return "zBack"
        4. If all fail: Call _display_url_fallback()

    Skip List:
        - "unknown": No browser configured
        - "Safari": macOS default, use webbrowser.open()
        - "Edge": Windows default, use webbrowser.open()

    Display Integration:
        - Success (preferred): "Opened URL in {browser}" (GREEN)
        - Success (default): "Opened URL in default browser" (GREEN)
        - Failure: "Browser failed to open URL" (RED)
        - Error: "Browser error: {error}" (RED)

    Example:
        >>> _open_url_browser("https://example.com", "firefox", display, logger)
        "zBack"  # Firefox launched successfully

    Version: v1.5.4
    """
    try:
        # Try to use specific browser if available
        if browser and browser not in _BROWSERS_SKIP:
            # Get platform-specific launch command from zConfig
            cmd, args = get_browser_launch_command(browser)
            
            if cmd:
                try:
                    # Build full command: cmd + args + [url]
                    full_cmd = [cmd] + args + [url]
                    subprocess.run(full_cmd, check=False, timeout=5)
                    logger.info(_LOG_SUCCESS_SPECIFIC, browser)
                    display.zDeclare(
                        _MSG_OPENED_BROWSER_URL.format(browser=browser),
                        color=COLOR_SUCCESS,
                        indent=_INDENT_URL_INFO,
                        style=_STYLE_SINGLE
                    )
                    return RETURN_ZBACK
                except Exception as e:
                    logger.warning("Browser launch failed for %s: %s", browser, e)

        # Fallback to system default browser (webbrowser module)
        success = webbrowser.open(url)
        if success:
            logger.info(_LOG_SUCCESS_DEFAULT)
            display.zDeclare(
                _MSG_OPENED_DEFAULT,
                color=COLOR_SUCCESS,
                indent=_INDENT_URL_INFO,
                style=_STYLE_SINGLE
            )
            return RETURN_ZBACK
        else:
            logger.warning(_LOG_BROWSER_FAILED)
            display.zDeclare(
                _MSG_BROWSER_FAILED_URL,
                color=COLOR_ERROR,
                indent=_INDENT_URL_INFO,
                style=_STYLE_SINGLE
            )
            return _display_url_fallback(url, display, logger)

    except Exception as e:
        logger.warning(_LOG_BROWSER_ERROR, e)
        display.zDeclare(
            _MSG_BROWSER_ERROR.format(error=str(e)),
            color=COLOR_ERROR,
            indent=_INDENT_URL_INFO,
            style=_STYLE_SINGLE
        )
        return _display_url_fallback(url, display, logger)


def _display_url_fallback(
    url: str,
    display: Any,
    logger: Any
) -> str:
    """
    Display URL information when browser opening fails.

    Final fallback when all browser launching attempts fail. Displays the URL
    in a readable format for the user to manually copy and paste.

    Args:
        url: URL that failed to open
        display: zDisplay instance for output
        logger: Logger instance for warning output

    Returns:
        Always returns "zBack" (user can see URL and continue)

    Display Format:
        URL Information
        URL: https://example.com
        Unable to open in browser. Please copy and paste into your browser.

    Note:
        This is a graceful degradation - user still gets the URL information
        and can manually open it, so we return "zBack" rather than "stop".

    Example:
        >>> _display_url_fallback("https://example.com", display, logger)
        "zBack"  # URL info displayed for manual copy-paste

    Version: v1.5.4
    """
    logger.warning(_ERR_URL_OPEN_FAILED)

    display.zDeclare(
        _MSG_URL_INFO_TITLE,
        color=COLOR_INFO,
        indent=_INDENT_URL_INFO,
        style=_STYLE_SECTION
    )
    display.write_line(f"URL: {url}")
    display.write_line(_MSG_URL_MANUAL)

    return RETURN_ZBACK


# ═══════════════════════════════════════════════════════════════
# Module Exports
# ═══════════════════════════════════════════════════════════════

__all__ = [
    "open_url",  # Main URL opening function
]

