import logging
import os
from typing import cast

from splatnet3_scraper.auth.exceptions import FTokenException
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.auth.tokens.environment_manager import (
    EnvironmentVariablesManager,
)
from splatnet3_scraper.auth.tokens.manager import TokenManager
from splatnet3_scraper.auth.tokens.regenerator import TokenRegenerator
from splatnet3_scraper.constants import (
    APP_VERSION_OVERRIDE_ENV,
    DEFAULT_F_TOKEN_URL,
    DEFAULT_USER_AGENT,
    NXAPI_AUTH_TOKEN_URL,
    NXAPI_AUTH_TOKEN_URL_ENV,
    NXAPI_CLIENT_ASSERTION_ENV,
    NXAPI_CLIENT_ASSERTION_JKU_ENV,
    NXAPI_CLIENT_ASSERTION_KID_ENV,
    NXAPI_CLIENT_ASSERTION_PRIVATE_KEY_PATH_ENV,
    NXAPI_CLIENT_ASSERTION_TYPE_ENV,
    NXAPI_CLIENT_ID_ENV,
    NXAPI_CLIENT_SECRET_ENV,
    NXAPI_CLIENT_SECRET_ENV_ALIASES,
    NXAPI_CLIENT_VERSION_ENV,
    NXAPI_DEFAULT_AUTH_SCOPE,
    NXAPI_DEFAULT_CLIENT_VERSION,
    NXAPI_SCOPE_ENV,
    NXAPI_USER_AGENT_ENV,
    TOKENS,
)

logger = logging.getLogger(__name__)


def _get_env_with_aliases(
    key: str, *aliases: str, default: str | None = None
) -> str | None:
    value = os.getenv(key)
    if value:
        return value

    for alias in aliases:
        alias_value = os.getenv(alias)
        if alias_value:
            return alias_value

    return default


