# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from ..._types import SequenceNotStr

__all__ = ["DocumentUploadFromURLParams"]


class DocumentUploadFromURLParams(TypedDict, total=False):
    urls: Required[SequenceNotStr[str]]
    """URLs to download documents from"""

    workspace_ext_id: Required[str]

    config_ext_id: Optional[str]
    """Configuration to use for processing"""

    shared: bool
    """Whether the document should be shared with workspace members"""
