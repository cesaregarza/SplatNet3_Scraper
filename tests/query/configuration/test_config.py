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

    @pytest.mark.parametrize(
        "default",
        [
            "default",
            None,
        ],
        ids=[
            "default",
            "no default",
        ],
    )
    @pytest.mark.parametrize(
        "value",
        [
            "test",
            None,
        ],
        ids=[
            "value",
            "no value",
        ],
    )
    def test_get_value(self, value: str | None, default: str | None) -> None:
        mock_handler = MagicMock()
        mock_handler.get_value.return_value = value
        config = Config(mock_handler)
        if value is None and default is None:
            assert config.get_value("test") is None
        elif value is None:
            assert config.get_value("test", default) == default
        else:
            assert config.get_value("test", default) == value
        mock_handler.get_value.assert_called_once_with("test")

    @pytest.mark.parametrize(
        "option",
        [
            "test",
            TOKENS.SESSION_TOKEN,
        ],
        ids=[
            "normal option",
            "token",
        ],
    )
    def test_set_value(self, option: str) -> None:
        mock_handler = MagicMock()
        mock_token_manager = MagicMock()
        config = Config(mock_handler, token_manager=mock_token_manager)
        config.set_value(option, "test")
        mock_handler.set_value.assert_called_once_with(option, "test")
        if option == TOKENS.SESSION_TOKEN:
            mock_token_manager.add_token.assert_called_once_with(
                mock_handler.tokens[option],
                option,
            )

    @pytest.mark.parametrize(
        "save_to_file",
        [
            True,
            False,
        ],
        ids=[
            "save to file",
            "no save to file",
        ],
    )
    def test_from_config_handler(self, save_to_file: bool) -> None:
        mock_handler = MagicMock()
        mock_token_manager = MagicMock()
        expected_file_path = "test" if save_to_file else None

        with (
            patch(config_path) as mock_config,
            patch(base_config_path + ".TokenManagerConstructor") as mock_tmc,
        ):
            mock_config.DEFAULT_PREFIX = "SN3S"
            mock_tmc.from_tokens.return_value = mock_token_manager

            config = Config.from_config_handler(
                mock_handler,
                output_file_path=expected_file_path,
            )
            mock_tmc.from_tokens.assert_called_once_with(
                session_token=mock_handler.get_value.return_value,
                gtoken=mock_handler.get_value.return_value,
                bullet_token=mock_handler.get_value.return_value,
            )
            mock_config.assert_called_once_with(
                mock_handler,
                token_manager=mock_token_manager,
                output_file_path=expected_file_path,
            )
            assert mock_handler.get_value.call_count == 3

    @pytest.mark.parametrize(
        "prefix",
        [
            "test",
            None,
        ],
        ids=[
            "prefix",
            "no prefix",
        ],
    )
    @pytest.mark.parametrize(
        "save_to_file",
        [
            True,
            False,
        ],
        ids=[
            "save to file",
            "no save to file",
        ],
    )
    def test_from_file(
        self,
        save_to_file: bool,
        prefix: str | None,
    ) -> None:
        mock_handler_instance = MagicMock()
        mock_configp = MagicMock()

        expected_prefix = prefix or "SN3S"
        expected_file_path = "test" if save_to_file else None

        with (
            patch(
                base_config_path + ".configparser.ConfigParser"
            ) as mock_configparser,
            patch(base_config_path + ".ConfigOptionHandler") as mock_handler,
            patch(config_path + ".from_config_handler") as mock_config,
        ):
            mock_configparser.return_value = mock_configp
            mock_handler.return_value = mock_handler_instance
            mock_config.DEFAULT_PREFIX = "SN3S"

            config = Config.from_file(
                "test",
                save_to_file=save_to_file,
                prefix=prefix,
            )
            mock_configparser.assert_called_once_with()
            mock_configp.read.assert_called_once_with("test")
            mock_handler.assert_called_once_with(prefix=expected_prefix)
            mock_handler_instance.read_from_configparser.assert_called_once_with(
                mock_configp
            )
            mock_config.assert_called_once_with(
                mock_handler_instance,
                output_file_path=expected_file_path,
            )

    class TestFromFileNoMock:
        def test_extra_tokens(self, extra_tokens: str) -> None:
            config = Config.from_file(
                extra_tokens,
            )
            assert config.session_token == "test_session_token"

    @pytest.mark.parametrize(
        "prefix",
        [
            "test",
            None,
        ],
        ids=[
            "prefix",
            "no prefix",
        ],
    )
    def test_from_dict(
        self,
        prefix: str | None,
    ) -> None:
        mock_handler_instance = MagicMock()
        mock_dict = MagicMock()

        expected_prefix = prefix or "SN3S"

        with (
            patch(base_config_path + ".ConfigOptionHandler") as mock_handler,
            patch(config_path + ".from_config_handler") as mock_config,
        ):
            mock_handler.return_value = mock_handler_instance
            mock_config.DEFAULT_PREFIX = "SN3S"

            config = Config.from_dict(mock_dict, prefix=prefix)
            mock_handler.assert_called_once_with(prefix=expected_prefix)
            mock_handler_instance.read_from_dict.assert_called_once_with(
                mock_dict
            )
            mock_config.assert_called_once_with(
                mock_handler_instance,
            )
