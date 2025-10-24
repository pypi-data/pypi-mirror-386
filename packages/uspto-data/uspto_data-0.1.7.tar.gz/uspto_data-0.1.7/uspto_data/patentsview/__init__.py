"""
PatentsView API Client

This module provides access to the PatentsView Search API.
PatentsView is a USPTO database that provides detailed information about US patents and patent applications.
"""

from uspto_data.patentsview.client import PatentsViewClient

__all__ = ['PatentsViewClient']
