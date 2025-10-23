# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from .dataset import Dataset
from .._models import BaseModel
from .shared.identity import Identity

__all__ = ["Evaluation"]


class Evaluation(BaseModel):
    id: str

    created_at: datetime

    created_by: Identity
    """The identity that created the entity."""

    datasets: List[Dataset]

    name: str

    status: Literal["failed", "completed", "running"]

    tags: List[str]
    """The tags associated with the entity"""

    archived_at: Optional[datetime] = None

    description: Optional[str] = None

    metadata: Optional[Dict[str, object]] = None
    """Metadata key-value pairs for the evaluation"""

    object: Optional[Literal["evaluation"]] = None

    status_reason: Optional[str] = None
    """Reason for evaluation status"""

    tasks: Optional[List["EvaluationTask"]] = None
    """Tasks executed during evaluation. Populated with optional `task` view."""


from .evaluation_task import EvaluationTask
