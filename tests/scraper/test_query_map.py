import pytest

from splatnet3_scraper.scraper.query_map import QueryMap

class TestQueryMap:
    def test_get(self):
        # Valid
        assert QueryMap.get("ANARCHY") == QueryMap.ANARCHY
        # lowercase
        assert QueryMap.get("anarchy") == QueryMap.ANARCHY
        # Invalid
        with pytest.raises(AttributeError):
            QueryMap.get("invalid")