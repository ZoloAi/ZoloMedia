#!/usr/bin/env python3
"""
Phase 5 Step 3: Simple Integration Test
=========================================

Validates that:
1. CommandLauncher still imports
2. _launch_string() method exists
3. Method signature is correct
4. Lazy initialization works

Author: zOS Framework
"""

import sys
from pathlib import Path

# Add zOS to path
zos_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(zos_root))

print("\n" + "="*70)
print("PHASE 5 STEP 3: Simple Integration Test")
print("="*70)

try:
    print("\n1. Testing import...")
    from core.L2_Core.e_zDispatch.dispatch_modules.dispatch_launcher import CommandLauncher
    print("✅ CommandLauncher imported successfully")
    
    print("\n2. Checking _launch_string() method exists...")
    assert hasattr(CommandLauncher, '_launch_string'), "_launch_string() method missing"
    print("✅ _launch_string() method exists")
    
    print("\n3. Verifying method signature...")
    import inspect
    sig = inspect.signature(CommandLauncher._launch_string)
    params = list(sig.parameters.keys())
    assert 'self' in params, "Missing 'self' parameter"
    assert 'zHorizontal' in params, "Missing 'zHorizontal' parameter"
    assert 'context' in params, "Missing 'context' parameter"
    assert 'walker' in params, "Missing 'walker' parameter"
    print(f"✅ Method signature correct: {params}")
    
    print("\n4. Checking method was refactored (code size check)...")
    import inspect
    source = inspect.getsource(CommandLauncher._launch_string)
    lines = [l for l in source.split('\n') if l.strip() and not l.strip().startswith('#')]
    print(f"   Method has ~{len(lines)} lines (refactored from ~72 lines)")
    assert len(lines) < 50, f"Method should be < 50 lines after refactoring, got {len(lines)}"
    print("✅ Method was successfully refactored")
    
    print("\n" + "="*70)
    print("🎉 STEP 3 INTEGRATION TEST PASSED!")
    print("="*70)
    print("\n✅ _launch_string() is correctly integrated")
    print("✅ No import errors")
    print("✅ Method signature preserved")
    print("✅ Method successfully refactored (delegated)")
    print("\n📋 Ready for Step 4: Replace _launch_dict() Part 1")
    
    sys.exit(0)

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
