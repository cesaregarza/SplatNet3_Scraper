import configparser
from configparser import ConfigParser
from unittest.mock import mock_open, patch

import pytest
import pytest_mock

from splatnet3_scraper.constants import DEFAULT_USER_AGENT
from splatnet3_scraper.query.config import Config
from splatnet3_scraper.query.config_options import ConfigOptions
from tests.mock import MockConfigParser, MockTokenManager

config_path = "splatnet3_scraper.query.config.Config"
config_mangled = config_path + "._Config"
token_manager_path = "splatnet3_scraper.auth.token_manager.TokenManager"


class TestConfig:
    @pytest.mark.parametrize(
        "config_path_var",
        [
            "test_path",
            None,
        ],
        ids=["path", "no_path"],
    )
    @pytest.mark.parametrize(
        "token_manager",
        [
            MockTokenManager(),
            None,
        ],
        ids=["token_manager", "no_token_manager"],
    )
    @pytest.mark.parametrize(
        "write_to_file",
        [
            True,
            False,
        ],
        ids=["write_to_file", "no_write_to_file"],
    )
    @pytest.mark.parametrize(
        "config",
        [
            MockConfigParser(),
            None,
        ],
        ids=["config", "no_config"],
    )
    def test_init(self, config_path_var, token_manager, write_to_file, config):
        with (
            patch(config_path + ".generate_token_manager") as mock_generate,
            patch(config_path + ".initialize_options") as mock_initialize,
        ):
            mock_generate.return_value = None
            mock_initialize.return_value = None
            
            instance = Config(
                config_path=config_path_var,
                token_manager=token_manager,
                write_to_file=write_to_file,
                config=config,
            )
            assert instance.write_to_file == write_to_file
            assert isinstance(instance.config_options, ConfigOptions)
            if token_manager is None:
                mock_generate.assert_called_once_with(config_path_var)
                assert not hasattr(instance, "config_path")
                assert not hasattr(instance, "token_manager")
                mock_initialize.assert_not_called()
            else:
                mock_generate.assert_not_called()
                assert instance.config_path == config_path_var
                assert instance.token_manager == token_manager
                mock_initialize.assert_called_once_with(config)
