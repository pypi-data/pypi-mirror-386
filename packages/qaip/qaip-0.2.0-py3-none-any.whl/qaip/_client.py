# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, List, Mapping, Iterable
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from .types import client_search_params, client_extract_params, client_completion_params
from ._types import (
    Body,
    Omit,
    Query,
    Headers,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    SequenceNotStr,
    omit,
    not_given,
)
from ._utils import (
    is_given,
    maybe_transform,
    get_async_library,
    async_maybe_transform,
)
from ._version import __version__
from ._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import QaipError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
    make_request_options,
)
from .types.shared.content import Content
from .types.search_response import SearchResponse
from .types.extract_response import ExtractResponse
from .types.shared.file_type import FileType
from .types.shared.source_type import SourceType
from .types.completion_response import CompletionResponse

__all__ = ["Timeout", "Transport", "ProxiesTypes", "RequestOptions", "Qaip", "AsyncQaip", "Client", "AsyncClient"]


class Qaip(SyncAPIClient):
    with_raw_response: QaipWithRawResponse
    with_streaming_response: QaipWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Qaip client instance.

        This automatically infers the `api_key` argument from the `QAIP_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("QAIP_API_KEY")
        if api_key is None:
            raise QaipError(
                "The api_key client option must be set either by passing api_key to the client or by setting the QAIP_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("QAIP_BASE_URL")
        if base_url is None:
            base_url = f"https://developer.qaip.com/api/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.with_raw_response = QaipWithRawResponse(self)
        self.with_streaming_response = QaipWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"x-api-key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    def completion(
        self,
        *,
        messages: Iterable[client_completion_params.Message],
        citation: bool | Omit = omit,
        date_from: int | Omit = omit,
        date_to: int | Omit = omit,
        domains: SequenceNotStr[str] | Omit = omit,
        file_types: List[FileType] | Omit = omit,
        source_types: List[SourceType] | Omit = omit,
        stream: bool | Omit = omit,
        tag_ids: SequenceNotStr[str] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CompletionResponse:
        """Generates a completion based on the input messages and retrieval chunks.

        If the
        'stream' parameter is set to true, the response is returned as a stream of plain
        text (text/plain).

        Args:
          messages: The messages to generate completion for

          citation: Whether to include citations in the response

          date_from: Start date for content search (Unix timestamp in seconds)

          date_to: End date for content search (Unix timestamp in seconds)

          domains: Array of domains to search within (supports partial matching)

          stream: Whether to stream the response. If true, the response is sent as a stream using
              the 'text/plain' content type.

          tag_ids: target tag IDs to be obtained

          tags: target tag names to be obtained

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self.post(
            "/completions",
            body=maybe_transform(
                {
                    "messages": messages,
                    "citation": citation,
                    "date_from": date_from,
                    "date_to": date_to,
                    "domains": domains,
                    "file_types": file_types,
                    "source_types": source_types,
                    "stream": stream,
                    "tag_ids": tag_ids,
                    "tags": tags,
                },
                client_completion_params.ClientCompletionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CompletionResponse,
        )

    def content(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Content:
        """
        Get through indexed content

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self.get(
            f"/contents/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Content,
        )

    def extract(
        self,
        *,
        schema: object,
        date_from: int | Omit = omit,
        date_to: int | Omit = omit,
        domains: SequenceNotStr[str] | Omit = omit,
        file_types: List[FileType] | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        prompt: str | Omit = omit,
        source_types: List[SourceType] | Omit = omit,
        tag_ids: SequenceNotStr[str] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExtractResponse:
        """
        Performs data extraction using LLM based on the specified data source, filter
        conditions, and JSON schema. Retrieves chunked data and uses the schema to
        extract and return the result as JSON via LLM.

        Args:
          schema: JSON Schema for the data to be extracted.

          date_from: Start date for content search (Unix timestamp in seconds)

          date_to: End date for content search (Unix timestamp in seconds)

          prompt: Additional prompt for the LLM (optional, if not specified, a default prompt in
              Japanese will be used).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self.post(
            "/extract",
            body=maybe_transform(
                {
                    "schema": schema,
                    "date_from": date_from,
                    "date_to": date_to,
                    "domains": domains,
                    "file_types": file_types,
                    "limit": limit,
                    "offset": offset,
                    "prompt": prompt,
                    "source_types": source_types,
                    "tag_ids": tag_ids,
                    "tags": tags,
                },
                client_extract_params.ClientExtractParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExtractResponse,
        )

    def search(
        self,
        *,
        query: str,
        date_from: int | Omit = omit,
        date_to: int | Omit = omit,
        domains: SequenceNotStr[str] | Omit = omit,
        file_types: List[FileType] | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        source_types: List[SourceType] | Omit = omit,
        tag_ids: SequenceNotStr[str] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchResponse:
        """
        Searches through indexed content using query

        Args:
          query: Search query string

          date_from: Start date for content search (Unix timestamp in seconds)

          date_to: End date for content search (Unix timestamp in seconds)

          domains: Array of domains to search within (supports partial matching)

          limit: Maximum number of results to return

          offset: Number of results to skip

          tag_ids: target tag IDs to be obtained

          tags: target tag names to be obtained

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self.post(
            "/search",
            body=maybe_transform(
                {
                    "query": query,
                    "date_from": date_from,
                    "date_to": date_to,
                    "domains": domains,
                    "file_types": file_types,
                    "limit": limit,
                    "offset": offset,
                    "source_types": source_types,
                    "tag_ids": tag_ids,
                    "tags": tags,
                },
                client_search_params.ClientSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchResponse,
        )

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncQaip(AsyncAPIClient):
    with_raw_response: AsyncQaipWithRawResponse
    with_streaming_response: AsyncQaipWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncQaip client instance.

        This automatically infers the `api_key` argument from the `QAIP_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("QAIP_API_KEY")
        if api_key is None:
            raise QaipError(
                "The api_key client option must be set either by passing api_key to the client or by setting the QAIP_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("QAIP_BASE_URL")
        if base_url is None:
            base_url = f"https://developer.qaip.com/api/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.with_raw_response = AsyncQaipWithRawResponse(self)
        self.with_streaming_response = AsyncQaipWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"x-api-key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    async def completion(
        self,
        *,
        messages: Iterable[client_completion_params.Message],
        citation: bool | Omit = omit,
        date_from: int | Omit = omit,
        date_to: int | Omit = omit,
        domains: SequenceNotStr[str] | Omit = omit,
        file_types: List[FileType] | Omit = omit,
        source_types: List[SourceType] | Omit = omit,
        stream: bool | Omit = omit,
        tag_ids: SequenceNotStr[str] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CompletionResponse:
        """Generates a completion based on the input messages and retrieval chunks.

        If the
        'stream' parameter is set to true, the response is returned as a stream of plain
        text (text/plain).

        Args:
          messages: The messages to generate completion for

          citation: Whether to include citations in the response

          date_from: Start date for content search (Unix timestamp in seconds)

          date_to: End date for content search (Unix timestamp in seconds)

          domains: Array of domains to search within (supports partial matching)

          stream: Whether to stream the response. If true, the response is sent as a stream using
              the 'text/plain' content type.

          tag_ids: target tag IDs to be obtained

          tags: target tag names to be obtained

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self.post(
            "/completions",
            body=await async_maybe_transform(
                {
                    "messages": messages,
                    "citation": citation,
                    "date_from": date_from,
                    "date_to": date_to,
                    "domains": domains,
                    "file_types": file_types,
                    "source_types": source_types,
                    "stream": stream,
                    "tag_ids": tag_ids,
                    "tags": tags,
                },
                client_completion_params.ClientCompletionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CompletionResponse,
        )

    async def content(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Content:
        """
        Get through indexed content

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self.get(
            f"/contents/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Content,
        )

    async def extract(
        self,
        *,
        schema: object,
        date_from: int | Omit = omit,
        date_to: int | Omit = omit,
        domains: SequenceNotStr[str] | Omit = omit,
        file_types: List[FileType] | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        prompt: str | Omit = omit,
        source_types: List[SourceType] | Omit = omit,
        tag_ids: SequenceNotStr[str] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExtractResponse:
        """
        Performs data extraction using LLM based on the specified data source, filter
        conditions, and JSON schema. Retrieves chunked data and uses the schema to
        extract and return the result as JSON via LLM.

        Args:
          schema: JSON Schema for the data to be extracted.

          date_from: Start date for content search (Unix timestamp in seconds)

          date_to: End date for content search (Unix timestamp in seconds)

          prompt: Additional prompt for the LLM (optional, if not specified, a default prompt in
              Japanese will be used).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self.post(
            "/extract",
            body=await async_maybe_transform(
                {
                    "schema": schema,
                    "date_from": date_from,
                    "date_to": date_to,
                    "domains": domains,
                    "file_types": file_types,
                    "limit": limit,
                    "offset": offset,
                    "prompt": prompt,
                    "source_types": source_types,
                    "tag_ids": tag_ids,
                    "tags": tags,
                },
                client_extract_params.ClientExtractParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExtractResponse,
        )

    async def search(
        self,
        *,
        query: str,
        date_from: int | Omit = omit,
        date_to: int | Omit = omit,
        domains: SequenceNotStr[str] | Omit = omit,
        file_types: List[FileType] | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        source_types: List[SourceType] | Omit = omit,
        tag_ids: SequenceNotStr[str] | Omit = omit,
        tags: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchResponse:
        """
        Searches through indexed content using query

        Args:
          query: Search query string

          date_from: Start date for content search (Unix timestamp in seconds)

          date_to: End date for content search (Unix timestamp in seconds)

          domains: Array of domains to search within (supports partial matching)

          limit: Maximum number of results to return

          offset: Number of results to skip

          tag_ids: target tag IDs to be obtained

          tags: target tag names to be obtained

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self.post(
            "/search",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "date_from": date_from,
                    "date_to": date_to,
                    "domains": domains,
                    "file_types": file_types,
                    "limit": limit,
                    "offset": offset,
                    "source_types": source_types,
                    "tag_ids": tag_ids,
                    "tags": tags,
                },
                client_search_params.ClientSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchResponse,
        )

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class QaipWithRawResponse:
    def __init__(self, client: Qaip) -> None:
        self.completion = to_raw_response_wrapper(
            client.completion,
        )
        self.content = to_raw_response_wrapper(
            client.content,
        )
        self.extract = to_raw_response_wrapper(
            client.extract,
        )
        self.search = to_raw_response_wrapper(
            client.search,
        )


class AsyncQaipWithRawResponse:
    def __init__(self, client: AsyncQaip) -> None:
        self.completion = async_to_raw_response_wrapper(
            client.completion,
        )
        self.content = async_to_raw_response_wrapper(
            client.content,
        )
        self.extract = async_to_raw_response_wrapper(
            client.extract,
        )
        self.search = async_to_raw_response_wrapper(
            client.search,
        )


class QaipWithStreamedResponse:
    def __init__(self, client: Qaip) -> None:
        self.completion = to_streamed_response_wrapper(
            client.completion,
        )
        self.content = to_streamed_response_wrapper(
            client.content,
        )
        self.extract = to_streamed_response_wrapper(
            client.extract,
        )
        self.search = to_streamed_response_wrapper(
            client.search,
        )


class AsyncQaipWithStreamedResponse:
    def __init__(self, client: AsyncQaip) -> None:
        self.completion = async_to_streamed_response_wrapper(
            client.completion,
        )
        self.content = async_to_streamed_response_wrapper(
            client.content,
        )
        self.extract = async_to_streamed_response_wrapper(
            client.extract,
        )
        self.search = async_to_streamed_response_wrapper(
            client.search,
        )


Client = Qaip

AsyncClient = AsyncQaip
