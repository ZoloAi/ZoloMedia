"""
zDispatch - List Command Handler
=================================

Extracted from dispatch_launcher.py Phase 4 refactoring.

Purpose:
    Handles sequential execution of command lists. Enables streamlined YAML
    where multiple commands can be listed directly under a key without
    requiring intermediate named sub-keys.

Dependencies:
    - No internal dispatch dependencies (leaf module)
    - Delegates back to dispatcher for recursive command execution

Author: zOS Framework
"""

from typing import Any, Dict, List, Optional, Union


class ListCommandHandler:
    """Handles execution of list-based commands."""
    
    def __init__(self, zcli: Any, logger: Any) -> None:
        """
        Initialize the list command handler.
        
        Args:
            zcli: Reference to zCLI instance
            logger: Logger instance
        """
        self.zcli = zcli
        self.logger = logger
    
    def handle(
        self,
        zHorizontal: List[Any],
        context: Optional[Dict[str, Any]],
        walker: Optional[Any],
        dispatcher_launch_fn: Any  # Reference to dispatcher's launch() method
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Execute a list of commands sequentially.
        
        This enables streamlined YAML where multiple zDisplay events (or other commands)
        can be listed directly under a key without requiring intermediate named sub-keys.
        
        Examples:
            # YAML Pattern - List of zDisplay events
            Hero_Section:
              - zDisplay:
                  event: header
                  content: "Zolo"
              - zDisplay:
                  event: header
                  content: "A digital solution"
              - zDisplay:
                  event: text
                  content: "Build intelligent CLI..."
        
        Args:
            zHorizontal: List of commands (dicts, strings, or nested lists)
            context: Optional context dict
            walker: Optional walker instance
            dispatcher_launch_fn: Reference to dispatcher's launch() method for recursion
        
        Returns:
            Result from the last item in the list, or None
        
        Notes:
            - Processes list items sequentially
            - Respects navigation signals (zBack, exit, stop, error)
            - Stops on zLink navigation to trigger immediate navigation
            - Recursively handles nested lists
        """
        if not zHorizontal:
            return None
        
        result = None
        for i, item in enumerate(zHorizontal):
            self.logger.framework.debug(
                f"[ListCommandHandler] Processing item {i+1}/{len(zHorizontal)}: {type(item)}"
            )
            
            # Recursively launch each item via dispatcher
            result = dispatcher_launch_fn(item, context=context, walker=walker)
            
            # Check for navigation signals (stop processing if user wants to go back/exit)
            if result in ('zBack', 'exit', 'stop', 'error'):
                self.logger.framework.warning(
                    f"[ListCommandHandler] Stopping at item {i+1} due to signal: {result}"
                )
                return result
            
            # Check for zLink navigation (stop processing and return to trigger navigation)
            if isinstance(result, dict) and 'zLink' in result:
                return result
        
        return result
