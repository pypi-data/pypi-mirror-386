# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from unifieddatalibrary import Unifieddatalibrary, AsyncUnifieddatalibrary
from unifieddatalibrary.types import (
    SigactListResponse,
    SigactTupleResponse,
    SigactQueryhelpResponse,
)
from unifieddatalibrary._utils import parse_datetime
from unifieddatalibrary.pagination import SyncOffsetPage, AsyncOffsetPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSigact:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_list(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.list(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SyncOffsetPage[SigactListResponse], sigact, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.list(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(SyncOffsetPage[SigactListResponse], sigact, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Unifieddatalibrary) -> None:
        response = client.sigact.with_raw_response.list(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = response.parse()
        assert_matches_type(SyncOffsetPage[SigactListResponse], sigact, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Unifieddatalibrary) -> None:
        with client.sigact.with_streaming_response.list(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = response.parse()
            assert_matches_type(SyncOffsetPage[SigactListResponse], sigact, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_count(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.count(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(str, sigact, path=["response"])

    @parametrize
    def test_method_count_with_all_params(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.count(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(str, sigact, path=["response"])

    @parametrize
    def test_raw_response_count(self, client: Unifieddatalibrary) -> None:
        response = client.sigact.with_raw_response.count(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = response.parse()
        assert_matches_type(str, sigact, path=["response"])

    @parametrize
    def test_streaming_response_count(self, client: Unifieddatalibrary) -> None:
        with client.sigact.with_streaming_response.count(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = response.parse()
            assert_matches_type(str, sigact, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_bulk(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "report_date": parse_datetime("2018-01-01T16:00:00.123Z"),
                    "source": "Bluestaq",
                }
            ],
        )
        assert sigact is None

    @parametrize
    def test_raw_response_create_bulk(self, client: Unifieddatalibrary) -> None:
        response = client.sigact.with_raw_response.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "report_date": parse_datetime("2018-01-01T16:00:00.123Z"),
                    "source": "Bluestaq",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = response.parse()
        assert sigact is None

    @parametrize
    def test_streaming_response_create_bulk(self, client: Unifieddatalibrary) -> None:
        with client.sigact.with_streaming_response.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "report_date": parse_datetime("2018-01-01T16:00:00.123Z"),
                    "source": "Bluestaq",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = response.parse()
            assert sigact is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_queryhelp(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.queryhelp()
        assert_matches_type(SigactQueryhelpResponse, sigact, path=["response"])

    @parametrize
    def test_raw_response_queryhelp(self, client: Unifieddatalibrary) -> None:
        response = client.sigact.with_raw_response.queryhelp()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = response.parse()
        assert_matches_type(SigactQueryhelpResponse, sigact, path=["response"])

    @parametrize
    def test_streaming_response_queryhelp(self, client: Unifieddatalibrary) -> None:
        with client.sigact.with_streaming_response.queryhelp() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = response.parse()
            assert_matches_type(SigactQueryhelpResponse, sigact, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_tuple(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.tuple(
            columns="columns",
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SigactTupleResponse, sigact, path=["response"])

    @parametrize
    def test_method_tuple_with_all_params(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.tuple(
            columns="columns",
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(SigactTupleResponse, sigact, path=["response"])

    @parametrize
    def test_raw_response_tuple(self, client: Unifieddatalibrary) -> None:
        response = client.sigact.with_raw_response.tuple(
            columns="columns",
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = response.parse()
        assert_matches_type(SigactTupleResponse, sigact, path=["response"])

    @parametrize
    def test_streaming_response_tuple(self, client: Unifieddatalibrary) -> None:
        with client.sigact.with_streaming_response.tuple(
            columns="columns",
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = response.parse()
            assert_matches_type(SigactTupleResponse, sigact, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_upload_zip(self, client: Unifieddatalibrary) -> None:
        sigact = client.sigact.upload_zip(
            file=b"raw file contents",
        )
        assert sigact is None

    @parametrize
    def test_raw_response_upload_zip(self, client: Unifieddatalibrary) -> None:
        response = client.sigact.with_raw_response.upload_zip(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = response.parse()
        assert sigact is None

    @parametrize
    def test_streaming_response_upload_zip(self, client: Unifieddatalibrary) -> None:
        with client.sigact.with_streaming_response.upload_zip(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = response.parse()
            assert sigact is None

        assert cast(Any, response.is_closed) is True


class TestAsyncSigact:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.list(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(AsyncOffsetPage[SigactListResponse], sigact, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.list(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(AsyncOffsetPage[SigactListResponse], sigact, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.sigact.with_raw_response.list(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = await response.parse()
        assert_matches_type(AsyncOffsetPage[SigactListResponse], sigact, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.sigact.with_streaming_response.list(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = await response.parse()
            assert_matches_type(AsyncOffsetPage[SigactListResponse], sigact, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.count(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(str, sigact, path=["response"])

    @parametrize
    async def test_method_count_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.count(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(str, sigact, path=["response"])

    @parametrize
    async def test_raw_response_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.sigact.with_raw_response.count(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = await response.parse()
        assert_matches_type(str, sigact, path=["response"])

    @parametrize
    async def test_streaming_response_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.sigact.with_streaming_response.count(
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = await response.parse()
            assert_matches_type(str, sigact, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_bulk(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "report_date": parse_datetime("2018-01-01T16:00:00.123Z"),
                    "source": "Bluestaq",
                }
            ],
        )
        assert sigact is None

    @parametrize
    async def test_raw_response_create_bulk(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.sigact.with_raw_response.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "report_date": parse_datetime("2018-01-01T16:00:00.123Z"),
                    "source": "Bluestaq",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = await response.parse()
        assert sigact is None

    @parametrize
    async def test_streaming_response_create_bulk(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.sigact.with_streaming_response.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "report_date": parse_datetime("2018-01-01T16:00:00.123Z"),
                    "source": "Bluestaq",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = await response.parse()
            assert sigact is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.queryhelp()
        assert_matches_type(SigactQueryhelpResponse, sigact, path=["response"])

    @parametrize
    async def test_raw_response_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.sigact.with_raw_response.queryhelp()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = await response.parse()
        assert_matches_type(SigactQueryhelpResponse, sigact, path=["response"])

    @parametrize
    async def test_streaming_response_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.sigact.with_streaming_response.queryhelp() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = await response.parse()
            assert_matches_type(SigactQueryhelpResponse, sigact, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.tuple(
            columns="columns",
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SigactTupleResponse, sigact, path=["response"])

    @parametrize
    async def test_method_tuple_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.tuple(
            columns="columns",
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(SigactTupleResponse, sigact, path=["response"])

    @parametrize
    async def test_raw_response_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.sigact.with_raw_response.tuple(
            columns="columns",
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = await response.parse()
        assert_matches_type(SigactTupleResponse, sigact, path=["response"])

    @parametrize
    async def test_streaming_response_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.sigact.with_streaming_response.tuple(
            columns="columns",
            report_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = await response.parse()
            assert_matches_type(SigactTupleResponse, sigact, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_upload_zip(self, async_client: AsyncUnifieddatalibrary) -> None:
        sigact = await async_client.sigact.upload_zip(
            file=b"raw file contents",
        )
        assert sigact is None

    @parametrize
    async def test_raw_response_upload_zip(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.sigact.with_raw_response.upload_zip(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sigact = await response.parse()
        assert sigact is None

    @parametrize
    async def test_streaming_response_upload_zip(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.sigact.with_streaming_response.upload_zip(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sigact = await response.parse()
            assert sigact is None

        assert cast(Any, response.is_closed) is True
