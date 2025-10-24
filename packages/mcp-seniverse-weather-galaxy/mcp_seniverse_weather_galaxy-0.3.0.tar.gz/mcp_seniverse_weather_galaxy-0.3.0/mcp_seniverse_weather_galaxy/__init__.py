from mcp_seniverse_weather_galaxy.server import mcp

def main():
    """Entry point for the weather mcp server"""
    mcp.run(transport="stdio")

if __name__ == '__main__':
    main()