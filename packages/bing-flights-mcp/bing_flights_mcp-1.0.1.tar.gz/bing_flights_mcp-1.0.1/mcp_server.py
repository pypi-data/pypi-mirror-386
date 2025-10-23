"""Bing Flights MCP Server using FastMCP."""
from fastmcp import FastMCP
from bing_flights_scraper.scraper import BingFlightsScraper

mcp = FastMCP("Bing Flights")


@mcp.tool()
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    cabin_class: int = 0,
    max_results: int = 10,
    headless: bool = True
) -> dict:
    """Search for flights on Bing Flights.

    Args:
        origin: Origin airport code (e.g., "SEA")
        destination: Destination airport code (e.g., "ICN")
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (optional)
        adults: Number of adult passengers (default: 1)
        children: Number of child passengers (default: 0)
        infants: Number of infant passengers (default: 0)
        cabin_class: 0=Economy, 1=Premium Economy, 2=Business,
            3=First (default: 0)
        max_results: Maximum number of results to return (default: 10)
        headless: Run browser in headless mode (default: True)

    Returns:
        Dictionary containing flight search results with structure:
        - search_params: Search parameters used
        - results_count: Number of results returned
        - flights: List of flight options with pricing, airline, times, etc.
        - timestamp: When the search was performed
    """
    scraper = BingFlightsScraper(headless=headless)
    try:
        results = await scraper.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants=infants,
            cabin_class=cabin_class,
            max_results=max_results
        )
        return results
    finally:
        await scraper.close()


@mcp.tool()
def get_scraper_status() -> dict:
    """Check scraper health and configuration.

    Returns:
        Dictionary with scraper status information including:
        - status: Current status ("healthy")
        - version: Scraper version
        - capabilities: Supported features
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "capabilities": {
            "one_way_search": True,
            "round_trip_search": True,
            "cabin_classes": [
                "economy", "premium_economy", "business", "first"
            ],
            "max_results": 50,
            "headless_mode": True
        }
    }


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
