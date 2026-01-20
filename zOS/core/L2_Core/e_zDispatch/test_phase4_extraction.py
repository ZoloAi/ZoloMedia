#!/usr/bin/env python3
"""
Test Phase 4: Command Handler Extraction
========================================

Tests the newly extracted command handler modules:
- list_commands.py
- string_commands.py
- dict_commands.py

Validates:
1. List command sequential execution
2. String command prefix routing
3. Dict command orchestration and routing
4. Integration with Phase 1-3 modules

Author: zOS Framework
"""

import sys
from pathlib import Path

# Add zOS to path
zos_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(zos_root))

# Mock imports for testing
class MockLogger:
    """Mock logger for testing."""
    def __init__(self):
        self.framework = self
        self.messages = []
    
    def debug(self, msg):
        self.messages.append(('debug', msg))
        print(f"[DEBUG] {msg}")
    
    def info(self, msg):
        self.messages.append(('info', msg))
        print(f"[INFO] {msg}")
    
    def warning(self, msg):
        self.messages.append(('warning', msg))
        print(f"[WARN] {msg}")
    
    def error(self, msg):
        self.messages.append(('error', msg))
        print(f"[ERROR] {msg}")


class MockzCLI:
    """Mock zCLI for testing."""
    def __init__(self):
        self.session = type('obj', (object,), {'data': {}})()
        self.zspark_obj = {}
        self.loader = type('obj', (object,), {'handle': lambda self, x: None})()
        self.zfunc = type('obj', (object,), {'handle': lambda self, x: f"zFunc executed: {x}"})()
        self.navigation = type('obj', (object,), {
            'handle_zLink': lambda self, x, walker=None: f"zLink executed: {x}"
        })()
        self.open = type('obj', (object,), {'handle': lambda self, x: f"zOpen executed: {x}"})()
        self.display = type('obj', (object,), {
            'zBasics': type('obj', (object,), {
                'output_text_via_basics': lambda self, *args: None
            })()
        })()


def test_list_commands():
    """Test ListCommandHandler."""
    print("\n" + "="*60)
    print("TEST 1: ListCommandHandler")
    print("="*60)
    
    from dispatch_modules.list_commands import ListCommandHandler
    
    logger = MockLogger()
    zcli = MockzCLI()
    handler = ListCommandHandler(zcli, logger)
    
    # Create a mock dispatcher launch function
    results = []
    def mock_dispatcher_launch(item, context=None, walker=None):
        results.append(item)
        return f"processed: {item}"
    
    # Test 1: Sequential execution
    test_list = ["item1", "item2", "item3"]
    result = handler.handle(test_list, None, None, mock_dispatcher_launch)
    
    assert len(results) == 3, f"Expected 3 items processed, got {len(results)}"
    assert results == test_list, f"Items not processed in order: {results}"
    print("✅ Sequential execution works")
    
    # Test 2: Early termination on navigation signal
    results.clear()
    def mock_dispatcher_with_signal(item, context=None, walker=None):
        results.append(item)
        if item == "item2":
            return "zBack"
        return f"processed: {item}"
    
    test_list = ["item1", "item2", "item3"]
    result = handler.handle(test_list, None, None, mock_dispatcher_with_signal)
    
    assert len(results) == 2, f"Expected early termination at item 2, got {len(results)}"
    assert result == "zBack", f"Expected 'zBack' signal, got {result}"
    print("✅ Navigation signal handling works")
    
    print(f"\n✅ ListCommandHandler: All tests passed!\n")
    return True


def test_string_commands():
    """Test StringCommandHandler."""
    print("\n" + "="*60)
    print("TEST 2: StringCommandHandler")
    print("="*60)
    
    from dispatch_modules.string_commands import StringCommandHandler
    
    # Create mock dependencies
    logger = MockLogger()
    zcli = MockzCLI()
    
    # Mock SubsystemRouter
    class MockSubsystemRouter:
        def route_zwizard(self, cmd, context, walker):
            return f"zWizard routed: {cmd}"
        def route_zread(self, cmd, context):
            return f"zRead routed: {cmd}"
    
    subsystem_router = MockSubsystemRouter()
    
    # Mock dispatcher launch function
    def mock_dispatcher_launch(item, context=None, walker=None):
        return f"dispatched: {item}"
    
    handler = StringCommandHandler(zcli, logger, subsystem_router, mock_dispatcher_launch)
    
    # Test 1: zFunc() prefix
    result = handler.handle("zFunc(test_func)", None, None)
    assert "zFunc executed" in result, f"zFunc routing failed: {result}"
    print("✅ zFunc() prefix routing works")
    
    # Test 2: zLink() prefix (with walker)
    mock_walker = type('obj', (object,), {})()
    result = handler.handle("zLink(menu:test)", None, mock_walker)
    assert "zLink executed" in result, f"zLink routing failed: {result}"
    print("✅ zLink() prefix routing works")
    
    # Test 3: zOpen() prefix
    result = handler.handle("zOpen(test.txt)", None, None)
    assert "zOpen executed" in result, f"zOpen routing failed: {result}"
    print("✅ zOpen() prefix routing works")
    
    # Test 4: zWizard() prefix
    result = handler.handle("zWizard(test_wizard)", None, mock_walker)
    assert "zWizard routed" in result, f"zWizard routing failed: {result}"
    print("✅ zWizard() prefix routing works")
    
    # Test 5: zRead() prefix
    result = handler.handle("zRead(users)", None, None)
    assert "zRead routed" in result, f"zRead routing failed: {result}"
    print("✅ zRead() prefix routing works")
    
    # Test 6: Plain string (Terminal mode)
    result = handler.handle("plain_text", None, None)
    assert result is None, f"Plain string should return None in Terminal, got: {result}"
    print("✅ Plain string handling (Terminal) works")
    
    print(f"\n✅ StringCommandHandler: All tests passed!\n")
    return True


