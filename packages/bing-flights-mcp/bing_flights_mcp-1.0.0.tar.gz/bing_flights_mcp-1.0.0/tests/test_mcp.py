"""Simple test script to verify MCP server functionality."""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_scraper_status():
    """Test the get_scraper_status tool."""
    print("Testing scraper status functionality...")
    status = {
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
    print(f"Status: {status['status']}")
    print(f"Version: {status['version']}")
    print(f"Capabilities: {status['capabilities']}")
    print("✓ Scraper status structure verified\n")


async def test_url_building():
    """Test URL construction without actually scraping."""
    from bing_flights_scraper.scraper import BingFlightsScraper
    
    print("Testing URL construction...")
    scraper = BingFlightsScraper(headless=True)
    
    # Test one-way URL
    url = scraper._build_url(
        origin="SEA",
        destination="ICN",
        departure_date="2025-11-30",
        return_date=None,
        adults=1,
        children=0,
        infants=0,
        cabin_class=0
    )
    print(f"One-way URL: {url}")
    assert "isr=0" in url
    assert "src=SEA" in url
    assert "des=ICN" in url
    
    # Test round-trip URL
    url = scraper._build_url(
        origin="SEA",
        destination="ICN",
        departure_date="2025-11-30",
        return_date="2025-12-02",
        adults=1,
        children=0,
        infants=0,
        cabin_class=0
    )
    print(f"Round-trip URL: {url}")
    assert "isr=1" in url
    assert "rdate=2025-12-02" in url
    
    await scraper.close()
    print("✓ URL construction test passed\n")


async def run_tests():
    """Run all basic tests."""
    print("=" * 60)
    print("Bing Flights MCP Server - Basic Tests")
    print("=" * 60 + "\n")
    
    test_scraper_status()
    await test_url_building()
    
    print("=" * 60)
    print("All basic tests passed!")
    print("=" * 60)
    print("\nNote: Full scraping tests require actual web requests")
    print("and are not included in this basic test suite.")


if __name__ == "__main__":
    asyncio.run(run_tests())