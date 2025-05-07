"""
Azure Network Tool for analyzing connectivity between VMs.

This tool provides utilities for analyzing Azure network configurations,
particularly VM connectivity based on route information.
"""

__version__ = "0.1.0"

from .vm_connectivity import (
    parse_vm_data,
    build_graph,
    check_connectivity
)