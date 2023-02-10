import random
from unittest.mock import patch

import pytest

from splatnet3_scraper.query.handler import QueryHandler
from splatnet3_scraper.query.responses import QueryResponse
from splatnet3_scraper.scraper.main import SplatNet_Scraper
from splatnet3_scraper.scraper.query_map import QueryMap
from tests.mock import MockQueryHandler

param = pytest.mark.parametrize
query_handler_path = "splatnet3_scraper.query.handler.QueryHandler"
scraper_path = "splatnet3_scraper.scraper.main.SplatNet_Scraper"
scraper_mangled_path = scraper_path + "._SplatNet_Scraper"


class TestSplatNetScraper:
    def test_init(self):
        with patch(query_handler_path) as mock:
            scraper = SplatNet_Scraper(mock)
            mock.assert_not_called()
            assert scraper._query_handler == mock

    @param(
        "method, args",
        [
            ("from_session_token", "test_session_token"),
            ("from_config_file", "test_config_path"),
            ("from_env", None),
            ("from_s3s_config", "test_config_path"),
        ],
        ids=[
            "from_session_token",
            "from_config",
            "from_env",
            "from_s3s_config",
        ],
    )
    def test_from_methods(self, method, args, monkeypatch: pytest.MonkeyPatch):
        with monkeypatch.context() as m:
            m.setattr(QueryHandler, method, MockQueryHandler)
            if args is None:
                scraper = getattr(SplatNet_Scraper, method)()
            else:
                scraper = getattr(SplatNet_Scraper, method)(args)
            assert isinstance(scraper, SplatNet_Scraper)
            assert isinstance(scraper._query_handler, MockQueryHandler)

    def test_query(self):
        scraper = SplatNet_Scraper(MockQueryHandler())
        variables = {"test_key": "test_value"}
        with patch.object(MockQueryHandler, "query") as mock_handled_query:
            mock_handled_query.return_value = "test_return"
            scraper._SplatNet_Scraper__query("test_query", variables)
            mock_handled_query.assert_called_once_with("test_query", variables)

    @param(
        "query, expected",
        [
            (QueryMap.SALMON, QueryMap.SALMON),
            (QueryMap.ANARCHY, QueryMap.ANARCHY),
            (QueryMap.CATALOG, None),
            ("invalid_query", None),
        ],
        ids=[
            "coop",
            "vs",
            "valid query, not vs or coop",
            "invalid query",
        ],
    )
    def test_detailed_vs_or_coop_query(self, query, expected):
        scraper = SplatNet_Scraper(MockQueryHandler())
        with patch(scraper_mangled_path + "__query") as mock_query:
            mock_query.return_value = "test_return"
            expected_exception = (
                ValueError if expected is None else AttributeError
            )
            with pytest.raises(expected_exception):
                scraper._SplatNet_Scraper__detailed_vs_or_coop(query)
            if expected is not None:
                mock_query.assert_called_once_with(expected)
            else:
                mock_query.assert_not_called()

    @param(
        "query, variable_name",
        [
            (QueryMap.SALMON, "coopHistoryDetailId"),
            (QueryMap.ANARCHY, "vsHistoryDetailId"),
        ],
        ids=[
            "coop",
            "vs",
        ],
    )
    @param(
        "num_groups, num_per_group",
        [
            (random.randint(2, 5), random.randint(5, 10)),
            (random.randint(3, 8), random.randint(10, 20)),
            (random.randint(11, 13), random.randint(30, 50)),
        ],
        ids=[
            "2-5 groups, 5-10 per group",
            "3-8 groups, 10-20 per group",
            "11-13 groups, 30-50 per group",
        ],
    )
    @param(
        "ids",
        [
            [f"test_id_{i}_{j}" for i in range(2) for j in range(3)],
            "string",
            None,
        ],
        ids=[
            "list of ids",
            "string",
            "None",
        ],
    )
    @param(
        "num_limit",
        [
            None,
            random.randint(1, 4),
            "minus_one",
        ],
        ids=[
            "No limit",
            "Random limit",
            "Minus one limit",
        ],
    )
    def test_detailed_vs_or_coop_limit(
        self,
        query,
        variable_name,
        num_groups,
        num_per_group,
        ids,
        num_limit,
        monkeypatch: pytest.MonkeyPatch,
    ):

        scraper = SplatNet_Scraper(MockQueryHandler())
        num_total = num_groups * num_per_group
        ret_value = QueryResponse(
            {
                "results": {
                    "historyGroups": {
                        "nodes": [
                            {
                                "historyDetails": {
                                    "nodes": [
                                        {"id": f"test_id_{i}_{j}"}
                                        for j in range(num_per_group)
                                    ]
                                }
                            }
                            for i in range(num_groups)
                        ]
                    }
                }
            }
        )

        if ids == "string":
            ids = "test_id_2_4"
            expected_total = 2 * num_per_group + 4
        elif ids is None:
            expected_total = num_total
        else:
            expected_total = num_total - len(ids)

        if num_limit == "minus_one":
            num_limit = num_total - 1
        elif num_limit is None:
            num_limit = num_total

        expected_total = min(expected_total, num_limit)
        counter = 0

        def mock_query(query: str, variables: dict = {}) -> dict:
            nonlocal counter
            counter += 1
            if counter == 1:
                return ret_value
            else:
                assert query in (
                    QueryMap.SALMON_DETAIL,
                    QueryMap.ANARCHY_DETAIL,
                )
                assert variable_name in variables

        with monkeypatch.context() as m:
            m.setattr(scraper, "_SplatNet_Scraper__query", mock_query)
            scraper._SplatNet_Scraper__detailed_vs_or_coop(
                query, limit=num_limit, existing_ids=ids
            )
            assert counter == expected_total + 1
