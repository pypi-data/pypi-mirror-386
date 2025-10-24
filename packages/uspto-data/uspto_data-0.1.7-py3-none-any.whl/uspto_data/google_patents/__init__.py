"""
Google Patents Scraper

This module provides functionality to scrape patent data from Google Patents
and create USPatent/USPublication objects compatible with the existing entity classes.
"""

from uspto_data.google_patents.scraper import GooglePatentsScraper
from uspto_data.google_patents.factory import (
    create_patent_from_google,
    create_publication_from_google
)

__all__ = [
    'GooglePatentsScraper',
    'create_patent_from_google',
    'create_publication_from_google'
]
