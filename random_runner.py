#!/usr/bin/env python
"""CLI entry point for random test runner."""
import argparse
import sys

from runner import RunnerCore


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Random test runner - executes tests in random order",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s tests/                    # Run tests from directory
  %(prog)s tests/test_file.py        # Run tests from file
  %(prog)s tests/test_file.py::test_name  # Run specific test
  %(prog)s tests/ --count 5 --seed 42     # 5 runs with seed 42
  %(prog)s tests/ --stop-on-fail -v      # Stop on failure, verbose
        """
    )

    parser.add_argument(
        "test_spec",
        help="Test specification (file, class, method, or directory path)"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of test runs to execute (default: 10)"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: auto-generated)"
    )

    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Stop execution on first test failure"
    )

    parser.add_argument(
        "--report-dir",
        default="./reports",
        help="Directory to save reports (default: ./reports)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for CLI."""
    args = parse_args()

    try:
        runner = RunnerCore(
            test_spec=args.test_spec,
            count=args.count,
            seed=args.seed,
            stop_on_fail=args.stop_on_fail,
            report_dir=args.report_dir,
            verbose=args.verbose
        )

        exit_code = runner.run()
        return exit_code

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())