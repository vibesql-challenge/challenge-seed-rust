# SQL Vibe Coding Challenge - Rust Seed

[![SQLLogicTest](https://img.shields.io/badge/SQLLogicTest-0%25-red)](https://www.sqlite.org/sqllogictest/doc/trunk/about.wiki)

Build a SQL database from scratch using AI-assisted development. Pass 100% of SQLLogicTest in less than 25 days.

## Quick Start

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/YOUR_USERNAME/challenge-seed-rust.git
cd challenge-seed-rust

# Build
cargo build --release

# Run tests
make test
```

## The Challenge

| Metric | Target |
|--------|--------|
| Test Suite | SQLLogicTest (~7.4M tests) |
| Pass Rate | 100% (622/622 files) |
| Record | 25 days ([VibeSQL](https://github.com/rjwalters/vibesql)) |
| Trophy | Beat it by 5% (24 days or less) |

## Structure

```
.
├── CLAUDE.md              # AI development instructions
├── Cargo.toml             # Rust project config
├── src/
│   └── main.rs            # Your database starts here
├── third_party/
│   └── sqllogictest/      # Test suite (submodule)
└── scripts/
    └── run_tests.py       # Test runner
```

## Rules

1. **Fork this repo** - Your first commit is your start time
2. **Build from scratch** - No copying from existing databases
3. **Public history** - Git history is your proof
4. **100% tests** - All files must pass

## Resources

- [SQLLogicTest Documentation](https://www.sqlite.org/sqllogictest/doc/trunk/about.wiki)
- [VibeSQL (Baseline)](https://github.com/rjwalters/vibesql)
- [Challenge Homepage](https://vibesql.org)

## Submission

Hit 100%? Open an issue at [vibesql-challenge/submissions](https://github.com/vibesql-challenge/submissions).

## License

MIT
