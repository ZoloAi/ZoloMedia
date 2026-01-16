"""
Unit tests for Code Action Registry (themes/__init__.py)

Tests YAML parsing and querying of code actions from zolo_default.yaml.
"""
import pytest
from themes import load_theme, CodeActionRegistry


class TestThemeCodeActions:
    """Test Theme class code action support"""
    
    def test_theme_loads_code_actions(self):
        """Test that theme loads code_actions section"""
        theme = load_theme('zolo_default')
        
        assert hasattr(theme, 'code_actions')
        assert isinstance(theme.code_actions, dict)
        assert len(theme.code_actions) > 0
    
    def test_theme_loads_code_action_config(self):
        """Test that theme loads code_action_config section"""
        theme = load_theme('zolo_default')
        
        assert hasattr(theme, 'code_action_config')
        assert isinstance(theme.code_action_config, dict)
        assert 'enabled' in theme.code_action_config
    
    def test_get_code_action_by_id(self):
        """Test getting a specific code action"""
        theme = load_theme('zolo_default')
        
        action = theme.get_code_action('add_type_hint')
        
        assert action is not None
        assert action['id'] == 'zolo.addTypeHint'
        assert action['enabled'] is True
    
    def test_get_enabled_actions(self):
        """Test getting all enabled actions"""
        theme = load_theme('zolo_default')
        
        enabled = theme.get_enabled_actions()
        
        assert isinstance(enabled, list)
        assert len(enabled) >= 3  # At least 3 enabled actions
        
        # Verify all have enabled=True
        for action in enabled:
            assert action['enabled'] is True
    
    def test_enabled_actions_sorted_by_priority(self):
        """Test that enabled actions are sorted by priority"""
        theme = load_theme('zolo_default')
        
        enabled = theme.get_enabled_actions()
        
        # Check that priorities are in descending order
        priorities = [action.get('priority', 0) for action in enabled]
        assert priorities == sorted(priorities, reverse=True)
    
    def test_get_actions_by_category(self):
        """Test filtering actions by category"""
        theme = load_theme('zolo_default')
        
        quickfix_actions = theme.get_actions_by_category('quickfix')
        refactor_actions = theme.get_actions_by_category('refactor')
        
        assert len(quickfix_actions) >= 2  # add_type_hint, fix_indentation
        assert len(refactor_actions) >= 1  # add_required_fields
        
        # Verify categories
        for action in quickfix_actions:
            assert action['category'] == 'quickfix'
        
        for action in refactor_actions:
            assert action['category'] == 'refactor'


class TestCodeActionRegistry:
    """Test CodeActionRegistry class"""
    
    def test_registry_initialization(self):
        """Test registry loads and validates actions"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        assert len(registry.actions) >= 3
        assert registry.is_enabled() is True
    
    def test_action_validation(self):
        """Test that actions are validated"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        # All loaded actions should be valid
        for action in registry.actions:
            assert registry._validate_action(action)
            assert 'id' in action
            assert 'title' in action
            assert 'triggers' in action
            assert 'execution' in action
    
    def test_get_actions_for_diagnostic(self):
        """Test matching actions to diagnostic messages"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        # Test type hint diagnostic
        matches = registry.get_actions_for_diagnostic("Consider adding type hint")
        
        assert len(matches) >= 1
        assert any(action['_id'] == 'add_type_hint' for action in matches)
    
    def test_diagnostic_matching_case_insensitive(self):
        """Test case-insensitive diagnostic matching"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        # Different cases should match
        matches1 = registry.get_actions_for_diagnostic("TYPE HINT")
        matches2 = registry.get_actions_for_diagnostic("type hint")
        matches3 = registry.get_actions_for_diagnostic("Type Hint")
        
        assert len(matches1) == len(matches2) == len(matches3)
    
    def test_indentation_diagnostic_matching(self):
        """Test matching indentation-related diagnostics"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        matches = registry.get_actions_for_diagnostic("inconsistent indentation")
        
        assert len(matches) >= 1
        assert any(action['_id'] == 'fix_indentation' for action in matches)
    
    def test_get_actions_for_file(self):
        """Test matching actions to file patterns"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        # Test zSchema file
        zschema_actions = registry.get_actions_for_file('zSchema.users.zolo')
        
        # Should include add_required_fields (file_patterns: ["zSchema.*.zolo"])
        assert any(action['_id'] == 'add_required_fields' for action in zschema_actions)
    
    def test_file_pattern_matching(self):
        """Test glob-like file pattern matching"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        # Test various patterns
        assert registry._matches_file_pattern('zSchema.users.zolo', 'zSchema.*.zolo')
        assert registry._matches_file_pattern('zSchema.products.zolo', 'zSchema.*.zolo')
        assert not registry._matches_file_pattern('zUI.navbar.zolo', 'zSchema.*.zolo')
        assert registry._matches_file_pattern('zSchema.test.yaml', 'zSchema.*.yaml')
    
    def test_get_max_actions(self):
        """Test retrieving max actions config"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        max_actions = registry.get_max_actions()
        
        assert isinstance(max_actions, int)
        assert max_actions > 0
    
    def test_pattern_matching(self):
        """Test general pattern matching"""
        theme = load_theme('zolo_default')
        registry = CodeActionRegistry(theme)
        
        # Case sensitive
        assert registry._matches_pattern("Hello World", "Hello", True)
        assert not registry._matches_pattern("Hello World", "hello", True)
        
        # Case insensitive
        assert registry._matches_pattern("Hello World", "hello", False)
        assert registry._matches_pattern("HELLO WORLD", "hello", False)


class TestCodeActionStructure:
    """Test structure of loaded code actions"""
    
    def test_add_type_hint_structure(self):
        """Test add_type_hint action has correct structure"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        assert action['id'] == 'zolo.addTypeHint'
        assert action['category'] == 'quickfix'
        assert action['priority'] == 1
        assert 'triggers' in action
        assert 'diagnostics' in action['triggers']
        assert 'execution' in action
        assert action['execution']['type'] == 'insert_at_end_of_line'
        assert 'patterns' in action['execution']
    
    def test_fix_indentation_structure(self):
        """Test fix_indentation action has correct structure"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('fix_indentation')
        
        assert action['id'] == 'zolo.fixIndentation'
        assert action['category'] == 'quickfix'
        assert action['execution']['type'] == 'replace_indentation'
        assert 'config' in action['execution']
        assert action['execution']['config']['standard_indent'] == 2
    
    def test_add_required_fields_structure(self):
        """Test add_required_fields action has correct structure"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_required_fields')
        
        assert action['id'] == 'zolo.addRequiredFields'
        assert action['category'] == 'refactor'
        assert 'file_patterns' in action['triggers']
        assert 'zSchema.*.zolo' in action['triggers']['file_patterns']
        assert action['execution']['type'] == 'insert_multiline_template'
        assert 'templates' in action['execution']
        
        # Check templates exist
        templates = action['execution']['templates']
        assert 'str' in templates
        assert 'int' in templates
        assert 'email' in templates
