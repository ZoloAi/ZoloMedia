# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_data.py

"""
BasicData - Structured Data Display with zDialog/zData Integration
===================================================================

This event package provides structured data display (lists and JSON) with
comprehensive formatting options, building on the BasicOutputs A+ foundation
(Week 6.4.7 complete).

Composition Architecture
------------------------
BasicData builds on BasicOutputs (the A+ grade foundation):

Layer 3: display_delegates.py (PRIMARY API)
    ↓
Layer 2: display_events.py (ORCHESTRATOR)
    ↓
Layer 2: events/display_event_data.py (BasicData) ← THIS MODULE
    ↓
Layer 2: events/display_event_outputs.py (BasicOutputs) ← A+ FOUNDATION
    ↓
Layer 1: display_primitives.py (FOUNDATION I/O)

Composition Flow:
1. BasicData method called (list() or json_data())
2. Try GUI mode via primitives.send_gui_event()
3. If terminal mode:
   a. Format data (numbered list, bullet list, or JSON)
   b. Apply styling (indentation, syntax coloring for JSON)
   c. Display via BasicOutputs.text() for consistent I/O
4. Return control to caller

List Display (2 Styles)
------------------------
BasicData provides 2 list display styles:

**Numbered Style:**
- Display: "1. item", "2. item", "3. item"
- Use case: Form field options, menu items, ordered lists
- Method: list(items, style="number")

**Bullet Style:**
- Display: "• item", "• item", "• item" (using [BULLET] marker)
- Use case: Validation errors, feature lists, unordered items
- Method: list(items, style="bullet")

JSON Display (Pretty Print + Syntax Coloring)
----------------------------------------------
BasicData provides JSON display with professional formatting:

**Features:**
- Pretty printing: json.dumps() with configurable indentation
- Base indentation: Applied to all lines for nested display
- Syntax coloring (terminal only): 4-color scheme via regex
  - Cyan: JSON keys
  - Green: String values
  - Yellow: Numeric values
  - Magenta: Booleans and null

**Implementation:**
- Regex-based: 4 substitution passes in _colorize_json()
- Optional: color=True parameter enables coloring
- Fallback: Plain JSON if coloring disabled or fails

Dual-Mode I/O Pattern
----------------------
All methods implement the same dual-mode pattern:

1. **GUI Mode (Bifrost):** Try send_gui_event() first
   - Send clean JSON event with data
   - Returns immediately (GUI handles async)
   - GUI frontend will display data

2. **Terminal Mode (Fallback):** Format and display locally
   - Format data (numbered, bullet, or JSON)
   - Apply styling (indentation, colors)
   - Display via BasicOutputs.text() for consistent I/O

zDialog Integration (Week 6.5 - Documented for Future Use)
-----------------------------------------------------------
**Current State:** zDialog does NOT use BasicData yet (as of Week 6.4).

**Integration Potential (HIGH PRIORITY for Week 6.5):**

1. **Form Field Options Display:**
   ```python
   # Current: Manual numbering in display_event_system.py zDialog()
   # Future: Use BasicData for consistency
   self.BasicData.list(field_options, style="number", indent=1)
   # Benefit: Professional display + dual-mode support
   ```

2. **Validation Error Display:**
   ```python
   # Current: Text blocks or manual formatting
   # Future: Use BasicData for clarity
   self.BasicData.list(validation_errors, style="bullet", indent=1)
   # Benefit: Clear, bullet-point error lists
   ```

3. **Form Data Preview Before Submission:**
   ```python
   # Current: Not implemented
   # Future: Add preview feature
   self.BasicData.json_data(form_data, color=True, indent_size=2)
   # Benefit: User sees exactly what will be submitted
   ```

4. **Schema/Model Structure Display:**
   ```python
   # Current: Not implemented
   # Future: Schema introspection
   self.BasicData.json_data(model_schema, color=True)
   # Benefit: Developers can inspect form structure
   ```

**Integration Timeline:**
- Week 6.4.10: Document potential (THIS MODULE)
- Week 6.5.5: Implement integration in display_event_system.py → zDialog()
- Week 6.5.6: Test with zDialog demos

**See:** plan_week_6.5_parser_loader_dialog.html for detailed integration checklist

zData Integration (Week 6.6 - Documented for Future Use)
---------------------------------------------------------
**Current State:** zData uses display.zTable() (AdvancedData) for query results.
This is CORRECT separation - zTable for complex tabular data, BasicData for
simple lists and JSON.

**Integration Potential (HIGH VALUE for Week 6.6):**

1. **Query Results (JSON Format):**
   ```python
   # Current: Only table format via zTable()
   # Future: Add format parameter to READ operations
   if request.get("format") == "json":
       ops.zcli.display.zEvents.BasicData.json_data(rows, color=True)
   # Benefit: API-friendly JSON output, better for debugging
   ```

2. **Schema Definitions (Meta Display):**
   ```python
   # Current: Not displayed
   # Future: Schema introspection command
   schema_meta = ops.schema.get("Meta", {})
   ops.zcli.display.zEvents.BasicData.json_data(schema_meta, color=True)
   # Benefit: Developers can inspect database schema
   ```

3. **Table Names Listing:**
   ```python
   # Current: Raw print or manual formatting
   # Future: Use BasicData for consistency
   table_names = ops.adapter.list_tables()
   ops.zcli.display.zEvents.BasicData.list(table_names, style="bullet")
   # Benefit: Professional list display
   ```

4. **Column Names (Schema Introspection):**
   ```python
   # Current: Not implemented
   # Future: Schema inspection command
   columns = list(ops.schema[table_name].keys())
   ops.zcli.display.zEvents.BasicData.list(columns, style="number")
   # Benefit: Quick column reference
   ```

5. **Validation Errors (Structured):**
   ```python
   # Current: Text-based error messages
   # Future: Structured error display
   ops.zcli.display.zEvents.BasicData.json_data(validation_errors, color=True)
   # Or: ops.zcli.display.zEvents.BasicData.list(error_list, style="bullet")
   # Benefit: Clear, structured error reporting
   ```

**Integration Timeline:**
- Week 6.4.10: Document potential (THIS MODULE)
- Week 6.6: Implement format parameter in zData CRUD operations
- Week 6.6: Add schema introspection commands

**See:** Future Week 6.6 plan for detailed integration checklist

Benefits of Composition
-----------------------
- **Reuses BasicOutputs logic:** Indentation, I/O, dual-mode handling
- **Consistent behavior:** All events use same display primitives
- **Single responsibility:** BasicData focuses on data formatting only
- **Easy maintenance:** Changes to I/O logic happen in one place (BasicOutputs)

Layer Position
--------------
BasicData occupies the Event Layer in the zDisplay architecture:
- **Depends on:** BasicOutputs (A+ foundation)
- **Used by:** ~27 references across 14 files (delegates, zOpen, zFunc, zShell, etc.)
- **Dependency:** BasicOutputs must be wired after initialization (done by display_events.py)

Usage Statistics
----------------
- **~27 total references** across 14 files
- **Used by:** display_delegates, zOpen, zFunc, zShell, zAuth, Documentation
- **2 public methods:** list() and json_data()
- **1 helper method:** _colorize_json() (internal)

zCLI Integration
----------------
- **Initialized by:** display_events.py (zEvents.__init__)
- **Cross-referenced:** BasicOutputs wired after init (lines 225-228 in display_events.py)
- **Accessed via:** zcli.display.zEvents.BasicData
- **No session access** - delegates to primitives + BasicOutputs

Thread Safety
-------------
Not thread-safe. All display operations should occur on the main thread or
with appropriate synchronization.

Example Usage
-------------
```python
# Via display_events orchestrator:
events = zEvents(display_instance)

# List display (numbered)
events.BasicData.list(["Option A", "Option B", "Option C"], style="number")
# Output:
#   1. Option A
#   2. Option B
#   3. Option C

# List display (bullet)
events.BasicData.list(["Error 1", "Error 2"], style="bullet")
# Output:
#   • Error 1
#   • Error 2

# JSON display (with syntax coloring)
data = {"name": "John", "age": 30, "active": True}
events.BasicData.json_data(data, color=True, indent_size=2)
# Output (colored):
#   {
#     "name": "John",    (keys in cyan, values in green)
#     "age": 30,         (number in yellow)
#     "active": true     (boolean in magenta)
#   }

# Direct usage (rare):
basic_data = BasicData(display_instance)
basic_data.BasicOutputs = basic_outputs  # Must wire dependency
basic_data.list(["Item 1", "Item 2"], style="bullet")
```

Integration Examples (Week 6.5 - zDialog)
------------------------------------------
```python
# In display_event_system.py → zDialog() method:

# Form field options (Week 6.5.5)
self.BasicData.list(
    field_options,
    style="number",  # Professional numbered display
    indent=1
)

# Validation errors (Week 6.5.5)
if validation_errors:
    self.BasicData.list(
        validation_errors,
        style="bullet",  # Clear bullet-point errors
        indent=1
    )

# Form preview before submit (Week 6.5.5)
self.BasicData.json_data(
    form_data,
    color=True,       # Syntax highlighting for clarity
    indent_size=2
)
```

Integration Examples (Week 6.6 - zData)
----------------------------------------
```python
# In zData crud_read.py:

# Add format parameter to READ operations (Week 6.6)
format_type = request.get("format", "table")

if format_type == "json":
    # JSON format for API responses
    ops.zcli.display.zEvents.BasicData.json_data(
        rows,
        color=True,
        indent_size=2
    )
elif format_type == "list" and len(columns) == 1:
    # Simple list for single-column results
    items = [row[columns[0]] for row in rows]
    ops.zcli.display.zEvents.BasicData.list(items, style="bullet")
else:
    # Default: table format (existing zTable)
    ops.zcli.display.zTable(table_display, columns, rows)

# Table names listing (Week 6.6)
table_names = ops.adapter.list_tables()
ops.zcli.display.zEvents.BasicData.list(table_names, style="number")

# Schema introspection (Week 6.6)
schema_meta = ops.schema.get("Meta", {})
ops.zcli.display.zEvents.BasicData.json_data(schema_meta, color=True)
```
"""

