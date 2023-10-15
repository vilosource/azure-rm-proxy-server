# Azure RM Proxy Server - Development Guide

This guide explains how to set up and run the Azure RM Proxy Server in development mode, and provides guidelines for contributing to the project.

## Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installation)
- Azure subscription and credentials (Service Principal or Azure CLI login)
- Azure CLI (optional, for test harness generation)

## Setup

1.  **Clone the repository**

    ```bash
    git clone <repository_url>
    cd azure-rm-proxy-server
    ```

2.  **Install dependencies with Poetry**

    This will create a virtual environment and install all the required dependencies.

    ```bash
    poetry install
    ```

    To install the client dependencies as well:

    ```bash
    poetry install -E client
    ```

    For development dependencies (testing):

    ```bash
    poetry install --with dev
    ```

## Authentication Configuration

The Azure RM Proxy Server uses the `DefaultAzureCredential` from Azure Identity library, which attempts to authenticate using multiple methods in the following order:

1.  **Environment variables (Service Principal)**

    Set the following environment variables for Service Principal authentication:

    ```bash
    export AZURE_CLIENT_ID=<your-client-id>
    export AZURE_CLIENT_SECRET=<your-client-secret>
    export AZURE_TENANT_ID=<your-tenant-id>
    ```

2.  **Azure CLI** (fallback)

    If environment variables are not set, the proxy will attempt to use Azure CLI credentials. Ensure you're logged in:

    ```bash
    az login
    ```

## Running the Server

### Using Poetry

The easiest way to run the server in development mode is using the Poetry script:

```bash
poetry run start-proxy
```

This will:

*   Start the FastAPI application with Uvicorn
*   Enable auto-reload for development
*   Bind to all interfaces on port 8000

### Manual Run

Alternatively, you can run the server directly:

```bash
uvicorn azure_rm_proxy.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration Options

Configuration can be managed through environment variables:

*   `LOG_LEVEL`: Set the logging level (default: INFO)
*   `MAX_CONCURRENCY`: Maximum number of concurrent Azure API calls (default: 5)
*   `USE_MOCK`: Use the mock Azure service instead of connecting to real Azure (default: false)
*   `MOCK_FIXTURES_DIR`: Directory containing test harnesses (default: `./test_harnesses`)

For example:

```bash
export LOG_LEVEL=DEBUG
export MAX_CONCURRENCY=10
poetry run start-proxy
```

## Test Harnesses and Mock Service

The project includes a mock Azure service that can be used for development and testing without needing to connect to real Azure resources.

### Generating Test Harnesses

To generate test harnesses for use with the mock service, you need to use the provided script and have the Azure CLI installed and authenticated:

```bash
poetry run generate-test-harnesses
```

The test harnesses will be stored in the specified directory (default: `./test_harnesses`) and are automatically excluded from git through the `.gitignore` file.

### Using the Mock Service

To use the mock service instead of connecting to Azure:

1.  Generate test harnesses as described above.
2.  Set the environment variable `USE_MOCK=true`.
3.  Optionally, set `MOCK_FIXTURES_DIR` to specify a custom test harnesses directory.

```bash
export USE_MOCK=true
poetry run start-proxy
```

This will use the test harnesses to simulate Azure resources, allowing for offline development and testing.

### Testing the Mock Service

To verify that the mock service works correctly with your test harnesses, you can run the tests with the `USE_MOCK` environment variable set:

```bash
export USE_MOCK=true
poetry run pytest
```

## Using the CLI Client

The project includes a command-line client for interacting with the API:

```bash
poetry run azure-rm-proxy-client --help
```

For more client commands:

```bash
poetry run azure-rm-proxy-client <command> --help
```

## Testing the API

Once the server is running, you can access:

*   API documentation: `http://localhost:8000/docs`
*   OpenAPI specification: `http://localhost:8000/openapi.json`
*   API health check: `http://localhost:8000/ping`

Example API calls using `curl`:

```bash
curl http://localhost:8000/subscriptions
curl http://localhost:8000/resource_groups?subscription_id=<your-subscription-id>
```

## Development Guidelines

1.  **Code Structure**

    *   API endpoint definitions in `azure_rm_proxy/api/`
    *   Business logic in `azure_rm_proxy/core/`
    *   Application configuration in `azure_rm_proxy/app/`
    *   Mock implementations in `azure_rm_proxy/tools/`
    *   Test harnesses stored in `./test_harnesses/`

2.  **Adding New Endpoints**

    When adding a new API endpoint for a specific Azure resource type:

    *   Create a new router file in `azure_rm_proxy/api/` to define the endpoint(s).
    *   Include the new router in `azure_rm_proxy/app/main.py`.
    *   Add corresponding methods to the relevant mixin class in `azure_rm_proxy/core/mixins/`.
    *   If necessary, update the `AzureResourceService` in `azure_rm_proxy/core/azure_service.py` to orchestrate calls to the new mixin methods.
    *   Update the mock service in `azure_rm_proxy/tools/mock_azure_service.py` to simulate the new endpoint and resource type.
    *   Generate new test harnesses that include data for the new resource type.

3.  **Testing**

    *   Tests are located in the `azure_rm_proxy/tests/` directory.
    *   Run all tests with `poetry run pytest`.
    *   Use the mock service for faster and offline testing by setting `USE_MOCK=true`.
    *   Write new tests for any new functionality or endpoints you add.

4.  **Code Style and Linting**

    *   The project likely follows a specific code style (e.g., Black, Flake8). Ensure your code adheres to it.
    *   Run linters and formatters before submitting changes.

5.  **Committing Changes**

    *   Write clear and concise commit messages.
    *   Ensure your changes are atomic and address a single concern.

## Contributing

We welcome contributions to the Azure RM Proxy Server! Please follow these steps to contribute:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Implement your changes, following the development guidelines.
4.  Write tests for your changes.
5.  Run all tests and linters to ensure everything passes.
6.  Submit a pull request with a clear description of your changes.

Thank you for contributing!