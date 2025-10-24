"""
Google Patents Web Scraper

Scrapes patent and publication data from Google Patents pages.
"""

import re
import requests
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class GooglePatentData:
    """
    Container for scraped patent data from Google Patents.
    """
    patent_number: Optional[str] = None
    publication_number: Optional[str] = None
    application_number: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    filing_date: Optional[str] = None
    grant_date: Optional[str] = None
    publication_date: Optional[str] = None
    inventors: List[str] = None
    assignee: Optional[str] = None
    claims: List[str] = None
    description: Optional[str] = None
    classifications: List[Dict[str, str]] = None
    priority_date: Optional[str] = None
    application_events: List[Dict[str, Any]] = None
    citations: List[Dict[str, str]] = None
    family_members: List[Dict[str, str]] = None
    legal_events: List[Dict[str, Any]] = None
    raw_html: Optional[str] = None

    def __post_init__(self):
        if self.inventors is None:
            self.inventors = []
        if self.claims is None:
            self.claims = []
        if self.classifications is None:
            self.classifications = []
        if self.application_events is None:
            self.application_events = []
        if self.citations is None:
            self.citations = []
        if self.family_members is None:
            self.family_members = []
        if self.legal_events is None:
            self.legal_events = []


class GooglePatentsScraper:
    """
    Scraper for Google Patents website.

    Extracts patent and publication information from Google Patents HTML pages.
    """

    BASE_URL = "https://patents.google.com/patent/"

    def __init__(self, user_agent: str = None):
        """
        Initialize the scraper.

        :param user_agent: Optional custom user agent string
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_patent(self, patent_id: str) -> GooglePatentData:
        """
        Fetch and parse patent data from Google Patents.

        :param patent_id: Patent number (e.g., "US10000000", "US20230083854A1")
        :return: GooglePatentData object with scraped information
        """
        # Normalize patent ID
        patent_id = self._normalize_patent_id(patent_id)
        url = f"{self.BASE_URL}{patent_id}/en"

        response = self.session.get(url)
        response.raise_for_status()

        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        data = GooglePatentData(raw_html=html_content)

        # Extract basic information
        self._extract_title(soup, data)
        self._extract_numbers(soup, data)
        self._extract_dates(soup, data)
        self._extract_abstract(soup, data)
        self._extract_inventors(soup, data)
        self._extract_assignee(soup, data)
        self._extract_claims(soup, data)
        self._extract_description(soup, data)
        self._extract_classifications(soup, data)
        self._extract_citations(soup, data)
        self._extract_legal_events(soup, data)

        return data

    def _normalize_patent_id(self, patent_id: str) -> str:
        """Normalize patent ID to Google Patents format."""
        # Remove spaces, commas, and forward slashes
        patent_id = patent_id.replace(" ", "").replace(",", "").replace("/", "")

        # Ensure it starts with "US" if it's just numbers
        if patent_id.isdigit():
            patent_id = f"US{patent_id}"
        elif not patent_id.startswith("US"):
            patent_id = f"US{patent_id}"

        return patent_id

    def _extract_title(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract patent title."""
        title_elem = soup.find('meta', {'name': 'DC.title'})
        if title_elem and title_elem.get('content'):
            data.title = title_elem['content']
        else:
            # Fallback to h1
            h1 = soup.find('h1', {'id': 'title'})
            if h1:
                data.title = h1.get_text(strip=True)

    def _extract_numbers(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract patent, publication, and application numbers."""
        # Publication number
        pub_meta = soup.find('meta', {'name': 'DC.identifier'})
        if pub_meta:
            pub_num = pub_meta.get('content', '').replace('US', '').replace('patent/', '')
            # Determine if it's a patent or publication
            if 'A1' in pub_num or 'A' in pub_num:
                data.publication_number = pub_num.replace('A1', '').replace('A', '')
            else:
                data.patent_number = pub_num.replace('B1', '').replace('B2', '').replace('B', '')

        # Look for application number in the page
        app_dd = soup.find('dd', {'itemprop': 'applicationNumber'})
        if app_dd:
            data.application_number = app_dd.get_text(strip=True).replace('US', '')

    def _extract_dates(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract filing, grant, and publication dates."""
        # Filing date
        filing_meta = soup.find('meta', {'name': 'DC.date'})
        if filing_meta:
            date_str = filing_meta.get('content')
            # Try to determine which date this is based on context
            data.filing_date = date_str

        # Look for specific date fields
        time_tags = soup.find_all('time', {'itemprop': True})
        for time_tag in time_tags:
            date_value = time_tag.get('datetime') or time_tag.get_text(strip=True)
            prop = time_tag.get('itemprop')

            if prop == 'filingDate':
                data.filing_date = date_value
            elif prop == 'publicationDate':
                data.publication_date = date_value
            elif prop == 'grantDate' or prop == 'issueDate':
                data.grant_date = date_value
            elif prop == 'priorityDate':
                data.priority_date = date_value

    def _extract_abstract(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract patent abstract."""
        abstract_div = soup.find('div', {'class': 'abstract'}) or soup.find('abstract')
        if abstract_div:
            data.abstract = abstract_div.get_text(strip=True)
        else:
            # Try meta tag
            abstract_meta = soup.find('meta', {'name': 'DC.description'})
            if abstract_meta:
                data.abstract = abstract_meta.get('content')

    def _extract_inventors(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract inventor names."""
        inventor_elements = soup.find_all('dd', {'itemprop': 'inventor'})
        for elem in inventor_elements:
            inventor_name = elem.get_text(strip=True)
            if inventor_name:
                data.inventors.append(inventor_name)

        # Fallback to meta tags
        if not data.inventors:
            creator_metas = soup.find_all('meta', {'name': 'DC.creator'})
            for meta in creator_metas:
                inventor = meta.get('content')
                if inventor:
                    data.inventors.append(inventor)

    def _extract_assignee(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract assignee/owner information."""
        assignee_elem = soup.find('dd', {'itemprop': 'assigneeCurrent'}) or \
                       soup.find('dd', {'itemprop': 'assignee'})
        if assignee_elem:
            data.assignee = assignee_elem.get_text(strip=True)

    def _extract_claims(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract patent claims."""
        claims_section = soup.find('section', {'itemprop': 'claims'})
        if claims_section:
            claim_divs = claims_section.find_all('div', {'class': 'claim'}) or \
                        claims_section.find_all('claim')
            for claim_div in claim_divs:
                claim_text = claim_div.get_text(strip=True)
                if claim_text:
                    data.claims.append(claim_text)

    def _extract_description(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract patent description."""
        desc_section = soup.find('section', {'itemprop': 'description'})
        if desc_section:
            data.description = desc_section.get_text(strip=True)

    def _extract_classifications(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract classification information (CPC, IPC, etc.)."""
        # CPC classifications
        cpc_elements = soup.find_all('span', {'itemprop': 'Cpc'})
        for elem in cpc_elements:
            classification = elem.get_text(strip=True)
            if classification:
                data.classifications.append({
                    'type': 'CPC',
                    'code': classification
                })

        # IPC classifications
        ipc_elements = soup.find_all('span', {'itemprop': 'Ipc'})
        for elem in ipc_elements:
            classification = elem.get_text(strip=True)
            if classification:
                data.classifications.append({
                    'type': 'IPC',
                    'code': classification
                })

    def _extract_citations(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract cited patents and non-patent literature."""
        # Find citations section
        citations_section = soup.find('section', {'id': 'citations'})
        if citations_section:
            citation_links = citations_section.find_all('a', href=re.compile(r'/patent/'))
            for link in citation_links:
                patent_id = link.get('href', '').split('/patent/')[-1].split('/')[0]
                citation_text = link.get_text(strip=True)
                if patent_id:
                    data.citations.append({
                        'patent_id': patent_id,
                        'text': citation_text
                    })

    def _extract_legal_events(self, soup: BeautifulSoup, data: GooglePatentData):
        """Extract legal events and status information."""
        # Look for legal events table or section
        events_section = soup.find('section', {'id': 'legal-events'}) or \
                        soup.find('table', {'id': 'legal-events'})

        if events_section:
            rows = events_section.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 2:
                    event = {
                        'date': cols[0].get_text(strip=True) if cols else None,
                        'code': cols[1].get_text(strip=True) if len(cols) > 1 else None,
                        'description': cols[2].get_text(strip=True) if len(cols) > 2 else None
                    }
                    data.legal_events.append(event)

    def get_patent_url(self, patent_id: str) -> str:
        """
        Get the Google Patents URL for a given patent ID.

        :param patent_id: Patent number
        :return: Full URL to the patent on Google Patents
        """
        patent_id = self._normalize_patent_id(patent_id)
        return f"{self.BASE_URL}{patent_id}/en"


if __name__ == "__main__":
    # Example usage
    scraper = GooglePatentsScraper()

    # Test with a granted patent
    print("Fetching US10000000...")
    patent_data = scraper.fetch_patent("US10000000")
    print(f"Title: {patent_data.title}")
    print(f"Patent Number: {patent_data.patent_number}")
    print(f"Filing Date: {patent_data.filing_date}")
    print(f"Grant Date: {patent_data.grant_date}")
    print(f"Inventors: {', '.join(patent_data.inventors)}")
    print(f"Assignee: {patent_data.assignee}")
    print(f"Abstract: {patent_data.abstract[:200]}..." if patent_data.abstract else "No abstract")
    print(f"Number of claims: {len(patent_data.claims)}")

    # Test with a publication
    print("\n\nFetching US20230083854A1...")
    pub_data = scraper.fetch_patent("US20230083854A1")
    print(f"Title: {pub_data.title}")
    print(f"Publication Number: {pub_data.publication_number}")
    print(f"Filing Date: {pub_data.filing_date}")
