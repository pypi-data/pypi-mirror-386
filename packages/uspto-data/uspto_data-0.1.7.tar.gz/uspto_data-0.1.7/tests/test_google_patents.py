"""
Unit tests for Google Patents scraper.

Run with: python -m pytest tests/test_google_patents.py
"""

import pytest
from unittest.mock import Mock, patch
from uspto_data.google_patents import (
    GooglePatentsScraper,
    create_patent_from_google,
    create_publication_from_google
)
from uspto_data.google_patents.scraper import GooglePatentData
from uspto_data.google_patents.adapter import GooglePatentsAdapter


class TestGooglePatentsScraper:
    """Tests for GooglePatentsScraper class."""

    def test_scraper_initialization(self):
        """Test that scraper initializes correctly."""
        scraper = GooglePatentsScraper()
        assert scraper is not None
        assert scraper.BASE_URL == "https://patents.google.com/patent/"

    def test_normalize_patent_id(self):
        """Test patent ID normalization."""
        scraper = GooglePatentsScraper()

        assert scraper._normalize_patent_id("10000000") == "US10000000"
        assert scraper._normalize_patent_id("US10000000") == "US10000000"
        assert scraper._normalize_patent_id("US10000000B2") == "US10000000B2"
        assert scraper._normalize_patent_id("20230083854") == "US20230083854"

    def test_get_patent_url(self):
        """Test URL generation."""
        scraper = GooglePatentsScraper()
        url = scraper.get_patent_url("10000000")
        assert url == "https://patents.google.com/patent/US10000000/en"


class TestGooglePatentData:
    """Tests for GooglePatentData dataclass."""

    def test_data_initialization(self):
        """Test that GooglePatentData initializes with defaults."""
        data = GooglePatentData()

        assert data.patent_number is None
        assert isinstance(data.inventors, list)
        assert isinstance(data.claims, list)
        assert isinstance(data.classifications, list)
        assert len(data.inventors) == 0

    def test_data_with_values(self):
        """Test GooglePatentData with values."""
        data = GooglePatentData(
            patent_number="10000000",
            title="Test Patent",
            inventors=["John Doe", "Jane Smith"],
            filing_date="2015-01-01"
        )

        assert data.patent_number == "10000000"
        assert data.title == "Test Patent"
        assert len(data.inventors) == 2
        assert data.filing_date == "2015-01-01"


class TestGooglePatentsAdapter:
    """Tests for GooglePatentsAdapter."""

    def test_create_patent_file_wrapper_data_bag(self):
        """Test adapter creates proper data structure."""
        google_data = GooglePatentData(
            patent_number="10000000",
            application_number="14123456",
            title="Test Patent",
            filing_date="2015-01-01",
            grant_date="2018-06-01",
            inventors=["John Doe"],
            assignee="Test Company"
        )

        patent_info = GooglePatentsAdapter.create_patent_file_wrapper_data_bag(google_data)

        assert patent_info.applicationNumberText == "14123456"
        assert patent_info.applicationMetaData.patentNumber == "10000000"
        assert patent_info.applicationMetaData.inventionTitle == "Test Patent"
        assert patent_info.applicationMetaData.filingDate == "2015-01-01"
        assert patent_info.applicationMetaData.grantDate == "2018-06-01"

    def test_extract_cpc_codes(self):
        """Test CPC code extraction."""
        google_data = GooglePatentData(
            classifications=[
                {"type": "CPC", "code": "H01L21/8249"},
                {"type": "IPC", "code": "H01L 29/66"},
                {"type": "CPC", "code": "H01L29/737"}
            ]
        )

        cpc_codes = GooglePatentsAdapter._extract_cpc_codes(google_data)

        assert len(cpc_codes) == 2
        assert "H01L21/8249" in cpc_codes
        assert "H01L29/737" in cpc_codes

    def test_create_inventor_bag(self):
        """Test inventor bag creation."""
        google_data = GooglePatentData(
            inventors=["John Michael Doe", "Jane Smith"]
        )

        inventor_bag = GooglePatentsAdapter._create_inventor_bag(google_data)

        assert len(inventor_bag) == 2
        assert inventor_bag[0].firstName == "John"
        assert inventor_bag[0].lastName == "Doe"
        assert inventor_bag[0].middleName == "Michael"
        assert inventor_bag[1].firstName == "Jane"
        assert inventor_bag[1].lastName == "Smith"


class TestFactoryFunctions:
    """Tests for factory functions."""

    @patch('uspto_data.google_patents.factory.GooglePatentsScraper')
    def test_create_patent_from_google(self, mock_scraper_class):
        """Test patent creation from Google Patents."""
        # Mock the scraper
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper

        # Mock the scraped data
        mock_data = GooglePatentData(
            patent_number="10000000",
            application_number="14123456",
            title="Test Patent",
            filing_date="2015-01-01",
            grant_date="2018-06-01",
            inventors=["John Doe"]
        )
        mock_scraper.fetch_patent.return_value = mock_data

        # Create patent
        patent = create_patent_from_google("10000000")

        # Verify
        assert patent.patent_number == "10000000"
        assert patent.application_number == "14123456"
        assert patent.patent_info is not None
        assert hasattr(patent, '_google_patents_data')

    @patch('uspto_data.google_patents.factory.GooglePatentsScraper')
    def test_create_publication_from_google(self, mock_scraper_class):
        """Test publication creation from Google Patents."""
        # Mock the scraper
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper

        # Mock the scraped data
        mock_data = GooglePatentData(
            publication_number="20230083854",
            application_number="17123456",
            title="Test Publication",
            filing_date="2021-01-01",
            publication_date="2023-03-01",
            inventors=["Jane Smith"]
        )
        mock_scraper.fetch_patent.return_value = mock_data

        # Create publication
        publication = create_publication_from_google("20230083854")

        # Verify
        assert publication.publication_number == "20230083854"
        assert publication.application_number == "17123456"
        assert publication.patent_info is not None
        assert hasattr(publication, '_google_patents_data')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
