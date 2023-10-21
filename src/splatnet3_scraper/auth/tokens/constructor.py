import logging
from typing import cast

from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.auth.tokens.environment_manager import (
    EnvironmentVariablesManager,
)
from splatnet3_scraper.auth.tokens.manager import TokenManager
from splatnet3_scraper.auth.tokens.regenerator import TokenRegenerator
from splatnet3_scraper.constants import (
    DEFAULT_F_TOKEN_URL,
    DEFAULT_USER_AGENT,
    TOKENS,
)

logger = logging.getLogger(__name__)


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
                the default URL provided by imink will be used. Defaults to
                None.

        Returns:
            TokenManager: The ``TokenManager`` object.
        """
        if nso is None:
            nso = NSO.new_instance()
            nso._session_token = session_token
        else:
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
                the default URL provided by imink will be used. Defaults to
                None.
            user_agent (str): The user agent to use when generating the bullet
                token. Defaults to DEFAULT_USER_AGENT.

        Returns:
            TokenManager: The ``TokenManager`` object.
        """
        manager = TokenManagerConstructor.from_session_token(
            session_token, nso=nso, f_token_url=f_token_url
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
        return manager

    @staticmethod
    def from_env(
        env_manager: EnvironmentVariablesManager | None = None,
        *,
        nso: NSO | None = None,
        f_token_url: str | list[str] = DEFAULT_F_TOKEN_URL,
        user_agent: str = DEFAULT_USER_AGENT,
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
                the default URL provided by imink will be used. Defaults to
                None.
            user_agent (str): The user agent to use when generating the bullet
                token. Defaults to DEFAULT_USER_AGENT.

        Returns:
            TokenManager: The token manager with the tokens loaded.
        """
        env_manager = env_manager or EnvironmentVariablesManager()
        tokens = env_manager.get_all()
        manager = TokenManagerConstructor.from_tokens(
            session_token=cast(str, tokens[TOKENS.SESSION_TOKEN]),
            gtoken=tokens.get(TOKENS.GTOKEN, None),
            bullet_token=tokens.get(TOKENS.BULLET_TOKEN, None),
            nso=nso,
            f_token_url=f_token_url,
            user_agent=user_agent,
        )
        manager.flag_origin("env")
        return manager
