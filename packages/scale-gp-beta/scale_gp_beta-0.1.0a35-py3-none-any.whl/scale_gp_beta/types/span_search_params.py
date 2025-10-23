# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .span_type import SpanType
from .span_status import SpanStatus

__all__ = ["SpanSearchParams"]


class SpanSearchParams(TypedDict, total=False):
    ending_before: str

    from_ts: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """The starting (oldest) timestamp in ISO format."""

    limit: int

    sort_order: Literal["asc", "desc"]

    starting_after: str

    to_ts: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """The ending (most recent) timestamp in ISO format."""

    application_variant_ids: SequenceNotStr[str]
    """Filter by application variant IDs"""

    assessment_types: SequenceNotStr[str]
    """Filter spans by traces that have assessments of these types"""

    excluded_span_ids: SequenceNotStr[str]
    """List of span IDs to exclude from results"""

    excluded_trace_ids: SequenceNotStr[str]
    """List of trace IDs to exclude from results"""

    extra_metadata: Dict[str, object]
    """Filter on custom metadata key-value pairs"""

    group_id: str
    """Filter by group ID"""

    max_duration_ms: int
    """Maximum span duration in milliseconds (inclusive)"""

    min_duration_ms: int
    """Minimum span duration in milliseconds (inclusive)"""

    names: SequenceNotStr[str]
    """Filter by trace/span name"""

    parents_only: bool
    """Only fetch spans that are the top-level (ie. have no parent_id)"""

    search_texts: SequenceNotStr[str]
    """Free text search across span input and output fields"""

    span_ids: SequenceNotStr[str]
    """Filter by span IDs"""

    statuses: List[SpanStatus]
    """Filter on span status"""

    trace_ids: SequenceNotStr[str]
    """Filter by trace IDs"""

    types: List[SpanType]
