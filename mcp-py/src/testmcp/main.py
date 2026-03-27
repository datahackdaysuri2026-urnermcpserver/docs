from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("firsttest")


@mcp.tool()
async def get_forecast(place: str) -> str:
    """Get weather forecast for a location.

    Args:
        place: Name of the location
    """
    # First get the forecast grid endpoint
    
    forecast = f"""
Temperature: 10 °C
Wind: 5 km/h NW
Forecast: Clear skies
"""
        

    return f"---{forecast}"



def main():
    # Initialize and run the server
    
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()