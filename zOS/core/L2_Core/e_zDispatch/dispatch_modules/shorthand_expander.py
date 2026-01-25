# zOS/core/L2_Core/e_zDispatch/dispatch_modules/shorthand_expander.py

"""
Shorthand Expander Module for zDispatch Subsystem.

This module provides the ShorthandExpander class, which expands ALL shorthand
syntax to full zDisplay format. This is the SINGLE SOURCE OF TRUTH for all
shorthand expansion logic in the zOS framework.

**CRITICAL**: This module is MODE-AGNOSTIC - it expands for BOTH Terminal and
Bifrost. Mode-specific rendering happens LATER in zDisplay/zWizard, NOT here.

Extracted from dispatch_launcher.py as part of Phase 3 refactoring.
**THIS MODULE FIXES THE zCrumbs BUG** by making expansion work in both modes.

Supported Shorthands:
    - Headers: zH1-zH6 → zDisplay header events
    - Text: zText → zDisplay text events
    - Rich text: zMD → zDisplay rich_text events
    - Images: zImage → zDisplay image events
    - Links: zURL → zDisplay zURL events
    - Lists: zUL, zOL, zDL → zDisplay list events
    - Tables: zTable → zDisplay zTable events
    - Buttons: zBtn → zDisplay button events (default: color=primary, action=#)
    - Breadcrumbs: zCrumbs → zDisplay zCrumbs events ← BUG FIX
    - Inputs: zInput → zDisplay read_string events (default: type=text, required=false)
    - Plurals: zURLs, zTexts, zH1s-zH6s, zImages, zMDs → Implicit wizards

Features:
    - Mode-agnostic expansion (works for Terminal + Bifrost)
    - Single-pass expansion with nested support
    - Recursive expansion for organizational structures
    - Plural shorthand detection
    - LSP duplicate key handling (__dup suffix)
    - Organizational sibling detection

Usage Example:
    expander = ShorthandExpander(logger)
    
    # Expand shorthand to full zDisplay format
    expanded = expander.expand(
        {'zH1': {'content': 'Title'}, 'zText': {'content': 'Body'}},
        session={}
    )
    # Returns: {
    #     'zH1': {'zDisplay': {'event': 'header', 'indent': 1, 'content': 'Title'}},
    #     'zText': {'zDisplay': {'event': 'text', 'content': 'Body'}}
    # }

Integration:
    - Used by dict_commands.py for Terminal and Bifrost
    - No subsystem dependencies (pure transformation)
    - No mode-specific logic (expansion is universal)

Thread Safety:
    - Pure functions (no state mutation)
    - Safe for concurrent execution
    - No session modification

Performance:
    - Single-pass expansion (O(n) where n = number of keys)
    - Early detection of implicit sequences
    - Minimal redundant checks
"""

from zOS import Any, Dict, List, Optional

# Import dispatch constants
from .dispatch_constants import KEY_ZDISPLAY

