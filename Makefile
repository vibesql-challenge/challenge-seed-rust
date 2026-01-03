.PHONY: build test test-fast conformance clean help

# Default target
all: build

# Build the database (release mode for speed)
build:
	cargo build --release

# Build in debug mode (faster compile, slower runtime)
build-debug:
	cargo build

# Run full SQLLogicTest suite
test: build
	@echo "Running SQLLogicTest suite..."
	@python3 scripts/run_tests.py

# Run tests, stop on first failure (recommended for development)
test-fast: build
	@echo "Running SQLLogicTest suite (fail-fast mode)..."
	@python3 scripts/run_tests.py -x

# Run a specific test file (e.g., make test-file FILE=select1)
test-file: build
	@python3 scripts/run_tests.py -x -f $(FILE)

# Show conformance summary only
conformance: build
	@echo "Checking conformance..."
	@python3 scripts/run_tests.py --summary

# Clean build artifacts
clean:
	cargo clean

# Show help
help:
	@echo "SQL Vibe Coding Challenge - Rust Seed"
	@echo ""
	@echo "Targets:"
	@echo "  build       - Build database (release mode)"
	@echo "  build-debug - Build database (debug mode, faster compile)"
	@echo "  test        - Run full SQLLogicTest suite"
	@echo "  test-fast   - Run tests, stop on first failure"
	@echo "  test-file   - Run specific test (FILE=select1)"
	@echo "  conformance - Show pass rate summary"
	@echo "  clean       - Remove build artifacts"
	@echo ""
	@echo "Quick start:"
	@echo "  make build"
	@echo "  make test-fast"
