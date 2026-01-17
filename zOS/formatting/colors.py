# zOS/formatting/colors.py
"""
ANSI color codes for terminal output.

Pure color definitions with no logic or dependencies.

NOTE: Color definitions are also available in zConfig.colors.zolo for:
- Better maintainability
- User customization
- Integration with .zolo ecosystem
- Documentation and reference

This Python class remains for backward compatibility and runtime performance.
Future: Colors may be loaded from zConfig.colors.zolo at initialization.
"""


class Colors:
    """ANSI color codes for zKernel terminal output."""
    
    # Subsystem colors
    ZDATA      = "\033[97;48;5;94m"         # Brown bg (CRUD operations)
    ZFUNC      = "\033[97;41m"              # Red bg (Function execution)
    ZDIALOG    = "\033[97;45m"              # Magenta bg (Dialogs)
    ZWIZARD    = "\033[38;5;154;48;5;57m"   # Purple bg (Wizards)
    ZDISPLAY   = "\033[30;48;5;99m"         # Magenta bg (Display)
    PARSER     = "\033[38;5;236;48;5;230m"  # Dark text, cream background (Parsing)
    CONFIG     = "\033[97;48;5;65m"         # Green bg (Configuration)
    SCHEMA     = CONFIG                     # Backward compatibility
    ZOPEN      = "\033[97;48;5;27m"         # Blue bg (File/URL opening)
    ZCOMM      = "\033[97;48;5;33m"         # Bright blue bg (Communication & services)
    ZAUTH      = "\033[97;48;5;130m"        # Orange-brown bg (Authentication)
    EXTERNAL   = "\033[30;103m"             # Yellow bg (External API)

    # Walker colors (UI/navigation)
    MAIN       = "\033[30;48;5;120m"        # Light green bg (Main walker)
    SUB        = "\033[30;48;5;223m"        # Light yellow bg (Sub menus)
    MENU       = "\033[30;48;5;250m"        # Gray bg (Menu rendering)
    DISPATCH   = "\033[30;48;5;215m"        # Peach bg (Dispatch)
    ZLINK      = "\033[30;48;5;99m"         # Purple bg (Link navigation)
    ZCRUMB     = "\033[38;5;154m"           # Bright green text (Breadcrumbs)
    LOADER     = "\033[30;106m"             # Cyan bg (File loading)
    SUBLOADER  = "\033[38;5;214m"           # Orange text (Sub-loading)

    # Standard colors
    GREEN      = "\033[92m"                 # Bright green (Success)
    YELLOW     = "\033[93m"                 # Bright yellow (Highlights)
    MAGENTA    = "\033[95m"                 # Bright magenta (Special data)
    CYAN       = "\033[96m"                 # Bright cyan (Info)
    RED        = "\033[91m"                 # Bright red (Errors)
    PEACH      = "\033[38;5;223m"           # Peach (Debug)
    RESET      = "\033[0m"                  # Reset to default

    # Status colors
    ERROR      = "\033[97;48;5;124m"        # Dark red bg (Error states)
    WARNING    = "\033[31;48;5;178m"        # Orange bg (Warnings)
    RETURN     = "\033[38;5;214m"           # Orange text (Return values)

    # CSS-aligned semantic colors (foreground, no background)
    # Mirrors:
    #   --color-info:    #5CA9FF
    #   --color-success: #52B788
    #   --color-warning: #FFB347
    #   --color-error:   #E63946
    #
    # NOTE: Added (do not overwrite existing names) to preserve backward compatibility.
    # 256-color for broad terminal compatibility (macOS Terminal-safe)
    zInfo      = "\033[38;5;75m"    # light blue / info
    # Use 256-color foreground codes for broad terminal compatibility (macOS Terminal-safe)
    # (Truecolor 38;2;R;G;B may be flattened depending on terminal/theme settings)
    zSuccess   = "\033[38;5;78m"    # green
    zWarning   = "\033[38;5;215m"   # orange/yellow
    zError     = "\033[38;5;203m"   # red

    # Uppercase aliases for consistency with existing callers using ALLCAPS names
    ZINFO      = zInfo
    ZSUCCESS   = zSuccess
    ZWARNING   = zWarning
    ZERROR     = zError
    INFO       = zInfo
    # CSS-aligned brand colors (foreground, no background)
    # Mirrors:
    #   --color-primary:   #A2D46E (Intention - the heart of zCLI)
    #   --color-secondary: #9370DB (Validation - structure & elegance)
    # 256-color for broad terminal compatibility
    PRIMARY    = "\033[38;5;150m"   # light green (intention)
    primary    = PRIMARY
    SECONDARY  = "\033[38;5;98m"    # medium purple (validation)
    secondary  = SECONDARY
    DEFAULT    = RESET
    default    = DEFAULT

    @classmethod
    def get_semantic_color(cls, color_name: str) -> str:
        """
        Get ANSI color code for a semantic color name.
        
        This is the single source of truth for Terminal-first color mapping,
        used by all zDisplay events (links, buttons, headers, text, etc.)
        
        Args:
            color_name: Semantic color name (PRIMARY, SUCCESS, DANGER, etc.)
                       Case-insensitive.
        
        Returns:
            ANSI color code string, or empty string for no color
        
        Examples:
            >>> Colors.get_semantic_color('PRIMARY')
            '\033[38;5;75m'  # Cyan (ZINFO)
            >>> Colors.get_semantic_color('success')
            '\033[38;5;78m'  # Green (ZSUCCESS)
            >>> Colors.get_semantic_color('MUTED')
            ''  # No color (plain text)
        """
        color_map = {
            'PRIMARY': cls.ZINFO,      # Cyan (encouraging for default actions)
            'SECONDARY': cls.SECONDARY,  # Purple (secondary/validation actions)
            'SUCCESS': cls.ZSUCCESS,   # Green (encouraging for positive actions)
            'DANGER': cls.ZERROR,      # Red (alarming for destructive actions)
            'WARNING': cls.ZWARNING,   # Yellow (cautious for risky actions)
            'INFO': cls.ZINFO,         # Cyan (informational)
            'DEFAULT': '',             # Plain text (no color)
            'MUTED': '',               # Plain text (neutral)
        }
        return color_map.get(color_name.upper(), color_map.get('PRIMARY', ''))

