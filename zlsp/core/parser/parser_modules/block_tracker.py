"""
Block Tracker - Unified context tracking for parser

Replaces 17+ individual block tracking lists with a single, maintainable system.
Tracks nested block contexts (zRBAC, ZNAVBAR, zMeta, etc.) for context-aware parsing.
"""

from typing import List, Tuple, Optional, Dict


class BlockTracker:
    """
    Unified block tracking for context-aware parsing.
    
    Manages nested block contexts to enable context-specific token emission.
    For example, keys inside a zRBAC block get different colors than keys outside.
    
    Examples:
        >>> tracker = BlockTracker()
        >>> tracker.enter_block('zRBAC', indent=0, line=5)
        >>> tracker.is_inside('zRBAC', current_indent=2)
        True
        >>> tracker.is_first_level('zRBAC', current_indent=2)
        True
        >>> tracker.is_first_level('zRBAC', current_indent=4)
        False
    """
    
    def __init__(self):
        """Initialize empty block tracking."""
        # Each block type maps to a stack of (indent_level, line_number) tuples
        self._blocks: Dict[str, List[Tuple[int, int]]] = {}
        
        # Special blocks that store additional data (e.g., plural shorthand name)
        self._blocks_with_data: Dict[str, List[Tuple[int, int, str]]] = {}
    
    def enter_block(self, block_type: str, indent: int, line: int, data: Optional[str] = None):
        """
        Enter a new block context.
        
        Args:
            block_type: Type of block (e.g., 'zRBAC', 'ZNAVBAR', 'zMeta')
            indent: Indentation level where block starts
            line: Line number where block starts
            data: Optional additional data (e.g., shorthand name for plural blocks)
        """
        if data is not None:
            # Block with additional data
            if block_type not in self._blocks_with_data:
                self._blocks_with_data[block_type] = []
            self._blocks_with_data[block_type].append((indent, line, data))
        else:
            # Standard block
            if block_type not in self._blocks:
                self._blocks[block_type] = []
            self._blocks[block_type].append((indent, line))
    
    def enter_block_single(self, block_type: str, indent: int, line: int):
        """
        Enter a block that can only have one active instance (e.g., ZNAVBAR, zMeta).
        
        Clears any previous instances before adding the new one.
        
        Args:
            block_type: Type of block
            indent: Indentation level
            line: Line number
        """
        self._blocks[block_type] = [(indent, line)]
    
    def update_blocks(self, current_indent: int, current_line: int):
        """
        Update all block contexts based on current indentation.
        
        Exits blocks that have been unindented (indent >= current_indent).
        Special case: If at root level (indent=0), clear all blocks.
        
        Args:
            current_indent: Current indentation level
            current_line: Current line number (unused, for compatibility)
        """
        if current_indent == 0:
            # Root level - clear all blocks
            self._blocks.clear()
            self._blocks_with_data.clear()
            return
        
        # Exit blocks with indent >= current_indent
        for block_type in list(self._blocks.keys()):
            self._blocks[block_type] = [
                (indent, line) for indent, line in self._blocks[block_type]
                if indent < current_indent
            ]
            if not self._blocks[block_type]:
                del self._blocks[block_type]
        
        # Exit blocks with data
        for block_type in list(self._blocks_with_data.keys()):
            self._blocks_with_data[block_type] = [
                (indent, line, data) for indent, line, data in self._blocks_with_data[block_type]
                if indent < current_indent
            ]
            if not self._blocks_with_data[block_type]:
                del self._blocks_with_data[block_type]
    
    def is_inside(self, block_type: str, current_indent: int) -> bool:
        """
        Check if currently inside a block of given type at any depth.
        
        Args:
            block_type: Type of block to check
            current_indent: Current indentation level
        
        Returns:
            True if inside the block, False otherwise
        """
        if block_type in self._blocks:
            return any(indent < current_indent for indent, _ in self._blocks[block_type])
        if block_type in self._blocks_with_data:
            return any(indent < current_indent for indent, _, _ in self._blocks_with_data[block_type])
        return False
    
    def is_first_level(self, block_type: str, current_indent: int, indent_size: int = 2) -> bool:
        """
        Check if at EXACTLY the first nesting level under a block (not deeper).
        
        Used for highlighting only direct children, not grandchildren.
        Example: In ZNAVBAR, highlight first-level keys but not their nested children.
        
        Args:
            block_type: Type of block to check
            current_indent: Current indentation level
            indent_size: Size of one indentation level (default: 2 spaces)
        
        Returns:
            True if at first level, False otherwise
        """
        blocks = self._blocks.get(block_type, [])
        if not blocks:
            # Also check blocks with data
            blocks_with_data = self._blocks_with_data.get(block_type, [])
            if not blocks_with_data:
                return False
            block_indent = blocks_with_data[-1][0]
        else:
            block_indent = blocks[-1][0]
        
        # First level is exactly one indent deeper than block start
        return current_indent == block_indent + indent_size
    
    def is_at_depth(self, block_type: str, current_indent: int, min_depth: int = 1, indent_size: int = 2) -> bool:
        """
        Check if at a specific depth or deeper within a block.
        
        Args:
            block_type: Type of block to check
            current_indent: Current indentation level
            min_depth: Minimum depth level (1 = first level, 2 = second level, etc.)
            indent_size: Size of one indentation level (default: 2 spaces)
        
        Returns:
            True if at or deeper than min_depth, False otherwise
        """
        blocks = self._blocks.get(block_type, [])
        if not blocks:
            blocks_with_data = self._blocks_with_data.get(block_type, [])
            if not blocks_with_data:
                return False
            block_indent = blocks_with_data[-1][0]
        else:
            block_indent = blocks[-1][0]
        
        required_indent = block_indent + (indent_size * min_depth)
        return current_indent >= required_indent
    
    def get_block_data(self, block_type: str) -> Optional[str]:
        """
        Get additional data stored with a block (if any).
        
        Args:
            block_type: Type of block
        
        Returns:
            Block data if available, None otherwise
        """
        blocks = self._blocks_with_data.get(block_type, [])
        if blocks:
            return blocks[-1][2]  # Return data from most recent block
        return None
    
    def clear_block_type(self, block_type: str):
        """
        Clear all instances of a specific block type.
        
        Args:
            block_type: Type of block to clear
        """
        self._blocks.pop(block_type, None)
        self._blocks_with_data.pop(block_type, None)
    
    def clear_all(self):
        """Clear all tracked blocks."""
        self._blocks.clear()
        self._blocks_with_data.clear()
    
    def __repr__(self) -> str:
        """Debug representation showing active blocks."""
        active = []
        for block_type, blocks in self._blocks.items():
            active.append(f"{block_type}({len(blocks)})")
        for block_type, blocks in self._blocks_with_data.items():
            active.append(f"{block_type}+data({len(blocks)})")
        return f"BlockTracker({', '.join(active)})" if active else "BlockTracker(empty)"
