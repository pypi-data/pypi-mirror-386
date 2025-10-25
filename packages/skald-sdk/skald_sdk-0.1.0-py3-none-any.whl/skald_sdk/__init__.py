"""
Skald Python SDK

Official Python SDK for Skald - The AI-powered knowledge management platform.
"""

from skald_sdk.client import Skald
from skald_sdk.types import (
    MemoData,
    UpdateMemoData,
    ListMemosParams,
    SearchRequest,
    ChatRequest,
    GenerateDocRequest,
    CreateMemoResponse,
    UpdateMemoResponse,
    Memo,
    MemoListItem,
    ListMemosResponse,
    SearchResponse,
    SearchResult,
    ChatResponse,
    ChatStreamEvent,
    GenerateDocResponse,
    GenerateDocStreamEvent,
    Filter,
    IdType,
    SearchMethod,
    FilterOperator,
    FilterType,
)

__version__ = "0.1.3"
__all__ = [
    "Skald",
    "MemoData",
    "UpdateMemoData",
    "ListMemosParams",
    "SearchRequest",
    "ChatRequest",
    "GenerateDocRequest",
    "CreateMemoResponse",
    "UpdateMemoResponse",
    "Memo",
    "MemoListItem",
    "ListMemosResponse",
    "SearchResponse",
    "SearchResult",
    "ChatResponse",
    "ChatStreamEvent",
    "GenerateDocResponse",
    "GenerateDocStreamEvent",
    "Filter",
    "IdType",
    "SearchMethod",
    "FilterOperator",
    "FilterType",
]
