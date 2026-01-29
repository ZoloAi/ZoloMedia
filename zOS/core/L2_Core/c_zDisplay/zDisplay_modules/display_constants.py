# zDisplay Shared Constants
# ===========================
# Centralized constants for all zDisplay events and modules.
# Industry-grade pattern: Single source of truth for maintainability.
#
# PUBLIC vs PRIVATE API Boundary
# ===============================
# This module defines a clear distinction between PUBLIC and PRIVATE constants:
#
# PUBLIC Constants (NO _ prefix) - 42 constants:
#   - Colors: COLOR_RED, COLOR_GREEN, COLOR_CYAN, etc. (11)
#   - Styles: STYLE_FULL, STYLE_BULLET, STYLE_NUMBERED, etc. (14)
#   - Modes: MODE_TERMINAL, MODE_BIFROST, MODE_WALKER (4)
#   - Link Targets: TARGET_SELF, TARGET_BLANK, etc. (5)
#   - Public Defaults: DEFAULT_INDENT, DEFAULT_BREAK_MESSAGE, etc. (13)
#   Used in: External code, method signatures, user apps
#
# PRIVATE Constants (_ prefix) - 158 constants:
#   - Event Names: _EVENT_TEXT, _EVENT_PROGRESS_BAR, etc. (50+)
#   - JSON Keys: _KEY_LABEL, _KEY_COLOR, _KEY_CONTENT, etc. (40+)
#   - Messages: _MSG_NO_SESSION, _MSG_INVALID_NUMBER, etc. (30+)
#   - Prompts: _PROMPT_INPUT, _PROMPT_LINK_TEMPLATE, etc. (4)
#   - Internal Defaults: _DEFAULT_SPINNER_STYLE, etc. (12)
#   - Formatting: _CHAR_DOUBLE_LINE, _BOX_TOP_LEFT, _ANSI_*, etc. (30+)
#   - Misc: _LOG_PREFIX, _OPTION_INDEX_OFFSET, etc. (6)
#   Used in: Internal zDisplay modules only
#
# Why This Matters:
#   - Clear API contract: External code knows what's safe to use
#   - PEP 8 compliance: _ prefix signals internal implementation
#   - Maintainability: Private constants can be refactored freely
#   - Consistency: Matches zConfig/zComm standards

# Subsystem Configuration
SUBSYSTEM_NAME = "zDisplay"
READY_MESSAGE = "ZDISPLAY Ready"
DEFAULT_COLOR = "ZDISPLAY"
DEFAULT_MODE = "Terminal"

# Display Modes
MODE_TERMINAL = "Terminal"
MODE_WALKER = "Walker"
MODE_EMPTY = ""
MODE_BIFROST = "zBifrost"

# Event Names - Output Events (Internal)
_EVENT_TEXT = "text"
_EVENT_RICH_TEXT = "rich_text"
_EVENT_HEADER = "header"
_EVENT_LINE = "line"
_EVENT_NAME_HEADER = "header"
_EVENT_NAME_TEXT = "text"

# Event Names - Signal Events (Internal)
_EVENT_ERROR = "error"
_EVENT_WARNING = "warning"
_EVENT_SUCCESS = "success"
_EVENT_INFO = "info"
_EVENT_ZMARKER = "zMarker"
_EVENT_NAME_ERROR = "error"
_EVENT_NAME_WARNING = "warning"
_EVENT_NAME_SUCCESS = "success"
_EVENT_NAME_INFO = "info"
_EVENT_NAME_ZMARKER = "zMarker"

# Event Names - Data Events (Internal)
_EVENT_LIST = "list"
_EVENT_DL = "dl"
_EVENT_JSON = "json"
_EVENT_JSON_DATA = "json_data"
_EVENT_ZTABLE = "zTable"
_EVENT_NAME_LIST = "list"
_EVENT_NAME_JSON = "json"

# Event Names - Media Events (Internal)
_EVENT_IMAGE = "image"
_EVENT_VIDEO = "video"
_EVENT_AUDIO = "audio"
_EVENT_PICTURE = "picture"

