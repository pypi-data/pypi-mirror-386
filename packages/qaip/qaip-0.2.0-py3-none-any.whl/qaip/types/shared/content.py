# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel
from .file_type import FileType
from .source_type import SourceType

__all__ = ["Content"]


class Content(BaseModel):
    id: str
    """Content ID"""

    file_type: FileType
    """The type of the source file"""

    page_number: int
    """Page number for paginated documents like PDFs.

    Set to 0 for sources without page numbers
    """

    source_type: SourceType
    """The type of the source"""

    text: str
    """Content chunk from the source"""

    timestamp: int
    """Unix timestamp when the content was indexed"""

    title: str
    """Title of the content or document"""

    url: str
    """Source URL of the content"""

    keywords: Optional[List[str]] = None
