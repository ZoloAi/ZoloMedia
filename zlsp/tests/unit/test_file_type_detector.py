"""
Unit tests for FileTypeDetector - File type classification

Tests the detection and classification of special .zolo file types.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

import pytest
from core.parser.parser_modules.file_type_detector import (
    FileType,
    FileTypeDetector,
    detect_file_type,
    extract_component_name,
    get_file_info,
)


class TestFileTypeDetection:
    """Test basic file type detection from filenames."""
    
    def test_zspark_detection(self):
        """Test zSpark file detection."""
        detector = FileTypeDetector('zSpark.app.zolo')
        assert detector.file_type == FileType.ZSPARK
        assert detector.is_zspark()
        assert not detector.is_zenv()
        
    def test_zenv_detection(self):
        """Test zEnv file detection."""
        detector = FileTypeDetector('zEnv.development.zolo')
        assert detector.file_type == FileType.ZENV
        assert detector.is_zenv()
        assert not detector.is_zui()
        
    def test_zui_detection(self):
        """Test zUI file detection."""
        detector = FileTypeDetector('zUI.zVaF.zolo')
        assert detector.file_type == FileType.ZUI
        assert detector.is_zui()
        assert not detector.is_zconfig()
        
    def test_zconfig_detection(self):
        """Test zConfig file detection."""
        detector = FileTypeDetector('zConfig.machine.zolo')
        assert detector.file_type == FileType.ZCONFIG
        assert detector.is_zconfig()
        assert not detector.is_zschema()
        
    def test_zschema_detection(self):
        """Test zSchema file detection."""
        detector = FileTypeDetector('zSchema.users.zolo')
        assert detector.file_type == FileType.ZSCHEMA
        assert detector.is_zschema()
        assert not detector.is_zspark()
        
    def test_generic_file_detection(self):
        """Test generic .zolo file detection."""
        detector = FileTypeDetector('config.zolo')
        assert detector.file_type == FileType.GENERIC
        assert detector.is_generic()
        assert not detector.is_zspark()
        assert not detector.is_zenv()
        
    def test_none_filename(self):
        """Test with None filename."""
        detector = FileTypeDetector(None)
        assert detector.file_type == FileType.GENERIC
        assert detector.is_generic()
        
    def test_empty_filename(self):
        """Test with empty filename."""
        detector = FileTypeDetector('')
        assert detector.file_type == FileType.GENERIC
        assert detector.is_generic()


class TestComponentNameExtraction:
    """Test component name extraction from special file types."""
    
    def test_zui_component_extraction(self):
        """Test extracting component name from zUI file."""
        detector = FileTypeDetector('zUI.zVaF.zolo')
        assert detector.component_name == 'zVaF'
        
    def test_zspark_component_extraction(self):
        """Test extracting component name from zSpark file."""
        detector = FileTypeDetector('zSpark.app.zolo')
        assert detector.component_name == 'app'
        
    def test_zenv_component_extraction(self):
        """Test extracting component name from zEnv file."""
        detector = FileTypeDetector('zEnv.development.zolo')
        assert detector.component_name == 'development'
        
    def test_zconfig_component_extraction(self):
        """Test extracting component name from zConfig file."""
        detector = FileTypeDetector('zConfig.machine.zolo')
        assert detector.component_name == 'machine'
        
    def test_zschema_component_extraction(self):
        """Test extracting component name from zSchema file."""
        detector = FileTypeDetector('zSchema.users.zolo')
        assert detector.component_name == 'users'
        
    def test_generic_no_component(self):
        """Test that generic files return None for component name."""
        detector = FileTypeDetector('config.zolo')
        assert detector.component_name is None
        
    def test_component_with_dots(self):
        """Test component names with dots."""
        detector = FileTypeDetector('zUI.user.profile.zolo')
        assert detector.component_name == 'user.profile'
        
    def test_none_filename_no_component(self):
        """Test that None filename returns None for component."""
        detector = FileTypeDetector(None)
        assert detector.component_name is None


class TestConvenienceMethods:
    """Test convenience methods for file type checks."""
    
    def test_has_modifiers_true(self):
        """Test has_modifiers for files that support modifiers."""
        zui_detector = FileTypeDetector('zUI.zVaF.zolo')
        zenv_detector = FileTypeDetector('zEnv.dev.zolo')
        zspark_detector = FileTypeDetector('zSpark.app.zolo')
        
        assert zui_detector.has_modifiers()
        assert zenv_detector.has_modifiers()
        assert zspark_detector.has_modifiers()
        
    def test_has_modifiers_false(self):
        """Test has_modifiers for files that don't support modifiers."""
        zconfig_detector = FileTypeDetector('zConfig.machine.zolo')
        zschema_detector = FileTypeDetector('zSchema.users.zolo')
        generic_detector = FileTypeDetector('config.zolo')
        
        assert not zconfig_detector.has_modifiers()
        assert not zschema_detector.has_modifiers()
        assert not generic_detector.has_modifiers()


