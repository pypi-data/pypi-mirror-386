"""
USPTO Bulk Data Fetcher

Fetches patent full text from USPTO bulk data archives.
Uses the new USPTO Bulk Dataset API.
"""

import re
import io
import zipfile
import requests
import os
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass
from bs4 import BeautifulSoup

TIMEOUT = 45
USER_AGENT = "USPTO-FullText-Fetcher/uspto-data"

# Patent number milestones for estimating issue year
MILESTONES = [
    (4000000, 1976), (5000000, 1991), (6000000, 1999),
    (7000000, 2006), (8000000, 2011), (9000000, 2015),
    (10000000, 2018), (11000000, 2021), (12000000, 2024)
]


@dataclass
class BulkDataPatentText:
    """Container for patent text extracted from bulk data."""
    patent_number: str
    abstract: str
    description: str
    claims: str
    source_file: Optional[str] = None
    source_url: Optional[str] = None
    year: Optional[int] = None
    raw_xml: Optional[str] = None


class USPTOBulkDataFetcher:
    """
    Fetches patent full text from USPTO bulk data archives.

    This class searches through USPTO RedBook archives to find and extract
    patent text including abstract, description, and claims.
    """

    def __init__(self, uspto_client=None, user_agent: str = USER_AGENT, timeout: int = TIMEOUT):
        """
        Initialize the bulk data fetcher.

        :param uspto_client: USPTOClient instance (optional, will create one if not provided)
        :param user_agent: User agent string for HTTP requests
        :param timeout: HTTP request timeout in seconds
        """
        if uspto_client is None:
            from uspto_data.uspto_client import get_default_client
            self.client = get_default_client()
        else:
            self.client = uspto_client

        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}
        self._product_cache = None

    def _get_patent_grant_products(self):
        """Get and cache the patent grant XML products."""
        if self._product_cache is not None:
            return self._product_cache

        print("[i] Fetching available patent grant datasets...")
        result = self.client.call_api('datasets/products/search', query_params={'query': 'patent grant xml'})

        # Find the XML patent grant products
        self._product_cache = []
        for product in result.bulkDataProductBag:
            if 'XML' in product.productIdentifier or 'xml' in (product.productTitleText or '').lower():
                self._product_cache.append(product)

        return self._product_cache

    def _get_product_details(self, product_id: str):
        """Get full product details with all files."""
        try:
            product_detail = self.client.call_api('datasets/products/{productIdentifier}', url_params={'productIdentifier': product_id})
            return product_detail.bulkDataProductBag[0] if product_detail.bulkDataProductBag else None
        except Exception as e:
            print(f"[!] Error fetching product {product_id}: {e}")
            return None

    def _find_files_for_year(self, product_detail, year: int):
        """Find files for a specific year within product details."""
        matching_files = []
        if product_detail and product_detail.productFileBag:
            for file_data in product_detail.productFileBag.fileDataBag:
                # Check if filename contains the year
                if str(year) in file_data.fileName:
                    matching_files.append(file_data)
        return matching_files

    def _download_and_search_file(self, file_data, patnum: str):
        """Download a file and search for the patent."""
        print(f"[i] Downloading {file_data.fileName}...")
        try:
            # Use the USPTO client's session which has the API key
            response = self.client.session.get(file_data.fileDownloadURI, timeout=self.timeout)
            response.raise_for_status()

            result = self._scan_zip_for_patent(response.content, patnum)
            if result:
                return file_data.fileName, file_data.fileDownloadURI, result
        except Exception as e:
            print(f"[!] Error downloading/scanning {file_data.fileName}: {e}")

        return None

    def fetch_patent_text(self, patent_number: str) -> Optional[BulkDataPatentText]:
        """
        Fetch full text for a given patent number from bulk data.

        :param patent_number: Patent number (e.g., "10000000", "US10000000")
        :return: BulkDataPatentText object or None if not found
        """
        # Normalize patent number
        patnum = self._normalize_patent_number(patent_number)
        if not patnum:
            raise ValueError(f"Invalid patent number: {patent_number}")

        # Estimate issue year
        patnum_int = int(patnum)
        approx_year = self._guess_issue_year(patnum_int)

        print(f"[i] Searching for US{patnum} (estimated year: ~{approx_year})")

        # Get available patent grant products
        products = self._get_patent_grant_products()
        if not products:
            print("[!] No patent grant products found")
            return None

        # Get full details for the main patent grant XML product (most likely to have what we need)
        print("[i] Fetching patent grant XML product details...")
        product_details = None
        for product in products:
            if product.productIdentifier == 'PTGRXML':
                product_details = self._get_product_details(product.productIdentifier)
                break

        if not product_details:
            print("[!] Could not fetch product details")
            return None

        print(f"[i] Found {len(product_details.productFileBag.fileDataBag)} files in product")

        # Search across years (centered on estimated year)
        years = sorted(
            range(approx_year - 2, approx_year + 3),
            key=lambda y: abs(y - approx_year)
        )

        for year in years:
            print(f"[i] Scanning year {year}...")
            files = self._find_files_for_year(product_details, year)

            if not files:
                print(f"[i] No files found for year {year}")
                continue

            print(f"[i] Found {len(files)} files for year {year}")
            for file_data in files:
                result = self._download_and_search_file(file_data, patnum)
                if result:
                    fname, url, (abst, desc, clms, raw_xml) = result
                    return BulkDataPatentText(
                        patent_number=patnum,
                        abstract=abst,
                        description=desc,
                        claims=clms,
                        source_file=fname,
                        source_url=url,
                        year=year,
                        raw_xml=raw_xml
                    )

        return None

    def _normalize_patent_number(self, s: str) -> str:
        """Normalize patent number to digits only."""
        if not s:
            return ""

        s = s.strip().upper()
        # Remove common prefixes and separators
        s = s.replace("US", " ").replace(",", "").replace("-", " ").replace("/", " ")
        # Remove whitespace
        s = re.sub(r"\s+", "", s)
        # Remove kind codes (e.g., B1, B2, A1)
        s = re.sub(r"[A-Z]\d?$", "", s)
        # Extract only digits
        return re.sub(r"\D", "", s)

    def _guess_issue_year(self, patnum: int) -> int:
        """
        Estimate the issue year based on patent number.

        Uses known patent number milestones to interpolate the year.
        """
        anchors = [(0, 1963)] + MILESTONES + [(99999999, 2035)]

        # Find bounding milestones
        low = anchors[0]
        high = anchors[-1]

        for n, y in anchors:
            if n <= patnum and n >= low[0]:
                low = (n, y)
            if n >= patnum and n <= high[0]:
                high = (n, y)

        # If exact match
        if high[0] == low[0]:
            return low[1]

        # Interpolate year
        frac = (patnum - low[0]) / float(high[0] - low[0])
        return int(round(low[1] + frac * (high[1] - low[1])))

    def _contains_patent_number(self, text: str, patnum: str) -> bool:
        """Check if text contains the given patent number."""
        patterns = [
            rf"<doc-number>\s*{patnum}\s*</doc-number>",
            rf"\bPATNUM\W*{patnum}\b",
            rf"\bPNO\W*{patnum}\b",
            rf"\b{patnum}\b"
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _extract_xml_fields(self, xml_text: str) -> Tuple[str, str, str]:
        """Extract abstract, description, and claims from XML format."""
        soup = BeautifulSoup(xml_text, "lxml-xml")

        # Extract abstract
        abst = " ".join(
            t.get_text(" ", strip=True) for t in soup.find_all("abstract")
        )

        # Extract description
        desc = " ".join(
            t.get_text(" ", strip=True) for t in soup.find_all("description")
        )

        # Extract claims
        claims_elems = soup.find_all("claims")
        if claims_elems:
            cl_texts = []
            for ce in claims_elems:
                for c in ce.find_all("claim"):
                    cl_texts.append(c.get_text(" ", strip=True))
            clms = "\n\n".join(cl_texts)
        else:
            clms = "\n\n".join([
                c.get_text(" ", strip=True) for c in soup.find_all("claim")
            ])

        return abst.strip(), desc.strip(), clms.strip()

    def _extract_aps_fields(self, sgml_text: str) -> Tuple[str, str, str]:
        """Extract abstract, description, and claims from SGML/APS format."""
        def grab(tag):
            m = re.search(
                rf"<{tag}>(.*?)</{tag}>",
                sgml_text,
                flags=re.IGNORECASE | re.DOTALL
            )
            return m.group(1).strip() if m else ""

        abst = grab("ABST")
        desc = grab("DETDESC") or grab("DESC")
        clms = grab("CLMS")

        def clean(t):
            # Clean up whitespace
            t = re.sub(r"\s+", " ", t)
            # Remove HTML/SGML tags
            t = re.sub(r"<.*?>", " ", t)
            return t.strip()

        return clean(abst), clean(desc), clean(clms)

    def _scan_zip_for_patent(self, zip_bytes: bytes, patnum: str) -> Optional[Tuple[str, str, str, str]]:
        """
        Scan a ZIP file for the given patent number.

        :param zip_bytes: ZIP file contents
        :param patnum: Patent number to search for
        :return: Tuple of (abstract, description, claims, raw_xml) or None
        """
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for name in z.namelist():
                # Only process relevant file types
                if not name.lower().endswith((".xml", ".sgml", ".txt")):
                    continue

                # Read file content
                text = z.read(name).decode("utf-8", errors="ignore")

                # Check if this file contains our patent
                if not self._contains_patent_number(text, patnum):
                    continue

                # Extract fields based on format
                if "<us-patent-grant" in text:
                    abst, desc, clms = self._extract_xml_fields(text)
                else:
                    abst, desc, clms = self._extract_aps_fields(text)

                return abst, desc, clms, text

        return None


# Convenience function
def fetch_patent_text(patent_number: str) -> Optional[BulkDataPatentText]:
    """
    Convenience function to fetch patent text from bulk data.

    :param patent_number: Patent number (e.g., "10000000")
    :return: BulkDataPatentText object or None if not found
    """
    fetcher = USPTOBulkDataFetcher()
    return fetcher.fetch_patent_text(patent_number)


if __name__ == "__main__":
    # Example usage
    result = fetch_patent_text("10000000")

    if result:
        print(f"\n✓ Found patent US{result.patent_number}")
        print(f"  Source: {result.source_file} ({result.year})")
        print(f"  Abstract: {result.abstract[:150]}...")
        print(f"  Description length: {len(result.description)} chars")
        print(f"  Claims length: {len(result.claims)} chars")
    else:
        print("✗ Patent not found in bulk data")
