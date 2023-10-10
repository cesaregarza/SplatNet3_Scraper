import configparser
from unittest.mock import MagicMock, mock_open, patch

import pytest

from splatnet3_scraper.query.config_new import Config
from splatnet3_scraper.query.config_options import ConfigOptions
from tests.mock import MockConfigParser, MockTokenManager

base_config_path = "splatnet3_scraper.query.config"
config_path = base_config_path + ".Config"
config_parser_path = base_config_path + ".configparser"
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
    def test_init(
        self,
        config_path_var: str | None,
        token_manager: MockTokenManager | None,
        write_to_file: bool,
        config: MockConfigParser | None,
    ):
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

    @pytest.mark.parametrize(
        "config_path_var",
        [
            "test_path",
            None,
        ],
        ids=["path", "no_path"],
    )
    @pytest.mark.parametrize(
        "options",
        [True, False],
        ids=["options", "no_options"],
    )
    @pytest.mark.parametrize(
        "write_to_file",
        [
            True,
            False,
        ],
        ids=["write_to_file", "no_write_to_file"],
    )
    def test_generate_token_manager(
        self, config_path_var: str | None, options: bool, write_to_file: bool
    ):
        # Mock TokenManager and ConfigParser
        mock_token_manager = MockTokenManager()
        mock_config = MagicMock()

        # Mock options for ConfigParser
        mock_option_1 = MagicMock()
        mock_option_2 = MagicMock()
        mock_options = [mock_option_1, mock_option_2]

        # Counter to control when to raise NoSectionError
        count = 0 if options else 1

        # Function to raise NoSectionError on the first call if options is False
        def raise_on_first_call(*args, **kwargs):
            nonlocal count
            if count > 0:
                count -= 1
                raise configparser.NoSectionError("options")
            return mock_options

        # Patching methods and classes
        with (
            patch(config_path + ".initialize_options") as mock_initialize,
            patch(token_manager_path + ".from_config_file") as mock_from_config,
            patch(token_manager_path + ".load") as mock_load,
            patch(
                config_parser_path + ".ConfigParser", return_value=mock_config
            ) as mock_config_parser,
            patch("builtins.open", mock_open()) as mock_open_file,
            patch(config_path + ".manage_option") as mock_manage_option,
        ):
            # Set return values for mocks
            mock_initialize.return_value = None
            mock_from_config.return_value = mock_token_manager
            mock_load.return_value = mock_token_manager
            mock_manage_option.return_value = None

            # Set side effect to raise NoSectionError
            mock_config.options.side_effect = raise_on_first_call

            # Run method under test
            instance = Config(
                token_manager="test_token_manager", write_to_file=write_to_file
            )
            instance.generate_token_manager(config_path_var)

            # Assert path logic
            config_path_var_expected = (
                config_path_var
                if config_path_var
                else Config.DEFAULT_CONFIG_PATH
            )

            # Assert TokenManager method calls based on config_path_var
            if config_path_var:
                mock_from_config.assert_called_once_with(config_path_var)
                mock_load.assert_not_called()
            else:
                mock_from_config.assert_not_called()
                mock_load.assert_called_once()

            # Assert instance variables
            assert instance.token_manager == mock_token_manager
            assert instance.config_path == config_path_var_expected
            assert instance.config_path is not None
            assert instance.config == mock_config

            # Assert ConfigParser method calls
            mock_config.read.assert_called_once_with(config_path_var_expected)

            if options:
                mock_config.options.assert_called_once_with("options")
            else:
                mock_config.add_section.assert_called_once_with("options")
                assert mock_config.options.call_count == 2

            # Assert option management
            assert mock_manage_option.call_count == 2
            assert instance.options == mock_options

            # Assert file write logic
            if write_to_file:
                mock_open_file.assert_called_once_with(
                    config_path_var_expected, "w"
                )
                mock_config.write.assert_called_once_with(mock_open_file())
            else:
                mock_open_file.assert_not_called()
                mock_config.write.assert_not_called()

    @pytest.mark.parametrize(
        "config",
        [
            "config",
            None,
        ],
        ids=["config", "no_config"],
    )
    @pytest.mark.parametrize(
        "origin",
        [
            "env",
            "other",
        ],
        ids=["env", "other"],
    )
    def test_initialize_options(self, config: str | None, origin: str):
        mock_token_manager = MagicMock()
        mock_token_manager.origin = {"origin": origin}
        tokens = {
            "base_token_1": "nonzero_value",
            "base_token_2": None,
            "non_base_token_1": "nonzero_value",
            "non_base_token_2": None,
        }
        base_tokens = ["base_token_1", "base_token_2"]
        mock_token_manager.env_manager.get_all.return_value = tokens
        mock_token_manager.env_manager.BASE_TOKENS = base_tokens
        mock_config = MagicMock()

        with (
            patch(config_path + ".generate_token_manager") as mock_generate,
            patch(config_parser_path + ".ConfigParser") as mock_config_parser,
        ):
            mock_generate.return_value = None
            mock_config_parser.return_value = mock_config

            instance = Config()
            instance.token_manager = mock_token_manager
            instance.initialize_options(config=config)

            if config:
                assert instance.config == config
                mock_config_parser.assert_not_called()
                return

            mock_config_parser.assert_called_once()
            assert instance.config == mock_config
            mock_config.add_section.assert_called_once_with("options")
            mock_config.options.assert_called_once_with("options")
            assert instance.options == mock_config.options.return_value

            if origin == "other":
                mock_token_manager.env_manager.get_all.assert_not_called()
                return

            mock_token_manager.env_manager.get_all.assert_called_once()
            # assert that mock_config["options"]["non_base_token_1"] is the only
            # token that was set
            getitem = mock_config.__getitem__.return_value
            getitem.__setitem__.assert_called_once_with(
                "non_base_token_1", "nonzero_value"
            )

    @pytest.mark.parametrize(
        "env_manager",
        ["env_manager", None],
        ids=["env_manager", "no_env_manager"],
    )
    def test_from_env(self, env_manager: str | None):
        mock_token_manager = MagicMock()

        with (
            patch(token_manager_path + ".from_env") as mock_from_env,
            patch(config_path) as mock_config,
            patch(config_path + ".initialize_options") as mock_initialize,
        ):
            mock_from_env.return_value = mock_token_manager
            mock_config.return_value = None
            mock_initialize.return_value = None

            instance = Config.from_env(env_manager=env_manager)

            mock_from_env.assert_called_once_with(env_manager)
            assert instance.token_manager == mock_token_manager

    @pytest.mark.parametrize(
        "config_path_var",
        [
            "test_path",
            None,
        ],
        ids=["path", "no_path"],
    )
    def test_from_s3s_config(self, config_path_var: str | None):
        mock_token_manager = MagicMock()

        with (
            patch(token_manager_path + ".from_text_file") as mock_from_s3s,
            patch(config_path) as mock_config,
            patch(config_path + ".initialize_options") as mock_initialize,
        ):
            mock_from_s3s.return_value = mock_token_manager
            mock_config.return_value = None
            mock_initialize.return_value = None

            instance = Config.from_s3s_config(config_path_var)

            mock_from_s3s.assert_called_once_with(config_path_var)
            assert instance.token_manager == mock_token_manager

    @pytest.mark.parametrize(
        "path",
        [
            "test_path",
            None,
        ],
        ids=["path", "no_path"],
    )
    @pytest.mark.parametrize(
        "include_tokens",
        [
            True,
            False,
        ],
        ids=["include_tokens", "no_include_tokens"],
    )
    @pytest.mark.parametrize(
        "origin",
        [
            "env",
            "other",
        ],
        ids=["env", "other"],
    )
    @pytest.mark.parametrize(
        "config_path_var",
        [
            "test_path_config",
            None,
        ],
        ids=["config_path", "no_config_path"],
    )
    def test_save(
        self,
        path: str | None,
        include_tokens: bool,
        origin: str,
        config_path_var: str | None,
    ):
        mock_token_manager = MagicMock()
        mock_token_manager.origin = {"origin": origin}
        mock_config = MagicMock()

        with (
            patch(config_path + ".generate_token_manager") as mock_generate,
            patch(config_path + ".initialize_options") as mock_initialize,
            patch(config_path + ".manage_option") as mock_manage_option,
            patch(config_parser_path + ".ConfigParser") as mock_config_parser,
            patch("builtins.open", mock_open()) as mock_open_file,
        ):
            mock_generate.return_value = None
            mock_initialize.return_value = None
            mock_manage_option.return_value = None
            mock_config_parser.return_value = None

            instance = Config()
            instance.token_manager = mock_token_manager
            instance.config_path = config_path_var
            instance.config = mock_config
            instance.save(path, include_tokens)

            if (not include_tokens) or (origin == "env"):
                mock_config.remove_section.assert_called_once_with("tokens")

            if (path is None) and (config_path_var is not None):
                expected_path = config_path_var
            elif path is None:
                expected_path = Config.DEFAULT_CONFIG_PATH
            else:
                expected_path = path

            mock_open_file.assert_called_once_with(expected_path, "w")
            mock_config.write.assert_called_once_with(mock_open_file())

    @pytest.mark.parametrize(
        "has_unknown",
        [
            True,
            False,
        ],
        ids=["has_unknown", "no_unknown"],
    )
    @pytest.mark.parametrize(
        "has_deprecated",
        [
            True,
            False,
        ],
        ids=["has_deprecated", "no_deprecated"],
    )
    @pytest.mark.parametrize(
        "option",
        ["supported", "deprecated", "not_supported"],
        ids=["supported", "deprecated", "not_supported"],
    )
    def test_manage_option(
        self,
        has_unknown: bool,
        has_deprecated: bool,
        option: str,
    ):
        mock_token_manager = MagicMock()
        mock_config = MagicMock()
        mock_config_options = MagicMock()

        with (
            patch(config_path + ".generate_token_manager") as mock_generate,
            patch(config_path + ".initialize_options") as mock_initialize,
            patch(
                base_config_path + ".ConfigOptions"
            ) as mock_config_options_class,
            patch(config_parser_path + ".ConfigParser") as mock_config_parser,
        ):
            mock_generate.return_value = None
            mock_initialize.return_value = None
            mock_config_parser.return_value = None
            mock_config_options_class.return_value = None

            instance = Config()
            instance.token_manager = mock_token_manager
            instance.config = mock_config
            instance.config_options = mock_config_options

            # Set up mock_config.has_section
            def has_section(section: str) -> bool:
                if section == "unknown":
                    return has_unknown
                if section == "deprecated":
                    return has_deprecated
                return True

            mock_config.has_section.side_effect = has_section

            mock_config_options.SUPPORTED_OPTIONS = [
                "supported",
                "not_deprecated",
                "deprecated",
            ]
            mock_config_options.DEPRECATED_OPTIONS = {
                "deprecated": "replacement"
            }

            instance.manage_option(option)

            if option == "not_supported":
                if has_unknown:
                    mock_config.add_section.assert_not_called()
                else:
                    mock_config.add_section.assert_called_once_with("unknown")

                mock_config.has_section.assert_called_once_with("unknown")
                assert mock_config.__getitem__.call_count == 2
                getitem = mock_config.__getitem__.return_value
                getitem.__getitem__.assert_called_once_with(option)
                option_getitem = getitem.__getitem__.return_value
                getitem.__setitem__.assert_called_once_with(
                    option, option_getitem
                )
                return

            elif option == "supported":
                mock_config.has_section.assert_not_called()
                return

            if has_deprecated:
                mock_config.add_section.assert_not_called()
            else:
                mock_config.add_section.assert_called_once_with("deprecated")

            getitem = mock_config.__getitem__.return_value
            getitem_getitem = getitem.__getitem__.return_value
            getitem_setitem = getitem.__setitem__
            getitem_setitem.assert_any_call("replacement", getitem_getitem)
            getitem_setitem.assert_any_call("deprecated", getitem_getitem)
            mock_config.remove_option.assert_called_once_with(
                "options", "deprecated"
            )

    def test_get(self):
        accepted_options = [
            "set_key",
            "not_set_with_default",
            "not_set_no_default",
        ]
        deprecated_options = {"deprecated": "set_key"}
        default_options = {"not_set_with_default": "default_value"}

        mock_token_manager = MagicMock()
        mock_config_options = MagicMock()

        with (
            patch(config_path + ".generate_token_manager") as mock_generate,
            patch(config_path + ".initialize_options") as mock_initialize,
            patch(
                base_config_path + ".ConfigOptions"
            ) as mock_config_options_class,
            patch(config_parser_path + ".ConfigParser") as mock_config_parser,
        ):
            mock_generate.return_value = None
            mock_initialize.return_value = None
            mock_config_parser.return_value = None
            mock_config_options_class.return_value = None

            instance = Config()
            instance.token_manager = mock_token_manager
            instance.config = {"options": {"set_key": "set_value"}}
            instance.config_options = mock_config_options

            mock_config_options.ACCEPTED_OPTIONS = accepted_options
            mock_config_options.DEPRECATED_OPTIONS = deprecated_options
            mock_config_options.DEFAULT_OPTIONS = default_options

            assert instance.get("set_key") == "set_value"
            assert instance.get("not_set_with_default") == "default_value"
            with pytest.raises(KeyError):
                instance.get("not_set_no_default")
            assert instance.get("deprecated") == "set_value"
            with pytest.raises(KeyError):
                instance.get("not_supported")

    # TODO: test_get_data
    @pytest.mark.parametrize(
        "full_token",
        [
            True,
            False,
        ],
        ids=["full_token", "no_full_token"],
    )
    def test_get_token(self, full_token: bool):
        mock_token_manager = MagicMock()
        mock_token_manager.get_token.return_value = "test_token"

        with patch(config_path + ".generate_token_manager") as mock_generate:
            mock_generate.return_value = None

            instance = Config()
            instance.token_manager = mock_token_manager
            instance.get_token("test_token", full_token)
            mock_token_manager.get.assert_called_once_with(
                "test_token", full_token
            )
