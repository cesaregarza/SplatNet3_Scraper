from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from splatnet3_scraper.auth.exceptions import (
    AccountCooldownException,
    FTokenException,
    SplatNetException,
)
from splatnet3_scraper.auth.tokens.manager import ManagerOrigin, TokenManager
from splatnet3_scraper.constants import (
    NXAPI_ZNCA_URL,
    RATE_LIMIT_BASE_COOLDOWN,
    TOKENS,
)

ftoken_urls = [
    "ftoken_url_1",
    "ftoken_url_2",
    "ftoken_url_3",
    "ftoken_url_4",
]

base_token_manager_path = "splatnet3_scraper.auth.tokens.manager"
token_manager_path = base_token_manager_path + ".TokenManager"


class TestTokenManager:
    @pytest.fixture
    def mock_token_manager(self) -> TokenManager:
        with (
            patch(base_token_manager_path + ".NSO"),
            patch(base_token_manager_path + ".EnvironmentVariablesManager"),
            patch(base_token_manager_path + ".TokenKeychain"),
            patch(base_token_manager_path + ".ManagerOrigin"),
        ):
            manager = TokenManager()
            token = MagicMock()
            token.value = "token"
            token.is_expired = False
            manager.keychain.get.return_value = token
            return manager

    @pytest.mark.parametrize(
        "with_nso",
        [True, "without_session", False],
        ids=["with_nso", "with_nso_no_session", "without_nso"],
    )
    @pytest.mark.parametrize(
        "f_token_url",
        [
            ftoken_urls[0],
            ftoken_urls,
        ],
        ids=["single_url", "multiple_urls"],
    )
    @pytest.mark.parametrize(
        "with_env_manager",
        [True, False],
        ids=["with_env_manager", "without_env_manager"],
    )
    @pytest.mark.parametrize(
        "with_origin",
        [True, False],
        ids=["with_origin", "without_origin"],
    )
    @pytest.mark.parametrize(
        "with_origin_data",
        [True, False],
        ids=["with_origin_data", "without_origin_data"],
    )
    def test_init(
        self,
        with_nso: bool | str,
        f_token_url: str | list[str] | None,
        with_env_manager: bool,
        with_origin: bool,
        with_origin_data: bool,
    ) -> None:
        nso = MagicMock()
        env_manager = MagicMock()

        def session_token_side_effect(*args, **kwargs) -> str:
            if with_nso == "without_session":
                raise ValueError("test")
            return "test_session_token"

        type(nso).session_token = PropertyMock(
            side_effect=session_token_side_effect
        )

        with (
            patch(base_token_manager_path + ".NSO") as mock_nso,
            patch(
                base_token_manager_path + ".EnvironmentVariablesManager"
            ) as mock_env_manager,
            patch(base_token_manager_path + ".TokenKeychain") as mock_keychain,
            patch(base_token_manager_path + ".ManagerOrigin") as mock_origin,
        ):
            mock_nso.new_instance.return_value = nso
            mock_env_manager.return_value = env_manager

            if with_nso == "without_session":
                with pytest.raises(ValueError):
                    TokenManager(
                        nso=None,
                        f_token_url=f_token_url,
                        env_manager=env_manager if with_env_manager else None,
                        origin="origin" if with_origin else "memory",
                        origin_data="test_data" if with_origin_data else None,
                    )
                return

            instance = TokenManager(
                nso=nso if with_nso else None,
                f_token_url=f_token_url,
                env_manager=env_manager if with_env_manager else None,
                origin="origin" if with_origin else "memory",
                origin_data="test_data" if with_origin_data else None,
            )

            if with_nso:
                mock_nso.new_instance.assert_not_called()
            else:
                mock_nso.new_instance.assert_called_once()

            if with_env_manager:
                mock_env_manager.assert_not_called()
            else:
                mock_env_manager.assert_called_once()

            if isinstance(f_token_url, str):
                expected_f_token_url = [f_token_url]
            else:
                expected_f_token_url = f_token_url

            assert instance.nso == nso
            assert instance.f_token_url == expected_f_token_url
            assert instance.env_manager == env_manager
            assert instance.keychain == mock_keychain.return_value
            assert instance.origin == mock_origin.return_value

            mock_origin.assert_called_once_with(
                "origin" if with_origin else "memory",
                "test_data" if with_origin_data else None,
            )

    def test_flag_origin(self, mock_token_manager: TokenManager) -> None:
        mock_token_manager.flag_origin("test_origin", "test_data")
        assert isinstance(mock_token_manager.origin, ManagerOrigin)
        assert mock_token_manager.origin.origin == "test_origin"
        assert mock_token_manager.origin.data == "test_data"

    @pytest.mark.parametrize(
        "token_name",
        [
            TOKENS.SESSION_TOKEN,
            TOKENS.GTOKEN,
            TOKENS.BULLET_TOKEN,
        ],
        ids=["session_token", "gtoken", "bullet_token"],
    )
    @pytest.mark.parametrize(
        "raise_exception",
        [True, False],
        ids=["raise_exception", "no_exception"],
    )
    def test_add_token(
        self,
        mock_token_manager: TokenManager,
        token_name: str,
        raise_exception: bool,
    ) -> None:
        token = MagicMock()
        token.name = token_name
        nso = mock_token_manager.nso

        def simulate_add_token(*args, **kwargs):
            if raise_exception:
                raise ValueError("test")
            return token

        mock_token_manager.keychain.add_token.side_effect = simulate_add_token

        if raise_exception:
            with pytest.raises(ValueError):
                mock_token_manager.add_token(token)
            return

        # Add token is called on init, so we need to reset the call count
        mock_token_manager.keychain.add_token.reset_mock()
        mock_token_manager.add_token(token)
        mock_token_manager.keychain.add_token.assert_called_once_with(
            token, None, None
        )
        if token_name == TOKENS.GTOKEN:
            assert nso._gtoken == token.value
        else:
            assert nso._gtoken != token.value

        if token_name == TOKENS.SESSION_TOKEN:
            assert nso._session_token == token.value
        else:
            assert nso._session_token != token.value

    def test_configure_nxapi_requires_credentials(self) -> None:
        class DummyNSO:
            def __init__(self) -> None:
                self._session_token = "session"
                self.session = MagicMock()
                self._set_client = None

            @property
            def session_token(self) -> str:
                return self._session_token

            def set_nxapi_client(self, client):
                self._set_client = client

        manager = TokenManager(nso=DummyNSO(), f_token_url=[NXAPI_ZNCA_URL])

        with pytest.raises(FTokenException):
            manager.configure_nxapi(
                token_url="https://nxapi-auth.fancy.org.uk/api/oauth/token",
                scope="ca:gf",
                client_id=None,
                client_secret=None,
                client_assertion=None,
                client_assertion_type=None,
                user_agent=None,
                client_version="1.0.0",
            )

    def test_configure_nxapi_uses_default_client_version(
        self,
    ) -> None:
        from splatnet3_scraper.constants import (
            NXAPI_DEFAULT_CLIENT_VERSION,
        )

        class DummyNSO:
            def __init__(self) -> None:
                self._session_token = "session"
                self.session = MagicMock()
                self._set_client = None

            @property
            def session_token(self) -> str:
                return self._session_token

            def set_nxapi_client(self, client):
                self._set_client = client

        manager = TokenManager(nso=DummyNSO(), f_token_url=[NXAPI_ZNCA_URL])

        # Should NOT raise — uses default client version
        manager.configure_nxapi(
            token_url=("https://nxapi-auth.fancy.org.uk/api/oauth/token"),
            scope="ca:gf",
            client_id="client-id",
            client_secret=None,
            client_assertion=None,
            client_assertion_type=None,
            user_agent=None,
            client_version=None,
        )
        assert manager._nxapi_client is not None
        assert (
            manager._nxapi_client.client_version == NXAPI_DEFAULT_CLIENT_VERSION
        )

    def test_generate_bullet_token_refreshes_invalid_gtoken(
        self,
        mock_token_manager: TokenManager,
    ) -> None:
        token = MagicMock()
        token.name = TOKENS.BULLET_TOKEN

        with patch(
            base_token_manager_path
            + ".TokenRegenerator.generate_bullet_token"
        ) as mock_generate_bullet:
            mock_generate_bullet.side_effect = [
                SplatNetException(
                    "Error 401: Invalid Game Web Token (gtoken)"
                ),
                token,
            ]
            mock_token_manager.generate_gtoken = MagicMock()
            mock_token_manager.add_token = MagicMock()

            mock_token_manager.generate_bullet_token()

            mock_token_manager.generate_gtoken.assert_called_once_with()
            assert mock_generate_bullet.call_count == 2
            mock_token_manager.add_token.assert_called_once_with(token)

    def test_generate_bullet_token_reraises_other_splatnet_errors(
        self,
        mock_token_manager: TokenManager,
    ) -> None:
        with patch(
            base_token_manager_path
            + ".TokenRegenerator.generate_bullet_token"
        ) as mock_generate_bullet:
            mock_generate_bullet.side_effect = SplatNetException(
                "Error 403: Outdated Version"
            )
            mock_token_manager.generate_gtoken = MagicMock()

            with pytest.raises(SplatNetException, match="Outdated Version"):
                mock_token_manager.generate_bullet_token()

            mock_token_manager.generate_gtoken.assert_not_called()

    def test_configure_nxapi_missing_credentials_non_nxapi(self) -> None:
        class DummyNSO:
            def __init__(self) -> None:
                self._session_token = "session"
                self.session = MagicMock()

            @property
            def session_token(self) -> str:
                return self._session_token

            def set_nxapi_client(self, client):
                self._set_client = client

        manager = TokenManager(
            nso=DummyNSO(), f_token_url=["https://example.com/f"]
        )

        # Should quietly disable nxapi helper without raising
        manager.configure_nxapi(
            token_url="https://nxapi-auth.fancy.org.uk/api/oauth/token",
            scope="ca:gf",
            client_id=None,
            client_secret=None,
            client_assertion=None,
            client_assertion_type=None,
            user_agent=None,
            client_version=None,
        )

    def test_configure_nxapi_rejects_partial_generated_assertion_inputs(
        self,
    ) -> None:
        class DummyNSO:
            def __init__(self) -> None:
                self._session_token = "session"
                self.session = MagicMock()
                self._set_client = None

            @property
            def session_token(self) -> str:
                return self._session_token

            def set_nxapi_client(self, client):
                self._set_client = client

        manager = TokenManager(nso=DummyNSO(), f_token_url=[NXAPI_ZNCA_URL])

        with pytest.raises(FTokenException, match="nxapi_client_assertion_kid"):
            manager.configure_nxapi(
                token_url="https://nxapi-auth.fancy.org.uk/api/oauth/token",
                scope="ca:gf",
                client_id="client-id",
                client_assertion_private_key_path="/tmp/private.pem",
                client_assertion_jku=(
                    "https://example.com/.well-known/jwks.json"
                ),
            )

    @pytest.mark.parametrize(
        "raise_exception",
        [True, False],
        ids=["raise_exception", "no_exception"],
    )
    def test_get_token(
        self, mock_token_manager: TokenManager, raise_exception: bool
    ) -> None:
        mock_token = MagicMock()

        def simulate_get(*args, **kwargs):
            if raise_exception:
                raise ValueError("test")
            return mock_token

        mock_token_manager.keychain.get.side_effect = simulate_get

        if raise_exception:
            with pytest.raises(ValueError):
                mock_token_manager.get_token("test")
            return

        token = mock_token_manager.get_token("test")
        mock_token_manager.keychain.get.assert_called_once_with(
            "test", full_token=True
        )
        assert token == mock_token

    def test_regenerate_tokens(self, mock_token_manager: TokenManager) -> None:
        with (
            patch(
                base_token_manager_path
                + ".TokenRegenerator.generate_all_tokens"
            ) as mock_generate_all_tokens,
            patch(token_manager_path + ".add_token") as mock_add_token,
        ):
            mock_generate_all_tokens.return_value = {
                f"test_token_{i}": f"test_value_{i}" for i in range(15)
            }
            mock_token_manager.regenerate_tokens()
            mock_generate_all_tokens.assert_called_once_with(
                mock_token_manager.nso, mock_token_manager.f_token_url
            )
            assert mock_add_token.call_count == 15

    def test_record_response_rate_limit_sets_cooldown(
        self, mock_token_manager: TokenManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            f"{base_token_manager_path}.time.time", lambda: 1000.0
        )
        monkeypatch.setattr(
            f"{base_token_manager_path}.random.uniform", lambda a, b: 1.0
        )

        mock_token_manager.record_response(429)

        assert mock_token_manager.error_count == 1
        assert mock_token_manager.cooldown_remaining() == pytest.approx(
            RATE_LIMIT_BASE_COOLDOWN
        )

    def test_ensure_tokens_valid_respects_cooldown(
        self, mock_token_manager: TokenManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            f"{base_token_manager_path}.time.time", lambda: 50.0
        )
        mock_token_manager.next_available_at = 60.0

        with pytest.raises(AccountCooldownException):
            mock_token_manager.ensure_tokens_valid()

    def test_ensure_tokens_valid_refreshes_expired_tokens(
        self, mock_token_manager: TokenManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tokens = {
            TOKENS.GTOKEN: MagicMock(is_expired=True, value="gtoken"),
            TOKENS.BULLET_TOKEN: MagicMock(is_expired=False, value="bullet"),
        }

        def get_token(name: str, *, full_token: bool = True):
            return tokens[name]

        mock_token_manager.keychain.get.side_effect = get_token
        mock_token_manager.generate_gtoken = MagicMock()
        mock_token_manager.generate_bullet_token = MagicMock()
        mock_token_manager.regenerate_tokens = MagicMock()
        mock_token_manager._id_token_expires_at = 400.0

        monkeypatch.setattr(
            f"{base_token_manager_path}.time.time", lambda: 500.0
        )

        mock_token_manager.ensure_tokens_valid()

        mock_token_manager.generate_gtoken.assert_called_once()
        mock_token_manager.regenerate_tokens.assert_not_called()

    def test_ensure_tokens_valid_does_not_force_full_refresh_for_stale_app_timer(
        self, mock_token_manager: TokenManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tokens = {
            TOKENS.GTOKEN: MagicMock(is_expired=False, value="gtoken"),
            TOKENS.BULLET_TOKEN: MagicMock(is_expired=False, value="bullet"),
        }

        def get_token(name: str, *, full_token: bool = True):
            return tokens[name]

        mock_token_manager.keychain.get.side_effect = get_token
        mock_token_manager.generate_gtoken = MagicMock()
        mock_token_manager.generate_bullet_token = MagicMock()
        mock_token_manager.regenerate_tokens = MagicMock()
        mock_token_manager._id_token_expires_at = 400.0

        monkeypatch.setattr(
            f"{base_token_manager_path}.time.time", lambda: 500.0
        )

        mock_token_manager.ensure_tokens_valid()

        mock_token_manager.generate_gtoken.assert_not_called()
        mock_token_manager.generate_bullet_token.assert_not_called()
        mock_token_manager.regenerate_tokens.assert_not_called()
