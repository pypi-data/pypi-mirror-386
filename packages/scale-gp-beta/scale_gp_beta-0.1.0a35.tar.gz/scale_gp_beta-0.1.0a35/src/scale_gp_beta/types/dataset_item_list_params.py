# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["DatasetItemListParams"]


class DatasetItemListParams(TypedDict, total=False):
    dataset_id: str
    """Optional dataset identifier.

    Must be provided if a specific version is requested.
    """

    ending_before: str

    include_archived: bool

    limit: int

    sort_order: Literal["asc", "desc"]

    starting_after: str

    version: int
    """Optional dataset version.

    When unset, returns the latest version. Requires a valid dataset_id when set.
    """
