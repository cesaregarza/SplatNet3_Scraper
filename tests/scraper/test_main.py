import pytest
from unittest.mock import patch

from splatnet3_scraper.query.handler import SplatNet_QueryHandler
from splatnet3_scraper.scraper.main import SplatNet_Scraper
from tests.mock import MockQueryHandler

param = pytest.mark.parametrize
query_handler_path = "splatnet3_scraper.query.handler.SplatNet_QueryHandler"
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
            m.setattr(SplatNet_QueryHandler, method, MockQueryHandler)
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
