from unittest.mock import patch

import pytest
from pytest_lazyfixture import lazy_fixture

from splatnet3_scraper.query.json_parser import JSONParser
from splatnet3_scraper.query.responses import QueryResponse

param = pytest.mark.parametrize


class TestQueryResponse:
    @param("invalid", [True, False], ids=["NV", "V"])
    @param("timestamp_", [None, lazy_fixture("timestamp")], ids=["NT", "T"])
    @param("query", [None, "test_query"], ids=["NQ", "Q"])
    def test_init_metadata(
        self, invalid, timestamp_, query, timestamp_datetime
    ):
        # Build metadata
        metadata = {
            "query": query,
            "timestamp": timestamp_,
            "invalid": invalid,
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}
        # If not invalid, pop invalid
        if not invalid:
            metadata.pop("invalid", None)

        test_data = {"test_key": "test_value"}
        response = QueryResponse(test_data, metadata)
        expected_metadata = metadata.copy()
        expected_metadata.pop("invalid", None)
        assert response.data == test_data

        keys = (  # (attr, expected, should_raise)
            ("query", "test_query", query is None),
            ("timestamp_raw", timestamp_, timestamp_ is None),
            ("timestamp", timestamp_datetime, timestamp_ is None),
            ("metadata", expected_metadata, len(expected_metadata) == 0),
        )

        for attr, expected, should_raise in keys:
            if should_raise:
                with pytest.raises(ValueError):
                    getattr(response, attr)
            else:
                assert getattr(response, attr) == expected

    def test_parse_json(self, json_small: dict):
        # No detailed
        response = QueryResponse(json_small)
        parser = response.parse_json()
        assert parser == JSONParser(json_small)

    @param(
        "query",
        [None, "test_query", "test_long_query_over_20_characters"],
        ids=["NQ", "Q", "LQ"],
    )
    @param("timestamp_", [None, lazy_fixture("timestamp")], ids=["NT", "T"])
    @param("mocked_float", [True, False], ids=["MF", "NF"])
    def test_repr(
        self, query, timestamp_, timestamp_datetime_str, mocked_float
    ):
        test_data = {"test_key": "test_value"}
        metadata = {
            "query": query,
            "timestamp": timestamp_,
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}
        response = QueryResponse(test_data, metadata)

        if mocked_float:
            try:
                response._metadata["high_precision_float"] = 1.23456789
                metadata["high_precision_float"] = 1.23
            except TypeError:  # metadata is None
                pass

        expected = "QueryResponse("
        if len(metadata) == 0:
            expected += ")"
            assert repr(response) == expected
            return
        spaces = " " * len(expected)
        for key, value in metadata.items():
            if key == "timestamp":
                value = timestamp_datetime_str
            elif key == "query" and len(value) > 20:
                value = f"{value[:20]}..."
            elif key == "high_precision_float":
                value = f"{value:.2f}"

            expected += f"{spaces}{key}={value},\n"
        expected = expected[:-2] + ")"
        assert repr(response) == expected

    @param("metadata_1", [None, {"query": "test_query"}], ids=["NM1", "M1"])
    @param("metadata_2", [None, {"query": "test_query"}], ids=["NM2", "M2"])
    @param("other_data", [None, {"test_key": "test_value"}], ids=["ND", "D"])
    def test_eq(self, json_small: dict, metadata_1, metadata_2, other_data):
        response_1 = QueryResponse(json_small, metadata_1)
        other_data = other_data or json_small
        response_2 = QueryResponse(other_data, metadata_2)
        resp_eq = response_1 == response_2
        data_eq = json_small == other_data
        metadata_eq = metadata_1 == metadata_2
        assert resp_eq == (data_eq and metadata_eq)

        # Type check
        assert response_1 != "test_type"

    def test_getitem(self, json_deep_nested: dict):
        metadata = {"query": "test_query"}
        response = QueryResponse(json_deep_nested, metadata)
        assert response["c"] == QueryResponse(json_deep_nested["c"], metadata)
        assert response["c", "d"] == json_deep_nested["c"]["d"]
        assert response["c", "e", "g", "h"] == 5

    def test_keys(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        assert response.keys() == list(json_deep_nested.keys())

    def test_values(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        assert response.values() == list(json_deep_nested.values())

    def test_items(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        assert response.items() == list(json_deep_nested.items())

    def test_iter(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        assert list(response) == list(json_deep_nested)
        generator = iter(response)
        assert next(generator) == "a"

    def test_show(self, json_deep_nested: dict):
        # return_value False
        response = QueryResponse(json_deep_nested)
        with patch("builtins.print") as print_mock:
            response.show()
        print_mock.assert_called_once_with(json_deep_nested)

        # return_value True
        response = QueryResponse(json_deep_nested)
        with patch("builtins.print") as print_mock:
            ret_value = response.show(True)
        print_mock.assert_not_called()
        assert isinstance(ret_value, dict)
