#!/usr/bin/env python3
"""
SQLLogicTest runner for the SQL Vibe Coding Challenge.

Executes SQLLogicTest files against your database implementation and
reports pass/fail results.

Usage:
    python3 scripts/run_tests.py                    # Run all tests
    python3 scripts/run_tests.py -x                 # Stop on first failure
    python3 scripts/run_tests.py --file select1    # Run specific test file
    python3 scripts/run_tests.py --summary          # Show summary only
    python3 scripts/run_tests.py --verbose          # Show all SQL executed
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from slt_parser import (
    parse_file,
    Statement,
    Query,
    Control,
    SortMode,
    compare_results,
)


class DatabaseRunner:
    """Manages a database subprocess for executing SQL."""

    def __init__(self, db_path: Path, verbose: bool = False):
        self.db_path = db_path
        self.verbose = verbose
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> bool:
        """Start the database process. Returns True on success."""
        if not self.db_path.exists():
            print(f"Error: Database binary not found at {self.db_path}", file=sys.stderr)
            print("Run 'make build' first.", file=sys.stderr)
            return False

        try:
            self.process = subprocess.Popen(
                [str(self.db_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
            return True
        except Exception as e:
            print(f"Error starting database: {e}", file=sys.stderr)
            return False

    def execute(self, sql: str) -> tuple[bool, list[str], str]:
        """
        Execute SQL and return results.

        Returns:
            (success, result_rows, error_message)
            - success: True if no error occurred
            - result_rows: List of result values (flattened)
            - error_message: Error text if success is False
        """
        if not self.process or self.process.poll() is not None:
            return False, [], "Database process not running"

        if self.verbose:
            print(f"    SQL: {sql[:80]}{'...' if len(sql) > 80 else ''}")

        try:
            # Send SQL followed by a delimiter line
            # Protocol: SQL ending with semicolon, then blank line
            sql_clean = sql.strip()
            if not sql_clean.endswith(';'):
                sql_clean += ';'

            self.process.stdin.write(sql_clean + '\n')
            self.process.stdin.write('\n')  # Empty line signals end of statement
            self.process.stdin.flush()

            # Read response until we get an empty line
            results = []
            error_msg = ""

            while True:
                line = self.process.stdout.readline()
                if not line:
                    # Process died
                    stderr = self.process.stderr.read()
                    return False, [], f"Database process died: {stderr}"

                line = line.rstrip('\n\r')

                if line == '':
                    # Empty line signals end of response
                    break

                if line.startswith('Error:') or line.startswith('ERROR:'):
                    error_msg = line
                    # Continue reading until empty line
                    continue

                # Parse result row - split by tab or |
                if '\t' in line:
                    results.extend(line.split('\t'))
                elif '|' in line:
                    results.extend(line.split('|'))
                else:
                    results.append(line)

            if error_msg:
                return False, [], error_msg

            return True, results, ""

        except BrokenPipeError:
            stderr = self.process.stderr.read() if self.process else ""
            return False, [], f"Database process crashed: {stderr}"
        except Exception as e:
            return False, [], str(e)

    def stop(self):
        """Stop the database process."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            self.process = None

    def restart(self) -> bool:
        """Restart the database (fresh state for new test file)."""
        self.stop()
        return self.start()


