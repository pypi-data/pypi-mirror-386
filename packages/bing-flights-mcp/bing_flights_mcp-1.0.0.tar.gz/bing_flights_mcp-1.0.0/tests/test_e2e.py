"""End-to-end test for Bing Flights MCP Server."""
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bing_flights_scraper import BingFlightsScraper  # noqa: E402


async def test_one_way_search():
    """Test a real one-way flight search."""
    print("\n" + "=" * 60)
    print("Test 1: One-Way Flight Search (SEA to LAX)")
    print("=" * 60)
    
    # Use a date in the future
    future_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    
    scraper = BingFlightsScraper(headless=True)
    try:
        print(f"Searching for flights on {future_date}...")
        print("This may take 30-60 seconds...\n")
        
        results = await scraper.search_flights(
            origin="SEA",
            destination="LAX",
            departure_date=future_date,
            return_date=None,
            adults=1,
            cabin_class=0,
            max_results=10
        )
        
        # Verify response structure
        assert 'search_params' in results, "Missing search_params in response"
        assert 'flights' in results, "Missing flights in response"
        assert 'results_count' in results, "Missing results_count"
        assert 'timestamp' in results, "Missing timestamp"
        
        print("✓ Search completed successfully")
        print(f"✓ Found {results['results_count']} flights")
        print(f"✓ Search params: {results['search_params']}")
        
        # Verify we actually got flight results
        if results['results_count'] == 0 or not results['flights']:
            print("\n✗ FAILED: No flights found!")
            print("This route should have available flights.")
            return False
        
        # Display all results
        print("\n--- Flight Results ---")
        for i, flight in enumerate(results['flights'], 1):
            print(f"\nFlight {i}:")
            print(f"  Price: {flight['price']}")
            print(f"  Airlines: {flight['airlines']}")
            print(f"  Departure: {flight['outbound']['departure_time']}")
            print(f"  Arrival: {flight['outbound']['arrival_time']}")
            print(f"  Duration: {flight['outbound']['duration']}")
            print(f"  Stops: {flight['outbound']['stops']}")
            if flight.get('booking_link'):
                print(f"  Booking: {flight['booking_link']}")
        
        print("\n✓ One-way search test PASSED")
        return True
        
    except AssertionError as e:
        print(f"\n✗ One-way search test FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ One-way search test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await scraper.close()


async def test_round_trip_search():
    """Test a real round-trip flight search."""
    print("\n" + "=" * 60)
    print("Test 2: Round-Trip Flight Search (LAX to SFO)")
    print("=" * 60)
    
    # Use dates in the future
    departure = (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
    return_date = (datetime.now() + timedelta(days=48)).strftime('%Y-%m-%d')
    
    scraper = BingFlightsScraper(headless=True)
    try:
        print(f"Searching for flights: {departure} to {return_date}...")
        print("This may take 30-60 seconds...\n")
        
        results = await scraper.search_flights(
            origin="LAX",
            destination="SFO",
            departure_date=departure,
            return_date=return_date,
            adults=1,
            cabin_class=0,
            max_results=10
        )
        
        # Verify response structure
        assert 'search_params' in results, "Missing search_params"
        assert results['search_params']['trip_type'] == 'round-trip', \
            "Trip type should be round-trip"
        assert results['search_params']['return_date'] == return_date, \
            "Return date mismatch"
        assert 'flights' in results, "Missing flights"
        
        print("✓ Search completed successfully")
        print(f"✓ Found {results['results_count']} flights")
        print(f"✓ Trip type: {results['search_params']['trip_type']}")
        
        # Verify we actually got flight results
        if results['results_count'] == 0 or not results['flights']:
            print("\n✗ FAILED: No flights found!")
            print("This route should have available flights.")
            return False
        
        # Display first result
        flight = results['flights'][0]
        print("\n--- Sample Flight Result ---")
        print(f"  Price: {flight['price']}")
        print(f"  Airlines: {flight['airlines']}")
        print(f"  Outbound Departure: "
              f"{flight['outbound']['departure_time']}")
        print(f"  Outbound Arrival: {flight['outbound']['arrival_time']}")
        print(f"  Duration: {flight['outbound']['duration']}")
        print(f"  Stops: {flight['outbound']['stops']}")
        
        print("\n✓ Round-trip search test PASSED")
        return True
        
    except AssertionError as e:
        print(f"\n✗ Round-trip search test FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Round-trip search test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await scraper.close()


async def test_invalid_parameters():
    """Test error handling with invalid parameters."""
    print("\n" + "=" * 60)
    print("Test 3: Invalid Parameters (Error Handling)")
    print("=" * 60)
    
    scraper = BingFlightsScraper(headless=True)
    try:
        # Test 1: Missing origin
        try:
            await scraper.search_flights(
                origin="",
                destination="JFK",
                departure_date="2025-12-01"
            )
            print("✗ Should have raised ValueError for empty origin")
            return False
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        
        # Test 2: Invalid cabin class
        try:
            await scraper.search_flights(
                origin="LAX",
                destination="JFK",
                departure_date="2025-12-01",
                cabin_class=10
            )
            print("✗ Should have raised ValueError for invalid cabin class")
            return False
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        
        # Test 3: Invalid adult count
        try:
            await scraper.search_flights(
                origin="LAX",
                destination="JFK",
                departure_date="2025-12-01",
                adults=0
            )
            print("✗ Should have raised ValueError for 0 adults")
            return False
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        
        print("\n✓ Invalid parameters test PASSED")
        return True
        
    finally:
        await scraper.close()


async def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 60)
    print("BING FLIGHTS MCP SERVER - END-TO-END TESTS")
    print("=" * 60)
    print("\nNote: These tests make real web requests and may take")
    print("several minutes to complete. Please be patient.")
    print("\nThe tests will use headless browser mode.")
    print("Tests use popular US routes that should have flights.")
    
    results = []
    
    # Run all tests
    results.append(("Invalid Parameters", await test_invalid_parameters()))
    results.append(("One-Way Search", await test_one_way_search()))
    results.append(("Round-Trip Search", await test_round_trip_search()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))