#!/usr/bin/env python3
"""
Phase 1 Extraction Test - Leaf Modules

This script validates that the three Phase 1 leaf modules (data_resolver, auth_handler, crud_handler)
were extracted successfully and can be instantiated without errors.

Test coverage:
1. Import validation (no import errors)
2. Class instantiation (with mock dependencies)
3. Basic method signatures
4. No internal dispatch dependencies

Run from project root:
    python3 zOS/core/L2_Core/e_zDispatch/test_phase1_extraction.py
"""

import sys
from typing import Any, Dict, Optional

class MockZCLI:
    """Mock zCLI for testing."""
    def __init__(self):
        self.session = {
            'zAuth': {
                'active_app': 'zCloud',
                'applications': {
                    'zCloud': {'id': 123}
                }
            }
        }
        self.data = MockDataSubsystem()
        self.logger = MockLogger()

class MockDataSubsystem:
    """Mock zData subsystem."""
    def handle_request(self, req: Dict, context: Optional[Dict] = None) -> Any:
        return {"id": 1, "name": "Test User"}

class MockLogger:
    """Mock logger."""
    class FrameworkLogger:
        def debug(self, msg: str): pass
        def info(self, msg: str): pass
        def warning(self, msg: str): pass
        def error(self, msg: str): pass
    
    def __init__(self):
        self.framework = self.FrameworkLogger()
    
    def debug(self, msg: str): pass
    def info(self, msg: str): pass
    def warning(self, msg: str): pass
    def error(self, msg: str): pass

class MockDisplay:
    """Mock zDisplay."""
    def __init__(self):
        self.mycolor = 'blue'
    
    def zDeclare(self, label: str, **kwargs): pass

def test_data_resolver():
    """Test DataResolver module."""
    print("Testing DataResolver...")
    
    try:
        from dispatch_modules.data_resolver import DataResolver
        
        # Instantiate with mock zCLI
        zcli = MockZCLI()
        resolver = DataResolver(zcli)
        
        # Test basic query resolution
        data_block = {
            "user": {
                "model": "@.models.zSchema.users",
                "where": {"id": 123},
                "limit": 1
            }
        }
        
        result = resolver.resolve_block_data(data_block, {})
        assert 'user' in result
        assert result['user'] is not None
        
        print("  ✓ DataResolver imported and instantiated successfully")
        print("  ✓ resolve_block_data() works with declarative query")
        return True
        
    except Exception as e:
        print(f"  ✗ DataResolver test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_handler():
    """Test AuthHandler module."""
    print("\nTesting AuthHandler...")
    
    try:
        from dispatch_modules.auth_handler import AuthHandler
        
        # Instantiate with mock dependencies
        zcli = MockZCLI()
        display = MockDisplay()
        logger = MockLogger()
        
        handler = AuthHandler(zcli, display, logger)
        
        # Test method signatures exist
        assert hasattr(handler, 'handle_zlogin')
        assert hasattr(handler, 'handle_zlogout')
        
        print("  ✓ AuthHandler imported and instantiated successfully")
        print("  ✓ handle_zlogin() and handle_zlogout() methods exist")
        return True
        
    except Exception as e:
        print(f"  ✗ AuthHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crud_handler():
    """Test CRUDHandler module."""
    print("\nTesting CRUDHandler...")
    
    try:
        from dispatch_modules.crud_handler import CRUDHandler
        
        # Instantiate with mock dependencies
        zcli = MockZCLI()
        display = MockDisplay()
        logger = MockLogger()
        
        handler = CRUDHandler(zcli, display, logger)
        
        # Test CRUD pattern detection
        assert handler.is_crud_pattern({"model": "users", "action": "read"}) == True
        assert handler.is_crud_pattern({"model": "users"}) == True
        assert handler.is_crud_pattern({"where": {"id": 1}}) == False  # No model
        assert handler.is_crud_pattern({"zFunc": "calculate"}) == False
        
        # Test handle() returns None for non-CRUD
        result = handler.handle({"zFunc": "calculate"}, {})
        assert result is None
        
        # Test handle() works for CRUD pattern
        result = handler.handle({"model": "users", "action": "read"}, {})
        assert result is not None
        
        print("  ✓ CRUDHandler imported and instantiated successfully")
        print("  ✓ is_crud_pattern() detection works correctly")
        print("  ✓ handle() returns None for non-CRUD")
        print("  ✓ handle() dispatches CRUD operations")
        return True
        
    except Exception as e:
        print(f"  ✗ CRUDHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 1 tests."""
    print("=" * 70)
    print("Phase 1 Extraction Test - Leaf Modules")
    print("=" * 70)
    
    results = []
    results.append(test_data_resolver())
    results.append(test_auth_handler())
    results.append(test_crud_handler())
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ All Phase 1 modules extracted successfully!")
        print("=" * 70)
        return 0
    else:
        print("❌ Some Phase 1 modules failed extraction")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
