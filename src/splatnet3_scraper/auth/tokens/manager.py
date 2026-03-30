from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from splatnet3_scraper.auth.exceptions import (
    AccountCooldownException,
    FTokenException,
)
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.auth.tokens.environment_manager import (
    EnvironmentVariablesManager,
)
from splatnet3_scraper.auth.tokens.keychain import TokenKeychain
from splatnet3_scraper.auth.tokens.regenerator import TokenRegenerator
from splatnet3_scraper.auth.tokens.token_typing import ORIGIN
from splatnet3_scraper.auth.tokens.tokens import Token
from splatnet3_scraper.constants import (
    APP_ID_TOKEN_LIFETIME,
    AUTH_FAILURE_COOLDOWN,
    DEFAULT_F_TOKEN_URL,
    DEFAULT_USER_AGENT,
    NXAPI_DEFAULT_CLIENT_VERSION,
    NXAPI_ZNCA_URL,
    RATE_LIMIT_BASE_COOLDOWN,
    RATE_LIMIT_COOLDOWN_CAP,
    TOKENS,
    WEB_SERVICE_ID_TOKEN_LIFETIME,
)

if TYPE_CHECKING:
    from splatnet3_scraper.auth.nxapi_client import NXAPIClient

logger = logging.getLogger(__name__)

_NXAPI_HOST = urlparse(NXAPI_ZNCA_URL).netloc


class ManagerOrigin:
    def __init__(self, origin: ORIGIN, data: str | None = None) -> None:
        self.origin = origin
        self.data = data


