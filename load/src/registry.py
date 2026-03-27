"""
Decorator and registry for scraping functions.
"""

from typing import List, Dict, Callable, Any
from functools import wraps


# Registry to store all registered scrapers
SCRAPER_REGISTRY: List[Dict[str, Any]] = []


def scraper(name: str, schedule: str):
    """
    Decorator to register a scraping function.
    
    Args:
        name: Human-readable name for the scraper
        schedule: Cron-style schedule expression (e.g., "0 8 * * *" for daily at 8am)
    
    Example:
        @scraper(name="Cinema Leuzinger", schedule="0 8 * * *")
        def scrape_cinema():
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Register the function with metadata
        SCRAPER_REGISTRY.append({
            'name': name,
            'schedule': schedule,
            'function': func,
            'module': func.__module__,
            'qualname': func.__qualname__
        })
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Add metadata as function attributes
        wrapper.scraper_name = name
        wrapper.scraper_schedule = schedule
        
        return wrapper
    return decorator


def list_scrapers() -> List[Dict[str, Any]]:
    """List all registered scrapers."""
    return SCRAPER_REGISTRY


def run_scraper(name: str) -> Any:
    """Run a specific scraper by name."""
    for scraper_info in SCRAPER_REGISTRY:
        if scraper_info['name'] == name:
            print(f"Running scraper: {name}")
            return scraper_info['function']()
    raise ValueError(f"Scraper '{name}' not found")
