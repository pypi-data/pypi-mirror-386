# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from unifieddatalibrary import Unifieddatalibrary, AsyncUnifieddatalibrary
from unifieddatalibrary.types import (
    MissionAssignmentGetResponse,
    MissionAssignmentListResponse,
    MissionAssignmentTupleResponse,
    MissionAssignmentQueryhelpResponse,
)
from unifieddatalibrary._utils import parse_datetime
from unifieddatalibrary.pagination import SyncOffsetPage, AsyncOffsetPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMissionAssignment:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.create(
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        )
        assert mission_assignment is None

    @parametrize
    def test_method_create_with_all_params(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.create(
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
            id="MISSIONASSIGNMENT-ID",
            c1associateddmpis=3,
            c2air="C2AIR",
            c2alt=3,
            c2crs=3,
            c2exerciseindicator="C2EXERCISE",
            c2exercisemof="MOF",
            c2id="C2ID",
            c2idamplifyingdescriptor="C2IDAMP",
            c2lnd="C2LND",
            c2spc="C2SPC",
            c2spd=3,
            c2specialinterestindicator="C2SPECIAL",
            c2sur="C2SUR",
            c3elv=10.23,
            c3lat=10.23,
            c3lon=10.23,
            c3ptl="C3PTL",
            c3ptnum="C3PTNUM",
            c4colon=5,
            c4def="C4DEF",
            c4egress=4,
            c4mod=5,
            c4numberofstores=3,
            c4runin=5,
            c4tgt="C4TGT",
            c4timediscrete="C4TIMED",
            c4tm=4,
            c4typeofstores=2,
            c5colon=5,
            c5elevationlsbs=5,
            c5haeadj=5,
            c5latlsb=5,
            c5lonlsb=5,
            c5tgtbrng=5,
            c5tw=5,
            c6dspc="C6DSPC",
            c6dspct="C6DSPCT",
            c6fplpm="C6FPLPM",
            c6intel=5,
            c6laser=5,
            c6longpm="C6LONGPM",
            c6tnr3=5,
            c7elang2=5.23,
            c7in3p=3,
            c7tnor="C7TNOR",
            env="ENV",
            index=5,
            lat=45.23,
            lon=45.23,
            orginx="ORIGIN",
            origin="THIRD_PARTY_DATASOURCE",
            rc="RC-123",
            rr=2,
            sz="STRENGTH",
            tno="TRACK_NUMBER",
            trk_id="TRK-ID",
            twenv="THREAT_WARNING",
        )
        assert mission_assignment is None

    @parametrize
    def test_raw_response_create(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.create(
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert mission_assignment is None

    @parametrize
    def test_streaming_response_create(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.create(
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert mission_assignment is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_update(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.update(
            path_id="id",
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        )
        assert mission_assignment is None

    @parametrize
    def test_method_update_with_all_params(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.update(
            path_id="id",
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
            body_id="MISSIONASSIGNMENT-ID",
            c1associateddmpis=3,
            c2air="C2AIR",
            c2alt=3,
            c2crs=3,
            c2exerciseindicator="C2EXERCISE",
            c2exercisemof="MOF",
            c2id="C2ID",
            c2idamplifyingdescriptor="C2IDAMP",
            c2lnd="C2LND",
            c2spc="C2SPC",
            c2spd=3,
            c2specialinterestindicator="C2SPECIAL",
            c2sur="C2SUR",
            c3elv=10.23,
            c3lat=10.23,
            c3lon=10.23,
            c3ptl="C3PTL",
            c3ptnum="C3PTNUM",
            c4colon=5,
            c4def="C4DEF",
            c4egress=4,
            c4mod=5,
            c4numberofstores=3,
            c4runin=5,
            c4tgt="C4TGT",
            c4timediscrete="C4TIMED",
            c4tm=4,
            c4typeofstores=2,
            c5colon=5,
            c5elevationlsbs=5,
            c5haeadj=5,
            c5latlsb=5,
            c5lonlsb=5,
            c5tgtbrng=5,
            c5tw=5,
            c6dspc="C6DSPC",
            c6dspct="C6DSPCT",
            c6fplpm="C6FPLPM",
            c6intel=5,
            c6laser=5,
            c6longpm="C6LONGPM",
            c6tnr3=5,
            c7elang2=5.23,
            c7in3p=3,
            c7tnor="C7TNOR",
            env="ENV",
            index=5,
            lat=45.23,
            lon=45.23,
            orginx="ORIGIN",
            origin="THIRD_PARTY_DATASOURCE",
            rc="RC-123",
            rr=2,
            sz="STRENGTH",
            tno="TRACK_NUMBER",
            trk_id="TRK-ID",
            twenv="THREAT_WARNING",
        )
        assert mission_assignment is None

    @parametrize
    def test_raw_response_update(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.update(
            path_id="id",
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert mission_assignment is None

    @parametrize
    def test_streaming_response_update(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.update(
            path_id="id",
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert mission_assignment is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: Unifieddatalibrary) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `path_id` but received ''"):
            client.mission_assignment.with_raw_response.update(
                path_id="",
                classification_marking="U",
                data_mode="TEST",
                mad="MAD",
                source="Bluestaq",
                ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
            )

    @parametrize
    def test_method_list(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.list(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SyncOffsetPage[MissionAssignmentListResponse], mission_assignment, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.list(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(SyncOffsetPage[MissionAssignmentListResponse], mission_assignment, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.list(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert_matches_type(SyncOffsetPage[MissionAssignmentListResponse], mission_assignment, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.list(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert_matches_type(SyncOffsetPage[MissionAssignmentListResponse], mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.delete(
            "id",
        )
        assert mission_assignment is None

    @parametrize
    def test_raw_response_delete(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert mission_assignment is None

    @parametrize
    def test_streaming_response_delete(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert mission_assignment is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: Unifieddatalibrary) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.mission_assignment.with_raw_response.delete(
                "",
            )

    @parametrize
    def test_method_count(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.count(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(str, mission_assignment, path=["response"])

    @parametrize
    def test_method_count_with_all_params(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.count(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(str, mission_assignment, path=["response"])

    @parametrize
    def test_raw_response_count(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.count(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert_matches_type(str, mission_assignment, path=["response"])

    @parametrize
    def test_streaming_response_count(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.count(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert_matches_type(str, mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_bulk(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "mad": "MAD",
                    "source": "Bluestaq",
                    "ts": parse_datetime("2021-01-01T01:01:01.123456Z"),
                }
            ],
        )
        assert mission_assignment is None

    @parametrize
    def test_raw_response_create_bulk(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "mad": "MAD",
                    "source": "Bluestaq",
                    "ts": parse_datetime("2021-01-01T01:01:01.123456Z"),
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert mission_assignment is None

    @parametrize
    def test_streaming_response_create_bulk(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "mad": "MAD",
                    "source": "Bluestaq",
                    "ts": parse_datetime("2021-01-01T01:01:01.123456Z"),
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert mission_assignment is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_get(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.get(
            id="id",
        )
        assert_matches_type(MissionAssignmentGetResponse, mission_assignment, path=["response"])

    @parametrize
    def test_method_get_with_all_params(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.get(
            id="id",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(MissionAssignmentGetResponse, mission_assignment, path=["response"])

    @parametrize
    def test_raw_response_get(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.get(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert_matches_type(MissionAssignmentGetResponse, mission_assignment, path=["response"])

    @parametrize
    def test_streaming_response_get(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.get(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert_matches_type(MissionAssignmentGetResponse, mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_get(self, client: Unifieddatalibrary) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.mission_assignment.with_raw_response.get(
                id="",
            )

    @parametrize
    def test_method_queryhelp(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.queryhelp()
        assert_matches_type(MissionAssignmentQueryhelpResponse, mission_assignment, path=["response"])

    @parametrize
    def test_raw_response_queryhelp(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.queryhelp()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert_matches_type(MissionAssignmentQueryhelpResponse, mission_assignment, path=["response"])

    @parametrize
    def test_streaming_response_queryhelp(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.queryhelp() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert_matches_type(MissionAssignmentQueryhelpResponse, mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_tuple(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.tuple(
            columns="columns",
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(MissionAssignmentTupleResponse, mission_assignment, path=["response"])

    @parametrize
    def test_method_tuple_with_all_params(self, client: Unifieddatalibrary) -> None:
        mission_assignment = client.mission_assignment.tuple(
            columns="columns",
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(MissionAssignmentTupleResponse, mission_assignment, path=["response"])

    @parametrize
    def test_raw_response_tuple(self, client: Unifieddatalibrary) -> None:
        response = client.mission_assignment.with_raw_response.tuple(
            columns="columns",
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = response.parse()
        assert_matches_type(MissionAssignmentTupleResponse, mission_assignment, path=["response"])

    @parametrize
    def test_streaming_response_tuple(self, client: Unifieddatalibrary) -> None:
        with client.mission_assignment.with_streaming_response.tuple(
            columns="columns",
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = response.parse()
            assert_matches_type(MissionAssignmentTupleResponse, mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMissionAssignment:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.create(
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        )
        assert mission_assignment is None

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.create(
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
            id="MISSIONASSIGNMENT-ID",
            c1associateddmpis=3,
            c2air="C2AIR",
            c2alt=3,
            c2crs=3,
            c2exerciseindicator="C2EXERCISE",
            c2exercisemof="MOF",
            c2id="C2ID",
            c2idamplifyingdescriptor="C2IDAMP",
            c2lnd="C2LND",
            c2spc="C2SPC",
            c2spd=3,
            c2specialinterestindicator="C2SPECIAL",
            c2sur="C2SUR",
            c3elv=10.23,
            c3lat=10.23,
            c3lon=10.23,
            c3ptl="C3PTL",
            c3ptnum="C3PTNUM",
            c4colon=5,
            c4def="C4DEF",
            c4egress=4,
            c4mod=5,
            c4numberofstores=3,
            c4runin=5,
            c4tgt="C4TGT",
            c4timediscrete="C4TIMED",
            c4tm=4,
            c4typeofstores=2,
            c5colon=5,
            c5elevationlsbs=5,
            c5haeadj=5,
            c5latlsb=5,
            c5lonlsb=5,
            c5tgtbrng=5,
            c5tw=5,
            c6dspc="C6DSPC",
            c6dspct="C6DSPCT",
            c6fplpm="C6FPLPM",
            c6intel=5,
            c6laser=5,
            c6longpm="C6LONGPM",
            c6tnr3=5,
            c7elang2=5.23,
            c7in3p=3,
            c7tnor="C7TNOR",
            env="ENV",
            index=5,
            lat=45.23,
            lon=45.23,
            orginx="ORIGIN",
            origin="THIRD_PARTY_DATASOURCE",
            rc="RC-123",
            rr=2,
            sz="STRENGTH",
            tno="TRACK_NUMBER",
            trk_id="TRK-ID",
            twenv="THREAT_WARNING",
        )
        assert mission_assignment is None

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.create(
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert mission_assignment is None

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.create(
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert mission_assignment is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_update(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.update(
            path_id="id",
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        )
        assert mission_assignment is None

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.update(
            path_id="id",
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
            body_id="MISSIONASSIGNMENT-ID",
            c1associateddmpis=3,
            c2air="C2AIR",
            c2alt=3,
            c2crs=3,
            c2exerciseindicator="C2EXERCISE",
            c2exercisemof="MOF",
            c2id="C2ID",
            c2idamplifyingdescriptor="C2IDAMP",
            c2lnd="C2LND",
            c2spc="C2SPC",
            c2spd=3,
            c2specialinterestindicator="C2SPECIAL",
            c2sur="C2SUR",
            c3elv=10.23,
            c3lat=10.23,
            c3lon=10.23,
            c3ptl="C3PTL",
            c3ptnum="C3PTNUM",
            c4colon=5,
            c4def="C4DEF",
            c4egress=4,
            c4mod=5,
            c4numberofstores=3,
            c4runin=5,
            c4tgt="C4TGT",
            c4timediscrete="C4TIMED",
            c4tm=4,
            c4typeofstores=2,
            c5colon=5,
            c5elevationlsbs=5,
            c5haeadj=5,
            c5latlsb=5,
            c5lonlsb=5,
            c5tgtbrng=5,
            c5tw=5,
            c6dspc="C6DSPC",
            c6dspct="C6DSPCT",
            c6fplpm="C6FPLPM",
            c6intel=5,
            c6laser=5,
            c6longpm="C6LONGPM",
            c6tnr3=5,
            c7elang2=5.23,
            c7in3p=3,
            c7tnor="C7TNOR",
            env="ENV",
            index=5,
            lat=45.23,
            lon=45.23,
            orginx="ORIGIN",
            origin="THIRD_PARTY_DATASOURCE",
            rc="RC-123",
            rr=2,
            sz="STRENGTH",
            tno="TRACK_NUMBER",
            trk_id="TRK-ID",
            twenv="THREAT_WARNING",
        )
        assert mission_assignment is None

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.update(
            path_id="id",
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert mission_assignment is None

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.update(
            path_id="id",
            classification_marking="U",
            data_mode="TEST",
            mad="MAD",
            source="Bluestaq",
            ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert mission_assignment is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `path_id` but received ''"):
            await async_client.mission_assignment.with_raw_response.update(
                path_id="",
                classification_marking="U",
                data_mode="TEST",
                mad="MAD",
                source="Bluestaq",
                ts=parse_datetime("2021-01-01T01:01:01.123456Z"),
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.list(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(AsyncOffsetPage[MissionAssignmentListResponse], mission_assignment, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.list(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(AsyncOffsetPage[MissionAssignmentListResponse], mission_assignment, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.list(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert_matches_type(AsyncOffsetPage[MissionAssignmentListResponse], mission_assignment, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.list(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert_matches_type(AsyncOffsetPage[MissionAssignmentListResponse], mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.delete(
            "id",
        )
        assert mission_assignment is None

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert mission_assignment is None

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert mission_assignment is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.mission_assignment.with_raw_response.delete(
                "",
            )

    @parametrize
    async def test_method_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.count(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(str, mission_assignment, path=["response"])

    @parametrize
    async def test_method_count_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.count(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(str, mission_assignment, path=["response"])

    @parametrize
    async def test_raw_response_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.count(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert_matches_type(str, mission_assignment, path=["response"])

    @parametrize
    async def test_streaming_response_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.count(
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert_matches_type(str, mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_bulk(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "mad": "MAD",
                    "source": "Bluestaq",
                    "ts": parse_datetime("2021-01-01T01:01:01.123456Z"),
                }
            ],
        )
        assert mission_assignment is None

    @parametrize
    async def test_raw_response_create_bulk(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "mad": "MAD",
                    "source": "Bluestaq",
                    "ts": parse_datetime("2021-01-01T01:01:01.123456Z"),
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert mission_assignment is None

    @parametrize
    async def test_streaming_response_create_bulk(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.create_bulk(
            body=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "mad": "MAD",
                    "source": "Bluestaq",
                    "ts": parse_datetime("2021-01-01T01:01:01.123456Z"),
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert mission_assignment is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_get(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.get(
            id="id",
        )
        assert_matches_type(MissionAssignmentGetResponse, mission_assignment, path=["response"])

    @parametrize
    async def test_method_get_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.get(
            id="id",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(MissionAssignmentGetResponse, mission_assignment, path=["response"])

    @parametrize
    async def test_raw_response_get(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.get(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert_matches_type(MissionAssignmentGetResponse, mission_assignment, path=["response"])

    @parametrize
    async def test_streaming_response_get(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.get(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert_matches_type(MissionAssignmentGetResponse, mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_get(self, async_client: AsyncUnifieddatalibrary) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.mission_assignment.with_raw_response.get(
                id="",
            )

    @parametrize
    async def test_method_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.queryhelp()
        assert_matches_type(MissionAssignmentQueryhelpResponse, mission_assignment, path=["response"])

    @parametrize
    async def test_raw_response_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.queryhelp()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert_matches_type(MissionAssignmentQueryhelpResponse, mission_assignment, path=["response"])

    @parametrize
    async def test_streaming_response_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.queryhelp() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert_matches_type(MissionAssignmentQueryhelpResponse, mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.tuple(
            columns="columns",
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(MissionAssignmentTupleResponse, mission_assignment, path=["response"])

    @parametrize
    async def test_method_tuple_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        mission_assignment = await async_client.mission_assignment.tuple(
            columns="columns",
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
            first_result=0,
            max_results=0,
        )
        assert_matches_type(MissionAssignmentTupleResponse, mission_assignment, path=["response"])

    @parametrize
    async def test_raw_response_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.mission_assignment.with_raw_response.tuple(
            columns="columns",
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission_assignment = await response.parse()
        assert_matches_type(MissionAssignmentTupleResponse, mission_assignment, path=["response"])

    @parametrize
    async def test_streaming_response_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.mission_assignment.with_streaming_response.tuple(
            columns="columns",
            ts=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission_assignment = await response.parse()
            assert_matches_type(MissionAssignmentTupleResponse, mission_assignment, path=["response"])

        assert cast(Any, response.is_closed) is True
