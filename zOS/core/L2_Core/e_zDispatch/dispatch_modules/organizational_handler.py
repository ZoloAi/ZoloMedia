# zOS/core/L2_Core/e_zDispatch/dispatch_modules/organizational_handler.py

"""
Organizational Handler Module for zDispatch Subsystem.

This module provides the OrganizationalHandler class, which handles nested
organizational structures (dicts/lists with no direct actions). It recursively
processes nested content and integrates with ShorthandExpander.

Extracted from dispatch_launcher.py as part of Phase 3 refactoring.
This module depends on ShorthandExpander and CommandRouter (circular dependency
resolved via composition).

Detection Rules:
    A dict is considered organizational if:
    1. All content keys are nested (dicts or lists)
    2. It's NOT a subsystem call
    3. It's NOT a CRUD call

Special Cases:
    - Implicit sequences: All keys are UI events → process sequentially
    - Mixed structures: Some UI events + organizational keys → recurse

Usage Example:
    handler = OrganizationalHandler(expander, logger)
    
    # Check and handle organizational structure
    result = handler.handle(
        {'Header': {'zH1': {...}}, 'Body': {'zText': {...}}},
        context={},
        walker=None,
        command_router=router
    )

Integration:
    - ShorthandExpander: Nested shorthand expansion
    - CommandRouter: Recursive command execution (circular dependency)

Thread Safety:
    - Modifies walker.session if walker provided (not thread-safe per walker)
    - Safe for concurrent walkers
"""

from zOS import Any, Dict, List, Optional

