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
    else:
        print("🧪 Running all tests...")
    
    pytest_args.append(test_dir)
    
    # Add coverage if requested
    if args.coverage:
        pytest_args.extend(["--cov=core", "--cov-report=term-missing"])
        print("📊 Coverage reporting enabled")
    
    # Add verbose flag
    if args.verbose:
        pytest_args.append("-vv")
    
    # Add specific test if provided
    if args.test:
        pytest_args.append(f"-k {args.test}")
        print(f"🎯 Running test: {args.test}")
    
    print(f"Running: pytest {' '.join(pytest_args)}\n")
    
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
    print("  zlsp test           - Run all tests")
    print("  zlsp test --unit    - Run unit tests")
    print("  zlsp test --e2e     - Run end-to-end tests")
    print("  zlsp server         - Start LSP server")
    print("  zlsp info           - Show this information")
    print("\n🔗 More info: https://github.com/ZoloAi/ZoloMedia/tree/main/zlsp")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="zlsp",
        description="Zolo Language Server Protocol - Testing and Server CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zlsp test                  # Run all tests
  zlsp test --unit           # Run only unit tests
  zlsp test --coverage       # Run with coverage report
  zlsp test -k test_parser   # Run specific test
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
    test_parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    test_parser.add_argument("-k", "--test", help="Run specific test by name")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start LSP server")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show zlsp information")
    
    args = parser.parse_args()
    
    # Route to appropriate handler
    if args.command == "test":
        sys.exit(run_tests(args))
    elif args.command == "server":
        start_server(args)
    elif args.command == "info":
        show_info(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
