import configparser
import json
from unittest.mock import MagicMock, patch

import pytest

from splatnet3_scraper.auth.tokens import TokenManager, TokenManagerConstructor
from splatnet3_scraper.constants import (
    NXAPI_AUTH_TOKEN_URL,
    NXAPI_DEFAULT_AUTH_SCOPE,
    TOKENS,
)
from splatnet3_scraper.query.config.config import Config
from splatnet3_scraper.query.config.config_option_handler import (
    ConfigOptionHandler,
)

base_config_path = "splatnet3_scraper.query.config.config"
config_path = base_config_path + ".Config"
base_handler_path = "splatnet3_scraper.query.config.config_option_handler"
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

    def test_set_value_app_version_override(self) -> None:
        mock_handler = MagicMock()
        mock_token_manager = MagicMock()
        config = Config(mock_handler, token_manager=mock_token_manager)
        config._apply_app_version_override = MagicMock()
        config.set_value("app_version_override", "4.5.6")
        mock_handler.set_value.assert_called_once_with(
            "app_version_override", "4.5.6"
        )
        config._apply_app_version_override.assert_called_once_with()

    def test_config_configures_nxapi_with_client_version(self) -> None:
        handler = ConfigOptionHandler()
        handler.set_value(TOKENS.SESSION_TOKEN, "session")
        handler.set_value(TOKENS.GTOKEN, "gtoken")
        handler.set_value(TOKENS.BULLET_TOKEN, "bullet")
        handler.set_value("nxapi_client_id", "client")
        handler.set_value("nxapi_client_version", "2.0.1")

        mock_token_manager = MagicMock()
        mock_token_manager.nso = MagicMock()
        mock_token_manager.uses_nxapi_provider.return_value = True

        Config(handler, token_manager=mock_token_manager)

        mock_token_manager.nso.set_app_version_override.assert_called_once_with(
            None
        )
        mock_token_manager.configure_nxapi.assert_called_once_with(
            token_url=NXAPI_AUTH_TOKEN_URL,
            scope=NXAPI_DEFAULT_AUTH_SCOPE,
            client_id="client",
            client_secret=None,
            client_assertion=None,
            client_assertion_private_key_path=None,
            client_assertion_jku=None,
            client_assertion_kid=None,
            client_assertion_type=None,
            user_agent=None,
            client_version="2.0.1",
        )

    def test_config_configures_generated_nxapi_assertion(self) -> None:
        handler = ConfigOptionHandler()
        handler.set_value(TOKENS.SESSION_TOKEN, "session")
        handler.set_value("nxapi_client_id", "client")
        handler.set_value(
            "nxapi_client_assertion_private_key_path",
            "/tmp/private.pem",
        )
        handler.set_value(
            "nxapi_client_assertion_jku",
            "https://example.com/.well-known/jwks.json",
        )
        handler.set_value("nxapi_client_assertion_kid", "kid-1")

        mock_token_manager = MagicMock()
        mock_token_manager.nso = MagicMock()
        mock_token_manager.uses_nxapi_provider.return_value = True

        Config(handler, token_manager=mock_token_manager)

        call_kwargs = mock_token_manager.configure_nxapi.call_args.kwargs
        assert (
            call_kwargs["client_assertion_private_key_path"]
            == "/tmp/private.pem"
        )
        assert (
            call_kwargs["client_assertion_jku"]
            == "https://example.com/.well-known/jwks.json"
        )
        assert call_kwargs["client_assertion_kid"] == "kid-1"

    @pytest.mark.parametrize(
        "prefix",
        [
            "test",
            "",
        ],
        ids=[
            "prefix",
            "no prefix",
        ],
    )
    def test_from_empty_handler(self, prefix: str) -> None:
        mock_handler = MagicMock()

        with (
            patch(base_config_path + ".ConfigOptionHandler") as mock_handler,
            patch(config_path) as mock_config,
        ):
            mock_config.DEFAULT_PREFIX = "SN3S"
            expected_prefix = prefix or "SN3S"
            config = Config.from_empty_handler(prefix)
            mock_handler.assert_called_once_with(prefix=expected_prefix)
            mock_get = mock_handler.return_value.get_value
            assert mock_get.call_count == 4
            mock_config.from_tokens.assert_called_once_with(
                session_token=mock_get.return_value,
                gtoken=mock_get.return_value,
                bullet_token=mock_get.return_value,
                prefix=expected_prefix,
                app_version=mock_get.return_value,
            )

    @pytest.mark.parametrize(
        "prefix",
        [
            "test",
            "",
        ],
        ids=[
            "prefix",
            "no prefix",
        ],
    )
    def test_from_tokens(self, prefix: str) -> None:
        session_token = MagicMock()
        gtoken = MagicMock()
        bullet_token = MagicMock()
        mock_token_manager = MagicMock()

        with (
            patch(base_config_path + ".ConfigOptionHandler") as mock_handler,
            patch(base_config_path + ".TokenManagerConstructor") as mock_tmc,
            patch(config_path) as mock_config,
        ):
            mock_config.DEFAULT_PREFIX = "SN3S"
            mock_tmc.from_tokens.return_value = mock_token_manager
            config = Config.from_tokens(
                session_token,
                gtoken=gtoken,
                bullet_token=bullet_token,
                prefix=prefix,
            )
            mock_tmc.from_tokens.assert_called_once_with(
                session_token=session_token,
                gtoken=gtoken,
                bullet_token=bullet_token,
                app_version=None,
            )
            expected_prefix = prefix or "SN3S"
            mock_handler.assert_called_once_with(prefix=expected_prefix)
            assert mock_handler.return_value.set_value.call_count == 4
            mock_handler.return_value.set_value.assert_any_call(
                "app_version_override", None
            )
            mock_config.assert_called_once_with(
                mock_handler.return_value,
                token_manager=mock_token_manager,
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

        mock_session = "session_token_value"
        mock_gtoken = "gtoken_value"
        mock_bullet = "bullet_token_value"
        mock_app_version = "3.2.1"

        def get_value_side_effect(key: str):
            return {
                "session_token": mock_session,
                "gtoken": mock_gtoken,
                "bullet_token": mock_bullet,
                "app_version_override": mock_app_version,
            }[key]

        mock_handler.get_value.side_effect = get_value_side_effect

        with (
            patch(config_path) as mock_config,
            patch(base_config_path + ".TokenManagerConstructor") as mock_tmc,
        ):
            mock_config.DEFAULT_PREFIX = "SN3S"
            mock_tmc.from_session_token.return_value = mock_token_manager

            config = Config.from_config_handler(
                mock_handler,
                output_file_path=expected_file_path,
            )
            mock_tmc.from_session_token.assert_called_once_with(
                mock_session,
                app_version=mock_app_version,
            )
            mock_token_manager.add_token.assert_any_call(mock_gtoken, "gtoken")
            mock_token_manager.add_token.assert_any_call(
                mock_bullet, "bullet_token"
            )
            mock_config.assert_called_once_with(
                mock_handler,
                token_manager=mock_token_manager,
                output_file_path=expected_file_path,
            )
            assert mock_handler.get_value.call_count == 4

    def test_from_config_handler_without_app_version_uses_none(self) -> None:
        mock_handler = MagicMock()
        mock_token_manager = MagicMock()

        def get_value_side_effect(key: str):
            if key == "app_version_override":
                raise ValueError("missing")
            return {
                "session_token": "session_token_value",
                "gtoken": "gtoken_value",
                "bullet_token": "bullet_token_value",
            }[key]

        mock_handler.get_value.side_effect = get_value_side_effect

        with (
            patch(config_path) as mock_config,
            patch(base_config_path + ".TokenManagerConstructor") as mock_tmc,
        ):
            mock_config.DEFAULT_PREFIX = "SN3S"
            mock_tmc.from_session_token.return_value = mock_token_manager

            Config.from_config_handler(mock_handler)

        mock_tmc.from_session_token.assert_called_once_with(
            "session_token_value",
            app_version=None,
        )
        mock_config.assert_called_once_with(
            mock_handler,
            token_manager=mock_token_manager,
            output_file_path=None,
        )

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
            assert config.gtoken == "test_gtoken"
            assert config.bullet_token == "test_bullet_token"
            assert config.handler.unknown_options == [
                ("extra_token", "test_extra_token")
            ]
            assert config.handler.get_value("country") == "US"
            assert config.handler.get_value("language") == "en-US"

        def test_no_data(self, no_data: str) -> None:
            config = Config.from_file(
                no_data,
            )
            assert config.session_token == "test_session_token"
            assert config.gtoken == "test_gtoken"
            assert config.bullet_token == "test_bullet_token"
            assert config.handler.get_value("user_agent") == "test_user_agent"
            assert config.handler.get_option("user_agent").section == "options"

        def test_no_tokens_section(self, no_tokens_section: str) -> None:
            config = Config.from_file(
                no_tokens_section,
            )
            assert config.session_token == "test_session_token"
            assert config.gtoken == "test_gtoken"
            assert config.bullet_token == "test_bullet_token"
            assert config.handler.get_value("country") == "US"
            assert config.handler.get_value("language") == "en-US"
            assert config.handler.get_value("user_agent") == "test_user_agent"
            assert config.handler.get_option("user_agent").section == "options"

        def test_valid(self, valid: str) -> None:
            config = Config.from_file(
                valid,
            )
            assert config.session_token == "test_session_token"
            assert config.gtoken == "test_gtoken"
            assert config.bullet_token == "test_bullet_token"
            assert config.handler.get_value("country") == "US"
            assert config.handler.get_value("language") == "en-US"
            assert config.handler.get_value("user_agent") == "test_user_agent"
            assert config.handler.get_option("user_agent").section == "options"

        def test_valid_with_ftoken(self, valid_with_ftoken: str) -> None:
            config = Config.from_file(
                valid_with_ftoken,
            )
            assert config.session_token == "test_session_token"
            assert config.gtoken == "test_gtoken"
            assert config.bullet_token == "test_bullet_token"
            assert config.handler.get_value("country") == "US"
            assert config.handler.get_value("language") == "en-US"
            assert config.handler.get_value("user_agent") == "test_user_agent"
            assert config.handler.get_option("user_agent").section == "options"
            assert config.handler.get_value("f_token_url") == [
                "test_f_token_url"
            ]

        def test_valid_with_ftoken_list(
            self, valid_with_ftoken_list: str
        ) -> None:
            config = Config.from_file(
                valid_with_ftoken_list,
            )
            assert config.session_token == "test_session_token"
            assert config.gtoken == "test_gtoken"
            assert config.bullet_token == "test_bullet_token"
            assert config.handler.get_value("country") == "US"
            assert config.handler.get_value("language") == "en-US"
            assert config.handler.get_value("user_agent") == "test_user_agent"
            assert config.handler.get_option("user_agent").section == "options"
            assert config.handler.get_value("f_token_url") == [
                "test_f_token_url0",
                "test_f_token_url1",
            ]

        def test_s3s_config(self, s3s_config: str) -> None:
            config = Config.from_s3s_config(
                s3s_config,
            )
            assert config.session_token == "test_session_token"
            assert config.gtoken == "test_gtoken"
            assert config.bullet_token == "test_bullet_token"
            assert config.handler.get_value("country") == "US"
            assert config.handler.get_value("language") == "en-US"
            assert config.handler.get_value("user_agent") == "test_user_agent"
            assert config.handler.get_option("user_agent").section == "options"
            assert config.handler.get_value("f_token_url") == [
                "test_f_token_url",
            ]

        def test_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
            with monkeypatch.context() as m:
                m.setenv("SN3S_SESSION_TOKEN", "test_session_token")
                m.setenv("SN3S_GTOKEN", "test_gtoken")
                m.setenv("SN3S_BULLET_TOKEN", "test_bullet_token")
                config = Config.from_empty_handler("SN3S")
                assert config.session_token == "test_session_token"
                assert config.gtoken == "test_gtoken"
                assert config.bullet_token == "test_bullet_token"

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
