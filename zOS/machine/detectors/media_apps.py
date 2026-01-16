# zOS/machine/detectors/media_apps.py
"""Image viewer, video player, and audio player detection for Zolo ecosystem."""

import os
import platform
import subprocess
import shutil
from typing import Optional
from .shared import SUBPROCESS_TIMEOUT_SEC, _log_info, _log_warning

# Image viewer constants
IMAGE_VIEWER_MAPPING_MACOS = {
    'preview': 'Preview',
    'pixelmator': 'Pixelmator Pro',
    'affinity': 'Affinity Photo',
    'photoshop': 'Adobe Photoshop',
    'gimp': 'GIMP',
    'xnview': 'XnView',
}

LINUX_IMAGE_VIEWERS = (
    "eog",           # Eye of GNOME (GNOME default)
    "gwenview",      # KDE default
    "feh",           # Lightweight
    "gthumb",        # GNOME
    "ristretto",     # XFCE
    "gpicview",      # LXDE
    "nomacs",        # Cross-platform
    "geeqie",        # Lightweight
    "gimp",          # Power user
)

DEFAULT_MACOS_IMAGE_VIEWER = "Preview"
DEFAULT_LINUX_IMAGE_VIEWER = "eog"
DEFAULT_WINDOWS_IMAGE_VIEWER = "Photos"

# Video player constants
VIDEO_PLAYER_MAPPING_MACOS = {
    'quicktime': 'QuickTime Player',
    'vlc': 'VLC',
    'iina': 'IINA',
    'mpv': 'mpv',
}

LINUX_VIDEO_PLAYERS = (
    "vlc",           # Cross-platform, most common
    "mpv",           # Lightweight
    "totem",         # GNOME default (Videos)
    "celluloid",     # mpv GUI
    "smplayer",      # Feature-rich
    "parole",        # XFCE
    "dragon",        # KDE
)

DEFAULT_MACOS_VIDEO_PLAYER = "QuickTime Player"
DEFAULT_LINUX_VIDEO_PLAYER = "vlc"
DEFAULT_WINDOWS_VIDEO_PLAYER = "Movies"

# Audio player constants
AUDIO_PLAYER_MAPPING_MACOS = {
    'music': 'Music',
    'itunes': 'iTunes',
    'vlc': 'VLC',
    'quicktime': 'QuickTime Player',
}

LINUX_AUDIO_PLAYERS = (
    "vlc",           # Cross-platform, most common
    "audacious",     # Lightweight
    "rhythmbox",     # GNOME default
    "clementine",    # Feature-rich
    "deadbeef",      # Minimal
    "mpv",           # Terminal-friendly
    "totem",         # Videos (also plays audio)
)

DEFAULT_MACOS_AUDIO_PLAYER = "Music"
DEFAULT_LINUX_AUDIO_PLAYER = "vlc"
DEFAULT_WINDOWS_AUDIO_PLAYER = "Music"


# Image Viewer Detection

