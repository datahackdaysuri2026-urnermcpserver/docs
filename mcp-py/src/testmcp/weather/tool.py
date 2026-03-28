from mcp.server.fastmcp import FastMCP

from testmcp.base import UriMCPTool, register_as_tool


class WeatherTool(UriMCPTool):

    @register_as_tool()
    async def get_forecast(self, place: str) -> str:
        """Get weather forecast for a location.

        Args:
            place: Name of the location 
        """
        # First get the forecast grid endpoint
        
        forecast = f"""
    Place: {place}
    Temperature: 10 °C
    Wind: 5 km/h NW
    Forecast: Clear skies
    """
            

        return f"---{forecast}"