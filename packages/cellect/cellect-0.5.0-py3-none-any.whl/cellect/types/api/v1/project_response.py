# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from ...._models import BaseModel

__all__ = ["ProjectResponse"]


class ProjectResponse(BaseModel):
    id: str
    """Project ID"""

    attributes: Optional[Dict[str, str]] = None
    """Project attributes"""
