# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["OmittedReasoningContent"]


class OmittedReasoningContent(BaseModel):
    signature: Optional[str] = None
    """A unique identifier for this reasoning step."""

    type: Optional[Literal["omitted_reasoning"]] = None
    """Indicates this is an omitted reasoning step."""
