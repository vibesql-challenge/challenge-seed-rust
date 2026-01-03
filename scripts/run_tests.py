#!/usr/bin/env python3
"""
SQLLogicTest runner for the SQL Vibe Coding Challenge.

Usage:
    python3 scripts/run_tests.py           # Run all tests
    python3 scripts/run_tests.py --summary # Show pass/fail summary only
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def find_test_files(test_dir: Path) -> list[Path]:
    """Find all .test files in the test directory."""
    return sorted(test_dir.rglob("*.test"))


def run_test(db_path: Path, test_file: Path) -> tuple[bool, str]:
    """Run a single test file. Returns (passed, error_message)."""
    # TODO: Implement actual test execution
    # This is a placeholder - you'll need to implement the actual
    # SQLLogicTest protocol in your database or use a test harness.
    #
    # For now, this just checks if the database binary exists.
    if not db_path.exists():
        return False, "Database binary not found. Run 'cargo build --release' first."

    # Placeholder: always fails until you implement test execution
    return False, "Test execution not yet implemented"


def main():
    parser = argparse.ArgumentParser(description="Run SQLLogicTest suite")
    parser.add_argument("--summary", action="store_true", help="Show summary only")
    args = parser.parse_args()

    # Paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    db_path = repo_root / "target" / "release" / "sql-challenge"
    test_dir = repo_root / "third_party" / "sqllogictest" / "test"

    # Check prerequisites
    if not test_dir.exists():
        print("Error: SQLLogicTest submodule not found.", file=sys.stderr)
        print("Run: git submodule update --init --recursive", file=sys.stderr)
        sys.exit(1)

    # Find tests
    test_files = find_test_files(test_dir)
    total = len(test_files)

    if total == 0:
        print("No test files found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {total} test files")
    print()

    # Run tests
    passed = 0
    failed = 0

    for test_file in test_files:
        rel_path = test_file.relative_to(test_dir)
        success, error = run_test(db_path, test_file)

        if success:
            passed += 1
            if not args.summary:
                print(f"  PASS: {rel_path}")
        else:
            failed += 1
            if not args.summary:
                print(f"  FAIL: {rel_path}")
                if error:
                    print(f"        {error}")

    # Summary
    print()
    print("=" * 60)
    pct = (passed / total * 100) if total > 0 else 0
    print(f"Results: {passed}/{total} passed ({pct:.1f}%)")

    if pct == 100:
        print()
        print("🎉 CONGRATULATIONS! You've achieved 100% conformance!")
        print("   Submit your entry at: https://github.com/vibesql-challenge/submissions")
    elif pct >= 90:
        print(f"   Almost there! {total - passed} tests to go.")
    elif pct >= 50:
        print(f"   Good progress! Keep going.")
    else:
        print(f"   Keep building! See CLAUDE.md for tips.")

    sys.exit(0 if pct == 100 else 1)


if __name__ == "__main__":
    main()
