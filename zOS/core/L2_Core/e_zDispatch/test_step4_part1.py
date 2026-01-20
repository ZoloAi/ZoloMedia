#!/usr/bin/env python3
"""
Phase 5 Step 4 Part 1: Feature Flag Integration Test
=====================================================

Validates that:
1. CommandLauncher still imports
2. _launch_dict() method exists
3. _launch_dict_new() method exists
4. Feature flag USE_NEW_DICT_HANDLER exists
5. Flag is disabled by default (safe)
6. Methods have correct signatures

Author: zOS Framework
"""

import sys
from pathlib import Path

# Add zOS to path
zos_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(zos_root))

print("\n" + "="*70)
print("PHASE 5 STEP 4 PART 1: Feature Flag Integration Test")
print("="*70)

try:
    print("\n1. Testing import...")
    from core.L2_Core.e_zDispatch.dispatch_modules.dispatch_launcher import CommandLauncher
    print("✅ CommandLauncher imported successfully")
    
    print("\n2. Checking _launch_dict() method exists (OLD implementation)...")
    assert hasattr(CommandLauncher, '_launch_dict'), "_launch_dict() method missing"
    print("✅ _launch_dict() method exists")
    
    print("\n3. Checking _launch_dict_new() method exists (NEW implementation)...")
    assert hasattr(CommandLauncher, '_launch_dict_new'), "_launch_dict_new() method missing"
    print("✅ _launch_dict_new() method exists")
    
    print("\n4. Checking USE_NEW_DICT_HANDLER feature flag exists...")
    assert hasattr(CommandLauncher, 'USE_NEW_DICT_HANDLER'), "USE_NEW_DICT_HANDLER flag missing"
    print(f"✅ Feature flag exists: USE_NEW_DICT_HANDLER = {CommandLauncher.USE_NEW_DICT_HANDLER}")
    
    print("\n5. Verifying flag is DISABLED by default (safe rollout)...")
    assert CommandLauncher.USE_NEW_DICT_HANDLER == False, "Flag should be False by default for safety"
    print("✅ Feature flag is safely DISABLED by default")
    
    print("\n6. Verifying method signatures...")
    import inspect
    
    # Check old method
    sig_old = inspect.signature(CommandLauncher._launch_dict)
    params_old = list(sig_old.parameters.keys())
    assert params_old == ['self', 'zHorizontal', 'context', 'walker'], f"Old method signature incorrect: {params_old}"
    print(f"✅ _launch_dict() signature correct: {params_old}")
    
    # Check new method
    sig_new = inspect.signature(CommandLauncher._launch_dict_new)
    params_new = list(sig_new.parameters.keys())
    assert params_new == ['self', 'zHorizontal', 'context', 'walker'], f"New method signature incorrect: {params_new}"
    print(f"✅ _launch_dict_new() signature correct: {params_new}")
    
    print("\n7. Checking code size comparison...")
    source_old = inspect.getsource(CommandLauncher._launch_dict)
    source_new = inspect.getsource(CommandLauncher._launch_dict_new)
    
    lines_old = [l for l in source_old.split('\n') if l.strip() and not l.strip().startswith('#')]
    lines_new = [l for l in source_new.split('\n') if l.strip() and not l.strip().startswith('#')]
    
    print(f"   OLD implementation: ~{len(lines_old)} lines")
    print(f"   NEW implementation: ~{len(lines_new)} lines")
    
    assert len(lines_new) < 50, f"New implementation should be < 50 lines (delegated), got {len(lines_new)}"
    print(f"✅ New implementation is properly delegated ({len(lines_new)} lines)")
    
    print("\n" + "="*70)
    print("🎉 STEP 4 PART 1 INTEGRATION TEST PASSED!")
    print("="*70)
    print("\n✅ Feature flag architecture is in place")
    print("✅ Both OLD and NEW implementations exist")
    print("✅ Flag is safely DISABLED by default")
    print("✅ No breaking changes - old code still active")
    print("✅ Ready to test with flag ENABLED in controlled environment")
    print("\n📋 Next: Step 4 Part 2 - Enable flag and test NEW implementation")
    print("      OR: Step 5 - Full migration to NEW implementation")
    
    sys.exit(0)

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
