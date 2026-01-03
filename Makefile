.PHONY: build test conformance clean

# Build the database
build:
	cargo build --release

# Run SQLLogicTest suite
test: build
	@echo "Running SQLLogicTest suite..."
	@python3 scripts/run_tests.py

# Show conformance summary
conformance: build
	@echo "Checking conformance..."
	@python3 scripts/run_tests.py --summary

# Clean build artifacts
clean:
	cargo clean
