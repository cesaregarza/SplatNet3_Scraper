from unittest.mock import MagicMock, patch

import pytest

from splatnet3_scraper.auth.exceptions import SplatNetException
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.query.handler import QueryHandler
from splatnet3_scraper.query.responses import QueryResponse
from tests.mock import MockConfig, MockNSO, MockResponse, MockTokenManager

base_handler_path = "splatnet3_scraper.query.handler"
config_path = base_handler_path + ".Config"
handler_path = base_handler_path + ".QueryHandler"


class TestSplatNetQueryHandler:
    def test_init(self) -> None:
        config = MagicMock()
        handler = QueryHandler(config)
        assert handler.config == config

    def test_from_config_file(self) -> None:
        config = MagicMock()
        with patch(config_path) as mock_config:
            mock_config.from_file.return_value = config
            handler = QueryHandler.from_config_file("test")
            mock_config.from_file.assert_called_once_with("test")
            assert handler.config == config