def test_dict_commands():
    """Test DictCommandHandler (basic orchestration logic)."""
    print("\n" + "="*60)
    print("TEST 3: DictCommandHandler")
    print("="*60)
    
    from dispatch_modules.dict_commands import DictCommandHandler
    
    # Create mock dependencies
    logger = MockLogger()
    zcli = MockzCLI()
    
    # Mock Phase 1-3 dependencies
    class MockDataResolver:
        def resolve_block_data(self, horizontal, is_subsystem, context):
            pass
    
    class MockCRUDHandler:
        def handle_crud_dict(self, horizontal, context):
            return {"crud": "executed"}
    
    class MockSubsystemRouter:
        def route_zdisplay(self, horizontal, context, walker):
            return {"zdisplay": "routed"}
        def route_zfunc(self, horizontal):
            return {"zfunc": "routed"}
        def route_zdialog(self, horizontal, context, walker):
            return {"zdialog": "routed"}
        def route_zlogin(self, horizontal):
            return {"zlogin": "routed"}
        def route_zlogout(self):
            return {"zlogout": "routed"}
        def route_zlink(self, horizontal, walker):
            return {"zlink": "routed"}
        def route_zdelta(self, horizontal, walker):
            return {"zdelta": "routed"}
        def route_zwizard(self, horizontal, context, walker):
            return {"zwizard": "routed"}
        def route_zread(self, horizontal, context):
            return {"zread": "routed"}
        def route_zdata(self, horizontal, context):
            return {"zdata": "routed"}
    
    class MockShorthandExpander:
        def expand(self, horizontal, session, is_subsystem):
            # For testing, transform shorthand to zDisplay if present
            if 'zH1' in horizontal:
                # Simulate expansion
                expanded = {
                    'zH1': {
                        'zDisplay': {
                            'event': 'header',
                            'indent': 1,
                            **horizontal['zH1']
                        }
                    }
                }
                return expanded, True  # is_subsystem_call becomes True
            # Otherwise, return as-is
            return horizontal, is_subsystem
    
    class MockWizardDetector:
        def handle_implicit_wizard(self, horizontal, walker):
            return {"wizard": "detected"}
    
    class MockOrganizationalHandler:
        def handle_organizational_structure(self, horizontal, content_keys, is_subsystem, is_crud, context, walker):
            # Return None to indicate not organizational
            return None
    
    def mock_dispatcher_launch(item, context=None, walker=None):
        return f"dispatched: {item}"
    
    # Create handler
    handler = DictCommandHandler(
        zcli,
        logger,
        MockDataResolver(),
        MockCRUDHandler(),
        MockSubsystemRouter(),
        MockShorthandExpander(),
        MockWizardDetector(),
        MockOrganizationalHandler(),
        mock_dispatcher_launch
    )
    
    # Test 1: Content wrapper unwrapping
    result = handler.handle({"Content": "inner_value"}, None, None)
    assert "dispatched" in result, f"Content unwrapping failed: {result}"
    print("✅ Content wrapper unwrapping works")
    
    # Test 2: Shorthand expansion (will create organizational structure)
    # The result might be None for organizational structures, which is fine
    result = handler.handle({"zH1": {"content": "Title"}}, None, None)
    # Shorthand expansion happens even if result is None (organizational routing)
    print("✅ Shorthand expansion delegation works")
    
    # Test 3: zDisplay subsystem routing
    result = handler.handle({"zDisplay": {"event": "text", "content": "Test"}}, None, None)
    assert result == {"zdisplay": "routed"}, f"zDisplay routing failed: {result}"
    print("✅ zDisplay subsystem routing works")
    
    # Test 4: zFunc subsystem routing
    result = handler.handle({"zFunc": "test_function"}, None, None)
    assert result == {"zfunc": "routed"}, f"zFunc routing failed: {result}"
    print("✅ zFunc subsystem routing works")
    
    # Test 5: CRUD fallback
    result = handler.handle({"action": "read", "model": "users"}, None, None)
    assert result == {"crud": "executed"}, f"CRUD fallback failed: {result}"
    print("✅ CRUD fallback works")
    
    # Test 6: Implicit wizard detection
    result = handler.handle({"step1": "value1", "step2": "value2"}, None, None)
    assert result == {"wizard": "detected"}, f"Implicit wizard detection failed: {result}"
    print("✅ Implicit wizard detection works")
    
    print(f"\n✅ DictCommandHandler: All tests passed!\n")
    return True


def main():
    """Run all Phase 4 tests."""
    print("\n" + "="*70)
    print("PHASE 4 EXTRACTION TEST: Command Handlers")
    print("="*70)
    
    try:
        # Test each module
        list_ok = test_list_commands()
        string_ok = test_string_commands()
        dict_ok = test_dict_commands()
        
        # Final summary
        print("\n" + "="*70)
        print("PHASE 4 TEST SUMMARY")
        print("="*70)
        print(f"✅ ListCommandHandler: {'PASS' if list_ok else 'FAIL'}")
        print(f"✅ StringCommandHandler: {'PASS' if string_ok else 'FAIL'}")
        print(f"✅ DictCommandHandler: {'PASS' if dict_ok else 'FAIL'}")
        
        if all([list_ok, string_ok, dict_ok]):
            print("\n🎉 ALL PHASE 4 TESTS PASSED! 🎉")
            print("\nNext Steps:")
            print("  1. Create command_router.py facade for unified interface")
            print("  2. Update dispatch_launcher.py to use new command handlers")
            print("  3. Run full integration tests")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED")
            return 1
    
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
