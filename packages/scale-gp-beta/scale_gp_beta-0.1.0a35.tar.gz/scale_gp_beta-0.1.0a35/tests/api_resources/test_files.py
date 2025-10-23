# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from scale_gp_beta import SGPClient, AsyncSGPClient
from scale_gp_beta.types import File, FileDeleteResponse
from scale_gp_beta.pagination import SyncCursorPage, AsyncCursorPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestFiles:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: SGPClient) -> None:
        file = client.files.create(
            file=b"raw file contents",
        )
        assert_matches_type(File, file, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: SGPClient) -> None:
        response = client.files.with_raw_response.create(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(File, file, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: SGPClient) -> None:
        with client.files.with_streaming_response.create(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(File, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: SGPClient) -> None:
        file = client.files.retrieve(
            "file_id",
        )
        assert_matches_type(File, file, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: SGPClient) -> None:
        response = client.files.with_raw_response.retrieve(
            "file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(File, file, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: SGPClient) -> None:
        with client.files.with_streaming_response.retrieve(
            "file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(File, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: SGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            client.files.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_update(self, client: SGPClient) -> None:
        file = client.files.update(
            file_id="file_id",
        )
        assert_matches_type(File, file, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: SGPClient) -> None:
        file = client.files.update(
            file_id="file_id",
            tags={"foo": "bar"},
        )
        assert_matches_type(File, file, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: SGPClient) -> None:
        response = client.files.with_raw_response.update(
            file_id="file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(File, file, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: SGPClient) -> None:
        with client.files.with_streaming_response.update(
            file_id="file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(File, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: SGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            client.files.with_raw_response.update(
                file_id="",
            )

    @parametrize
    def test_method_list(self, client: SGPClient) -> None:
        file = client.files.list()
        assert_matches_type(SyncCursorPage[File], file, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: SGPClient) -> None:
        file = client.files.list(
            ending_before="ending_before",
            filename="filename",
            limit=1,
            sort_order="asc",
            starting_after="starting_after",
        )
        assert_matches_type(SyncCursorPage[File], file, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: SGPClient) -> None:
        response = client.files.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(SyncCursorPage[File], file, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: SGPClient) -> None:
        with client.files.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(SyncCursorPage[File], file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: SGPClient) -> None:
        file = client.files.delete(
            "file_id",
        )
        assert_matches_type(FileDeleteResponse, file, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: SGPClient) -> None:
        response = client.files.with_raw_response.delete(
            "file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(FileDeleteResponse, file, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: SGPClient) -> None:
        with client.files.with_streaming_response.delete(
            "file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(FileDeleteResponse, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: SGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            client.files.with_raw_response.delete(
                "",
            )


class TestAsyncFiles:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncSGPClient) -> None:
        file = await async_client.files.create(
            file=b"raw file contents",
        )
        assert_matches_type(File, file, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.files.with_raw_response.create(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(File, file, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncSGPClient) -> None:
        async with async_client.files.with_streaming_response.create(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(File, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncSGPClient) -> None:
        file = await async_client.files.retrieve(
            "file_id",
        )
        assert_matches_type(File, file, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.files.with_raw_response.retrieve(
            "file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(File, file, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncSGPClient) -> None:
        async with async_client.files.with_streaming_response.retrieve(
            "file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(File, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncSGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            await async_client.files.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncSGPClient) -> None:
        file = await async_client.files.update(
            file_id="file_id",
        )
        assert_matches_type(File, file, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncSGPClient) -> None:
        file = await async_client.files.update(
            file_id="file_id",
            tags={"foo": "bar"},
        )
        assert_matches_type(File, file, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.files.with_raw_response.update(
            file_id="file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(File, file, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncSGPClient) -> None:
        async with async_client.files.with_streaming_response.update(
            file_id="file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(File, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncSGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            await async_client.files.with_raw_response.update(
                file_id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncSGPClient) -> None:
        file = await async_client.files.list()
        assert_matches_type(AsyncCursorPage[File], file, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSGPClient) -> None:
        file = await async_client.files.list(
            ending_before="ending_before",
            filename="filename",
            limit=1,
            sort_order="asc",
            starting_after="starting_after",
        )
        assert_matches_type(AsyncCursorPage[File], file, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.files.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(AsyncCursorPage[File], file, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSGPClient) -> None:
        async with async_client.files.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(AsyncCursorPage[File], file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncSGPClient) -> None:
        file = await async_client.files.delete(
            "file_id",
        )
        assert_matches_type(FileDeleteResponse, file, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.files.with_raw_response.delete(
            "file_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(FileDeleteResponse, file, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncSGPClient) -> None:
        async with async_client.files.with_streaming_response.delete(
            "file_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(FileDeleteResponse, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncSGPClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `file_id` but received ''"):
            await async_client.files.with_raw_response.delete(
                "",
            )
