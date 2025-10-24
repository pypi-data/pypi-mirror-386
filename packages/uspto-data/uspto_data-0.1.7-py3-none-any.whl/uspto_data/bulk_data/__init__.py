"""
USPTO Bulk Data Interface

This module provides functionality to fetch patent full text from USPTO bulk data archives.
"""

from uspto_data.bulk_data.fetcher import USPTOBulkDataFetcher
from uspto_data.bulk_data.factory import (
    create_patent_from_bulk_data,
    fetch_patent_text
)

__all__ = [
    'USPTOBulkDataFetcher',
    'create_patent_from_bulk_data',
    'fetch_patent_text'
]
