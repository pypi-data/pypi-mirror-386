# Bing Flights MCP Server

[![PyPI version](https://badge.fury.io/py/bing-flights-mcp.svg)](https://pypi.org/project/bing-flights-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that scrapes flight information from Bing Flights using Playwright. This project provides both a standalone Python scraper module and an MCP server wrapper for integration with MCP-compatible applications.

**📦 [View on PyPI](https://pypi.org/project/bing-flights-mcp/)**

## Features

- 🔍 Search for one-way and round-trip flights
- ✈️ Support for multiple passengers (adults, children, infants)
- 💺 All cabin classes (Economy, Premium Economy, Business, First)
- 🤖 Headless or headed browser modes
- 📊 Structured JSON responses
- 🔧 Easy integration via MCP protocol

## Project Structure

```
bing-flights-mcp/
├── pyproject.toml             # Package configuration
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── bing_flights_scraper/      # Standalone scraper module
│   ├── __init__.py
│   └── scraper.py
├── mcp_server.py              # MCP server implementation
└── tests/                     # Test suite
    ├── __init__.py
    ├── test_mcp.py
    └── test_e2e.py
```

## Installation

### Quick Start (Recommended)

The easiest way to use this MCP server is with `uvx`:

```bash
uvx bing-flights-mcp
```

This will automatically install the package and its dependencies in an isolated environment.

### Installation via pip

You can also install from PyPI:

```bash
pip install bing-flights-mcp
```

After installation, install the Playwright browser:

```bash
playwright install chromium
```

### Development Installation

For development or if you want to modify the code:

1. **Clone or download this repository**

2. **Create and activate a virtual environment**

   On Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   On macOS/Linux:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**

   ```bash
   playwright install chromium
   ```

## Usage

### As an MCP Server

#### Using uvx (Recommended)

If you installed via PyPI, run:

```bash
uvx bing-flights-mcp
```

Or add to your MCP settings configuration:

```json
{
  "mcpServers": {
    "bing-flights": {
      "command": "uvx",
      "args": ["bing-flights-mcp"]
    }
  }
}
```

#### Running from Source

If you're developing or running from source:

```bash
python mcp_server.py
```

#### Available Tools

The MCP server exposes two tools:

**1. `search_flights`**

Search for flight options from Bing Flights.

**Parameters:**
- `origin` (string, required): Origin airport code (e.g., "SEA")
- `destination` (string, required): Destination airport code (e.g., "ICN")
- `departure_date` (string, required): Departure date in YYYY-MM-DD format
- `return_date` (string, optional): Return date for round-trip searches
- `adults` (integer, optional, default=1): Number of adult passengers
- `children` (integer, optional, default=0): Number of child passengers
- `infants` (integer, optional, default=0): Number of infant passengers
- `cabin_class` (integer, optional, default=0): 0=Economy, 1=Premium Economy, 2=Business, 3=First
- `max_results` (integer, optional, default=10): Maximum number of results
- `headless` (boolean, optional, default=true): Run browser in headless mode

**Example MCP Tool Call:**
```json
{
  "origin": "SEA",
  "destination": "ICN",
  "departure_date": "2025-11-30",
  "return_date": "2025-12-02",
  "adults": 1,
  "cabin_class": 0,
  "max_results": 10,
  "headless": true
}
```

**2. `get_scraper_status`**

Check scraper health and configuration.

**Example Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "capabilities": {
    "one_way_search": true,
    "round_trip_search": true,
    "cabin_classes": ["economy", "premium_economy", "business", "first"],
    "max_results": 50,
    "headless_mode": true
  }
}
```

### As a Standalone Python Module

You can also use the scraper directly in your Python code:

```python
from bing_flights_scraper import BingFlightsScraper

# Create scraper instance
scraper = BingFlightsScraper(headless=True)

try:
    # Search for flights
    results = scraper.search_flights(
        origin="SEA",
        destination="ICN",
        departure_date="2025-11-30",
        return_date="2025-12-02",
        adults=1,
        cabin_class=0,
        max_results=10
    )
    
    # Process results
    print(f"Found {results['results_count']} flights")
    for flight in results['flights']:
        print(f"Price: ${flight['price']['total']}")
        print(f"Airlines: {', '.join(flight['airlines'])}")
        print(f"Departure: {flight['outbound']['departure_time']}")
        print(f"Arrival: {flight['outbound']['arrival_time']}")
        print(f"Duration: {flight['outbound']['duration']}")
        print("---")
finally:
    scraper.close()
```

## Response Format

The scraper returns results in the following JSON structure:

```json
{
  "search_params": {
    "origin": "SEA",
    "destination": "ICN",
    "departure_date": "2025-11-30",
    "return_date": "2025-12-02",
    "trip_type": "round-trip",
    "passengers": {
      "adults": 1,
      "children": 0,
      "infants": 0
    },
    "cabin_class": "economy"
  },
  "results_count": 10,
  "flights": [
    {
      "price": {
        "total": 1200.00,
        "currency": "USD",
        "per_person": 1200.00
      },
      "airlines": ["Korean Air", "Delta"],
      "outbound": {
        "departure_time": "10:30",
        "arrival_time": "14:45",
        "duration": "13h 15m",
        "stops": 1,
        "layovers": [],
        "flight_numbers": []
      },
      "booking_link": "https://www.bing.com/...",
      "result_index": 1
    }
  ],
  "timestamp": "2025-10-23T02:19:00Z"
}
```

## Configuration Options

### Cabin Classes

- `0` - Economy
- `1` - Premium Economy
- `2` - Business
- `3` - First Class

### Browser Modes

- `headless=True` - Browser runs in the background (faster, no UI)
- `headless=False` - Browser window visible (useful for debugging)

## Troubleshooting

### Common Issues

**Issue: Playwright browser not found**
```
Solution: Run `playwright install chromium`
```

**Issue: Timeout waiting for flight results**
```
Solution: 
- Check your internet connection
- Try with headless=False to see what's happening
- Verify the airport codes are valid
- Ensure the dates are in the future
```

**Issue: No results returned**
```
Solution:
- Verify airport codes are correct (use IATA codes like "SEA", "ICN")
- Check that dates are in YYYY-MM-DD format
- Try different date ranges
- Some routes may not have available flights
```

**Issue: Import errors**
```
Solution:
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Verify Python version is 3.10 or higher
```

### Debugging

To debug scraping issues, run with `headless=False`:

```python
scraper = BingFlightsScraper(headless=False)
```

This will show the browser window so you can see what's being loaded.

## Running Tests

### Basic Tests

Run the basic unit tests that verify module imports and URL construction:

```bash
python tests/test_mcp.py
```

### End-to-End Tests

Run comprehensive end-to-end tests that perform actual flight searches:

```bash
python tests/test_e2e.py
```

**Note:** E2E tests make real web requests to Bing Flights and may take several minutes to complete. They include:

1. **Invalid Parameters Test** - Verifies error handling
2. **One-Way Search Test** - Real search from SEA to ICN
3. **Round-Trip Search Test** - Real search from LAX to JFK
4. **Multiple Passengers Test** - Search with 2 adults and 1 child

The tests use headless browser mode and future dates to ensure valid searches.

## Technical Details

### Web Scraping Approach

- Uses Playwright for browser automation
- Waits for dynamic content to load
- Extracts data from Bing Flights result cards
- Handles multiple selector patterns for robustness

### Error Handling

The scraper uses minimal error handling and allows exceptions to propagate:

- Network errors → Raises exception
- Timeout errors → Raises `PlaywrightTimeoutError`
- Invalid parameters → Raises `ValueError`
- Parsing errors → Returns partial results or empty list

This design allows the MCP client to implement appropriate retry logic and error recovery.

## Limitations

- Only returns outbound flight details (return flight info not available on Bing results page)
- Maximum results limited by what's visible on the initial page load
- No pagination support (first page results only)
- Scraping depends on Bing's page structure (may break if they change their HTML)

## Dependencies

- `fastmcp>=0.1.0` - MCP server framework
- `playwright>=1.40.0` - Browser automation
- `python-dateutil>=2.8.2` - Date parsing utilities

## Contributing

When contributing, please:

1. Test changes with both headless and headed modes
2. Verify compatibility with the MCP protocol
3. Update documentation for new features
4. Follow existing code style and patterns

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool scrapes publicly available data from Bing Flights. Please:
- Use responsibly and respect rate limits
- Review Bing's Terms of Service
- Do not use for commercial purposes without proper authorization
- Be aware that web scraping may break if the website changes

## Support

For issues, questions, or contributions, please open an issue on the project repository.