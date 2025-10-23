"""Bing Flights scraper using Playwright."""
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError
)


class BingFlightsScraper:
    """Scraper for Bing Flights search results."""

    CABIN_CLASSES = {
        0: "economy",
        1: "premium_economy",
        2: "business",
        3: "first"
    }

    def __init__(self, headless: bool = True):
        """Initialize the scraper with Playwright browser.

        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _start(self):
        """Start Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        )

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: int = 0,
        max_results: int = 10
    ) -> dict:
        """Search for flights and return results.

        Args:
            origin: Airport code (e.g., "SEA")
            destination: Airport code (e.g., "ICN")
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (None for one-way)
            adults: Number of adult passengers (default: 1)
            children: Number of child passengers (default: 0)
            infants: Number of infant passengers (default: 0)
            cabin_class: 0=Economy, 1=Premium Economy, 2=Business,
                3=First (default: 0)
            max_results: Maximum number of results to return (default: 10)

        Returns:
            Dictionary with flight results

        Raises:
            ValueError: If parameters are invalid
            PlaywrightTimeoutError: If page doesn't load within timeout
        """
        # Validate inputs
        if not origin or not destination:
            raise ValueError("Origin and destination are required")
        if not departure_date:
            raise ValueError("Departure date is required")
        if cabin_class not in self.CABIN_CLASSES:
            raise ValueError(f"Cabin class must be 0-3, got {cabin_class}")
        if adults < 1:
            raise ValueError("At least 1 adult passenger is required")
        if max_results < 1:
            raise ValueError("max_results must be at least 1")

        # Build URL
        url = self._build_url(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants=infants,
            cabin_class=cabin_class
        )

        # Ensure browser is started
        if not self.context:
            await self._start()

        # Create page and navigate
        page = await self.context.new_page()
        try:
            await page.goto(url, timeout=60000, wait_until='networkidle')
            
            # Store the URL for use in flight data
            search_url = url

            # Wait for flight results to load - Bing uses .itrCard class
            try:
                await page.wait_for_selector('.itrCard', timeout=30000)
            except PlaywrightTimeoutError:
                # If no results, still try to scrape
                await page.wait_for_timeout(5000)

            # Scrape results
            flights = await self._scrape_flight_results(
                page, max_results, search_url
            )

            # Build response
            trip_type = "round-trip" if return_date else "one-way"
            return {
                "search_params": {
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "trip_type": trip_type,
                    "passengers": {
                        "adults": adults,
                        "children": children,
                        "infants": infants
                    },
                    "cabin_class": self.CABIN_CLASSES[cabin_class]
                },
                "results_count": len(flights),
                "flights": flights,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        finally:
            await page.close()

    def _build_url(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        adults: int,
        children: int,
        infants: int,
        cabin_class: int
    ) -> str:
        """Construct Bing Flights URL from parameters.

        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD) or None
            adults: Number of adults
            children: Number of children
            infants: Number of infants
            cabin_class: Cabin class (0-3)

        Returns:
            Complete Bing Flights search URL
        """
        # Determine if round-trip
        is_roundtrip = return_date is not None
        isr = 1 if is_roundtrip else 0

        # Use return_date if provided, otherwise use departure_date
        rdate = return_date if return_date else departure_date

        params = {
            'q': f'flights from {origin}-{destination}',
            'src': origin,
            'des': destination,
            'ddate': departure_date,
            'isr': isr,
            'rdate': rdate,
            'cls': cabin_class,
            'adult': adults,
            'child': children,
            'infant': infants,
            'form': 'FLAFLI' if not is_roundtrip else 'UNKHUB',
            'entrypoint': 'UNKHUB'
        }

        base_url = 'https://www.bing.com/travel/flight-search'
        return f"{base_url}?{urlencode(params)}"

    async def _scrape_flight_results(
        self,
        page: Page,
        max_results: int,
        search_url: str
    ) -> list:
        """Extract flight data from page.

        Args:
            page: Playwright page object
            max_results: Maximum number of results to extract
            search_url: The search URL to use as booking link

        Returns:
            List of flight dictionaries
        """
        flights = []

        # Bing uses .itrCard class for flight cards
        flight_elements = await page.query_selector_all('.itrCard')

        for idx, element in enumerate(flight_elements[:max_results], start=1):
            try:
                flight_data = await self._parse_flight_card(
                    element, idx, search_url
                )
                if flight_data:
                    flights.append(flight_data)
            except Exception as e:
                # Skip flights that can't be parsed
                print(f"Error parsing flight {idx}: {e}")
                continue

        return flights

    async def _parse_flight_card(
        self,
        element,
        index: int,
        search_url: str
    ) -> Optional[dict]:
        """Parse individual flight result card.

        Args:
            element: Playwright element locator for flight card
            index: Result index (1-indexed)
            search_url: The search URL to use as booking link

        Returns:
            Dictionary with flight details or None if parsing fails
        """
        try:
            # Extract price - look for .itrPriceVal
            price_text = None
            price_elem = await element.query_selector('.itrPriceVal')
            if price_elem:
                price_text = await price_elem.inner_text()
                price_text = price_text.strip()

            # Extract airline - look for .airlinePair
            airlines = []
            airline_pair = await element.query_selector('.airlinePair')
            if airline_pair:
                airline_elem = await airline_pair.query_selector(
                    '.bt_focusText'
                )
                if airline_elem:
                    airline_text = await airline_elem.inner_text()
                    airline_text = airline_text.strip()
                    if airline_text:
                        airlines = [airline_text]

            # Extract times and duration from .durationPair
            departure_time = None
            arrival_time = None
            duration = None
            
            duration_pair = await element.query_selector('.durationPair')
            if duration_pair:
                # Get time range (e.g., "11:00 AM - 3:55 PM")
                time_elem = await duration_pair.query_selector('.bt_focusText')
                if time_elem:
                    time_text = await time_elem.inner_text()
                    time_text = time_text.strip()
                    # Parse departure and arrival times
                    if ' - ' in time_text:
                        parts = time_text.split(' - ')
                        departure_time = parts[0].strip()
                        # Remove +1D suffix if present
                        arrival_time = parts[1].replace('+1D', '').strip()
                
                # Get duration from the span (e.g., "11h 55m")
                duration_spans = await duration_pair.query_selector_all('span')
                for span in duration_spans:
                    text = await span.inner_text()
                    text = text.strip()
                    if 'h' in text and 'm' in text:
                        duration = text
                        break

            # Extract stops info from .stopsPair
            stops = 0
            stops_pair = await element.query_selector('.stopsPair')
            if stops_pair:
                stops_elem = await stops_pair.query_selector('.bt_focusText')
                if stops_elem:
                    stops_text = await stops_elem.inner_text()
                    stops_text = stops_text.strip().lower()
                    if 'non-stop' in stops_text or 'nonstop' in stops_text:
                        stops = 0
                    elif '1 stop' in stops_text:
                        stops = 1
                    elif '2 stop' in stops_text:
                        stops = 2

            # Use the search URL as the booking link
            booking_link = search_url

            # Parse price
            price_value = None
            currency = "USD"
            if price_text:
                # Extract numeric value from price text
                import re
                cleaned_price = price_text.replace(',', '')
                price_match = re.search(r'[\d,]+\.?\d*', cleaned_price)
                if price_match:
                    price_value = float(price_match.group())
                # Try to detect currency
                if '$' in price_text:
                    currency = "USD"
                elif '€' in price_text:
                    currency = "EUR"
                elif '£' in price_text:
                    currency = "GBP"

            # Build flight data
            flight_data = {
                "price": {
                    "total": price_value,
                    "currency": currency,
                    "per_person": price_value
                },
                "airlines": airlines if airlines else ["Unknown"],
                "outbound": {
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "duration": duration,
                    "stops": stops,
                    "layovers": [],
                    "flight_numbers": []
                },
                "booking_link": booking_link,
                "result_index": index
            }

            return flight_data

        except Exception as e:
            print(f"Error parsing flight card: {e}")
            return None

    async def close(self):
        """Close browser and cleanup resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()