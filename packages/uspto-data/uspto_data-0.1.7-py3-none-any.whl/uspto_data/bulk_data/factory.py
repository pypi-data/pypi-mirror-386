"""
Factory Module for Bulk Data Integration

Provides factory functions to create USPatent objects with bulk data text content.
"""

from typing import Optional
from uspto_data.entities.patent import USPatent
from uspto_data.bulk_data.fetcher import USPTOBulkDataFetcher, BulkDataPatentText
from uspto_data.entities.content.patent_content import USPatentContent


def create_patent_from_bulk_data(
    patent_number: str,
    api_key: str = None,
    uspto_client: Optional[object] = None
) -> USPatent:
    """
    Create a USPatent object by fetching full text from USPTO bulk data.

    This function fetches patent text from USPTO bulk data archives,
    and creates a USPatent object. The bulk data text (abstract, description, claims)
    is stored in the patent object for easy access.

    Args:
        patent_number: Patent number (e.g., "10000000", "US10000000")
        api_key: USPTO API key (optional, for other API calls)
        uspto_client: USPTOClient instance (optional)

    Returns:
        USPatent: A USPatent object with bulk data text attached

    Example:
        >>> patent = create_patent_from_bulk_data("10000000")
        >>> # Access bulk data text
        >>> if hasattr(patent, '_bulk_data_text'):
        >>>     print(patent._bulk_data_text.abstract)
        >>>     print(patent._bulk_data_text.claims)
    """
    # Fetch bulk data
    fetcher = USPTOBulkDataFetcher()
    bulk_data = fetcher.fetch_patent_text(patent_number)

    if not bulk_data:
        raise ValueError(f"Patent {patent_number} not found in bulk data archives")

    # Create a USPatent object
    patent = USPatent(
        patent_number=bulk_data.patent_number,
        api_key=api_key,
        uspto_client=uspto_client,
        auto_load=False  # Don't auto-load from USPTO API
    )

    # Attach bulk data text to the patent object
    patent._bulk_data_text = bulk_data

    # If we have raw XML, try to create USPatentContent
    if bulk_data.raw_xml and "<us-patent-grant" in bulk_data.raw_xml:
        try:
            patent.xml_content = bulk_data.raw_xml
            patent.content = USPatentContent(bulk_data.raw_xml)
        except Exception as e:
            print(f"[!] Could not parse XML content: {e}")
            # Still attach the text data even if XML parsing fails

    return patent


def fetch_patent_text(patent_number: str) -> Optional[BulkDataPatentText]:
    """
    Convenience function to fetch patent text from bulk data.

    Args:
        patent_number: Patent number (e.g., "10000000")

    Returns:
        BulkDataPatentText object or None if not found

    Example:
        >>> text = fetch_patent_text("10000000")
        >>> print(text.abstract)
        >>> print(text.claims)
    """
    fetcher = USPTOBulkDataFetcher()
    return fetcher.fetch_patent_text(patent_number)


def add_bulk_data_to_patent(patent: USPatent) -> USPatent:
    """
    Add bulk data text to an existing USPatent object.

    This function fetches bulk data for the given patent and attaches it
    to the existing USPatent object.

    Args:
        patent: Existing USPatent object

    Returns:
        The same USPatent object with bulk data attached

    Example:
        >>> patent = USPatent("10000000")
        >>> patent = add_bulk_data_to_patent(patent)
        >>> print(patent._bulk_data_text.abstract)
    """
    bulk_data = fetch_patent_text(patent.patent_number)

    if bulk_data:
        patent._bulk_data_text = bulk_data

        # If we have raw XML, try to create USPatentContent
        if bulk_data.raw_xml and "<us-patent-grant" in bulk_data.raw_xml:
            try:
                patent.xml_content = bulk_data.raw_xml
                patent.content = USPatentContent(bulk_data.raw_xml)
            except Exception as e:
                print(f"[!] Could not parse XML content: {e}")

    return patent


if __name__ == "__main__":
    # Example usage
    patent = create_patent_from_bulk_data("10000000")

    print(f"Patent: US{patent.patent_number}")

    if hasattr(patent, '_bulk_data_text'):
        data = patent._bulk_data_text
        print(f"Source: {data.source_file} ({data.year})")
        print(f"\nAbstract:")
        print(data.abstract[:200] + "...")
        print(f"\nClaims length: {len(data.claims)} chars")
        print(f"Description length: {len(data.description)} chars")

    if patent.content:
        print(f"\nUSPatentContent available!")
        print(f"Title: {patent.content.get_title()}")
        print(f"Claims count: {len(patent.content.get_claims())}")
