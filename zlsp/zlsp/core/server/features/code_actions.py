"""
Generic Code Action Executor for zlsp.

Executes code actions based on YAML configurations from themes/zolo_default.yaml.
All logic is data-driven - no hardcoded action implementations!

Architecture:
- Pattern matching engine: Evaluates conditions from YAML
- Text edit generators: Create LSP TextEdit objects
- Execution types: insert_at_end_of_line, replace_indentation, insert_multiline_template
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from lsprotocol.types import TextEdit, Range, Position


class CodeActionExecutor:
    """
    Generic executor for code actions defined in YAML.
    
    Reads action['execution'] config and generates LSP TextEdit objects.
    No hardcoded logic for specific actions - all driven by YAML config.
    """
    
    def execute(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[TextEdit]:
        """
        Execute a code action and return text edits.
        
        Args:
            action: Action configuration from YAML (via CodeActionRegistry)
            context: Current editor context with keys:
                - document_content: Full document text
                - line: Current line text
                - line_number: 0-based line number
                - cursor_position: Character position in line
                - file_name: Name of the file (for pattern matching)
        
        Returns:
            List of LSP TextEdit objects to apply
        """
        execution = action.get('execution', {})
        execution_type = execution.get('type')
        
        if execution_type == 'insert_at_end_of_line':
            return self._execute_insert_eol(action, context)
        elif execution_type == 'replace_indentation':
            return self._execute_replace_indent(action, context)
        elif execution_type == 'insert_multiline_template':
            return self._execute_multiline(action, context)
        else:
            # Unknown execution type
            return []
    
    def _execute_insert_eol(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[TextEdit]:
        """
        Execute insert_at_end_of_line action (e.g., add type hint).
        
        Evaluates patterns to determine what to insert based on value.
        """
        execution = action['execution']
        patterns = execution.get('patterns', [])
        format_config = execution.get('format', {})
        
        line = context['line']
        line_number = context['line_number']
        
        # Extract value from line (after colon)
        value = self._extract_value_from_line(line)
        
        # Find matching pattern
        hint = None
        for pattern in patterns:
            if self._matches_pattern_condition(value, pattern):
                hint = pattern.get('hint', '')
                break
        
        if not hint:
            # No pattern matched
            return []
        
        # Generate edit to insert at end of line
        padding_before = format_config.get('padding_before', '  ')
        padding_after = format_config.get('padding_after', '')
        
        insert_text = f"{padding_before}{hint}{padding_after}"
        line_length = len(line.rstrip('\n'))
        
        return [TextEdit(
            range=Range(
                start=Position(line=line_number, character=line_length),
                end=Position(line=line_number, character=line_length)
            ),
            new_text=insert_text
        )]
    
    def _execute_replace_indent(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[TextEdit]:
        """
        Execute replace_indentation action (e.g., normalize to 2 spaces).
        
        Replaces leading whitespace with correct indentation.
        """
        execution = action['execution']
        config = execution.get('config', {})
        
        line = context['line']
        line_number = context['line_number']
        
        # Detect current indentation
        current_indent, indent_length = self._get_leading_whitespace(line)
        
        # Calculate target indentation
        standard_indent = config.get('standard_indent', 2)
        target_level = self._detect_indent_level(context, standard_indent)
        target_indent = ' ' * (target_level * standard_indent)
        
        # Convert tabs if needed
        if config.get('convert_tabs', True):
            target_indent = target_indent.replace('\t', ' ' * standard_indent)
        
        # Generate edit to replace indentation
        return [TextEdit(
            range=Range(
                start=Position(line=line_number, character=0),
                end=Position(line=line_number, character=indent_length)
            ),
            new_text=target_indent
        )]
    
    def _execute_multiline(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[TextEdit]:
        """
        Execute insert_multiline_template action (e.g., scaffold zSchema fields).
        
        Inserts multiple lines based on template from YAML.
        """
        execution = action['execution']
        templates = execution.get('templates', {})
        format_config = execution.get('format', {})
        
        line = context['line']
        line_number = context['line_number']
        
        # Detect type from current context
        # (e.g., look for "type: str" in nearby lines)
        field_type = self._detect_field_type(context)
        
        if field_type not in templates:
            # No template for this type
            return []
        
        template_lines = templates[field_type]
        
        # Calculate indentation
        current_indent = self._get_leading_whitespace(line)[1]
        indent_increase = format_config.get('indent_increase', 2)
        target_indent = ' ' * (current_indent + indent_increase)
        
        # Build multiline text
        lines = [target_indent + line for line in template_lines]
        insert_text = '\n' + '\n'.join(lines)
        
        # Insert after current line
        return [TextEdit(
            range=Range(
                start=Position(line=line_number + 1, character=0),
                end=Position(line=line_number + 1, character=0)
            ),
            new_text=insert_text
        )]
    
    # ─────────────────────────────────────────────────────────────────
    # Pattern Matching Engine
    # ─────────────────────────────────────────────────────────────────
    
    def _matches_pattern_condition(
        self,
        value: str,
        pattern: Dict[str, Any]
    ) -> bool:
        """
        Check if value matches a pattern condition from YAML.
        
        Supports:
        - match_regex: Regular expression matching
        - match_values: Exact value matching (list)
        - condition: Special conditions (default always matches)
        """
        condition = pattern.get('condition', '')
        
        # Check for default fallback
        if condition == 'default':
            return True
        
        # Check regex match
        if 'match_regex' in pattern:
            regex = pattern['match_regex']
            return bool(re.search(regex, value))
        
        # Check exact values
        if 'match_values' in pattern:
            return value.strip() in pattern['match_values']
        
        # No match criteria - shouldn't happen, but be safe
        return False
    
    # ─────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────
    
    def _extract_value_from_line(self, line: str) -> str:
        """
        Extract value part from a line (everything after colon).
        
        Args:
            line: Line text (e.g., "email: john@example.com")
        
        Returns:
            Value portion (e.g., "john@example.com")
        """
        if ':' in line:
            parts = line.split(':', 1)
            return parts[1].strip() if len(parts) > 1 else ''
        return line.strip()
    
    def _get_leading_whitespace(self, line: str) -> Tuple[str, int]:
        """
        Get leading whitespace from a line.
        
        Args:
            line: Line text
        
        Returns:
            Tuple of (whitespace string, length)
        """
        stripped = line.lstrip()
        indent_length = len(line) - len(stripped)
        indent_str = line[:indent_length]
        return indent_str, indent_length
    
    def _detect_indent_level(
        self,
        context: Dict[str, Any],
        standard_indent: int
    ) -> int:
        """
        Detect correct indentation level based on context.
        
        Args:
            context: Editor context
            standard_indent: Standard indent size (e.g., 2)
        
        Returns:
            Indentation level (0, 1, 2, etc.)
        """
        # Simple heuristic: count parent levels by looking at previous lines
        # For now, return based on current indentation (normalize to standard)
        line = context['line']
        current_indent = self._get_leading_whitespace(line)[1]
        
        # Calculate indent level (floor division for consistent rounding)
        level = current_indent // standard_indent
        
        # If not evenly divisible, determine closest level
        if current_indent % standard_indent != 0:
            # Round to nearest level
            remainder = current_indent % standard_indent
            if remainder >= standard_indent / 2:
                level += 1
        
        return max(0, level)
    
    def _detect_field_type(self, context: Dict[str, Any]) -> str:
        """
        Detect field type from context (e.g., "str", "int", "email").
        
        For zSchema files, looks for "type: <type>" in nearby lines.
        Prioritizes special field names (email, password) over generic types.
        
        Args:
            context: Editor context with document_content and line_number
        
        Returns:
            Field type string (e.g., "str", "int", "email")
        """
        # FIRST: Check for special field names (highest priority)
        current_line = context.get('line', '')
        if ':' in current_line:
            key = current_line.split(':', 1)[0].strip()
            # Check for special patterns in field name
            if 'email' in key.lower():
                return 'email'
            elif 'password' in key.lower() or 'passwd' in key.lower():
                return 'password'
        
        # SECOND: Look for explicit "type: <value>" in nearby lines
        document = context.get('document_content', '')
        line_number = context.get('line_number', 0)
        
        lines = document.split('\n')
        search_range = lines[line_number:line_number + 5]
        
        for line in search_range:
            if 'type:' in line:
                type_value = line.split('type:', 1)[1].strip()
                # Only return generic types if no special field name was detected
                return type_value
        
        # Default fallback
        return 'str'


# ═════════════════════════════════════════════════════════════════════
# Public API
# ═════════════════════════════════════════════════════════════════════

def execute_code_action(
    action: Dict[str, Any],
    context: Dict[str, Any]
) -> List[TextEdit]:
    """
    Convenience function to execute a code action.
    
    Args:
        action: Action configuration from CodeActionRegistry
        context: Editor context (document, line, position, etc.)
    
    Returns:
        List of LSP TextEdit objects
    
    Example:
        >>> from themes import load_theme, CodeActionRegistry
        >>> theme = load_theme('zolo_default')
        >>> registry = CodeActionRegistry(theme)
        >>> action = registry.actions[0]
        >>> context = {
        ...     'line': 'email: john@example.com',
        ...     'line_number': 5,
        ...     'cursor_position': 10,
        ...     'document_content': '...',
        ...     'file_name': 'test.zolo'
        ... }
        >>> edits = execute_code_action(action, context)
    """
    executor = CodeActionExecutor()
    return executor.execute(action, context)
