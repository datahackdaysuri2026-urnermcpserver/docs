import abc
from typing import Self

from mcp.server.fastmcp import FastMCP


def register_as_tool():
    """Decorator to mark a method as a tool for FastMCP."""
    def decorator(func):
        func._is_tool = True  # Mark the function with a custom attribute
        return func
    return decorator

def register_as_resource(uri: str):
    """Decorator to mark a method as a resource for FastMCP."""
    def decorator(func):
        func._is_resource = True  # Mark the function with a custom attribute
        func._resource_uri = uri  # Store the URI for later registration
        return func
    return decorator




class UriMCPTool(abc.ABC):



    @classmethod
    def create(cls, mcp: FastMCP) -> Self:
        """Class method to register the tool with the MCP server."""
        instance = cls()
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if callable(attr) and hasattr(attr, "_is_tool"):
                mcp.tool()(attr)
            elif callable(attr) and hasattr(attr, "_is_resource"):
                mcp.resource(attr._resource_uri)(attr)
        return instance
