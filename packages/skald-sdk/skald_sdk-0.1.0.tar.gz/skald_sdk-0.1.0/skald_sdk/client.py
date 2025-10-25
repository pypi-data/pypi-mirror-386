"""
Skald Python SDK Client

Main client implementation for interacting with the Skald API.
"""

import json
from typing import AsyncIterator, Optional
from urllib.parse import quote

import httpx

from skald_sdk.types import (
    ChatRequest,
    ChatResponse,
    ChatStreamEvent,
    CreateMemoResponse,
    GenerateDocRequest,
    GenerateDocResponse,
    GenerateDocStreamEvent,
    IdType,
    ListMemosParams,
    ListMemosResponse,
    Memo,
    MemoData,
    SearchRequest,
    SearchResponse,
    UpdateMemoData,
    UpdateMemoResponse,
)


class Skald:
    """
    Official Python SDK for Skald - The AI-powered knowledge management platform.

    This SDK provides methods to create, read, update, and delete memos, as well as
    perform semantic search, chat with your knowledge base, and generate documents.

    Args:
        api_key: Your Skald API key for authentication
        base_url: The base URL for the Skald API (default: https://api.useskald.com)

    Example:
        >>> skald = Skald("your-api-key")
        >>> await skald.create_memo({
        ...     "title": "Meeting Notes",
        ...     "content": "Discussion about Q1 goals..."
        ... })
    """

    def __init__(self, api_key: str, base_url: str = "https://api.useskald.com") -> None:
        """
        Initialize the Skald client.

        Args:
            api_key: Your Skald API key for authentication
            base_url: The base URL for the Skald API (default: https://api.useskald.com)
        """
        self._api_key = api_key
        # Remove trailing slashes from base_url
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self._api_key}",
            },
            timeout=30.0,
        )

    async def __aenter__(self) -> "Skald":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,  # type: ignore
    ) -> httpx.Response:
        """
        Make an HTTP request to the Skald API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint path
            json_data: Optional JSON data for request body

        Returns:
            The HTTP response

        Raises:
            Exception: If the API returns an error status code
        """
        url = f"{self._base_url}{endpoint}"
        response = await self._client.request(method, url, json=json_data)

        if not response.is_success:
            error_text = response.text
            raise Exception(f"Skald API error ({response.status_code}): {error_text}")

        return response

    # CRUD Operations

    async def create_memo(self, memo_data: MemoData) -> CreateMemoResponse:
        """
        Create a new memo in your Skald knowledge base.

        The memo will be automatically summarized, chunked, and indexed for search.

        Args:
            memo_data: The memo data including title, content, and optional metadata

        Returns:
            Response indicating success

        Raises:
            Exception: If the API request fails

        Example:
            >>> response = await skald.create_memo({
            ...     "title": "Product Requirements",
            ...     "content": "We need to build...",
            ...     "metadata": {"priority": "high"},
            ...     "tags": ["product", "planning"],
            ...     "source": "notion"
            ... })
        """
        # Auto-initialize metadata to empty dict if not provided
        data = dict(memo_data)
        if "metadata" not in data:
            data["metadata"] = {}

        response = await self._request("POST", "/api/v1/memo", json_data=data)
        return response.json()

    async def get_memo(
        self, memo_id: str, id_type: IdType = "memo_uuid"
    ) -> Memo:
        """
        Retrieve a memo by its ID.

        Args:
            memo_id: The memo's UUID or reference ID
            id_type: Type of ID provided - 'memo_uuid' or 'reference_id' (default: 'memo_uuid')

        Returns:
            Complete memo details including content, tags, and chunks

        Raises:
            Exception: If the API request fails or ID type is invalid

        Example:
            >>> memo = await skald.get_memo("550e8400-e29b-41d4-a716-446655440000")
            >>> memo_by_ref = await skald.get_memo("my-ref-123", id_type="reference_id")
        """
        # Validate id_type
        if id_type not in ("memo_uuid", "reference_id"):
            raise ValueError(f"Invalid id_type: {id_type}")

        # URL encode the memo_id
        encoded_id = quote(memo_id, safe="")
        endpoint = f"/api/v1/memo/{encoded_id}"

        # Only add id_type query param if not memo_uuid
        if id_type != "memo_uuid":
            endpoint += f"?id_type={id_type}"

        response = await self._request("GET", endpoint)
        return response.json()

    async def list_memos(
        self, params: Optional[ListMemosParams] = None
    ) -> ListMemosResponse:
        """
        List memos with pagination.

        Args:
            params: Optional pagination parameters (page, page_size)

        Returns:
            Paginated list of memos with metadata

        Raises:
            Exception: If the API request fails

        Example:
            >>> response = await skald.list_memos({"page": 1, "page_size": 50})
            >>> for memo in response["results"]:
            ...     print(memo["title"])
        """
        params = params or {}
        page = params.get("page", 1)
        page_size = params.get("page_size", 20)

        endpoint = f"/api/v1/memo?page={page}&page_size={page_size}"
        response = await self._request("GET", endpoint)
        return response.json()

    async def update_memo(
        self,
        memo_id: str,
        update_data: UpdateMemoData,
        id_type: IdType = "memo_uuid",
    ) -> UpdateMemoResponse:
        """
        Update an existing memo.

        If content is updated, the memo will be re-summarized, re-tagged, and re-chunked.

        Args:
            memo_id: The memo's UUID or reference ID
            update_data: Fields to update (all optional)
            id_type: Type of ID provided - 'memo_uuid' or 'reference_id' (default: 'memo_uuid')

        Returns:
            Response indicating success

        Raises:
            Exception: If the API request fails or ID type is invalid

        Example:
            >>> await skald.update_memo(
            ...     "550e8400-e29b-41d4-a716-446655440000",
            ...     {"title": "Updated Title", "content": "New content..."}
            ... )
        """
        # Validate id_type
        if id_type not in ("memo_uuid", "reference_id"):
            raise ValueError(f"Invalid id_type: {id_type}")

        # URL encode the memo_id
        encoded_id = quote(memo_id, safe="")
        endpoint = f"/api/v1/memo/{encoded_id}"

        # Only add id_type query param if not memo_uuid
        if id_type != "memo_uuid":
            endpoint += f"?id_type={id_type}"

        response = await self._request("PATCH", endpoint, json_data=update_data)
        return response.json()

    async def delete_memo(
        self, memo_id: str, id_type: IdType = "memo_uuid"
    ) -> None:
        """
        Delete a memo from your knowledge base.

        Args:
            memo_id: The memo's UUID or reference ID
            id_type: Type of ID provided - 'memo_uuid' or 'reference_id' (default: 'memo_uuid')

        Raises:
            Exception: If the API request fails or ID type is invalid

        Example:
            >>> await skald.delete_memo("550e8400-e29b-41d4-a716-446655440000")
        """
        # Validate id_type
        if id_type not in ("memo_uuid", "reference_id"):
            raise ValueError(f"Invalid id_type: {id_type}")

        # URL encode the memo_id
        encoded_id = quote(memo_id, safe="")
        endpoint = f"/api/v1/memo/{encoded_id}"

        # Only add id_type query param if not memo_uuid
        if id_type != "memo_uuid":
            endpoint += f"?id_type={id_type}"

        await self._request("DELETE", endpoint)

    # Search and Query Operations

    async def search(self, search_params: SearchRequest) -> SearchResponse:
        """
        Search your knowledge base using various methods.

        Args:
            search_params: Search parameters including query, method, and optional filters

        Returns:
            Search results with relevance scores

        Raises:
            Exception: If the API request fails

        Example:
            >>> results = await skald.search({
            ...     "query": "quarterly goals",
            ...     "search_method": "chunk_vector_search",
            ...     "limit": 10,
            ...     "filters": [{
            ...         "field": "source",
            ...         "operator": "eq",
            ...         "value": "notion",
            ...         "filter_type": "native_field"
            ...     }]
            ... })
        """
        response = await self._request("POST", "/api/v1/search", json_data=search_params)
        return response.json()

    async def chat(self, chat_params: ChatRequest) -> ChatResponse:
        """
        Chat with your knowledge base using natural language.

        Returns a complete response with citations in [[N]] format.

        Args:
            chat_params: Chat parameters including query and optional filters

        Returns:
            Chat response with citations and intermediate steps

        Raises:
            Exception: If the API request fails

        Example:
            >>> response = await skald.chat({
            ...     "query": "What were the main discussion points?",
            ...     "filters": [{
            ...         "field": "tags",
            ...         "operator": "in",
            ...         "value": ["meeting"],
            ...         "filter_type": "native_field"
            ...     }]
            ... })
            >>> print(response["response"])
        """
        data = dict(chat_params)
        data["stream"] = False
        response = await self._request("POST", "/api/v1/chat", json_data=data)
        return response.json()

    async def streamed_chat(
        self, chat_params: ChatRequest
    ) -> AsyncIterator[ChatStreamEvent]:
        """
        Chat with your knowledge base using streaming for real-time responses.

        Yields token events as they're generated, followed by a done event.

        Args:
            chat_params: Chat parameters including query and optional filters

        Yields:
            Stream events with type 'token' (contains content) or 'done'

        Raises:
            Exception: If the API request fails

        Example:
            >>> async for event in skald.streamed_chat({"query": "What are our goals?"}):
            ...     if event["type"] == "token":
            ...         print(event["content"], end="", flush=True)
            ...     elif event["type"] == "done":
            ...         print("\\nDone!")
        """
        data = dict(chat_params)
        data["stream"] = True

        url = f"{self._base_url}/api/v1/chat"
        async with self._client.stream(
            "POST",
            url,
            json=data,
        ) as response:
            if not response.is_success:
                error_text = await response.aread()
                raise Exception(
                    f"Skald API error ({response.status_code}): {error_text.decode()}"
                )

            buffer = ""
            async for chunk in response.aiter_bytes():
                buffer += chunk.decode("utf-8")
                lines = buffer.split("\n")
                buffer = lines.pop()  # Keep incomplete line in buffer

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith(": ping"):
                        continue
                    if line.startswith("data: "):
                        json_str = line[6:]  # Remove "data: " prefix
                        try:
                            event = json.loads(json_str)
                            yield event
                            if event.get("type") == "done":
                                return
                        except json.JSONDecodeError:
                            # Skip invalid JSON
                            continue

    async def generate_doc(
        self, generate_params: GenerateDocRequest
    ) -> GenerateDocResponse:
        """
        Generate a document based on your knowledge base.

        Returns a complete document with citations in [[N]] format.

        Args:
            generate_params: Generation parameters including prompt, optional rules, and filters

        Returns:
            Generated document response with citations

        Raises:
            Exception: If the API request fails

        Example:
            >>> response = await skald.generate_doc({
            ...     "prompt": "Create a PRD for a mobile app",
            ...     "rules": "Use formal language. Include: Overview, Requirements, Timeline"
            ... })
            >>> print(response["response"])
        """
        data = dict(generate_params)
        data["stream"] = False
        response = await self._request("POST", "/api/v1/generate", json_data=data)
        return response.json()

    async def streamed_generate_doc(
        self, generate_params: GenerateDocRequest
    ) -> AsyncIterator[GenerateDocStreamEvent]:
        """
        Generate a document with streaming for real-time generation.

        Yields token events as they're generated, followed by a done event.

        Args:
            generate_params: Generation parameters including prompt, optional rules, and filters

        Yields:
            Stream events with type 'token' (contains content) or 'done'

        Raises:
            Exception: If the API request fails

        Example:
            >>> async for event in skald.streamed_generate_doc({
            ...     "prompt": "Write a technical spec",
            ...     "rules": "Include Architecture and Security sections"
            ... }):
            ...     if event["type"] == "token":
            ...         print(event["content"], end="", flush=True)
        """
        data = dict(generate_params)
        data["stream"] = True

        url = f"{self._base_url}/api/v1/generate"
        async with self._client.stream(
            "POST",
            url,
            json=data,
        ) as response:
            if not response.is_success:
                error_text = await response.aread()
                raise Exception(
                    f"Skald API error ({response.status_code}): {error_text.decode()}"
                )

            buffer = ""
            async for chunk in response.aiter_bytes():
                buffer += chunk.decode("utf-8")
                lines = buffer.split("\n")
                buffer = lines.pop()  # Keep incomplete line in buffer

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith(": ping"):
                        continue
                    if line.startswith("data: "):
                        json_str = line[6:]  # Remove "data: " prefix
                        try:
                            event = json.loads(json_str)
                            yield event
                            if event.get("type") == "done":
                                return
                        except json.JSONDecodeError:
                            # Skip invalid JSON
                            continue
