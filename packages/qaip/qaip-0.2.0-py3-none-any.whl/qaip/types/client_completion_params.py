# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable
from typing_extensions import Literal, Required, TypedDict

from .._types import SequenceNotStr
from .shared.file_type import FileType
from .shared.source_type import SourceType

__all__ = ["ClientCompletionParams", "Message"]


class ClientCompletionParams(TypedDict, total=False):
    messages: Required[Iterable[Message]]
    """The messages to generate completion for"""

    citation: bool
    """Whether to include citations in the response"""

    date_from: int
    """Start date for content search (Unix timestamp in seconds)"""

    date_to: int
    """End date for content search (Unix timestamp in seconds)"""

    domains: SequenceNotStr[str]
    """Array of domains to search within (supports partial matching)"""

    file_types: List[FileType]

    source_types: List[SourceType]

    stream: bool
    """Whether to stream the response.

    If true, the response is sent as a stream using the 'text/plain' content type.
    """

    tag_ids: SequenceNotStr[str]
    """target tag IDs to be obtained"""

    tags: SequenceNotStr[str]
    """target tag names to be obtained"""


class Message(TypedDict, total=False):
    content: Required[str]
    """The content of the message"""

    role: Required[Literal["system", "user", "assistant"]]
    """The role of the message sender"""
