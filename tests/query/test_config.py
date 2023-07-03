import configparser
from configparser import ConfigParser
from unittest.mock import mock_open, patch

import pytest
import pytest_mock

from splatnet3_scraper.constants import DEFAULT_USER_AGENT
from splatnet3_scraper.query.config import Config
from tests.mock import MockConfigParser, MockTokenManager

config_path = "splatnet3_scraper.query.config.Config"
config_mangled = config_path + "._Config"
token_manager_path = "splatnet3_scraper.auth.token_manager.TokenManager"


class TestConfig:
    def test_init(self, mocker: pytest_mock.MockFixture):
        # token manager is none
        mock_post_init = mocker.patch.object(Config, "generate_token_manager")
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
        assert config.options == config.config.options("options")

    def test_generate_token_manager(self, monkeypatch: pytest.MonkeyPatch):
        config = Config(token_manager=MockTokenManager())
        # config path is not none
        with (
            patch(
                token_manager_path + ".from_config_file"
            ) as mock_from_config_file,
            patch("configparser.ConfigParser.read") as mock_read,
            patch("configparser.ConfigParser.options") as mock_options,
            patch(config_path + ".manage_options") as mock_manage_options,
            patch("builtins.open", mock_open()) as mock_file,
            patch("configparser.ConfigParser.write") as mock_write,
        ):
            mock_options.return_value = True
            config.generate_token_manager("config_path")
            mock_from_config_file.assert_called_once_with("config_path")
            mock_read.assert_called_once_with("config_path")
            mock_options.assert_called_once_with("options")
            mock_manage_options.assert_called_once()
            mock_file.assert_called_once_with("config_path", "w")
            mock_write.assert_called_once()

        # config path is none
        with (
            patch(
                token_manager_path + ".from_config_file"
            ) as mock_from_config_file,
            patch(token_manager_path + ".load") as mock_load,
            patch("configparser.ConfigParser.read") as mock_read,
            patch(config_path + ".manage_options") as mock_manage_options,
            patch("builtins.open", mock_open()) as mock_file,
            patch("configparser.ConfigParser.write") as mock_write,
            monkeypatch.context() as m,
        ):
            count = 0

            def options(*args, **kwargs):
                nonlocal count
                count += 1
                if count == 1:
                    raise configparser.NoSectionError("options")
                else:
                    return True

            m.setattr(ConfigParser, "options", options)
            mock_options.return_value = True
            mock_load.return_value = MockTokenManager()
            config.generate_token_manager(None)
            mock_from_config_file.assert_not_called()
            mock_load.assert_called_once()
            mock_read.assert_called_once_with(".splatnet3_scraper")
            assert count == 2
            mock_manage_options.assert_called_once()
            mock_file.assert_called_once_with(".splatnet3_scraper", "w")
            mock_write.assert_called_once()

    @pytest.mark.parametrize(
        "origin",
        [
            {"origin": "env", "data": None},
            {"origin": "config", "data": "test_path"},
            {"origin": "test_origin", "data": "test_data"},
        ],
        ids=["env", "config", "test_origin"],
    )
    @pytest.mark.parametrize(
        "has_config",
        [True, False],
        ids=["has_config", "no_config"],
    )
    def test_initialize_options(
        self,
        origin: dict[str, str | None] | dict[str, str],
        has_config: bool,
        monkeypatch: pytest.MonkeyPatch,
    ):
        token_manager = MockTokenManager()
        MockTokenManager.origin = origin

        with monkeypatch.context() as m:
            m.setattr(Config, "__init__", lambda *args, **kwargs: None)
            config = Config(token_manager=token_manager)
            config.token_manager = token_manager
            if has_config:
                config.config = True
            config.initialize_options()

            # Test short circuit
            if has_config:
                assert config.config is True
                return

            assert config.config.sections() == ["options"]

            if origin["origin"] == "env":
                test_key_str = "test_key_%s"
                test_value_str = "test_value_%s"
                for i, option in [(i, test_key_str % i) for i in range(3)]:
                    # assert it's not in the config under options
                    assert not config.config.has_option("options", option)
                for i, option in [(i, test_key_str % i) for i in range(3, 5)]:
                    # assert it's in the config under options
                    assert config.config.has_option("options", option)
                    assert (
                        config.config.get("options", option)
                        == test_value_str % i
                    )

    def test_from_env(self):
        config = Config(token_manager=MockTokenManager())
        with (
            patch(token_manager_path + ".from_env") as mock_from_env,
            patch(config_path + ".generate_token_manager") as mock_post_init,
        ):
            mock_from_env.return_value = MockTokenManager()
            config.from_env()
            mock_from_env.assert_called_once()
            mock_post_init.assert_not_called()

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

    def test_manage_options(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)

        mock_config = MockConfigParser()
        test_options = {
            # accepted options
            "user_agent": "test_user_agent",
            # deprecated options
            "api_key": "test_stat_ink_api_token",
            # invalid options
            "invalid_option": "test_invalid_option",
        }
        mock_config["options"] = test_options
        config.config = mock_config
        config.options = mock_config.options("options")
        config.manage_options()
        expected_options = {
            "user_agent": "test_user_agent",
            "stat.ink_api_token": "test_stat_ink_api_token",
        }
        expected_deprecated = {
            "api_key": "test_stat_ink_api_token",
        }
        expected_unknown = {
            "invalid_option": "test_invalid_option",
        }
        assert config.config["options"] == expected_options
        assert config.config["deprecated"] == expected_deprecated
        assert config.config["unknown"] == expected_unknown

    def test_get(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)

        mock_config = MockConfigParser()
        test_options = {
            "stat.ink_api_token": "test_stat_ink_api_key",
        }
        mock_config["options"] = test_options
        config.config = mock_config
        config.options = mock_config.options("options")
        config.manage_options()
        # Accepted option and set
        assert config.get("stat.ink_api_token") == "test_stat_ink_api_key"
        # Accepted option, not set, but has default
        assert config.get("user_agent") == DEFAULT_USER_AGENT
        # Accepted option, not set, and no default
        with pytest.raises(KeyError):
            config.get("log_file")
        # Deprecated option
        assert config.get("api_key") == "test_stat_ink_api_key"
        # Invalid option
        with pytest.raises(KeyError):
            config.get("invalid_option")

    def test_get_data_fed_data(self):
        token_manager = MockTokenManager(
            data={"test_key_1": "test_value_1", "test_key_2": "test_value_2"}
        )
        config = Config(token_manager=token_manager)

        assert not config.config.has_section("data")
        assert config.get_data("test_key_1") == "test_value_1"
        assert config.config.has_section("data")
        assert config.config["data"]["test_key_1"] == "test_value_1"
        assert config.get_data("test_key_2") == "test_value_2"

    def test_get_data_defaults(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)

        assert not config.config.has_section("data")
        assert config.get_data("language") == "en-US"
        assert config.config.has_section("data")
        assert config.config["data"] == {}

    def test_add_accepted_options(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)
        base_options = [x for x in config.ACCEPTED_OPTIONS]
        test_options = [f"test_option_{i}" for i in range(10)]
        config.add_accepted_options(test_options)
        assert config.ACCEPTED_OPTIONS == base_options + test_options

    def test_add_deprecated_options(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)
        base_options = {k: v for k, v in config.DEPRECATED_OPTIONS.items()}
        test_options = {
            f"test_option_{i}": f"test_value_{i}" for i in range(10)
        }
        config.add_deprecated_options(test_options)
        assert config.DEPRECATED_OPTIONS == {**base_options, **test_options}

    def test_add_default_options(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)
        base_options = {k: v for k, v in config.DEFAULT_OPTIONS.items()}
        test_options = {
            f"test_option_{i}": f"test_value_{i}" for i in range(10)
        }
        config.add_default_options(test_options)
        assert config.DEFAULT_OPTIONS == {**base_options, **test_options}

    def test_remove_accepted_options(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)
        base_options = [x for x in config.ACCEPTED_OPTIONS]
        test_options = [f"test_option_{i}" for i in range(10)]
        config.add_accepted_options(test_options)
        assert config.ACCEPTED_OPTIONS == base_options + test_options
        config.remove_accepted_options(test_options)
        assert config.ACCEPTED_OPTIONS == base_options

    def test_remove_deprecated_options(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)
        base_options = {
            k: v for k, v in config.DEPRECATED_OPTIONS.items()
        }.copy()
        test_options = {
            f"test_option_{i}": f"test_value_{i}" for i in range(10)
        }
        config.add_deprecated_options(test_options)
        assert config.DEPRECATED_OPTIONS == {**base_options, **test_options}
        config.remove_deprecated_options(test_options.keys())
        assert config.DEPRECATED_OPTIONS == base_options

    def test_remove_default_options(self):
        token_manager = MockTokenManager()
        config = Config(token_manager=token_manager)
        base_options = {k: v for k, v in config.DEFAULT_OPTIONS.items()}.copy()
        test_options = {
            f"test_option_{i}": f"test_value_{i}" for i in range(10)
        }
        config.add_default_options(test_options)
        assert config.DEFAULT_OPTIONS == {**base_options, **test_options}
        config.remove_default_options(test_options)
        assert config.DEFAULT_OPTIONS == base_options
