"""
Type definitions for the Skald SDK.

This module contains all the type definitions used throughout the SDK,
including request/response models and enums.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired

# Type aliases for enums
IdType = Literal["memo_uuid", "reference_id"]
SearchMethod = Literal["chunk_vector_search", "title_contains", "title_startswith"]
FilterOperator = Literal["eq", "neq", "contains", "startswith", "endswith", "in", "not_in"]
FilterType = Literal["native_field", "custom_metadata"]


# Input Types


class MemoData(TypedDict):
    """Data required to create a new memo."""

    title: str
    content: str
    metadata: NotRequired[Dict[str, Any]]
    reference_id: NotRequired[str]
    tags: NotRequired[List[str]]
    source: NotRequired[str]
    expiration_date: NotRequired[str]


class UpdateMemoData(TypedDict, total=False):
    """Data for updating an existing memo."""

    title: str
    content: str
    metadata: Dict[str, Any]
    client_reference_id: str
    source: str
    expiration_date: str


class ListMemosParams(TypedDict, total=False):
    """Parameters for listing memos."""

    page: int
    page_size: int


class Filter(TypedDict):
    """Filter for search and query operations."""

    field: str
    operator: FilterOperator
    value: Union[str, List[str]]
    filter_type: FilterType


class SearchRequest(TypedDict):
    """Request parameters for search operations."""

    query: str
    search_method: SearchMethod
    limit: NotRequired[int]
    filters: NotRequired[List[Filter]]


class ChatRequest(TypedDict):
    """Request parameters for chat operations."""

    query: str
    filters: NotRequired[List[Filter]]


class GenerateDocRequest(TypedDict):
    """Request parameters for document generation."""

    prompt: str
    rules: NotRequired[str]
    filters: NotRequired[List[Filter]]


# Output Types


class CreateMemoResponse(TypedDict):
    """Response from creating a memo."""

    ok: bool


class UpdateMemoResponse(TypedDict):
    """Response from updating a memo."""

    ok: bool


class Memo(TypedDict):
    """Complete memo details."""

    uuid: str
    created_at: str
    updated_at: str
    title: str
    content: str
    summary: str
    content_length: int
    metadata: Dict[str, Any]
    client_reference_id: Optional[str]
    source: Optional[str]
    type: str
    expiration_date: Optional[str]
    archived: bool
    pending: bool


class MemoListItem(TypedDict):
    """Lightweight memo information for list responses."""

    uuid: str
    created_at: str
    updated_at: str
    title: str
    summary: str
    content_length: int
    metadata: Dict[str, Any]
    client_reference_id: Optional[str]


class ListMemosResponse(TypedDict):
    """Response from listing memos."""

    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[MemoListItem]


class SearchResult(TypedDict):
    """A single search result."""

    uuid: str
    title: str
    summary: str
    content_snippet: str
    distance: Optional[float]


class SearchResponse(TypedDict):
    """Response from search operations."""

    results: List[SearchResult]


class ChatResponse(TypedDict):
    """Response from chat operations."""

    ok: bool
    response: str
    intermediate_steps: List[Any]


class ChatStreamEvent(TypedDict):
    """Event from streaming chat operations."""

    type: Literal["token", "done"]
    content: NotRequired[str]


class GenerateDocResponse(TypedDict):
    """Response from document generation."""

    ok: bool
    response: str
    intermediate_steps: List[Any]


class GenerateDocStreamEvent(TypedDict):
    """Event from streaming document generation."""

    type: Literal["token", "done"]
    content: NotRequired[str]
