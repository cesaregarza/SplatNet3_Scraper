import datetime as dt
import json
from unittest import mock

import freezegun
import pytest
import requests
from pytest_lazyfixture import lazy_fixture

from splatnet3_scraper.constants import GRAPH_QL_REFERENCE_URL
from splatnet3_scraper.utils import (
    delinearize_json,
    enumerate_all_paths,
    fallback_path,
    get_fallback_hash_data,
    get_hash_data,
    get_splatnet_hashes,
    get_splatnet_version,
    get_ttl_hash,
    linearize_json,
    match_partial_path,
    retry,
)
from tests.mock import MockResponse

utils_path = "splatnet3_scraper.utils"


class TestRetry:
    def test_success(self):
        @retry(times=1)
        def test_func():
            return True

        assert test_func()

    @mock.patch("logging.warning")
    def test_failure(self, mock_logger: mock.MagicMock):
        count = 0

        @retry(times=1)
        def test_func():
            nonlocal count
            count += 1
            raise Exception

        with pytest.raises(Exception):
            test_func()

        assert mock_logger.call_count == 1
        assert count == 2

    @mock.patch("logging.warning")
    def test_success_after_failure(self, mock_logger: mock.MagicMock):
        count = 0

        @retry(times=2)
        def test_func():
            nonlocal count
            count += 1
            if count < 2:
                raise Exception
            return True

        assert test_func()

        assert mock_logger.call_count == 1
        assert count == 2

    @mock.patch("logging.warning")
    def test_multiple_exceptions(self, mock_logger: mock.MagicMock):
        count = 0

        @retry(times=2, exceptions=(ValueError, TypeError))
        def test_func():
            nonlocal count
            count += 1
            if count == 1:
                raise ValueError
            elif count == 2:
                raise TypeError
            return True

        assert test_func()

        assert mock_logger.call_count == 2
        assert count == 3

    @mock.patch("logging.warning")
    def test_exception_not_defined(self, mock_logger: mock.MagicMock):
        count = 0

        @retry(times=2, exceptions=(ValueError, TypeError))
        def test_func():
            nonlocal count
            count += 1
            if count == 1:
                raise ValueError
            elif count == 2:
                raise IndexError
            return True

        with pytest.raises(IndexError):
            test_func()

        assert mock_logger.call_count == 1
        assert count == 2


class TestLinearizeJSON:
    @pytest.mark.parametrize(
        "input, expected",
        [
            (lazy_fixture("json_small"), lazy_fixture("json_small_linear")),
            (lazy_fixture("json_nested"), lazy_fixture("json_nested_linear")),
            (lazy_fixture("json_list"), lazy_fixture("json_list_linear")),
            (
                lazy_fixture("json_nested_list"),
                lazy_fixture("json_nested_list_linear"),
            ),
            (
                lazy_fixture("json_deep_nested"),
                lazy_fixture("json_deep_nested_linear"),
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                lazy_fixture("json_deep_nested_list_linear"),
            ),
            (
                lazy_fixture("json_with_none"),
                lazy_fixture("json_with_none_linear"),
            ),
        ],
        ids=[
            "small",
            "nested",
            "list",
            "nested_list",
            "deep_nested",
            "deep_nested_list",
            "with_none",
        ],
    )
    def test_linearize_json(self, input, expected):
        assert linearize_json(input) == expected


class TestDelinearizeJSON:
    @pytest.mark.parametrize(
        "input, expected",
        [
            (lazy_fixture("json_small_linear"), lazy_fixture("json_small")),
            (lazy_fixture("json_nested_linear"), lazy_fixture("json_nested")),
            (lazy_fixture("json_list_linear"), lazy_fixture("json_list")),
            (
                lazy_fixture("json_nested_list_linear"),
                lazy_fixture("json_nested_list"),
            ),
            (
                lazy_fixture("json_deep_nested_linear"),
                lazy_fixture("json_deep_nested"),
            ),
            (
                lazy_fixture("json_deep_nested_list_linear"),
                lazy_fixture("json_deep_nested_list"),
            ),
            (
                lazy_fixture("json_with_none_linear"),
                lazy_fixture("json_with_none"),
            ),
            (
                lazy_fixture("json_linear_inserted_none"),
                lazy_fixture("json_with_none"),
            ),
        ],
        ids=[
            "small",
            "nested",
            "list",
            "nested_list",
            "deep_nested",
            "deep_nested_list",
            "with_none",
            "inserted_none",
        ],
    )
    def test_delinearize_json(self, input, expected):
        assert delinearize_json(*input) == expected


