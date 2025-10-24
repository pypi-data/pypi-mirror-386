"""
Factory Module

Provides factory functions to create USPatent and USPublication objects
from Google Patents data.
"""

from typing import Optional
from uspto_data.entities.patent import USPatent
from uspto_data.entities.publication import USPublication
from uspto_data.google_patents.scraper import GooglePatentsScraper
from uspto_data.google_patents.adapter import GooglePatentsAdapter
from uspto_data.google_patents.mock_client import MockUSPTOClient


def create_patent_from_google(
    patent_number: str,
    api_key: str = None,
    uspto_client: Optional[object] = None
) -> USPatent:
    """
    Create a USPatent object by scraping data from Google Patents.

    This function fetches patent data from Google Patents, converts it to
    the USPTO data model format, and returns a USPatent object that is
    compatible with the existing entity class.

    Args:
        patent_number: Patent number (e.g., "10000000", "US10000000")
        api_key: USPTO API key (optional, used for PDF downloads if needed)
        uspto_client: USPTOClient instance (optional)

    Returns:
        USPatent: A USPatent object populated with Google Patents data

    Example:
        >>> patent = create_patent_from_google("10000000")
        >>> print(patent.title())
        >>> print(patent.filing_date())
    """
    # Scrape data from Google Patents
    scraper = GooglePatentsScraper()
    google_data = scraper.fetch_patent(patent_number)

    # Use mock client if none provided and no API key
    # This prevents Google Patents from requiring a USPTO API key
    if uspto_client is None and api_key is None:
        uspto_client = MockUSPTOClient()

    # Create a USPatent object
    patent = USPatent(
        patent_number=google_data.patent_number or patent_number,
        api_key=api_key,
        uspto_client=uspto_client,
        auto_load=False  # Don't auto-load from USPTO API
    )

    # Convert Google Patents data to USPTO data model format
    patent_info = GooglePatentsAdapter.create_patent_file_wrapper_data_bag(google_data)

    # Manually set the patent_info to bypass USPTO API call
    patent.patent_info = patent_info
    patent.application_number = patent_info.applicationNumberText

    # Store the raw Google Patents data as additional metadata
    patent._google_patents_data = google_data

    return patent


def create_publication_from_google(
    publication_number: str,
    api_key: str = None,
    uspto_client: Optional[object] = None
) -> USPublication:
    """
    Create a USPublication object by scraping data from Google Patents.

    This function fetches publication data from Google Patents, converts it to
    the USPTO data model format, and returns a USPublication object that is
    compatible with the existing entity class.

    Args:
        publication_number: Publication number (e.g., "20230083854", "US20230083854A1")
        api_key: USPTO API key (optional, used for PDF downloads if needed)
        uspto_client: USPTOClient instance (optional)

    Returns:
        USPublication: A USPublication object populated with Google Patents data

    Example:
        >>> publication = create_publication_from_google("20230083854")
        >>> print(publication.title())
        >>> print(publication.filing_date())
    """
    # Scrape data from Google Patents
    scraper = GooglePatentsScraper()
    google_data = scraper.fetch_patent(publication_number)

    # Use mock client if none provided and no API key
    # This prevents Google Patents from requiring a USPTO API key
    if uspto_client is None and api_key is None:
        uspto_client = MockUSPTOClient()

    # Create a USPublication object
    publication = USPublication(
        publication_number=google_data.publication_number or publication_number,
        api_key=api_key,
        uspto_client=uspto_client,
        auto_load=False  # Don't auto-load from USPTO API
    )

    # Convert Google Patents data to USPTO data model format
    patent_info = GooglePatentsAdapter.create_patent_file_wrapper_data_bag(google_data)

    # Manually set the patent_info to bypass USPTO API call
    publication.patent_info = patent_info
    publication.application_number = patent_info.applicationNumberText

    # Store the raw Google Patents data as additional metadata
    publication._google_patents_data = google_data

    return publication


def fetch_from_google_or_uspto(
    patent_or_pub_number: str,
    api_key: str = None,
    prefer_google: bool = True
) -> Optional[object]:
    """
    Fetch patent/publication data from Google Patents or USPTO API.

    Tries Google Patents first (if prefer_google=True), falls back to USPTO API
    if that fails, or vice versa.

    Args:
        patent_or_pub_number: Patent or publication number
        api_key: USPTO API key (required for USPTO API fallback)
        prefer_google: If True, try Google Patents first; otherwise try USPTO API first

    Returns:
        USPatent or USPublication object, or None if both sources fail

    Example:
        >>> result = fetch_from_google_or_uspto("10000000", api_key="your_key")
        >>> print(result.title())
    """
    # Determine if it's a patent or publication based on number format
    is_publication = 'A' in patent_or_pub_number or len(patent_or_pub_number.replace('US', '')) > 7

    def try_google():
        """Try fetching from Google Patents."""
        try:
            if is_publication:
                return create_publication_from_google(patent_or_pub_number, api_key=api_key)
            else:
                return create_patent_from_google(patent_or_pub_number, api_key=api_key)
        except Exception as e:
            print(f"Google Patents fetch failed: {e}")
            return None

    def try_uspto():
        """Try fetching from USPTO API."""
        try:
            if is_publication:
                return USPublication(patent_or_pub_number, api_key=api_key, auto_load=True)
            else:
                return USPatent(patent_or_pub_number, api_key=api_key, auto_load=True)
        except Exception as e:
            print(f"USPTO API fetch failed: {e}")
            return None

    # Try preferred source first, then fallback
    if prefer_google:
        result = try_google()
        if result is None and api_key:
            print("Falling back to USPTO API...")
            result = try_uspto()
    else:
        result = try_uspto()
        if result is None:
            print("Falling back to Google Patents...")
            result = try_google()

    return result
