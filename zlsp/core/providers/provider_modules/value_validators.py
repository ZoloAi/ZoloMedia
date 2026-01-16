"""
Value Validators - Validate specific key values in .zolo files

Provides validation for known keys with restricted value sets.
Emits helpful error messages with valid options.
"""

from typing import List, Optional, Set
from lsprotocol import types as lsp_types
from ...parser.parser_modules.file_type_detector import FileType, detect_file_type


# Valid browser names (cross-platform)
VALID_BROWSERS: Set[str] = {
    "Chrome", "Firefox", "Safari", "Arc", "Brave", "Edge", "Opera", "Chromium",
    # Case variations
    "chrome", "firefox", "safari", "arc", "brave", "edge", "opera", "chromium"
}

# Valid IDE/editor names (cross-platform)
VALID_IDES: Set[str] = {
    # CLI editors
    "vim", "nvim", "neovim", "emacs", "nano", "vi",
    # GUI editors
    "code", "vscode", "cursor", "subl", "sublime", "atom",
    "gedit", "kate", "notepad++", "notepad",
    # IDEs
    "idea", "intellij", "pycharm", "webstorm", "phpstorm",
    "eclipse", "netbeans", "android-studio",
    # macOS specific
    "TextEdit", "BBEdit", "Nova",
}

# Valid image viewer applications (cross-platform)
VALID_IMAGE_VIEWERS: Set[str] = {
    # macOS
    "Preview", "Photos",
    # Windows
    "Photos", "Paint", "IrfanView",
    # Linux
    "eog", "Eye of GNOME", "gwenview", "feh", "sxiv", "gthumb",
    # Cross-platform
    "GIMP", "gimp", "XnView", "FastStone",
}

# Valid video player applications (cross-platform)
VALID_VIDEO_PLAYERS: Set[str] = {
    # macOS
    "QuickTime Player", "QuickTime", "IINA",
    # Windows
    "Windows Media Player", "wmplayer",
    # Cross-platform
    "VLC", "vlc", "mpv", "mplayer", "MPlayer", "SMPlayer",
    "Kodi", "Plex", "PotPlayer",
}

# Valid audio player applications (cross-platform)
VALID_AUDIO_PLAYERS: Set[str] = {
    # macOS
    "Music", "iTunes",
    # Windows
    "Windows Media Player", "wmplayer", "Groove Music",
    # Linux
    "rhythmbox", "Rhythmbox", "clementine", "Clementine",
    "audacious", "Audacious", "amarok", "Amarok",
    # Cross-platform
    "VLC", "vlc", "Spotify", "spotify", "foobar2000",
    "Winamp", "AIMP", "MusicBee",
}

# Valid time format strings (standard conventions)
VALID_TIME_FORMATS: Set[str] = {
    # 24-hour formats
    "HH:MM:SS", "HH:MM", "HH:mm:ss", "HH:mm",
    # 12-hour formats
    "hh:mm:ss AM/PM", "hh:mm AM/PM", "hh:mm:ss a", "hh:mm a",
    # Compact formats
    "HHMMSS", "HHmm",
}

# Valid date format strings (standard conventions)
VALID_DATE_FORMATS: Set[str] = {
    # ISO 8601
    "YYYY-MM-DD", "yyyy-mm-dd",
    # European (day-first)
    "DD/MM/YYYY", "dd/mm/yyyy", "DD-MM-YYYY", "dd-mm-yyyy",
    "DD.MM.YYYY", "dd.mm.yyyy",
    # US (month-first)
    "MM/DD/YYYY", "mm/dd/yyyy", "MM-DD-YYYY", "mm-dd-yyyy",
    "MM.DD.YYYY", "mm.dd.yyyy",
    # Compact formats
    "ddmmyyyy", "DDMMYYYY", "mmddyyyy", "MMDDYYYY",
    "yyyymmdd", "YYYYMMDD",
    # Text formats
    "DD MMM YYYY", "dd mmm yyyy", "MMM DD, YYYY", "mmm dd, yyyy",
}

