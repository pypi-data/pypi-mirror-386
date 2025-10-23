"""
Nexus Proto - Shared Protocol Buffer definitions for Nexus microservices
"""

__version__ = "0.4.0"
__author__ = "Keeps"
__license__ = "MIT"

import os
import sys

# Get the path to the protos directory
PROTO_DIR = os.path.join(os.path.dirname(__file__), '..', 'protos')

def get_proto_path(proto_name: str) -> str:
    """
    Get the full path to a proto file.
    
    Args:
        proto_name: Name of the proto file (e.g., 'users', 'workspaces')
    
    Returns:
        Full path to the proto file
    """
    return os.path.join(PROTO_DIR, f'{proto_name}.proto')

def get_proto_dir() -> str:
    """
    Get the path to the protos directory.
    
    Returns:
        Path to the protos directory
    """
    return PROTO_DIR

__all__ = ['get_proto_path', 'get_proto_dir', 'PROTO_DIR']

