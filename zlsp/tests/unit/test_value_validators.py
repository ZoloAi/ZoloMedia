"""
Unit tests for ValueValidator

Tests value validation logic for context-aware special values.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.parser.parser_modules.value_validators import ValueValidator
from core.parser.parser_modules.token_emitter import TokenEmitter


class TestValueValidator:
    """Test ValueValidator class"""
    
    def test_validate_zmode_valid_terminal(self):
        """Test zMode validation with valid 'Terminal' value"""
        diagnostic = ValueValidator.validate_zmode('Terminal', 0, 10)
        assert diagnostic is None
    
    def test_validate_zmode_valid_zbifrost(self):
        """Test zMode validation with valid 'zBifrost' value"""
        diagnostic = ValueValidator.validate_zmode('zBifrost', 0, 10)
        assert diagnostic is None
    
    def test_validate_zmode_invalid(self):
        """Test zMode validation with invalid value"""
        diagnostic = ValueValidator.validate_zmode('Invalid', 0, 10)
        assert diagnostic is not None
        assert 'Invalid zMode value' in diagnostic.message
        assert 'Terminal or zBifrost' in diagnostic.message
    
    def test_validate_deployment_valid_production(self):
        """Test deployment validation with valid 'Production' value"""
        diagnostic = ValueValidator.validate_deployment('Production', 0, 10)
        assert diagnostic is None
    
    def test_validate_deployment_valid_development(self):
        """Test deployment validation with valid 'Development' value"""
        diagnostic = ValueValidator.validate_deployment('Development', 0, 10)
        assert diagnostic is None
    
    def test_validate_deployment_invalid(self):
        """Test deployment validation with invalid value"""
        diagnostic = ValueValidator.validate_deployment('Staging', 0, 10)
        assert diagnostic is not None
        assert 'Invalid deployment value' in diagnostic.message
        assert ('Production' in diagnostic.message and 'Development' in diagnostic.message)
    
    def test_validate_logger_valid_all_levels(self):
        """Test logger validation with all valid log levels"""
        valid_levels = ['DEBUG', 'SESSION', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'PROD']
        for level in valid_levels:
            diagnostic = ValueValidator.validate_logger(level, 0, 10)
            assert diagnostic is None, f"{level} should be valid"
    
    def test_validate_logger_invalid(self):
        """Test logger validation with invalid value"""
        diagnostic = ValueValidator.validate_logger('TRACE', 0, 10)
        assert diagnostic is not None
        assert 'Invalid logger value' in diagnostic.message
    
    def test_validate_zvafile_valid(self):
        """Test zVaFile validation with valid value"""
        diagnostic = ValueValidator.validate_zvafile('zUI.zVaF', 0, 10)
        assert diagnostic is None
    
    def test_validate_zvafile_valid_complex(self):
        """Test zVaFile validation with valid complex name"""
        diagnostic = ValueValidator.validate_zvafile('zUI.zBreakpoints', 0, 10)
        assert diagnostic is None
    
    def test_validate_zvafile_invalid_no_zui(self):
        """Test zVaFile validation with missing zUI prefix"""
        diagnostic = ValueValidator.validate_zvafile('Component', 0, 10)
        assert diagnostic is not None
        assert 'Invalid zVaFile value' in diagnostic.message
        assert "Must start with 'zUI.'" in diagnostic.message
    
    def test_validate_zvafile_invalid_wrong_prefix(self):
        """Test zVaFile validation with wrong prefix"""
        diagnostic = ValueValidator.validate_zvafile('zBlock.Component', 0, 10)
        assert diagnostic is not None
        assert 'Invalid zVaFile value' in diagnostic.message
    
    def test_validate_zblock_valid(self):
        """Test zBlock validation with valid value"""
        diagnostic = ValueValidator.validate_zblock('zBlock.Navbar', 0, 10)
        assert diagnostic is None
    
    def test_validate_zblock_valid_complex(self):
        """Test zBlock validation with valid complex name"""
        diagnostic = ValueValidator.validate_zblock('zBlock.UserProfile', 0, 10)
        assert diagnostic is None
    
    def test_validate_zblock_invalid_no_zblock(self):
        """Test zBlock validation with missing zBlock prefix"""
        diagnostic = ValueValidator.validate_zblock('Component', 0, 10)
        assert diagnostic is not None
        assert 'Invalid zBlock value' in diagnostic.message
        assert "Must start with 'zBlock.'" in diagnostic.message
    
    def test_validate_zblock_invalid_wrong_prefix(self):
        """Test zBlock validation with wrong prefix"""
        diagnostic = ValueValidator.validate_zblock('zUI.Component', 0, 10)
        assert diagnostic is not None
        assert 'Invalid zBlock value' in diagnostic.message


class TestValueValidatorIntegration:
    """Test ValueValidator integration with TokenEmitter"""
    
    def test_validate_for_key_zspark_zmode_valid(self):
        """Test validate_for_key with valid zMode in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('zMode', 'Terminal', 0, 10, emitter)
        assert result is True  # Validation was performed
        assert len(emitter.diagnostics) == 0  # No errors
    
    def test_validate_for_key_zspark_zmode_invalid(self):
        """Test validate_for_key with invalid zMode in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('zMode', 'Invalid', 0, 10, emitter)
        assert result is True  # Validation was performed
        assert len(emitter.diagnostics) == 1  # Error added
        assert 'Invalid zMode value' in emitter.diagnostics[0].message
    
    def test_validate_for_key_zspark_deployment_valid(self):
        """Test validate_for_key with valid deployment in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('deployment', 'Production', 0, 10, emitter)
        assert result is True
        assert len(emitter.diagnostics) == 0
    
    def test_validate_for_key_zspark_deployment_invalid(self):
        """Test validate_for_key with invalid deployment in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('deployment', 'Staging', 0, 10, emitter)
        assert result is True
        assert len(emitter.diagnostics) == 1
        assert 'Invalid deployment value' in emitter.diagnostics[0].message
    
    def test_validate_for_key_zspark_logger_valid(self):
        """Test validate_for_key with valid logger in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('logger', 'DEBUG', 0, 10, emitter)
        assert result is True
        assert len(emitter.diagnostics) == 0
    
    def test_validate_for_key_zspark_logger_invalid(self):
        """Test validate_for_key with invalid logger in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('logger', 'TRACE', 0, 10, emitter)
        assert result is True
        assert len(emitter.diagnostics) == 1
        assert 'Invalid logger value' in emitter.diagnostics[0].message
    
    def test_validate_for_key_zspark_zvafile_valid(self):
        """Test validate_for_key with valid zVaFile in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('zVaFile', 'zUI.zVaF', 0, 10, emitter)
        assert result is True
        assert len(emitter.diagnostics) == 0
    
    def test_validate_for_key_zspark_zvafile_invalid(self):
        """Test validate_for_key with invalid zVaFile in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('zVaFile', 'Component', 0, 10, emitter)
        assert result is True
        assert len(emitter.diagnostics) == 1
        assert 'Invalid zVaFile value' in emitter.diagnostics[0].message
    
    def test_validate_for_key_zspark_zblock_valid(self):
        """Test validate_for_key with valid zBlock in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('zBlock', 'zBlock.Navbar', 0, 10, emitter)
        assert result is True
        assert len(emitter.diagnostics) == 0
    
    def test_validate_for_key_zspark_zblock_invalid(self):
        """Test validate_for_key with invalid zBlock in zSpark file"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('zBlock', 'Component', 0, 10, emitter)
        assert result is True
        assert len(emitter.diagnostics) == 1
        assert 'Invalid zBlock value' in emitter.diagnostics[0].message
    
    def test_validate_for_key_unknown_key(self):
        """Test validate_for_key with unknown key (no validation)"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        result = ValueValidator.validate_for_key('unknownKey', 'value', 0, 10, emitter)
        assert result is False  # No validation performed
        assert len(emitter.diagnostics) == 0
    
    def test_validate_for_key_non_zspark_file(self):
        """Test validate_for_key with zMode key in non-zSpark file (no validation)"""
        emitter = TokenEmitter("", filename="basic.zolo")
        result = ValueValidator.validate_for_key('zMode', 'Invalid', 0, 10, emitter)
        assert result is False  # No validation for non-zSpark files
        assert len(emitter.diagnostics) == 0


