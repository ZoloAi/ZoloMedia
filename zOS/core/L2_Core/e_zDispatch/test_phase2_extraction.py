#!/usr/bin/env python3
"""
Phase 2 Extraction Test - Navigation & Subsystem Routing

This script validates that the Phase 2 modules (navigation_handler, subsystem_router)
were extracted successfully and can be instantiated without errors.

Test coverage:
1. Import validation (no import errors)
2. Class instantiation (with mock dependencies)
3. Basic method signatures
4. Integration with Phase 1 modules (AuthHandler)

Run from project root:
    python3 zOS/core/L2_Core/e_zDispatch/test_phase2_extraction.py
"""

import sys
from typing import Any, Dict, Optional

class MockZCLI:
    """Mock zCLI for testing."""
    def __init__(self):
        self.session = {'zMode': 'Terminal'}
        self.navigation = MockNavigation()
        self.display = MockDisplay()
        self.zfunc = MockZFunc()
        self.wizard = MockWizard()
        self.data = MockDataSubsystem()
        self.logger = MockLogger()

class MockNavigation:
    """Mock zNavigation subsystem."""
    def handle_zLink(self, cmd: Dict, walker: Any = None) -> Any:
        return "navigation_result"

class MockDisplay:
    """Mock zDisplay."""
    def __init__(self):
        self.mycolor = 'blue'
    
    def zDeclare(self, label: str, **kwargs): pass
    def handle(self, data: Dict) -> Any: return None

class MockZFunc:
    """Mock zFunc subsystem."""
    def handle(self, spec: Any, **kwargs) -> Any:
        return "function_result"

class MockWizard:
    """Mock zWizard subsystem."""
    def handle(self, wizard_obj: Dict) -> Any:
        return "wizard_result"

class MockDataSubsystem:
    """Mock zData subsystem."""
    def handle_request(self, req: Dict, context: Optional[Dict] = None) -> Any:
        return {"id": 1, "name": "Test"}

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

class MockWalker:
    """Mock walker for navigation tests."""
    def __init__(self):
        self.session = {
            'zVaFile': '@.UI.zUI.index',
            'zBlock': 'Main',
            'zCrumbs': {}
        }
        self.zSpark_obj = {'zVaFile': '@.UI.zUI.index'}
        self.loader = MockLoader()
    
    def execute_loop(self, items_dict: Dict) -> Any:
        return "executed"

class MockLoader:
    """Mock zLoader."""
    def handle(self, path: str) -> Optional[Dict]:
        # Simulate file loading
        if 'Settings' in path:
            return {'Settings_Menu': {'zH1': {'content': 'Settings'}}}
        return {'Main': {'zH1': {'content': 'Main Block'}}}

