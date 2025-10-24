"""
PatentsView API Endpoints

Defines all available endpoints for the PatentsView Search API.
"""

# Endpoint mapping: friendly name -> API path
ENDPOINTS = {
    # Granted Patent Endpoints
    "patent": "patent/",
    "us_patent_citation": "patent/us_patent_citation/",
    "us_application_citation": "patent/us_application_citation/",
    "foreign_citation": "patent/foreign_citation/",
    "other_reference": "patent/other_reference/",
    "patent_attorney": "patent/attorney/",

    # Pre-grant Publication Endpoints
    "publication": "publication/",

    # Common Endpoints
    "assignee": "assignee/",
    "inventor": "inventor/",
    "location": "location/",

    # Classification Endpoints - CPC
    "cpc_class": "cpc_class/",
    "cpc_subclass": "cpc_subclass/",
    "cpc_group": "cpc_group/",
    "cpc_subgroup": "cpc_subgroup/",

    # Classification Endpoints - IPC
    "ipc": "ipc/",

    # Classification Endpoints - USPC
    "uspc_mainclass": "uspc_mainclass/",
    "uspc_subclass": "uspc_subclass/",

    # Classification Endpoints - WIPO
    "wipo": "wipo/",

    # Patent Text Endpoints
    "patent_brief_summary_text": "patent/brief_summary_text/",
    "patent_claim": "patent/claim/",
    "patent_detail_desc_text": "patent/detail_desc_text/",
    "patent_draw_desc_text": "patent/draw_desc_text/",

    # Publication Text Endpoints
    "publication_brief_summary_text": "publication/brief_summary_text/",
    "publication_claim": "publication/claim/",
    "publication_detail_desc_text": "publication/detail_desc_text/",
    "publication_draw_desc_text": "publication/draw_desc_text/",
}


# Common field sets for different endpoint types
COMMON_PATENT_FIELDS = [
    "patent_id",
    "patent_number",
    "patent_title",
    "patent_abstract",
    "patent_date",
    "patent_type",
    "patent_kind",
    "patent_num_claims",
    "patent_num_combined_citations",
]

COMMON_INVENTOR_FIELDS = [
    "inventor_id",
    "inventor_first_name",
    "inventor_last_name",
    "inventor_key_id",
]

COMMON_ASSIGNEE_FIELDS = [
    "assignee_id",
    "assignee_organization",
    "assignee_type",
    "assignee_first_name",
    "assignee_last_name",
    "assignee_key_id",
]

COMMON_LOCATION_FIELDS = [
    "location_id",
    "city",
    "state",
    "country",
    "latitude",
    "longitude",
]

COMMON_CPC_FIELDS = [
    "cpc_section_id",
    "cpc_subsection_id",
    "cpc_group_id",
    "cpc_subgroup_id",
    "cpc_category",
]


def get_endpoint_path(endpoint_name: str) -> str:
    """
    Get the API path for a given endpoint name.

    :param endpoint_name: The friendly endpoint name
    :return: The API path
    :raises ValueError: If the endpoint name is not found
    """
    if endpoint_name not in ENDPOINTS:
        raise ValueError(
            f"Unknown endpoint: {endpoint_name}. "
            f"Available endpoints: {', '.join(ENDPOINTS.keys())}"
        )
    return ENDPOINTS[endpoint_name]


def list_endpoints() -> list:
    """Return a list of all available endpoint names."""
    return list(ENDPOINTS.keys())


def get_common_fields(endpoint_name: str) -> list:
    """
    Get common fields for a given endpoint type.

    :param endpoint_name: The endpoint name
    :return: List of common field names for that endpoint type
    """
    if "patent" in endpoint_name and "publication" not in endpoint_name:
        return COMMON_PATENT_FIELDS
    elif "inventor" in endpoint_name:
        return COMMON_INVENTOR_FIELDS
    elif "assignee" in endpoint_name:
        return COMMON_ASSIGNEE_FIELDS
    elif "location" in endpoint_name:
        return COMMON_LOCATION_FIELDS
    elif "cpc" in endpoint_name:
        return COMMON_CPC_FIELDS
    else:
        return []
