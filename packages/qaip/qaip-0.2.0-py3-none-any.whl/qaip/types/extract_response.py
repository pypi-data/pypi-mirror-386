# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["ExtractResponse"]


class ExtractResponse(BaseModel):
    created: int
    """抽出実行時刻（Unix timestamp）"""

    result: object
    """Extraction result as a JSON object conforming to the provided schema."""