# Event Names - System Events (Internal)
_EVENT_ZDECLARE = "zDeclare"
_EVENT_ZSESSION = "zSession"
_EVENT_ZCONFIG = "zConfig"
_EVENT_ZCRUMBS = "zCrumbs"
_EVENT_ZMENU = "zMenu"
_EVENT_ZDASH = "zDash"
_EVENT_ZDIALOG = "zDialog"
_EVENT_ZTERMINAL = "zTerminal"

# Event Names - TimeBased/Widget Events (Internal)
_EVENT_PROGRESS_BAR = "progress_bar"
_EVENT_PROGRESS_COMPLETE = "progress_complete"
_EVENT_SPINNER = "spinner"
_EVENT_SPINNER_START = "spinner_start"
_EVENT_SPINNER_STOP = "spinner_stop"
_EVENT_SWIPER_INIT = "swiper_init"
_EVENT_SWIPER_UPDATE = "swiper_update"
_EVENT_SWIPER_COMPLETE = "swiper_complete"
_EVENT_PROGRESS_ITERATOR = "progress_iterator"
_EVENT_INDETERMINATE_PROGRESS = "indeterminate_progress"

# Event Names - Input Events (Internal)
_EVENT_SELECTION = "selection"
_EVENT_NAME_SELECTION = "selection"
_EVENT_NAME_BUTTON = "button"
_EVENT_READ_STRING = "read_string"
_EVENT_READ_PASSWORD = "read_password"
_EVENT_READ_BOOL = "read_bool"
_EVENT_READ_RANGE = "read_range"
_EVENT_BUTTON = "button"
_EVENT_LINK = "zURL"  # Renamed from "link" to distinguish from zLink (inter-file navigation)

# Event Names - Primitive Events (Internal)
_EVENT_WRITE_RAW = "write_raw"
_EVENT_WRITE_LINE = "write_line"
_EVENT_WRITE_BLOCK = "write_block"

# Event Type Constants (WebSocket/Bifrost - Internal)
_EVENT_TYPE_OUTPUT = "output"
_EVENT_TYPE_INPUT_REQUEST = "input_request"
_EVENT_TYPE_ZDISPLAY = "zdisplay"

# Write Type Constants (Internal)
_WRITE_TYPE_RAW = "raw"
_WRITE_TYPE_LINE = "line"
_WRITE_TYPE_BLOCK = "block"

# Input Type Constants (Internal)
_INPUT_TYPE_STRING = "string"
_INPUT_TYPE_PASSWORD = "password"

# JSON Key Constants (Internal - used for building event dictionaries)
_KEY_EVENT = "event"
_KEY_LABEL = "label"
_KEY_COLOR = "color"
_KEY_INDENT = "indent"
_KEY_STYLE = "style"
_KEY_CONTENT = "content"
_KEY_BREAK = "break"
_KEY_BREAK_MESSAGE = "break_message"
_KEY_PROGRESS_ID = "progressId"
_KEY_CURRENT = "current"
_KEY_TOTAL = "total"
_KEY_SHOW_PERCENTAGE = "show_percentage"
_KEY_SHOW_ETA = "show_eta"
_KEY_ETA = "eta"
_KEY_CONTAINER = "container"
_KEY_SPINNER_ID = "spinnerId"
_KEY_SWIPER_ID = "swiperId"
_KEY_SLIDES = "slides"
_KEY_CURRENT_SLIDE = "current_slide"
_KEY_TOTAL_SLIDES = "total_slides"
_KEY_AUTO_ADVANCE = "auto_advance"
_KEY_DELAY = "delay"
_KEY_LOOP = "loop"
_KEY_SESSION = "session"
_KEY_CRUMBS = "crumbs"
_KEY_MENU = "menu"
_KEY_PROMPT = "prompt"
_KEY_RETURN_SELECTION = "return_selection"
_KEY_CONTEXT = "context"
_KEY_MODEL = "model"
_KEY_FIELDS = "fields"
_KEY_FOLDER = "folder"
_KEY_SIDEBAR = "sidebar"
_KEY_PANELS = "panels"
_KEY_OPTIONS = "options"
_KEY_MULTI = "multi"
_KEY_DEFAULT = "default"
_KEY_ACTION = "action"
_KEY_ITEMS = "items"
_KEY_STYLES = "styles"
_KEY_DATA = "data"
_KEY_INDENT_SIZE = "indent_size"

