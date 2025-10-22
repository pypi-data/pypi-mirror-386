# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr
from .shared.file_type import FileType
from .shared.source_type import SourceType

__all__ = ["ClientSearchParams"]


class ClientSearchParams(TypedDict, total=False):
    query: Required[str]
    """Search query string"""

    date_from: int
    """Start date for content search (Unix timestamp in seconds)"""

    date_to: int
    """End date for content search (Unix timestamp in seconds)"""

    domains: SequenceNotStr[str]
    """Array of domains to search within (supports partial matching)"""

    file_types: List[FileType]

    limit: int
    """Maximum number of results to return"""

    offset: int
    """Number of results to skip"""

    source_types: List[SourceType]

    tag_ids: SequenceNotStr[str]
    """target tag IDs to be obtained"""

    tags: SequenceNotStr[str]
    """target tag names to be obtained"""