def test_navigation_handler():
    """Test NavigationHandler module."""
    print("Testing NavigationHandler...")
    
    try:
        from dispatch_modules.navigation_handler import NavigationHandler
        
        # Instantiate with mock dependencies
        zcli = MockZCLI()
        display = MockDisplay()
        logger = MockLogger()
        
        handler = NavigationHandler(zcli, display, logger)
        
        # Test method signatures exist
        assert hasattr(handler, 'handle_zlink')
        assert hasattr(handler, 'handle_zdelta')
        
        # Test zLink routing
        walker = MockWalker()
        result = handler.handle_zlink({'zLink': 'menu:users'}, walker)
        assert result == "navigation_result"
        
        # Test zDelta routing (basic)
        result = handler.handle_zdelta({'zDelta': '$Main'}, walker)
        assert result == "executed"
        
        print("  ✓ NavigationHandler imported and instantiated successfully")
        print("  ✓ handle_zlink() routes to zNavigation")
        print("  ✓ handle_zdelta() resolves target blocks")
        return True
        
    except Exception as e:
        print(f"  ✗ NavigationHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_subsystem_router():
    """Test SubsystemRouter module."""
    print("\nTesting SubsystemRouter...")
    
    try:
        from dispatch_modules.subsystem_router import SubsystemRouter
        from dispatch_modules.auth_handler import AuthHandler
        from dispatch_modules.navigation_handler import NavigationHandler
        
        # Instantiate with mock dependencies + Phase 1 handlers
        zcli = MockZCLI()
        display = MockDisplay()
        logger = MockLogger()
        
        auth_handler = AuthHandler(zcli, display, logger)
        nav_handler = NavigationHandler(zcli, display, logger)
        
        router = SubsystemRouter(zcli, display, logger, auth_handler, nav_handler)
        
        # Test method signatures exist
        assert hasattr(router, 'route_zdisplay')
        assert hasattr(router, 'route_zfunc')
        assert hasattr(router, 'route_zdialog')
        assert hasattr(router, 'route_zlink')
        assert hasattr(router, 'route_zdelta')
        assert hasattr(router, 'route_zlogin')
        assert hasattr(router, 'route_zlogout')
        assert hasattr(router, 'route_zwizard')
        assert hasattr(router, 'route_zread_string')
        assert hasattr(router, 'route_zread_dict')
        assert hasattr(router, 'route_zdata')
        
        # Test zFunc routing
        result = router.route_zfunc({'zFunc': 'calculate'}, {})
        assert result == "function_result"
        
        # Test zLink routing (delegates to NavigationHandler)
        walker = MockWalker()
        result = router.route_zlink({'zLink': 'menu:users'}, walker)
        assert result == "navigation_result"
        
        # Test zRead routing
        result = router.route_zread_string("zRead(users)", {})
        assert result is not None
        
        print("  ✓ SubsystemRouter imported and instantiated successfully")
        print("  ✓ All 11 routing methods exist")
        print("  ✓ route_zfunc() dispatches to zFunc")
        print("  ✓ route_zlink() delegates to NavigationHandler")
        print("  ✓ route_zread_string() dispatches to zData")
        return True
        
    except Exception as e:
        print(f"  ✗ SubsystemRouter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_phase1():
    """Test integration with Phase 1 modules."""
    print("\nTesting Phase 1/2 Integration...")
    
    try:
        from dispatch_modules.subsystem_router import SubsystemRouter
        from dispatch_modules.auth_handler import AuthHandler
        from dispatch_modules.navigation_handler import NavigationHandler
        from dispatch_modules.data_resolver import DataResolver
        from dispatch_modules.crud_handler import CRUDHandler
        
        # Instantiate all modules
        zcli = MockZCLI()
        display = MockDisplay()
        logger = MockLogger()
        
        # Phase 1 modules
        data_resolver = DataResolver(zcli)
        auth_handler = AuthHandler(zcli, display, logger)
        crud_handler = CRUDHandler(zcli, display, logger)
        
        # Phase 2 modules
        nav_handler = NavigationHandler(zcli, display, logger)
        router = SubsystemRouter(zcli, display, logger, auth_handler, nav_handler)
        
        # Test cross-module integration
        assert auth_handler is not None
        assert nav_handler is not None
        assert router.auth_handler == auth_handler
        assert router.nav_handler == nav_handler
        
        print("  ✓ All Phase 1 modules imported successfully")
        print("  ✓ All Phase 2 modules imported successfully")
        print("  ✓ SubsystemRouter integrates with AuthHandler")
        print("  ✓ SubsystemRouter integrates with NavigationHandler")
        return True
        
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 2 tests."""
    print("=" * 70)
    print("Phase 2 Extraction Test - Navigation & Subsystem Routing")
    print("=" * 70)
    
    results = []
    results.append(test_navigation_handler())
    results.append(test_subsystem_router())
    results.append(test_integration_with_phase1())
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ All Phase 2 modules extracted successfully!")
        print("=" * 70)
        return 0
    else:
        print("❌ Some Phase 2 modules failed extraction")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
