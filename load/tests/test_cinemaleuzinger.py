"""
Test suite for Cinema Leuzinger web scraper

Run with: python -m pytest test_cinemaleuzinger.py -v
Or: python test_cinemaleuzinger.py
"""

import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Import the scraper function
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from loaders.cinemaleuzinger import scrape_cinema_leuzinger


class TestCinemaLeuzingerScraper(unittest.TestCase):
    """Test cases for the Cinema Leuzinger scraper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_html = """
        <html>
        <body>
        <div class="film-liste">
            <div class="film-element">
                <a href="https://www.cinema-leuzinger.ch/kinoprogramm/item/13799-hoppers">
                    <div class="film-titel">HOPPERS</div>
                    <div class="film-details">Trickfilm Familienfilm Komödie | Deutsch | 104 Min. | 16:00 Uhr</div>
                </a>
            </div>
            <div class="film-element">
                <a href="https://www.cinema-leuzinger.ch/kinoprogramm/item/13802-melodie">
                    <div class="film-titel">MELODIE</div>
                    <div class="film-details">Dokumentarfilm | Schweizerdeutsch | 87 Min | 18:00 Uhr</div>
                </a>
            </div>
            <div class="film-element">
                <a href="https://www.cinema-leuzinger.ch/kinoprogramm/item/13796-astronaut">
                    <div class="film-titel">DER ASTRONAUT – PROJEKT HAIL MARY</div>
                    <div class="film-details">Drama Science Fiction Thriller | Deutsch | 156 Min. | 20:00 Uhr</div>
                </a>
            </div>
        </div>
        </body>
        </html>
        """
        
        self.empty_html = """
        <html>
        <body>
        <div class="other-content">No movies today</div>
        </body>
        </html>
        """
        
        self.malformed_html = """
        <html>
        <body>
        <div class="film-liste">
            <div class="film-element">
                <a href="#">
                    <div class="film-titel">TEST MOVIE</div>
                    <!-- Missing film-details -->
                </a>
            </div>
        </div>
        </body>
        </html>
        """
    
    @patch('loaders.cinemaleuzinger.requests.get')
    def test_successful_scraping(self, mock_get):
        """Test successful scraping with valid HTML."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.sample_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        # Run scraper for 1 day
        results = scrape_cinema_leuzinger(start_date="2026-03-28", days=1)
        
        # Verify results
        self.assertEqual(len(results), 3, "Should find 3 movies")
        
        # Check first movie
        first_movie = results[0]
        self.assertEqual(first_movie['Datum'], "2026-03-28")
        self.assertEqual(first_movie['Zeit'], "16:00")
        self.assertEqual(first_movie['Titel'], "HOPPERS")
        self.assertEqual(first_movie['Typ'], "Trickfilm Familienfilm Komödie")
        self.assertEqual(first_movie['Sprache'], "Deutsch")
        self.assertEqual(first_movie['Dauer'], "104 Min.")
        
        # Check second movie
        second_movie = results[1]
        self.assertEqual(second_movie['Titel'], "MELODIE")
        self.assertEqual(second_movie['Zeit'], "18:00")
        
        # Check third movie
        third_movie = results[2]
        self.assertEqual(third_movie['Titel'], "DER ASTRONAUT – PROJEKT HAIL MARY")
        self.assertEqual(third_movie['Zeit'], "20:00")
    
    @patch('loaders.cinemaleuzinger.requests.get')
    def test_empty_film_list(self, mock_get):
        """Test handling when no film list is found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.empty_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        results = scrape_cinema_leuzinger(start_date="2026-03-28", days=1)
        
        self.assertEqual(len(results), 0, "Should return empty list when no films found")
    
    @patch('loaders.cinemaleuzinger.requests.get')
    def test_malformed_html(self, mock_get):
        """Test handling of malformed HTML."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.malformed_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        results = scrape_cinema_leuzinger(start_date="2026-03-28", days=1)
        
        # Should handle gracefully without crashing
        self.assertEqual(len(results), 0, "Should skip movies with missing details")
    
    @patch('loaders.cinemaleuzinger.requests.get')
    def test_network_error(self, mock_get):
        """Test handling of network errors."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Network error")
        
        results = scrape_cinema_leuzinger(start_date="2026-03-28", days=1)
        
        self.assertEqual(len(results), 0, "Should return empty list on network error")
    
    @patch('loaders.cinemaleuzinger.requests.get')
    def test_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response
        
        results = scrape_cinema_leuzinger(start_date="2026-03-28", days=1)
        
        self.assertEqual(len(results), 0, "Should return empty list on HTTP error")
    
    @patch('loaders.cinemaleuzinger.requests.get')
    def test_multiple_days(self, mock_get):
        """Test scraping multiple days."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.sample_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        results = scrape_cinema_leuzinger(start_date="2026-03-28", days=3)
        
        # Should make 3 requests (one per day)
        self.assertEqual(mock_get.call_count, 3)
        
        # Should get 9 movies (3 per day)
        self.assertEqual(len(results), 9)
        
        # Verify dates
        dates = [movie['Datum'] for movie in results]
        self.assertIn("2026-03-28", dates)
        self.assertIn("2026-03-29", dates)
        self.assertIn("2026-03-30", dates)
    
    @patch('loaders.cinemaleuzinger.requests.get')
    def test_url_construction(self, mock_get):
        """Test that URLs are constructed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.sample_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        scrape_cinema_leuzinger(start_date="2026-03-28", days=2)
        
        # Check the URLs that were called
        calls = mock_get.call_args_list
        self.assertEqual(calls[0][0][0], "https://www.cinema-leuzinger.ch/?date=2026-03-28")
        self.assertEqual(calls[1][0][0], "https://www.cinema-leuzinger.ch/?date=2026-03-29")
    
    def test_data_structure(self):
        """Test that returned data has the correct structure."""
        with patch('loaders.cinemaleuzinger.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = self.sample_html.encode('utf-8')
            mock_get.return_value = mock_response
            
            results = scrape_cinema_leuzinger(start_date="2026-03-28", days=1)
            
            # Check each movie has all required fields
            required_fields = ['Datum', 'Zeit', 'Titel', 'Typ', 'Sprache', 'Dauer']
            for movie in results:
                for field in required_fields:
                    self.assertIn(field, movie, f"Movie should have '{field}' field")
                    self.assertIsInstance(movie[field], str, f"'{field}' should be a string")


class TestDebugScenarios(unittest.TestCase):
    """Additional test cases for debugging specific scenarios."""
    
    @patch('loaders.cinemaleuzinger.requests.get')
    def test_varying_detail_formats(self, mock_get):
        """Test different formats in film-details."""
        html_variants = """
        <html>
        <body>
        <div class="film-liste">
            <div class="film-element">
                <a href="#">
                    <div class="film-titel">MOVIE 1</div>
                    <div class="film-details">Drama | English | 120 Min. | 14:30 Uhr</div>
                </a>
            </div>
            <div class="film-element">
                <a href="#">
                    <div class="film-titel">MOVIE 2</div>
                    <div class="film-details">Comedy Action | French | 90 Min | 16:00 Uhr</div>
                </a>
            </div>
            <div class="film-element">
                <a href="#">
                    <div class="film-titel">MOVIE 3</div>
                    <div class="film-details">Horror | Spanish</div>
                </a>
            </div>
        </div>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_variants.encode('utf-8')
        mock_get.return_value = mock_response
        
        results = scrape_cinema_leuzinger(start_date="2026-03-28", days=1)
        
        print("\n--- Debug: Varying Detail Formats ---")
        for i, movie in enumerate(results, 1):
            print(f"\nMovie {i}:")
            print(f"  Title: {movie['Titel']}")
            print(f"  Type: {movie['Typ']}")
            print(f"  Language: {movie['Sprache']}")
            print(f"  Duration: {movie['Dauer']}")
            print(f"  Time: {movie['Zeit']}")


