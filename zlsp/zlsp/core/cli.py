"""
CLI for zlsp - Language Server and test runner.

Commands:
    zlsp test         # Run tests
    zlsp test --unit  # Run unit tests only
    zlsp server       # Start LSP server
"""

import argparse
import sys
import os


def run_tests(args):
    """Run zlsp tests using pytest."""
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed. Install with: pip install pytest")
        return 1
    
    # Build pytest arguments
    pytest_args = ["-v"]
    
    # Determine which tests to run
    test_dir = "tests"
    if args.unit:
        test_dir = "tests/unit"
        print("🧪 Running unit tests...")
    elif args.integration:
        test_dir = "tests/integration"
        print("🔗 Running integration tests...")
    elif args.e2e:
        test_dir = "tests/e2e"
        print("🎯 Running end-to-end tests...")
    elif args.quick:
        # Quick mode: unit + integration only (skip slow tests)
        pytest_args.extend(["-m", "not slow"])
        print("⚡ Running quick tests (unit + integration)...")
        print("   Skipping: e2e tests (slow)")
    else:
        # Full mode: all tests including visual
        print("🧪 Running FULL test suite...")
        print("   ├─ Unit tests")
        print("   ├─ Integration tests")
        print("   ├─ End-to-end tests")
    
    pytest_args.append(test_dir)
    
    # Add coverage if requested
    if args.coverage:
        pytest_args.extend(["--cov=core", "--cov-report=term-missing", "--cov-report=html"])
        print("📊 Coverage reporting enabled (terminal + HTML)")
    
    # Add verbose flag
    if args.verbose:
        pytest_args.append("-vv")
    
    # Add specific test if provided
    if args.test:
        pytest_args.append(f"-k")
        pytest_args.append(args.test)
        print(f"🎯 Running test: {args.test}")
    
    # Fail fast (stop on first failure)
    if args.failfast:
        pytest_args.append("-x")
        print("⚡ Fail-fast enabled (stop on first failure)")
    
    print(f"\nRunning: pytest {' '.join(pytest_args)}\n")
    
    # Run pytest
    return pytest.main(pytest_args)


def start_server(args):
    """Start the LSP server."""
    print("🚀 Starting Zolo LSP Server...")
    from core.server.lsp_server import main as server_main
    server_main()


def show_info(args):
    """Show zlsp information."""
    from core import __version__
    
    print("╔═══════════════════════════════════════╗")
    print("║   Zolo Language Server Protocol      ║")
    print("╚═══════════════════════════════════════╝")
    print(f"\n📦 Version: {__version__}")
    print(f"📁 Installation: {os.path.dirname(__file__)}")
    print("\n🎯 Features:")
    print("  • String-first philosophy")
    print("  • Semantic token highlighting")
    print("  • Real-time diagnostics")
    print("  • Code completion")
    print("  • Hover information")
    print("\n📚 Commands:")
    print("  zlsp verify            - Verify installation health")
    print("  zlsp test              - Run all tests (full suite)")
    print("  zlsp test --quick      - Run quick tests (unit + integration)")
    print("  zlsp test --unit       - Run unit tests only")
    print("  zlsp test --integration - Run integration tests (includes semantic token snapshots)")
    print("  zlsp test --e2e        - Run end-to-end tests only")
    print("  zlsp test --coverage   - Run with coverage report")
    print("  zlsp server            - Start LSP server")
    print("  zlsp info              - Show this information")
    print("\n🔗 More info: https://github.com/ZoloAi/ZoloMedia/tree/main/zlsp")


