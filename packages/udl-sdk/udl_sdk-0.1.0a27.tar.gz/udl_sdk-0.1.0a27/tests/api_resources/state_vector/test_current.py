# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from unifieddatalibrary import Unifieddatalibrary, AsyncUnifieddatalibrary
from unifieddatalibrary.types import StateVectorAbridged
from unifieddatalibrary.pagination import SyncOffsetPage, AsyncOffsetPage
from unifieddatalibrary.types.state_vector import CurrentTupleResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCurrent:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_list(self, client: Unifieddatalibrary) -> None:
        current = client.state_vector.current.list()
        assert_matches_type(SyncOffsetPage[StateVectorAbridged], current, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Unifieddatalibrary) -> None:
        current = client.state_vector.current.list(
            first_result=0,
            max_results=0,
        )
        assert_matches_type(SyncOffsetPage[StateVectorAbridged], current, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Unifieddatalibrary) -> None:
        response = client.state_vector.current.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        current = response.parse()
        assert_matches_type(SyncOffsetPage[StateVectorAbridged], current, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Unifieddatalibrary) -> None:
        with client.state_vector.current.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            current = response.parse()
            assert_matches_type(SyncOffsetPage[StateVectorAbridged], current, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_tuple(self, client: Unifieddatalibrary) -> None:
        current = client.state_vector.current.tuple(
            columns="columns",
        )
        assert_matches_type(CurrentTupleResponse, current, path=["response"])

    @parametrize
    def test_method_tuple_with_all_params(self, client: Unifieddatalibrary) -> None:
        current = client.state_vector.current.tuple(
            columns="columns",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(CurrentTupleResponse, current, path=["response"])

    @parametrize
    def test_raw_response_tuple(self, client: Unifieddatalibrary) -> None:
        response = client.state_vector.current.with_raw_response.tuple(
            columns="columns",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        current = response.parse()
        assert_matches_type(CurrentTupleResponse, current, path=["response"])

    @parametrize
    def test_streaming_response_tuple(self, client: Unifieddatalibrary) -> None:
        with client.state_vector.current.with_streaming_response.tuple(
            columns="columns",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            current = response.parse()
            assert_matches_type(CurrentTupleResponse, current, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCurrent:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        current = await async_client.state_vector.current.list()
        assert_matches_type(AsyncOffsetPage[StateVectorAbridged], current, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        current = await async_client.state_vector.current.list(
            first_result=0,
            max_results=0,
        )
        assert_matches_type(AsyncOffsetPage[StateVectorAbridged], current, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.state_vector.current.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        current = await response.parse()
        assert_matches_type(AsyncOffsetPage[StateVectorAbridged], current, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.state_vector.current.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            current = await response.parse()
            assert_matches_type(AsyncOffsetPage[StateVectorAbridged], current, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        current = await async_client.state_vector.current.tuple(
            columns="columns",
        )
        assert_matches_type(CurrentTupleResponse, current, path=["response"])

    @parametrize
    async def test_method_tuple_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        current = await async_client.state_vector.current.tuple(
            columns="columns",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(CurrentTupleResponse, current, path=["response"])

    @parametrize
    async def test_raw_response_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.state_vector.current.with_raw_response.tuple(
            columns="columns",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        current = await response.parse()
        assert_matches_type(CurrentTupleResponse, current, path=["response"])

    @parametrize
    async def test_streaming_response_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.state_vector.current.with_streaming_response.tuple(
            columns="columns",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            current = await response.parse()
            assert_matches_type(CurrentTupleResponse, current, path=["response"])

        assert cast(Any, response.is_closed) is True