class TestScraperAnnotations(unittest.TestCase):
    """Test cases for verifying scraper decorator annotations."""
    
    def test_scraper_has_name_attribute(self):
        """Test that the scraper function has a name attribute."""
        self.assertTrue(hasattr(scrape_cinema_leuzinger, 'scraper_name'))
        self.assertEqual(scrape_cinema_leuzinger.scraper_name, "Cinema Leuzinger")
    
    def test_scraper_has_schedule_attribute(self):
        """Test that the scraper function has a schedule attribute."""
        self.assertTrue(hasattr(scrape_cinema_leuzinger, 'scraper_schedule'))
        self.assertEqual(scrape_cinema_leuzinger.scraper_schedule, "0 8 * * *")
    
    def test_scraper_is_registered(self):
        """Test that the scraper is registered in the global registry."""
        from registry import list_scrapers
        
        scrapers = list_scrapers()
        self.assertGreater(len(scrapers), 0, "Registry should have at least one scraper")
        
        # Find our scraper
        cinema_scraper = next(
            (s for s in scrapers if s['name'] == "Cinema Leuzinger"),
            None
        )
        
        self.assertIsNotNone(cinema_scraper, "Cinema Leuzinger should be in registry")
        self.assertEqual(cinema_scraper['schedule'], "0 8 * * *")
        self.assertEqual(cinema_scraper['qualname'], "scrape_cinema_leuzinger")


def run_manual_test():
    """Run a manual test against the live website."""
    print("=" * 60)
    print("MANUAL TEST - Live Website Scraping")
    print("=" * 60)
    
    try:
        print("\nFetching data from https://www.cinema-leuzinger.ch...")
        results = scrape_cinema_leuzinger(start_date="2026-03-28", days=7)
        
        print(f"\nTotal movies found: {len(results)}")
        
        if results:
            print("\n--- Sample Results ---")
            for i, movie in enumerate(results[:5], 1):  # Show first 5
                print(f"\n{i}. {movie['Titel']}")
                print(f"   Date: {movie['Datum']}")
                print(f"   Time: {movie['Zeit']}")
                print(f"   Type: {movie['Typ']}")
                print(f"   Language: {movie['Sprache']}")
                print(f"   Duration: {movie['Dauer']}")
            
            if len(results) > 5:
                print(f"\n... and {len(results) - 5} more movies")
        else:
            print("\nNo movies found!")
        
        # Data validation
        print("\n--- Data Validation ---")
        issues = []
        for i, movie in enumerate(results):
            if not movie['Titel']:
                issues.append(f"Movie {i+1}: Missing title")
            if not movie['Zeit']:
                issues.append(f"Movie {i+1} ({movie['Titel']}): Missing time")
            if not movie['Typ']:
                issues.append(f"Movie {i+1} ({movie['Titel']}): Missing type")
        
        if issues:
            print("⚠️  Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ All movies have complete data")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during manual test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        # Run live test
        run_manual_test()
    else:
        # Run unit tests
        print("Running unit tests...")
        print("Use '--live' flag to test against the actual website\n")
        unittest.main(verbosity=2)
