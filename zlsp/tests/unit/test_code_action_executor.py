"""
Unit tests for Code Action Executor (core/server/features/code_actions.py)

Tests generic execution engine that turns YAML configs into LSP TextEdit objects.
"""
import pytest
from themes import load_theme, CodeActionRegistry
from core.server.features.code_actions import CodeActionExecutor, execute_code_action
from lsprotocol.types import Position


class TestCodeActionExecutor:
    """Test CodeActionExecutor class"""
    
    def test_executor_initialization(self):
        """Test executor can be instantiated"""
        executor = CodeActionExecutor()
        assert executor is not None
    
    def test_execute_with_unknown_type(self):
        """Test executor returns empty list for unknown execution type"""
        executor = CodeActionExecutor()
        action = {
            'execution': {
                'type': 'unknown_type'
            }
        }
        context = {'line': 'test', 'line_number': 0}
        
        edits = executor.execute(action, context)
        
        assert edits == []


class TestInsertAtEndOfLine:
    """Test insert_at_end_of_line execution type"""
    
    def test_add_type_hint_string(self):
        """Test adding type hint for string value"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'email: "john@example.com"',
            'line_number': 5,
            'cursor_position': 10,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> str <#'
        assert edits[0].range.start.line == 5
        assert edits[0].range.start.character == len(context['line'])
    
    def test_add_type_hint_integer(self):
        """Test adding type hint for integer value"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'port: 8080',
            'line_number': 10,
            'cursor_position': 5,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> int <#'
    
    def test_add_type_hint_boolean(self):
        """Test adding type hint for boolean value"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'enabled: true',
            'line_number': 3,
            'cursor_position': 8,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> bool <#'
    
    def test_add_type_hint_float(self):
        """Test adding type hint for float value"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'timeout: 3.14',
            'line_number': 7,
            'cursor_position': 10,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> float <#'
    
    def test_add_type_hint_list(self):
        """Test adding type hint for list value"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'items: [1, 2, 3]',
            'line_number': 12,
            'cursor_position': 8,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> list <#'
    
    def test_add_type_hint_dict(self):
        """Test adding type hint for dict value"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'config: { key: value }',
            'line_number': 15,
            'cursor_position': 10,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> dict <#'
    
    def test_add_type_hint_null(self):
        """Test adding type hint for null value"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'optional_field: null',
            'line_number': 20,
            'cursor_position': 15,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> None <#'
    
    def test_add_type_hint_zpath(self):
        """Test adding type hint for zPath value"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'path: @.logs',
            'line_number': 25,
            'cursor_position': 10,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> zPath <#'
    
    def test_add_type_hint_default_fallback(self):
        """Test adding type hint falls back to Any for unknown types"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'unknown: some_weird_value',
            'line_number': 30,
            'cursor_position': 10,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert edits[0].new_text == '  #> Any <#'


class TestReplaceIndentation:
    """Test replace_indentation execution type"""
    
    def test_fix_indentation_4_to_2_spaces(self):
        """Test fixing indentation from 4 to 2 spaces (preserves level 2)"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('fix_indentation')
        
        context = {
            'line': '    email: test',  # 4 spaces = level 2
            'line_number': 10,
            'cursor_position': 5,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        # 4 spaces = level 2, normalized to 2*2 = 4 spaces (preserves nesting)
        assert edits[0].new_text == '    '
        assert edits[0].range.start.line == 10
        assert edits[0].range.start.character == 0
        assert edits[0].range.end.character == 4
    
    def test_fix_indentation_tabs_to_spaces(self):
        """Test converting tabs to spaces"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('fix_indentation')
        
        context = {
            'line': '\t\temail: test',  # 2 tabs = 2 chars
            'line_number': 5,
            'cursor_position': 2,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        # 2 tabs = 2 chars, rounds to level 1 (2 // 2 = 1), so 1*2 = 2 spaces
        assert edits[0].new_text == '  '
        assert edits[0].range.start.character == 0
        assert edits[0].range.end.character == 2
    
    def test_fix_indentation_mixed_spaces_tabs(self):
        """Test fixing mixed spaces and tabs"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('fix_indentation')
        
        context = {
            'line': '  \t  name: value',  # Mixed
            'line_number': 8,
            'cursor_position': 5,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        # Should normalize to consistent spacing
        assert all(c == ' ' for c in edits[0].new_text)


class TestInsertMultilineTemplate:
    """Test insert_multiline_template execution type"""
    
    def test_add_required_fields_str(self):
        """Test scaffolding string field"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_required_fields')
        
        document = """users:
  email:
    type: str
"""
        
        context = {
            'line': '  email:',
            'line_number': 1,
            'cursor_position': 8,
            'document_content': document,
            'file_name': 'zSchema.users.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        # Should insert required, rules, max_length
        assert 'required: true' in edits[0].new_text
        assert 'rules:' in edits[0].new_text
        assert 'max_length: 255' in edits[0].new_text
    
    def test_add_required_fields_int(self):
        """Test scaffolding integer field"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_required_fields')
        
        document = """users:
  age:
    type: int
"""
        
        context = {
            'line': '  age:',
            'line_number': 1,
            'cursor_position': 6,
            'document_content': document,
            'file_name': 'zSchema.users.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        assert 'required: true' in edits[0].new_text
        assert 'default: 0' in edits[0].new_text
    
    def test_add_required_fields_email(self):
        """Test scaffolding email field (special case)"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_required_fields')
        
        document = """users:
  email:
    type: str
"""
        
        context = {
            'line': '  email:',  # "email" key triggers special template
            'line_number': 1,
            'cursor_position': 8,
            'document_content': document,
            'file_name': 'zSchema.users.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        # Email template has unique and format
        assert 'unique: true' in edits[0].new_text
        assert 'format: email' in edits[0].new_text
    
    def test_add_required_fields_password(self):
        """Test scaffolding password field (special case)"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_required_fields')
        
        document = """users:
  password:
    type: str
"""
        
        context = {
            'line': '  password:',  # "password" key triggers special template
            'line_number': 1,
            'cursor_position': 11,
            'document_content': document,
            'file_name': 'zSchema.users.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert len(edits) == 1
        # Password template has zHash and min_length
        assert 'zHash: bcrypt' in edits[0].new_text
        assert 'min_length: 8' in edits[0].new_text


class TestHelperMethods:
    """Test executor helper methods"""
    
    def test_extract_value_from_line(self):
        """Test extracting value from key: value line"""
        executor = CodeActionExecutor()
        
        assert executor._extract_value_from_line('email: john@test.com') == 'john@test.com'
        assert executor._extract_value_from_line('port: 8080') == '8080'
        assert executor._extract_value_from_line('enabled: true') == 'true'
        assert executor._extract_value_from_line('no_colon') == 'no_colon'
    
    def test_get_leading_whitespace(self):
        """Test getting leading whitespace"""
        executor = CodeActionExecutor()
        
        ws, length = executor._get_leading_whitespace('  test')
        assert ws == '  '
        assert length == 2
        
        ws, length = executor._get_leading_whitespace('    test')
        assert ws == '    '
        assert length == 4
        
        ws, length = executor._get_leading_whitespace('test')
        assert ws == ''
        assert length == 0
    
    def test_matches_pattern_condition_regex(self):
        """Test pattern matching with regex"""
        executor = CodeActionExecutor()
        
        pattern = {'match_regex': r'^\d+$'}
        assert executor._matches_pattern_condition('123', pattern)
        assert not executor._matches_pattern_condition('abc', pattern)
    
    def test_matches_pattern_condition_values(self):
        """Test pattern matching with exact values"""
        executor = CodeActionExecutor()
        
        pattern = {'match_values': ['true', 'false']}
        assert executor._matches_pattern_condition('true', pattern)
        assert executor._matches_pattern_condition('false', pattern)
        assert not executor._matches_pattern_condition('maybe', pattern)
    
    def test_matches_pattern_condition_default(self):
        """Test default pattern always matches"""
        executor = CodeActionExecutor()
        
        pattern = {'condition': 'default', 'hint': '#> Any <#'}
        assert executor._matches_pattern_condition('anything', pattern)
        assert executor._matches_pattern_condition('', pattern)


class TestConvenienceFunction:
    """Test execute_code_action convenience function"""
    
    def test_execute_code_action_function(self):
        """Test convenience function works"""
        theme = load_theme('zolo_default')
        action = theme.get_code_action('add_type_hint')
        
        context = {
            'line': 'name: "John"',
            'line_number': 0,
            'cursor_position': 5,
            'document_content': '',
            'file_name': 'test.zolo'
        }
        
        edits = execute_code_action(action, context)
        
        assert isinstance(edits, list)
        assert len(edits) > 0
        assert edits[0].new_text == '  #> str <#'
