from __future__ import annotations

import configparser
import json
from typing import TypeVar, cast

from splatnet3_scraper.auth.tokens import TokenManager, TokenManagerConstructor
from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.config.config_option_handler import (
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

    @property
    def tokens(self) -> dict[str, str]:
        """The tokens.

        Returns:
            dict[str, str]: The tokens.
        """
        return {
            TOKENS.SESSION_TOKEN: self.session_token,
            TOKENS.GTOKEN: self.gtoken,
            TOKENS.BULLET_TOKEN: self.bullet_token,
        }

    def get_value(
        self, option: str, default: T | None = None
    ) -> str | T | None:
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

    def set_value(self, option: str, value: str | None) -> None:
        """Sets the value of the option.

        Args:
            option (str): The name of the option.
            value (str | None): The value to set the option to.
        """
        self.handler.set_value(option, value)
        if option in [
            TOKENS.SESSION_TOKEN,
            TOKENS.GTOKEN,
            TOKENS.BULLET_TOKEN,
        ]:
            if (token := self.handler.tokens[option]) is not None:
                self.token_manager.add_token(
                    token,
                    option,
                )

    @staticmethod
    def from_empty_handler(prefix: str = "") -> Config:
        """Creates a ``Config`` object from an empty ``ConfigOptionHandler``
        object. This is useful if you have environment variables set and want to
        create a ``Config`` object from them.

        Args:
            prefix (str): The prefix to use for the config options environment
                variables. Defaults to "SN3S".

        Returns:
            Config: The ``Config`` object.
        """
        prefix = prefix or Config.DEFAULT_PREFIX
        handler = ConfigOptionHandler(prefix=prefix)
        session_token = cast(str, handler.get_value(TOKENS.SESSION_TOKEN))
        gtoken = handler.get_value(TOKENS.GTOKEN)
        bullet_token = handler.get_value(TOKENS.BULLET_TOKEN)
        return Config.from_tokens(
            session_token=session_token,
            gtoken=gtoken,
            bullet_token=bullet_token,
            prefix=prefix,
        )

    @staticmethod
    def from_tokens(
        session_token: str,
        gtoken: str | None = None,
        bullet_token: str | None = None,
        *,
        prefix: str = "",
    ) -> Config:
        """Creates a ``Config`` object from a session token and other tokens.

        Args:
            session_token (str): The session token to use.
            gtoken (str | None): The gtoken to use. If None is provided, a new
                gtoken will be generated.
            bullet_token (str | None): The bullet token to use. If None is
                provided, a new bullet token will be generated.
            prefix (str): The prefix to use for the config options. Defaults to
                "SN3S".

        Returns:
            Config: The ``Config`` object.
        """
        token_manager = TokenManagerConstructor.from_tokens(
            session_token=session_token,
            gtoken=gtoken,
            bullet_token=bullet_token,
        )

        prefix = prefix or Config.DEFAULT_PREFIX
        handler = ConfigOptionHandler(prefix=prefix)
        handler.set_value(TOKENS.SESSION_TOKEN, session_token)
        handler.set_value(TOKENS.GTOKEN, gtoken)
        handler.set_value(TOKENS.BULLET_TOKEN, bullet_token)

        return Config(
            handler,
            token_manager=token_manager,
        )

    @staticmethod
    def from_config_handler(
        handler: ConfigOptionHandler,
        output_file_path: str | None = None,
    ) -> Config:
        """Creates a ``Config`` object from a ``ConfigOptionHandler`` object.

        Args:
            handler (ConfigOptionHandler): The ``ConfigOptionHandler`` object
                to create the ``Config`` object from.
            output_file_path (str | None): The path to the file to save the
                config to. Defaults to None.

        Raises:
            ValueError: If the session token is not provided.

        Returns:
            Config: The ``Config`` object created from the
                ``ConfigOptionHandler`` object.
        """
        session_token = handler.get_value(TOKENS.SESSION_TOKEN)
        gtoken = handler.get_value(TOKENS.GTOKEN)
        bullet_token = handler.get_value(TOKENS.BULLET_TOKEN)
        if session_token is None:
            raise ValueError("Session token not provided.")

        token_manager = TokenManagerConstructor.from_tokens(
            session_token=session_token,
            gtoken=gtoken,
            bullet_token=bullet_token,
        )

        return Config(
            handler,
            token_manager=token_manager,
            output_file_path=output_file_path,
        )

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
        return Config.from_config_handler(
            handler,
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

        return Config.from_config_handler(handler)

    def save_to_file(self, file_path: str | None = None) -> None:
        """Saves the config to a file.

        Args:
            file_path (str | None): The path to the file to save the config to.
                Defaults to None.

        Raises:
            ValueError: If no file path is provided and no output file path is
                set.
        """
        file_path = file_path or self._output_file_path
        if file_path is None:
            raise ValueError("No file path provided.")
        config = self.handler.save_to_configparser()
        with open(file_path, "w") as f:
            config.write(f)

    @staticmethod
    def from_s3s_config(
        path: str,
        *,
        prefix: str = "",
    ) -> Config:
        """Creates a ``Config`` object from an s3s config file. This method is
        useful if you already have an s3s config file and want to use it to
        create a ``Config`` object. It is not recommended to use this method if
        you can avoid it.

        Args:
            path (str): The path to the s3s config file.
            prefix (str): The prefix to use for the config options. Defaults to
                "SN3S".

        Returns:
            Config: The ``Config`` object created from the s3s config file.
        """
        prefix = prefix or Config.DEFAULT_PREFIX
        with open(path, "r") as f:
            data = json.load(f)

        if "acc_loc" in data:
            acc_loc: str = cast(str, data["acc_loc"])
            language, country = acc_loc.split("|")
            data["language"] = language
            data["country"] = country
            del data["acc_loc"]

        handler = ConfigOptionHandler(prefix=prefix)
        handler.read_from_dict(data)
        return Config.from_config_handler(handler, Config.DEFAULT_CONFIG_PATH)
