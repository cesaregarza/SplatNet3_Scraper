from unittest.mock import MagicMock, patch

import pytest

from splatnet3_scraper.auth.exceptions import FTokenException
from splatnet3_scraper.auth.tokens.constructor import TokenManagerConstructor
from splatnet3_scraper.constants import (
    APP_VERSION_OVERRIDE_ENV,
    NXAPI_CLIENT_ASSERTION_JKU_ENV,
    NXAPI_CLIENT_ASSERTION_KID_ENV,
    NXAPI_CLIENT_ASSERTION_PRIVATE_KEY_PATH_ENV,
    NXAPI_CLIENT_ID_ENV,
    NXAPI_CLIENT_VERSION_ENV,
    NXAPI_DEFAULT_CLIENT_VERSION,
)

base_constructor_path = "splatnet3_scraper.auth.tokens.constructor"
constructor_path = base_constructor_path + ".TokenManagerConstructor"


class TestConstructor:
    @pytest.mark.parametrize(
        "with_nso",
        [True, False],
        ids=["with_nso", "without_nso"],
    )
    def test_from_session_token(self, with_nso: bool) -> None:
        nso = MagicMock()
        nso.set_app_version_override = MagicMock()
        session_token = MagicMock()
        f_token_url = MagicMock()
        with (
            patch(base_constructor_path + ".NSO") as mock_nso,
            patch(base_constructor_path + ".TokenManager") as mock_manager,
        ):
            mock_nso.new_instance.return_value = nso
            manager = TokenManagerConstructor.from_session_token(
                session_token,
                nso=nso if with_nso else None,
                f_token_url=f_token_url,
            )
            if with_nso:
                mock_nso.new_instance.assert_not_called()
            else:
                mock_nso.new_instance.assert_called_once_with()

            mock_manager.assert_called_once_with(
                nso=nso,
                f_token_url=f_token_url,
                origin="memory",
            )
            mock_manager.return_value.add_token.assert_called_once_with(
                session_token,
                "session_token",
            )
            nso.set_app_version_override.assert_called_once_with(None)
            assert manager == mock_manager.return_value

    @pytest.mark.parametrize(
        "with_gtoken",
        [True, False],
        ids=["with_gtoken", "without_gtoken"],
    )
    @pytest.mark.parametrize(
        "with_bullet_token",
        [True, False],
        ids=["with_bullet_token", "without_bullet_token"],
    )
    def test_from_tokens(
        self, with_gtoken: bool, with_bullet_token: bool
    ) -> None:
        nso = MagicMock()
        session_token = MagicMock()
        gtoken = MagicMock()
        bullet_token = MagicMock()
        f_token_url = MagicMock()
        user_agent = MagicMock()
        app_version = "9.9.9"

        with (
            patch(base_constructor_path + ".NSO") as mock_nso,
            patch(
                base_constructor_path + ".TokenRegenerator"
            ) as mock_regenerator,
            patch(
                constructor_path + ".from_session_token"
            ) as mock_from_session_token,
        ):
            mock_regenerator.generate_gtoken.return_value.value = gtoken
            mock_regenerator.generate_bullet_token.return_value.value = (
                bullet_token
            )
            mock_from_session_token.return_value.nso = nso
            mock_from_session_token.return_value.f_token_url = f_token_url
            manager = TokenManagerConstructor.from_tokens(
                session_token,
                gtoken=gtoken if with_gtoken else None,
                bullet_token=bullet_token if with_bullet_token else None,
                nso=nso,
                f_token_url=f_token_url,
                user_agent=user_agent,
                app_version=app_version,
            )
            mock_from_session_token.assert_called_once_with(
                session_token,
                nso=nso,
                f_token_url=f_token_url,
                app_version=app_version,
            )
            if with_gtoken:
                mock_regenerator.generate_gtoken.assert_not_called()

            else:
                mock_regenerator.generate_gtoken.assert_called_once_with(
                    nso, f_token_url
                )
            manager.add_token.assert_any_call(gtoken, "gtoken")

            if with_bullet_token:
                mock_regenerator.generate_bullet_token.assert_not_called()
            else:
                mock_regenerator.generate_bullet_token.assert_called_once_with(
                    nso, f_token_url, user_agent=user_agent
                )
            manager.add_token.assert_any_call(bullet_token, "bullet_token")

            assert manager == mock_from_session_token.return_value

    @pytest.mark.parametrize(
        "with_env_manager",
        [True, False],
        ids=["with_env_manager", "without_env_manager"],
    )
    def test_from_env(
        self,
        with_env_manager: bool,
    ) -> None:
        nso = MagicMock()
        f_token_url = MagicMock()
        user_agent = MagicMock()
        env_manager = MagicMock()

        with (
            patch(constructor_path + ".from_tokens") as mock_from_tokens,
            patch(
                base_constructor_path + ".EnvironmentVariablesManager"
            ) as mock_env_manager,
            patch.dict(
                "os.environ", {APP_VERSION_OVERRIDE_ENV: "8.8.8"}, clear=False
            ),
        ):
            mock_env_manager.return_value = env_manager
            mock_from_tokens.return_value.uses_nxapi_provider.return_value = (
                False
            )
            manager = TokenManagerConstructor.from_env(
                nso=nso,
                f_token_url=f_token_url,
                user_agent=user_agent,
                env_manager=env_manager if with_env_manager else None,
            )
            if with_env_manager:
                mock_env_manager.assert_not_called()
            else:
                mock_env_manager.assert_called_once_with()

            env_manager.get_all.assert_called_once_with()
            env_get_all: MagicMock = env_manager.get_all.return_value
            session_token = env_get_all.__getitem__.return_value
            env_get_all.get.assert_any_call("gtoken", None)
            env_get_all.get.assert_any_call("bullet_token", None)
            mock_from_tokens.assert_called_once_with(
                session_token=session_token,
                gtoken=env_get_all.get.return_value,
                bullet_token=env_get_all.get.return_value,
                nso=nso,
                f_token_url=f_token_url,
                user_agent=user_agent,
                app_version="8.8.8",
            )
            mock_from_tokens.return_value.flag_origin.assert_called_once_with(
                "env"
            )
            assert manager == mock_from_tokens.return_value

    def test_configure_nxapi_from_env_requires_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = MagicMock()
        manager.uses_nxapi_provider.return_value = True

        monkeypatch.delenv(NXAPI_CLIENT_ID_ENV, raising=False)

        with pytest.raises(FTokenException):
            TokenManagerConstructor._configure_nxapi_from_env(manager)

    def test_configure_nxapi_from_env_skips_when_not_using_nxapi(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = MagicMock()
        manager.uses_nxapi_provider.return_value = False

        monkeypatch.delenv(NXAPI_CLIENT_ID_ENV, raising=False)

        TokenManagerConstructor._configure_nxapi_from_env(manager)
        manager.configure_nxapi.assert_not_called()

    def test_configure_nxapi_from_env_applies_when_credentials_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = MagicMock()
        manager.uses_nxapi_provider.return_value = True

        monkeypatch.setenv(NXAPI_CLIENT_ID_ENV, "client")
        monkeypatch.setenv("NXAPI_AUTH_TOKEN_URL", "https://example.com/token")
        monkeypatch.setenv("NXAPI_ZNCA_API_AUTH_SCOPE", "ca:gf")
        monkeypatch.setenv("NXAPI_ZNCA_API_CLIENT_SECRET", "secret")
        monkeypatch.setenv("NXAPI_ZNCA_API_CLIENT_ASSERTION", "assertion")
        monkeypatch.setenv(
            "NXAPI_ZNCA_API_CLIENT_ASSERTION_TYPE",
            "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        )
        monkeypatch.setenv("NXAPI_USER_AGENT", "agent")
        monkeypatch.setenv(NXAPI_CLIENT_VERSION_ENV, "1.2.3")

        TokenManagerConstructor._configure_nxapi_from_env(manager)
        manager.configure_nxapi.assert_called_once_with(
            token_url="https://example.com/token",
            scope="ca:gf",
            client_id="client",
            client_secret="secret",
            client_assertion="assertion",
            client_assertion_private_key_path=None,
            client_assertion_jku=None,
            client_assertion_kid=None,
            client_assertion_type="urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            user_agent="agent",
            client_version="1.2.3",
        )

    def test_configure_nxapi_from_env_defaults_client_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = MagicMock()
        manager.uses_nxapi_provider.return_value = True

        monkeypatch.setenv(NXAPI_CLIENT_ID_ENV, "client")
        monkeypatch.delenv(NXAPI_CLIENT_VERSION_ENV, raising=False)

        TokenManagerConstructor._configure_nxapi_from_env(manager)
        call_kwargs = manager.configure_nxapi.call_args.kwargs
        assert call_kwargs["client_version"] == NXAPI_DEFAULT_CLIENT_VERSION

    def test_configure_nxapi_from_env_uses_legacy_secret_alias(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = MagicMock()
        manager.uses_nxapi_provider.return_value = True

        monkeypatch.setenv(NXAPI_CLIENT_ID_ENV, "client")
        monkeypatch.delenv("NXAPI_ZNCA_API_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("NXAPI_SHARED_SECRET", "legacy-secret")

        TokenManagerConstructor._configure_nxapi_from_env(manager)
        call_kwargs = manager.configure_nxapi.call_args.kwargs
        assert call_kwargs["client_secret"] == "legacy-secret"

    def test_configure_nxapi_from_env_reads_generated_assertion_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = MagicMock()
        manager.uses_nxapi_provider.return_value = True

        monkeypatch.setenv(NXAPI_CLIENT_ID_ENV, "client")
        monkeypatch.setenv(
            NXAPI_CLIENT_ASSERTION_PRIVATE_KEY_PATH_ENV,
            "/tmp/private.pem",
        )
        monkeypatch.setenv(
            NXAPI_CLIENT_ASSERTION_JKU_ENV,
            "https://example.com/.well-known/jwks.json",
        )
        monkeypatch.setenv(NXAPI_CLIENT_ASSERTION_KID_ENV, "kid-1")

        TokenManagerConstructor._configure_nxapi_from_env(manager)
        call_kwargs = manager.configure_nxapi.call_args.kwargs
        assert (
            call_kwargs["client_assertion_private_key_path"]
            == "/tmp/private.pem"
        )
        assert (
            call_kwargs["client_assertion_jku"]
            == "https://example.com/.well-known/jwks.json"
        )
        assert call_kwargs["client_assertion_kid"] == "kid-1"
