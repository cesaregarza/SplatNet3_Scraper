import configparser
from unittest.mock import MagicMock, patch

import pytest

from splatnet3_scraper.auth.tokens import TokenManager, TokenManagerConstructor
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.configuration.config import Config
from splatnet3_scraper.query.configuration.config_option_handler import (
    ConfigOptionHandler,
)

base_config_path = "splatnet3_scraper.query.configuration.config"
config_path = base_config_path + ".Config"
base_handler_path = (
    "splatnet3_scraper.query.configuration.config_option_handler"
)
handler_path = base_handler_path + ".ConfigOptionHandler"


class TestConfig:
    def test_init(self) -> None:
        mock_handler = MagicMock()
        mock_token_manager = MagicMock()
        mock_output_file_path = MagicMock()
        config = Config(
            mock_handler,
            token_manager=mock_token_manager,
            output_file_path=mock_output_file_path,
        )
        assert config.handler == mock_handler
        assert config._token_manager == mock_token_manager
        assert config._output_file_path == mock_output_file_path

    def test_token_manager_property(self) -> None:
        mock_token_manager = MagicMock()
        config = Config(MagicMock(), token_manager=mock_token_manager)
        assert config.token_manager == mock_token_manager

    def test_regenerate_tokens(self) -> None:
        mock_token_manager = MagicMock()
        mock_handler = MagicMock()
        config = Config(mock_handler, token_manager=mock_token_manager)
        config.regenerate_tokens()
        mock_token_manager.regenerate_tokens.assert_called_once_with()
        assert mock_handler.set_value.call_count == 3

    @pytest.mark.parametrize(
        "token",
        [
            TOKENS.SESSION_TOKEN,
            TOKENS.GTOKEN,
            TOKENS.BULLET_TOKEN,
        ],
        ids=["session_token", "gtoken", "bullet_token"],
    )
    def test_token_properties(self, token: str) -> None:
        mock_token_manager = MagicMock()
        mock_token_manager.get_token.return_value.value = "test"
        config = Config(MagicMock(), token_manager=mock_token_manager)
        assert getattr(config, token.lower()) == "test"
        mock_token_manager.get_token.assert_called_once_with(token)
