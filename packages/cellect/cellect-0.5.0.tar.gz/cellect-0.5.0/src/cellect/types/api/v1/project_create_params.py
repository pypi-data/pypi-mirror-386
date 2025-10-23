# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ProjectCreateParams"]


class ProjectCreateParams(TypedDict, total=False):
    project_name: Required[str]
    """Project name"""
