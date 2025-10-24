"""
Response parser for PatentsView API responses.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class PatentsViewResponse:
    """
    Represents a response from the PatentsView API.

    Attributes:
        patents: List of patent records (for patent endpoint)
        inventors: List of inventor records (for inventor endpoint)
        assignees: List of assignee records (for assignee endpoint)
        publications: List of publication records (for publication endpoint)
        count: Number of records returned in this response
        total_hits: Total number of records matching the query
        error: Whether an error occurred
        error_message: Error message if error occurred
        raw_response: The complete raw response dictionary
    """
    count: int = 0
    total_hits: int = 0
    error: bool = False
    error_message: Optional[str] = None
    patents: List[Dict[str, Any]] = field(default_factory=list)
    inventors: List[Dict[str, Any]] = field(default_factory=list)
    assignees: List[Dict[str, Any]] = field(default_factory=list)
    publications: List[Dict[str, Any]] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    cpc_classes: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    raw_response: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> 'PatentsViewResponse':
        """
        Parse a PatentsView API response into a PatentsViewResponse object.

        :param response: The raw API response dictionary
        :return: PatentsViewResponse object
        """
        obj = cls(
            count=response.get('count', 0),
            total_hits=response.get('total_hits', 0),
            error=response.get('error', False),
            error_message=response.get('error_message'),
            raw_response=response
        )

        # Extract the appropriate data based on what's in the response
        if 'patents' in response:
            obj.patents = response['patents']
        if 'inventors' in response:
            obj.inventors = response['inventors']
        if 'assignees' in response:
            obj.assignees = response['assignees']
        if 'publications' in response:
            obj.publications = response['publications']
        if 'locations' in response:
            obj.locations = response['locations']
        if 'cpc_classes' in response:
            obj.cpc_classes = response['cpc_classes']
        if 'us_patent_citations' in response:
            obj.citations = response['us_patent_citations']
        if 'us_application_citations' in response:
            obj.citations = response['us_application_citations']
        if 'foreign_citations' in response:
            obj.citations = response['foreign_citations']

        return obj

    def get_results(self) -> List[Dict[str, Any]]:
        """
        Get the primary results from this response.
        Returns whichever result list has data.

        :return: List of result dictionaries
        """
        if self.patents:
            return self.patents
        if self.inventors:
            return self.inventors
        if self.assignees:
            return self.assignees
        if self.publications:
            return self.publications
        if self.locations:
            return self.locations
        if self.cpc_classes:
            return self.cpc_classes
        if self.citations:
            return self.citations
        return []

    def __len__(self) -> int:
        """Return the count of results in this response."""
        return self.count

    def __iter__(self):
        """Iterate over the primary results."""
        return iter(self.get_results())

    def __getitem__(self, index: int) -> Dict[str, Any]:
        """Get a result by index."""
        return self.get_results()[index]
