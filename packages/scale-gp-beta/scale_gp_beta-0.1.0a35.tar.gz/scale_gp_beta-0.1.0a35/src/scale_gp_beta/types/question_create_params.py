# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr

__all__ = [
    "QuestionCreateParams",
    "CategoricalQuestionRequest",
    "CategoricalQuestionRequestConfiguration",
    "RatingQuestionRequest",
    "RatingQuestionRequestConfiguration",
    "NumberQuestionRequest",
    "NumberQuestionRequestConfiguration",
    "FreeTextQuestionRequest",
    "FreeTextQuestionRequestConfiguration",
    "FormQuestionRequest",
    "FormQuestionRequestConfiguration",
]


class CategoricalQuestionRequest(TypedDict, total=False):
    configuration: Required[CategoricalQuestionRequestConfiguration]

    name: Required[str]

    prompt: Required[str]
    """user-facing question prompt"""

    question_type: Literal["categorical"]


class CategoricalQuestionRequestConfiguration(TypedDict, total=False):
    choices: Required[SequenceNotStr[str]]
    """Categorical answer choices (must contain at least one entry)"""


class RatingQuestionRequest(TypedDict, total=False):
    configuration: Required[RatingQuestionRequestConfiguration]

    name: Required[str]

    prompt: Required[str]
    """user-facing question prompt"""

    question_type: Literal["rating"]


class RatingQuestionRequestConfiguration(TypedDict, total=False):
    max_label: Required[str]
    """Label shown for the maximum rating"""

    min_label: Required[str]
    """Label shown for the minimum rating"""

    steps: Required[int]
    """Number of discrete points on the scale (e.g., 5 for a 1–5 scale)"""


class NumberQuestionRequest(TypedDict, total=False):
    name: Required[str]

    prompt: Required[str]
    """user-facing question prompt"""

    configuration: NumberQuestionRequestConfiguration

    question_type: Literal["number"]


class NumberQuestionRequestConfiguration(TypedDict, total=False):
    max: float
    """Maximum value for the number"""

    min: float
    """Minimum value for the number"""


class FreeTextQuestionRequest(TypedDict, total=False):
    name: Required[str]

    prompt: Required[str]
    """user-facing question prompt"""

    configuration: FreeTextQuestionRequestConfiguration

    question_type: Literal["free_text"]


class FreeTextQuestionRequestConfiguration(TypedDict, total=False):
    max_length: int
    """Maximum characters allowed"""

    min_length: int
    """Minimum characters required"""


class FormQuestionRequest(TypedDict, total=False):
    configuration: Required[FormQuestionRequestConfiguration]

    name: Required[str]

    prompt: Required[str]
    """user-facing question prompt"""

    question_type: Literal["form"]


class FormQuestionRequestConfiguration(TypedDict, total=False):
    form_schema: Required[Dict[str, object]]
    """The JSON schema of the desired form object"""


QuestionCreateParams: TypeAlias = Union[
    CategoricalQuestionRequest,
    RatingQuestionRequest,
    NumberQuestionRequest,
    FreeTextQuestionRequest,
    FormQuestionRequest,
]
