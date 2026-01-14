"""
Unit tests for KeyDetector

Tests context-aware key type detection for all special .zolo file types.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.parser.parser_modules.key_detector import KeyDetector, detect_key_type
from core.parser.parser_modules.token_emitter import TokenEmitter
from core.lsp_types import TokenType


class TestRootKeyDetection:
    """Test root-level key detection"""
    
    def test_zmeta_in_zui_file(self):
        """Test zMeta detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = KeyDetector.detect_root_key('zMeta', emitter, 0)
        assert token_type == TokenType.ZMETA_KEY
    
    def test_zvaf_in_zui_file(self):
        """Test zVaF detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = KeyDetector.detect_root_key('zVaF', emitter, 0)
        assert token_type == TokenType.ZMETA_KEY
    
    def test_component_name_in_zui_file(self):
        """Test component name detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.MyComponent.zolo")
        token_type = KeyDetector.detect_root_key('MyComponent', emitter, 0)
        assert token_type == TokenType.ZMETA_KEY
    
    def test_zmeta_in_zschema_file(self):
        """Test zMeta detection in zSchema files"""
        emitter = TokenEmitter("", filename="zSchema.users.zolo")
        token_type = KeyDetector.detect_root_key('zMeta', emitter, 0)
        assert token_type == TokenType.ZMETA_KEY
    
    def test_zspark_in_zspark_file(self):
        """Test zSpark detection in zSpark files"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        token_type = KeyDetector.detect_root_key('zSpark', emitter, 0)
        assert token_type == TokenType.ZSPARK_KEY
    
    def test_zenv_config_keys(self):
        """Test DEPLOYMENT, DEBUG, LOG_LEVEL in zEnv files"""
        emitter = TokenEmitter("", filename="zEnv.development.zolo")
        assert KeyDetector.detect_root_key('DEPLOYMENT', emitter, 0) == TokenType.ZENV_CONFIG_KEY
        assert KeyDetector.detect_root_key('DEBUG', emitter, 0) == TokenType.ZENV_CONFIG_KEY
        assert KeyDetector.detect_root_key('LOG_LEVEL', emitter, 0) == TokenType.ZENV_CONFIG_KEY
    
    def test_uppercase_z_prefixed_in_zenv(self):
        """Test uppercase Z-prefixed keys in zEnv files"""
        emitter = TokenEmitter("", filename="zEnv.development.zolo")
        token_type = KeyDetector.detect_root_key('ZNAVBAR', emitter, 0)
        assert token_type == TokenType.ZCONFIG_KEY
    
    def test_zconfig_component_name(self):
        """Test zConfig component name detection"""
        emitter = TokenEmitter("", filename="zConfig.machine.zolo")
        token_type = KeyDetector.detect_root_key('machine', emitter, 0)
        assert token_type == TokenType.ZCONFIG_KEY
    
    def test_regular_root_key(self):
        """Test regular root keys default to ROOT_KEY"""
        emitter = TokenEmitter("", filename="basic.zolo")
        token_type = KeyDetector.detect_root_key('myKey', emitter, 0)
        assert token_type == TokenType.ROOT_KEY


class TestNestedKeyDetection:
    """Test nested key detection"""
    
    def test_zrbac_in_zenv_file(self):
        """Test zRBAC detection in zEnv files"""
        emitter = TokenEmitter("", filename="zEnv.development.zolo")
        token_type = KeyDetector.detect_nested_key('zRBAC', emitter, 2)
        assert token_type == TokenType.ZRBAC_KEY
    
    def test_zrbac_in_zui_file(self):
        """Test zRBAC detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = KeyDetector.detect_nested_key('zRBAC', emitter, 2)
        assert token_type == TokenType.ZRBAC_KEY
    
    def test_zrbac_option_keys(self):
        """Test zRBAC option keys"""
        emitter = TokenEmitter("", filename="zEnv.development.zolo")
        emitter.enter_zrbac_block(2, 0)
        
        for key in ['access', 'role', 'permissions', 'owner', 'public', 'private']:
            token_type = KeyDetector.detect_nested_key(key, emitter, 4)
            assert token_type == TokenType.ZRBAC_OPTION_KEY
    
    def test_znavbar_first_level_keys(self):
        """Test ZNAVBAR first-level nested keys"""
        emitter = TokenEmitter("", filename="zEnv.development.zolo")
        emitter.enter_znavbar_block(0, 0)
        token_type = KeyDetector.detect_nested_key('home', emitter, 2)
        assert token_type == TokenType.ZNAVBAR_NESTED_KEY
    
    def test_zkernel_data_keys_in_zschema(self):
        """Test zKernel data keys under zMeta in zSchema files"""
        emitter = TokenEmitter("", filename="zSchema.users.zolo")
        emitter.enter_zmeta_block(0, 0)
        
        for key in ['Data_Type', 'Data_Label', 'Data_Source', 'Schema_Name', 'zMigration', 'zMigrationVersion']:
            token_type = KeyDetector.detect_nested_key(key, emitter, 2)
            assert token_type == TokenType.ZKERNEL_DATA_KEY
    
    def test_zschema_property_keys(self):
        """Test zSchema property keys"""
        emitter = TokenEmitter("", filename="zSchema.users.zolo")
        # Not inside zMeta, at grandchild+ level
        for key in ['type', 'pk', 'required', 'default', 'rules', 'unique']:
            token_type = KeyDetector.detect_nested_key(key, emitter, 4)
            assert token_type == TokenType.ZSCHEMA_PROPERTY_KEY
    
    def test_zsub_grandchild_in_zenv(self):
        """Test zSub at grandchild level in zEnv files"""
        emitter = TokenEmitter("", filename="zEnv.development.zolo")
        token_type = KeyDetector.detect_nested_key('zSub', emitter, 4)
        assert token_type == TokenType.ZSUB_KEY
    
    def test_zsub_shallow_in_zui(self):
        """Test zSub at shallow level in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = KeyDetector.detect_nested_key('zSub', emitter, 2)
        assert token_type == TokenType.UI_ELEMENT_KEY
    
    def test_bifrost_keys(self):
        """Test underscore-prefixed Bifrost keys"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        assert KeyDetector.detect_nested_key('_zClass', emitter, 2) == TokenType.BIFROST_KEY
        assert KeyDetector.detect_nested_key('_zId', emitter, 2) == TokenType.BIFROST_KEY


