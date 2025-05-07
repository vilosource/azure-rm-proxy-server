# Azure RM Network Tool

This tool provides network analysis functionality for Azure Virtual Machines, particularly for analyzing connectivity between VMs based on their routes and network configurations.

## Features

- **VM Connectivity Analysis**: Check if there's a valid network path between two VMs based on their route tables
- **Network Graph Building**: Create a graph model of your Azure network including VMs and Virtual Network Gateways 
- **Integration with Azure RM Client**: Run VM connectivity checks directly from the Azure RM CLI

## Requirements

- Python 3.10+
- NetworkX library
- VM data from Azure RM Proxy Server

## Usage

### Command Line Interface

The tool can be used directly from the command line:

```bash
# Using the entry point
check-vm-connectivity -s source-vm -d destination-vm -f path/to/infra-data

# Or directly with Python
python -m azure_rm_network_tool.vm_connectivity -s source-vm -d destination-vm -f path/to/infra-data
```

### Azure RM Client Integration

This tool is also integrated with the Azure RM Client, allowing you to run checks using:

```bash
azure-rm-client vm-connectivity -s source-vm -d destination-vm -f path/to/infra-data
```

### Arguments

- `-s, --source-vm`: Source VM name (required)
- `-d, --destination-vm`: Destination VM name (required)
- `-f, --folder`: Path to infrastructure data folder (default: infra-data)
- `-g, --gateway-ip`: Virtual Network Gateway IP (default: 20.240.246.240)
- `-r, --routes-file`: Path to gateway routes JSON file (optional)

## How It Works

1. The tool parses VM configuration data from JSON files in the specified folder
2. It builds a directed graph where:
   - Nodes represent VMs and Virtual Network Gateways
   - Edges represent network paths based on route tables
3. Using NetworkX's path finding algorithms, it determines if a path exists between source and destination VMs
4. The tool outputs the path information, showing each hop along the route

## Example Output

When VMs are connected:

```
✅ Connectivity confirmed! Path:
Hop 1: vm-source | IPs: 10.0.0.4
Hop 2: VirtualNetworkGateway | IPs: 20.240.246.240
Hop 3: vm-destination | IPs: 172.20.5.10
```

When VMs are not connected:

```
❌ No connectivity path found between the specified VMs.
```

## Integration with Azure RM Proxy

This tool works best when used with data exported from the Azure RM Proxy Server. Use the `dump-infra-data` command to generate the necessary VM configuration data:

```bash
dump-infra-data -o path/to/infra-data
```

Then analyze connectivity using that data:

```bash
check-vm-connectivity -s source-vm -d destination-vm -f path/to/infra-data
```