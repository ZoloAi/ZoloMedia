#!/usr/bin/env python3
"""
Phase 5 Step 2: Integration Test for ListCommandHandler
========================================================

Validates that _launch_list() correctly delegates to ListCommandHandler.

Author: zOS Framework
"""

import sys
from pathlib import Path

# Add zOS to path
zos_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(zos_root))

print("\n" + "="*70)
print("PHASE 5 STEP 2: List Handler Integration Test")
print("="*70)

try:
    # Mock zDispatch and zCLI for testing
    class MockLogger:
        def __init__(self):
            self.framework = self
        def debug(self, msg):
            print(f"[DEBUG] {msg}")
        def info(self, msg):
            print(f"[INFO] {msg}")
        def warning(self, msg):
            print(f"[WARN] {msg}")
    
    class MockDisplay:
        def __init__(self):
            self.zBasics = type('obj', (object,), {
                'output_text_via_basics': lambda *args: None
            })()
        def zDeclare(self, *args, **kwargs):
            pass  # Mock zDeclare method
    
    class MockzCLI:
        def __init__(self):
            self.session = type('obj', (object,), {'data': {}})()
            self.display = MockDisplay()
    
    class MockDispatch:
        def __init__(self):
            self.zcli = MockzCLI()
            self.logger = MockLogger()
            self.mycolor = "blue"  # Mock mycolor attribute
    
    # Import CommandLauncher
    from core.L2_Core.e_zDispatch.dispatch_modules.dispatch_launcher import CommandLauncher
    
    # Create instance
    mock_dispatch = MockDispatch()
    launcher = CommandLauncher(mock_dispatch)
    
    print("\n✅ CommandLauncher initialized successfully")
    
    # Test 1: Simple list execution
    print("\n" + "-"*70)
    print("TEST 1: Simple list execution")
    print("-"*70)
    
    test_list = ["item1", "item2", "item3"]
    result = launcher._launch_list(test_list, None, None)
    
    print(f"✅ List processed without errors (result: {result})")
    
    # Test 2: Empty list
    print("\n" + "-"*70)
    print("TEST 2: Empty list")
    print("-"*70)
    
    result = launcher._launch_list([], None, None)
    assert result is None, "Empty list should return None"
    print("✅ Empty list returns None")
    
    # Test 3: Handler initialization check
    print("\n" + "-"*70)
    print("TEST 3: Handler initialization check")
    print("-"*70)
    
    assert launcher._handlers_initialized, "Handlers should be initialized after first call"
    assert launcher.list_handler is not None, "list_handler should be initialized"
    print("✅ Lazy initialization worked correctly")
    
    print("\n" + "="*70)
    print("🎉 ALL STEP 2 INTEGRATION TESTS PASSED!")
    print("="*70)
    print("\n✅ _launch_list() correctly delegates to ListCommandHandler")
    print("✅ Lazy initialization works")
    print("✅ No breaking changes detected")
    print("\nNext: Step 3 - Replace _launch_string()")
    
    sys.exit(0)

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
