import random
from unittest.mock import MagicMock, patch

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

    def test_handler_property(self):
        with patch(query_handler_path) as mock:
            scraper = SplatNet_Scraper(mock)
            assert scraper.query_handler == mock
            mock.assert_not_called()

    @param(
        "method, args",
        [
            ("from_session_token", "test_session_token"),
            ("from_config_file", "test_config_path"),
            ("from_env", None),
            ("from_s3s_config", "test_config_path"),
            ("from_tokens", ["test_session_token", "test_gtoken"]),
        ],
        ids=[
            "from_session_token",
            "from_config",
            "from_env",
            "from_s3s_config",
            "from_tokens",
        ],
    )
    def test_from_methods(self, method, args, monkeypatch: pytest.MonkeyPatch):
        with monkeypatch.context() as m:
            m.setattr(QueryHandler, method, MockQueryHandler)
            if args is None:
                scraper = getattr(SplatNet_Scraper, method)()
            elif isinstance(args, list):
                scraper = getattr(SplatNet_Scraper, method)(*args)
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
            (QueryMap.ANARCHY, "vsResultId"),
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
    @param(
        "progress_callback",
        [
            False,
            True,
        ],
        ids=[
            "No progress callback",
            "Progress callback",
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
        progress_callback,
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

        mock_progress_callback = MagicMock()

        progress_arg = mock_progress_callback if progress_callback else None

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
                query,
                limit=num_limit,
                existing_ids=ids,
                progress_callback=progress_arg,
            )
            assert counter == expected_total + 1
            if progress_callback:
                mock_progress_callback.call_count == expected_total
            else:
                mock_progress_callback.assert_not_called()

    @param(
        "mode, expect_error, expected_query",
        [
            ("regular", False, QueryMap.REGULAR),
            ("anarchy", False, QueryMap.ANARCHY),
            ("xbattle", False, QueryMap.XBATTLE),
            ("private", False, QueryMap.PRIVATE),
            ("salmon", False, QueryMap.SALMON),
            ("challenge", False, QueryMap.CHALLENGE),
            ("not_a_mode", True, None),
        ],
        ids=[
            "regular",
            "anarchy",
            "x battle",
            "private",
            "salmon",
            "challenge",
            "not a mode",
        ],
    )
    @param(
        "detail",
        [True, False],
        ids=["detail", "no detail"],
    )
    @param(
        "progress_callback",
        [True, False],
        ids=["progress callback", "no progress callback"],
    )
    def test_get_matches(
        self,
        mode: str,
        expect_error: bool,
        expected_query: str,
        detail: bool,
        progress_callback: bool,
    ):
        scraper = SplatNet_Scraper(MockQueryHandler())
        detail_path = scraper_mangled_path + "__detailed_vs_or_coop"
        with (
            patch(detail_path) as mock_detailed,
            patch(scraper_mangled_path + "__query") as mock_query,
        ):
            mock_detailed.return_value = "test_detailed"
            mock_query.return_value = "test_query"
            if expect_error:
                if mode == "not_a_mode":
                    error_type = AttributeError
                else:
                    error_type = ValueError
                with pytest.raises(error_type):
                    scraper.get_matches(mode, detail)
                mock_detailed.assert_not_called()
                mock_query.assert_not_called()
                return

            expected = "test_detailed" if detail else "test_query"
            assert (
                scraper.get_matches(
                    mode, detail, progress_callback=progress_callback
                )
                == expected
            )
            if detail:
                mock_detailed.assert_called_once_with(
                    expected_query, None, None, progress_callback
                )
                mock_query.assert_not_called()
            else:
                mock_detailed.assert_not_called()
                mock_query.assert_called_once_with(expected_query)
