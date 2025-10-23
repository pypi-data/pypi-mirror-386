# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal, TypeAlias

__all__ = ["SpanType"]

SpanType: TypeAlias = Literal[
    "TEXT_INPUT",
    "TEXT_OUTPUT",
    "COMPLETION_INPUT",
    "COMPLETION",
    "KB_RETRIEVAL",
    "KB_INPUT",
    "RERANKING",
    "EXTERNAL_ENDPOINT",
    "PROMPT_ENGINEERING",
    "DOCUMENT_INPUT",
    "MAP_REDUCE",
    "DOCUMENT_SEARCH",
    "DOCUMENT_PROMPT",
    "CUSTOM",
    "CODE_EXECUTION",
    "DATA_MANIPULATION",
    "EVALUATION",
    "FILE_RETRIEVAL",
    "KB_ADD_CHUNK",
    "KB_MANAGEMENT",
    "GUARDRAIL",
    "TRACER",
    "AGENT_TRACER",
    "AGENT_WORKFLOW",
    "STANDALONE",
]