class TestUIElementKeys:
    """Test UI element key detection"""
    
    def test_zimage_key(self):
        """Test zImage detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = KeyDetector.detect_nested_key('zImage', emitter, 2)
        assert token_type == TokenType.UI_ELEMENT_KEY
    
    def test_ztext_key(self):
        """Test zText detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = KeyDetector.detect_nested_key('zText', emitter, 2)
        assert token_type == TokenType.UI_ELEMENT_KEY
    
    def test_zmd_key(self):
        """Test zMD detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = KeyDetector.detect_nested_key('zMD', emitter, 2)
        assert token_type == TokenType.UI_ELEMENT_KEY
    
    def test_zurl_key(self):
        """Test zURL detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = KeyDetector.detect_nested_key('zURL', emitter, 2)
        assert token_type == TokenType.UI_ELEMENT_KEY
    
    def test_header_keys(self):
        """Test zH1-zH6 detection in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        for key in ['zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6']:
            token_type = KeyDetector.detect_nested_key(key, emitter, 2)
            assert token_type == TokenType.UI_ELEMENT_KEY
    
    def test_plural_shorthand_keys(self):
        """Test plural shorthand keys detection"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        # Plural shorthand keys are detected as UI_ELEMENT_KEY
        for key in ['zURLs', 'zTexts', 'zImages', 'zMDs', 'zH1s', 'zH2s']:
            token_type = KeyDetector.detect_nested_key(key, emitter, 2)
            assert token_type == TokenType.UI_ELEMENT_KEY
    
    def test_ui_element_option_keys(self):
        """Test UI element option keys default to NESTED_KEY"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        emitter.enter_zimage_block(2, 0)
        
        # UI element option keys are just regular nested keys
        for key in ['src', 'alt', 'width', 'height', 'quality']:
            token_type = KeyDetector.detect_nested_key(key, emitter, 4)
            assert token_type == TokenType.NESTED_KEY
    
    def test_ui_element_keys_non_zui_file(self):
        """Test UI element keys in non-zUI files default to NESTED_KEY"""
        emitter = TokenEmitter("", filename="basic.zolo")
        token_type = KeyDetector.detect_nested_key('zImage', emitter, 2)
        assert token_type == TokenType.NESTED_KEY


class TestModifierExtraction:
    """Test key modifier extraction"""
    
    def test_prefix_caret_modifier(self):
        """Test ^ prefix modifier"""
        core, prefix, suffix = KeyDetector.extract_modifiers('^locked')
        assert core == 'locked'
        assert prefix == '^'
        assert suffix is None
    
    def test_prefix_tilde_modifier(self):
        """Test ~ prefix modifier"""
        core, prefix, suffix = KeyDetector.extract_modifiers('~default')
        assert core == 'default'
        assert prefix == '~'
        assert suffix is None
    
    def test_suffix_exclamation_modifier(self):
        """Test ! suffix modifier"""
        core, prefix, suffix = KeyDetector.extract_modifiers('editable!')
        assert core == 'editable'
        assert prefix is None
        assert suffix == '!'
    
    def test_suffix_asterisk_modifier(self):
        """Test * suffix modifier"""
        core, prefix, suffix = KeyDetector.extract_modifiers('required*')
        assert core == 'required'
        assert prefix is None
        assert suffix == '*'
    
    def test_both_modifiers(self):
        """Test both prefix and suffix modifiers"""
        core, prefix, suffix = KeyDetector.extract_modifiers('^optional*')
        assert core == 'optional'
        assert prefix == '^'
        assert suffix == '*'
    
    def test_no_modifiers(self):
        """Test key with no modifiers"""
        core, prefix, suffix = KeyDetector.extract_modifiers('regularKey')
        assert core == 'regularKey'
        assert prefix is None
        assert suffix is None


class TestBlockEntryDetection:
    """Test block entry detection"""
    
    def test_zrbac_block_entry(self):
        """Test zRBAC block entry detection"""
        emitter = TokenEmitter("", filename="zEnv.development.zolo")
        block_type = KeyDetector.should_enter_block('zRBAC', emitter)
        assert block_type == 'zrbac'
    
    def test_zmeta_block_entry_zschema(self):
        """Test zMeta block entry in zSchema files"""
        emitter = TokenEmitter("", filename="zSchema.users.zolo")
        block_type = KeyDetector.should_enter_block('zMeta', emitter)
        assert block_type == 'zmeta'
    
    def test_zmeta_no_block_entry_zui(self):
        """Test zMeta doesn't trigger block entry in zUI files"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        block_type = KeyDetector.should_enter_block('zMeta', emitter)
        assert block_type is None
    
    def test_znavbar_block_entry(self):
        """Test ZNAVBAR block entry"""
        emitter = TokenEmitter("", filename="zEnv.development.zolo")
        block_type = KeyDetector.should_enter_block('ZNAVBAR', emitter)
        assert block_type == 'znavbar'
    
    def test_ui_element_block_entries(self):
        """Test UI element block entries"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        assert KeyDetector.should_enter_block('zImage', emitter) == 'zimage'
        assert KeyDetector.should_enter_block('zText', emitter) == 'ztext'
        assert KeyDetector.should_enter_block('zMD', emitter) == 'zmd'
        assert KeyDetector.should_enter_block('zURL', emitter) == 'zurl'
        assert KeyDetector.should_enter_block('zH1', emitter) == 'header'
        assert KeyDetector.should_enter_block('zURLs', emitter) == 'plural_shorthand'
    
    def test_no_block_entry(self):
        """Test regular keys don't trigger block entry"""
        emitter = TokenEmitter("", filename="basic.zolo")
        block_type = KeyDetector.should_enter_block('regularKey', emitter)
        assert block_type is None


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_detect_key_type_root(self):
        """Test detect_key_type helper for root keys"""
        emitter = TokenEmitter("", filename="zSpark.example.zolo")
        token_type = detect_key_type('zSpark', emitter, 0, is_root=True)
        assert token_type == TokenType.ZSPARK_KEY
    
    def test_detect_key_type_nested(self):
        """Test detect_key_type helper for nested keys"""
        emitter = TokenEmitter("", filename="zUI.zVaF.zolo")
        token_type = detect_key_type('zImage', emitter, 2, is_root=False)
        assert token_type == TokenType.UI_ELEMENT_KEY


class TestKeyDetectorSets:
    """Test key detector constant sets"""
    
    def test_zkernel_data_keys_complete(self):
        """Test ZKERNEL_DATA_KEYS set completeness"""
        expected = {'Data_Type', 'Data_Label', 'Data_Source', 'Schema_Name', 'zMigration', 'zMigrationVersion'}
        assert KeyDetector.ZKERNEL_DATA_KEYS == expected
    
    def test_zschema_property_keys_complete(self):
        """Test ZSCHEMA_PROPERTY_KEYS set completeness"""
        required_keys = {'type', 'pk', 'required', 'default', 'rules'}
        assert required_keys.issubset(KeyDetector.ZSCHEMA_PROPERTY_KEYS)
    
    def test_ui_element_keys_complete(self):
        """Test UI_ELEMENT_KEYS set completeness"""
        required_keys = {'zImage', 'zText', 'zMD', 'zURL', 'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'}
        assert required_keys.issubset(KeyDetector.UI_ELEMENT_KEYS)
    
    def test_plural_shorthand_keys_complete(self):
        """Test PLURAL_SHORTHAND_KEYS set completeness"""
        expected = {'zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs'}
        assert KeyDetector.PLURAL_SHORTHAND_KEYS == expected


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
