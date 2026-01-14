"""
Unit tests for BlockTracker

Tests the unified block tracking system that replaces 17+ individual lists.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.parser.parser_modules.block_tracker import BlockTracker


class TestBlockTrackerBasics:
    """Test basic block tracking functionality."""
    
    def test_enter_and_check_inside(self):
        """Test entering a block and checking if inside it."""
        tracker = BlockTracker()
        
        # Not inside initially
        assert not tracker.is_inside('zRBAC', current_indent=2)
        
        # Enter block at indent 0
        tracker.enter_block('zRBAC', indent=0, line=5)
        
        # Now inside at indent 2 (deeper than 0)
        assert tracker.is_inside('zRBAC', current_indent=2)
        assert tracker.is_inside('zRBAC', current_indent=4)
        
        # Not inside at indent 0 (same level)
        assert not tracker.is_inside('zRBAC', current_indent=0)
    
    def test_first_level_detection(self):
        """Test detection of first nesting level."""
        tracker = BlockTracker()
        tracker.enter_block('ZNAVBAR', indent=0, line=1)
        
        # First level is exactly 2 spaces deeper
        assert tracker.is_first_level('ZNAVBAR', current_indent=2)
        
        # Not first level (too deep)
        assert not tracker.is_first_level('ZNAVBAR', current_indent=4)
        assert not tracker.is_first_level('ZNAVBAR', current_indent=6)
        
        # Not first level (same level or less)
        assert not tracker.is_first_level('ZNAVBAR', current_indent=0)
        assert not tracker.is_first_level('ZNAVBAR', current_indent=1)
    
    def test_single_block_replacement(self):
        """Test enter_block_single clears previous instances."""
        tracker = BlockTracker()
        
        # Enter ZNAVBAR at line 5
        tracker.enter_block_single('ZNAVBAR', indent=0, line=5)
        assert tracker.is_inside('ZNAVBAR', current_indent=2)
        
        # Enter ZNAVBAR again at line 10 (should replace)
        tracker.enter_block_single('ZNAVBAR', indent=0, line=10)
        assert tracker.is_inside('ZNAVBAR', current_indent=2)
        
        # Should only have one instance
        assert tracker._blocks['ZNAVBAR'] == [(0, 10)]


class TestBlockTrackerUpdates:
    """Test block tracking updates based on indentation."""
    
    def test_update_blocks_exit(self):
        """Test exiting blocks based on indentation."""
        tracker = BlockTracker()
        
        # Enter block at indent 0
        tracker.enter_block('zRBAC', indent=0, line=5)
        assert tracker.is_inside('zRBAC', current_indent=2)
        
        # Update at indent 2 (still inside)
        tracker.update_blocks(current_indent=2, current_line=10)
        assert tracker.is_inside('zRBAC', current_indent=2)
        
        # Update at indent 0 (should exit all blocks - root level)
        tracker.update_blocks(current_indent=0, current_line=15)
        assert not tracker.is_inside('zRBAC', current_indent=2)
    
    def test_update_blocks_nested(self):
        """Test nested block management."""
        tracker = BlockTracker()
        
        # Enter nested blocks
        tracker.enter_block('outer', indent=0, line=1)
        tracker.enter_block('inner', indent=2, line=5)
        
        assert tracker.is_inside('outer', current_indent=2)
        assert tracker.is_inside('inner', current_indent=4)
        
        # Exit inner block (indent back to 2)
        tracker.update_blocks(current_indent=2, current_line=10)
        assert tracker.is_inside('outer', current_indent=2)
        assert not tracker.is_inside('inner', current_indent=4)
    
    def test_update_blocks_root_clears_all(self):
        """Test that reaching root level clears all blocks."""
        tracker = BlockTracker()
        
        # Add multiple blocks
        tracker.enter_block('block1', indent=0, line=1)
        tracker.enter_block('block2', indent=2, line=5)
        tracker.enter_block('block3', indent=4, line=10)
        
        # All should be active
        assert tracker.is_inside('block1', current_indent=2)
        assert tracker.is_inside('block2', current_indent=4)
        assert tracker.is_inside('block3', current_indent=6)
        
        # Root level clears everything
        tracker.update_blocks(current_indent=0, current_line=20)
        assert not tracker.is_inside('block1', current_indent=2)
        assert not tracker.is_inside('block2', current_indent=4)
        assert not tracker.is_inside('block3', current_indent=6)


class TestBlockTrackerWithData:
    """Test block tracking with additional data."""
    
    def test_enter_block_with_data(self):
        """Test storing and retrieving block data."""
        tracker = BlockTracker()
        
        # Enter block with data (plural shorthand name)
        tracker.enter_block('plural_shorthand', indent=0, line=5, data='zURLs')
        
        assert tracker.is_inside('plural_shorthand', current_indent=2)
        assert tracker.get_block_data('plural_shorthand') == 'zURLs'
    
    def test_block_data_updates(self):
        """Test block data updates with indentation."""
        tracker = BlockTracker()
        
        # Enter block with data
        tracker.enter_block('plural_shorthand', indent=0, line=5, data='zURLs')
        assert tracker.get_block_data('plural_shorthand') == 'zURLs'
        
        # Update blocks - should persist
        tracker.update_blocks(current_indent=2, current_line=10)
        assert tracker.get_block_data('plural_shorthand') == 'zURLs'
        
        # Exit block
        tracker.update_blocks(current_indent=0, current_line=15)
        assert tracker.get_block_data('plural_shorthand') is None


class TestBlockTrackerDepth:
    """Test depth-based block checking."""
    
    def test_is_at_depth(self):
        """Test checking specific depth levels."""
        tracker = BlockTracker()
        tracker.enter_block('zRBAC', indent=0, line=5)
        
        # Depth 1 (first level) = indent 2
        assert tracker.is_at_depth('zRBAC', current_indent=2, min_depth=1)
        
        # Depth 2 (second level) = indent 4
        assert tracker.is_at_depth('zRBAC', current_indent=4, min_depth=1)
        assert tracker.is_at_depth('zRBAC', current_indent=4, min_depth=2)
        
        # Not at depth 2 if indent is only 2
        assert not tracker.is_at_depth('zRBAC', current_indent=2, min_depth=2)


class TestBlockTrackerUtilities:
    """Test utility methods."""
    
    def test_clear_block_type(self):
        """Test clearing specific block type."""
        tracker = BlockTracker()
        
        tracker.enter_block('block1', indent=0, line=1)
        tracker.enter_block('block2', indent=0, line=5)
        
        assert tracker.is_inside('block1', current_indent=2)
        assert tracker.is_inside('block2', current_indent=2)
        
        # Clear only block1
        tracker.clear_block_type('block1')
        assert not tracker.is_inside('block1', current_indent=2)
        assert tracker.is_inside('block2', current_indent=2)
    
    def test_clear_all(self):
        """Test clearing all blocks."""
        tracker = BlockTracker()
        
        tracker.enter_block('block1', indent=0, line=1)
        tracker.enter_block('block2', indent=0, line=5)
        tracker.enter_block('block3', indent=0, line=10, data='test')
        
        tracker.clear_all()
        
        assert not tracker.is_inside('block1', current_indent=2)
        assert not tracker.is_inside('block2', current_indent=2)
        assert not tracker.is_inside('block3', current_indent=2)
    
    def test_repr(self):
        """Test debug representation."""
        tracker = BlockTracker()
        
        # Empty tracker
        assert repr(tracker) == "BlockTracker(empty)"
        
        # With blocks
        tracker.enter_block('zRBAC', indent=0, line=5)
        tracker.enter_block('ZNAVBAR', indent=0, line=10)
        repr_str = repr(tracker)
        
        assert 'zRBAC' in repr_str
        assert 'ZNAVBAR' in repr_str


class TestBlockTrackerRealWorld:
    """Test real-world usage patterns from parser."""
    
    def test_znavbar_pattern(self):
        """Test ZNAVBAR block pattern (single instance, first-level tracking)."""
        tracker = BlockTracker()
        
        # Enter ZNAVBAR at root
        tracker.enter_block_single('ZNAVBAR', indent=0, line=10)
        
        # First-level keys (indent 2) should be detected
        assert tracker.is_first_level('ZNAVBAR', current_indent=2)
        
        # Second-level keys (indent 4) should NOT be first-level
        assert not tracker.is_first_level('ZNAVBAR', current_indent=4)
        assert tracker.is_inside('ZNAVBAR', current_indent=4)  # But still inside
    
    def test_zrbac_pattern(self):
        """Test zRBAC block pattern (can be nested anywhere)."""
        tracker = BlockTracker()
        
        # zRBAC can appear at any level
        tracker.enter_block('zRBAC', indent=2, line=15)
        
        # Check if inside at various depths
        assert tracker.is_inside('zRBAC', current_indent=4)
        assert tracker.is_inside('zRBAC', current_indent=6)
        assert not tracker.is_inside('zRBAC', current_indent=2)
    
    def test_plural_shorthand_pattern(self):
        """Test plural shorthand pattern (tracks shorthand name)."""
        tracker = BlockTracker()
        
        # Enter zURLs shorthand block
        tracker.enter_block('plural_shorthand', indent=2, line=20, data='zURLs')
        
        assert tracker.is_inside('plural_shorthand', current_indent=4)
        assert tracker.get_block_data('plural_shorthand') == 'zURLs'
        
        # At depth 2 (4 spaces deeper than block start)
        assert tracker.is_at_depth('plural_shorthand', current_indent=6, min_depth=2)
    
    def test_zmeta_pattern(self):
        """Test zMeta block pattern (single instance, first-level only)."""
        tracker = BlockTracker()
        
        # zMeta at root
        tracker.enter_block_single('zMeta', indent=0, line=1)
        
        # First-level keys are zKernel data keys
        assert tracker.is_first_level('zMeta', current_indent=2)
        
        # Exit zMeta when new root key appears
        tracker.update_blocks(current_indent=0, current_line=10)
        assert not tracker.is_inside('zMeta', current_indent=2)
