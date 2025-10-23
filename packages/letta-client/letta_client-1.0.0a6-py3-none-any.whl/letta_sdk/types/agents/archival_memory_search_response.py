# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["ArchivalMemorySearchResponse", "Result"]


class Result(BaseModel):
    content: str
    """Text content of the archival memory passage"""

    timestamp: str
    """Timestamp of when the memory was created, formatted in agent's timezone"""

    tags: Optional[List[str]] = None
    """List of tags associated with this memory"""


class ArchivalMemorySearchResponse(BaseModel):
    count: int
    """Total number of results returned"""

    results: List[Result]
    """List of search results matching the query"""