class OrganizationalHandler:
    """
    Handles nested organizational structures (recursion).
    
    This class detects and processes organizational structures, which are
    dicts with nested dicts/lists that don't directly execute actions.
    
    Attributes:
        expander: ShorthandExpander instance for nested expansion
        logger: Logger instance for debug output
    
    Methods:
        handle(): Main entry point - detect and process organizational structures
        is_organizational(): Check if dict is organizational
        detect_implicit_sequence(): Check if all keys are UI events
        
        Private:
        _recurse_nested_structure(): Recursively process nested keys
        _process_nested_key(): Process individual nested key
        _is_all_nested(): Check if all content keys are nested
    
    Example:
        handler = OrganizationalHandler(expander, logger)
        
        # Organizational structure
        result = handler.handle(
            {'Page_Header': {...}, 'Page_Body': {...}},
            context,
            walker,
            command_router
        )
    """
    
    def __init__(self, expander: Any, logger: Any) -> None:
        """
        Initialize organizational handler.
        
        Args:
            expander: ShorthandExpander instance for nested expansion
            logger: Logger instance for debug output
        
        Example:
            handler = OrganizationalHandler(expander, logger)
        """
        self.expander = expander
        self.logger = logger
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def handle(
        self,
        zHorizontal: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        walker: Optional[Any],
        command_router: Any
    ) -> Optional[Any]:
        """
        Handle organizational structure (nested dicts/lists with no direct actions).
        
        If dict has only nested dicts/lists, it's organizational - recurse into it
        rather than treating as implicit wizard. Enables flexible YAML organization.
        
        Args:
            zHorizontal: Dict command
            context: Optional context dict
            walker: Optional walker instance
            command_router: CommandRouter instance for recursive execution
        
        Returns:
            Recursion result, or None if not organizational structure
        
        Example:
            result = handler.handle(
                {'Header': {...}, 'Body': {...}},
                context,
                walker,
                command_router
            )
        
        Notes:
            - Detects implicit sequences (all UI events)
            - Recursively processes nested structures
            - Integrates with ShorthandExpander for nested expansion
        """
        # Get ALL content keys, excluding only metadata (_zClass, _zStyle, _zHTML, etc.)
        metadata_keys = {'_zClass', '_zStyle', '_zHTML', '_zId', '_zScripts', 'zId'}
        content_keys = [k for k in zHorizontal.keys() if k not in metadata_keys]
        
        # Check if organizational (all nested)
        if not self._is_all_nested(zHorizontal, content_keys):
            return None
        
        # Process keys in their original order to maintain correct buffering sequence
        # This ensures injection order matches processing order
        # CRITICAL: Check for _ prefix FIRST before checking zDisplay
        # Organizational containers like _Visual_Caption may contain expanded zDisplay,
        # but they should still be treated as organizational, not UI events
        
        # Track what we find for logging
        ui_event_count = 0
        org_key_count = 0
        input_event_count = 0
        processed_any = False
        
        # ═══════════════════════════════════════════════════════════════
        # TERMINAL MODE CHECK (2026-01-28)
        # Detect mode to skip terminal-suppressed content (_prefixed keys)
        # ═══════════════════════════════════════════════════════════════
        is_terminal_mode = True  # Default to Terminal
        if walker and hasattr(walker, 'session'):
            mode = walker.session.get('zMode', 'Terminal')
            is_terminal_mode = (mode != 'zBifrost')
        elif context and 'zMode' in context:
            is_terminal_mode = (context.get('zMode') != 'zBifrost')
        
        for key in content_keys:
            val = zHorizontal[key]
            
            # Check for organizational container FIRST (before zDisplay check)
            if key.startswith('_'):
                # ═══════════════════════════════════════════════════════════════
                # TERMINAL SUPPRESSION: Skip _ prefixed keys in Terminal mode
                # These are Bifrost-only visual elements (e.g. _Visual_Progression)
                # ═══════════════════════════════════════════════════════════════
                if is_terminal_mode:
                    self.logger.framework.debug(
                        f"[OrganizationalHandler] Skipping terminal-suppressed key '{key}' (Terminal mode)"
                    )
                    continue
                
                # Bifrost mode: Organizational container (not metadata)
                org_key_count += 1
                self.logger.framework.debug(
                    f"[OrganizationalHandler] Processing organizational container '{key}' in order"
                )
                if command_router:
                    result = self._process_nested_key(key, val, context, walker, command_router)
                    processed_any = True
                    
                    # Check for navigation signals
                    if result in ('zBack', 'exit', 'stop', 'error'):
                        return result
                    if isinstance(result, dict) and 'zLink' in result:
                        return result
                        
            elif isinstance(val, dict) and 'zDisplay' in val:
                # UI event with explicit zDisplay wrapper
                ui_event_count += 1
                
                # Check if this is an input event - skip execution if so (let wizard handle)
                event_type = val.get('zDisplay', {}).get('event', '')
                is_input_event = event_type in ('read_string', 'read_password', 'selection', 'button')
                
                if is_input_event:
                    input_event_count += 1
                    self.logger.framework.debug(
                        f"[OrganizationalHandler] Skipping input event '{key}' (event: {event_type}) - will be handled by wizard"
                    )
                    # Don't execute, let wizard handle it
                    continue
                
                self.logger.framework.debug(
                    f"[OrganizationalHandler] Processing UI event '{key}' in order"
                )
                if command_router:
                    # Process single UI event (not as a list)
                    result = command_router._launch_dict(val, context, walker)
                    processed_any = True
                    
                    # Check for navigation signals
                    if result in ('zBack', 'exit', 'stop', 'error'):
                        return result
                    if isinstance(result, dict) and 'zLink' in result:
                        return result
                        
            else:
                # Non-UI, non-organizational key - treat as organizational
                org_key_count += 1
                self.logger.framework.debug(
                    f"[OrganizationalHandler] Processing non-UI organizational key '{key}' in order"
                )
                if command_router:
                    result = self._process_nested_key(key, val, context, walker, command_router)
                    processed_any = True
                    
                    # Check for navigation signals
                    if result in ('zBack', 'exit', 'stop', 'error'):
                        return result
                    if isinstance(result, dict) and 'zLink' in result:
                        return result
        
        self.logger.framework.debug(
            f"[OrganizationalHandler] Processed {ui_event_count} UI events and {org_key_count} organizational containers in original order"
        )
        
        # If we processed anything, return None (success)
        if processed_any:
            return None
        
        # Check if this is a wizard input container (all keys are input events)
        # If so, treat it as an IMPLICIT WIZARD and route to wizard subsystem
        if input_event_count > 0 and input_event_count == len(content_keys):
            self.logger.framework.debug(
                f"[OrganizationalHandler] Wizard input container detected ({input_event_count} input events) - routing as implicit wizard"
            )
            # Route as implicit wizard for sequential execution with if conditions
            if command_router and hasattr(command_router, 'wizard_detector'):
                # Mark as implicit wizard and route to wizard subsystem
                self.logger.framework.debug("[OrganizationalHandler] Routing wizard input container to wizard subsystem")
                return command_router._handle_implicit_wizard(zHorizontal, walker)
            # Fallback: return None if no wizard detector available
            return None
        
        # Recurse into organizational structure
        self.logger.framework.debug(
            f"[OrganizationalHandler] Organizational structure detected ({len(content_keys)} keys)"
        )
        
        return self._recurse_nested_structure(zHorizontal, content_keys, context, walker, command_router)
    
    def is_organizational(
        self,
        zHorizontal: Dict[str, Any],
        is_subsystem_call: bool,
        is_crud_call: bool
    ) -> bool:
        """
        Check if dict is organizational (all nested dicts/lists).
        
        Args:
            zHorizontal: Dict to check
            is_subsystem_call: Whether this is a subsystem call
            is_crud_call: Whether this is a CRUD call
        
        Returns:
            True if organizational, False otherwise
        
        Example:
            is_org = handler.is_organizational(
                {'Header': {...}, 'Body': {...}},
                is_subsystem_call=False,
                is_crud_call=False
            )
            # Returns: True
        """
        # Get ALL content keys, excluding only metadata (_zClass, _zStyle, _zHTML, etc.)
        metadata_keys = {'_zClass', '_zStyle', '_zHTML', '_zId', '_zScripts', 'zId'}
        content_keys = [k for k in zHorizontal.keys() if k not in metadata_keys]
        
        # Not organizational if subsystem or CRUD call
        if is_subsystem_call or is_crud_call:
            return False
        
        # Not organizational if no content keys
        if not content_keys:
            return False
        
        # Check if all nested
        return self._is_all_nested(zHorizontal, content_keys)
    
    def detect_implicit_sequence(
        self,
        zHorizontal: Dict[str, Any],
        content_keys: List[str]
    ) -> bool:
        """
        Detect if all keys are UI events (implicit sequence).
        
        Args:
            zHorizontal: Dict to check
            content_keys: List of content keys
        
        Returns:
            True if all keys are UI events, False otherwise
        
        Example:
            is_seq = handler.detect_implicit_sequence(
                {'zH1': {...}, 'zText': {...}},
                ['zH1', 'zText']
            )
            # Returns: True
        """
        if len(content_keys) < 2:
            return False
        
        # Check if all keys are UI events (after expansion)
        ui_event_count = 0
        for key in content_keys:
            val = zHorizontal[key]
            
            # Check if already expanded (has zDisplay)
            if isinstance(val, dict) and 'zDisplay' in val:
                ui_event_count += 1
        
        return ui_event_count == len(content_keys) and ui_event_count >= 2
    
    # ========================================================================
    # PRIVATE - Recursion Logic
    # ========================================================================
    
    def _is_all_nested(
        self,
        zHorizontal: Dict[str, Any],
        content_keys: List[str]
    ) -> bool:
        """
        Check if all content keys are nested (dicts or lists).
        
        Args:
            zHorizontal: Dict to check
            content_keys: List of content keys
        
        Returns:
            True if all nested, False otherwise
        """
        return all(
            isinstance(zHorizontal[k], (dict, list))
            for k in content_keys
        )
    
    def _recurse_nested_structure(
        self,
        zHorizontal: Dict[str, Any],
        content_keys: List[str],
        context: Optional[Dict[str, Any]],
        walker: Optional[Any],
        command_router: Any
    ) -> Optional[Any]:
        """
        Recursively process nested organizational structure.
        
        Args:
            zHorizontal: Dict with nested structure
            content_keys: List of content keys
            context: Optional context dict
            walker: Optional walker instance
            command_router: CommandRouter for recursive execution
        
        Returns:
            Last recursion result, or None
        
        Notes:
            - Processes each nested key individually
            - Checks for navigation signals (zBack, exit, etc.)
            - Stops on navigation signal
            - Skips terminal-suppressed keys (_prefix) in Terminal mode
        """
        result = None
        
        # Detect mode for terminal suppression
        is_terminal_mode = True  # Default to Terminal
        if walker and hasattr(walker, 'session'):
            mode = walker.session.get('zMode', 'Terminal')
            is_terminal_mode = (mode != 'zBifrost')
        elif context and 'zMode' in context:
            is_terminal_mode = (context.get('zMode') != 'zBifrost')
        
        for key in content_keys:
            # Skip terminal-suppressed keys in Terminal mode
            if is_terminal_mode and key.startswith('_'):
                self.logger.framework.debug(
                    f"[OrganizationalHandler] Skipping terminal-suppressed key '{key}' in _recurse_nested_structure"
                )
                continue
            
            value = zHorizontal[key]
            
            self.logger.framework.debug(
                f"[OrganizationalHandler] Processing nested key: {key} (type: {type(value).__name__})"
            )
            
            # Process nested content
            result = self._process_nested_key(key, value, context, walker, command_router)
            
            # Check for navigation signals
            if result in ('zBack', 'exit', 'stop', 'error'):
                return result
            
            # Check for zLink navigation
            if isinstance(result, dict) and 'zLink' in result:
                return result
        
        return result
    
    def _process_nested_key(
        self,
        key: str,
        value: Any,
        context: Optional[Dict[str, Any]],
        walker: Optional[Any],
        command_router: Any
    ) -> Optional[Any]:
        """
        Process individual nested key (recursively).
        
        Args:
            key: Key name
            value: Key value (dict or list)
            context: Optional context dict
            walker: Optional walker instance
            command_router: CommandRouter for recursive execution
        
        Returns:
            Recursion result
        
        Notes:
            - Applies shorthand expansion if needed
            - Recursively launches dicts and lists
            - Supports 'if:' conditions on shorthands (wizard context)
        """
        # Apply shorthand expansion if dict
        # The 'if' parameter will be passed through to zDisplay wrapper
        # for the wizard to evaluate during sequential execution
        if isinstance(value, dict) and self.expander:
            # DEBUG: Log metadata before expansion
            if key.startswith('_Box_') or key.startswith('_Visual_'):
                has_style_before = '_zStyle' in value
                self.logger.framework.debug(
                    f"[OrganizationalHandler] 🎨 BEFORE expansion of {key}: _zStyle present = {has_style_before}, keys = {list(value.keys())}"
                )
            
            # ═══════════════════════════════════════════════════════════════
            # KEY-LEVEL SHORTHAND EXPANSION (2026-01-29)
            # If the KEY itself is a UI element shorthand (zTerminal, etc.),
            # we need to wrap {key: value} before expansion so expander sees it
            # ═══════════════════════════════════════════════════════════════
            clean_key = key.split('__dup')[0] if '__dup' in key else key
            if clean_key in self.expander.UI_ELEMENT_KEYS:
                # Wrap key-value, expand, then extract result
                wrapped = {key: value}
                expanded, _ = self.expander.expand(wrapped, walker.session if walker else {}, False)
                # Get the expanded value (might be wrapped in zDisplay now)
                value = expanded.get(key, value)
                self.logger.framework.debug(
                    f"[OrganizationalHandler] Expanded UI element shorthand '{key}' -> {list(value.keys()) if isinstance(value, dict) else type(value)}"
                )
            else:
                # Regular nested expansion (for non-UI element keys)
                value, _ = self.expander.expand(value, walker.session if walker else {}, False)
            
            # DEBUG: Log metadata after expansion
            if key.startswith('_Box_') or key.startswith('_Visual_'):
                has_style_after = '_zStyle' in value
                self.logger.framework.debug(
                    f"[OrganizationalHandler] 🎨 AFTER expansion of {key}: _zStyle present = {has_style_after}, keys = {list(value.keys())}"
                )
        
        # NOTE: 'if' conditions are NOT evaluated here during organizational preprocessing.
        # They are evaluated by the wizard during sequential execution when zHat is available.
        # The 'if' parameter passes through in the zDisplay wrapper for wizard handling.
        
        # Recursively process
        if isinstance(value, dict) and command_router:
            # Mark nested content to prevent wizards from triggering navigation
            nested_context = context.copy() if context else {}
            nested_context['_is_nested_in_org_container'] = True
            return command_router._launch_dict(value, nested_context, walker)
        elif isinstance(value, list) and command_router:
            # Mark nested content to prevent wizards from triggering navigation
            nested_context = context.copy() if context else {}
            nested_context['_is_nested_in_org_container'] = True
            return command_router._launch_list(value, nested_context, walker)
        
        return None
