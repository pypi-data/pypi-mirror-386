# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel
from .shared.content import Content

__all__ = ["SearchResponse"]


class SearchResponse(BaseModel):
    created: int
    """The Unix timestamp (in seconds) of when the search was performed"""

    results: List[Content]
    """Array of search results"""