class TestEnumerateAllPaths:
    @pytest.mark.parametrize(
        "input, expected",
        [
            (lazy_fixture("json_small"), lazy_fixture("json_small_keys")),
            (lazy_fixture("json_nested"), lazy_fixture("json_nested_keys")),
            (
                lazy_fixture("json_nested_list"),
                lazy_fixture("json_nested_list_keys"),
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                lazy_fixture("json_deep_nested_list_keys"),
            ),
        ],
        ids=[
            "small",
            "nested",
            "nested_list",
            "deep_nested_list",
        ],
    )
    def test_enumerate_all_paths(self, input, expected):
        assert enumerate_all_paths(input) == expected


class TestMatchPartialPath:
    @pytest.mark.parametrize(
        "input, path, expected",
        [
            (
                lazy_fixture("json_nested_list"),
                "d",
                lazy_fixture("json_nested_list_exp_pp"),
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                ("g", "h"),
                lazy_fixture("json_deep_nested_list_exp_pp"),
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                [("g", "h"), ("g", "i")],
                lazy_fixture("json_deep_nested_list_exp_pp_2"),
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                (":", "e"),
                [("c", 0, "e"), ("c", 1, "e")],
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                [("c", ":", "e"), (":", "d")],
                [("c", 0, "e"), ("c", 1, "e"), ("c", 0, "d"), ("c", 1, "d")],
            ),
        ],
        ids=[
            "nested_list",
            "deep_nested_list",
            "list_of_paths",
            "path_with_wildcard",
            "list_of_paths_with_wildcard",
        ],
    )
    def test_match_partial_path(self, input, path, expected):
        assert match_partial_path(input, path) == expected