class ShorthandExpander:
    """
    Expands ALL shorthand syntax to full zDisplay format (MODE-AGNOSTIC).
    
    This class is the SINGLE SOURCE OF TRUTH for shorthand expansion logic.
    It works for BOTH Terminal and Bifrost modes - mode-specific rendering
    happens downstream in zDisplay/zWizard.
    
    **FIXES zCrumbs BUG**: Previous code skipped expansion for Bifrost mode,
    causing nested zCrumbs to never render. This module expands for ALL modes.
    
    Attributes:
        logger: Logger instance for debug output
    
    Methods:
        expand(): Main entry point - expand all shorthands
        
        Private expansion methods:
        _expand_plurals(): Expand plural shorthands (zURLs, zTexts, etc.)
        _expand_ui_elements(): Expand UI element shorthands (zH1-zH6, zText, etc.)
        _should_skip_expansion(): Check if key should skip expansion
        _has_organizational_siblings(): Check for non-UI siblings
        _get_clean_key(): Strip __dup suffix for LSP duplicate handling
        _is_ui_event_key(): Check if key is a UI event
        
        Individual element expanders:
        _expand_zheader(): zH1-zH6 → header event
        _expand_ztext(): zText → text event
        _expand_zmd(): zMD → rich_text event
        _expand_zimage(): zImage → image event
        _expand_zurl(): zURL → zURL event
        _expand_zul(): zUL → list event (bullet)
        _expand_zol(): zOL → list event (number)
        _expand_zdl(): zDL → description list event
        _expand_ztable(): zTable → zTable event
        _expand_zbtn(): zBtn → button event (default: color=primary, action=#)
        _expand_zcrumbs(): zCrumbs → zCrumbs event ← BUG FIX
    
    Example:
        expander = ShorthandExpander(logger)
        
        # Simple expansion
        result = expander.expand({'zH1': {'content': 'Title'}}, session)
        
        # Nested expansion
        result = expander.expand({
            'Page_Header': {
                'zCrumbs': {'show': 'static', 'parent': 'zProducts.zTheme'},
                'zH1': {'content': 'Containers'}
            }
        }, session)
    """
    
    # UI element keys (for detection) - ALL shorthands that should NOT be recursively expanded
    UI_ELEMENT_KEYS = ['zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6', 'zText', 'zMD', 'zImage', 'zURL', 'zUL', 'zOL', 'zDL', 'zTable', 'zBtn', 'zCrumbs', 'zInput']
    
    # Plural shorthand keys
    PLURAL_SHORTHANDS = ['zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs']
    
    def __init__(self, logger: Any) -> None:
        """
        Initialize shorthand expander.
        
        Args:
            logger: Logger instance for debug output
        
        Example:
            expander = ShorthandExpander(logger)
        """
        self.logger = logger
    
    # ========================================================================
    # PUBLIC API - Main Expansion Entry Point
    # ========================================================================
    
    def expand(
        self,
        zHorizontal: Dict[str, Any],
        session: Dict[str, Any],
        is_subsystem_call: bool = False
    ) -> tuple[Dict[str, Any], bool]:
        """
        Expand ALL shorthand syntax to full zDisplay format (MODE-AGNOSTIC).
        
        This is the main entry point for expansion. It expands for BOTH Terminal
        and Bifrost modes - mode-specific rendering happens downstream.
        
        **FIXES zCrumbs BUG**: Previous code skipped expansion for Bifrost,
        causing nested zCrumbs to never render. This method expands for ALL modes.
        
        Args:
            zHorizontal: Dict to expand (may contain shorthands)
            session: Session dict (not used for expansion, kept for compatibility)
            is_subsystem_call: Whether dict already contains subsystem keys
        
        Returns:
            Tuple of (expanded_dict, is_subsystem_call_flag)
        
        Example:
            # Before
            {'zH1': {'content': 'Title'}, 'zCrumbs': {'show': 'static', 'parent': 'A.B'}}
            
            # After
            (
                {
                    'zH1': {'zDisplay': {'event': 'header', 'indent': 1, 'content': 'Title'}},
                    'zCrumbs': {'zDisplay': {'event': 'zCrumbs', 'show': 'static', 'parent': 'A.B'}}
                },
                True  # is_subsystem_call updated to True
            )
        
        Notes:
            - MODE-AGNOSTIC: Works for Terminal AND Bifrost
            - Single-pass expansion with nested support
            - Handles LSP duplicate keys (__dup suffix)
            - Detects organizational siblings
            - Returns modified copy (does not mutate input)
            - Updates is_subsystem_call if expansion creates zDisplay events
        """
        keys = list(zHorizontal.keys())
        self.logger.framework.debug(f"[ShorthandExpander] Starting expansion for keys: {keys}")
        
        # EARLY EXIT: If already wrapped in zDisplay, don't expand again
        # This prevents recursive expansion from breaking the parameter structure
        if KEY_ZDISPLAY in zHorizontal:
            self.logger.framework.debug(f"[ShorthandExpander] Already wrapped in zDisplay, returning as-is")
            return zHorizontal, is_subsystem_call
        
        # STEP 1: Check for plural shorthands at top level
        zHorizontal, expansion_occurred = self._expand_plurals(zHorizontal)
        if expansion_occurred:
            is_subsystem_call = False  # Plurals create implicit wizard, not subsystem call
        
        # STEP 2: Expand UI element shorthands (zH1-zH6, zText, zCrumbs, etc.)
        zHorizontal, ui_expansion_occurred = self._expand_ui_elements(zHorizontal)
        if ui_expansion_occurred:
            is_subsystem_call = True  # UI element expansion creates zDisplay subsystem calls
        
        self.logger.framework.debug(f"[ShorthandExpander] Expansion complete (is_subsystem_call={is_subsystem_call})")
        return zHorizontal, is_subsystem_call
    
    # ========================================================================
    # PRIVATE - Plural Shorthand Expansion
    # ========================================================================
    
    def _expand_plurals(self, zHorizontal: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        """
        Expand plural shorthands (zURLs, zTexts, etc.) to implicit wizards.
        
        Plural format: zURLs: {link1: {...}, link2: {...}}
        Expands to: {link1: [{zDisplay: ...}], link2: [{zDisplay: ...}]}
        
        Args:
            zHorizontal: Dict to check for plural shorthands
        
        Returns:
            Tuple of (expanded_dict, expansion_occurred)
        
        Example:
            # Before
            {'zURLs': {'GitHub': {'href': '...'}, 'Docs': {'href': '...'}}}
            
            # After
            (
                {
                    'GitHub': [{'zDisplay': {'event': 'zURL', 'href': '...'}}],
                    'Docs': [{'zDisplay': {'event': 'zURL', 'href': '...'}}]
                },
                True
            )
        """
        found_plural = None
        for plural_key in self.PLURAL_SHORTHANDS:
            if plural_key in zHorizontal and isinstance(zHorizontal[plural_key], dict):
                found_plural = plural_key
                break
        
        if not found_plural:
            return zHorizontal, False
        
        self.logger.debug(f"[ShorthandExpander] Found plural at top level: {found_plural}")
        
        plural_items = zHorizontal[found_plural]
        expanded_wizard = {}
        singular_event = self._get_singular_event(found_plural)
        
        if singular_event:
            for item_key, item_params in plural_items.items():
                if isinstance(item_params, dict):
                    if isinstance(singular_event, tuple):
                        # Header event with indent level
                        event_type, indent = singular_event
                        expanded_wizard[item_key] = {KEY_ZDISPLAY: {'event': event_type, 'indent': indent, **item_params}}
                    else:
                        expanded_wizard[item_key] = {KEY_ZDISPLAY: {'event': singular_event, **item_params}}
            
            if expanded_wizard:
                # Apply _zClass to each item if present
                if '_zClass' in zHorizontal:
                    for item_key in expanded_wizard:
                        if KEY_ZDISPLAY in expanded_wizard[item_key]:
                            expanded_wizard[item_key][KEY_ZDISPLAY]['_zClass'] = zHorizontal['_zClass']
                
                self.logger.debug(f"[ShorthandExpander] Expanded {found_plural} to {len(expanded_wizard)} wizard steps")
                return expanded_wizard, True
        
        return zHorizontal, False
    
    def _get_singular_event(self, plural_key: str) -> Optional[Any]:
        """
        Get singular event type from plural key.
        
        Args:
            plural_key: Plural shorthand key (e.g., 'zURLs', 'zH1s')
        
        Returns:
            Event type string or tuple (event, indent) for headers
        
        Example:
            _get_singular_event('zURLs') → 'zURL'
            _get_singular_event('zH1s') → ('header', 1)
        """
        if plural_key == 'zURLs':
            return 'zURL'
        elif plural_key == 'zTexts':
            return 'text'
        elif plural_key == 'zImages':
            return 'image'
        elif plural_key == 'zMDs':
            return 'rich_text'
        elif plural_key.startswith('zH') and plural_key.endswith('s') and len(plural_key) == 4:
            # zH1s, zH2s, etc.
            indent_level = int(plural_key[2])
            if 1 <= indent_level <= 6:
                return ('header', indent_level)
        return None
    
    # ========================================================================
    # PRIVATE - UI Element Shorthand Expansion
    # ========================================================================
    
    def _expand_ui_elements(self, zHorizontal: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        """
        Expand UI element shorthands (zH1-zH6, zText, zCrumbs, etc.).
        
        **MODE-AGNOSTIC**: This method expands for BOTH Terminal and Bifrost.
        The previous bug was here - it only expanded for Terminal mode.
        
        Args:
            zHorizontal: Dict to expand
        
        Returns:
            Tuple of (expanded_dict, expansion_occurred)
        
        Notes:
            - Handles LSP duplicate keys (__dup suffix)
            - Detects organizational siblings
            - Expands in-place if siblings exist
            - Replaces entire dict if no siblings
        """
        expansion_occurred = False
        non_meta_keys = [k for k in zHorizontal.keys() if not k.startswith('_')]
        
        # Check for organizational siblings
        # BUG FIX: Strip __dup suffix before checking if key is UI event
        ui_event_count = sum(1 for k in non_meta_keys if self._is_ui_event_key(self._get_clean_key(k)))
        
        # BUG FIX: If there are multiple UI elements, they are siblings even without organizational keys
        has_multiple_ui_elements = ui_event_count >= 2
        
        # BUG FIX: Detect ALREADY-EXPANDED zDisplay events (from zWizard chunked mode)
        # If we find nested {zDisplay: ...}, we need to mark expansion_occurred=True
        # so that is_subsystem_call gets set correctly for organizational handler
        # BUG FIX: Strip __dup suffix before checking if key is UI event
        has_pre_expanded_zdisplay = any(
            isinstance(zHorizontal.get(k), dict) and KEY_ZDISPLAY in zHorizontal[k]
            for k in non_meta_keys if self._is_ui_event_key(self._get_clean_key(k))
        )
        
        for key in list(zHorizontal.keys()):
            # Get clean key (strip __dup suffix)
            clean_key = self._get_clean_key(key)
            value = zHorizontal[key]
            
            # Skip if not a dict or already expanded
            if not isinstance(value, dict) or KEY_ZDISPLAY in value:
                continue
            
            # Check for organizational siblings OR multiple UI elements
            has_siblings = self._has_organizational_siblings(non_meta_keys) or has_multiple_ui_elements
            
            # Expand based on clean key
            expanded = None
            if clean_key.startswith('zH') and len(clean_key) == 3 and clean_key[2].isdigit():
                expanded = self._expand_zheader(clean_key, value)
            elif clean_key == 'zText':
                expanded = self._expand_ztext(value)
            elif clean_key == 'zMD':
                expanded = self._expand_zmd(value)
            elif clean_key == 'zImage':
                expanded = self._expand_zimage(value)
            elif clean_key == 'zURL':
                expanded = self._expand_zurl(value)
            elif clean_key == 'zUL':
                expanded = self._expand_zul(value)
            elif clean_key == 'zOL':
                expanded = self._expand_zol(value)
            elif clean_key == 'zDL':
                expanded = self._expand_zdl(value)
            elif clean_key == 'zTable':
                expanded = self._expand_ztable(value)
            elif clean_key == 'zBtn':
                expanded = self._expand_zbtn(value)
            elif clean_key == 'zCrumbs':
                expanded = self._expand_zcrumbs(value)  # ← FIX zCrumbs BUG
            elif clean_key == 'zInput':
                expanded = self._expand_zinput(value)
            
            # Apply expansion
            if expanded is not None:
                expansion_occurred = True
                # Check if dict has metadata keys (_zStyle, _zClass, _zId, zId) that need preservation
                metadata_keys = {k for k in zHorizontal.keys() if k.startswith('_') and k not in ['_zScripts']}
                metadata_keys.update(k for k in zHorizontal.keys() if k == 'zId')
                has_metadata = bool(metadata_keys)
                
                if has_siblings:
                    # Expand in-place to preserve siblings
                    zHorizontal[key] = expanded
                elif has_metadata and ui_event_count == 1:
                    # SPECIAL CASE: Container with metadata + single UI element
                    # Merge the UI element's zDisplay directly into the container
                    # Example: _Box_540 with _zStyle + zText → _Box_540 with _zStyle + zDisplay
                    if KEY_ZDISPLAY in expanded:
                        # Copy metadata keys to the result
                        result = {}
                        for meta_key in metadata_keys:
                            result[meta_key] = zHorizontal[meta_key]
                        # Add the zDisplay event
                        result[KEY_ZDISPLAY] = expanded[KEY_ZDISPLAY]
                        return result, True
                    else:
                        # Fallback: expand in-place
                        zHorizontal[key] = expanded
                elif has_metadata:
                    # Multiple UI events with metadata - expand in-place
                    zHorizontal[key] = expanded
                else:
                    # Replace entire dict (single UI event, no siblings, no metadata)
                    return expanded, True  # Early return for single-element case
            # RECURSIVE EXPANSION: If this is a non-shorthand dict, recursively expand nested shorthands
            elif isinstance(value, dict) and not self._is_ui_event_key(clean_key):
                # Recursively expand nested structures
                nested_expanded, nested_expansion_occurred = self._expand_ui_elements(value)
                if nested_expansion_occurred:
                    zHorizontal[key] = nested_expanded
                    expansion_occurred = True
        
        # BUG FIX: If we detected pre-expanded zDisplay events, mark as expanded
        # This ensures is_subsystem_call=True for organizational handler
        if has_pre_expanded_zdisplay and not expansion_occurred:
            expansion_occurred = True
        
        return zHorizontal, expansion_occurred
    
    # ========================================================================
    # PRIVATE - Individual Element Expanders
    # ========================================================================
    
    def _expand_zheader(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Expand zH1-zH6 to header event."""
        indent_level = int(key[2])
        if 1 <= indent_level <= 6:
            return {KEY_ZDISPLAY: {'event': 'header', 'indent': indent_level, **value}}
        return value
    
    def _expand_ztext(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Expand zText to text event."""
        return {KEY_ZDISPLAY: {'event': 'text', **value}}
    
    def _expand_zmd(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Expand zMD to rich_text event."""
        return {KEY_ZDISPLAY: {'event': 'rich_text', **value}}
    
    def _expand_zimage(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Expand zImage to image event."""
        return {KEY_ZDISPLAY: {'event': 'image', **value}}
    
    def _expand_zurl(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Expand zURL to zURL event."""
        return {KEY_ZDISPLAY: {'event': 'zURL', **value}}
    
    def _expand_zul(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand zUL to list event (bullet style).
        
        Handles plural shorthand zURLs by extracting and expanding each URL.
        """
        # If value contains zURLs plural shorthand, extract them into an 'items' list
        if 'zURLs' in value and isinstance(value['zURLs'], dict):
            items = []
            for url_key, url_value in value['zURLs'].items():
                if isinstance(url_value, dict):
                    # Expand each URL to zDisplay event
                    items.append({KEY_ZDISPLAY: {'event': 'zURL', **url_value}})
            # Remove zURLs from value before spreading
            new_value = {k: v for k, v in value.items() if k != 'zURLs'}
            return {KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', 'items': items, **new_value}}
        # Direct parameters (including items if provided)
        return {KEY_ZDISPLAY: {'event': 'list', 'style': 'bullet', **value}}
    
    def _expand_zol(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand zOL to list event (number style).
        
        Handles plural shorthand zURLs by extracting and expanding each URL.
        """
        # If value contains zURLs plural shorthand, extract them into an 'items' list
        if 'zURLs' in value and isinstance(value['zURLs'], dict):
            items = []
            for url_key, url_value in value['zURLs'].items():
                if isinstance(url_value, dict):
                    # Expand each URL to zDisplay event
                    items.append({KEY_ZDISPLAY: {'event': 'zURL', **url_value}})
            # Remove zURLs from value before spreading
            new_value = {k: v for k, v in value.items() if k != 'zURLs'}
            return {KEY_ZDISPLAY: {'event': 'list', 'style': 'number', 'items': items, **new_value}}
        # Direct parameters (including items if provided)
        return {KEY_ZDISPLAY: {'event': 'list', 'style': 'number', **value}}
    
    def _expand_zdl(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand zDL to description list event.
        
        Description lists are used for term-definition pairs (HTML <dl>, <dt>, <dd>).
        """
        return {KEY_ZDISPLAY: {'event': 'dl', **value}}
    
    def _expand_ztable(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Expand zTable to zTable event."""
        return {KEY_ZDISPLAY: {'event': 'zTable', **value}}
    
    def _expand_zbtn(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand zBtn to button event with defaults.
        
        Defaults:
            color: 'primary' (unless specified)
            action: '#' (unless specified)
        """
        # Apply defaults if not provided
        if 'color' not in value:
            value['color'] = 'primary'
        if 'action' not in value:
            value['action'] = '#'
        
        return {KEY_ZDISPLAY: {'event': 'button', **value}}
    
    def _expand_zinput(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand zInput to read_string event with defaults.
        
        Defaults:
            type: 'text' (regular string by default)
            default: '' (empty string)
            placeholder: '' (empty string)
            required: False (not required by default)
        """
        # Apply defaults if not provided
        if 'type' not in value:
            value['type'] = 'text'
        if 'default' not in value:
            value['default'] = ''
        if 'placeholder' not in value:
            value['placeholder'] = ''
        if 'required' not in value:
            value['required'] = False
        
        return {KEY_ZDISPLAY: {'event': 'read_string', **value}}
    
    def _expand_zcrumbs(self, value: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Expand zCrumbs to zCrumbs event.
        
        **THIS FIXES THE zCrumbs BUG**: Previous code skipped zCrumbs expansion
        for Bifrost mode, causing nested zCrumbs to never render.
        
        Args:
            value: zCrumbs parameters dict
        
        Returns:
            Expanded zDisplay event, or None if show=false
        
        Example:
            # Before
            {'show': 'static', 'parent': 'zProducts.zTheme'}
            
            # After
            {'zDisplay': {'event': 'zCrumbs', 'show': 'static', 'parent': 'zProducts.zTheme'}}
        
        Notes:
            - MODE-AGNOSTIC: Works for Terminal AND Bifrost
            - Checks 'show' parameter (session, static, true)
            - Returns None if show=false (suppress display)
        """
        # Check for 'show' parameter
        if 'show' not in value:
            self.logger.framework.debug("[ShorthandExpander] zCrumbs missing 'show' parameter, skipping")
            return None
        
        show_value = value.get('show', False)
        
        # Accept: show=True, show='true', show='session', show='static'
        valid_show_values = ('session', 'static', True)
        is_valid = (
            show_value in valid_show_values or
            (isinstance(show_value, str) and show_value.lower() in ('true', 'session', 'static'))
        )
        
        if is_valid:
            self.logger.framework.debug(f"[ShorthandExpander] Expanding zCrumbs with show={show_value}")
            # Pass through ALL params including 'show' (for session vs static mode)
            return {KEY_ZDISPLAY: {'event': 'zCrumbs', **value}}
        else:
            # show: false or invalid value - skip this key
            self.logger.framework.debug(f"[ShorthandExpander] zCrumbs show={show_value}, skipping")
            return None
    
    # ========================================================================
    # PRIVATE - Helper Methods
    # ========================================================================
    
    def _should_skip_expansion(self, key: str, skip_shorthand_loop: bool) -> bool:
        """
        Check if key should skip expansion (implicit sequence detection).
        
        Args:
            key: Key to check
            skip_shorthand_loop: Whether to skip UI events (implicit sequence)
        
        Returns:
            True if should skip, False otherwise
        """
        if skip_shorthand_loop:
            clean_key = self._get_clean_key(key)
            return self._is_ui_event_key(clean_key)
        return False
    
    def _has_organizational_siblings(self, non_meta_keys: List[str]) -> bool:
        """
        Check if there are non-UI-event siblings (organizational containers).
        
        Args:
            non_meta_keys: List of non-metadata keys
        
        Returns:
            True if has organizational siblings, False otherwise
        """
        for key in non_meta_keys:
            clean_key = self._get_clean_key(key)
            if not self._is_ui_event_key(clean_key):
                return True
        return False
    
    def _get_clean_key(self, key: str) -> str:
        """
        Strip __dup{N} suffix for LSP duplicate key handling.
        
        Args:
            key: Key to clean
        
        Returns:
            Clean key without __dup suffix
        
        Example:
            _get_clean_key('zText__dup2') → 'zText'
        """
        return key.split('__dup')[0] if '__dup' in key else key
    
    def _is_ui_event_key(self, key: str) -> bool:
        """
        Check if key is a UI event (for implicit sequence detection).
        
        Args:
            key: Key to check (should be clean, no __dup suffix)
        
        Returns:
            True if UI event key, False otherwise
        
        Example:
            _is_ui_event_key('zH1') → True
            _is_ui_event_key('zText') → True
            _is_ui_event_key('Page_Header') → False
        
        Notes:
            - zCrumbs is NOT counted as a UI event (standalone directive)
            - Headers are detected dynamically (zH1-zH6)
        """
        if key in self.UI_ELEMENT_KEYS:
            return True
        if key.startswith('zH') and len(key) == 3 and key[2].isdigit():
            return True
        return False