class TestRunner:
    """Runs SQLLogicTest files and tracks results."""

    def __init__(
        self,
        db_path: Path,
        test_dir: Path,
        fail_fast: bool = False,
        verbose: bool = False,
        summary_only: bool = False,
    ):
        self.db_path = db_path
        self.test_dir = test_dir
        self.fail_fast = fail_fast
        self.verbose = verbose
        self.summary_only = summary_only

        self.files_passed = 0
        self.files_failed = 0
        self.total_statements = 0
        self.total_queries = 0
        self.failed_statements = 0
        self.failed_queries = 0

        self.first_failure: Optional[tuple[Path, int, str]] = None

    def find_test_files(self, pattern: Optional[str] = None) -> list[Path]:
        """Find test files, optionally filtered by pattern."""
        all_files = sorted(self.test_dir.rglob("*.test"))

        if pattern:
            # Filter by pattern (substring match on filename)
            all_files = [f for f in all_files if pattern in f.stem]

        return all_files

    def run_file(self, test_file: Path, db: DatabaseRunner) -> tuple[bool, str]:
        """
        Run a single test file.

        Returns:
            (passed, error_message)
        """
        rel_path = test_file.relative_to(self.test_dir)

        if not self.summary_only:
            print(f"  Testing {rel_path}...", end=" ", flush=True)

        # Restart database for fresh state
        if not db.restart():
            if not self.summary_only:
                print("SKIP (db failed to start)")
            return False, "Database failed to start"

        file_passed = True
        error_detail = ""
        statements_in_file = 0
        queries_in_file = 0

        try:
            for record in parse_file(test_file):
                if isinstance(record, Control):
                    if record.directive == 'halt':
                        break
                    continue

                if isinstance(record, Statement):
                    self.total_statements += 1
                    statements_in_file += 1

                    success, _, error = db.execute(record.sql)

                    if record.expect_error:
                        # We expected an error
                        if success:
                            file_passed = False
                            self.failed_statements += 1
                            error_detail = f"Line {record.line_number}: Expected error but got success"
                            if self.fail_fast:
                                break
                    else:
                        # We expected success
                        if not success:
                            file_passed = False
                            self.failed_statements += 1
                            error_detail = f"Line {record.line_number}: {error}"
                            if self.fail_fast:
                                break

                elif isinstance(record, Query):
                    self.total_queries += 1
                    queries_in_file += 1

                    success, results, error = db.execute(record.sql)

                    if not success:
                        file_passed = False
                        self.failed_queries += 1
                        error_detail = f"Line {record.line_number}: {error}"
                        if self.fail_fast:
                            break
                    else:
                        # Compare results
                        passed, diff = compare_results(
                            results,
                            record.expected_values,
                            record.column_types,
                            record.sort_mode,
                        )
                        if not passed:
                            file_passed = False
                            self.failed_queries += 1
                            error_detail = f"Line {record.line_number}: {diff}"
                            if self.fail_fast:
                                break

        except Exception as e:
            file_passed = False
            error_detail = f"Parse error: {e}"

        # Report result
        if not self.summary_only:
            if file_passed:
                print(f"PASS ({statements_in_file} stmt, {queries_in_file} queries)")
            else:
                print(f"FAIL")
                if error_detail:
                    print(f"        {error_detail}")

        if file_passed:
            self.files_passed += 1
        else:
            self.files_failed += 1
            if self.first_failure is None:
                line_num = 0
                if error_detail and "Line " in error_detail:
                    try:
                        line_num = int(error_detail.split("Line ")[1].split(":")[0])
                    except:
                        pass
                self.first_failure = (test_file, line_num, error_detail)

        return file_passed, error_detail

    def run(self, pattern: Optional[str] = None) -> bool:
        """
        Run all tests (or filtered by pattern).

        Returns:
            True if all tests passed
        """
        test_files = self.find_test_files(pattern)

        if not test_files:
            if pattern:
                print(f"No test files matching '{pattern}'")
            else:
                print("No test files found")
            return False

        print(f"Running {len(test_files)} test file(s)...")
        print()

        db = DatabaseRunner(self.db_path, self.verbose)

        start_time = time.time()

        for test_file in test_files:
            passed, _ = self.run_file(test_file, db)

            if not passed and self.fail_fast:
                print()
                print("Stopping on first failure (--fail-fast)")
                break

        db.stop()

        elapsed = time.time() - start_time

        # Print summary
        print()
        print("=" * 60)
        total_files = self.files_passed + self.files_failed
        pct = (self.files_passed / total_files * 100) if total_files > 0 else 0

        print(f"Files:      {self.files_passed}/{total_files} passed ({pct:.1f}%)")
        print(f"Statements: {self.total_statements - self.failed_statements}/{self.total_statements} passed")
        print(f"Queries:    {self.total_queries - self.failed_queries}/{self.total_queries} passed")
        print(f"Time:       {elapsed:.1f}s")

        if self.first_failure:
            path, line, detail = self.first_failure
            print()
            print(f"First failure: {path}:{line}")
            print(f"  {detail}")

        if pct == 100:
            print()
            print("=" * 60)
            print("  CONGRATULATIONS! You've achieved 100% conformance!")
            print("  Submit at: https://github.com/vibesql-challenge/submissions")
            print("=" * 60)
        elif pct >= 90:
            print()
            print(f"Almost there! {self.files_failed} file(s) to go.")
        elif pct >= 50:
            print(f"Good progress! Keep building.")
        elif pct > 0:
            print(f"Getting started! See CLAUDE.md for tips.")

        return self.files_failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Run SQLLogicTest suite against your database"
    )
    parser.add_argument(
        "-x", "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Run only test files matching this pattern"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show SQL being executed"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary only, not per-file results"
    )
    args = parser.parse_args()

    # Paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    db_path = repo_root / "target" / "release" / "sql-challenge"
    test_dir = repo_root / "third_party" / "sqllogictest" / "test"

    # Check prerequisites
    if not db_path.exists():
        # Try debug build
        db_path = repo_root / "target" / "debug" / "sql-challenge"
        if not db_path.exists():
            print("Error: Database binary not found.", file=sys.stderr)
            print("Run 'cargo build --release' first.", file=sys.stderr)
            sys.exit(1)

    if not test_dir.exists():
        print("Error: SQLLogicTest submodule not found.", file=sys.stderr)
        print("Run: git submodule update --init --recursive", file=sys.stderr)
        sys.exit(1)

    # Run tests
    runner = TestRunner(
        db_path=db_path,
        test_dir=test_dir,
        fail_fast=args.fail_fast,
        verbose=args.verbose,
        summary_only=args.summary,
    )

    success = runner.run(pattern=args.file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