class TokenManager:
    """Manages the tokens used for authentication. Handles regeneration and
    interaction with the keychain. This class is meant to mostly be used via its
    "get" method
    """

    def __init__(
        self,
        nso: NSO | None = None,
        f_token_url: str | list[str] = DEFAULT_F_TOKEN_URL,
        *,
        env_manager: EnvironmentVariablesManager | None = None,
        origin: ORIGIN = "memory",
        origin_data: str | None = None,
    ) -> None:
        """Initializes a ``TokenManager`` object. The ``TokenManager`` object
        handles the tokens used for authentication. It handles regeneration and
        interaction with the keychain. This class is meant to mostly be used via
        its "get" method.

        Args:
            nso (NSO | None): An instance of the ``NSO`` class. If one is not
                provided, a new instance will be created. Defaults to None.
            f_token_url (str | list[str] | None): The URL(s) to use to generate
                tokens. If a list is provided, each URL will be tried in order
                until a token is successfully generated. If None is provided,
                the default NXAPI URL will be used. Defaults to None.
            env_manager (EnvironmentVariablesManager | None): An instance of the
                ``EnvironmentVariablesManager`` class. If one is not provided, a
                new instance will be created. Defaults to None.
            origin (ORIGIN): The origin of the tokens. Defaults to "memory". One
                of "memory", "env", or "file".
            origin_data (str | None): The data associated with the origin. If
                the origin is "memory" or "env", this is ignored. If the origin
                is "file", this should be the path to the file. Defaults to
                None.

        Raises:
            ValueError: If the ``NSO`` object does not have a session token.
        """
        nso = nso or NSO.new_instance()
        self.keychain = TokenKeychain()
        # Check that nso has a session token
        try:
            session_token = nso.session_token
            self.nso = nso
            self.add_token(session_token, TOKENS.SESSION_TOKEN)
        except ValueError as e:
            raise e

        if isinstance(f_token_url, str):
            self.f_token_url = [f_token_url]
        else:
            self.f_token_url = f_token_url

        self.env_manager = env_manager or EnvironmentVariablesManager()
        self.origin = ManagerOrigin(origin, origin_data)
        self._nxapi_client: NXAPIClient | None = None
        self.next_available_at: float = 0.0
        self.error_count: int = 0
        self.last_status_code: int | None = None
        self._id_token_expires_at: float = 0.0
        self._web_service_token_expires_at: float = 0.0

    def flag_origin(self, origin: ORIGIN, data: str | None = None) -> None:
        """Flags the origin of the token manager. This is used to identify where
        the token manager was loaded from, if anywhere. This is used to help
        keep track of whether the user wants to save the tokens to disk or not,
        but can potentially be used for other things in the future. This is
        called automatically when the token manager is loaded from a config
        file or environment variables. Subsequent calls to this method will
        overwrite the previous origin.

        Args:
            origin (ORIGIN): The origin of the token manager. One of "memory",
            "env", or "file".
            data (str | None): Additional data about the origin. For example,
                if the token manager was loaded from a config file, this would
                be the path to the config file. On the other hand, if the token
                manager was loaded from environment variables, this would be
                None.
        """
        logger.debug("Flagging origin %s with data %s", origin, data)
        self.origin = ManagerOrigin(origin, data)

    def configure_nxapi(
        self,
        *,
        token_url: str,
        scope: str,
        client_id: str | None,
        client_secret: str | None = None,
        client_assertion: str | None = None,
        client_assertion_private_key_path: str | None = None,
        client_assertion_jku: str | None = None,
        client_assertion_kid: str | None = None,
        client_assertion_type: str | None = None,
        user_agent: str | None = None,
        client_version: str | None = None,
    ) -> None:
        """Attach an nxapi-auth client to the managed NSO instance.

        If the NXAPI provider is in use but credentials are missing, a
        ``FTokenException`` is raised immediately so callers can surface the
        misconfiguration instead of failing mid-request.
        """
        if not client_id:
            if self.uses_nxapi_provider():
                raise FTokenException(
                    "NXAPI client id is required when using "
                    "the default ftoken provider. Set "
                    "nxapi_client_id in your config or "
                    "override f_token_url."
                )
            logger.debug("NXAPI client id not provided; disabling nxapi helper")
            self._nxapi_client = None
            if hasattr(self.nso, "set_nxapi_client"):
                self.nso.set_nxapi_client(None)
            return

        resolved_version = client_version or NXAPI_DEFAULT_CLIENT_VERSION
        generated_assertion_fields = {
            "nxapi_client_assertion_private_key_path": (
                client_assertion_private_key_path
            ),
            "nxapi_client_assertion_jku": client_assertion_jku,
            "nxapi_client_assertion_kid": client_assertion_kid,
        }
        if any(generated_assertion_fields.values()):
            missing = [
                name
                for name, value in generated_assertion_fields.items()
                if not value
            ]
            if missing:
                missing_csv = ", ".join(missing)
                raise FTokenException(
                    "Generated NXAPI client assertions require "
                    f"{missing_csv} to be set."
                )

        from splatnet3_scraper.auth.nxapi_client import NXAPIClient

        self._nxapi_client = NXAPIClient(
            client_id=client_id,
            client_secret=client_secret,
            client_assertion=client_assertion,
            client_assertion_private_key_path=(
                client_assertion_private_key_path
            ),
            client_assertion_jku=client_assertion_jku,
            client_assertion_kid=client_assertion_kid,
            client_assertion_type=client_assertion_type,
            scope=scope,
            token_url=token_url,
            user_agent=user_agent,
            client_version=resolved_version,
            session=self.nso.session,
        )
        if hasattr(self.nso, "set_nxapi_client"):
            self.nso.set_nxapi_client(self._nxapi_client)

    def uses_nxapi_provider(self) -> bool:
        for url in self.f_token_url:
            try:
                if urlparse(url).netloc == _NXAPI_HOST:
                    return True
            except ValueError:
                continue
        return False

    def _record_token_refresh(self) -> None:
        now = time.time()
        self._id_token_expires_at = now + APP_ID_TOKEN_LIFETIME
        self._web_service_token_expires_at = now + WEB_SERVICE_ID_TOKEN_LIFETIME
        self.next_available_at = max(self.next_available_at, now)
        self.error_count = 0

    def mark_tokens_fresh(self) -> None:
        """Expose token refresh bookkeeping for constructors and tests."""
        self._record_token_refresh()

    def _schedule_rate_limit_backoff(self) -> None:
        self.error_count += 1
        exponent = max(self.error_count - 1, 0)
        delay = RATE_LIMIT_BASE_COOLDOWN * (2**exponent)
        delay = min(delay, RATE_LIMIT_COOLDOWN_CAP)
        jitter = random.uniform(0.6, 1.4)
        cooldown = min(delay * jitter, RATE_LIMIT_COOLDOWN_CAP)
        self.next_available_at = max(
            self.next_available_at, time.time() + cooldown
        )
        logger.debug(
            "Scheduling rate limit cooldown for %.2fs (error count=%s)",
            cooldown,
            self.error_count,
        )

    def _schedule_auth_cooldown(self) -> None:
        self.error_count += 1
        base = AUTH_FAILURE_COOLDOWN * max(self.error_count, 1)
        jitter = random.uniform(0.6, 1.2)
        cooldown = min(base * jitter, RATE_LIMIT_COOLDOWN_CAP)
        self.next_available_at = max(
            self.next_available_at, time.time() + cooldown
        )
        logger.debug(
            "Scheduling auth cooldown for %.2fs (error count=%s)",
            cooldown,
            self.error_count,
        )

    def cooldown_remaining(self) -> float:
        return max(0.0, self.next_available_at - time.time())

    def ready_for_endpoint(self, endpoint: str = "web") -> bool:
        now = time.time()
        if now < self.next_available_at:
            return False
        if endpoint == "app":
            return now < self._id_token_expires_at
        return now < self._web_service_token_expires_at

    def ensure_tokens_valid(self) -> None:
        now = time.time()
        if now < self.next_available_at:
            raise AccountCooldownException(
                "Account is cooling down for another"
                f" {self.cooldown_remaining():.1f} seconds."
            )

        try:
            gtoken = self.keychain.get(TOKENS.GTOKEN, full_token=True)
        except ValueError:
            self.generate_gtoken()
        else:
            if gtoken.is_expired:
                self.generate_gtoken()

        try:
            bullet_token = self.keychain.get(
                TOKENS.BULLET_TOKEN, full_token=True
            )
        except ValueError:
            self.generate_bullet_token()
        else:
            if bullet_token.is_expired:
                self.generate_bullet_token()

        if now >= self._id_token_expires_at:
            self.regenerate_tokens()

    def record_response(self, status_code: int) -> None:
        self.last_status_code = status_code
        if status_code in (429, 503):
            self._schedule_rate_limit_backoff()
        elif status_code in (401, 403):
            self._schedule_auth_cooldown()
        elif 200 <= status_code < 400:
            self.error_count = 0
            self.next_available_at = max(self.next_available_at, time.time())

    def add_token(
        self,
        token: str | Token,
        name: str | None = None,
        timestamp: float | None = None,
    ) -> None:
        """Adds a token to the keychain. If the token is a string, the name of
        the token must be provided. If the token is a ``Token`` object, the
        name of the token will be used. If the token already exists, it will
        overwrite the existing token.

        Args:
            token (str | Token): The token to add to the keychain.
            name (str | None, optional): The name of the token. Only required if
                the token is a string. Defaults to None.
            timestamp (float | None, optional): The timestamp of the token.
                Defaults to None.

        Raises:
            ValueError: If the token is a string and the name of the token is
                not provided.
        """
        try:
            new_token = self.keychain.add_token(token, name, timestamp)
        except ValueError as e:
            raise e

        logger.debug("Added token %s to keychain", new_token.name)
        if new_token.name == TOKENS.GTOKEN:
            self.nso._gtoken = new_token.value
        elif new_token.name == TOKENS.SESSION_TOKEN:
            self.nso._session_token = new_token.value

    def get_token(self, name: str) -> Token:
        """Gets a token from the keychain.

        Args:
            name (str): The name of the token to get.

        Raises:
            ValueError: If the token is not found in the keychain.

        Returns:
            Token: The token that was retrieved.
        """
        try:
            token = self.keychain.get(name, full_token=True)
        except ValueError as e:
            raise e

        logger.debug("Retrieved token %s from keychain", token.name)
        return token

    def regenerate_tokens(self) -> None:
        """Regenerates all the tokens. This is done by calling the
        ``TokenRegenerator.generate_all_tokens`` method. The tokens are then
        added to the keychain.
        """
        logger.info("Regenerating tokens")
        tokens = TokenRegenerator.generate_all_tokens(
            self.nso, self.f_token_url
        )
        for token in tokens.values():
            self.add_token(token)
        self._record_token_refresh()

    def generate_gtoken(self) -> None:
        """Generates a gtoken. This is done by calling the
        ``TokenRegenerator.generate_gtoken`` method. The token is then added to
        the keychain.
        """
        logger.info("Generating gtoken")
        token = TokenRegenerator.generate_gtoken(self.nso, self.f_token_url)
        self.add_token(token)
        self._record_token_refresh()

    def generate_bullet_token(self) -> None:
        """Generates a bullet token. This is done by calling the
        ``TokenRegenerator.generate_bullet_token`` method. The token is then
        added to the keychain.
        """
        logger.info("Generating bullet token")
        token = TokenRegenerator.generate_bullet_token(
            self.nso, self.f_token_url, DEFAULT_USER_AGENT
        )
        self.add_token(token)
