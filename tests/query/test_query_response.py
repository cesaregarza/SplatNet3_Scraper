from unittest.mock import mock_open, patch

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

    def test_getitem(self, json_deep_nested_list: dict):
        metadata = {"query": "test_query"}
        response = QueryResponse(json_deep_nested_list, metadata)
        assert response["c"] == QueryResponse(
            json_deep_nested_list["c"], metadata
        )
        assert response["c", 0, "d"] == json_deep_nested_list["c"][0]["d"]
        assert response["c", 0, "e", "g", "h"] == 5

    @param(
        "data", [lazy_fixture("json_deep_nested"), [1, 2, 3]], ids=["D", "L"]
    )
    def test_keys(self, data):
        response = QueryResponse(data)
        if isinstance(data, list):
            assert response.keys() == list(range(len(data)))
        else:
            assert response.keys() == list(data.keys())

    def test_values(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        expected_values = [
            val if not isinstance(val, dict) else QueryResponse(val)
            for val in json_deep_nested.values()
        ]
        assert response.values() == expected_values

    def test_items(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        assert response.items() == list(json_deep_nested.items())

    def test_iter(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        assert list(response) == [
            val if not isinstance(val, dict) else QueryResponse(val)
            for val in json_deep_nested.values()
        ]
        generator = iter(response)
        assert next(generator) == json_deep_nested["a"]

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

    def test_get(self, json_deep_nested_list: dict):
        response = QueryResponse(json_deep_nested_list)
        assert response.get("a") == json_deep_nested_list["a"]
        assert response.get("a", "default") == json_deep_nested_list["a"]
        assert response.get("d") is None
        assert response.get(("c", 0, "d")) == json_deep_nested_list["c"][0]["d"]

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
        ],
        ids=[
            "nested_list",
            "deep_nested_list",
            "list_of_paths",
        ],
    )
    def test_match_partial_path(self, input, path, expected):
        response = QueryResponse(input)
        assert response.match_partial_path(path) == expected

    def test_match_partial_path_args(
        self, json_deep_nested_list: dict, json_deep_nested_list_exp_pp: dict
    ):
        response = QueryResponse(json_deep_nested_list)
        assert (
            response.match_partial_path("g", "h")
            == json_deep_nested_list_exp_pp
        )

    def test_match_partial_path_error(self, json_deep_nested_list: dict):
        response = QueryResponse(json_deep_nested_list)
        with pytest.raises(TypeError):
            response.match_partial_path(("g", "h"), "i")

    @pytest.mark.parametrize(
        "data, path, partial, func, expected",
        [
            (
                lazy_fixture("json_nested_list"),
                "d",
                True,
                lambda x: x + 1,
                [4, 6],
            ),
            (
                lazy_fixture("json_nested_list"),
                ("c", 0, "d"),
                False,
                lambda x: x + 1,
                4,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                ("g", "h"),
                True,
                lambda x: x + 1,
                [6, 10],
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                [("g", "h"), ("g", "i")],
                True,
                lambda x: x + 1,
                [6, 10, 7, 11],
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                [("c", 0, "e", "g", "h"), ("c", 1, "e", "g", "i")],
                False,
                lambda x: x + 1,
                [6, 11],
            ),
        ],
        ids=[
            "nested_list",
            "nested_list_partial_false",
            "deep_nested_list",
            "list_of_paths",
            "list_of_paths_partial_false",
        ],
    )
    def test_apply(self, data, path, partial, func, expected):
        response = QueryResponse(data)
        assert response.apply(func, path, partial=partial) == expected

    @pytest.mark.parametrize(
        "data, path, partial, func, reduce_func, expected",
        [
            (
                lazy_fixture("json_nested_list"),
                "d",
                True,
                lambda x: x + 1,
                sum,
                10,
            ),
            (
                lazy_fixture("json_nested_list"),
                ("c", 0, "d"),
                False,
                lambda x: x + 1,
                sum,
                4,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                ("g", "h"),
                True,
                lambda x: x + 1,
                sum,
                16,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                [("g", "h"), ("g", "i")],
                True,
                lambda x: x + 1,
                sum,
                34,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                [("c", 0, "e", "g", "h"), ("c", 1, "e", "g", "i")],
                False,
                lambda x: x + 1,
                sum,
                17,
            ),
        ],
        ids=[
            "nested_list",
            "nested_list_single_apply_result",
            "deep_nested_list",
            "list_of_paths",
            "list_of_paths_partial_false",
        ],
    )
    def test_apply_reduce(
        self, data, path, partial, func, reduce_func, expected
    ):
        response = QueryResponse(data)
        assert (
            response.apply_reduce(func, reduce_func, path, partial=partial)
            == expected
        )

    @pytest.mark.parametrize(
        "data, path, expected, unpack",
        [
            (
                lazy_fixture("json_nested_list"),
                "d",
                [3, 5],
                None,
            ),
            (
                lazy_fixture("json_nested_list"),
                ("c", 0, "d"),
                [3],
                None,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                ("g", "h"),
                [5, 9],
                None,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                [("g", "h"), ("g", "i")],
                [5, 9, 6, 10],
                None,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                [("c", 0, "e", "g", "h"), ("c", 1, "e", "g", "i")],
                [5, 10],
                None,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                ("e", "g"),
                [{"h": 5, "i": 6}, {"h": 9, "i": 10}],
                None,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                ("e", "g"),
                [{"h": 5, "i": 6}, {"h": 9, "i": 10}],
                True,
            ),
            (
                lazy_fixture("json_deep_nested_list"),
                ("e", "g"),
                [
                    QueryResponse({"h": 5, "i": 6}),
                    QueryResponse({"h": 9, "i": 10}),
                ],
                False,
            ),
        ],
        ids=[
            "nested_list",
            "nested_list_single_value",
            "deep_nested_list",
            "list_of_paths",
            "list_of_paths_from_root",
            "list_of_paths_no_kwarg",
            "list_of_paths_unpack",
            "list_of_paths_unpack_false",
        ],
    )
    def test_get_partial_path(self, data, path, expected, unpack):
        response = QueryResponse(data)
        if unpack is None:
            assert response.get_partial_path(path) == expected
        else:
            assert (
                response.get_partial_path(path, unpack_query_response=unpack)
                == expected
            )

    def test_to_json(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        path = "test.json"
        with (
            patch("json.dump", return_value=None) as mock_dump,
            patch("builtins.open", mock_open()) as mock_file,
        ):
            response.to_json("test.json")
            mock_file.assert_called_once_with(path, "w", encoding="utf-8")
            mock_dump.assert_called_once_with(
                response.data, mock_file(), ensure_ascii=False, indent=4
            )

    def test_to_gzipped_json(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        path = "test.json.gz"
        with (
            patch("gzip.open", mock_open()) as mock_file,
            patch("json.dump", return_value=None) as mock_dump,
        ):
            response.to_gzipped_json("test.json.gz")
            mock_file.assert_called_once_with(path, "wt", encoding="utf-8")
            mock_dump.assert_called_once_with(
                response.data, mock_file(), ensure_ascii=False, indent=4
            )
