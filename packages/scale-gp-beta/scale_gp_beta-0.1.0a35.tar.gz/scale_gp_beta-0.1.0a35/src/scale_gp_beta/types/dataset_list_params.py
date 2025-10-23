# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

from .._types import SequenceNotStr

__all__ = ["DatasetListParams"]


class DatasetListParams(TypedDict, total=False):
    ending_before: str

    include_archived: bool

    limit: int

    name: str

    sort_order: Literal["asc", "desc"]

    starting_after: str

    tags: SequenceNotStr[str]
