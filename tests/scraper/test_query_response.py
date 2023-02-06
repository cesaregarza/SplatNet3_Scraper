from unittest.mock import patch

import pytest

from splatnet3_scraper.scraper.json_parser import JSONParser
from splatnet3_scraper.scraper.responses import QueryResponse


class TestQueryResponse:
    def test_init(self):
        # No detailed
        response = QueryResponse({"test_key": "test_value"})
        assert response.data == {"test_key": "test_value"}
        with pytest.raises(AttributeError):
            response.additional_data
        assert response._additional_data is None
        # Detailed
        response = QueryResponse(
            {"test_key": "test_value"}, [{"test_key": "test_value"}]
        )
        assert response.data == {"test_key": "test_value"}
        assert response.additional_data == response._additional_data
        # Detailed None
        response = QueryResponse({"test_key": "test_value"}, None)
        assert response.data == {"test_key": "test_value"}
        with pytest.raises(AttributeError):
            response.additional_data
        assert response._additional_data is None

    def test_parse_json(self, json_small: dict, json_deep_nested: dict):
        # No detailed
        response = QueryResponse(json_small)
        parser = response.parse_json()
        assert parser == JSONParser(json_small)
        # Detailed
        response = QueryResponse(json_small, json_deep_nested)
        parser = response.parse_json(additional=True)
        assert parser == JSONParser(json_deep_nested)
        # Detailed None
        response = QueryResponse(json_small, None)
        with pytest.raises(AttributeError):
            response.parse_json(additional=True)

    def test_repr(self):
        # No detailed
        response = QueryResponse({"test_key": "test_value"})
        assert repr(response) == "QueryResponse()"
        # Detailed
        response = QueryResponse(
            {"test_key": "test_value"}, [{"test_key": "test_value"}]
        )
        assert repr(response) == "QueryResponse+()"

    def test_eq(self, json_small: dict):
        response = QueryResponse(json_small)
        assert response == QueryResponse(json_small)
        assert response != QueryResponse(json_small, json_small)
        assert response == QueryResponse(json_small, None)
        assert response != json_small

    def test_getitem(self, json_deep_nested: dict):
        response = QueryResponse(json_deep_nested)
        assert response["c"] == QueryResponse(json_deep_nested["c"])
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