class TestDiagnosticDetails:
    """Test diagnostic message details and positions"""
    
    def test_diagnostic_position_zmode(self):
        """Test diagnostic position for zMode error"""
        diagnostic = ValueValidator.validate_zmode('Bad', 5, 20)
        assert diagnostic.range.start.line == 5
        assert diagnostic.range.start.character == 20
        assert diagnostic.range.end.line == 5
        assert diagnostic.range.end.character == 23  # 20 + len('Bad')
    
    def test_diagnostic_severity(self):
        """Test diagnostic severity is Error (1)"""
        diagnostic = ValueValidator.validate_zmode('Bad', 0, 0)
        assert diagnostic.severity == 1  # Error
    
    def test_diagnostic_source(self):
        """Test diagnostic source is 'zolo-lsp'"""
        diagnostic = ValueValidator.validate_zmode('Bad', 0, 0)
        assert diagnostic.source == 'zolo-lsp'
    
    def test_diagnostic_message_content_zmode(self):
        """Test diagnostic message includes invalid value and valid options"""
        diagnostic = ValueValidator.validate_zmode('Bad', 0, 0)
        assert "'Bad'" in diagnostic.message
        assert 'Terminal' in diagnostic.message or 'zBifrost' in diagnostic.message
    
    def test_diagnostic_message_content_logger(self):
        """Test diagnostic message includes all valid logger levels"""
        diagnostic = ValueValidator.validate_logger('INVALID', 0, 0)
        assert "'INVALID'" in diagnostic.message
        assert 'DEBUG' in diagnostic.message
        assert 'PROD' in diagnostic.message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
