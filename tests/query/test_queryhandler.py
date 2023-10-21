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
        prefix = MagicMock()
        with patch(config_path) as mock_config:
            mock_config.from_file.return_value = config
            handler = QueryHandler.from_config_file("test", prefix=prefix)
            mock_config.from_file.assert_called_once_with("test", prefix=prefix)
            assert handler.config == config

    def test_from_tokens(self) -> None:
        config = MagicMock()
        session_token = MagicMock()
        gtoken = MagicMock()
        bullet_token = MagicMock()
        prefix = MagicMock()

        with patch(config_path) as mock_config:
            mock_config.from_tokens.return_value = config
            handler = QueryHandler.from_tokens(
                session_token,
                gtoken=gtoken,
                bullet_token=bullet_token,
                prefix=prefix,
            )
            mock_config.from_tokens.assert_called_once_with(
                session_token=session_token,
                gtoken=gtoken,
                bullet_token=bullet_token,
                prefix=prefix,
            )
            assert handler.config == config

    def test_from_session_token(self) -> None:
        config = MagicMock()
        session_token = MagicMock()
        prefix = MagicMock()

        with patch(config_path) as mock_config:
            mock_config.from_tokens.return_value = config
            handler = QueryHandler.from_session_token(
                session_token,
                prefix=prefix,
            )
            mock_config.from_tokens.assert_called_once_with(
                session_token=session_token,
                prefix=prefix,
            )
            config.regenerate_tokens.assert_called_once_with()
            assert handler.config == config

    def test_new_instance(self) -> None:
        config = MagicMock()
        prefix = MagicMock()

        with patch(config_path) as mock_config:
            mock_config.from_empty_handler.return_value = config
            handler = QueryHandler.new_instance(prefix=prefix)
            mock_config.from_empty_handler.assert_called_once_with(
                prefix=prefix
            )
            assert handler.config == config
