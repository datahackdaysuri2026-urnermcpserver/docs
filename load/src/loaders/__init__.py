"""
Loaders package - contains all data loading/scraping modules.

Each module should use the @scraper decorator to register its functions.
"""

# Import all loader modules here to register them
from . import cinemaleuzinger

__all__ = ['cinemaleuzinger']
