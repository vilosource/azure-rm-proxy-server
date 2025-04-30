# Azure RM Proxy Server OpenAPI Documentation

## Overview
This document provides an overview of the API endpoints exposed by the Azure RM Proxy Server. The API is defined using the OpenAPI 3.1.0 specification.

## General Information
- **Title**: Azure RM Proxy Server
- **Version**: 0.1.0

## Endpoints

### Subscriptions
- **GET** `/api/subscriptions/`
  - **Description**: Lists Azure subscriptions.
  - **Parameters**:
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: List of subscriptions.
    - `422`: Validation error.

### Resource Groups
- **GET** `/api/subscriptions/{subscription_id}/resource-groups/`
  - **Description**: Lists resource groups within a subscription.
  - **Parameters**:
    - `subscription_id` (path, required, string): Azure subscription ID.
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: List of resource groups.
    - `422`: Validation error.

### Virtual Machines
- **GET** `/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/`
  - **Description**: Lists virtual machines in a resource group.
  - **Parameters**:
    - `subscription_id` (path, required, string): Azure subscription ID.
    - `resource_group_name` (path, required, string): Resource group name.
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: List of virtual machines.
    - `422`: Validation error.

- **GET** `/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name}`
  - **Description**: Fetches details of a specific virtual machine.
  - **Parameters**:
    - `subscription_id` (path, required, string): Azure subscription ID.
    - `resource_group_name` (path, required, string): Resource group name.
    - `vm_name` (path, required, string): Virtual machine name.
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: Virtual machine details.
    - `422`: Validation error.

### VM Shortcuts
- **GET** `/api/subscriptions/virtual_machines/`
  - **Description**: Lists all virtual machines across all subscriptions and resource groups.
  - **Parameters**:
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: List of virtual machines.
    - `422`: Validation error.

- **GET** `/api/subscriptions/virtual_machines/{vm_name}`
  - **Description**: Finds a virtual machine by name across all subscriptions and resource groups.
  - **Parameters**:
    - `vm_name` (path, required, string): Virtual machine name.
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
    - `debug` (query, optional, boolean): Enable extra debug logging for troubleshooting.
  - **Responses**:
    - `200`: Virtual machine details.
    - `422`: Validation error.

### VM Hostnames
- **GET** `/api/subscriptions/hostnames/`
  - **Description**: Lists VM names and their hostnames.
  - **Parameters**:
    - `subscription-id` (query, optional, string): Azure subscription ID.
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: List of VM hostnames.
    - `422`: Validation error.

### VM Reports
- **GET** `/api/reports/virtual-machines`
  - **Description**: Generates a detailed report of all virtual machines.
  - **Parameters**:
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: VM report.
    - `422`: Validation error.

### Route Tables
- **GET** `/api/subscriptions/{subscription_id}/routetables`
  - **Description**: Lists route tables for a subscription.
  - **Parameters**:
    - `subscription_id` (path, required, string): Azure subscription ID.
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: List of route tables.
    - `422`: Validation error.

- **GET** `/api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/routetables/{route_table_name}`
  - **Description**: Fetches details of a specific route table.
  - **Parameters**:
    - `subscription_id` (path, required, string): Azure subscription ID.
    - `resource_group_name` (path, required, string): Resource group name.
    - `route_table_name` (path, required, string): Route table name.
    - `refresh-cache` (query, optional, boolean): Whether to bypass cache and fetch fresh data.
  - **Responses**:
    - `200`: Route table details.
    - `422`: Validation error.

### Miscellaneous
- **GET** `/`
  - **Description**: Returns project information.
  - **Responses**:
    - `200`: Project information.

- **GET** `/api/ping`
  - **Description**: Health check endpoint.
  - **Responses**:
    - `200`: Successful response.