# Additional Internal JSON Keys (private - WebSocket specific)
_KEY_TYPE = "type"
_KEY_TIMESTAMP = "timestamp"
_KEY_REQUEST_ID = "requestId"
_KEY_DISPLAY_EVENT = "display_event"
_KEY_MASKED = "masked"

# Colors
COLOR_RED = "RED"
COLOR_YELLOW = "YELLOW"
COLOR_GREEN = "GREEN"
COLOR_CYAN = "CYAN"
COLOR_MAGENTA = "MAGENTA"
COLOR_RESET = "RESET"
COLOR_MAIN = "CYAN"
COLOR_ERROR = "RED"
COLOR_WARNING = "YELLOW"
COLOR_SUCCESS = "GREEN"
COLOR_INFO = "CYAN"

# Colors - JSON Syntax Highlighting
COLOR_ATTR_CYAN = "CYAN"
COLOR_ATTR_GREEN = "GREEN"
COLOR_ATTR_YELLOW = "YELLOW"
COLOR_ATTR_MAGENTA = "MAGENTA"
COLOR_ATTR_RESET = "RESET"

# Style Constants
STYLE_BULLET = "bullet"
STYLE_NUMBER = "number"
STYLE_LETTER = "letter"
STYLE_ROMAN = "roman"
STYLE_DOTS = "dots"
STYLE_LINE = "line"
STYLE_ARC = "arc"
STYLE_ARROW = "arrow"
STYLE_BOUNCING_BALL = "bouncing_ball"
STYLE_SIMPLE = "simple"
STYLE_FULL = "full"
STYLE_SINGLE = "single"
STYLE_WAVE = "wave"
STYLE_NUMBERED = "numbered"

# Link/Navigation Constants (PUBLIC API)
TARGET_SELF = "_self"
TARGET_BLANK = "_blank"
TARGET_PARENT = "_parent"
TARGET_TOP = "_top"
DEFAULT_TARGET = "_self"

# Link Type Constants (Internal)
_LINK_TYPE_INTERNAL_DELTA = "internal_delta"
_LINK_TYPE_INTERNAL_ZPATH = "internal_zpath"
_LINK_TYPE_EXTERNAL = "external"
_LINK_TYPE_ANCHOR = "anchor"
_LINK_TYPE_PLACEHOLDER = "placeholder"

# Markers (Internal)
_MARKER_CHECKED = "[✓]"
_MARKER_UNCHECKED = "[ ]"
_MARKER_SELECTED = "→"
_MARKER_UNSELECTED = " "

# Characters (Internal)
_CHAR_SPACE = " "
_CHAR_NEWLINE = "\n"
_CHAR_DOUBLE_LINE = "═"
_CHAR_SINGLE_LINE = "─"
_CHAR_WAVE = "~"
_CHAR_FILLED = "█"
_CHAR_EMPTY = "░"
_CHAR_CHECKMARK = "✓"
_EMPTY_LINE = ""

# Box Drawing Characters (Internal)
_BOX_TOP_LEFT = "╔"
_BOX_TOP_RIGHT = "╗"
_BOX_BOTTOM_LEFT = "╚"
_BOX_BOTTOM_RIGHT = "╝"
_BOX_HORIZONTAL = "═"
_BOX_VERTICAL = "║"
_BOX_LEFT_T = "╠"
_BOX_RIGHT_T = "╣"

# ANSI Sequences (Internal)
_ANSI_CARRIAGE_RETURN = "\r"
_ANSI_CLEAR_LINE = "\033[2K"
_ANSI_CURSOR_UP = "\033[1A"
_ANSI_CLEAR_SCREEN = "\033[2J"
_ANSI_HOME = "\033[H"