class TokenManagerConstructor:
    """This class is used to construct a ``TokenManager`` object. This class
    should only contain static methods that are used to construct the
    ``TokenManager`` object.
    """

    @staticmethod
    def from_session_token(
        session_token: str,
        *,
        nso: NSO | None = None,
        f_token_url: str | list[str] = DEFAULT_F_TOKEN_URL,
        app_version: str | None = None,
    ) -> TokenManager:
        """Creates a ``TokenManager`` object from a session token. This method
        is the bare minimum needed to create a ``TokenManager`` object.

        Args:
            session_token (str): The session token to use.
            nso (NSO | None): An instance of the ``NSO`` class. If one is not
                provided, a new instance will be created. Defaults to None.
            f_token_url (str | list[str] | None): The URL(s) to use to generate
                tokens. If a list is provided, each URL will be tried in order
                until a token is successfully generated. If None is provided,
                the default NXAPI URL will be used. Defaults to None.
            app_version (str | None): Optional override for the NSO app version
                used during authentication.

        Returns:
            TokenManager: The ``TokenManager`` object.
        """
        if nso is None:
            nso = NSO.new_instance()
        nso.set_app_version_override(app_version)
        nso._session_token = session_token
        manager = TokenManager(
            nso=nso,
            f_token_url=f_token_url,
            origin="memory",
        )
        manager.add_token(session_token, TOKENS.SESSION_TOKEN)
        return manager

    @staticmethod
    def from_tokens(
        session_token: str,
        gtoken: str | None = None,
        bullet_token: str | None = None,
        *,
        nso: NSO | None = None,
        f_token_url: str | list[str] = DEFAULT_F_TOKEN_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        app_version: str | None = None,
    ) -> TokenManager:
        """Creates a ``TokenManager`` object from a session token and other
        tokens. This method is the bare minimum needed to create a
        ``TokenManager`` object.

        Args:
            session_token (str): The session token to use.
            gtoken (str | None): The gtoken to use. If None is provided, a new
                gtoken will be generated.
            bullet_token (str | None): The bullet token to use. If None is
                provided, a new bullet token will be generated.
            nso (NSO | None): An instance of the ``NSO`` class. If one is not
                provided, a new instance will be created. Defaults to None.
            f_token_url (str | list[str] | None): The URL(s) to use to generate
                tokens. If a list is provided, each URL will be tried in order
                until a token is successfully generated. If None is provided,
                the default NXAPI URL will be used. Defaults to None.
            user_agent (str): The user agent to use when generating the bullet
                token. Defaults to DEFAULT_USER_AGENT.
            app_version (str | None): Optional override for the NSO app version
                used during token regeneration.

        Returns:
            TokenManager: The ``TokenManager`` object.
        """
        manager = TokenManagerConstructor.from_session_token(
            session_token,
            nso=nso,
            f_token_url=f_token_url,
            app_version=app_version,
        )
        if gtoken is None:
            gtoken = TokenRegenerator.generate_gtoken(
                manager.nso, manager.f_token_url
            ).value
        manager.add_token(gtoken, TOKENS.GTOKEN)

        if bullet_token is None:
            bullet_token = TokenRegenerator.generate_bullet_token(
                manager.nso, manager.f_token_url, user_agent=user_agent
            ).value
        manager.add_token(bullet_token, TOKENS.BULLET_TOKEN)
        manager.mark_tokens_fresh()
        return manager

    @staticmethod
    def from_env(
        env_manager: EnvironmentVariablesManager | None = None,
        *,
        nso: NSO | None = None,
        f_token_url: str | list[str] = DEFAULT_F_TOKEN_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        app_version: str | None = None,
    ) -> TokenManager:
        """Loads tokens from environment variables.

        This method will create a token manager and add the tokens found in the
        environment variables to it. The environment variables that are
        supported are:

        - SN3S_SESSION_TOKEN
        - SN3S_GTOKEN
        - SN3S_BULLET_TOKEN

        The session token environment variable is required, and if it is not
        set, a ValueError will be raised. The other environment variables are
        optional and will be generated if they are not set.

        Tests the tokens before returning the token manager using the
        ``test_tokens`` method.

        Args:
            env_manager (EnvironmentVariablesManager): The environment variables
                manager to use. If not provided, a new one will be created.
                Defaults to None.
            nso (NSO | None): An instance of the ``NSO`` class. If one is not
                provided, a new instance will be created. Defaults to None.
            f_token_url (str | list[str] | None): The URL(s) to use to generate
                tokens. If a list is provided, each URL will be tried in order
                until a token is successfully generated. If None is provided,
                the default NXAPI URL will be used. Defaults to None.
            user_agent (str): The user agent to use when generating the bullet
                token. Defaults to DEFAULT_USER_AGENT.
            app_version (str | None): Optional override for the NSO app version
                used when regenerating tokens.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        env_manager = env_manager or EnvironmentVariablesManager()
        tokens = env_manager.get_all()
        if app_version is None:
            app_version = os.getenv(APP_VERSION_OVERRIDE_ENV)
        manager = TokenManagerConstructor.from_tokens(
            session_token=cast(str, tokens[TOKENS.SESSION_TOKEN]),
            gtoken=tokens.get(TOKENS.GTOKEN, None),
            bullet_token=tokens.get(TOKENS.BULLET_TOKEN, None),
            nso=nso,
            f_token_url=f_token_url,
            user_agent=user_agent,
            app_version=app_version,
        )
        TokenManagerConstructor._configure_nxapi_from_env(manager)
        manager.flag_origin("env")
        return manager

    @staticmethod
    def _configure_nxapi_from_env(manager: TokenManager) -> None:
        client_id = os.getenv(NXAPI_CLIENT_ID_ENV)
        if not client_id:
            if manager.uses_nxapi_provider():
                raise FTokenException(
                    "NXAPI client id is required when using the default ftoken "
                    "provider. Set NXAPI_ZNCA_API_CLIENT_ID or override "
                    "f_token_url."
                )
            return

        manager.configure_nxapi(
            token_url=os.getenv(NXAPI_AUTH_TOKEN_URL_ENV, NXAPI_AUTH_TOKEN_URL),
            scope=os.getenv(NXAPI_SCOPE_ENV, NXAPI_DEFAULT_AUTH_SCOPE),
            client_id=client_id,
            client_secret=_get_env_with_aliases(
                NXAPI_CLIENT_SECRET_ENV,
                *NXAPI_CLIENT_SECRET_ENV_ALIASES,
            ),
            client_assertion=os.getenv(NXAPI_CLIENT_ASSERTION_ENV),
            client_assertion_private_key_path=os.getenv(
                NXAPI_CLIENT_ASSERTION_PRIVATE_KEY_PATH_ENV
            ),
            client_assertion_jku=os.getenv(NXAPI_CLIENT_ASSERTION_JKU_ENV),
            client_assertion_kid=os.getenv(NXAPI_CLIENT_ASSERTION_KID_ENV),
            client_assertion_type=os.getenv(NXAPI_CLIENT_ASSERTION_TYPE_ENV),
            user_agent=os.getenv(NXAPI_USER_AGENT_ENV),
            client_version=os.getenv(
                NXAPI_CLIENT_VERSION_ENV,
                NXAPI_DEFAULT_CLIENT_VERSION,
            ),
        )
