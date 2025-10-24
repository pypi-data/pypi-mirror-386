"""
USPTO Data Package

Provides clients for accessing USPTO API, PatentsView API, Google Patents, and USPTO Bulk Data.
"""

from uspto_data.uspto_client import USPTOClient, get_default_client
from uspto_data.patentsview import PatentsViewClient
from uspto_data.google_patents import (
    GooglePatentsScraper,
    create_patent_from_google,
    create_publication_from_google
)
from uspto_data.bulk_data import (
    USPTOBulkDataFetcher,
    create_patent_from_bulk_data,
    fetch_patent_text
)

__all__ = [
    'USPTOClient',
    'get_default_client',
    'PatentsViewClient',
    'GooglePatentsScraper',
    'create_patent_from_google',
    'create_publication_from_google',
    'USPTOBulkDataFetcher',
    'create_patent_from_bulk_data',
    'fetch_patent_text'
]
