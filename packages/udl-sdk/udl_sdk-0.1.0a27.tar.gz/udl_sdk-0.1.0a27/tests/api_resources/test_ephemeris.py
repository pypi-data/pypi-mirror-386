# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from unifieddatalibrary import Unifieddatalibrary, AsyncUnifieddatalibrary
from unifieddatalibrary.types import (
    EphemerisAbridged,
    EphemerisTupleResponse,
    EphemerisQueryhelpResponse,
)
from unifieddatalibrary._utils import parse_datetime
from unifieddatalibrary.pagination import SyncOffsetPage, AsyncOffsetPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEphemeris:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_list(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.list(
            es_id="esId",
        )
        assert_matches_type(SyncOffsetPage[EphemerisAbridged], ephemeris, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.list(
            es_id="esId",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(SyncOffsetPage[EphemerisAbridged], ephemeris, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Unifieddatalibrary) -> None:
        response = client.ephemeris.with_raw_response.list(
            es_id="esId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = response.parse()
        assert_matches_type(SyncOffsetPage[EphemerisAbridged], ephemeris, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Unifieddatalibrary) -> None:
        with client.ephemeris.with_streaming_response.list(
            es_id="esId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = response.parse()
            assert_matches_type(SyncOffsetPage[EphemerisAbridged], ephemeris, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_count(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.count(
            es_id="esId",
        )
        assert_matches_type(str, ephemeris, path=["response"])

    @parametrize
    def test_method_count_with_all_params(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.count(
            es_id="esId",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(str, ephemeris, path=["response"])

    @parametrize
    def test_raw_response_count(self, client: Unifieddatalibrary) -> None:
        response = client.ephemeris.with_raw_response.count(
            es_id="esId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = response.parse()
        assert_matches_type(str, ephemeris, path=["response"])

    @parametrize
    def test_streaming_response_count(self, client: Unifieddatalibrary) -> None:
        with client.ephemeris.with_streaming_response.count(
            es_id="esId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = response.parse()
            assert_matches_type(str, ephemeris, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_file_upload(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.file_upload(
            category="category",
            classification="classification",
            data_mode="REAL",
            ephem_format_type="ModITC",
            has_mnvr=True,
            sat_no=0,
            source="source",
            type="type",
            body="20090183552.438 854.324972 -806.523053 7049.922417 6.895812284 -2.628367346 -1.133733106\n20090183652.438 1266.133860 -962.545669 6968.125830 6.826675764 -2.570691008 -1.591933762\n20090183752.438 1672.992049 -1114.804860 6859.014485 6.730841878 -2.502960267 -2.043929218\n20090183852.438 2073.308235 -1262.705018 6723.013691 6.608678828 -2.425436636 -2.487957283\n20090183952.437 2465.516236 -1405.667354 6560.653649 6.460655493 -2.338419085 -2.922284617\n20090184052.437 2848.081001 -1543.132119 6372.567559 6.287340800 -2.242243249 -3.345212234\n20090184152.437 3219.504606 -1674.560790 6159.489368 6.089403061 -2.137280899 -3.755082127\n20090184252.437 3578.332160 -1799.438213 5922.251081 5.867608030 -2.023938998 -4.150285005\n20090184352.437 3923.157564 -1917.274669 5661.779621 5.622815776 -1.902658091 -4.529267262\n20090184452.437 4252.629072 -2027.607829 5379.093303 5.355977415 -1.773910426 -4.890537084\n20090184552.438 4565.454650 -2130.004610 5075.297949 5.068131657 -1.638198207 -5.232670449\n20090184652.438 4860.407121 -2224.062913 4751.582647 4.760401074 -1.496051826 -5.554316609\n20090184752.438 5136.329082 -2309.413262 4409.215191 4.433988183 -1.348027904 -5.854203792\n20090184852.438 5392.137572 -2385.720309 4049.537176 4.090171063 -1.194707051 -6.131144712\n20090184952.438 5626.828455 -2452.684200 3673.958773 3.730298408 -1.036691459 -6.384041406\n20090185052.438 5839.480522 -2510.041810 3283.953237 3.355784875 -0.874602755 -6.611889945\n20090185152.437 6029.259294 -2557.567834 2881.051109 2.968105821 -0.709079671 -6.813785484\n20090185252.437 6195.420471 -2595.075738 2466.834134 2.568790899 -0.540775331 -6.988926806\n20090185352.437 6337.313006 -2622.418539 2042.928930 2.159417590 -0.370354527 -7.136619912\n20090185452.437 6454.381765 -2639.489420 1611.000461 1.741604556 -0.198490869 -7.256280983\n20090185552.437 6546.169804 -2646.222176 1172.745350 1.317005015 -0.025863968 -7.347439001\n20090185652.438 6612.320241 -2642.591488 729.885039 0.887299878 0.146843350 -7.409738011\n20090185752.438 6652.577694 -2628.613029 284.158834 0.454190412 0.318947964 -7.442938697\n20090185852.438 6666.789294 -2604.343401 -162.683130 0.019391281 0.489769322 -7.446919583\n20090185952.438 6654.905265 -2569.879881 -608.886984 -0.415377036 0.658632454 -7.421677795\n20090190052.438 6616.979042 -2525.360006 -1052.702244 -0.848395994 0.824870985 -7.367328894\n20090190152.438 6553.166929 -2470.960963 -1492.388894 -1.277956388 0.987829985 -7.284105998\n20090190252.437 6463.727309 -2406.898823 -1926.224391 -1.702365928 1.146868752 -7.172358262\n20090190352.437 6349.019420 -2333.427607 -2352.510575 -2.119956347 1.301363455 -7.032548726\n20090190452.437 6209.501706 -2250.838192 -2769.580415 -2.529090096 1.450709724 -6.865251656\n20090190552.437 6045.729775 -2159.457075 -3175.804606 -2.928166964 1.594325073 -6.671149694\n20090190652.437 5858.353970 -2059.644985 -3569.597966 -3.315630505 1.731651201 -6.451030430\n20090190752.438 5648.116549 -1951.795371 -3949.425615 -3.689974155 1.862156222 -6.205782298\n20090190852.438 5415.848532 -1836.332754 -4313.808907 -4.049746799 1.985336490 -5.936390547\n20090190952.438 5162.466198 -1713.710980 -4661.331101 -4.393558446 2.100718445 -5.643932730\n20090191052.438 4888.967258 -1584.411363 -4990.642753 -4.720085507 2.207860388 -5.329573539\n20090191152.438 4596.426732 -1448.940726 -5300.466778 -5.028075349 2.306353880 -4.994559465\n20090191252.438 4285.992562 -1307.829369 -5589.603199 -5.316350511 2.395824993 -4.640213267\n20090191352.437 3958.880990 -1161.628964 -5856.933556 -5.583812443 2.475935445 -4.267928575\n20090191452.437 3616.371712 -1010.910385 -6101.425000 -5.829445081 2.546383684 -3.879164465\n20090191552.437 3259.802822 -856.261467 -6322.134041 -6.052318610 2.606905964 -3.475439590",
        )
        assert ephemeris is None

    @parametrize
    def test_method_file_upload_with_all_params(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.file_upload(
            category="category",
            classification="classification",
            data_mode="REAL",
            ephem_format_type="ModITC",
            has_mnvr=True,
            sat_no=0,
            source="source",
            type="type",
            body="20090183552.438 854.324972 -806.523053 7049.922417 6.895812284 -2.628367346 -1.133733106\n20090183652.438 1266.133860 -962.545669 6968.125830 6.826675764 -2.570691008 -1.591933762\n20090183752.438 1672.992049 -1114.804860 6859.014485 6.730841878 -2.502960267 -2.043929218\n20090183852.438 2073.308235 -1262.705018 6723.013691 6.608678828 -2.425436636 -2.487957283\n20090183952.437 2465.516236 -1405.667354 6560.653649 6.460655493 -2.338419085 -2.922284617\n20090184052.437 2848.081001 -1543.132119 6372.567559 6.287340800 -2.242243249 -3.345212234\n20090184152.437 3219.504606 -1674.560790 6159.489368 6.089403061 -2.137280899 -3.755082127\n20090184252.437 3578.332160 -1799.438213 5922.251081 5.867608030 -2.023938998 -4.150285005\n20090184352.437 3923.157564 -1917.274669 5661.779621 5.622815776 -1.902658091 -4.529267262\n20090184452.437 4252.629072 -2027.607829 5379.093303 5.355977415 -1.773910426 -4.890537084\n20090184552.438 4565.454650 -2130.004610 5075.297949 5.068131657 -1.638198207 -5.232670449\n20090184652.438 4860.407121 -2224.062913 4751.582647 4.760401074 -1.496051826 -5.554316609\n20090184752.438 5136.329082 -2309.413262 4409.215191 4.433988183 -1.348027904 -5.854203792\n20090184852.438 5392.137572 -2385.720309 4049.537176 4.090171063 -1.194707051 -6.131144712\n20090184952.438 5626.828455 -2452.684200 3673.958773 3.730298408 -1.036691459 -6.384041406\n20090185052.438 5839.480522 -2510.041810 3283.953237 3.355784875 -0.874602755 -6.611889945\n20090185152.437 6029.259294 -2557.567834 2881.051109 2.968105821 -0.709079671 -6.813785484\n20090185252.437 6195.420471 -2595.075738 2466.834134 2.568790899 -0.540775331 -6.988926806\n20090185352.437 6337.313006 -2622.418539 2042.928930 2.159417590 -0.370354527 -7.136619912\n20090185452.437 6454.381765 -2639.489420 1611.000461 1.741604556 -0.198490869 -7.256280983\n20090185552.437 6546.169804 -2646.222176 1172.745350 1.317005015 -0.025863968 -7.347439001\n20090185652.438 6612.320241 -2642.591488 729.885039 0.887299878 0.146843350 -7.409738011\n20090185752.438 6652.577694 -2628.613029 284.158834 0.454190412 0.318947964 -7.442938697\n20090185852.438 6666.789294 -2604.343401 -162.683130 0.019391281 0.489769322 -7.446919583\n20090185952.438 6654.905265 -2569.879881 -608.886984 -0.415377036 0.658632454 -7.421677795\n20090190052.438 6616.979042 -2525.360006 -1052.702244 -0.848395994 0.824870985 -7.367328894\n20090190152.438 6553.166929 -2470.960963 -1492.388894 -1.277956388 0.987829985 -7.284105998\n20090190252.437 6463.727309 -2406.898823 -1926.224391 -1.702365928 1.146868752 -7.172358262\n20090190352.437 6349.019420 -2333.427607 -2352.510575 -2.119956347 1.301363455 -7.032548726\n20090190452.437 6209.501706 -2250.838192 -2769.580415 -2.529090096 1.450709724 -6.865251656\n20090190552.437 6045.729775 -2159.457075 -3175.804606 -2.928166964 1.594325073 -6.671149694\n20090190652.437 5858.353970 -2059.644985 -3569.597966 -3.315630505 1.731651201 -6.451030430\n20090190752.438 5648.116549 -1951.795371 -3949.425615 -3.689974155 1.862156222 -6.205782298\n20090190852.438 5415.848532 -1836.332754 -4313.808907 -4.049746799 1.985336490 -5.936390547\n20090190952.438 5162.466198 -1713.710980 -4661.331101 -4.393558446 2.100718445 -5.643932730\n20090191052.438 4888.967258 -1584.411363 -4990.642753 -4.720085507 2.207860388 -5.329573539\n20090191152.438 4596.426732 -1448.940726 -5300.466778 -5.028075349 2.306353880 -4.994559465\n20090191252.438 4285.992562 -1307.829369 -5589.603199 -5.316350511 2.395824993 -4.640213267\n20090191352.437 3958.880990 -1161.628964 -5856.933556 -5.583812443 2.475935445 -4.267928575\n20090191452.437 3616.371712 -1010.910385 -6101.425000 -5.829445081 2.546383684 -3.879164465\n20090191552.437 3259.802822 -856.261467 -6322.134041 -6.052318610 2.606905964 -3.475439590",
            origin="origin",
            tags="tags",
        )
        assert ephemeris is None

    @parametrize
    def test_raw_response_file_upload(self, client: Unifieddatalibrary) -> None:
        response = client.ephemeris.with_raw_response.file_upload(
            category="category",
            classification="classification",
            data_mode="REAL",
            ephem_format_type="ModITC",
            has_mnvr=True,
            sat_no=0,
            source="source",
            type="type",
            body="20090183552.438 854.324972 -806.523053 7049.922417 6.895812284 -2.628367346 -1.133733106\n20090183652.438 1266.133860 -962.545669 6968.125830 6.826675764 -2.570691008 -1.591933762\n20090183752.438 1672.992049 -1114.804860 6859.014485 6.730841878 -2.502960267 -2.043929218\n20090183852.438 2073.308235 -1262.705018 6723.013691 6.608678828 -2.425436636 -2.487957283\n20090183952.437 2465.516236 -1405.667354 6560.653649 6.460655493 -2.338419085 -2.922284617\n20090184052.437 2848.081001 -1543.132119 6372.567559 6.287340800 -2.242243249 -3.345212234\n20090184152.437 3219.504606 -1674.560790 6159.489368 6.089403061 -2.137280899 -3.755082127\n20090184252.437 3578.332160 -1799.438213 5922.251081 5.867608030 -2.023938998 -4.150285005\n20090184352.437 3923.157564 -1917.274669 5661.779621 5.622815776 -1.902658091 -4.529267262\n20090184452.437 4252.629072 -2027.607829 5379.093303 5.355977415 -1.773910426 -4.890537084\n20090184552.438 4565.454650 -2130.004610 5075.297949 5.068131657 -1.638198207 -5.232670449\n20090184652.438 4860.407121 -2224.062913 4751.582647 4.760401074 -1.496051826 -5.554316609\n20090184752.438 5136.329082 -2309.413262 4409.215191 4.433988183 -1.348027904 -5.854203792\n20090184852.438 5392.137572 -2385.720309 4049.537176 4.090171063 -1.194707051 -6.131144712\n20090184952.438 5626.828455 -2452.684200 3673.958773 3.730298408 -1.036691459 -6.384041406\n20090185052.438 5839.480522 -2510.041810 3283.953237 3.355784875 -0.874602755 -6.611889945\n20090185152.437 6029.259294 -2557.567834 2881.051109 2.968105821 -0.709079671 -6.813785484\n20090185252.437 6195.420471 -2595.075738 2466.834134 2.568790899 -0.540775331 -6.988926806\n20090185352.437 6337.313006 -2622.418539 2042.928930 2.159417590 -0.370354527 -7.136619912\n20090185452.437 6454.381765 -2639.489420 1611.000461 1.741604556 -0.198490869 -7.256280983\n20090185552.437 6546.169804 -2646.222176 1172.745350 1.317005015 -0.025863968 -7.347439001\n20090185652.438 6612.320241 -2642.591488 729.885039 0.887299878 0.146843350 -7.409738011\n20090185752.438 6652.577694 -2628.613029 284.158834 0.454190412 0.318947964 -7.442938697\n20090185852.438 6666.789294 -2604.343401 -162.683130 0.019391281 0.489769322 -7.446919583\n20090185952.438 6654.905265 -2569.879881 -608.886984 -0.415377036 0.658632454 -7.421677795\n20090190052.438 6616.979042 -2525.360006 -1052.702244 -0.848395994 0.824870985 -7.367328894\n20090190152.438 6553.166929 -2470.960963 -1492.388894 -1.277956388 0.987829985 -7.284105998\n20090190252.437 6463.727309 -2406.898823 -1926.224391 -1.702365928 1.146868752 -7.172358262\n20090190352.437 6349.019420 -2333.427607 -2352.510575 -2.119956347 1.301363455 -7.032548726\n20090190452.437 6209.501706 -2250.838192 -2769.580415 -2.529090096 1.450709724 -6.865251656\n20090190552.437 6045.729775 -2159.457075 -3175.804606 -2.928166964 1.594325073 -6.671149694\n20090190652.437 5858.353970 -2059.644985 -3569.597966 -3.315630505 1.731651201 -6.451030430\n20090190752.438 5648.116549 -1951.795371 -3949.425615 -3.689974155 1.862156222 -6.205782298\n20090190852.438 5415.848532 -1836.332754 -4313.808907 -4.049746799 1.985336490 -5.936390547\n20090190952.438 5162.466198 -1713.710980 -4661.331101 -4.393558446 2.100718445 -5.643932730\n20090191052.438 4888.967258 -1584.411363 -4990.642753 -4.720085507 2.207860388 -5.329573539\n20090191152.438 4596.426732 -1448.940726 -5300.466778 -5.028075349 2.306353880 -4.994559465\n20090191252.438 4285.992562 -1307.829369 -5589.603199 -5.316350511 2.395824993 -4.640213267\n20090191352.437 3958.880990 -1161.628964 -5856.933556 -5.583812443 2.475935445 -4.267928575\n20090191452.437 3616.371712 -1010.910385 -6101.425000 -5.829445081 2.546383684 -3.879164465\n20090191552.437 3259.802822 -856.261467 -6322.134041 -6.052318610 2.606905964 -3.475439590",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = response.parse()
        assert ephemeris is None

    @parametrize
    def test_streaming_response_file_upload(self, client: Unifieddatalibrary) -> None:
        with client.ephemeris.with_streaming_response.file_upload(
            category="category",
            classification="classification",
            data_mode="REAL",
            ephem_format_type="ModITC",
            has_mnvr=True,
            sat_no=0,
            source="source",
            type="type",
            body="20090183552.438 854.324972 -806.523053 7049.922417 6.895812284 -2.628367346 -1.133733106\n20090183652.438 1266.133860 -962.545669 6968.125830 6.826675764 -2.570691008 -1.591933762\n20090183752.438 1672.992049 -1114.804860 6859.014485 6.730841878 -2.502960267 -2.043929218\n20090183852.438 2073.308235 -1262.705018 6723.013691 6.608678828 -2.425436636 -2.487957283\n20090183952.437 2465.516236 -1405.667354 6560.653649 6.460655493 -2.338419085 -2.922284617\n20090184052.437 2848.081001 -1543.132119 6372.567559 6.287340800 -2.242243249 -3.345212234\n20090184152.437 3219.504606 -1674.560790 6159.489368 6.089403061 -2.137280899 -3.755082127\n20090184252.437 3578.332160 -1799.438213 5922.251081 5.867608030 -2.023938998 -4.150285005\n20090184352.437 3923.157564 -1917.274669 5661.779621 5.622815776 -1.902658091 -4.529267262\n20090184452.437 4252.629072 -2027.607829 5379.093303 5.355977415 -1.773910426 -4.890537084\n20090184552.438 4565.454650 -2130.004610 5075.297949 5.068131657 -1.638198207 -5.232670449\n20090184652.438 4860.407121 -2224.062913 4751.582647 4.760401074 -1.496051826 -5.554316609\n20090184752.438 5136.329082 -2309.413262 4409.215191 4.433988183 -1.348027904 -5.854203792\n20090184852.438 5392.137572 -2385.720309 4049.537176 4.090171063 -1.194707051 -6.131144712\n20090184952.438 5626.828455 -2452.684200 3673.958773 3.730298408 -1.036691459 -6.384041406\n20090185052.438 5839.480522 -2510.041810 3283.953237 3.355784875 -0.874602755 -6.611889945\n20090185152.437 6029.259294 -2557.567834 2881.051109 2.968105821 -0.709079671 -6.813785484\n20090185252.437 6195.420471 -2595.075738 2466.834134 2.568790899 -0.540775331 -6.988926806\n20090185352.437 6337.313006 -2622.418539 2042.928930 2.159417590 -0.370354527 -7.136619912\n20090185452.437 6454.381765 -2639.489420 1611.000461 1.741604556 -0.198490869 -7.256280983\n20090185552.437 6546.169804 -2646.222176 1172.745350 1.317005015 -0.025863968 -7.347439001\n20090185652.438 6612.320241 -2642.591488 729.885039 0.887299878 0.146843350 -7.409738011\n20090185752.438 6652.577694 -2628.613029 284.158834 0.454190412 0.318947964 -7.442938697\n20090185852.438 6666.789294 -2604.343401 -162.683130 0.019391281 0.489769322 -7.446919583\n20090185952.438 6654.905265 -2569.879881 -608.886984 -0.415377036 0.658632454 -7.421677795\n20090190052.438 6616.979042 -2525.360006 -1052.702244 -0.848395994 0.824870985 -7.367328894\n20090190152.438 6553.166929 -2470.960963 -1492.388894 -1.277956388 0.987829985 -7.284105998\n20090190252.437 6463.727309 -2406.898823 -1926.224391 -1.702365928 1.146868752 -7.172358262\n20090190352.437 6349.019420 -2333.427607 -2352.510575 -2.119956347 1.301363455 -7.032548726\n20090190452.437 6209.501706 -2250.838192 -2769.580415 -2.529090096 1.450709724 -6.865251656\n20090190552.437 6045.729775 -2159.457075 -3175.804606 -2.928166964 1.594325073 -6.671149694\n20090190652.437 5858.353970 -2059.644985 -3569.597966 -3.315630505 1.731651201 -6.451030430\n20090190752.438 5648.116549 -1951.795371 -3949.425615 -3.689974155 1.862156222 -6.205782298\n20090190852.438 5415.848532 -1836.332754 -4313.808907 -4.049746799 1.985336490 -5.936390547\n20090190952.438 5162.466198 -1713.710980 -4661.331101 -4.393558446 2.100718445 -5.643932730\n20090191052.438 4888.967258 -1584.411363 -4990.642753 -4.720085507 2.207860388 -5.329573539\n20090191152.438 4596.426732 -1448.940726 -5300.466778 -5.028075349 2.306353880 -4.994559465\n20090191252.438 4285.992562 -1307.829369 -5589.603199 -5.316350511 2.395824993 -4.640213267\n20090191352.437 3958.880990 -1161.628964 -5856.933556 -5.583812443 2.475935445 -4.267928575\n20090191452.437 3616.371712 -1010.910385 -6101.425000 -5.829445081 2.546383684 -3.879164465\n20090191552.437 3259.802822 -856.261467 -6322.134041 -6.052318610 2.606905964 -3.475439590",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = response.parse()
            assert ephemeris is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_queryhelp(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.queryhelp()
        assert_matches_type(EphemerisQueryhelpResponse, ephemeris, path=["response"])

    @parametrize
    def test_raw_response_queryhelp(self, client: Unifieddatalibrary) -> None:
        response = client.ephemeris.with_raw_response.queryhelp()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = response.parse()
        assert_matches_type(EphemerisQueryhelpResponse, ephemeris, path=["response"])

    @parametrize
    def test_streaming_response_queryhelp(self, client: Unifieddatalibrary) -> None:
        with client.ephemeris.with_streaming_response.queryhelp() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = response.parse()
            assert_matches_type(EphemerisQueryhelpResponse, ephemeris, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_tuple(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.tuple(
            columns="columns",
            es_id="esId",
        )
        assert_matches_type(EphemerisTupleResponse, ephemeris, path=["response"])

    @parametrize
    def test_method_tuple_with_all_params(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.tuple(
            columns="columns",
            es_id="esId",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(EphemerisTupleResponse, ephemeris, path=["response"])

    @parametrize
    def test_raw_response_tuple(self, client: Unifieddatalibrary) -> None:
        response = client.ephemeris.with_raw_response.tuple(
            columns="columns",
            es_id="esId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = response.parse()
        assert_matches_type(EphemerisTupleResponse, ephemeris, path=["response"])

    @parametrize
    def test_streaming_response_tuple(self, client: Unifieddatalibrary) -> None:
        with client.ephemeris.with_streaming_response.tuple(
            columns="columns",
            es_id="esId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = response.parse()
            assert_matches_type(EphemerisTupleResponse, ephemeris, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_unvalidated_publish(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.unvalidated_publish(
            category="ANALYST",
            classification_marking="U",
            data_mode="TEST",
            num_points=1,
            point_end_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            point_start_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            source="Bluestaq",
            type="LAUNCH",
        )
        assert ephemeris is None

    @parametrize
    def test_method_unvalidated_publish_with_all_params(self, client: Unifieddatalibrary) -> None:
        ephemeris = client.ephemeris.unvalidated_publish(
            category="ANALYST",
            classification_marking="U",
            data_mode="TEST",
            num_points=1,
            point_end_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            point_start_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            source="Bluestaq",
            type="LAUNCH",
            id="EPHEMERISSET-ID",
            b_dot=1.1,
            cent_body="Earth",
            comments="Example notes",
            cov_reference_frame="J2000",
            description="Example notes",
            descriptor="Example descriptor",
            drag_model="JAC70",
            edr=1.1,
            ephemeris_list=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "source": "Bluestaq",
                    "ts": parse_datetime("2018-01-01T16:00:00.123456Z"),
                    "xpos": 1.1,
                    "xvel": 1.1,
                    "ypos": 1.1,
                    "yvel": 1.1,
                    "zpos": 1.1,
                    "zvel": 1.1,
                    "id": "EPHEMERIS-ID",
                    "cov": [1.1, 2.4, 3.8, 4.2, 5.5, 6],
                    "es_id": "ES-ID",
                    "id_on_orbit": "ONORBIT-ID",
                    "origin": "THIRD_PARTY_DATASOURCE",
                    "orig_object_id": "ORIGOBJECT-ID",
                    "xaccel": 1.1,
                    "yaccel": 1.1,
                    "zaccel": 1.1,
                }
            ],
            filename="Example file name",
            geopotential_model="GEM-T3",
            has_accel=False,
            has_cov=False,
            has_mnvr=False,
            id_maneuvers=["EXAMPLE_ID1", "EXAMPLE_ID2"],
            id_on_orbit="ONORBIT-ID",
            id_state_vector="STATEVECTOR-ID",
            integrator="COWELL",
            interpolation="LINEAR",
            interpolation_degree=5,
            lunar_solar=False,
            origin="THIRD_PARTY_DATASOURCE",
            orig_object_id="ORIGOBJECT-ID",
            pedigree="PROPAGATED",
            reference_frame="J2000",
            sat_no=2,
            solid_earth_tides=False,
            step_size=1,
            tags=["PROVIDER_TAG1", "PROVIDER_TAG2"],
            transaction_id="TRANSACTION-ID",
            usable_end_time=parse_datetime("2018-01-01T20:50:00.123456Z"),
            usable_start_time=parse_datetime("2018-01-01T16:10:00.123456Z"),
        )
        assert ephemeris is None

    @parametrize
    def test_raw_response_unvalidated_publish(self, client: Unifieddatalibrary) -> None:
        response = client.ephemeris.with_raw_response.unvalidated_publish(
            category="ANALYST",
            classification_marking="U",
            data_mode="TEST",
            num_points=1,
            point_end_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            point_start_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            source="Bluestaq",
            type="LAUNCH",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = response.parse()
        assert ephemeris is None

    @parametrize
    def test_streaming_response_unvalidated_publish(self, client: Unifieddatalibrary) -> None:
        with client.ephemeris.with_streaming_response.unvalidated_publish(
            category="ANALYST",
            classification_marking="U",
            data_mode="TEST",
            num_points=1,
            point_end_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            point_start_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            source="Bluestaq",
            type="LAUNCH",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = response.parse()
            assert ephemeris is None

        assert cast(Any, response.is_closed) is True


class TestAsyncEphemeris:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.list(
            es_id="esId",
        )
        assert_matches_type(AsyncOffsetPage[EphemerisAbridged], ephemeris, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.list(
            es_id="esId",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(AsyncOffsetPage[EphemerisAbridged], ephemeris, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.ephemeris.with_raw_response.list(
            es_id="esId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = await response.parse()
        assert_matches_type(AsyncOffsetPage[EphemerisAbridged], ephemeris, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.ephemeris.with_streaming_response.list(
            es_id="esId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = await response.parse()
            assert_matches_type(AsyncOffsetPage[EphemerisAbridged], ephemeris, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.count(
            es_id="esId",
        )
        assert_matches_type(str, ephemeris, path=["response"])

    @parametrize
    async def test_method_count_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.count(
            es_id="esId",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(str, ephemeris, path=["response"])

    @parametrize
    async def test_raw_response_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.ephemeris.with_raw_response.count(
            es_id="esId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = await response.parse()
        assert_matches_type(str, ephemeris, path=["response"])

    @parametrize
    async def test_streaming_response_count(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.ephemeris.with_streaming_response.count(
            es_id="esId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = await response.parse()
            assert_matches_type(str, ephemeris, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_file_upload(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.file_upload(
            category="category",
            classification="classification",
            data_mode="REAL",
            ephem_format_type="ModITC",
            has_mnvr=True,
            sat_no=0,
            source="source",
            type="type",
            body="20090183552.438 854.324972 -806.523053 7049.922417 6.895812284 -2.628367346 -1.133733106\n20090183652.438 1266.133860 -962.545669 6968.125830 6.826675764 -2.570691008 -1.591933762\n20090183752.438 1672.992049 -1114.804860 6859.014485 6.730841878 -2.502960267 -2.043929218\n20090183852.438 2073.308235 -1262.705018 6723.013691 6.608678828 -2.425436636 -2.487957283\n20090183952.437 2465.516236 -1405.667354 6560.653649 6.460655493 -2.338419085 -2.922284617\n20090184052.437 2848.081001 -1543.132119 6372.567559 6.287340800 -2.242243249 -3.345212234\n20090184152.437 3219.504606 -1674.560790 6159.489368 6.089403061 -2.137280899 -3.755082127\n20090184252.437 3578.332160 -1799.438213 5922.251081 5.867608030 -2.023938998 -4.150285005\n20090184352.437 3923.157564 -1917.274669 5661.779621 5.622815776 -1.902658091 -4.529267262\n20090184452.437 4252.629072 -2027.607829 5379.093303 5.355977415 -1.773910426 -4.890537084\n20090184552.438 4565.454650 -2130.004610 5075.297949 5.068131657 -1.638198207 -5.232670449\n20090184652.438 4860.407121 -2224.062913 4751.582647 4.760401074 -1.496051826 -5.554316609\n20090184752.438 5136.329082 -2309.413262 4409.215191 4.433988183 -1.348027904 -5.854203792\n20090184852.438 5392.137572 -2385.720309 4049.537176 4.090171063 -1.194707051 -6.131144712\n20090184952.438 5626.828455 -2452.684200 3673.958773 3.730298408 -1.036691459 -6.384041406\n20090185052.438 5839.480522 -2510.041810 3283.953237 3.355784875 -0.874602755 -6.611889945\n20090185152.437 6029.259294 -2557.567834 2881.051109 2.968105821 -0.709079671 -6.813785484\n20090185252.437 6195.420471 -2595.075738 2466.834134 2.568790899 -0.540775331 -6.988926806\n20090185352.437 6337.313006 -2622.418539 2042.928930 2.159417590 -0.370354527 -7.136619912\n20090185452.437 6454.381765 -2639.489420 1611.000461 1.741604556 -0.198490869 -7.256280983\n20090185552.437 6546.169804 -2646.222176 1172.745350 1.317005015 -0.025863968 -7.347439001\n20090185652.438 6612.320241 -2642.591488 729.885039 0.887299878 0.146843350 -7.409738011\n20090185752.438 6652.577694 -2628.613029 284.158834 0.454190412 0.318947964 -7.442938697\n20090185852.438 6666.789294 -2604.343401 -162.683130 0.019391281 0.489769322 -7.446919583\n20090185952.438 6654.905265 -2569.879881 -608.886984 -0.415377036 0.658632454 -7.421677795\n20090190052.438 6616.979042 -2525.360006 -1052.702244 -0.848395994 0.824870985 -7.367328894\n20090190152.438 6553.166929 -2470.960963 -1492.388894 -1.277956388 0.987829985 -7.284105998\n20090190252.437 6463.727309 -2406.898823 -1926.224391 -1.702365928 1.146868752 -7.172358262\n20090190352.437 6349.019420 -2333.427607 -2352.510575 -2.119956347 1.301363455 -7.032548726\n20090190452.437 6209.501706 -2250.838192 -2769.580415 -2.529090096 1.450709724 -6.865251656\n20090190552.437 6045.729775 -2159.457075 -3175.804606 -2.928166964 1.594325073 -6.671149694\n20090190652.437 5858.353970 -2059.644985 -3569.597966 -3.315630505 1.731651201 -6.451030430\n20090190752.438 5648.116549 -1951.795371 -3949.425615 -3.689974155 1.862156222 -6.205782298\n20090190852.438 5415.848532 -1836.332754 -4313.808907 -4.049746799 1.985336490 -5.936390547\n20090190952.438 5162.466198 -1713.710980 -4661.331101 -4.393558446 2.100718445 -5.643932730\n20090191052.438 4888.967258 -1584.411363 -4990.642753 -4.720085507 2.207860388 -5.329573539\n20090191152.438 4596.426732 -1448.940726 -5300.466778 -5.028075349 2.306353880 -4.994559465\n20090191252.438 4285.992562 -1307.829369 -5589.603199 -5.316350511 2.395824993 -4.640213267\n20090191352.437 3958.880990 -1161.628964 -5856.933556 -5.583812443 2.475935445 -4.267928575\n20090191452.437 3616.371712 -1010.910385 -6101.425000 -5.829445081 2.546383684 -3.879164465\n20090191552.437 3259.802822 -856.261467 -6322.134041 -6.052318610 2.606905964 -3.475439590",
        )
        assert ephemeris is None

    @parametrize
    async def test_method_file_upload_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.file_upload(
            category="category",
            classification="classification",
            data_mode="REAL",
            ephem_format_type="ModITC",
            has_mnvr=True,
            sat_no=0,
            source="source",
            type="type",
            body="20090183552.438 854.324972 -806.523053 7049.922417 6.895812284 -2.628367346 -1.133733106\n20090183652.438 1266.133860 -962.545669 6968.125830 6.826675764 -2.570691008 -1.591933762\n20090183752.438 1672.992049 -1114.804860 6859.014485 6.730841878 -2.502960267 -2.043929218\n20090183852.438 2073.308235 -1262.705018 6723.013691 6.608678828 -2.425436636 -2.487957283\n20090183952.437 2465.516236 -1405.667354 6560.653649 6.460655493 -2.338419085 -2.922284617\n20090184052.437 2848.081001 -1543.132119 6372.567559 6.287340800 -2.242243249 -3.345212234\n20090184152.437 3219.504606 -1674.560790 6159.489368 6.089403061 -2.137280899 -3.755082127\n20090184252.437 3578.332160 -1799.438213 5922.251081 5.867608030 -2.023938998 -4.150285005\n20090184352.437 3923.157564 -1917.274669 5661.779621 5.622815776 -1.902658091 -4.529267262\n20090184452.437 4252.629072 -2027.607829 5379.093303 5.355977415 -1.773910426 -4.890537084\n20090184552.438 4565.454650 -2130.004610 5075.297949 5.068131657 -1.638198207 -5.232670449\n20090184652.438 4860.407121 -2224.062913 4751.582647 4.760401074 -1.496051826 -5.554316609\n20090184752.438 5136.329082 -2309.413262 4409.215191 4.433988183 -1.348027904 -5.854203792\n20090184852.438 5392.137572 -2385.720309 4049.537176 4.090171063 -1.194707051 -6.131144712\n20090184952.438 5626.828455 -2452.684200 3673.958773 3.730298408 -1.036691459 -6.384041406\n20090185052.438 5839.480522 -2510.041810 3283.953237 3.355784875 -0.874602755 -6.611889945\n20090185152.437 6029.259294 -2557.567834 2881.051109 2.968105821 -0.709079671 -6.813785484\n20090185252.437 6195.420471 -2595.075738 2466.834134 2.568790899 -0.540775331 -6.988926806\n20090185352.437 6337.313006 -2622.418539 2042.928930 2.159417590 -0.370354527 -7.136619912\n20090185452.437 6454.381765 -2639.489420 1611.000461 1.741604556 -0.198490869 -7.256280983\n20090185552.437 6546.169804 -2646.222176 1172.745350 1.317005015 -0.025863968 -7.347439001\n20090185652.438 6612.320241 -2642.591488 729.885039 0.887299878 0.146843350 -7.409738011\n20090185752.438 6652.577694 -2628.613029 284.158834 0.454190412 0.318947964 -7.442938697\n20090185852.438 6666.789294 -2604.343401 -162.683130 0.019391281 0.489769322 -7.446919583\n20090185952.438 6654.905265 -2569.879881 -608.886984 -0.415377036 0.658632454 -7.421677795\n20090190052.438 6616.979042 -2525.360006 -1052.702244 -0.848395994 0.824870985 -7.367328894\n20090190152.438 6553.166929 -2470.960963 -1492.388894 -1.277956388 0.987829985 -7.284105998\n20090190252.437 6463.727309 -2406.898823 -1926.224391 -1.702365928 1.146868752 -7.172358262\n20090190352.437 6349.019420 -2333.427607 -2352.510575 -2.119956347 1.301363455 -7.032548726\n20090190452.437 6209.501706 -2250.838192 -2769.580415 -2.529090096 1.450709724 -6.865251656\n20090190552.437 6045.729775 -2159.457075 -3175.804606 -2.928166964 1.594325073 -6.671149694\n20090190652.437 5858.353970 -2059.644985 -3569.597966 -3.315630505 1.731651201 -6.451030430\n20090190752.438 5648.116549 -1951.795371 -3949.425615 -3.689974155 1.862156222 -6.205782298\n20090190852.438 5415.848532 -1836.332754 -4313.808907 -4.049746799 1.985336490 -5.936390547\n20090190952.438 5162.466198 -1713.710980 -4661.331101 -4.393558446 2.100718445 -5.643932730\n20090191052.438 4888.967258 -1584.411363 -4990.642753 -4.720085507 2.207860388 -5.329573539\n20090191152.438 4596.426732 -1448.940726 -5300.466778 -5.028075349 2.306353880 -4.994559465\n20090191252.438 4285.992562 -1307.829369 -5589.603199 -5.316350511 2.395824993 -4.640213267\n20090191352.437 3958.880990 -1161.628964 -5856.933556 -5.583812443 2.475935445 -4.267928575\n20090191452.437 3616.371712 -1010.910385 -6101.425000 -5.829445081 2.546383684 -3.879164465\n20090191552.437 3259.802822 -856.261467 -6322.134041 -6.052318610 2.606905964 -3.475439590",
            origin="origin",
            tags="tags",
        )
        assert ephemeris is None

    @parametrize
    async def test_raw_response_file_upload(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.ephemeris.with_raw_response.file_upload(
            category="category",
            classification="classification",
            data_mode="REAL",
            ephem_format_type="ModITC",
            has_mnvr=True,
            sat_no=0,
            source="source",
            type="type",
            body="20090183552.438 854.324972 -806.523053 7049.922417 6.895812284 -2.628367346 -1.133733106\n20090183652.438 1266.133860 -962.545669 6968.125830 6.826675764 -2.570691008 -1.591933762\n20090183752.438 1672.992049 -1114.804860 6859.014485 6.730841878 -2.502960267 -2.043929218\n20090183852.438 2073.308235 -1262.705018 6723.013691 6.608678828 -2.425436636 -2.487957283\n20090183952.437 2465.516236 -1405.667354 6560.653649 6.460655493 -2.338419085 -2.922284617\n20090184052.437 2848.081001 -1543.132119 6372.567559 6.287340800 -2.242243249 -3.345212234\n20090184152.437 3219.504606 -1674.560790 6159.489368 6.089403061 -2.137280899 -3.755082127\n20090184252.437 3578.332160 -1799.438213 5922.251081 5.867608030 -2.023938998 -4.150285005\n20090184352.437 3923.157564 -1917.274669 5661.779621 5.622815776 -1.902658091 -4.529267262\n20090184452.437 4252.629072 -2027.607829 5379.093303 5.355977415 -1.773910426 -4.890537084\n20090184552.438 4565.454650 -2130.004610 5075.297949 5.068131657 -1.638198207 -5.232670449\n20090184652.438 4860.407121 -2224.062913 4751.582647 4.760401074 -1.496051826 -5.554316609\n20090184752.438 5136.329082 -2309.413262 4409.215191 4.433988183 -1.348027904 -5.854203792\n20090184852.438 5392.137572 -2385.720309 4049.537176 4.090171063 -1.194707051 -6.131144712\n20090184952.438 5626.828455 -2452.684200 3673.958773 3.730298408 -1.036691459 -6.384041406\n20090185052.438 5839.480522 -2510.041810 3283.953237 3.355784875 -0.874602755 -6.611889945\n20090185152.437 6029.259294 -2557.567834 2881.051109 2.968105821 -0.709079671 -6.813785484\n20090185252.437 6195.420471 -2595.075738 2466.834134 2.568790899 -0.540775331 -6.988926806\n20090185352.437 6337.313006 -2622.418539 2042.928930 2.159417590 -0.370354527 -7.136619912\n20090185452.437 6454.381765 -2639.489420 1611.000461 1.741604556 -0.198490869 -7.256280983\n20090185552.437 6546.169804 -2646.222176 1172.745350 1.317005015 -0.025863968 -7.347439001\n20090185652.438 6612.320241 -2642.591488 729.885039 0.887299878 0.146843350 -7.409738011\n20090185752.438 6652.577694 -2628.613029 284.158834 0.454190412 0.318947964 -7.442938697\n20090185852.438 6666.789294 -2604.343401 -162.683130 0.019391281 0.489769322 -7.446919583\n20090185952.438 6654.905265 -2569.879881 -608.886984 -0.415377036 0.658632454 -7.421677795\n20090190052.438 6616.979042 -2525.360006 -1052.702244 -0.848395994 0.824870985 -7.367328894\n20090190152.438 6553.166929 -2470.960963 -1492.388894 -1.277956388 0.987829985 -7.284105998\n20090190252.437 6463.727309 -2406.898823 -1926.224391 -1.702365928 1.146868752 -7.172358262\n20090190352.437 6349.019420 -2333.427607 -2352.510575 -2.119956347 1.301363455 -7.032548726\n20090190452.437 6209.501706 -2250.838192 -2769.580415 -2.529090096 1.450709724 -6.865251656\n20090190552.437 6045.729775 -2159.457075 -3175.804606 -2.928166964 1.594325073 -6.671149694\n20090190652.437 5858.353970 -2059.644985 -3569.597966 -3.315630505 1.731651201 -6.451030430\n20090190752.438 5648.116549 -1951.795371 -3949.425615 -3.689974155 1.862156222 -6.205782298\n20090190852.438 5415.848532 -1836.332754 -4313.808907 -4.049746799 1.985336490 -5.936390547\n20090190952.438 5162.466198 -1713.710980 -4661.331101 -4.393558446 2.100718445 -5.643932730\n20090191052.438 4888.967258 -1584.411363 -4990.642753 -4.720085507 2.207860388 -5.329573539\n20090191152.438 4596.426732 -1448.940726 -5300.466778 -5.028075349 2.306353880 -4.994559465\n20090191252.438 4285.992562 -1307.829369 -5589.603199 -5.316350511 2.395824993 -4.640213267\n20090191352.437 3958.880990 -1161.628964 -5856.933556 -5.583812443 2.475935445 -4.267928575\n20090191452.437 3616.371712 -1010.910385 -6101.425000 -5.829445081 2.546383684 -3.879164465\n20090191552.437 3259.802822 -856.261467 -6322.134041 -6.052318610 2.606905964 -3.475439590",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = await response.parse()
        assert ephemeris is None

    @parametrize
    async def test_streaming_response_file_upload(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.ephemeris.with_streaming_response.file_upload(
            category="category",
            classification="classification",
            data_mode="REAL",
            ephem_format_type="ModITC",
            has_mnvr=True,
            sat_no=0,
            source="source",
            type="type",
            body="20090183552.438 854.324972 -806.523053 7049.922417 6.895812284 -2.628367346 -1.133733106\n20090183652.438 1266.133860 -962.545669 6968.125830 6.826675764 -2.570691008 -1.591933762\n20090183752.438 1672.992049 -1114.804860 6859.014485 6.730841878 -2.502960267 -2.043929218\n20090183852.438 2073.308235 -1262.705018 6723.013691 6.608678828 -2.425436636 -2.487957283\n20090183952.437 2465.516236 -1405.667354 6560.653649 6.460655493 -2.338419085 -2.922284617\n20090184052.437 2848.081001 -1543.132119 6372.567559 6.287340800 -2.242243249 -3.345212234\n20090184152.437 3219.504606 -1674.560790 6159.489368 6.089403061 -2.137280899 -3.755082127\n20090184252.437 3578.332160 -1799.438213 5922.251081 5.867608030 -2.023938998 -4.150285005\n20090184352.437 3923.157564 -1917.274669 5661.779621 5.622815776 -1.902658091 -4.529267262\n20090184452.437 4252.629072 -2027.607829 5379.093303 5.355977415 -1.773910426 -4.890537084\n20090184552.438 4565.454650 -2130.004610 5075.297949 5.068131657 -1.638198207 -5.232670449\n20090184652.438 4860.407121 -2224.062913 4751.582647 4.760401074 -1.496051826 -5.554316609\n20090184752.438 5136.329082 -2309.413262 4409.215191 4.433988183 -1.348027904 -5.854203792\n20090184852.438 5392.137572 -2385.720309 4049.537176 4.090171063 -1.194707051 -6.131144712\n20090184952.438 5626.828455 -2452.684200 3673.958773 3.730298408 -1.036691459 -6.384041406\n20090185052.438 5839.480522 -2510.041810 3283.953237 3.355784875 -0.874602755 -6.611889945\n20090185152.437 6029.259294 -2557.567834 2881.051109 2.968105821 -0.709079671 -6.813785484\n20090185252.437 6195.420471 -2595.075738 2466.834134 2.568790899 -0.540775331 -6.988926806\n20090185352.437 6337.313006 -2622.418539 2042.928930 2.159417590 -0.370354527 -7.136619912\n20090185452.437 6454.381765 -2639.489420 1611.000461 1.741604556 -0.198490869 -7.256280983\n20090185552.437 6546.169804 -2646.222176 1172.745350 1.317005015 -0.025863968 -7.347439001\n20090185652.438 6612.320241 -2642.591488 729.885039 0.887299878 0.146843350 -7.409738011\n20090185752.438 6652.577694 -2628.613029 284.158834 0.454190412 0.318947964 -7.442938697\n20090185852.438 6666.789294 -2604.343401 -162.683130 0.019391281 0.489769322 -7.446919583\n20090185952.438 6654.905265 -2569.879881 -608.886984 -0.415377036 0.658632454 -7.421677795\n20090190052.438 6616.979042 -2525.360006 -1052.702244 -0.848395994 0.824870985 -7.367328894\n20090190152.438 6553.166929 -2470.960963 -1492.388894 -1.277956388 0.987829985 -7.284105998\n20090190252.437 6463.727309 -2406.898823 -1926.224391 -1.702365928 1.146868752 -7.172358262\n20090190352.437 6349.019420 -2333.427607 -2352.510575 -2.119956347 1.301363455 -7.032548726\n20090190452.437 6209.501706 -2250.838192 -2769.580415 -2.529090096 1.450709724 -6.865251656\n20090190552.437 6045.729775 -2159.457075 -3175.804606 -2.928166964 1.594325073 -6.671149694\n20090190652.437 5858.353970 -2059.644985 -3569.597966 -3.315630505 1.731651201 -6.451030430\n20090190752.438 5648.116549 -1951.795371 -3949.425615 -3.689974155 1.862156222 -6.205782298\n20090190852.438 5415.848532 -1836.332754 -4313.808907 -4.049746799 1.985336490 -5.936390547\n20090190952.438 5162.466198 -1713.710980 -4661.331101 -4.393558446 2.100718445 -5.643932730\n20090191052.438 4888.967258 -1584.411363 -4990.642753 -4.720085507 2.207860388 -5.329573539\n20090191152.438 4596.426732 -1448.940726 -5300.466778 -5.028075349 2.306353880 -4.994559465\n20090191252.438 4285.992562 -1307.829369 -5589.603199 -5.316350511 2.395824993 -4.640213267\n20090191352.437 3958.880990 -1161.628964 -5856.933556 -5.583812443 2.475935445 -4.267928575\n20090191452.437 3616.371712 -1010.910385 -6101.425000 -5.829445081 2.546383684 -3.879164465\n20090191552.437 3259.802822 -856.261467 -6322.134041 -6.052318610 2.606905964 -3.475439590",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = await response.parse()
            assert ephemeris is None

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.queryhelp()
        assert_matches_type(EphemerisQueryhelpResponse, ephemeris, path=["response"])

    @parametrize
    async def test_raw_response_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.ephemeris.with_raw_response.queryhelp()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = await response.parse()
        assert_matches_type(EphemerisQueryhelpResponse, ephemeris, path=["response"])

    @parametrize
    async def test_streaming_response_queryhelp(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.ephemeris.with_streaming_response.queryhelp() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = await response.parse()
            assert_matches_type(EphemerisQueryhelpResponse, ephemeris, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.tuple(
            columns="columns",
            es_id="esId",
        )
        assert_matches_type(EphemerisTupleResponse, ephemeris, path=["response"])

    @parametrize
    async def test_method_tuple_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.tuple(
            columns="columns",
            es_id="esId",
            first_result=0,
            max_results=0,
        )
        assert_matches_type(EphemerisTupleResponse, ephemeris, path=["response"])

    @parametrize
    async def test_raw_response_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.ephemeris.with_raw_response.tuple(
            columns="columns",
            es_id="esId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = await response.parse()
        assert_matches_type(EphemerisTupleResponse, ephemeris, path=["response"])

    @parametrize
    async def test_streaming_response_tuple(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.ephemeris.with_streaming_response.tuple(
            columns="columns",
            es_id="esId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = await response.parse()
            assert_matches_type(EphemerisTupleResponse, ephemeris, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_unvalidated_publish(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.unvalidated_publish(
            category="ANALYST",
            classification_marking="U",
            data_mode="TEST",
            num_points=1,
            point_end_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            point_start_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            source="Bluestaq",
            type="LAUNCH",
        )
        assert ephemeris is None

    @parametrize
    async def test_method_unvalidated_publish_with_all_params(self, async_client: AsyncUnifieddatalibrary) -> None:
        ephemeris = await async_client.ephemeris.unvalidated_publish(
            category="ANALYST",
            classification_marking="U",
            data_mode="TEST",
            num_points=1,
            point_end_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            point_start_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            source="Bluestaq",
            type="LAUNCH",
            id="EPHEMERISSET-ID",
            b_dot=1.1,
            cent_body="Earth",
            comments="Example notes",
            cov_reference_frame="J2000",
            description="Example notes",
            descriptor="Example descriptor",
            drag_model="JAC70",
            edr=1.1,
            ephemeris_list=[
                {
                    "classification_marking": "U",
                    "data_mode": "TEST",
                    "source": "Bluestaq",
                    "ts": parse_datetime("2018-01-01T16:00:00.123456Z"),
                    "xpos": 1.1,
                    "xvel": 1.1,
                    "ypos": 1.1,
                    "yvel": 1.1,
                    "zpos": 1.1,
                    "zvel": 1.1,
                    "id": "EPHEMERIS-ID",
                    "cov": [1.1, 2.4, 3.8, 4.2, 5.5, 6],
                    "es_id": "ES-ID",
                    "id_on_orbit": "ONORBIT-ID",
                    "origin": "THIRD_PARTY_DATASOURCE",
                    "orig_object_id": "ORIGOBJECT-ID",
                    "xaccel": 1.1,
                    "yaccel": 1.1,
                    "zaccel": 1.1,
                }
            ],
            filename="Example file name",
            geopotential_model="GEM-T3",
            has_accel=False,
            has_cov=False,
            has_mnvr=False,
            id_maneuvers=["EXAMPLE_ID1", "EXAMPLE_ID2"],
            id_on_orbit="ONORBIT-ID",
            id_state_vector="STATEVECTOR-ID",
            integrator="COWELL",
            interpolation="LINEAR",
            interpolation_degree=5,
            lunar_solar=False,
            origin="THIRD_PARTY_DATASOURCE",
            orig_object_id="ORIGOBJECT-ID",
            pedigree="PROPAGATED",
            reference_frame="J2000",
            sat_no=2,
            solid_earth_tides=False,
            step_size=1,
            tags=["PROVIDER_TAG1", "PROVIDER_TAG2"],
            transaction_id="TRANSACTION-ID",
            usable_end_time=parse_datetime("2018-01-01T20:50:00.123456Z"),
            usable_start_time=parse_datetime("2018-01-01T16:10:00.123456Z"),
        )
        assert ephemeris is None

    @parametrize
    async def test_raw_response_unvalidated_publish(self, async_client: AsyncUnifieddatalibrary) -> None:
        response = await async_client.ephemeris.with_raw_response.unvalidated_publish(
            category="ANALYST",
            classification_marking="U",
            data_mode="TEST",
            num_points=1,
            point_end_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            point_start_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            source="Bluestaq",
            type="LAUNCH",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ephemeris = await response.parse()
        assert ephemeris is None

    @parametrize
    async def test_streaming_response_unvalidated_publish(self, async_client: AsyncUnifieddatalibrary) -> None:
        async with async_client.ephemeris.with_streaming_response.unvalidated_publish(
            category="ANALYST",
            classification_marking="U",
            data_mode="TEST",
            num_points=1,
            point_end_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            point_start_time=parse_datetime("2018-01-01T16:00:00.123456Z"),
            source="Bluestaq",
            type="LAUNCH",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ephemeris = await response.parse()
            assert ephemeris is None

        assert cast(Any, response.is_closed) is True
