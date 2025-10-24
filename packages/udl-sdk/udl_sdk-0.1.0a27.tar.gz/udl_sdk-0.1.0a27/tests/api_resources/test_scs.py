# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from tests.utils import assert_matches_type
from unifieddatalibrary import Unifieddatalibrary, AsyncUnifieddatalibrary
from unifieddatalibrary.types import (
    ScSearchResponse,
    ScHasWriteAccessResponse,
    ScAllowableFileMimesResponse,
    ScAllowableFileExtensionsResponse,
)
from unifieddatalibrary._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)

# pyright: reportDeprecated=false

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestScs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_delete(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = client.scs.delete(
                id="id",
            )

        assert sc is None

    @parametrize
    def test_raw_response_delete(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.scs.with_raw_response.delete(
                id="id",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert sc is None

    @parametrize
    def test_streaming_response_delete(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            with client.scs.with_streaming_response.delete(
                id="id",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = response.parse()
                assert sc is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_allowable_file_extensions(self, client: Unifieddatalibrary) -> None:
        sc = client.scs.allowable_file_extensions()
        assert_matches_type(ScAllowableFileExtensionsResponse, sc, path=["response"])

    @parametrize
    def test_raw_response_allowable_file_extensions(self, client: Unifieddatalibrary) -> None:
        response = client.scs.with_raw_response.allowable_file_extensions()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert_matches_type(ScAllowableFileExtensionsResponse, sc, path=["response"])

    @parametrize
    def test_streaming_response_allowable_file_extensions(self, client: Unifieddatalibrary) -> None:
        with client.scs.with_streaming_response.allowable_file_extensions() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sc = response.parse()
            assert_matches_type(ScAllowableFileExtensionsResponse, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_allowable_file_mimes(self, client: Unifieddatalibrary) -> None:
        sc = client.scs.allowable_file_mimes()
        assert_matches_type(ScAllowableFileMimesResponse, sc, path=["response"])

    @parametrize
    def test_raw_response_allowable_file_mimes(self, client: Unifieddatalibrary) -> None:
        response = client.scs.with_raw_response.allowable_file_mimes()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert_matches_type(ScAllowableFileMimesResponse, sc, path=["response"])

    @parametrize
    def test_streaming_response_allowable_file_mimes(self, client: Unifieddatalibrary) -> None:
        with client.scs.with_streaming_response.allowable_file_mimes() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sc = response.parse()
            assert_matches_type(ScAllowableFileMimesResponse, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_copy(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = client.scs.copy(
                id="id",
                target_path="targetPath",
            )

        assert_matches_type(str, sc, path=["response"])

    @parametrize
    def test_raw_response_copy(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.scs.with_raw_response.copy(
                id="id",
                target_path="targetPath",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert_matches_type(str, sc, path=["response"])

    @parametrize
    def test_streaming_response_copy(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            with client.scs.with_streaming_response.copy(
                id="id",
                target_path="targetPath",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = response.parse()
                assert_matches_type(str, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_download(self, client: Unifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.post("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        sc = client.scs.download(
            body=["/MyFolderToDownload/"],
        )
        assert sc.is_closed
        assert sc.json() == {"foo": "bar"}
        assert cast(Any, sc.is_closed) is True
        assert isinstance(sc, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_download(self, client: Unifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.post("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        sc = client.scs.with_raw_response.download(
            body=["/MyFolderToDownload/"],
        )

        assert sc.is_closed is True
        assert sc.http_request.headers.get("X-Stainless-Lang") == "python"
        assert sc.json() == {"foo": "bar"}
        assert isinstance(sc, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_download(self, client: Unifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.post("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        with client.scs.with_streaming_response.download(
            body=["/MyFolderToDownload/"],
        ) as sc:
            assert not sc.is_closed
            assert sc.http_request.headers.get("X-Stainless-Lang") == "python"

            assert sc.json() == {"foo": "bar"}
            assert cast(Any, sc.is_closed) is True
            assert isinstance(sc, StreamedBinaryAPIResponse)

        assert cast(Any, sc.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_file_download(self, client: Unifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.get("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        sc = client.scs.file_download(
            id="id",
        )
        assert sc.is_closed
        assert sc.json() == {"foo": "bar"}
        assert cast(Any, sc.is_closed) is True
        assert isinstance(sc, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_file_download_with_all_params(self, client: Unifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.get("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        sc = client.scs.file_download(
            id="id",
            first_result=0,
            max_results=0,
        )
        assert sc.is_closed
        assert sc.json() == {"foo": "bar"}
        assert cast(Any, sc.is_closed) is True
        assert isinstance(sc, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_file_download(self, client: Unifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.get("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        sc = client.scs.with_raw_response.file_download(
            id="id",
        )

        assert sc.is_closed is True
        assert sc.http_request.headers.get("X-Stainless-Lang") == "python"
        assert sc.json() == {"foo": "bar"}
        assert isinstance(sc, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_file_download(self, client: Unifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.get("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        with client.scs.with_streaming_response.file_download(
            id="id",
        ) as sc:
            assert not sc.is_closed
            assert sc.http_request.headers.get("X-Stainless-Lang") == "python"

            assert sc.json() == {"foo": "bar"}
            assert cast(Any, sc.is_closed) is True
            assert isinstance(sc, StreamedBinaryAPIResponse)

        assert cast(Any, sc.is_closed) is True

    @parametrize
    def test_method_file_upload(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = client.scs.file_upload(
                file_content=b"raw file contents",
                classification_marking="classificationMarking",
                file_name="fileName",
                path="path",
            )

        assert_matches_type(str, sc, path=["response"])

    @parametrize
    def test_method_file_upload_with_all_params(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = client.scs.file_upload(
                file_content=b"raw file contents",
                classification_marking="classificationMarking",
                file_name="fileName",
                path="path",
                delete_after="deleteAfter",
                description="description",
                overwrite=True,
                send_notification=True,
                tags="tags",
            )

        assert_matches_type(str, sc, path=["response"])

    @parametrize
    def test_raw_response_file_upload(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.scs.with_raw_response.file_upload(
                file_content=b"raw file contents",
                classification_marking="classificationMarking",
                file_name="fileName",
                path="path",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert_matches_type(str, sc, path=["response"])

    @parametrize
    def test_streaming_response_file_upload(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            with client.scs.with_streaming_response.file_upload(
                file_content=b"raw file contents",
                classification_marking="classificationMarking",
                file_name="fileName",
                path="path",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = response.parse()
                assert_matches_type(str, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_has_write_access(self, client: Unifieddatalibrary) -> None:
        sc = client.scs.has_write_access(
            path="path",
        )
        assert_matches_type(ScHasWriteAccessResponse, sc, path=["response"])

    @parametrize
    def test_method_has_write_access_with_all_params(self, client: Unifieddatalibrary) -> None:
        sc = client.scs.has_write_access(
            path="path",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(ScHasWriteAccessResponse, sc, path=["response"])

    @parametrize
    def test_raw_response_has_write_access(self, client: Unifieddatalibrary) -> None:
        response = client.scs.with_raw_response.has_write_access(
            path="path",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert_matches_type(ScHasWriteAccessResponse, sc, path=["response"])

    @parametrize
    def test_streaming_response_has_write_access(self, client: Unifieddatalibrary) -> None:
        with client.scs.with_streaming_response.has_write_access(
            path="path",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sc = response.parse()
            assert_matches_type(ScHasWriteAccessResponse, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_move(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = client.scs.move(
                id="id",
                target_path="targetPath",
            )

        assert_matches_type(str, sc, path=["response"])

    @parametrize
    def test_raw_response_move(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.scs.with_raw_response.move(
                id="id",
                target_path="targetPath",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert_matches_type(str, sc, path=["response"])

    @parametrize
    def test_streaming_response_move(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            with client.scs.with_streaming_response.move(
                id="id",
                target_path="targetPath",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = response.parse()
                assert_matches_type(str, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_rename(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = client.scs.rename(
                id="id",
                new_name="newName",
            )

        assert sc is None

    @parametrize
    def test_raw_response_rename(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.scs.with_raw_response.rename(
                id="id",
                new_name="newName",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert sc is None

    @parametrize
    def test_streaming_response_rename(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            with client.scs.with_streaming_response.rename(
                id="id",
                new_name="newName",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = response.parse()
                assert sc is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_search(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = client.scs.search(
                path="path",
            )

        assert_matches_type(ScSearchResponse, sc, path=["response"])

    @parametrize
    def test_method_search_with_all_params(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = client.scs.search(
                path="path",
                count=0,
                offset=0,
                content_criteria="contentCriteria",
                meta_data_criteria={"CREATED_AT": ["< 2022-06-14T07:48:11.302Z"]},
                non_range_criteria={"foo": ["string"]},
                range_criteria={"foo": ["string"]},
                search_after="searchAfter",
            )

        assert_matches_type(ScSearchResponse, sc, path=["response"])

    @parametrize
    def test_raw_response_search(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.scs.with_raw_response.search(
                path="path",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = response.parse()
        assert_matches_type(ScSearchResponse, sc, path=["response"])

    @parametrize
    def test_streaming_response_search(self, client: Unifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            with client.scs.with_streaming_response.search(
                path="path",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = response.parse()
                assert_matches_type(ScSearchResponse, sc, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncScs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_delete(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = await async_client.scs.delete(
                id="id",
            )

        assert sc is None

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.scs.with_raw_response.delete(
                id="id",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert sc is None

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.scs.with_streaming_response.delete(
                id="id",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = await response.parse()
                assert sc is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_allowable_file_extensions(self, async_client: AsyncUnifieddatalibrary) -> None:
        sc = await async_client.scs.allowable_file_extensions()
        assert_matches_type(ScAllowableFileExtensionsResponse, sc, path=["response"])

    @parametrize
    async def test_raw_response_allowable_file_extensions(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.scs.with_raw_response.allowable_file_extensions()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert_matches_type(ScAllowableFileExtensionsResponse, sc, path=["response"])

    @parametrize
    async def test_streaming_response_allowable_file_extensions(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.scs.with_streaming_response.allowable_file_extensions() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sc = await response.parse()
            assert_matches_type(ScAllowableFileExtensionsResponse, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_allowable_file_mimes(self, async_client: AsyncUnifieddatalibrary) -> None:
        sc = await async_client.scs.allowable_file_mimes()
        assert_matches_type(ScAllowableFileMimesResponse, sc, path=["response"])

    @parametrize
    async def test_raw_response_allowable_file_mimes(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.scs.with_raw_response.allowable_file_mimes()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert_matches_type(ScAllowableFileMimesResponse, sc, path=["response"])

    @parametrize
    async def test_streaming_response_allowable_file_mimes(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.scs.with_streaming_response.allowable_file_mimes() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sc = await response.parse()
            assert_matches_type(ScAllowableFileMimesResponse, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_copy(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = await async_client.scs.copy(
                id="id",
                target_path="targetPath",
            )

        assert_matches_type(str, sc, path=["response"])

    @parametrize
    async def test_raw_response_copy(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.scs.with_raw_response.copy(
                id="id",
                target_path="targetPath",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert_matches_type(str, sc, path=["response"])

    @parametrize
    async def test_streaming_response_copy(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.scs.with_streaming_response.copy(
                id="id",
                target_path="targetPath",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = await response.parse()
                assert_matches_type(str, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_download(self, async_client: AsyncUnifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.post("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        sc = await async_client.scs.download(
            body=["/MyFolderToDownload/"],
        )
        assert sc.is_closed
        assert await sc.json() == {"foo": "bar"}
        assert cast(Any, sc.is_closed) is True
        assert isinstance(sc, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_download(self, async_client: AsyncUnifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.post("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        sc = await async_client.scs.with_raw_response.download(
            body=["/MyFolderToDownload/"],
        )

        assert sc.is_closed is True
        assert sc.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await sc.json() == {"foo": "bar"}
        assert isinstance(sc, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_download(
        self, async_client: AsyncUnifieddatalibrary, respx_mock: MockRouter
    ) -> None:
        respx_mock.post("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        async with async_client.scs.with_streaming_response.download(
            body=["/MyFolderToDownload/"],
        ) as sc:
            assert not sc.is_closed
            assert sc.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await sc.json() == {"foo": "bar"}
            assert cast(Any, sc.is_closed) is True
            assert isinstance(sc, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, sc.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_file_download(self, async_client: AsyncUnifieddatalibrary, respx_mock: MockRouter) -> None:
        respx_mock.get("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        sc = await async_client.scs.file_download(
            id="id",
        )
        assert sc.is_closed
        assert await sc.json() == {"foo": "bar"}
        assert cast(Any, sc.is_closed) is True
        assert isinstance(sc, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_file_download_with_all_params(
        self, async_client: AsyncUnifieddatalibrary, respx_mock: MockRouter
    ) -> None:
        respx_mock.get("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        sc = await async_client.scs.file_download(
            id="id",
            first_result=0,
            max_results=0,
        )
        assert sc.is_closed
        assert await sc.json() == {"foo": "bar"}
        assert cast(Any, sc.is_closed) is True
        assert isinstance(sc, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_file_download(
        self, async_client: AsyncUnifieddatalibrary, respx_mock: MockRouter
    ) -> None:
        respx_mock.get("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        sc = await async_client.scs.with_raw_response.file_download(
            id="id",
        )

        assert sc.is_closed is True
        assert sc.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await sc.json() == {"foo": "bar"}
        assert isinstance(sc, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_file_download(
        self, async_client: AsyncUnifieddatalibrary, respx_mock: MockRouter
    ) -> None:
        respx_mock.get("/scs/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        async with async_client.scs.with_streaming_response.file_download(
            id="id",
        ) as sc:
            assert not sc.is_closed
            assert sc.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await sc.json() == {"foo": "bar"}
            assert cast(Any, sc.is_closed) is True
            assert isinstance(sc, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, sc.is_closed) is True

    @parametrize
    async def test_method_file_upload(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = await async_client.scs.file_upload(
                file_content=b"raw file contents",
                classification_marking="classificationMarking",
                file_name="fileName",
                path="path",
            )

        assert_matches_type(str, sc, path=["response"])

    @parametrize
    async def test_method_file_upload_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = await async_client.scs.file_upload(
                file_content=b"raw file contents",
                classification_marking="classificationMarking",
                file_name="fileName",
                path="path",
                delete_after="deleteAfter",
                description="description",
                overwrite=True,
                send_notification=True,
                tags="tags",
            )

        assert_matches_type(str, sc, path=["response"])

    @parametrize
    async def test_raw_response_file_upload(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.scs.with_raw_response.file_upload(
                file_content=b"raw file contents",
                classification_marking="classificationMarking",
                file_name="fileName",
                path="path",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert_matches_type(str, sc, path=["response"])

    @parametrize
    async def test_streaming_response_file_upload(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.scs.with_streaming_response.file_upload(
                file_content=b"raw file contents",
                classification_marking="classificationMarking",
                file_name="fileName",
                path="path",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = await response.parse()
                assert_matches_type(str, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_has_write_access(self, async_client: AsyncUnifieddatalibrary) -> None:
        sc = await async_client.scs.has_write_access(
            path="path",
        )
        assert_matches_type(ScHasWriteAccessResponse, sc, path=["response"])

    @parametrize
    async def test_method_has_write_access_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        sc = await async_client.scs.has_write_access(
            path="path",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(ScHasWriteAccessResponse, sc, path=["response"])

    @parametrize
    async def test_raw_response_has_write_access(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.scs.with_raw_response.has_write_access(
            path="path",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert_matches_type(ScHasWriteAccessResponse, sc, path=["response"])

    @parametrize
    async def test_streaming_response_has_write_access(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.scs.with_streaming_response.has_write_access(
            path="path",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sc = await response.parse()
            assert_matches_type(ScHasWriteAccessResponse, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_move(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = await async_client.scs.move(
                id="id",
                target_path="targetPath",
            )

        assert_matches_type(str, sc, path=["response"])

    @parametrize
    async def test_raw_response_move(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.scs.with_raw_response.move(
                id="id",
                target_path="targetPath",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert_matches_type(str, sc, path=["response"])

    @parametrize
    async def test_streaming_response_move(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.scs.with_streaming_response.move(
                id="id",
                target_path="targetPath",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = await response.parse()
                assert_matches_type(str, sc, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_rename(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = await async_client.scs.rename(
                id="id",
                new_name="newName",
            )

        assert sc is None

    @parametrize
    async def test_raw_response_rename(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.scs.with_raw_response.rename(
                id="id",
                new_name="newName",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert sc is None

    @parametrize
    async def test_streaming_response_rename(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.scs.with_streaming_response.rename(
                id="id",
                new_name="newName",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = await response.parse()
                assert sc is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_search(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = await async_client.scs.search(
                path="path",
            )

        assert_matches_type(ScSearchResponse, sc, path=["response"])

    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            sc = await async_client.scs.search(
                path="path",
                count=0,
                offset=0,
                content_criteria="contentCriteria",
                meta_data_criteria={"CREATED_AT": ["< 2022-06-14T07:48:11.302Z"]},
                non_range_criteria={"foo": ["string"]},
                range_criteria={"foo": ["string"]},
                search_after="searchAfter",
            )

        assert_matches_type(ScSearchResponse, sc, path=["response"])

    @parametrize
    async def test_raw_response_search(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.scs.with_raw_response.search(
                path="path",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sc = await response.parse()
        assert_matches_type(ScSearchResponse, sc, path=["response"])

    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.scs.with_streaming_response.search(
                path="path",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                sc = await response.parse()
                assert_matches_type(ScSearchResponse, sc, path=["response"])

        assert cast(Any, response.is_closed) is True
