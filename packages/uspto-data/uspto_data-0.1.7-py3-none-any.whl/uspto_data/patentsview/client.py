"""
PatentsView API Client

Provides a client for accessing the PatentsView Search API.
"""

import os
import time
import threading
from queue import Queue, Empty
from typing import Any, Dict, List, Optional, Union
import requests

from uspto_data.patentsview.endpoints import ENDPOINTS
from uspto_data.patentsview.query_builder import QueryBuilder, FieldList, SortBuilder, OptionsBuilder


BASE_URL = "https://search.patentsview.org/api/v1/"
DEFAULT_API_KEY = os.getenv("PATENTSVIEW_API_KEY", "")


class PatentsViewClient:
    """
    Client for the PatentsView Search API.

    Example usage:
        client = PatentsViewClient(api_key="YOUR_API_KEY")

        # Simple search
        results = client.search(
            endpoint="patent",
            query=QueryBuilder.eq("patent_number", "10000000"),
            fields=["patent_number", "patent_title", "patent_date"]
        )

        # Complex query with builder
        query = QueryBuilder.and_(
            QueryBuilder.gte("patent_date", "2020-01-01"),
            QueryBuilder.text_any("patent_abstract", "machine learning")
        )
        results = client.search("patent", query, fields=["patent_number", "patent_title"])
    """

    def __init__(self, api_key: str = None, rate_limit: float = 1.34):
        """
        Initialize the PatentsViewClient with your API key.

        :param api_key: Your PatentsView API key. If not provided, will use PATENTSVIEW_API_KEY env variable.
        :param rate_limit: Minimum interval (in seconds) between API requests.
                          Default is 1.34 seconds (45 requests/minute limit).
        """
        self.api_key = api_key or DEFAULT_API_KEY
        if not self.api_key:
            raise ValueError(
                "An API key must be provided either as a parameter or via the PATENTSVIEW_API_KEY environment variable"
            )

        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "X-Api-Key": self.api_key
        })

        self.rate_limit = rate_limit
        self.queue = Queue()
        self._stop_event = threading.Event()
        self._last_request_time = 0

        # Start a worker thread to process the request queue with rate limiting
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def _process_queue(self):
        """Worker thread to process requests in the queue while enforcing rate-limiting."""
        while not self._stop_event.is_set():
            try:
                func, args, kwargs, result_queue = self.queue.get(timeout=0.1)
                elapsed = time.time() - self._last_request_time
                if elapsed < self.rate_limit:
                    time.sleep(self.rate_limit - elapsed)
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(result)
                except Exception as e:
                    result_queue.put(e)
                finally:
                    self._last_request_time = time.time()
                    self.queue.task_done()
            except Empty:
                continue

    def _enqueue_request(self, func, *args, **kwargs):
        """
        Add a request to the queue and wait for the result.

        :param func: The function to execute.
        :param args: Positional arguments for the function.
        :param kwargs: Keyword arguments for the function.
        :return: The result of the function execution.
        """
        result_queue = Queue()
        self.queue.put((func, args, kwargs, result_queue))
        result = result_queue.get()
        if isinstance(result, Exception):
            raise result
        self.queue.join()
        return result

    def search(
        self,
        endpoint: str,
        query: Optional[Union[Dict[str, Any], QueryBuilder]] = None,
        fields: Optional[Union[List[str], FieldList]] = None,
        sort: Optional[Union[List[Dict[str, str]], SortBuilder]] = None,
        options: Optional[Union[Dict[str, Any], OptionsBuilder]] = None,
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Perform a search query against the PatentsView API.

        :param endpoint: The endpoint to query (e.g., "patent", "inventor", "assignee")
        :param query: Query object or dict using PatentsView query language
        :param fields: List of fields to return, or FieldList object
        :param sort: Sort specifications, or SortBuilder object
        :param options: Options dict or OptionsBuilder object (pagination, etc.)
        :param method: HTTP method to use (default "POST")
        :return: Response dictionary with results
        """
        if endpoint not in ENDPOINTS:
            raise ValueError(f"Unknown endpoint: {endpoint}. Available endpoints: {list(ENDPOINTS.keys())}")

        # Build the request payload
        payload = {}

        if query is not None:
            if isinstance(query, QueryBuilder):
                payload["q"] = query.build()
            else:
                payload["q"] = query

        if fields is not None:
            if isinstance(fields, FieldList):
                payload["f"] = fields.build()
            else:
                payload["f"] = fields

        if sort is not None:
            if isinstance(sort, SortBuilder):
                payload["s"] = sort.build()
            else:
                payload["s"] = sort

        if options is not None:
            if isinstance(options, OptionsBuilder):
                payload["o"] = options.build()
            else:
                payload["o"] = options

        # Construct the full URL
        url = f"{self.base_url}{ENDPOINTS[endpoint]}"

        # Make the request
        if method.upper() == "POST":
            response = self._enqueue_request(
                self.session.post,
                url,
                json=payload
            )
        else:  # GET
            response = self._enqueue_request(
                self.session.get,
                url,
                params=payload
            )

        response.raise_for_status()
        return response.json()

    def get_patent(
        self,
        patent_number: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to get a specific patent by patent number.

        :param patent_number: The patent number to retrieve
        :param fields: Optional list of fields to return
        :return: Patent data
        """
        query = QueryBuilder.eq("patent_number", patent_number)
        return self.search("patent", query=query, fields=fields)

    def get_inventor(
        self,
        inventor_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to get a specific inventor by ID.

        :param inventor_id: The inventor ID to retrieve
        :param fields: Optional list of fields to return
        :return: Inventor data
        """
        query = QueryBuilder.eq("inventor_id", inventor_id)
        return self.search("inventor", query=query, fields=fields)

    def get_assignee(
        self,
        assignee_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to get a specific assignee by ID.

        :param assignee_id: The assignee ID to retrieve
        :param fields: Optional list of fields to return
        :return: Assignee data
        """
        query = QueryBuilder.eq("assignee_id", assignee_id)
        return self.search("assignee", query=query, fields=fields)

    def search_patents_by_text(
        self,
        text: str,
        field: str = "patent_abstract",
        match_type: str = "any",
        fields: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Convenience method to search patents by text.

        :param text: The text to search for
        :param field: The field to search in (default: patent_abstract)
        :param match_type: Type of text match - "any", "all", or "phrase"
        :param fields: Optional list of fields to return
        :param limit: Maximum number of results (default: 100)
        :return: Search results
        """
        if match_type == "any":
            query = QueryBuilder.text_any(field, text)
        elif match_type == "all":
            query = QueryBuilder.text_all(field, text)
        elif match_type == "phrase":
            query = QueryBuilder.text_phrase(field, text)
        else:
            raise ValueError(f"Invalid match_type: {match_type}. Must be 'any', 'all', or 'phrase'")

        options = OptionsBuilder().size(limit)
        return self.search("patent", query=query, fields=fields, options=options)

    def search_patents_by_date_range(
        self,
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Convenience method to search patents by date range.

        :param start_date: Start date in YYYY-MM-DD format
        :param end_date: End date in YYYY-MM-DD format
        :param fields: Optional list of fields to return
        :param limit: Maximum number of results (default: 100)
        :return: Search results
        """
        query = QueryBuilder.and_(
            QueryBuilder.gte("patent_date", start_date),
            QueryBuilder.lte("patent_date", end_date)
        )
        options = OptionsBuilder().size(limit)
        return self.search("patent", query=query, fields=fields, options=options)

    def stop(self):
        """Stop the worker thread gracefully."""
        self._stop_event.set()
        self._worker_thread.join()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Example usage
if __name__ == "__main__":
    import json

    # Initialize client
    client = PatentsViewClient()

    try:
        # Example 1: Get a specific patent
        result = client.get_patent("10000000", fields=["patent_number", "patent_title", "patent_date"])
        print("Patent:", json.dumps(result, indent=2))

        # Example 2: Search patents by text
        result = client.search_patents_by_text(
            "machine learning",
            field="patent_abstract",
            match_type="any",
            fields=["patent_number", "patent_title"],
            limit=10
        )
        print(f"\nFound {result.get('total_hits', 0)} patents")

        # Example 3: Complex query
        query = QueryBuilder.and_(
            QueryBuilder.gte("patent_date", "2020-01-01"),
            QueryBuilder.text_any("patent_abstract", "artificial intelligence")
        )
        result = client.search(
            "patent",
            query=query,
            fields=["patent_number", "patent_title", "patent_date"],
            sort=SortBuilder().desc("patent_date"),
            options=OptionsBuilder().size(25)
        )
        print(f"\nComplex query found {result.get('total_hits', 0)} patents")

    finally:
        client.stop()
