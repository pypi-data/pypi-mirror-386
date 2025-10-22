# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from qaip import Qaip, AsyncQaip
from qaip.types import (
    SearchResponse,
    ExtractResponse,
    CompletionResponse,
)
from tests.utils import assert_matches_type
from qaip.types.shared import Content

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestClient:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_completion(self, client: Qaip) -> None:
        client_ = client.completion(
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        )
        assert_matches_type(CompletionResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_completion_with_all_params(self, client: Qaip) -> None:
        client_ = client.completion(
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
            citation=True,
            date_from=1735639200,
            date_to=1735639200,
            domains=["string"],
            file_types=["html"],
            source_types=["crawl"],
            stream=True,
            tag_ids=["string"],
            tags=["string"],
        )
        assert_matches_type(CompletionResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_completion(self, client: Qaip) -> None:
        response = client.with_raw_response.completion(
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client_ = response.parse()
        assert_matches_type(CompletionResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_completion(self, client: Qaip) -> None:
        with client.with_streaming_response.completion(
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client_ = response.parse()
            assert_matches_type(CompletionResponse, client_, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_content(self, client: Qaip) -> None:
        client_ = client.content(
            "id",
        )
        assert_matches_type(Content, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_content(self, client: Qaip) -> None:
        response = client.with_raw_response.content(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client_ = response.parse()
        assert_matches_type(Content, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_content(self, client: Qaip) -> None:
        with client.with_streaming_response.content(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client_ = response.parse()
            assert_matches_type(Content, client_, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_content(self, client: Qaip) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.with_raw_response.content(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_extract(self, client: Qaip) -> None:
        client_ = client.extract(
            schema={},
        )
        assert_matches_type(ExtractResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_extract_with_all_params(self, client: Qaip) -> None:
        client_ = client.extract(
            schema={},
            date_from=1735639200,
            date_to=1735639200,
            domains=["string"],
            file_types=["html"],
            limit=1,
            offset=0,
            prompt="prompt",
            source_types=["crawl"],
            tag_ids=["string"],
            tags=["string"],
        )
        assert_matches_type(ExtractResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_extract(self, client: Qaip) -> None:
        response = client.with_raw_response.extract(
            schema={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client_ = response.parse()
        assert_matches_type(ExtractResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_extract(self, client: Qaip) -> None:
        with client.with_streaming_response.extract(
            schema={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client_ = response.parse()
            assert_matches_type(ExtractResponse, client_, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: Qaip) -> None:
        client_ = client.search(
            query="machine learning and artificial intelligence",
        )
        assert_matches_type(SearchResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search_with_all_params(self, client: Qaip) -> None:
        client_ = client.search(
            query="machine learning and artificial intelligence",
            date_from=1735639200,
            date_to=1735639200,
            domains=["example.com", "blog.example.com"],
            file_types=["html"],
            limit=10,
            offset=0,
            source_types=["crawl"],
            tag_ids=["string"],
            tags=["string"],
        )
        assert_matches_type(SearchResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: Qaip) -> None:
        response = client.with_raw_response.search(
            query="machine learning and artificial intelligence",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client_ = response.parse()
        assert_matches_type(SearchResponse, client_, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: Qaip) -> None:
        with client.with_streaming_response.search(
            query="machine learning and artificial intelligence",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client_ = response.parse()
            assert_matches_type(SearchResponse, client_, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncClient:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_completion(self, async_client: AsyncQaip) -> None:
        client = await async_client.completion(
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        )
        assert_matches_type(CompletionResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_completion_with_all_params(self, async_client: AsyncQaip) -> None:
        client = await async_client.completion(
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
            citation=True,
            date_from=1735639200,
            date_to=1735639200,
            domains=["string"],
            file_types=["html"],
            source_types=["crawl"],
            stream=True,
            tag_ids=["string"],
            tags=["string"],
        )
        assert_matches_type(CompletionResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_completion(self, async_client: AsyncQaip) -> None:
        response = await async_client.with_raw_response.completion(
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client = await response.parse()
        assert_matches_type(CompletionResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_completion(self, async_client: AsyncQaip) -> None:
        async with async_client.with_streaming_response.completion(
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client = await response.parse()
            assert_matches_type(CompletionResponse, client, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_content(self, async_client: AsyncQaip) -> None:
        client = await async_client.content(
            "id",
        )
        assert_matches_type(Content, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_content(self, async_client: AsyncQaip) -> None:
        response = await async_client.with_raw_response.content(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client = await response.parse()
        assert_matches_type(Content, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_content(self, async_client: AsyncQaip) -> None:
        async with async_client.with_streaming_response.content(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client = await response.parse()
            assert_matches_type(Content, client, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_content(self, async_client: AsyncQaip) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.with_raw_response.content(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_extract(self, async_client: AsyncQaip) -> None:
        client = await async_client.extract(
            schema={},
        )
        assert_matches_type(ExtractResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_extract_with_all_params(self, async_client: AsyncQaip) -> None:
        client = await async_client.extract(
            schema={},
            date_from=1735639200,
            date_to=1735639200,
            domains=["string"],
            file_types=["html"],
            limit=1,
            offset=0,
            prompt="prompt",
            source_types=["crawl"],
            tag_ids=["string"],
            tags=["string"],
        )
        assert_matches_type(ExtractResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_extract(self, async_client: AsyncQaip) -> None:
        response = await async_client.with_raw_response.extract(
            schema={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client = await response.parse()
        assert_matches_type(ExtractResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_extract(self, async_client: AsyncQaip) -> None:
        async with async_client.with_streaming_response.extract(
            schema={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client = await response.parse()
            assert_matches_type(ExtractResponse, client, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncQaip) -> None:
        client = await async_client.search(
            query="machine learning and artificial intelligence",
        )
        assert_matches_type(SearchResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncQaip) -> None:
        client = await async_client.search(
            query="machine learning and artificial intelligence",
            date_from=1735639200,
            date_to=1735639200,
            domains=["example.com", "blog.example.com"],
            file_types=["html"],
            limit=10,
            offset=0,
            source_types=["crawl"],
            tag_ids=["string"],
            tags=["string"],
        )
        assert_matches_type(SearchResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncQaip) -> None:
        response = await async_client.with_raw_response.search(
            query="machine learning and artificial intelligence",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client = await response.parse()
        assert_matches_type(SearchResponse, client, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncQaip) -> None:
        async with async_client.with_streaming_response.search(
            query="machine learning and artificial intelligence",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client = await response.parse()
            assert_matches_type(SearchResponse, client, path=["response"])

        assert cast(Any, response.is_closed) is True
