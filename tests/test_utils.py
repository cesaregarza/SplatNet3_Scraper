import datetime as dt
from unittest import mock

import freezegun
import pytest
import requests
from pytest_lazyfixture import lazy_fixture

from splatnet3_scraper.constants import (
    GRAPH_QL_REFERENCE_URL,
    HASHES_FALLBACK,
    WEB_VIEW_VERSION_FALLBACK,
)
from splatnet3_scraper.utils import (
    delinearize_json,
    enumerate_all_paths,
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
                [(":", "e"), (":", "d")],
                [("c", 0, "e"), ("c", 1, "e"), ("c", 0, "d"), ("c", 1, "d")],
            )
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
    def test_get_hash_data(self):
        response_json = {
            "graphql": {
                "hash_map": {
                    "test_query": "test_hash",
                },
            },
            "version": "test_version",
        }
        with mock.patch.object(
            requests, "get", return_value=MockResponse(200, json=response_json)
        ) as mock_get:
            assert get_hash_data("test_query", 0) == (
                {"test_query": "test_hash"},
                "test_version",
            )
            mock_get.assert_called_once_with("test_query")

        with mock.patch.object(
            requests, "get", return_value=MockResponse(200, json=response_json)
        ) as mock_get:
            # Test if feeding no parameters returns the same result
            assert get_hash_data() == (
                {"test_query": "test_hash"},
                "test_version",
            )
            mock_get.assert_called_once_with(GRAPH_QL_REFERENCE_URL)

    def test_get_ttl_hash(self):
        frozen_time = "2023-04-14 12:00:00"
        with freezegun.freeze_time(frozen_time) as frozen_datetime:
            ft = get_ttl_hash()
            frozen_datetime.tick(delta=dt.timedelta(minutes=1))
            assert ft == get_ttl_hash()
            frozen_datetime.tick(delta=dt.timedelta(minutes=15))
            assert ft != get_ttl_hash()

    @mock.patch("logging.warning")
    def test_get_splatnet_hashes(self, mock_warning: mock.MagicMock):
        expected_hash = {
            "test_query": "test_hash",
        }
        frozen_time = "2023-04-14 12:00:00"
        with (
            mock.patch(
                utils_path + ".get_hash_data",
                return_value=(expected_hash, "test_version"),
            ) as mock_get_hash_data,
            freezegun.freeze_time(frozen_time),
        ):
            assert get_splatnet_hashes() == {"test_query": "test_hash"}
            ft = get_ttl_hash()
            mock_get_hash_data.assert_called_once_with(None, ft)

        def new_get_hash_data(*args, **kwargs):
            raise requests.exceptions.RequestException()

        with (
            mock.patch(
                utils_path + ".get_hash_data",
                side_effect=new_get_hash_data,
            ) as mock_get_hash_data,
            freezegun.freeze_time(frozen_time),
        ):
            assert get_splatnet_hashes() == HASHES_FALLBACK
            mock_get_hash_data.assert_called_once_with(None, ft)
            assert mock_warning.call_count == 2

    @mock.patch("logging.warning")
    def test_get_splatnet_version(self, mock_warning: mock.MagicMock):
        expected_version = "test_version"
        frozen_time = "2023-04-14 12:00:00"
        hash_return = {"graphql": {"hash_map": {"test_query": "test_hash"}}}
        with (
            mock.patch(
                utils_path + ".get_hash_data",
                return_value=(hash_return, expected_version),
            ) as mock_get_hash_data,
            freezegun.freeze_time(frozen_time),
        ):
            assert get_splatnet_version() == expected_version
            ft = get_ttl_hash()
            mock_get_hash_data.assert_called_once_with(None, ft)

        def new_get_hash_data(*args, **kwargs):
            raise requests.exceptions.RequestException()

        with (
            mock.patch(
                utils_path + ".get_hash_data",
                side_effect=new_get_hash_data,
            ) as mock_get_hash_data,
            freezegun.freeze_time(frozen_time),
        ):
            assert get_splatnet_version() == WEB_VIEW_VERSION_FALLBACK
            mock_get_hash_data.assert_called_once_with(None, ft)
            assert mock_warning.call_count == 2
