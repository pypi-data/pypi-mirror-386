# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from scale_gp_beta import SGPClient, AsyncSGPClient
from scale_gp_beta.types.chat import (
    CompletionCreateResponse,
    CompletionModelsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCompletions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create_overload_1(self, client: SGPClient) -> None:
        completion = client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
        )
        assert_matches_type(CompletionCreateResponse, completion, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_1(self, client: SGPClient) -> None:
        completion = client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
            audio={"foo": "bar"},
            frequency_penalty=-2,
            function_call={"foo": "bar"},
            functions=[{"foo": "bar"}],
            logit_bias={"foo": 0},
            logprobs=True,
            max_completion_tokens=0,
            max_tokens=0,
            metadata={"foo": "string"},
            modalities=["string"],
            n=0,
            parallel_tool_calls=True,
            prediction={"foo": "bar"},
            presence_penalty=-2,
            reasoning_effort="reasoning_effort",
            response_format={"foo": "bar"},
            seed=0,
            stop="string",
            store=True,
            stream=False,
            stream_options={"foo": "bar"},
            temperature=0,
            tool_choice="string",
            tools=[{"foo": "bar"}],
            top_k=0,
            top_logprobs=0,
            top_p=0,
        )
        assert_matches_type(CompletionCreateResponse, completion, path=["response"])

    @parametrize
    def test_raw_response_create_overload_1(self, client: SGPClient) -> None:
        response = client.chat.completions.with_raw_response.create(
            messages=[{"foo": "bar"}],
            model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = response.parse()
        assert_matches_type(CompletionCreateResponse, completion, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_1(self, client: SGPClient) -> None:
        with client.chat.completions.with_streaming_response.create(
            messages=[{"foo": "bar"}],
            model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = response.parse()
            assert_matches_type(CompletionCreateResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_2(self, client: SGPClient) -> None:
        completion_stream = client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
            stream=True,
        )
        completion_stream.response.close()

    @parametrize
    def test_method_create_with_all_params_overload_2(self, client: SGPClient) -> None:
        completion_stream = client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
            stream=True,
            audio={"foo": "bar"},
            frequency_penalty=-2,
            function_call={"foo": "bar"},
            functions=[{"foo": "bar"}],
            logit_bias={"foo": 0},
            logprobs=True,
            max_completion_tokens=0,
            max_tokens=0,
            metadata={"foo": "string"},
            modalities=["string"],
            n=0,
            parallel_tool_calls=True,
            prediction={"foo": "bar"},
            presence_penalty=-2,
            reasoning_effort="reasoning_effort",
            response_format={"foo": "bar"},
            seed=0,
            stop="string",
            store=True,
            stream_options={"foo": "bar"},
            temperature=0,
            tool_choice="string",
            tools=[{"foo": "bar"}],
            top_k=0,
            top_logprobs=0,
            top_p=0,
        )
        completion_stream.response.close()

    @parametrize
    def test_raw_response_create_overload_2(self, client: SGPClient) -> None:
        response = client.chat.completions.with_raw_response.create(
            messages=[{"foo": "bar"}],
            model="model",
            stream=True,
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = response.parse()
        stream.close()

    @parametrize
    def test_streaming_response_create_overload_2(self, client: SGPClient) -> None:
        with client.chat.completions.with_streaming_response.create(
            messages=[{"foo": "bar"}],
            model="model",
            stream=True,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = response.parse()
            stream.close()

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_models(self, client: SGPClient) -> None:
        completion = client.chat.completions.models()
        assert_matches_type(CompletionModelsResponse, completion, path=["response"])

    @parametrize
    def test_method_models_with_all_params(self, client: SGPClient) -> None:
        completion = client.chat.completions.models(
            ending_before="ending_before",
            limit=1,
            model_vendor="openai",
            sort_order="asc",
            starting_after="starting_after",
        )
        assert_matches_type(CompletionModelsResponse, completion, path=["response"])

    @parametrize
    def test_raw_response_models(self, client: SGPClient) -> None:
        response = client.chat.completions.with_raw_response.models()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = response.parse()
        assert_matches_type(CompletionModelsResponse, completion, path=["response"])

    @parametrize
    def test_streaming_response_models(self, client: SGPClient) -> None:
        with client.chat.completions.with_streaming_response.models() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = response.parse()
            assert_matches_type(CompletionModelsResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCompletions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        completion = await async_client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
        )
        assert_matches_type(CompletionCreateResponse, completion, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_1(self, async_client: AsyncSGPClient) -> None:
        completion = await async_client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
            audio={"foo": "bar"},
            frequency_penalty=-2,
            function_call={"foo": "bar"},
            functions=[{"foo": "bar"}],
            logit_bias={"foo": 0},
            logprobs=True,
            max_completion_tokens=0,
            max_tokens=0,
            metadata={"foo": "string"},
            modalities=["string"],
            n=0,
            parallel_tool_calls=True,
            prediction={"foo": "bar"},
            presence_penalty=-2,
            reasoning_effort="reasoning_effort",
            response_format={"foo": "bar"},
            seed=0,
            stop="string",
            store=True,
            stream=False,
            stream_options={"foo": "bar"},
            temperature=0,
            tool_choice="string",
            tools=[{"foo": "bar"}],
            top_k=0,
            top_logprobs=0,
            top_p=0,
        )
        assert_matches_type(CompletionCreateResponse, completion, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.chat.completions.with_raw_response.create(
            messages=[{"foo": "bar"}],
            model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = await response.parse()
        assert_matches_type(CompletionCreateResponse, completion, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_1(self, async_client: AsyncSGPClient) -> None:
        async with async_client.chat.completions.with_streaming_response.create(
            messages=[{"foo": "bar"}],
            model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = await response.parse()
            assert_matches_type(CompletionCreateResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        completion_stream = await async_client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
            stream=True,
        )
        await completion_stream.response.aclose()

    @parametrize
    async def test_method_create_with_all_params_overload_2(self, async_client: AsyncSGPClient) -> None:
        completion_stream = await async_client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
            stream=True,
            audio={"foo": "bar"},
            frequency_penalty=-2,
            function_call={"foo": "bar"},
            functions=[{"foo": "bar"}],
            logit_bias={"foo": 0},
            logprobs=True,
            max_completion_tokens=0,
            max_tokens=0,
            metadata={"foo": "string"},
            modalities=["string"],
            n=0,
            parallel_tool_calls=True,
            prediction={"foo": "bar"},
            presence_penalty=-2,
            reasoning_effort="reasoning_effort",
            response_format={"foo": "bar"},
            seed=0,
            stop="string",
            store=True,
            stream_options={"foo": "bar"},
            temperature=0,
            tool_choice="string",
            tools=[{"foo": "bar"}],
            top_k=0,
            top_logprobs=0,
            top_p=0,
        )
        await completion_stream.response.aclose()

    @parametrize
    async def test_raw_response_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.chat.completions.with_raw_response.create(
            messages=[{"foo": "bar"}],
            model="model",
            stream=True,
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = await response.parse()
        await stream.close()

    @parametrize
    async def test_streaming_response_create_overload_2(self, async_client: AsyncSGPClient) -> None:
        async with async_client.chat.completions.with_streaming_response.create(
            messages=[{"foo": "bar"}],
            model="model",
            stream=True,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = await response.parse()
            await stream.close()

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_models(self, async_client: AsyncSGPClient) -> None:
        completion = await async_client.chat.completions.models()
        assert_matches_type(CompletionModelsResponse, completion, path=["response"])

    @parametrize
    async def test_method_models_with_all_params(self, async_client: AsyncSGPClient) -> None:
        completion = await async_client.chat.completions.models(
            ending_before="ending_before",
            limit=1,
            model_vendor="openai",
            sort_order="asc",
            starting_after="starting_after",
        )
        assert_matches_type(CompletionModelsResponse, completion, path=["response"])

    @parametrize
    async def test_raw_response_models(self, async_client: AsyncSGPClient) -> None:
        response = await async_client.chat.completions.with_raw_response.models()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = await response.parse()
        assert_matches_type(CompletionModelsResponse, completion, path=["response"])

    @parametrize
    async def test_streaming_response_models(self, async_client: AsyncSGPClient) -> None:
        async with async_client.chat.completions.with_streaming_response.models() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = await response.parse()
            assert_matches_type(CompletionModelsResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True
