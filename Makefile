# Azure RM Proxy Server Makefile
.PHONY: help install run run-mock run-with-redis test lint format format-check clean fixtures harnesses docs test-client test-core test-subscriptions-worker test-workers

# Default target executed when no arguments are given to make.
help:
	@echo "Azure RM Proxy Server - Development Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make install          Install project dependencies using Poetry"
	@echo "  make install-dev      Install project with development dependencies"
	@echo "  make install-client   Install project with client dependencies"
	@echo "  make run              Run the proxy server with real Azure connection"
	@echo "  make run-mock         Run the proxy server in mock mode"
	@echo "  make run-with-redis   Run the proxy server with Redis caching"
	@echo "  make test             Run all tests"
	@echo "  make test-core        Run only core unit tests for azure_rm_proxy"
	@echo "  make test-client      Run client tests"
	@echo "  make test-subscriptions-worker Run tests for SubscriptionsWorker"
	@echo "  make test-workers     Run all worker-related tests"
	@echo "  make lint             Run linters (flake8, mypy)"
	@echo "  make format           Format code with Black"
	@echo "  make format-check     Check code formatting with Black"
	@echo "  make clean            Remove build artifacts and cache files"
	@echo "  make fixtures         Generate test fixtures"
	@echo "  make harnesses        Generate test harnesses"
	@echo "  make docs             Build documentation"
	@echo "  make force-stop-server Forcefully stop the server process"
	@echo ""

# Install dependencies
install:
	poetry install

# Install with development dependencies
install-dev:
	poetry install --with dev

# Install with client dependencies
install-client:
	poetry install -E client

# Run the server
run:
	poetry run start-proxy

# Run with mock data
run-mock:
	USE_MOCK=true poetry run start-proxy

# Run with Redis caching
run-with-redis:
	./tools/run_with_redis.sh

# Run all tests
test:
	poetry run pytest azure_rm_client/tests azure_rm_proxy/tests/unit

# Run only core unit tests for azure_rm_proxy
test-core:
	poetry run pytest azure_rm_proxy/tests/unit/core

# Run client tests
test-client:
	poetry run pytest azure_rm_client/tests

# Run SubscriptionsWorker tests
test-subscriptions-worker:
	@echo "Running SubscriptionsWorker tests..."
	poetry run pytest azure_rm_client/tests/test_subscriptions_worker.py -vv

# Run all worker-related tests
test-workers:
	poetry run pytest azure_rm_client/tests -v

# Run linters
lint:
	poetry run flake8 azure_rm_proxy
	# Run mypy with config file
	-poetry run mypy azure_rm_proxy

# Format code
format:
	poetry run black .

# Format check only (no changes)
format-check:
	poetry run black --check .

# Clean build artifacts and cache files
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf __pycache__
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	find . -name '.coverage' -delete
	find . -name '*.egg-info' -type d -exec rm -rf {} +
	find . -name '*.egg' -type d -exec rm -rf {} +
	find . -name '.DS_Store' -delete

# Generate test fixtures
fixtures:
	poetry run python -m azure_rm_proxy.tools.generate_test_fixtures --output-dir ./test_fixtures

# Generate test harnesses
harnesses:
	poetry run python -m azure_rm_proxy.tools.generate_test_harnesses --output-dir ./test_harnesses

# Build documentation (assuming a documentation tool is installed)
docs:
	@echo "Building documentation is not yet implemented."
	@echo "See the existing markdown files in the repository root and docs/ directory."

# Forcefully stop the server process
force-stop-server:
	pkill -f start-proxy || true
	@echo "Server forcefully stopped."