from zOS import json, re, Any, Optional, Union, List, Dict

# Import DRY helpers from primitives
from ..b_primitives.display_rendering_helpers import apply_indent_to_lines

# Import constants from centralized module
from ..display_constants import (
    _EVENT_NAME_LIST,
    _EVENT_NAME_JSON,
    STYLE_BULLET,
    STYLE_NUMBER,
    STYLE_LETTER,
    STYLE_ROMAN,
    _KEY_ITEMS,
    _KEY_STYLE,
    _KEY_STYLES,
    _KEY_INDENT,
    _KEY_DATA,
    _KEY_INDENT_SIZE,
    DEFAULT_INDENT,
    DEFAULT_INDENT_SIZE,
    DEFAULT_COLOR_ENABLED,
    _JSON_ENSURE_ASCII,
    _INDENT_STRING,
    COLOR_ATTR_CYAN,
    COLOR_ATTR_GREEN,
    COLOR_ATTR_YELLOW,
    COLOR_ATTR_MAGENTA,
    COLOR_ATTR_RESET,
)

# Local constants
MARKER_BULLET: str = "- "  # Specific to this module
DEFAULT_STYLE = STYLE_BULLET

# BasicData Class

class BasicData:
    """Structured data display with zDialog/zData integration potential.
    
    Builds on BasicOutputs (A+ foundation) to provide professional list and
    JSON display with comprehensive formatting options.
    
    **Composition:**
    - Depends on BasicOutputs (A+ grade, Week 6.4.7)
    - Pattern: BasicOutputs.text() for display + zPrimitives for events
    - Benefits: Reuses BasicOutputs logic (indent, I/O, dual-mode)
    
    **Display Styles:**
    - list(style="number") - Numbered lists (1. item, 2. item)
    - list(style="bullet") - Bullet lists (• item, • item)
    - json_data(color=True) - JSON with syntax coloring
    
    **Integration Potential:**
    - zDialog (Week 6.5): Form options, validation errors, data preview
    - zData (Week 6.6): Query results (JSON), schema display, table listing
    
    **Usage:**
    - ~27 references across 14 files
    - Used by: display_delegates, zOpen, zFunc, zShell, zAuth
    
    **Pattern:**
    All methods implement dual-mode I/O (GUI-first, terminal fallback).
    """

    # Type hints for instance attributes
    display: Any  # Parent zDisplay instance
    zPrimitives: Any  # Primitives instance for I/O operations
    zColors: Any  # Colors instance for terminal styling
    BasicOutputs: Optional[Any]  # BasicOutputs instance for composition (wired after init)

    def __init__(self, display_instance: Any) -> None:
        """Initialize BasicData with parent display reference.
        
        Args:
            display_instance: Parent zDisplay instance providing primitives and colors
            
        Note:
            BasicOutputs is set to None initially and wired after initialization
            by display_events.py to avoid circular dependencies. The fallback
            logic handles the rare edge case where BasicOutputs is not yet set.
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        # Get reference to BasicOutputs for composition
        self.BasicOutputs = None  # Will be set after zEvents initialization

    # Helper Methods - Output & GUI Event Handling (DRY Fixes)

    def _output_text(self, content: str, indent: int = DEFAULT_INDENT, break_after: bool = False) -> None:
        """Output text via BasicOutputs with fallback (DRY helper).
        
        Args:
            content: Text content to output
            indent: Indentation level (default: 0)
            break_after: Whether to pause after output (default: False)
            
        Note:
            This helper eliminates 3 duplicate BasicOutputs check + fallback patterns
            (lines 38-42, 75-80 in original). The fallback handles the rare edge
            case where BasicOutputs is not yet wired (initialization race condition).
        """
        if self.BasicOutputs:
            self.BasicOutputs.text(content, indent=indent, break_after=break_after)
        else:
            # Fallback if BasicOutputs not set (shouldn't happen)
            indented_content = self._build_indent(indent) + content
            self.zPrimitives.line(indented_content)

    def _build_indent(self, indent: int) -> str:
        """Build indentation string (DRY helper).
        
        Args:
            indent: Indentation level (number of indent units)
            
        Returns:
            str: Indentation string (e.g., "    " for indent=2)
            
        Note:
            This helper eliminates 2 duplicate indent calculation patterns
            (lines 42, 66-68 in original).
        """
        return _INDENT_STRING * indent

    def _send_gui_event(self, event_name: str, event_data: Dict[str, Any]) -> bool:
        """Send GUI event via primitives (DRY helper).
        
        Args:
            event_name: Name of the event (e.g., "list", "json")
            event_data: Event data dictionary
            
        Returns:
            bool: True if GUI event was sent, False if terminal mode
            
        Note:
            This helper eliminates 2 duplicate GUI event send patterns
            (lines 20-26, 46-52 in original).
        """
        return self.zPrimitives.send_gui_event(event_name, event_data)

    # Helper Methods - Prefix Generation & Number Conversion

    def _generate_prefix(self, style: str, number: int) -> str:
        """Generate list prefix based on style and number.
        
        Extracted from list() method for reuse in outline(). This implements
        the DRY principle - single source of truth for prefix generation.
        
        NEW v1.7: Added support for circle, square, dash styles
        
        Args:
            style: List style (bullet, number, letter, roman, circle, square, dash, none)
            number: Item number (1-indexed)
            
        Returns:
            str: Formatted prefix (e.g., "1. ", "a. ", "i. ", "• ", "○ ", "▪ ", "- ", or "")
        """
        if style == STYLE_NUMBER:
            return f"{number}. "
        elif style == STYLE_LETTER:
            # a, b, c... (26 letters, then aa, ab, etc.)
            return self._number_to_letter(number) + ". "
        elif style == STYLE_ROMAN:
            # i, ii, iii, iv...
            return self._number_to_roman(number) + ". "
        elif style == STYLE_BULLET:
            return MARKER_BULLET  # •
        elif style == 'circle':
            return "○ "  # White circle
        elif style == 'square':
            return "▪ "  # Black small square
        elif style == 'dash':
            return "- "  # Dash/hyphen
        else:  # "none" style or unknown
            return ""

    def _number_to_letter(self, num: int) -> str:
        """Convert number to lowercase letter (1→a, 2→b, 27→aa).
        
        Args:
            num: Number to convert (1-indexed)
            
        Returns:
            str: Lowercase letter(s)
        """
        result = ""
        while num > 0:
            num -= 1
            result = chr(97 + (num % 26)) + result
            num //= 26
        return result

    def _number_to_roman(self, num: int) -> str:
        """Convert number to lowercase roman numeral (1→i, 2→ii, 4→iv).
        
        Args:
            num: Number to convert (1-50 supported)
            
        Returns:
            str: Lowercase roman numeral
        """
        values = [50, 40, 10, 9, 5, 4, 1]
        symbols = ['l', 'xl', 'x', 'ix', 'v', 'iv', 'i']
        result = ""
        for i, value in enumerate(values):
            count = num // value
            if count:
                result += symbols[i] * count
                num -= value * count
        return result

    # Public Methods - List & JSON Display

    def list(self, items: Optional[List[Any]], style: Union[str, List[str]] = DEFAULT_STYLE, indent: int = DEFAULT_INDENT, **kwargs) -> Optional[Any]:
        """Display list with bullets or numbers in Terminal/GUI modes.
        
        Foundation method for list display. Implements dual-mode I/O pattern
        and composes with BasicOutputs for terminal display.
        
        NEW v1.7: Supports nested arrays and cascading styles!
        
        Supports display styles:
        - Single style: "bullet", "number", "letter", "roman", "none"
        - Cascading styles: ["bullet", "circle", "square"] for nested lists
        
        Args:
            items: List of items to display
                   - String: "Item text"
                   - List: [nested, items] - automatically indented with cascading style
                   - Dict with zDisplay: {zDisplay: {...}} - recursive event rendering
            style: Display style (default: "bullet")
                   - String: "number", "bullet", "letter", "roman", "none"
                   - List: ["bullet", "circle", "square"] - cascades through nesting levels
            indent: Base indentation level (default: 0)
            level: Internal - current nesting level for cascading (default: 0)
        
        Returns:
            None or navigation signal dict
            
        Example:
            # Numbered list (for form options, menu items)
            self.BasicData.list(["Option A", "Option B", "Option C"], style="number")
            # Output:
            #   1. Option A
            #   2. Option B
            #   3. Option C
            
            # Bullet list (for validation errors, feature lists)
            self.BasicData.list(["Error 1", "Error 2"], style="bullet", indent=1)
            # Output:
            #     - Error 1
            #     - Error 2
            
            # Plain list (for clean output like directory listings)
            self.BasicData.list(["[DIR] folder/", "[FILE] file.txt"], style="none")
            # Output:
            #   [DIR] folder/
            #   [FILE] file.txt
            
        zDialog Integration (Week 6.5):
            # Form field options
            self.list(field_options, style="number", indent=1)
            
            # Validation errors
            self.list(validation_errors, style="bullet", indent=1)
            
        zData Integration (Week 6.6):
            # Table names listing
            table_names = ops.adapter.list_tables()
            self.list(table_names, style="bullet")
            
            # Column names
            columns = list(schema[table].keys())
            self.list(columns, style="number")
        
        Note:
            Used by: display_delegates, zOpen, zFunc, zShell
            Composes with: BasicOutputs.text() for terminal display
        """
        # Handle None or empty list
        if not items:
            return

        # Extract internal level parameter for cascading styles
        level = kwargs.get('_level', 0)
        
        # Determine current style based on cascading
        if isinstance(style, list):
            # Cascading styles: cycle through list based on nesting level
            cascade_styles = style
            current_style = style[level % len(style)]
        else:
            # Single style: use for all levels
            cascade_styles = None
            current_style = style

        # NEW: In Bifrost mode, process nested zDisplay events in list items BEFORE buffering
        # This ensures nested events (like zURL inside zUL) get individually buffered
        mode = self.display.zcli.session.get('zMode', 'Terminal')
        if mode == 'zBifrost':
            for item in items:
                if isinstance(item, dict) and 'zDisplay' in item:
                    # Process nested zDisplay event to trigger its buffering
                    # Don't need the result, just need the side effect of buffering
                    self.display.handle(item['zDisplay'])

        # Try GUI mode first - send clean event
        if self._send_gui_event(_EVENT_NAME_LIST, {
            _KEY_ITEMS: items,
            _KEY_STYLE: style,  # Send original style (string or list)
            _KEY_INDENT: indent
        }):
            return  # GUI event sent successfully

        # Terminal mode - format and display list
        # Use _generate_prefix() helper for DRY (reused by outline() method)
        # Extract _context from kwargs for %data.* variable resolution (v1.5.12)
        _context = kwargs.get('_context')
        
        for i, item in enumerate(items, 1):
            prefix = self._generate_prefix(current_style, i)
            
            # NEW v1.7: Handle nested arrays naturally!
            if isinstance(item, list):
                # Nested array detected - render recursively with cascading style
                # Don't render prefix for nested list (it's a container)
                # Recursively render with incremented level and indent
                result = self.list(
                    item, 
                    style=cascade_styles if cascade_styles else current_style,
                    indent=indent + 1,
                    _level=level + 1,
                    _context=_context
                )
                if isinstance(result, dict) and 'zLink' in result:
                    return result
            
            # Check if item is a zDisplay event (recursive rendering support)
            elif isinstance(item, dict) and 'zDisplay' in item:
                # Recursively render the zDisplay event
                # Print prefix first
                self._output_text(prefix.rstrip(), indent=indent, break_after=False)
                # Then render the item's zDisplay event and capture result
                result = self.display.handle(item['zDisplay'])
                
                # If result is a navigation signal, propagate it immediately
                if isinstance(result, dict) and 'zLink' in result:
                    return result
            else:
                # Simple item - convert to string
                content = f"{prefix}{item}"
                
                # NEW v1.5.12: Resolve %variable references in list items
                if "%" in content and _context:
                    from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_variables
                    content = resolve_variables(content, self.display.zcli, _context)
                
                # Compose: use helper instead of direct BasicOutputs call
                self._output_text(content, indent=indent, break_after=False)
        
        # Return None if no navigation occurred
        return None

    def json_data(self, data: Optional[Union[Dict[str, Any], List[Any], Any]], 
                  indent_size: int = DEFAULT_INDENT_SIZE, 
                  indent: int = DEFAULT_INDENT, 
                  color: bool = DEFAULT_COLOR_ENABLED) -> None:
        """Display JSON with pretty formatting and optional syntax coloring.
        
        Foundation method for JSON display with dual-mode I/O pattern.
        
        Args:
            data: Data to serialize as JSON
            indent_size: JSON indentation size (default: 2)
            indent: Base indentation level (default: 0)
            color: Enable syntax coloring for terminal (default: False)
        """
        if data is None:
            return

        # Try GUI mode first
        if self._try_json_gui_mode(data, indent_size, indent):
            return

        # Terminal mode - format and display JSON
        self._render_json_terminal(data, indent_size, indent, color)

    def _try_json_gui_mode(self, data: Any, indent_size: int, indent: int) -> bool:
        """Try to send JSON as GUI event, return True if successful."""
        return self._send_gui_event(_EVENT_NAME_JSON, {
            _KEY_DATA: data,
            _KEY_INDENT_SIZE: indent_size,
            _KEY_INDENT: indent
        })

    def _render_json_terminal(self, data: Any, indent_size: int, indent: int, color: bool) -> None:
        """Render JSON for terminal mode with formatting and optional colors."""
        json_str = self._serialize_json(data, indent_size)
        json_str = self._apply_json_indentation(json_str, indent)
        
        if color:
            json_str = self._colorize_json(json_str)
        
        self._output_text(json_str, indent=0, break_after=False)

    def _serialize_json(self, data: Any, indent_size: int) -> str:
        """Serialize data to JSON string with error handling."""
        try:
            return json.dumps(data, indent=indent_size, ensure_ascii=_JSON_ENSURE_ASCII)
        except (TypeError, ValueError) as e:
            return f"<Error serializing JSON: {e}>"

    def _apply_json_indentation(self, json_str: str, indent: int) -> str:
        """Apply base indentation to each line of JSON string."""
        return apply_indent_to_lines(json_str, indent)


    # Helper Methods - JSON Syntax Coloring

    def _colorize_json(self, json_str: str) -> str:
        """Apply syntax coloring to JSON string with 4-color scheme.
        
        Implements regex-based syntax coloring for professional JSON display:
        - Cyan: JSON keys (quoted strings followed by colon)
        - Green: String values (quoted strings after colon)
        - Yellow: Numeric values (integers and floats)
        - Magenta: Boolean and null values
        
        Args:
            json_str: Plain JSON string to colorize
            
        Returns:
            str: JSON string with ANSI color codes inserted
            
        Implementation:
            Uses 4 regex substitution passes in order:
            1. Color keys: r'"([^"]+)"\s*:' → cyan
            2. Color string values: r':\s*"([^"]*)"' → green
            3. Color numbers: r'\b(\d+\.?\d*)\b' → yellow
            4. Color booleans/null: r'\b(true|false|null)\b' → magenta
            
        Note:
            This method is called internally by json_data() when color=True.
            The color scheme is optimized for dark terminal backgrounds.
        """
        # Color keys (quoted strings followed by colon)
        json_str = re.sub(
            r'"([^"]+)"\s*:',
            f'{self.zColors.CYAN}"\\1"{self.zColors.RESET}:',
            json_str
        )

        # Color string values (quoted strings not followed by colon)
        json_str = re.sub(
            r':\s*"([^"]*)"',
            f': {self.zColors.GREEN}"\\1"{self.zColors.RESET}',
            json_str
        )

        # Color numbers
        json_str = re.sub(
            r'\b(\d+\.?\d*)\b',
            f'{self.zColors.YELLOW}\\1{self.zColors.RESET}',
            json_str
        )

        # Color booleans and null
        json_str = re.sub(
            r'\b(true|false|null)\b',
            f'{self.zColors.MAGENTA}\\1{self.zColors.RESET}',
            json_str
        )

        return json_str