# Valid datetime format strings (combinations of date and time)
VALID_DATETIME_FORMATS: Set[str] = {
    # ISO 8601 datetime
    "YYYY-MM-DD HH:MM:SS", "yyyy-mm-dd HH:MM:SS",
    "YYYY-MM-DDTHH:MM:SS", "yyyy-mm-ddTHH:MM:SS",
    # European datetime
    "DD/MM/YYYY HH:MM:SS", "dd/mm/yyyy HH:MM:SS",
    "DD-MM-YYYY HH:MM:SS", "dd-mm-yyyy HH:MM:SS",
    # US datetime
    "MM/DD/YYYY HH:MM:SS", "mm/dd/yyyy HH:MM:SS",
    "MM-DD-YYYY HH:MM:SS", "mm-dd-yyyy HH:MM:SS",
    # Compact datetime
    "ddmmyyyy HH:MM:SS", "DDMMYYYY HH:MM:SS",
    "yyyymmdd HH:MM:SS", "YYYYMMDD HH:MM:SS",
    # With 12-hour time
    "YYYY-MM-DD hh:mm:ss AM/PM", "MM/DD/YYYY hh:mm:ss AM/PM",
}


class ValueValidator:
    """Validates values for specific keys in zConfig files."""
    
    @staticmethod
    def validate_value(
        key: str,
        value: str,
        line_num: int,
        file_type: FileType,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """
        Validate a key-value pair and return a diagnostic if invalid.
        
        Args:
            key: The key name (e.g., "browser")
            value: The value to validate
            line_num: Line number (0-based)
            file_type: Type of .zolo file
            start_char: Start character position of value
            end_char: End character position of value
        
        Returns:
            Diagnostic if value is invalid, None otherwise
        """
        # Only validate zConfig files
        if file_type != FileType.ZCONFIG:
            return None
        
        # Validate browser value
        if key == "browser":
            return ValueValidator._validate_browser(
                value, line_num, start_char, end_char
            )
        
        # Validate IDE value
        if key == "ide":
            return ValueValidator._validate_ide(
                value, line_num, start_char, end_char
            )
        
        # Validate image_viewer value
        if key == "image_viewer":
            return ValueValidator._validate_image_viewer(
                value, line_num, start_char, end_char
            )
        
        # Validate video_player value
        if key == "video_player":
            return ValueValidator._validate_video_player(
                value, line_num, start_char, end_char
            )
        
        # Validate audio_player value
        if key == "audio_player":
            return ValueValidator._validate_audio_player(
                value, line_num, start_char, end_char
            )
        
        # Validate time_format value
        if key == "time_format":
            return ValueValidator._validate_time_format(
                value, line_num, start_char, end_char
            )
        
        # Validate date_format value
        if key == "date_format":
            return ValueValidator._validate_date_format(
                value, line_num, start_char, end_char
            )
        
        # Validate datetime_format value
        if key == "datetime_format":
            return ValueValidator._validate_datetime_format(
                value, line_num, start_char, end_char
            )
        
        return None
    
    @staticmethod
    def _validate_browser(
        value: str,
        line_num: int,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """Validate browser value."""
        value = value.strip()
        
        # Empty value is okay (might be filled in later by zOS)
        if not value:
            return None
        
        # Check if value is in valid browsers set
        if value not in VALID_BROWSERS:
            # Create a helpful error message
            valid_browsers_str = ", ".join(sorted([
                "Chrome", "Firefox", "Safari", "Arc", "Brave", 
                "Edge", "Opera", "Chromium"
            ]))
            
            message = (
                f"Invalid browser '{value}'. "
                f"Expected one of: {valid_browsers_str}"
            )
            
            return lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=start_char),
                    end=lsp_types.Position(line=line_num, character=end_char)
                ),
                message=message,
                severity=lsp_types.DiagnosticSeverity.Error,
                source="zolo-validator"
            )
        
        return None
    
    @staticmethod
    def _validate_ide(
        value: str,
        line_num: int,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """Validate IDE value."""
        value = value.strip()
        
        # Empty value is okay
        if not value:
            return None
        
        # Check if value is in valid IDEs set
        if value not in VALID_IDES:
            # Create a helpful error message with common options
            common_ides = ["code", "cursor", "vim", "nvim", "subl", "intellij", "pycharm"]
            valid_ides_str = ", ".join(common_ides)
            
            message = (
                f"Invalid IDE '{value}'. "
                f"Common options: {valid_ides_str}"
            )
            
            return lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=start_char),
                    end=lsp_types.Position(line=line_num, character=end_char)
                ),
                message=message,
                severity=lsp_types.DiagnosticSeverity.Error,
                source="zolo-validator"
            )
        
        return None
    
    @staticmethod
    def _validate_image_viewer(
        value: str,
        line_num: int,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """Validate image viewer value."""
        value = value.strip()
        
        # Empty value is okay
        if not value:
            return None
        
        # Check if value is in valid image viewers set
        if value not in VALID_IMAGE_VIEWERS:
            # Create a helpful error message with common options
            common_viewers = ["Preview", "Photos", "GIMP", "eog", "gwenview", "feh"]
            valid_viewers_str = ", ".join(common_viewers)
            
            message = (
                f"Invalid image viewer '{value}'. "
                f"Common options: {valid_viewers_str}"
            )
            
            return lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=start_char),
                    end=lsp_types.Position(line=line_num, character=end_char)
                ),
                message=message,
                severity=lsp_types.DiagnosticSeverity.Error,
                source="zolo-validator"
            )
        
        return None
    
    @staticmethod
    def _validate_video_player(
        value: str,
        line_num: int,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """Validate video player value."""
        value = value.strip()
        
        # Empty value is okay
        if not value:
            return None
        
        # Check if value is in valid video players set
        if value not in VALID_VIDEO_PLAYERS:
            # Create a helpful error message with common options
            common_players = ["VLC", "QuickTime Player", "mpv", "IINA", "Windows Media Player"]
            valid_players_str = ", ".join(common_players)
            
            message = (
                f"Invalid video player '{value}'. "
                f"Common options: {valid_players_str}"
            )
            
            return lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=start_char),
                    end=lsp_types.Position(line=line_num, character=end_char)
                ),
                message=message,
                severity=lsp_types.DiagnosticSeverity.Error,
                source="zolo-validator"
            )
        
        return None
    
    @staticmethod
    def _validate_audio_player(
        value: str,
        line_num: int,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """Validate audio player value."""
        value = value.strip()
        
        # Empty value is okay
        if not value:
            return None
        
        # Check if value is in valid audio players set
        if value not in VALID_AUDIO_PLAYERS:
            # Create a helpful error message with common options
            common_players = ["Music", "VLC", "Spotify", "iTunes", "Rhythmbox", "Windows Media Player"]
            valid_players_str = ", ".join(common_players)
            
            message = (
                f"Invalid audio player '{value}'. "
                f"Common options: {valid_players_str}"
            )
            
            return lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=start_char),
                    end=lsp_types.Position(line=line_num, character=end_char)
                ),
                message=message,
                severity=lsp_types.DiagnosticSeverity.Error,
                source="zolo-validator"
            )
        
        return None
    
    @staticmethod
    def _validate_time_format(
        value: str,
        line_num: int,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """Validate time format string."""
        value = value.strip()
        
        # Empty value is okay
        if not value:
            return None
        
        # Check if value is in valid time formats set
        if value not in VALID_TIME_FORMATS:
            # Create a helpful error message with common options
            common_formats = ["HH:MM:SS", "HH:MM", "hh:mm:ss AM/PM", "hh:mm AM/PM"]
            valid_formats_str = ", ".join(common_formats)
            
            message = (
                f"Invalid time format '{value}'. "
                f"Common options: {valid_formats_str}"
            )
            
            return lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=start_char),
                    end=lsp_types.Position(line=line_num, character=end_char)
                ),
                message=message,
                severity=lsp_types.DiagnosticSeverity.Error,
                source="zolo-validator"
            )
        
        return None
    
    @staticmethod
    def _validate_date_format(
        value: str,
        line_num: int,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """Validate date format string."""
        value = value.strip()
        
        # Empty value is okay
        if not value:
            return None
        
        # Check if value is in valid date formats set
        if value not in VALID_DATE_FORMATS:
            # Create a helpful error message with common options
            common_formats = ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY", "ddmmyyyy", "yyyymmdd"]
            valid_formats_str = ", ".join(common_formats)
            
            message = (
                f"Invalid date format '{value}'. "
                f"Common options: {valid_formats_str}"
            )
            
            return lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=start_char),
                    end=lsp_types.Position(line=line_num, character=end_char)
                ),
                message=message,
                severity=lsp_types.DiagnosticSeverity.Error,
                source="zolo-validator"
            )
        
        return None
    
    @staticmethod
    def _validate_datetime_format(
        value: str,
        line_num: int,
        start_char: int,
        end_char: int
    ) -> Optional[lsp_types.Diagnostic]:
        """Validate datetime format string."""
        value = value.strip()
        
        # Empty value is okay
        if not value:
            return None
        
        # Check if value is in valid datetime formats set
        if value not in VALID_DATETIME_FORMATS:
            # Create a helpful error message with common options
            common_formats = [
                "YYYY-MM-DD HH:MM:SS",
                "DD/MM/YYYY HH:MM:SS",
                "ddmmyyyy HH:MM:SS",
                "YYYY-MM-DDTHH:MM:SS"
            ]
            valid_formats_str = ", ".join(common_formats)
            
            message = (
                f"Invalid datetime format '{value}'. "
                f"Common options: {valid_formats_str}"
            )
            
            return lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=start_char),
                    end=lsp_types.Position(line=line_num, character=end_char)
                ),
                message=message,
                severity=lsp_types.DiagnosticSeverity.Error,
                source="zolo-validator"
            )
        
        return None
    
    @staticmethod
    def validate_document(content: str, filename: Optional[str] = None) -> List[lsp_types.Diagnostic]:
        """
        Validate all key-value pairs in a document.
        
        Args:
            content: Full file content
            filename: Optional filename for file type detection
        
        Returns:
            List of diagnostics for invalid values
        """
        import logging
        logger = logging.getLogger(__name__)
        
        diagnostics = []
        
        # Detect file type
        file_type = detect_file_type(filename) if filename else FileType.GENERIC
        logger.info(f"🔍 ValueValidator: filename={filename}, file_type={file_type}")
        
        # Only validate zConfig files
        if file_type != FileType.ZCONFIG:
            logger.info(f"   ⏭️  Skipping validation (not a zConfig file)")
            return diagnostics
        
        logger.info(f"   ✅ Validating zConfig file...")
        
        lines = content.splitlines()
        logger.info(f"   📄 Processing {len(lines)} lines")
        
        # Track section context (which parent section we're in)
        current_section = None
        section_indent = -1
        
        for line_num, line in enumerate(lines):
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Calculate indentation level (tabs count as 1 indent level each)
            indent = 0
            for char in line:
                if char == '\t':
                    indent += 1
                elif char == ' ':
                    # Assume 4 spaces = 1 indent level
                    continue
                else:
                    break
            
            # Track section headers (indent level 1 under zMachine)
            if ':' in line and indent == 1:
                section_name = stripped.split(':')[0].strip()
                current_section = section_name
                section_indent = indent
                logger.info(f"   📂 Entered section: {current_section} at indent {indent}")
                continue
            
            # Reset section if we go back to same or lower indent
            if indent <= section_indent and ':' in line:
                current_section = None
                section_indent = -1
            
            # Look for key: value pairs
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # Define which keys should be validated in which sections
                    app_keys = {'browser', 'ide', 'image_viewer', 'video_player', 'audio_player'}
                    format_keys = {'time_format', 'date_format', 'datetime_format'}
                    
                    # Only log lines with validated keys for debugging
                    if key in app_keys or key in format_keys:
                        logger.info(f"   🔑 Line {line_num}: section='{current_section}', key='{key}', value='{value}'")
                    
                    # Skip validation if key is in wrong section
                    should_validate = False
                    if key in app_keys and current_section == 'user_preferences':
                        should_validate = True
                    elif key in format_keys and current_section == 'time_date_formatting':
                        should_validate = True
                    
                    if not should_validate:
                        if key in app_keys or key in format_keys:
                            logger.info(f"   ⏭️  Skipping validation (wrong section: {current_section})")
                        continue
                    
                    # Calculate value position in line
                    colon_pos = line.index(':')
                    value_start = colon_pos + 1
                    # Skip leading whitespace in value
                    while value_start < len(line) and line[value_start].isspace():
                        value_start += 1
                    value_end = value_start + len(value)
                    
                    # Validate the value
                    diagnostic = ValueValidator.validate_value(
                        key, value, line_num, file_type, value_start, value_end
                    )
                    
                    if diagnostic:
                        logger.info(f"   ❌ Diagnostic created for '{key}': {diagnostic.message}")
                        diagnostics.append(diagnostic)
        
        logger.info(f"   📊 Total diagnostics: {len(diagnostics)}")
        return diagnostics
