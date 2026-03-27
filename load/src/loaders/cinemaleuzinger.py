
"""
Cinema Leuzinger Web Scraper

Scrapes movie showtimes from https://www.cinema-leuzinger.ch for the next 7 days.

HTML Structure Reference:
<div class="film-liste">
    <div class="film-element">
        <a href="...">
            <div class="film-titel">HOPPERS</div>
            <div class="film-details">Trickfilm Familienfilm Komödie | Deutsch | 104 Min. | 16:00 Uhr</div>
        </a>
    </div>
</div>
"""

from datetime import datetime, timedelta
from typing import List, Dict
import re
import sys
from pathlib import Path

# Add parent directory to path to import registry
sys.path.insert(0, str(Path(__file__).parent.parent))
from registry import scraper

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Required packages not installed. Run: pip install requests beautifulsoup4")
    raise


@scraper(name="Cinema Leuzinger", schedule="0 8 * * *")
def scrape_cinema_leuzinger(start_date: str = "2026-03-28", days: int = 7) -> List[Dict[str, str]]:
    """
    Scrape cinema showtimes for the next N days.
    
    Args:
        start_date: Starting date in format YYYY-MM-DD (default: 2026-03-28)
        days: Number of days to scrape (default: 7)
        
    Returns:
        List of dictionaries containing:
        - Datum: Date of the showing
        - Zeit: Time of the showing
        - Titel: Movie title
        - Typ: Movie type/genre
        - Sprache: Language
        - Dauer: Duration
    """
    base_url = "https://www.cinema-leuzinger.ch/"
    results = []
    
    # Parse the start date
    start = datetime.strptime(start_date, "%Y-%m-%d")
    
    for day_offset in range(days):
        current_date = start + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Build URL with date parameter
        url = f"{base_url}?date={date_str}"
        
        try:
            # Fetch the page
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all film elements
            film_liste = soup.find('div', class_='film-liste')
            if not film_liste:
                print(f"No film list found for {date_str}")
                continue
                
            film_elements = film_liste.find_all('div', class_='film-element')
            
            for element in film_elements:
                # Extract title
                titel_div = element.find('div', class_='film-titel')
                titel = titel_div.get_text(strip=True) if titel_div else ""
                
                # Extract details
                details_div = element.find('div', class_='film-details')
                if not details_div:
                    continue
                    
                details_text = details_div.get_text(strip=True)
                
                # Parse details: "Type | Language | Duration | Time"
                parts = [part.strip() for part in details_text.split('|')]
                
                typ = ""
                sprache = ""
                dauer = ""
                zeit = ""
                
                if len(parts) >= 4:
                    typ = parts[0]
                    sprache = parts[1]
                    dauer = parts[2]
                    zeit = parts[3]
                elif len(parts) == 3:
                    typ = parts[0]
                    sprache = parts[1]
                    # Last part might contain both duration and time
                    last_part = parts[2]
                    time_match = re.search(r'(\d{2}:\d{2}\s*Uhr)', last_part)
                    if time_match:
                        zeit = time_match.group(1)
                        dauer = last_part.replace(zeit, '').strip()
                    else:
                        dauer = last_part
                
                # Clean up time format
                if zeit:
                    zeit = zeit.replace('Uhr', '').strip()
                
                # Add to results
                results.append({
                    "Datum": date_str,
                    "Zeit": zeit,
                    "Titel": titel,
                    "Typ": typ,
                    "Sprache": sprache,
                    "Dauer": dauer
                })
                
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue
        except Exception as e:
            print(f"Error parsing data for {date_str}: {e}")
            continue
    
    return results


def main():
    """Main function to run the scraper."""
    print("Scraping Cinema Leuzinger for the next 7 days...")
    
    movies = scrape_cinema_leuzinger(start_date="2026-03-28", days=7)
    
    print(f"\nFound {len(movies)} movie showings:\n")
    
    for movie in movies:
        print(f"Date: {movie['Datum']}")
        print(f"Time: {movie['Zeit']}")
        print(f"Title: {movie['Titel']}")
        print(f"Type: {movie['Typ']}")
        print(f"Language: {movie['Sprache']}")
        print(f"Duration: {movie['Dauer']}")
        print("-" * 50)
    
    return movies


if __name__ == "__main__":
    main()