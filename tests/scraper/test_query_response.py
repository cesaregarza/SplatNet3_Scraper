import pytest

from splatnet3_scraper.scraper.json_parser import JSONParser
from splatnet3_scraper.scraper.responses import QueryResponse


class TestQueryResponse:
    def test_init(self):
        # No detailed
        response = QueryResponse({"test_key": "test_value"})
        assert response.summary == JSONParser({"test_key": "test_value"})
        with pytest.raises(AttributeError):
            response.detailed
        assert response._detailed is None
        # Detailed
        response = QueryResponse(
            {"test_key": "test_value"}, [{"test_key": "test_value"}]
        )
        assert response.summary == JSONParser({"test_key": "test_value"})
        assert response.detailed == JSONParser([{"test_key": "test_value"}])
        # Detailed None
        response = QueryResponse({"test_key": "test_value"}, None)
        assert response.summary == JSONParser({"test_key": "test_value"})
        with pytest.raises(AttributeError):
            response.detailed
        assert response._detailed is None

    def test_repr(self):
        # No detailed
        response = QueryResponse({"test_key": "test_value"})
        assert repr(response) == "QueryResponse()"
        # Detailed
        response = QueryResponse(
            {"test_key": "test_value"}, [{"test_key": "test_value"}]
        )
        assert repr(response) == "QueryResponse(Detailed)"
