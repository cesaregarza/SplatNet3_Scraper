import pytest

from splatnet3_scraper.scraper.json_parser import JSONParser
from splatnet3_scraper.scraper.responses import QueryResponse


class TestQueryResponse:
    def test_init(self):
        # No detailed
        response = QueryResponse({"test_key": "test_value"})
        assert response.data == JSONParser({"test_key": "test_value"})
        with pytest.raises(AttributeError):
            response.additional_data
        assert response._additional_data is None
        # Detailed
        response = QueryResponse(
            {"test_key": "test_value"}, [{"test_key": "test_value"}]
        )
        assert response.data == JSONParser({"test_key": "test_value"})
        assert response.additional_data == JSONParser(
            [{"test_key": "test_value"}]
        )
        assert response._additional_data == [{"test_key": "test_value"}]
        # Detailed None
        response = QueryResponse({"test_key": "test_value"}, None)
        assert response.data == JSONParser({"test_key": "test_value"})
        with pytest.raises(AttributeError):
            response.additional_data
        assert response._additional_data is None

    def test_repr(self):
        # No detailed
        response = QueryResponse({"test_key": "test_value"})
        assert repr(response) == "QueryResponse()"
        # Detailed
        response = QueryResponse(
            {"test_key": "test_value"}, [{"test_key": "test_value"}]
        )
        assert repr(response) == "QueryResponse+()"

    def test_eq(self, json_small):
        response = QueryResponse(json_small)
        assert response == QueryResponse(json_small)
        assert response != QueryResponse(json_small, json_small)
        assert response == QueryResponse(json_small, None)
        assert response != json_small

    def test_getitem(self, json_deep_nested):
        response = QueryResponse(json_deep_nested)
        assert response["c"] == QueryResponse(json_deep_nested["c"])
        assert response["c", "d"] == json_deep_nested["c"]["d"]
        assert response["c", "e", "g", "h"] == 5
