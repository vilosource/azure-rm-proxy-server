# Python REST Client Specification

## Overview
This specification outlines the structure and components required for a Python REST client that fetches JSON data via HTTP requests, processes it, and presents it in multiple formats. The client will be designed following SOLID principles and will leverage design patterns extensively to ensure maintainability and scalability.

## Goals
- Retrieve data from REST endpoints.
- Format data into multiple outputs (Rich tables, Markdown, MediaWiki, JSON, and plain text).
- Follow SOLID principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion.
- Utilize Command, Strategy, and Factory design patterns.

## Project Structure
```
/
├── cmd.py           # Command-line interface, command invocation
├── client.py        # REST API client, manages HTTP requests
├── worker.py        # Implements command logic, coordinates between client and formatter
├── formatter.py     # Formats data into various outputs
├── commands/
│   ├── __init__.py
│   └── base_command.py
└── formatters/
    ├── __init__.py
    ├── formatter_interface.py
    ├── rich_formatter.py
    ├── markdown_formatter.py
    ├── mediawiki_formatter.py
    ├── json_formatter.py
    └── text_formatter.py
```

## Component Details

### cmd.py (Command Pattern Invoker)
- Parses CLI arguments.
- Creates command objects.
- Executes commands.

### commands/base_command.py (Command Interface)
- Defines abstract interface for commands.
- Concrete commands inherit this and implement specific logic.

### client.py (REST API Client)
- Encapsulates HTTP request logic using the `requests` library.
- Responsible solely for fetching data from REST endpoints.

### worker.py (Business Logic Handler)
- Implements logic for each command.
- Uses `client.py` to retrieve data.
- Passes retrieved data to `formatter.py`.

### formatter.py (Formatting Handler, Strategy Pattern)
- Manages formatting strategy selection.
- Invokes the selected formatter.

### formatters/formatter_interface.py
- Defines abstract formatter interface (`format(data)` method).

### Concrete Formatters
- Each formatter implements `formatter_interface`:
  - **rich_formatter.py** (Default) - Uses Python's Rich library.
  - **markdown_formatter.py** - Outputs markdown-formatted tables.
  - **mediawiki_formatter.py** - Outputs tables in MediaWiki format.
  - **json_formatter.py** - Outputs raw JSON.
  - **text_formatter.py** - Outputs plain text.

## SOLID Principles Implementation

### Single Responsibility Principle
- Each component has exactly one reason to change.
- Separate classes/modules for fetching data, formatting output, and command execution.

### Open/Closed Principle
- Easily extensible with new formatters or commands without modifying existing code.
- Implemented via interfaces and abstract classes.

### Liskov Substitution Principle
- Formatter and command implementations can be substituted seamlessly through their interfaces.

### Interface Segregation Principle
- Specific formatter interfaces ensure components depend only on methods they use.

### Dependency Inversion Principle
- High-level modules (commands, worker) depend on abstractions (`base_command.py`, `formatter_interface.py`) rather than concrete implementations.

## Design Patterns Used
- **Command Pattern**: Encapsulates each command's execution logic.
- **Strategy Pattern**: Defines a family of formatter algorithms, interchangeable at runtime.
- **Factory Pattern**: Creates formatter instances based on user input or configuration.

## Example Flow
1. User issues a command via `cmd.py`.
2. Command pattern triggers a specific command in `worker.py`.
3. `worker.py` fetches data via `client.py`.
4. `worker.py` sends data to `formatter.py`, which selects the formatting strategy.
5. Data is formatted and output displayed to the user.

## Commands

The `azrmc` CLI provides the following commands to interact with Azure resources. All commands support the `--refresh-cache` flag (default: `False`) to bypass the cache and fetch fresh data.

### Implemented Commands
1. **`azrmc subscriptions`**
   - **Description**: List all Azure subscriptions.
   - **Parameters**:
     - `--refresh-cache`: Bypass cache and fetch fresh data (default: `False`).

### Suggested Future Commands
1. **`azrmc resource-groups`**
   - **Description**: List all resource groups for a specific subscription.
   - **Parameters**:
     - `--subscription-id`: The ID of the subscription.
     - `--refresh-cache`: Bypass cache and fetch fresh data (default: `False`).

2. **`azrmc virtual-machines`**
   - **Description**: List all virtual machines in a subscription or resource group.
   - **Parameters**:
     - `--subscription-id`: The ID of the subscription.
     - `--resource-group`: The name of the resource group (optional).
     - `--refresh-cache`: Bypass cache and fetch fresh data (default: `False`).

3. **`azrmc vm-details`**
   - **Description**: Get detailed information about a specific virtual machine.
   - **Parameters**:
     - `--subscription-id`: The ID of the subscription.
     - `--resource-group`: The name of the resource group.
     - `--vm-name`: The name of the virtual machine.
     - `--refresh-cache`: Bypass cache and fetch fresh data (default: `False`).

4. **`azrmc route-tables`**
   - **Description**: List all route tables for a subscription or resource group.
   - **Parameters**:
     - `--subscription-id`: The ID of the subscription.
     - `--resource-group`: The name of the resource group (optional).
     - `--refresh-cache`: Bypass cache and fetch fresh data (default: `False`).

5. **`azrmc vm-hostnames`**
   - **Description**: List VM names and their hostnames from tags.
   - **Parameters**:
     - `--subscription-id`: The ID of the subscription (optional).
     - `--refresh-cache`: Bypass cache and fetch fresh data (default: `False`).

6. **`azrmc vm-report`**
   - **Description**: Generate a comprehensive report of all virtual machines across subscriptions.
   - **Parameters**:
     - `--refresh-cache`: Bypass cache and fetch fresh data (default: `False`).


