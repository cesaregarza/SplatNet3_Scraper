from unittest import mock

import pytest
import requests
from pytest_lazyfixture import lazy_fixture

from splatnet3_scraper.utils import (
    delinearize_json,
    get_splatnet_web_version,
    linearize_json,
    retry,
)


class TestRetry:
    def test_success(self):
        @retry(times=1)
        def test_func():
            return True

        assert test_func()

    @mock.patch("splatnet3_scraper.utils.logger")
    def test_failure(self, mock_logger):
        count = 0

        @retry(times=1)
        def test_func():
            nonlocal count
            count += 1
            raise Exception

        with pytest.raises(Exception):
            test_func()

        assert mock_logger.log.call_count == 1
        assert count == 2

    @mock.patch("splatnet3_scraper.utils.logger")
    def test_success_after_failure(self, mock_logger):
        count = 0

        @retry(times=2)
        def test_func():
            nonlocal count
            count += 1
            if count < 2:
                raise Exception
            return True

        assert test_func()

        assert mock_logger.log.call_count == 1
        assert count == 2

    @mock.patch("splatnet3_scraper.utils.logger")
    def test_multiple_exceptions(self, mock_logger):
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

        assert mock_logger.log.call_count == 2
        assert count == 3

    @mock.patch("splatnet3_scraper.utils.logger")
    def test_exception_not_defined(self, mock_logger):
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

        assert mock_logger.log.call_count == 1
        assert count == 2


class TestGetSplatnetWebVersion:
    class MockResponse:
        @staticmethod
        def json():
            return {"version": "test_version"}

    def test_success(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            return self.MockResponse()

        monkeypatch.setattr(requests, "get", mock_get)

        assert get_splatnet_web_version() == "test_version"

    def test_cache(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            return self.MockResponse()

        monkeypatch.setattr(requests, "get", mock_get)

        assert get_splatnet_web_version() == "test_version"

        class MockResponse2:
            @staticmethod
            def json():
                return {"version": "test_version2"}

        def mock_get2(*args, **kwargs):
            return MockResponse2()

        monkeypatch.setattr(requests, "get", mock_get2)

        assert get_splatnet_web_version() == "test_version"


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