# Default Values (PUBLIC API - used in method signatures)
DEFAULT_INDENT = 0
DEFAULT_INDENT_SIZE = 2
DEFAULT_WIDTH = 80
DEFAULT_SHOW_PERCENTAGE = True
DEFAULT_SHOW_ETA = True
DEFAULT_AUTO_ADVANCE = True
DEFAULT_LOOP = True
DEFAULT_SWIPER_DELAY = 3
DEFAULT_SWIPER_WIDTH = 60
DEFAULT_BREAK_MESSAGE = "Press Enter to continue..."
DEFAULT_MENU_PROMPT = "Select an option:"
DEFAULT_COLOR_ENABLED = True

# Internal Default Values (private - module-specific)
_DEFAULT_LABEL_PROCESSING = "Processing"
_DEFAULT_LABEL_LOADING = "Loading"
_DEFAULT_LABEL_SLIDES = "Slides"
_DEFAULT_MARKER_LABEL = "Marker"
_DEFAULT_MARKER_COLOR = "MAGENTA"
_DEFAULT_CONTAINER = "default"
_DEFAULT_THREAD_JOIN_TIMEOUT = 0.1
_DEFAULT_ANIMATION_DELAY = 0.1
_DEFAULT_SPINNER_STYLE = "dots"
_DEFAULT_IMAGE_ICON = "🖼️"
_DEFAULT_VIDEO_ICON = "🎬"
_DEFAULT_AUDIO_ICON = "🎵"
_DEFAULT_PICTURE_ICON = "📷"
_MARKER_LINE_WIDTH = 40
_MARKER_LINE_CHAR = "─"

# Sizing Constants (Internal)
_INDENT_WIDTH = 4
_INDENT_STR = "    "
_INDENT_STRING = "  "
_BASE_WIDTH = 80
_JSON_ENSURE_ASCII = False

# Messages (Internal)
_MSG_NO_SESSION = "No active session"
_MSG_VIEW_ZSESSION = "View session details with: zcli.display.zSession()"
_MSG_ZCRUMBS_HEADER = "Navigation Breadcrumbs"
_MSG_DEFAULT_MENU_PROMPT = "Select an option:"
_MSG_INVALID_NUMBER = "Invalid number"
_MSG_RANGE_ERROR_TEMPLATE = "Number must be between 1 and {max_num}"
_MSG_INVALID_INPUT_TEMPLATE = "Invalid input: {input}"
_MSG_INVALID_RANGE_TEMPLATE = "Invalid range: {range}"
_MSG_MULTI_SELECT_INSTRUCTIONS = "Use numbers separated by spaces (e.g., '1 3 5') or 'all'"
_MSG_ADDED_TEMPLATE = "Added: {option}"
_MSG_REMOVED_TEMPLATE = "Removed: {option}"
_MSG_BUTTON_CLICKED = "Button clicked: {label}"
_MSG_BUTTON_CANCELLED = "Button cancelled"
_MSG_BIFROST_INITIALIZED = "(Bifrost mode initialized)"
_MSG_SWIPER_FALLBACK = "Swiper not available in this terminal mode"
_MSG_SWIPER_COMPLETED = "Swiper completed"
_MSG_FORM_INPUT = "Form Input"
_MSG_FORM_COMPLETE = "Form completed"
_MSG_PRESS_ENTER = "Press Enter to continue"
_MSG_TOOL_PREFERENCES = "Tool Preferences"
_MSG_SYSTEM = "System"
_MSG_ZMACHINE_SECTION = "Machine Configuration"
_MSG_ZAUTH_SECTION = "Authentication"
_MSG_ACTIVE_CONTEXT = "Active Context"
_MSG_DUAL_MODE_INDICATOR = "Dual Mode"
_MSG_AUTHENTICATED_APPS = "Authenticated Apps"
_MSG_DASHBOARD_MENU_PROMPT = "\nDashboard Menu:"
_MSG_INVALID_PANEL_CHOICE = "Invalid choice. Please enter 1-{max} or 'done'"
_MSG_INVALID_INPUT_FORMAT = "Invalid input. Please enter 1-{max} or 'done'"

# Prompts (Internal)
_PROMPT_INPUT = "Input: "
_PROMPT_SINGLE_SELECT_TEMPLATE = "Select (1-{max_num}){default_hint}: "
_PROMPT_BUTTON_TEMPLATE = "Click [{label}]? (y/n): "
_PROMPT_LINK_INTERNAL = "Navigate to: {label}? (y/n): "
_PROMPT_LINK_EXTERNAL = "Open {label} in browser? (y/n): "
_PROMPT_LINK_PLACEHOLDER = "Click {label}? (y/n): "
_PROMPT_LINK_ANCHOR = "{label}? (y/n): "

