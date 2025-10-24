"""
Query Builder for PatentsView API

Provides a fluent interface for constructing PatentsView API queries using their query language.
"""

from typing import Any, Dict, List, Union


class QueryBuilder:
    """
    Builder class for constructing PatentsView API query objects.

    The PatentsView API uses a JSON-based query language with operators like:
    - _eq, _neq: Equality
    - _gt, _gte, _lt, _lte: Comparisons
    - _begins, _contains, _ends: String matching
    - _text_all, _text_any, _text_phrase: Full-text search
    - _and, _or, _not: Logical operators
    """

    def __init__(self):
        self.query_dict = {}

    # Comparison operators
    @staticmethod
    def eq(field: str, value: Any) -> Dict[str, Any]:
        """Equal to"""
        return {field: {"_eq": value}}

    @staticmethod
    def neq(field: str, value: Any) -> Dict[str, Any]:
        """Not equal to"""
        return {field: {"_neq": value}}

    @staticmethod
    def gt(field: str, value: Any) -> Dict[str, Any]:
        """Greater than"""
        return {field: {"_gt": value}}

    @staticmethod
    def gte(field: str, value: Any) -> Dict[str, Any]:
        """Greater than or equal to"""
        return {field: {"_gte": value}}

    @staticmethod
    def lt(field: str, value: Any) -> Dict[str, Any]:
        """Less than"""
        return {field: {"_lt": value}}

    @staticmethod
    def lte(field: str, value: Any) -> Dict[str, Any]:
        """Less than or equal to"""
        return {field: {"_lte": value}}

    # String operators
    @staticmethod
    def begins(field: str, value: str) -> Dict[str, Any]:
        """String begins with"""
        return {field: {"_begins": value}}

    @staticmethod
    def contains(field: str, value: str) -> Dict[str, Any]:
        """String contains"""
        return {field: {"_contains": value}}

    @staticmethod
    def ends(field: str, value: str) -> Dict[str, Any]:
        """String ends with"""
        return {field: {"_ends": value}}

    # Text search operators
    @staticmethod
    def text_all(field: str, value: str) -> Dict[str, Any]:
        """Full-text search - all words must match"""
        return {field: {"_text_all": value}}

    @staticmethod
    def text_any(field: str, value: str) -> Dict[str, Any]:
        """Full-text search - any word must match"""
        return {field: {"_text_any": value}}

    @staticmethod
    def text_phrase(field: str, value: str) -> Dict[str, Any]:
        """Full-text search - exact phrase match"""
        return {field: {"_text_phrase": value}}

    # Logical operators
    @staticmethod
    def and_(*conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Logical AND"""
        return {"_and": list(conditions)}

    @staticmethod
    def or_(*conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Logical OR"""
        return {"_or": list(conditions)}

    @staticmethod
    def not_(condition: Dict[str, Any]) -> Dict[str, Any]:
        """Logical NOT"""
        return {"_not": condition}

    def build(self) -> Dict[str, Any]:
        """Return the constructed query dictionary"""
        return self.query_dict if self.query_dict else {}


class FieldList:
    """
    Builder for constructing field lists for PatentsView API requests.
    """

    def __init__(self, fields: List[str] = None):
        self.fields = fields or []

    def add(self, *fields: str) -> 'FieldList':
        """Add fields to the field list"""
        self.fields.extend(fields)
        return self

    def build(self) -> List[str]:
        """Return the list of fields"""
        return self.fields


class SortBuilder:
    """
    Builder for constructing sort specifications for PatentsView API requests.
    """

    def __init__(self):
        self.sorts = []

    def asc(self, field: str) -> 'SortBuilder':
        """Sort by field in ascending order"""
        self.sorts.append({field: "asc"})
        return self

    def desc(self, field: str) -> 'SortBuilder':
        """Sort by field in descending order"""
        self.sorts.append({field: "desc"})
        return self

    def build(self) -> List[Dict[str, str]]:
        """Return the list of sort specifications"""
        return self.sorts


class OptionsBuilder:
    """
    Builder for constructing options for PatentsView API requests.
    """

    def __init__(self):
        self.options = {}

    def size(self, size: int) -> 'OptionsBuilder':
        """Set the number of results per page (max 10000)"""
        self.options["size"] = size
        return self

    def after(self, after_key: str) -> 'OptionsBuilder':
        """Set pagination cursor for retrieving next page"""
        self.options["after"] = after_key
        return self

    def matched_subentities_only(self, value: bool = True) -> 'OptionsBuilder':
        """Return only matched subentities"""
        self.options["matched_subentities_only"] = value
        return self

    def include_subentity_total_counts(self, value: bool = True) -> 'OptionsBuilder':
        """Include total counts for subentities"""
        self.options["include_subentity_total_counts"] = value
        return self

    def build(self) -> Dict[str, Any]:
        """Return the options dictionary"""
        return self.options
