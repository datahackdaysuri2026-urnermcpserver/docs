from mcp.server.fastmcp import FastMCP

import logging
from mcp.server.fastmcp.utilities.logging import get_logger


from testmcp.events.tool import EventsTool


# Server configuration
port = 8000
host = "0.0.0.0"


# Initialize FastMCP server
mcp = FastMCP("firsttest",
              host=host, 
              port=port)


def main():

    to_client_logger = get_logger(name="fastmcp.server.context.to_client")
    to_client_logger.setLevel(level=logging.INFO)
    
    uri_tools = [
        EventsTool
    ]
    
    for tool_cls in uri_tools:
        tool_cls.create(mcp)
    

    # Initialize and run the server
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()