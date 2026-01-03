#!/usr/bin/env python3
"""
SQLLogicTest file parser.

Parses .test files into a sequence of test records that can be executed
against a database implementation.

SQLLogicTest format reference:
https://www.sqlite.org/sqllogictest/doc/trunk/about.wiki
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional
import hashlib
import re


class SortMode(Enum):
    """How to sort results before comparison."""
    NOSORT = "nosort"      # Compare results in exact order
    ROWSORT = "rowsort"    # Sort rows lexicographically
    VALUESORT = "valuesort"  # Sort all values as one list


@dataclass
class Statement:
    """A SQL statement that should succeed or fail."""
    sql: str
    expect_error: bool  # True if statement should produce an error
    line_number: int


@dataclass
class Query:
    """A SQL query with expected results."""
    sql: str
    column_types: str  # e.g., "III" for 3 integer columns
    sort_mode: SortMode
    expected_values: list[str]  # Flattened list of expected values
    label: Optional[str] = None  # Optional label for the query
    line_number: int = 0


@dataclass
class HashResult:
    """Expected hash of query results (for large result sets)."""
    num_values: int
    hash_value: str


@dataclass
class Control:
    """Control directives (halt, skip conditions)."""
    directive: str
    argument: Optional[str] = None
    line_number: int = 0


# Type alias for parsed records
Record = Statement | Query | Control


class ParseError(Exception):
    """Error parsing a SQLLogicTest file."""
    def __init__(self, message: str, file: Path, line_number: int):
        self.file = file
        self.line_number = line_number
        super().__init__(f"{file}:{line_number}: {message}")


def parse_file(path: Path, target_db: str = "sqlite") -> Iterator[Record]:
    """
    Parse a SQLLogicTest file into records.

    Args:
        path: Path to the .test file
        target_db: Database name for skipif/onlyif directives

    Yields:
        Statement, Query, or Control records
    """
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    i = 0
    skip_next = False
    hash_threshold = 0  # 0 means disabled

    while i < len(lines):
        line = lines[i].rstrip('\n\r')
        line_num = i + 1

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            i += 1
            continue

        # Handle skipif/onlyif
        if line.startswith('skipif '):
            db = line[7:].strip()
            if db == target_db:
                skip_next = True
            i += 1
            continue

        if line.startswith('onlyif '):
            db = line[7:].strip()
            if db != target_db:
                skip_next = True
            i += 1
            continue

        # Handle halt
        if line == 'halt':
            yield Control(directive='halt', line_number=line_num)
            return

        # Handle hash-threshold
        if line.startswith('hash-threshold '):
            try:
                hash_threshold = int(line[15:].strip())
            except ValueError:
                pass
            i += 1
            continue

        # Handle statement
        if line.startswith('statement '):
            if skip_next:
                skip_next = False
                # Skip to next record (past the SQL)
                i += 1
                while i < len(lines) and lines[i].strip() and not _is_directive(lines[i]):
                    i += 1
                continue

            expect_error = 'error' in line.lower()
            i += 1

            # Collect SQL lines until empty line or next directive
            sql_lines = []
            while i < len(lines):
                sql_line = lines[i].rstrip('\n\r')
                if not sql_line or _is_directive(sql_line):
                    break
                sql_lines.append(sql_line)
                i += 1

            if sql_lines:
                yield Statement(
                    sql='\n'.join(sql_lines),
                    expect_error=expect_error,
                    line_number=line_num
                )
            continue

        # Handle query
        if line.startswith('query '):
            if skip_next:
                skip_next = False
                # Skip to next record (past the SQL and results)
                i += 1
                while i < len(lines) and lines[i].strip() != '----':
                    i += 1
                i += 1  # Skip ----
                while i < len(lines) and lines[i].strip():
                    i += 1
                continue

            # Parse query header: "query <types> [sort] [label]"
            parts = line[6:].split()
            if not parts:
                i += 1
                continue

            column_types = parts[0]
            sort_mode = SortMode.NOSORT
            label = None

            for part in parts[1:]:
                if part in ('nosort', 'rowsort', 'valuesort'):
                    sort_mode = SortMode(part)
                else:
                    label = part

            i += 1

            # Collect SQL lines until ----
            sql_lines = []
            while i < len(lines) and lines[i].rstrip('\n\r') != '----':
                sql_line = lines[i].rstrip('\n\r')
                if sql_line:  # Skip blank lines in SQL
                    sql_lines.append(sql_line)
                i += 1

            if i >= len(lines):
                # Malformed: no ---- found
                i += 1
                continue

            i += 1  # Skip ----

            # Collect expected results until empty line or next directive
            expected_values = []
            while i < len(lines):
                result_line = lines[i].rstrip('\n\r')
                if not result_line or _is_directive(result_line):
                    break
                # Split by | for multi-column results, or take whole line
                if '|' in result_line:
                    expected_values.extend(result_line.split('|'))
                else:
                    expected_values.append(result_line)
                i += 1

            if sql_lines:
                yield Query(
                    sql='\n'.join(sql_lines),
                    column_types=column_types,
                    sort_mode=sort_mode,
                    expected_values=expected_values,
                    label=label,
                    line_number=line_num
                )
            continue

        # Unknown directive, skip
        i += 1


def _is_directive(line: str) -> bool:
    """Check if a line starts a new directive."""
    line = line.lstrip()
    return (
        line.startswith('statement ') or
        line.startswith('query ') or
        line.startswith('hash-threshold ') or
        line.startswith('skipif ') or
        line.startswith('onlyif ') or
        line == 'halt'
    )


def normalize_value(value: str, type_char: str) -> str:
    """
    Normalize a result value for comparison.

    Args:
        value: The value to normalize
        type_char: 'I' for integer, 'R' for real, 'T' for text

    Returns:
        Normalized string representation
    """
    value = value.strip()

    # Handle NULL
    if value.upper() == 'NULL' or value == '':
        return 'NULL'

    if type_char == 'I':
        # Integer: remove decimal part if present
        try:
            return str(int(float(value)))
        except (ValueError, OverflowError):
            return value

    elif type_char == 'R':
        # Real: normalize to consistent decimal representation
        try:
            f = float(value)
            # Handle special cases
            if f == int(f):
                return f"{int(f)}.0"
            return f"{f:.3f}".rstrip('0').rstrip('.')
        except (ValueError, OverflowError):
            return value

    else:  # 'T' or unknown
        return value


def compare_results(
    actual: list[str],
    expected: list[str],
    column_types: str,
    sort_mode: SortMode
) -> tuple[bool, str]:
    """
    Compare actual results against expected.

    Args:
        actual: List of actual values (flattened)
        expected: List of expected values (flattened)
        column_types: Column type string (e.g., "III")
        sort_mode: How to sort before comparison

    Returns:
        (passed, error_message)
    """
    # Normalize values
    num_cols = len(column_types) if column_types else 1

    def normalize_list(values: list[str]) -> list[str]:
        result = []
        for i, v in enumerate(values):
            type_char = column_types[i % num_cols] if column_types else 'T'
            result.append(normalize_value(v, type_char))
        return result

    actual_norm = normalize_list(actual)
    expected_norm = normalize_list(expected)

    # Apply sorting
    if sort_mode == SortMode.ROWSORT:
        # Sort by rows
        def chunk_into_rows(vals, ncols):
            return [tuple(vals[i:i+ncols]) for i in range(0, len(vals), ncols)]

        actual_rows = sorted(chunk_into_rows(actual_norm, num_cols))
        expected_rows = sorted(chunk_into_rows(expected_norm, num_cols))

        actual_norm = [v for row in actual_rows for v in row]
        expected_norm = [v for row in expected_rows for v in row]

    elif sort_mode == SortMode.VALUESORT:
        # Sort all values together
        actual_norm = sorted(actual_norm)
        expected_norm = sorted(expected_norm)

    # Compare
    if len(actual_norm) != len(expected_norm):
        return False, f"Row count mismatch: got {len(actual_norm)}, expected {len(expected_norm)}"

    for i, (a, e) in enumerate(zip(actual_norm, expected_norm)):
        if a != e:
            row = i // num_cols
            col = i % num_cols
            return False, f"Mismatch at row {row}, col {col}: got '{a}', expected '{e}'"

    return True, ""


def compute_hash(values: list[str]) -> str:
    """Compute MD5 hash of result values for hash-threshold comparison."""
    content = '\n'.join(values)
    return hashlib.md5(content.encode()).hexdigest()


if __name__ == '__main__':
    # Simple test
    import sys
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        for record in parse_file(path):
            print(f"{type(record).__name__}: {record}")