class TestHelperFunctions:
    """Test module-level helper functions."""
    
    def test_detect_file_type_function(self):
        """Test detect_file_type helper function."""
        assert detect_file_type('zUI.zVaF.zolo') == FileType.ZUI
        assert detect_file_type('zSpark.app.zolo') == FileType.ZSPARK
        assert detect_file_type('config.zolo') == FileType.GENERIC
        assert detect_file_type(None) == FileType.GENERIC
        
    def test_extract_component_name_function(self):
        """Test extract_component_name helper function."""
        assert extract_component_name('zUI.zVaF.zolo') == 'zVaF'
        assert extract_component_name('zSpark.app.zolo') == 'app'
        assert extract_component_name('config.zolo') is None
        assert extract_component_name(None) is None
        
    def test_get_file_info_function(self):
        """Test get_file_info helper function."""
        file_type, component = get_file_info('zUI.zVaF.zolo')
        assert file_type == FileType.ZUI
        assert component == 'zVaF'
        
        file_type, component = get_file_info('config.zolo')
        assert file_type == FileType.GENERIC
        assert component is None


class TestFilePathHandling:
    """Test handling of various file path formats."""
    
    def test_absolute_path(self):
        """Test with absolute file path."""
        detector = FileTypeDetector('/Users/test/projects/zUI.zVaF.zolo')
        assert detector.file_type == FileType.ZUI
        assert detector.component_name == 'zVaF'
        
    def test_relative_path(self):
        """Test with relative file path."""
        detector = FileTypeDetector('examples/zEnv.development.zolo')
        assert detector.file_type == FileType.ZENV
        assert detector.component_name == 'development'
        
    def test_filename_only(self):
        """Test with just filename (no path)."""
        detector = FileTypeDetector('zSpark.app.zolo')
        assert detector.file_type == FileType.ZSPARK
        assert detector.component_name == 'app'


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_file_without_extension(self):
        """Test file without .zolo extension."""
        detector = FileTypeDetector('zUI.zVaF')
        # Should still detect as ZUI but won't extract component properly
        assert detector.file_type == FileType.ZUI
        # Component extraction expects .zolo extension
        assert detector.component_name is None
        
    def test_wrong_extension(self):
        """Test file with wrong extension."""
        detector = FileTypeDetector('zUI.zVaF.yaml')
        # Should still detect as ZUI based on prefix
        assert detector.file_type == FileType.ZUI
        # But won't extract component (expects .zolo)
        assert detector.component_name is None
        
    def test_component_empty_string(self):
        """Test when component would be empty string."""
        detector = FileTypeDetector('zUI..zolo')
        assert detector.file_type == FileType.ZUI
        assert detector.component_name is None  # Empty string becomes None
        
    def test_repr_with_component(self):
        """Test __repr__ with component name."""
        detector = FileTypeDetector('zUI.zVaF.zolo')
        repr_str = repr(detector)
        assert 'zui' in repr_str
        assert 'zVaF' in repr_str
        
    def test_repr_without_component(self):
        """Test __repr__ without component name."""
        detector = FileTypeDetector('config.zolo')
        repr_str = repr(detector)
        assert 'generic' in repr_str
        assert 'component' not in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
