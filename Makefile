# Azure RM Proxy Server Makefile
.PHONY: help install run run-mock run-with-redis test lint format clean fixtures harnesses docs test-mock-service test-integration test-integration-mock test-report-dir test-redis-cache

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
	@echo "  make test-mock        Run tests using mock service"
	@echo "  make test-mock-service Run mock service test script"
	@echo "  make test-integration  Run integration tests with real Azure"
	@echo "  make test-integration-mock Run integration tests with mock service"
	@echo "  make lint             Run linters (flake8, mypy)"
	@echo "  make format           Format code with Black"
	@echo "  make clean            Remove build artifacts and cache files"
	@echo "  make fixtures         Generate test fixtures"
	@echo "  make harnesses        Generate test harnesses"
	@echo "  make docs             Build documentation"
	@echo "  make test-redis-cache Test Redis cache functionality"
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
	poetry run pytest

# Run tests with mock data
test-mock:
	USE_MOCK=true poetry run pytest

# Run mock service test
test-mock-service:
	poetry run python -m azure_rm_proxy.tests.scripts.test_mock_service

# Run integration tests with real Azure
test-integration: test-report-dir
	poetry run python -m azure_rm_proxy.tests.scripts.integration_test

# Run integration tests with mock service
test-integration-mock: test-report-dir
	poetry run python -m azure_rm_proxy.tests.scripts.integration_test --mock

# Test Redis cache functionality
test-redis-cache:
	./tools/test_redis_cache.py

# Run linters
lint:
	poetry run flake8 azure_rm_proxy
	poetry run mypy azure_rm_proxy

# Format code
format:
	poetry run black azure_rm_proxy

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

# Test reports directory
test-report-dir:
	mkdir -p ./test_reports