class TestHash:
    TEST_HASH = "test_hash"
    TEST_QUERY = "test_query"
    TEST_VERSION = "test_version"
    TEST_HASH_MAP = {
        TEST_QUERY: TEST_HASH,
    }
    TEST_HASH_MAP = {
        "hash_map": TEST_HASH,
    }
    TEST_RESPONSE_JSON = {
        "graphql": {
            "hash_map": TEST_HASH_MAP,
        },
        "version": TEST_VERSION,
    }
    FROZEN_TIME = "2023-04-14 12:00:00"

    @pytest.mark.parametrize(
        "args, expected_url",
        [
            ((), GRAPH_QL_REFERENCE_URL),
            (("test_query",), "test_query"),
            (("test_query", 0), "test_query"),
        ],
        ids=[
            "no_args",
            "query_only",
            "query_and_version",
        ],
    )
    def test_get_hash_data_explicit(self, args: tuple, expected_url: str):
        with mock.patch.object(
            requests,
            "get",
            return_value=MockResponse(200, json=self.TEST_RESPONSE_JSON),
        ) as mock_get:
            assert get_hash_data(*args) == (
                self.TEST_HASH_MAP,
                self.TEST_VERSION,
            )
            mock_get.assert_called_once_with(expected_url)

    def test_get_ttl_hash(self):
        with freezegun.freeze_time(self.FROZEN_TIME) as frozen_datetime:
            ft = get_ttl_hash()
            frozen_datetime.tick(delta=dt.timedelta(minutes=1))
            assert ft == get_ttl_hash()
            frozen_datetime.tick(delta=dt.timedelta(minutes=15))
            assert ft != get_ttl_hash()

    def test_get_fallback_hash_data(self):
        with open(fallback_path, "r") as fallback_file:
            expected_fallback_data = json.load(fallback_file)

        fallback_data = get_fallback_hash_data()
        assert fallback_data == (
            expected_fallback_data["graphql"]["hash_map"],
            expected_fallback_data["version"],
        )

    def test_get_splatnet_hashes_success(self):
        with (
            mock.patch(
                utils_path + ".get_hash_data",
                return_value=(self.TEST_HASH_MAP, self.TEST_VERSION),
            ) as mock_get_hash_data,
            freezegun.freeze_time(self.FROZEN_TIME),
            mock.patch(
                "logging.warning",
            ) as mock_warning,
        ):
            assert get_splatnet_hashes() == self.TEST_HASH_MAP
            ft = get_ttl_hash()
            mock_get_hash_data.assert_called_once_with(None, ft)
            mock_warning.assert_not_called()

    def test_get_splatnet_hashes_failure(self):
        def get_hash_data_fail(*args, **kwargs):
            raise requests.exceptions.RequestException()

        with (
            mock.patch(
                utils_path + ".get_hash_data",
                side_effect=get_hash_data_fail,
            ) as mock_get_hash_data,
            freezegun.freeze_time(self.FROZEN_TIME),
            mock.patch(
                utils_path + ".get_fallback_hash_data",
                return_value=(self.TEST_HASH_MAP, self.TEST_VERSION),
            ) as mock_get_fallback_hash_data,
            mock.patch(
                "logging.warning",
            ) as mock_warning,
        ):
            assert get_splatnet_hashes() == self.TEST_HASH_MAP
            ft = get_ttl_hash()
            mock_get_hash_data.assert_called_once_with(None, ft)
            mock_get_fallback_hash_data.assert_called_once()
            assert mock_warning.call_count == 2

    def test_get_splatnet_hashes_success_empty(self):
        with (
            mock.patch(
                utils_path + ".get_hash_data",
                return_value=({}, self.TEST_VERSION),
            ) as mock_get_hash_data,
            freezegun.freeze_time(self.FROZEN_TIME),
            mock.patch(
                utils_path + ".get_fallback_hash_data",
                return_value=(self.TEST_HASH_MAP, self.TEST_VERSION),
            ) as mock_get_fallback_hash_data,
            mock.patch(
                "logging.warning",
            ) as mock_warning,
        ):
            assert get_splatnet_hashes() == self.TEST_HASH_MAP
            ft = get_ttl_hash()
            mock_get_hash_data.assert_called_once_with(None, ft)
            mock_get_fallback_hash_data.assert_called_once()
            assert mock_warning.call_count == 2

    def test_get_splatnet_version_success(self):
        with (
            mock.patch(
                utils_path + ".get_hash_data",
                return_value=(self.TEST_HASH_MAP, self.TEST_VERSION),
            ) as mock_get_hash_data,
            freezegun.freeze_time(self.FROZEN_TIME),
            mock.patch(
                "logging.warning",
            ) as mock_warning,
        ):
            assert get_splatnet_version() == self.TEST_VERSION
            ft = get_ttl_hash()
            mock_get_hash_data.assert_called_once_with(None, ft)
            mock_warning.assert_not_called()

    def test_get_splatnet_version_failure(self):
        def get_hash_data_fail(*args, **kwargs):
            raise requests.exceptions.RequestException()

        with (
            mock.patch(
                utils_path + ".get_hash_data",
                side_effect=get_hash_data_fail,
            ) as mock_get_hash_data,
            freezegun.freeze_time(self.FROZEN_TIME),
            mock.patch(
                utils_path + ".get_fallback_hash_data",
                return_value=(self.TEST_HASH_MAP, self.TEST_VERSION),
            ) as mock_get_fallback_hash_data,
            mock.patch(
                "logging.warning",
            ) as mock_warning,
        ):
            assert get_splatnet_version() == self.TEST_VERSION
            ft = get_ttl_hash()
            mock_get_hash_data.assert_called_once_with(None, ft)
            mock_get_fallback_hash_data.assert_called_once()
            assert mock_warning.call_count == 2

    def test_get_splatnet_version_success_empty(self):
        with (
            mock.patch(
                utils_path + ".get_hash_data",
                return_value=({}, self.TEST_VERSION),
            ) as mock_get_hash_data,
            freezegun.freeze_time(self.FROZEN_TIME),
            mock.patch(
                utils_path + ".get_fallback_hash_data",
                return_value=(self.TEST_HASH_MAP, self.TEST_VERSION),
            ) as mock_get_fallback_hash_data,
            mock.patch(
                "logging.warning",
            ) as mock_warning,
        ):
            assert get_splatnet_version() == self.TEST_VERSION
            ft = get_ttl_hash()
            mock_get_hash_data.assert_called_once_with(None, ft)
            mock_get_fallback_hash_data.assert_called_once()
            assert mock_warning.call_count == 2
