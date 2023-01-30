import pytest
import requests

from splatnet3_scraper.base.graph_ql_queries import GraphQLQueries


class TestGraphQLQueries:
    def test_get_hashes(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(self_, url: str) -> requests.Response:
            class MockResponse:
                def json(self) -> dict[str, str]:
                    return {"graphql": {"hash_map": {"test": "test"}}}

            return MockResponse()

        monkeypatch.setattr(requests.Session, "get", mock_get)
        queries = GraphQLQueries()
        assert queries.hash_map == {"test": "test"}

    def test_init(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get_hashes(self_) -> dict[str, str]:
            return {"test": "test"}

        monkeypatch.setattr(GraphQLQueries, "get_hashes", mock_get_hashes)
        queries = GraphQLQueries()
        assert queries.hash_map == {"test": "test"}
        assert isinstance(queries.session, requests.Session)

    # The other functions are so simple that they don't need to be tested, they
    # generally are helper functions to generate dictionaries with specific keys
    # and values.
