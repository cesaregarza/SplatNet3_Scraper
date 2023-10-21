import logging

from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.auth.tokens.environment_manager import (
    EnvironmentVariablesManager,
)
from splatnet3_scraper.auth.tokens.keychain import TokenKeychain
from splatnet3_scraper.auth.tokens.regenerator import TokenRegenerator
from splatnet3_scraper.auth.tokens.token_typing import ORIGIN
from splatnet3_scraper.auth.tokens.tokens import Token
from splatnet3_scraper.constants import (
    DEFAULT_F_TOKEN_URL,
    DEFAULT_USER_AGENT,
    TOKENS,
)

logger = logging.getLogger(__name__)


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
                the default URL provided by imink will be used. Defaults to
                None.
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

    def generate_gtoken(self) -> None:
        """Generates a gtoken. This is done by calling the
        ``TokenRegenerator.generate_gtoken`` method. The token is then added to
        the keychain.
        """
        logger.info("Generating gtoken")
        token = TokenRegenerator.generate_gtoken(self.nso, self.f_token_url)
        self.add_token(token)

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
