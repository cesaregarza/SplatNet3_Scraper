from __future__ import annotations

import configparser
from typing import Literal, overload

from splatnet3_scraper.auth.tokens import (
    EnvironmentVariablesManager,
    Token,
    TokenManager,
    TokenManagerConstructor,
)
from splatnet3_scraper.query.configuration.config_option_handler import (
    ConfigOptionHandler,
)


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

    def __init__(
        self,
        *,
        token_manager: TokenManager | None = None,
        file_path: str | None = None,
        write_to_file: bool = False,
        prefix: str = "SN3S",
    ) -> None:
        self.config = configparser.ConfigParser()
        self._token_manager = token_manager
        self._file_path = file_path
        self._write_to_file = write_to_file
        self._prefix = prefix

        self.handler = ConfigOptionHandler(prefix=self._prefix)

        self.initialize()

    def initialize(self) -> None:
        """Initializes the class.

        Reads the ConfigParser object from the file and initializes the
        ``TokenManager`` object.
        """
        if self._file_path is not None:
            self.load_from_file(self._file_path)

        if self._token_manager is None:
            self._token_manager = self.initialize_token_manager()

    def load_from_file(self, file_path: str) -> None:
        """Loads the config from a file.

        Args:
            file_path (str): The path to the file to load the config from.
        """
        self.config.read(file_path)

    def initialize_token_manager(self) -> TokenManager:
        """Initializes and returns a ``TokenManager`` object from the set
        config attribute.

        Returns:
            TokenManager: The ``TokenManager`` object.
        """
        # The config object is already initialized, so we can just use it. The
        # tokens are stored in the "token" section of the config object.

        # Get the tokens from the "Tokens" section of the config file.
        tokens = self.config["Tokens"]
        session_token = tokens.get("session_token")
        gtoken = tokens.get("gtoken")
        bullet_token = tokens.get("bullet_token")

        # Load options from the "Options" section of the config file.
        try:
            options = self.config["Options"]
        except KeyError:
            options = None

        if options is not None:
            f_token_url = options.get("f_token_url")
            user_agent = options.get("user_agent")
            kwargs = {
                "f_token_url": f_token_url,
                "user_agent": user_agent,
            }
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
        else:
            kwargs = {}

        return TokenManagerConstructor.from_tokens(
            session_token=session_token,
            gtoken=gtoken,
            bullet_token=bullet_token,
            **kwargs,
        )

    def get_value(self, option: str) -> str | None:
        """Gets the value of the option.

        Args:
            option (str): The name of the option.

        Returns:
            str | None: The value of the option.
        """

    @staticmethod
    def from_file(
        file_path: str | None = None,
        *,
        write_to_file: bool = True,
    ) -> Config:
        """Creates a ``Config`` object from a file. This method is the most
        common way to create a ``Config`` object.

        Args:
            file_path (str | None): The path to the file to load the config
                from. If None is provided, the default file path will be used.
                Defaults to None.
            write_to_file (bool): Whether or not to write the config to the
                file. Defaults to True.

        Returns:
            Config: The ``Config`` object created from the file.
        """
        file_path = file_path or Config.DEFAULT_CONFIG_PATH
        return Config(
            file_path=file_path,
            write_to_file=write_to_file,
        )

    @property
    def token_manager(self) -> TokenManager:
        """Returns the ``TokenManager`` object.

        Acts as a TypeGuard for the ``_token_manager`` attribute, ensuring that
        a ``TokenManager`` object is always returned.

        Raises:
            ValueError: If the ``_token_manager`` attribute is None.

        Returns:
            TokenManager: The ``TokenManager`` object.
        """
        if self._token_manager is None:
            raise ValueError("Token manager not initialized")
        return self._token_manager
