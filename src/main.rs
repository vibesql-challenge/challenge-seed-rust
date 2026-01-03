//! SQL Database Challenge - Rust Starter
//!
//! This is a minimal REPL skeleton that implements the protocol expected by
//! the SQLLogicTest runner. Your job is to replace the "not implemented"
//! responses with actual SQL execution.
//!
//! Protocol:
//! - Read SQL from stdin (one statement at a time, ending with semicolon)
//! - After receiving a blank line, execute the accumulated SQL
//! - Output results as tab-separated values, one row per line
//! - Output a blank line to signal end of results
//! - For errors, output "Error: <message>" then a blank line
//!
//! See CLAUDE.md for implementation tips and suggested approach.

use std::io::{self, BufRead, Write};

fn main() {
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    let mut sql_buffer = String::new();

    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };

        // Empty line signals end of statement - time to execute
        if line.is_empty() {
            if !sql_buffer.is_empty() {
                let sql = sql_buffer.trim();
                execute_sql(sql, &mut stdout);
                sql_buffer.clear();
            }
            continue;
        }

        // Accumulate SQL
        if !sql_buffer.is_empty() {
            sql_buffer.push(' ');
        }
        sql_buffer.push_str(&line);
    }

    // Handle any remaining SQL
    if !sql_buffer.is_empty() {
        let sql = sql_buffer.trim();
        execute_sql(sql, &mut stdout);
    }
}

/// Execute a SQL statement and write results to stdout.
///
/// This is where you implement your database!
///
/// For successful queries, output:
/// - Result rows as tab-separated values
/// - One row per line
/// - Blank line to signal end
///
/// For successful statements (CREATE, INSERT, etc.):
/// - Just output a blank line
///
/// For errors:
/// - Output "Error: <message>"
/// - Then a blank line
fn execute_sql<W: Write>(sql: &str, out: &mut W) {
    // Remove trailing semicolon for parsing
    let sql = sql.trim().trim_end_matches(';').trim();

    if sql.is_empty() {
        // Empty statement - just acknowledge
        writeln!(out).unwrap();
        out.flush().unwrap();
        return;
    }

    // TODO: Implement your SQL database here!
    //
    // Suggested modules to create:
    //
    // mod parser;     // Parse SQL into AST
    // mod types;      // SQL types: Integer, Real, Text, Null
    // mod storage;    // In-memory tables
    // mod executor;   // Execute queries
    // mod functions;  // Built-in functions (ABS, COALESCE, etc.)
    //
    // Start with these milestones:
    //
    // 1. SELECT <literal>
    //    - "SELECT 1" -> outputs "1"
    //    - "SELECT 'hello'" -> outputs "hello"
    //
    // 2. CREATE TABLE, INSERT, basic SELECT
    //    - Store tables in a HashMap<String, Table>
    //    - Table = Vec<Row>, Row = Vec<Value>
    //
    // 3. WHERE clauses
    //    - Filter rows based on predicates
    //
    // 4. JOINs
    //    - Start with CROSS JOIN, then INNER JOIN
    //
    // 5. Aggregates
    //    - COUNT, SUM, AVG, MIN, MAX
    //    - GROUP BY, HAVING
    //
    // 6. Subqueries
    //    - Scalar subqueries in SELECT
    //    - IN (subquery)
    //    - EXISTS
    //
    // For now, we just return "not implemented" for everything:

    writeln!(out, "Error: not implemented - {}", first_word(sql)).unwrap();
    writeln!(out).unwrap();
    out.flush().unwrap();
}

/// Get the first word of a SQL statement (for error messages)
fn first_word(sql: &str) -> &str {
    sql.split_whitespace().next().unwrap_or("unknown")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_first_word() {
        assert_eq!(first_word("SELECT 1"), "SELECT");
        assert_eq!(first_word("CREATE TABLE t1(x INT)"), "CREATE");
        assert_eq!(first_word("  INSERT INTO t1 VALUES(1)"), "INSERT");
    }
}
