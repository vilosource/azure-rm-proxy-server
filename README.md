# Azure RM Proxy Server

A proxy server for efficiently accessing Azure resources with caching. This server reduces redundant Azure API calls by caching results and provides a simple interface for retrieving Azure resource information.

## Key Features

- **Efficient Azure Resource Access**: Proxy requests to Azure with smart caching to reduce API calls
- **Resource Support**: Get information about subscriptions, resource groups, and virtual machines
- **VM Details**: Include network interfaces, Effective NSG rules, routes, and AAD group access
- **Test Harnesses**: Generate test data from your Azure environment for development and testing
- **Mock Service**: Develop and test without needing real Azure connections
- **CLI Client**: Includes a command-line interface for easy access
- **Modular and Extensible Architecture**: Built with a mixin pattern for easy addition of new Azure resource types.
- **Offline Testing**: Includes a mock service to facilitate testing without requiring a live Azure connection.

## Codebase Overview

The Azure RM Proxy Server codebase is structured to provide a modular and efficient way to interact with Azure resources. Key aspects of the codebase include:

*   **Mixin-based Architecture:** The server utilizes a mixin pattern to organize and extend functionality for different Azure resource types (e.g., AAD Groups, Network, Resource Groups, Virtual Machines, Subscriptions). This promotes code modularity and reusability.
*   **Caching Implementation:** The project incorporates a caching mechanism to store responses from Azure Resource Manager, reducing the need for repeated API calls and improving performance. The following caching mechanisms are available:
    *   `NoCache`: Disables caching.
    *   `MemoryCache`: Stores cache in memory.
    *   `RedisCache`: Uses Redis as a caching store.
    The caching strategy and implementation details can be found in the `azure_rm_proxy/core/caching/` directory and the `Caching.md` file.
*   **Authentication Handling:** The server includes logic for handling authentication with Azure, likely supporting different authentication methods. Details on the authentication process can be found within the `azure_rm_proxy/core/auth.py` file.
*   **Concurrency Management:** The codebase suggests the presence of concurrency management to handle multiple requests efficiently. Look into `azure_rm_proxy/core/concurrency.py` for more details.
*   **Mock Service for Testing:** The project includes a mock service that can be used for testing purposes without making actual calls to Azure. This is indicated by the `USE_MOCK` environment variable in the Quick Start section and the test scripts in `azure_rm_proxy/tests/scripts/`.
*   **Configuration Management:** Configuration settings for the server are managed, likely through environment variables or configuration files. Refer to `azure_rm_proxy/app/config.py` for configuration details.

## Quick Start

### Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installation)
- Azure subscription and credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/azure-rm-proxy-server.git
cd azure-rm-proxy-server

# Install dependencies
poetry install
```

### Running the Server

```bash
# Using Azure credentials 
# (requires AZURE_* environment variables or az login)
poetry run start-proxy

# Or use the mock service with test harnesses
export USE_MOCK=true
poetry run start-proxy
```

### Using the CLI Client

```bash
# List subscriptions
poetry run az-proxy-cli list-subscriptions

# Get help for more commands
poetry run az-proxy-cli --help
```

### Accessing the API

Once the server is running, access:
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/ping

Example API calls:
```bash
# List subscriptions
curl http://localhost:8000/subscriptions/

# List resource groups
curl http://localhost:8000/subscriptions/{subscription_id}/resource-groups/

# Get VM details
curl http://localhost:8000/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name}
```

## Supported Resources

- **Subscriptions**: List all Azure subscriptions
- **Resource Groups**: List resource groups within a subscription
- **Virtual Machines**: List and get details of VMs, including:
  - Network details (IPs, interfaces)
  - Effective NSG rules
  - Effective routes
  - Entra ID groups allowed access

## Development

For detailed development information, see the [Development Guide](Development.md).

## Contributing

We welcome contributions! Please see the [Development Guide](Development.md) for details on how to set up your development environment and contribute to the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.







