"""
Mock USPTO Client for Google Patents

Provides a dummy client that doesn't require an API key.
"""


class MockUSPTOClient:
    """
    Mock USPTO client that doesn't make any API calls.

    Used by Google Patents factory to avoid requiring USPTO API key.
    """

    def __init__(self):
        self.api_key = None
        self.BASE_URL = ""

    def call_api(self, *args, **kwargs):
        """Mock API call - does nothing."""
        raise NotImplementedError("This is a mock client from Google Patents data")

    def get_file(self, *args, **kwargs):
        """Mock file download - does nothing."""
        raise NotImplementedError("This is a mock client from Google Patents data")

    def stop(self):
        """Mock stop - does nothing."""
        pass