# Commands (Internal)
_CMD_DONE = "done"
_CMD_DONE_SHORT = "d"
_CMD_EMPTY = ""

# Swiper Commands (Internal)
_SWIPER_CMD_PREV = "prev"
_SWIPER_CMD_NEXT = "next"
_SWIPER_CMD_PAUSE = "pause"
_SWIPER_CMD_QUIT = "quit"

# Keyboard Keys (Internal)
_ESC_KEY = "\x1b"
_ARROW_RIGHT = "\x1b[C"
_ARROW_LEFT = "\x1b[D"

# Swiper Status (Internal)
_SWIPER_STATUS_PAUSED = "paused"
_SWIPER_STATUS_AUTO = "auto"
_SWIPER_STATUS_MANUAL = "manual"

# Misc (PUBLIC API + Internal)
DEFAULT_STYLE = "bullet"  # PUBLIC - used in method signatures
DEFAULT_MULTI = False  # PUBLIC - used in method signatures

# Internal Misc
_LOG_PREFIX = "[LinkEvents]"
_DEFAULT_DEPLOYMENT = "Development"
_OPTION_INDEX_OFFSET = 1

# zMachine Keys (Internal - used by display_event_system for zSession/zConfig rendering)
_ZMACHINE_KEY_OS = "os"
_ZMACHINE_KEY_HOSTNAME = "hostname"
_ZMACHINE_KEY_ARCHITECTURE = "architecture"
_ZMACHINE_KEY_PYTHON_VERSION = "python_version"
_ZMACHINE_KEY_DEPLOYMENT = "deployment"
_ZMACHINE_KEY_ROLE = "role"
_ZMACHINE_KEY_BROWSER = "browser"
_ZMACHINE_KEY_IDE = "ide"
_ZMACHINE_KEY_SHELL = "shell"
_ZMACHINE_KEY_CPU_CORES = "cpu_cores"
_ZMACHINE_KEY_MEMORY_GB = "memory_gb"
_ZMACHINE_KEY_ZCLI_VERSION = "zcli_version"

# zMachine Field Groups (Internal)
_ZMACHINE_IDENTITY_FIELDS = ["hostname", "os", "architecture"]
_ZMACHINE_TOOL_FIELDS = ["browser", "ide", "shell"]
_ZMACHINE_SYSTEM_FIELDS = ["cpu_cores", "memory_gb", "python_version"]

# Format Templates (Internal)
_FORMAT_BREADCRUMB_SEPARATOR = " → "
_FORMAT_CRUMB_SCOPE = "{scope}[{path}]"
_FORMAT_MENU_ITEM = "{index}. {label}"
_FORMAT_FIELD_PROMPT = "{label}: "
_FORMAT_FIELD_NEWLINE = "\n"
_FORMAT_FIELD_LABEL_INDENT = "  "
_FORMAT_TOOL_FIELD_INDENT = "    "

# Labels (Internal)
_LABEL_ZSESSION_ID = "Session ID"
_LABEL_ZMODE = "Mode"
_LABEL_ZCLI_VERSION = "zCLI Version"

# Deployment Modes (Internal)
_DEPLOYMENT_MODE_DEV = "Development"
_DEPLOYMENT_MODE_PROD = "Production"

# Internal Default Values (private)
_DEFAULT_PROMPT = ""
_DEFAULT_FLUSH = True

# Internal Terminal Sizing (private)
_TERMINAL_COLS_DEFAULT = 80
_TERMINAL_COLS_MIN = 60
_TERMINAL_COLS_MAX = 120

# Internal Error Messages (private)
_ERR_INVALID_OBJ = "zDisplay.handle() requires dict, got %s"
_ERR_MISSING_EVENT = "zDisplay event missing 'event' key"
_ERR_UNKNOWN_EVENT = "Unknown zDisplay event: %s"
_ERR_INVALID_PARAMS = "Invalid parameters for event '%s': %s"