def detect_image_viewer(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Detect default image viewer via env var or platform-specific methods.
    
    Detection Strategy:
    - macOS: Query LaunchServices for image/png handler → Preview
    - Linux: Check GUI environment (DISPLAY) → scan PATH for viewers → soft error if headless
    - Windows: Default to Photos → Paint fallback
    
    Returns:
        str: Image viewer name (e.g., "Preview", "eog", "Photos") or "none" if headless
    """
    # Check env var first (e.g., IMAGE_VIEWER="feh")
    viewer = os.getenv("IMAGE_VIEWER")
    if viewer:
        return viewer

    system = platform.system()
    if system == "Darwin":
        viewer = _detect_macos_image_viewer(log_level, is_production)
    elif system == "Linux":
        viewer = _detect_linux_image_viewer(log_level, is_production)
    elif system == "Windows":
        viewer = _detect_windows_image_viewer(log_level, is_production)
    else:
        viewer = "unknown"

    return viewer


def _detect_macos_image_viewer(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Query macOS LaunchServices for default image handler, fallback to Preview.
    
    Uses same pattern as browser detection - queries LSHandlers for image/png associations.
    """
    try:
        # Check LaunchServices for image/png handler
        result = subprocess.run(
            ['defaults', 'read', 'com.apple.LaunchServices/com.apple.launchservices.secure', 'LSHandlers'],
            capture_output=True, 
            text=True, 
            timeout=SUBPROCESS_TIMEOUT_SEC, 
            check=False
        )

        output_lower = result.stdout.lower()
        for key, name in IMAGE_VIEWER_MAPPING_MACOS.items():
            if key in output_lower:
                _log_info(f"Found default image viewer via LaunchServices: {name}", log_level, is_production)
                return name

    except Exception as e:
        _log_warning(f"Could not query LaunchServices for image viewer: {e}", log_level, is_production)

    return DEFAULT_MACOS_IMAGE_VIEWER


def _detect_linux_image_viewer(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Query Linux for GUI image viewer, gracefully handle headless environments.
    
    Strategy:
    1. Check if GUI is available (DISPLAY environment variable)
    2. If headless → log soft warning, return "none"
    3. If GUI → scan PATH for common image viewers
    4. Fallback to eog (most common)
    """
    # Check for GUI environment
    if not os.getenv("DISPLAY"):
        _log_warning("No GUI detected (DISPLAY not set). Image viewing unavailable in headless mode.", log_level, is_production)
        return "none"

    # Try xdg-mime first (freedesktop.org standard)
    try:
        result = subprocess.run(
            ['xdg-mime', 'query', 'default', 'image/png'],
            capture_output=True, 
            text=True, 
            timeout=SUBPROCESS_TIMEOUT_SEC, 
            check=False
        )
        if result.returncode == 0:
            desktop_file = result.stdout.strip().lower()
            # Extract viewer name from .desktop file (e.g., "eog.desktop" → "eog")
            if desktop_file:
                viewer_name = desktop_file.replace('.desktop', '')
                if shutil.which(viewer_name):
                    _log_info(f"Found image viewer via xdg-mime: {viewer_name}", log_level, is_production)
                    return viewer_name
    except Exception:
        pass  # Fall through to PATH scan

    # Scan PATH for common image viewers
    for viewer in LINUX_IMAGE_VIEWERS:
        if shutil.which(viewer):
            _log_info(f"Found image viewer in PATH: {viewer}", log_level, is_production)
            return viewer

    # Fallback
    _log_warning(f"No image viewer found in PATH. Defaulting to {DEFAULT_LINUX_IMAGE_VIEWER} (may not be installed).", log_level, is_production)
    return DEFAULT_LINUX_IMAGE_VIEWER


def _detect_windows_image_viewer(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Detect Windows image viewer, default to Photos app.
    
    Windows 10/11: Photos app (modern)
    Fallback: Paint (mspaint) - always available
    """
    # Windows 10/11 Photos app is default
    # We default optimistically and let zOpen handle actual invocation
    _log_info(f"Using Windows default image viewer: {DEFAULT_WINDOWS_IMAGE_VIEWER}", log_level, is_production)
    return DEFAULT_WINDOWS_IMAGE_VIEWER


def enumerate_installed_image_viewers() -> list:
    """
    Return list of all installed image viewers on this system.
    
    Returns:
        List of image viewer names (e.g., ["Preview", "GIMP", "eog"])
    """
    installed = []
    system = platform.system()
    
    if system == "Darwin":
        # macOS: Check /Applications/ folder
        macos_viewers = [
            ("Preview", "Preview"),
            ("Pixelmator Pro", "Pixelmator Pro"),
            ("Affinity Photo", "Affinity Photo"),
            ("Adobe Photoshop 2024", "Photoshop"),
            ("GIMP", "GIMP"),
            ("XnView MP", "XnView"),
        ]
        
        for app_name, display_name in macos_viewers:
            if os.path.exists(f"/Applications/{app_name}.app"):
                installed.append(display_name)
                
    elif system == "Linux":
        # Linux: Check PATH for executables
        for viewer in LINUX_IMAGE_VIEWERS:
            if shutil.which(viewer):
                installed.append(viewer)
                
    elif system == "Windows":
        # Windows: Default Photos app is always available
        installed.append("Photos")
    
    return installed


def enumerate_installed_video_players() -> list:
    """
    Return list of all installed video players on this system.
    
    Returns:
        List of video player names (e.g., ["QuickTime Player", "VLC", "IINA"])
    """
    installed = []
    system = platform.system()
    
    if system == "Darwin":
        # macOS: Check /Applications/ folder
        macos_players = [
            ("QuickTime Player", "QuickTime Player"),
            ("VLC", "VLC"),
            ("IINA", "IINA"),
            ("mpv", "mpv"),
        ]
        
        for app_name, display_name in macos_players:
            if os.path.exists(f"/Applications/{app_name}.app"):
                installed.append(display_name)
        
        # Check PATH for CLI tools
        if shutil.which("mpv") and "mpv" not in installed:
            installed.append("mpv")
                
    elif system == "Linux":
        # Linux: Check PATH for executables
        for player in LINUX_VIDEO_PLAYERS:
            if shutil.which(player):
                installed.append(player)
                
    elif system == "Windows":
        # Windows: Default Movies app is always available
        installed.append("Movies")
    
    return installed


def enumerate_installed_audio_players() -> list:
    """
    Return list of all installed audio players on this system.
    
    Returns:
        List of audio player names (e.g., ["Music", "VLC", "Audacious"])
    """
    installed = []
    system = platform.system()
    
    if system == "Darwin":
        # macOS: Check /Applications/ folder
        macos_players = [
            ("Music", "Music"),
            ("iTunes", "iTunes"),
            ("VLC", "VLC"),
            ("QuickTime Player", "QuickTime Player"),
        ]
        
        for app_name, display_name in macos_players:
            if os.path.exists(f"/Applications/{app_name}.app"):
                installed.append(display_name)
                
    elif system == "Linux":
        # Linux: Check PATH for executables
        for player in LINUX_AUDIO_PLAYERS:
            if shutil.which(player):
                installed.append(player)
                
    elif system == "Windows":
        # Windows: Default Music app is always available
        installed.append("Music")
    
    return installed


def get_image_viewer_launch_command(viewer_name: str) -> tuple:
    """
    Get platform-specific command to launch an image viewer.
    
    Args:
        viewer_name: Viewer name (e.g., "Preview", "eog", "Photos")
                    Case-insensitive, normalized internally
    
    Returns:
        Tuple of (command, args_template) where:
        - macOS: ("open", ["-a", "Preview"]) - use 'open -a "App Name"'
        - Linux: ("eog", []) - direct executable
        - Windows: ("start", [""]) - use start command for Photos
        - Unknown/None: (None, []) - viewer not available
    
    Examples:
        >>> get_image_viewer_launch_command("Preview")
        # macOS: ("open", ["-a", "Preview"])
        
        >>> get_image_viewer_launch_command("eog")
        # Linux: ("eog", [])
        
        >>> get_image_viewer_launch_command("Photos")
        # Windows: ("start", [""])
    """
    if viewer_name == "none" or viewer_name == "unknown":
        return (None, [])
    
    system = platform.system()
    viewer_lower = viewer_name.lower()
    
    # macOS: GUI apps need 'open -a'
    if system == "Darwin":
        macos_apps = {
            "preview": "Preview",
            "pixelmator": "Pixelmator Pro",
            "affinity": "Affinity Photo",
            "photoshop": "Adobe Photoshop",
            "gimp": "GIMP",
            "xnview": "XnView",
        }
        app_name = macos_apps.get(viewer_lower)
        if app_name:
            return ("open", ["-a", app_name])
        # If not in mapping, try direct command
        if shutil.which(viewer_lower):
            return (viewer_lower, [])
        return (None, [])
    
    # Linux: Direct executable names
    elif system == "Linux":
        # Check if viewer is in PATH
        if shutil.which(viewer_lower):
            return (viewer_lower, [])
        return (None, [])
    
    # Windows: Use 'start' command for default handlers
    elif system == "Windows":
        if viewer_lower == "photos":
            # Windows Photos app - use 'start' with empty first arg
            return ("start", [""])
        elif viewer_lower == "paint" or viewer_lower == "mspaint":
            return ("mspaint", [])
        # Try direct command
        if shutil.which(viewer_lower):
            return (viewer_lower, [])
        return (None, [])
    
    return (None, [])


# Video Player Detection

def detect_video_player(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Detect default video player via env var or platform-specific methods.
    
    Detection Strategy:
    - macOS: Query LaunchServices for video/mp4 handler → QuickTime Player
    - Linux: Check GUI environment (DISPLAY) → scan PATH for players → soft error if headless
    - Windows: Default to Movies & TV app
    
    Returns:
        str: Video player name (e.g., "QuickTime Player", "VLC", "Movies") or "none" if headless
    """
    # Check env var first (e.g., VIDEO_PLAYER="vlc")
    player = os.getenv("VIDEO_PLAYER")
    if player:
        return player

    system = platform.system()
    if system == "Darwin":
        player = _detect_macos_video_player(log_level, is_production)
    elif system == "Linux":
        player = _detect_linux_video_player(log_level, is_production)
    elif system == "Windows":
        player = _detect_windows_video_player(log_level, is_production)
    else:
        player = "unknown"

    return player


def _detect_macos_video_player(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Query macOS LaunchServices for default video handler, fallback to QuickTime Player.
    
    Uses same pattern as image viewer detection - queries LSHandlers for video/mp4 associations.
    """
    try:
        # Check LaunchServices for video/mp4 handler
        result = subprocess.run(
            ['defaults', 'read', 'com.apple.LaunchServices/com.apple.launchservices.secure', 'LSHandlers'],
            capture_output=True, 
            text=True, 
            timeout=SUBPROCESS_TIMEOUT_SEC, 
            check=False
        )

        output_lower = result.stdout.lower()
        for key, name in VIDEO_PLAYER_MAPPING_MACOS.items():
            if key in output_lower:
                _log_info(f"Found default video player via LaunchServices: {name}", log_level, is_production)
                return name

    except Exception as e:
        _log_warning(f"Could not query LaunchServices for video player: {e}", log_level, is_production)

    return DEFAULT_MACOS_VIDEO_PLAYER


def _detect_linux_video_player(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Query Linux for GUI video player, gracefully handle headless environments.
    
    Strategy:
    1. Check if GUI is available (DISPLAY environment variable)
    2. If headless → log soft warning, return "none"
    3. If GUI → scan PATH for common video players
    4. Fallback to vlc (most common)
    """
    # Check for GUI environment
    if not os.getenv("DISPLAY"):
        _log_warning("No GUI detected (DISPLAY not set). Video playback unavailable in headless mode.", log_level, is_production)
        return "none"

    # Try xdg-mime first (freedesktop.org standard)
    try:
        result = subprocess.run(
            ['xdg-mime', 'query', 'default', 'video/mp4'],
            capture_output=True, 
            text=True, 
            timeout=SUBPROCESS_TIMEOUT_SEC, 
            check=False
        )
        if result.returncode == 0:
            desktop_file = result.stdout.strip().lower()
            # Extract player name from .desktop file (e.g., "vlc.desktop" → "vlc")
            if desktop_file:
                player_name = desktop_file.replace('.desktop', '')
                if shutil.which(player_name):
                    _log_info(f"Found video player via xdg-mime: {player_name}", log_level, is_production)
                    return player_name
    except Exception:
        pass  # Fall through to PATH scan

    # Scan PATH for common video players
    for player in LINUX_VIDEO_PLAYERS:
        if shutil.which(player):
            _log_info(f"Found video player in PATH: {player}", log_level, is_production)
            return player

    # Fallback
    _log_warning(f"No video player found in PATH. Defaulting to {DEFAULT_LINUX_VIDEO_PLAYER} (may not be installed).", log_level, is_production)
    return DEFAULT_LINUX_VIDEO_PLAYER


def _detect_windows_video_player(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Detect Windows video player, default to Movies & TV app.
    
    Windows 10/11: Movies & TV app (modern)
    Fallback: Windows Media Player - always available
    """
    # Windows 10/11 Movies & TV app is default
    # We default optimistically and let zOpen handle actual invocation
    _log_info(f"Using Windows default video player: {DEFAULT_WINDOWS_VIDEO_PLAYER}", log_level, is_production)
    return DEFAULT_WINDOWS_VIDEO_PLAYER


def get_video_player_launch_command(player_name: str) -> tuple:
    """
    Get platform-specific command to launch a video player.
    
    Args:
        player_name: Player name (e.g., "QuickTime Player", "VLC", "Movies")
                    Case-insensitive, normalized internally
    
    Returns:
        Tuple of (command, args_template) where:
        - macOS: ("open", ["-a", "QuickTime Player"]) - use 'open -a "App Name"'
        - Linux: ("vlc", []) - direct executable
        - Windows: ("start", [""]) - use start command for Movies
        - Unknown/None: (None, []) - player not available
    
    Examples:
        >>> get_video_player_launch_command("QuickTime Player")
        # macOS: ("open", ["-a", "QuickTime Player"])
        
        >>> get_video_player_launch_command("vlc")
        # Linux: ("vlc", [])
        
        >>> get_video_player_launch_command("Movies")
        # Windows: ("start", [""])
    """
    if player_name == "none" or player_name == "unknown":
        return (None, [])
    
    system = platform.system()
    player_lower = player_name.lower()
    
    # macOS: GUI apps need 'open -a'
    if system == "Darwin":
        macos_apps = {
            "quicktime player": "QuickTime Player",
            "quicktime": "QuickTime Player",
            "vlc": "VLC",
            "iina": "IINA",
            "mpv": "mpv",
        }
        app_name = macos_apps.get(player_lower)
        if app_name:
            return ("open", ["-a", app_name])
        # If not in mapping, try direct command
        if shutil.which(player_lower):
            return (player_lower, [])
        return (None, [])
    
    # Linux: Direct executable names
    elif system == "Linux":
        # Check if player is in PATH
        if shutil.which(player_lower):
            return (player_lower, [])
        return (None, [])
    
    # Windows: Use 'start' command for default handlers
    elif system == "Windows":
        if player_lower == "movies":
            # Windows Movies & TV app - use 'start' with empty first arg
            return ("start", [""])
        elif player_lower == "windows media player" or player_lower == "wmplayer":
            return ("wmplayer", [])
        # Try direct command
        if shutil.which(player_lower):
            return (player_lower, [])
        return (None, [])
    
    return (None, [])


# Audio Player Detection

def detect_audio_player(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Detect default audio player via env var or platform-specific methods.
    
    Detection Strategy:
    - macOS: Query LaunchServices for audio/mp3 handler → Music.app
    - Linux: Check GUI environment (DISPLAY) → scan PATH for players → soft error if headless
    - Windows: Default to Music (Groove Music) app
    
    Returns:
        str: Audio player name (e.g., "Music", "VLC", "Audacious") or "none" if headless
    """
    # Check env var first (e.g., AUDIO_PLAYER="vlc")
    player = os.getenv("AUDIO_PLAYER")
    if player:
        return player

    system = platform.system()
    if system == "Darwin":
        player = _detect_macos_audio_player(log_level, is_production)
    elif system == "Linux":
        player = _detect_linux_audio_player(log_level, is_production)
    elif system == "Windows":
        player = _detect_windows_audio_player(log_level, is_production)
    else:
        player = "unknown"

    return player


def _detect_macos_audio_player(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Query macOS LaunchServices for default audio handler, fallback to Music.app.
    
    Uses same pattern as image/video - queries LSHandlers for audio/mp3 associations.
    """
    try:
        # Check LaunchServices for audio/mp3 handler
        result = subprocess.run(
            ['defaults', 'read', 'com.apple.LaunchServices/com.apple.launchservices.secure', 'LSHandlers'],
            capture_output=True, 
            text=True, 
            timeout=SUBPROCESS_TIMEOUT_SEC, 
            check=False
        )

        output_lower = result.stdout.lower()
        for key, name in AUDIO_PLAYER_MAPPING_MACOS.items():
            if key in output_lower:
                _log_info(f"Found default audio player via LaunchServices: {name}", log_level, is_production)
                return name

    except Exception as e:
        _log_warning(f"Could not query LaunchServices for audio player: {e}", log_level, is_production)

    return DEFAULT_MACOS_AUDIO_PLAYER


def _detect_linux_audio_player(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Query Linux for GUI audio player, gracefully handle headless environments.
    
    Strategy:
    1. Check if GUI is available (DISPLAY environment variable)
    2. If headless → log soft warning, return "none"
    3. If GUI → scan PATH for common audio players
    4. Fallback to vlc (most common)
    """
    # Check for GUI environment
    if not os.getenv("DISPLAY"):
        _log_warning("No GUI detected (DISPLAY not set). Audio playback unavailable in headless mode.", log_level, is_production)
        return "none"

    # Try xdg-mime first (freedesktop.org standard)
    try:
        result = subprocess.run(
            ['xdg-mime', 'query', 'default', 'audio/mpeg'],
            capture_output=True, 
            text=True, 
            timeout=SUBPROCESS_TIMEOUT_SEC, 
            check=False
        )
        if result.returncode == 0:
            desktop_file = result.stdout.strip().lower()
            # Extract player name from .desktop file
            if desktop_file:
                player_name = desktop_file.replace('.desktop', '')
                if shutil.which(player_name):
                    _log_info(f"Found audio player via xdg-mime: {player_name}", log_level, is_production)
                    return player_name
    except Exception:
        pass  # Fall through to PATH scan

    # Scan PATH for common audio players
    for player in LINUX_AUDIO_PLAYERS:
        if shutil.which(player):
            _log_info(f"Found audio player in PATH: {player}", log_level, is_production)
            return player

    # Fallback
    _log_warning(f"No audio player found in PATH. Defaulting to {DEFAULT_LINUX_AUDIO_PLAYER} (may not be installed).", log_level, is_production)
    return DEFAULT_LINUX_AUDIO_PLAYER


def _detect_windows_audio_player(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """
    Detect Windows audio player, default to Groove Music app.
    
    Windows 10/11: Groove Music (modern)
    Fallback: Windows Media Player - always available
    """
    # Windows 10/11 Groove Music app is default
    _log_info(f"Using Windows default audio player: {DEFAULT_WINDOWS_AUDIO_PLAYER}", log_level, is_production)
    return DEFAULT_WINDOWS_AUDIO_PLAYER


def get_audio_player_launch_command(player_name: str) -> tuple:
    """
    Get platform-specific command to launch an audio player.
    
    Args:
        player_name: Player name (e.g., "Music", "VLC", "Audacious")
                    Case-insensitive, normalized internally
    
    Returns:
        Tuple of (command, args_template) where:
        - macOS: ("open", ["-a", "Music"]) - use 'open -a "App Name"'
        - Linux: ("vlc", []) - direct executable
        - Windows: ("start", [""]) - use start command for Music
        - Unknown/None: (None, []) - player not available
    
    Examples:
        >>> get_audio_player_launch_command("Music")
        # macOS: ("open", ["-a", "Music"])
        
        >>> get_audio_player_launch_command("audacious")
        # Linux: ("audacious", [])
        
        >>> get_audio_player_launch_command("Music")
        # Windows: ("start", [""])
    """
    if player_name == "none" or player_name == "unknown":
        return (None, [])
    
    system = platform.system()
    player_lower = player_name.lower()
    
    # macOS: GUI apps need 'open -a'
    if system == "Darwin":
        macos_apps = {
            "music": "Music",
            "itunes": "iTunes",
            "vlc": "VLC",
            "quicktime player": "QuickTime Player",
            "quicktime": "QuickTime Player",
        }
        app_name = macos_apps.get(player_lower)
        if app_name:
            return ("open", ["-a", app_name])
        # If not in mapping, try direct command
        if shutil.which(player_lower):
            return (player_lower, [])
        return (None, [])
    
    # Linux: Direct executable names
    elif system == "Linux":
        # Check if player is in PATH
        if shutil.which(player_lower):
            return (player_lower, [])
        return (None, [])
    
    # Windows: Use 'start' command for default handlers
    elif system == "Windows":
        if player_lower == "music":
            # Windows Groove Music app - use 'start' with empty first arg
            return ("start", [""])
        elif player_lower == "windows media player" or player_lower == "wmplayer":
            return ("wmplayer", [])
        # Try direct command
        if shutil.which(player_lower):
            return (player_lower, [])
        return (None, [])
    
    return (None, [])