def run_health_check(args):
    """Run health check to verify zlsp installation."""
    verbose = args.verbose if hasattr(args, 'verbose') else False
    
    print("╔═══════════════════════════════════════╗")
    print("║   zlsp Health Check                  ║")
    print("╚═══════════════════════════════════════╝\n")
    
    issues = []
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Python version
    total_checks += 1
    print("📋 Checking Python version...")
    if sys.version_info >= (3, 8):
        print(f"   ✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (OK)")
        checks_passed += 1
    else:
        print(f"   ✗ Python {sys.version_info.major}.{sys.version_info.minor} (requires 3.8+)")
        issues.append("Python version too old (need 3.8+)")
    
    # Check 2: Core dependencies
    total_checks += 1
    print("\n📦 Checking dependencies...")
    try:
        import pygls
        import lsprotocol
        
        # Get versions safely
        pygls_version = getattr(pygls, '__version__', 'installed')
        lsprotocol_version = getattr(lsprotocol, '__version__', 'installed')
        
        print(f"   ✓ pygls {pygls_version} (OK)")
        print(f"   ✓ lsprotocol {lsprotocol_version} (OK)")
        checks_passed += 1
    except ImportError as e:
        print(f"   ✗ Missing dependency: {e}")
        issues.append(f"Missing dependency: {e}")
    
    # Check 3: Parser functionality
    total_checks += 1
    print("\n🔍 Testing parser...")
    try:
        from core.parser.parser import loads, dumps
        
        # Test basic parsing
        test_data = "name: Zolo\nversion(int): 1"
        result = loads(test_data)
        
        if result == {"name": "Zolo", "version": 1}:
            print("   ✓ Parser loads() working")
        else:
            print(f"   ✗ Parser returned unexpected result: {result}")
            issues.append("Parser loads() returned unexpected result")
        
        # Test dump
        dumped = dumps(result)
        if "name:" in dumped and "version" in dumped:
            print("   ✓ Parser dumps() working")
        else:
            print("   ✗ Parser dumps() failed")
            issues.append("Parser dumps() failed")
        
        checks_passed += 1
    except Exception as e:
        print(f"   ✗ Parser test failed: {e}")
        issues.append(f"Parser error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
    
    # Check 4: LSP server availability
    total_checks += 1
    print("\n🚀 Checking LSP server...")
    try:
        from core.server.lsp_server import ZoloLanguageServer
        print("   ✓ LSP server module available")
        checks_passed += 1
    except Exception as e:
        print(f"   ✗ LSP server unavailable: {e}")
        issues.append(f"LSP server error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
    
    # Check 5: Semantic tokenizer
    total_checks += 1
    print("\n🎨 Checking semantic tokenizer...")
    try:
        from core.server.semantic_tokenizer import encode_semantic_tokens
        from core.parser.parser import tokenize
        
        # Tokenize test content
        test_content = "test: value"
        parse_result = tokenize(test_content)
        
        # Test encoding the tokens
        encoded = encode_semantic_tokens(parse_result.tokens)
        
        # As long as it runs without crashing and returns something, it's working
        if encoded is not None:
            print("   ✓ Semantic tokenizer working")
            checks_passed += 1
        else:
            print("   ✗ Semantic tokenizer returned None")
            issues.append("Semantic tokenizer returned None")
    except Exception as e:
        print(f"   ✗ Semantic tokenizer failed: {e}")
        issues.append(f"Semantic tokenizer error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
    
    # Check 6: Editor integrations (optional)
    print("\n📝 Checking editor integrations...")
    editors_installed = []
    
    # Check Vim
    vim_config = os.path.expanduser("~/.vim/pack/zolo/start/zlsp")
    if os.path.exists(vim_config):
        editors_installed.append("Vim")
    
    # Check Neovim
    nvim_config = os.path.expanduser("~/.config/nvim/pack/zolo/start/zlsp")
    if os.path.exists(nvim_config):
        editors_installed.append("Neovim")
    
    # Check VSCode
    vscode_ext = os.path.expanduser("~/.vscode/extensions/zolo-lsp-1.0.0")
    if os.path.exists(vscode_ext):
        editors_installed.append("VSCode")
    
    # Check Cursor
    cursor_ext = os.path.expanduser("~/.cursor/extensions/zolo-lsp-1.0.0")
    if os.path.exists(cursor_ext):
        editors_installed.append("Cursor")
    
    if editors_installed:
        print(f"   ✓ Installed for: {', '.join(editors_installed)}")
    else:
        print("   ℹ No editor integrations detected (run zlsp-install-[editor])")
    
    # Check 7: Example files (verbose mode)
    if verbose:
        total_checks += 1
        print("\n📄 Checking example files...")
        try:
            # Try to find examples directory
            zlsp_root = os.path.dirname(os.path.dirname(__file__))
            examples_path = os.path.join(zlsp_root, 'examples')
            if os.path.exists(examples_path):
                examples = [f for f in os.listdir(examples_path) if f.endswith('.zolo')]
                print(f"   ✓ Found {len(examples)} example files")
                checks_passed += 1
            else:
                print("   ℹ Example files not found (normal for pip install)")
        except Exception as e:
            print(f"   ℹ Could not check examples: {e}")
    
    # Summary
    print("\n" + "="*42)
    print("📊 Health Check Summary")
    print("="*42)
    print(f"   Checks passed: {checks_passed}/{total_checks}")
    
    if issues:
        print(f"\n❌ Issues found ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n💡 Suggested fixes:")
        print("   • Reinstall: pip uninstall zlsp && pip install zlsp")
        print("   • Check Python version: python --version")
        print("   • Install dependencies: pip install pygls lsprotocol")
        return 1
    else:
        print("\n✅ All checks passed! zlsp is working correctly.")
        print("\n🎯 Next steps:")
        if not editors_installed:
            print("   • Install for your editor:")
            print("     - zlsp-install-vim")
            print("     - zlsp-install-vscode")
            print("     - zlsp-install-cursor")
        print("   • Try: zolo-lsp (starts LSP server)")
        print("   • Docs: https://github.com/ZoloAi/ZoloMedia/tree/main/zlsp")
        return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="zlsp",
        description="Zolo Language Server Protocol - Testing and Server CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zlsp verify                # Verify installation
  zlsp verify --verbose      # Detailed health check
  zlsp test                  # Run all tests (full suite)
  zlsp test --quick          # Quick tests (unit + integration + snapshots)
  zlsp test --unit           # Unit tests only
  zlsp test --integration    # Integration tests (includes semantic token snapshots)
  zlsp test --e2e            # End-to-end tests only
  zlsp test --coverage       # Run with coverage report
  zlsp test -k test_parser   # Run specific test
  zlsp test -x               # Stop on first failure
  zlsp server                # Start LSP server
  zlsp info                  # Show information

For more information: https://github.com/ZoloAi/ZoloMedia/tree/main/zlsp
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--unit", action="store_true", help="Run only unit tests (fast)")
    test_parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    test_parser.add_argument("--e2e", action="store_true", help="Run only end-to-end tests (slow)")
    test_parser.add_argument("--quick", action="store_true", help="Run quick tests (unit + integration, skip slow)")
    test_parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    test_parser.add_argument("-k", "--test", help="Run specific test by name")
    test_parser.add_argument("-x", "--failfast", action="store_true", help="Stop on first test failure")
    test_parser.set_defaults(func=run_tests)
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start LSP server")
    server_parser.set_defaults(func=start_server)
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show zlsp information")
    info_parser.set_defaults(func=show_info)
    
    # Health check / verify command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify zlsp installation and health"
    )
    verify_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed checks")
    verify_parser.set_defaults(func=run_health_check)
    
    args = parser.parse_args()
    
    # Route to appropriate handler
    if args.command == "test":
        sys.exit(run_tests(args))
    elif args.command == "server":
        start_server(args)
    elif args.command == "info":
        show_info(args)
    elif args.command == "verify":
        sys.exit(run_health_check(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
