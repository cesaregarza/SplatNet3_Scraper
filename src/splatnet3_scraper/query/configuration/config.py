from __future__ import annotations

import configparser
from typing import TypeVar

from splatnet3_scraper.auth.tokens import TokenManager, TokenManagerConstructor
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.configuration.config_option_handler import (
    ConfigOptionHandler,
)

T = TypeVar("T")


class Config:
    """The Config class is used to load, store, and manage the configuration
    options for the QueryHandler class. The Config class has a number of static
    methods that are used to create a new instance of the class, including from
    a file, from a few default options, etc. The bulk of the configuration
    options are stored in a ConfigParser object for uniformity and ease of use.
    It also functions as a high-level wrapper around the ``TokenManager`` class
    that enables the ``QueryHandler`` class to be quickly and easily
    instantiated, leading to less time spent configuring the ``QueryHandler``
    class and more time spent making queries.
    """

    DEFAULT_CONFIG_PATH = ".splatnet3_scraper"
    DEFAULT_PREFIX = "SN3S"

    def __init__(
        self,
        handler: ConfigOptionHandler,
        *,
        token_manager: TokenManager | None = None,
        output_file_path: str | None = None,
    ) -> None:
        self._token_manager = token_manager
        self._output_file_path = output_file_path

        self.handler = handler

    @property
    def token_manager(self) -> TokenManager:
        """The ``TokenManager`` object used to manage the tokens. Acts as a
        TypeGuard for the ``_token_manager`` attribute.

        Raises:
            ValueError: If the token manager has not been initialized.

        Returns:
            TokenManager: The ``TokenManager`` object used to manage the tokens.
        """
        if self._token_manager is None:
            raise ValueError("Token manager not initialized.")
        return self._token_manager

    def regenerate_tokens(self) -> None:
        """Regenerates the tokens and updates the config."""
        self.token_manager.regenerate_tokens()
        # Add tokens to config
        for token in [
            TOKENS.SESSION_TOKEN,
            TOKENS.GTOKEN,
            TOKENS.BULLET_TOKEN,
        ]:
            self.handler.set_value(
                token,
                self.token_manager.get_token(token).value,
            )

    @property
    def session_token(self) -> str:
        """The session token.

        Returns:
            str: The session token.
        """
        return self.token_manager.get_token(TOKENS.SESSION_TOKEN).value

    @property
    def gtoken(self) -> str:
        """The gtoken.

        Returns:
            str: The gtoken.
        """
        return self.token_manager.get_token(TOKENS.GTOKEN).value

    @property
    def bullet_token(self) -> str:
        """The bullet token.

        Returns:
            str: The bullet token.
        """
        return self.token_manager.get_token(TOKENS.BULLET_TOKEN).value

    def get_value(self, option: str, default: T = None) -> str | T:
        """Gets the value of the option.

        Args:
            option (str): The name of the option.
            default (T): The default value to return if the option is not
                defined.

        Returns:
            str | T: The value of the option.
        """
        return_value = self.handler.get_value(option)
        if return_value is None:
            return default
        return return_value

    @staticmethod
    def from_file(
        file_path: str,
        save_to_file: bool = True,
        prefix: str = "",
    ) -> Config:
        """Creates a ``Config`` object from a file.

        Args:
            file_path (str): The path to the file to load the config from.
            save_to_file (bool): Whether or not to save the config to the file.
                Defaults to True.
            prefix (str): The prefix to use for the config options. Defaults to
                "SN3S".

        Returns:
            Config: The ``Config`` object created from the file.
        """
        prefix = prefix or Config.DEFAULT_PREFIX
        cparse = configparser.ConfigParser()
        cparse.read(file_path)
        handler = ConfigOptionHandler(prefix=prefix)
        handler.read_from_configparser(cparse)

        session_token = handler.get_value(TOKENS.SESSION_TOKEN)
        gtoken = handler.get_value(TOKENS.GTOKEN)
        bullet_token = handler.get_value(TOKENS.BULLET_TOKEN)
        token_manager = TokenManagerConstructor.from_tokens(
            session_token=session_token,
            gtoken=gtoken,
            bullet_token=bullet_token,
        )

        return Config(
            handler,
            token_manager=token_manager,
            output_file_path=file_path if save_to_file else None,
        )

    @staticmethod
    def from_dict(
        config: dict[str, str],
        prefix: str = "",
    ) -> Config:
        """Creates a ``Config`` object from a dictionary.

        Args:
            config (dict[str, str]): The dictionary to load the config from.
            prefix (str): The prefix to use for the config options. Defaults to
                "SN3S".

        Returns:
            Config: The ``Config`` object created from the dictionary.
        """
        prefix = prefix or Config.DEFAULT_PREFIX
        handler = ConfigOptionHandler(prefix=prefix)
        handler.read_from_dict(config)

        session_token = handler.get_value(TOKENS.SESSION_TOKEN)
        gtoken = handler.get_value(TOKENS.GTOKEN)
        bullet_token = handler.get_value(TOKENS.BULLET_TOKEN)
        token_manager = TokenManagerConstructor.from_tokens(
            session_token=session_token,
            gtoken=gtoken,
            bullet_token=bullet_token,
        )

        return Config(
            handler,
            token_manager=token_manager,
            output_file_path=None,
        )
