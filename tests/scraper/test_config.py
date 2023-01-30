import configparser
import unittest
from configparser import ConfigParser
from unittest.mock import mock_open, patch

import pytest
import pytest_mock

from splatnet3_scraper.scraper.config import Config
from tests.mock import MockNSO, MockResponse, MockTokenManager

config_path = "splatnet3_scraper.scraper.config.Config"


class TestConfig:
    def test_init(self, mocker: pytest_mock.MockFixture):
        # token manager is none
        mock_post_init = mocker.patch.object(Config, "__post_init__")
        config = Config()
        mock_post_init.assert_called_once_with(None)
        assert not hasattr(config, "config_path")
        assert not hasattr(config, "config")

        # token manager is not none
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)
        assert config.token_manager == token_manager
        assert config.config_path is None
        assert isinstance(config.config, ConfigParser)
        assert config.config.sections() == ["options"]

    # No need to test __post_init__ because it is only called in __init__ and
    # is simple enough to not need testing.

    def test_save(self, monkeypatch: pytest.MonkeyPatch):
        def remove_section(*args, **kwargs):
            if args[1] == "tokens":
                raise configparser.NoSectionError("tokens")
            else:
                raise ValueError("Invalid section name")

        # Origin: env
        token_manager = MockTokenManager(origin={"origin": "env", "data": None})
        config = Config(token_manager=token_manager)
        with (
            monkeypatch.context() as m,
            pytest.raises(configparser.NoSectionError),
        ):

            m.setattr(ConfigParser, "remove_section", remove_section)
            config.save()

        # Remove tokens from config file
        with (
            monkeypatch.context() as m,
            pytest.raises(configparser.NoSectionError),
        ):
            m.setattr(ConfigParser, "remove_section", remove_section)
            token_manager._origin["origin"] = "file"
            config.save(include_tokens=False)

        # path is not none
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch(
                "configparser.ConfigParser.write", return_value=None
            ) as mock_write,
        ):
            config.save(path="test_write_path")
            mock_file.assert_called_once_with("test_write_path", "w")
            mock_write.assert_called_once_with(mock_file.return_value)

        # path is none, self.config_path is none
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch(
                "configparser.ConfigParser.write", return_value=None
            ) as mock_write,
        ):
            config.save()
            mock_file.assert_called_once_with(".splatnet3_scraper", "w")
            mock_write.assert_called_once_with(mock_file.return_value)

        # path is none, self.config_path is not none
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch(
                "configparser.ConfigParser.write", return_value=None
            ) as mock_write,
        ):
            config.config_path = "test_config_path"
            config.save()
            mock_file.assert_called_once_with("test_config_path", "w")
            mock_write.assert_called_once_with(mock_file.return_value)
