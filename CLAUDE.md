# SQL Vibe Coding Challenge - Rust Seed

## The Challenge

Build a SQL database that passes 100% of the SQLLogicTest suite (~7.4 million tests across 622 files).

**Current Record:** 25 days ([VibeSQL baseline](https://github.com/rjwalters/vibesql))

**Your Goal:** Beat 25 days (24 days or less for the trophy)

## Rules

### The Execution Boundary (Read This First)

> **Existing database systems may be studied, benchmarked, and used for external analysis, but they must never cross the execution boundary of your submitted system.**

**Outside the boundary (allowed):**
- Study source code and algorithms (e.g., read SQLite's B-tree implementation)
- Benchmark to identify optimization targets (e.g., run DuckDB to compare JOIN performance)
- Compare query plans and behaviors (e.g., check PostgreSQL's EXPLAIN output)
- Use scripts that call SQLite to pre-compute expected test outputs (offline reference data)

**Inside the boundary (disqualified):**
- Execute queries via existing engines (even "temporarily")
- Use as fallback for unsupported features
- Use as correctness oracle during tests
- Link, embed, or invoke at runtime

**Key test:** Removing SQLite must not change whether your engine builds, runs, or passes tests.

### Other Requirements

1. **Start from this seed** - Your first commit is when you fork this repo
2. **Public repo** - Your git history is your proof
3. **100% pass rate** - All 622 SQLLogicTest files must pass

## Timing

- **Start:** Your first commit after forking
- **End:** First commit where all tests pass
- **Verification:** We'll check your git history

## Running Tests

```bash
# Build your database
cargo build --release

# Run SQLLogicTest suite
make test

# Check pass rate
make conformance
```

## SQLLogicTest Format

Tests are in `third_party/sqllogictest/test/`. Each `.test` file contains:

```
statement ok
CREATE TABLE t1(x INTEGER)

statement ok
INSERT INTO t1 VALUES(1),(2),(3)

query I rowsort
SELECT x FROM t1
----
1
2
3
```

Your database needs to:
1. Parse SQL statements
2. Execute them correctly
3. Return results matching expected output

## Suggested Approach

### Week 1: Foundation
- SQL parser (SELECT, INSERT, CREATE TABLE)
- In-memory storage
- Basic expressions and types

### Week 2: Query Engine
- WHERE clauses
- JOINs (start with INNER)
- ORDER BY, GROUP BY

### Week 3: Completeness
- Subqueries
- Aggregates (COUNT, SUM, AVG, MIN, MAX)
- NULL handling

### Week 4: Edge Cases
- Fix failing tests
- Handle SQLite-specific syntax
- Performance (some tests are large)

## Tips

1. **Start simple** - Get basic SELECT working first
2. **Run tests often** - `make test` shows progress
3. **Focus on categories** - Tests are organized by feature
4. **SQLite semantics** - SQLLogicTest expects SQLite behavior
5. **Don't optimize early** - Correctness first, speed later

## Key SQL Features to Implement

- Data types: INTEGER, REAL, TEXT, NULL
- DDL: CREATE TABLE, CREATE INDEX
- DML: SELECT, INSERT, UPDATE, DELETE
- Clauses: WHERE, ORDER BY, GROUP BY, HAVING, LIMIT
- Joins: INNER, LEFT, RIGHT, CROSS
- Subqueries: scalar, IN, EXISTS
- Expressions: arithmetic, comparison, CASE, CAST
- Aggregates: COUNT, SUM, AVG, MIN, MAX
- Functions: COALESCE, NULLIF, ABS, etc.

## Submission

When you hit 100%, open an issue at [vibesql-challenge/submissions](https://github.com/vibesql-challenge/submissions) with:
- Link to your repo
- Your time (first commit → 100% commit)
- Commit hash of your 100% milestone

Good luck!
