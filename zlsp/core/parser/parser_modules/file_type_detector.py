"""
File Type Detector - Classify .zolo file types

Detects and classifies special .zolo file types based on filename patterns:
- zSpark.*.zolo - Spark configuration
- zEnv.*.zolo - Environment configuration
- zUI.*.zolo - UI components
- zConfig.*.zolo - System configuration
- zSchema.*.zolo - Data schema definitions
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Tuple


class FileType(Enum):
    """Enumeration of special .zolo file types."""
    
    GENERIC = "generic"      # Regular .zolo file
    ZSPARK = "zspark"        # zSpark.*.zolo
    ZENV = "zenv"            # zEnv.*.zolo
    ZUI = "zui"              # zUI.*.zolo
    ZCONFIG = "zconfig"      # zConfig.*.zolo
    ZSCHEMA = "zschema"      # zSchema.*.zolo


class FileTypeDetector:
    """
    Detector for .zolo file types and component names.
    
    Provides clean, testable file type detection without scattered logic.
    """
    
    # File type patterns: (prefix, prefix_length, FileType)
    FILE_PATTERNS = [
        ('zSpark.', 7, FileType.ZSPARK),
        ('zEnv.', 5, FileType.ZENV),
        ('zUI.', 4, FileType.ZUI),
        ('zConfig.', 8, FileType.ZCONFIG),
        ('zSchema.', 8, FileType.ZSCHEMA),
    ]
    
    def __init__(self, filename: Optional[str] = None):
        """
        Initialize file type detector.
        
        Args:
            filename: Optional filename to detect (can be None for generic files)
        """
        self.filename = filename
        self.file_type = self._detect_file_type()
        self.component_name = self._extract_component_name()
    
    def _detect_file_type(self) -> FileType:
        """
        Detect file type from filename.
        
        Returns:
            FileType enum value
            
        Examples:
            >>> detector = FileTypeDetector('zUI.zVaF.zolo')
            >>> detector.file_type
            FileType.ZUI
            
            >>> detector = FileTypeDetector('config.zolo')
            >>> detector.file_type
            FileType.GENERIC
        """
        if not self.filename:
            return FileType.GENERIC
        
        name = Path(self.filename).name
        
        for prefix, _, file_type in self.FILE_PATTERNS:
            if name.startswith(prefix):
                return file_type
        
        return FileType.GENERIC
    
    def _extract_component_name(self) -> Optional[str]:
        """
        Extract component name from special file types.
        
        Returns:
            Component name if applicable, None otherwise
            
        Examples:
            >>> detector = FileTypeDetector('zUI.zVaF.zolo')
            >>> detector.component_name
            'zVaF'
            
            >>> detector = FileTypeDetector('zSpark.app.zolo')
            >>> detector.component_name
            'app'
            
            >>> detector = FileTypeDetector('config.zolo')
            >>> detector.component_name
            None
        """
        if not self.filename or self.file_type == FileType.GENERIC:
            return None
        
        name = Path(self.filename).name
        
        # Find matching pattern
        for prefix, prefix_len, file_type in self.FILE_PATTERNS:
            if file_type == self.file_type:
                # Extract component: "zUI.zVaF.zolo" -> "zVaF"
                if name.startswith(prefix) and name.endswith('.zolo'):
                    component = name[prefix_len:-5]  # Remove prefix and ".zolo"
                    return component if component else None
        
        return None
    
    # ========================================================================
    # CONVENIENCE METHODS - For backward compatibility with existing code
    # ========================================================================
    
    def is_zspark(self) -> bool:
        """Check if file is a zSpark file."""
        return self.file_type == FileType.ZSPARK
    
    def is_zenv(self) -> bool:
        """Check if file is a zEnv file."""
        return self.file_type == FileType.ZENV
    
    def is_zui(self) -> bool:
        """Check if file is a zUI file."""
        return self.file_type == FileType.ZUI
    
    def is_zconfig(self) -> bool:
        """Check if file is a zConfig file."""
        return self.file_type == FileType.ZCONFIG
    
    def is_zschema(self) -> bool:
        """Check if file is a zSchema file."""
        return self.file_type == FileType.ZSCHEMA
    
    def is_generic(self) -> bool:
        """Check if file is a generic .zolo file."""
        return self.file_type == FileType.GENERIC
    
    def has_modifiers(self) -> bool:
        """
        Check if file type supports key modifiers (^, ~, !, *).
        
        Only zEnv, zUI, and zSpark files support dispatcher modifiers.
        """
        return self.file_type in (FileType.ZENV, FileType.ZUI, FileType.ZSPARK)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        if self.component_name:
            return f"FileTypeDetector({self.file_type.value}, component={self.component_name})"
        return f"FileTypeDetector({self.file_type.value})"


# ============================================================================
# HELPER FUNCTIONS - For quick detection without creating detector instance
# ============================================================================

def detect_file_type(filename: Optional[str]) -> FileType:
    """
    Quick file type detection without creating detector instance.
    
    Args:
        filename: Filename to check
        
    Returns:
        FileType enum value
        
    Examples:
        >>> detect_file_type('zUI.zVaF.zolo')
        FileType.ZUI
        
        >>> detect_file_type('config.zolo')
        FileType.GENERIC
    """
    detector = FileTypeDetector(filename)
    return detector.file_type


def extract_component_name(filename: Optional[str]) -> Optional[str]:
    """
    Quick component name extraction without creating detector instance.
    
    Args:
        filename: Filename to extract from
        
    Returns:
        Component name if applicable, None otherwise
        
    Examples:
        >>> extract_component_name('zUI.zVaF.zolo')
        'zVaF'
        
        >>> extract_component_name('config.zolo')
        None
    """
    detector = FileTypeDetector(filename)
    return detector.component_name


def get_file_info(filename: Optional[str]) -> Tuple[FileType, Optional[str]]:
    """
    Get both file type and component name in one call.
    
    Args:
        filename: Filename to analyze
        
    Returns:
        Tuple of (FileType, component_name)
        
    Examples:
        >>> get_file_info('zUI.zVaF.zolo')
        (FileType.ZUI, 'zVaF')
        
        >>> get_file_info('config.zolo')
        (FileType.GENERIC, None)
    """
    detector = FileTypeDetector(filename)
    return (detector.file_type, detector.component_name)
