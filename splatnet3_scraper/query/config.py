import configparser
from typing import Literal, overload

from splatnet3_scraper.auth import (
    EnvironmentVariablesManager,
    Token,
    TokenManager,
)
from splatnet3_scraper.constants import DEFAULT_USER_AGENT, IMINK_URL


class Config:
    """Class that can access the token manager as well as additional options."""

    def __init__(
        self,
        config_path: str | None = None,
        *args,
        token_manager: TokenManager | None = None,
    ) -> None:
        """Initializes the class. If token_manager is given, it will assume that
        this is a first time initialization and has not been setup yet.

        Token manager will look for tokens in the following order:
            1. the config_path argument
            2. check the current working directory for ".splatnet3_scraper"
            3. check for environment variables for defined tokens
            4. check the current working directory for "tokens.ini"

        If none of these are found, an exception will be raised.

        Args:
            config_path (str | None): The path to the config file. If None, it
                will look for ".splatnet3_scraper" in the current working
                directory. Defaults to None.
            *args: These are ignored.
            token_manager (TokenManager | None): The token manager to use.
                Keyword argument. If given, it will skip the post-init method.
                Defaults to None.
        """
        self.additional_accepted_options: list[str] = []
        self.additional_deprecated_options: dict[str, str] = {}
        self.additional_default_options: dict[str, str] = {}

        if token_manager is None:
            self.generate_token_manager(config_path)
            return
        else:
            self.config_path = config_path

        self.token_manager = token_manager
        self.initialize_options()

    def generate_token_manager(self, config_path: str | None = None) -> None:
        """Generates the token manager.

        Will only be called if the token manager is not given in the constructor
        or if the ``token_manager`` argument in the constructor is None. This
        means that the user prefers to use the default loading method for the
        token manager, which is to look for tokens in the following order:

            1. the config_path argument
            2. check the current working directory for ".splatnet3_scraper"
            3. check for environment variables for defined tokens
            4. check the current working directory for "tokens.ini"

        If none of these are found, an exception will be raised.

        Args:
            config_path (str | None): The path to the config file. If None, it
                will look for ".splatnet3_scraper" in the current working
                directory.
        """
        if config_path is not None:
            self.token_manager = TokenManager.from_config_file(config_path)
        # cgarza: A little bit of redundancy here, need better method.
        else:
            self.token_manager = TokenManager.load()

        config_path = (
            ".splatnet3_scraper" if config_path is None else config_path
        )

        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        try:
            self.options = self.config.options("options")
        except configparser.NoSectionError:
            self.config.add_section("options")
            self.options = self.config.options("options")
        self.manage_options()

        with open(config_path, "w") as configfile:
            self.config.write(configfile)

    def initialize_options(self) -> None:
        if getattr(self, "config", None) is not None:
            return

        origin = self.token_manager.origin
        self.config = configparser.ConfigParser()
        self.config.add_section("options")
        self.options = self.config.options("options")

        if origin["origin"] == "env":
            # If the tokens are in environment variables, we should check for
            # any additional tokens in the token's environment manager and add
            # them to the config variable under the "options" section.
            tokens = self.token_manager.env_manager.get_all()
            for token, value in tokens.items():
                if token in self.token_manager.env_manager.BASE_TOKENS:
                    continue
                if value is None:
                    continue
                self.config["options"][token] = value

            return

    @classmethod
    def from_env(
        cls, env_manager: EnvironmentVariablesManager | None = None
    ) -> "Config":
        """Creates a Config instance using the environment variables.

        Args:
            env_manager (EnvironmentVariablesManager | None): The environment
                variables manager to use. If None, it will create a new one.
                Defaults to None.

        Returns:
            Config: The Config instance.
        """
        return cls(token_manager=TokenManager.from_env(env_manager))

    @classmethod
    def from_s3s_config(cls, config_path: str) -> "Config":
        """Creates a Config instance using the config file from s3s.

        Args:
            config_path (str): The path to the config file.

        Returns:
            Config: The Config instance.
        """
        return cls(token_manager=TokenManager.from_text_file(config_path))

    def save(
        self, path: str | None = None, include_tokens: bool = True
    ) -> None:
        """Saves the config file to the given path.

        Args:
            path (str | None): The path to save the config file to. If the token
                manager is using environment variables, the tokens section will
                be removed from the config file. If None, it will save to the
                path given in the constructor or ".splatnet3_scraper" in the
                current working directory.
            include_tokens (bool): Whether or not to include the tokens in the
                config file. If False, the tokens will be removed from the
                config file.
        """
        # Check if the user has the tokens in a separate file
        origin = self.token_manager._origin["origin"]
        if (origin == "env") or (not include_tokens):
            # Remove the token manager from the config file
            self.config.remove_section("tokens")
        if path is None and self.config_path is not None:
            path = self.config_path
        elif path is None:
            path = ".splatnet3_scraper"

        with open(path, "w") as configfile:
            self.config.write(configfile)

    def manage_options(self) -> None:
        """Manage the options in the config file.

        This function will move invalid options to the "unknown" section and
        move deprecated options to the "deprecated" section while replacing them
        with the new option name.
        """
        for option in self.options:
            if option not in (
                self.ACCEPTED_OPTIONS + list(self.DEPRECATED_OPTIONS.keys())
            ):
                if not self.config.has_section("unknown"):
                    self.config.add_section("unknown")
                self.config["unknown"][option] = self.config["options"][option]
                self.config.remove_option("options", option)
            if option in self.DEPRECATED_OPTIONS:
                deprecated_name = option
                option_name = self.DEPRECATED_OPTIONS[option]
                if not self.config.has_section("deprecated"):
                    self.config.add_section("deprecated")
                # Make a copy of the deprecated option in the deprecated section
                # and then replace the deprecated option with the new option
                self.config["deprecated"][deprecated_name] = self.config[
                    "options"
                ][deprecated_name]
                self.config["options"][option_name] = self.config["options"][
                    deprecated_name
                ]
                self.config.remove_option("options", option)

    _ACCEPTED_OPTIONS = [
        "user_agent",
        "log_level",
        "log_file",
        "export_path",
        "language",
        "lang",
        "country",
        "stat.ink_api_token",
        "stat_ink_api_token",
        "statink_api_token",
        "f_token_url",
    ]

    _DEPRECATED_OPTIONS = {
        "api_key": "stat.ink_api_token",
        "f_gen": "f_token_url",
    }

    _DEFAULT_OPTIONS = {
        "user_agent": DEFAULT_USER_AGENT,
        "f_gen": IMINK_URL,
        "export_path": "",
    }

    @property
    def ACCEPTED_OPTIONS(self) -> list[str]:
        return self._ACCEPTED_OPTIONS + self.additional_accepted_options

    @property
    def DEPRECATED_OPTIONS(self) -> dict[str, str]:
        return {
            **self._DEPRECATED_OPTIONS,
            **self.additional_deprecated_options,
        }

    @property
    def DEFAULT_OPTIONS(self) -> dict[str, str]:
        return {**self._DEFAULT_OPTIONS, **self.additional_default_options}

    def get(self, key: str) -> str:
        """Get the value of an option. If the option is not set, the default
        value will be returned.

        Args:
            key (str): The name of the option.

        Raises:
            KeyError: If the option is valid, but not set and has no default.
            KeyError: If the option is not valid.

        Returns:
            str: The value of the option.
        """
        if key in self.ACCEPTED_OPTIONS:
            if key in self.config["options"]:
                return self.config["options"][key]
            elif key in self.DEFAULT_OPTIONS:
                return self.DEFAULT_OPTIONS[key]
            else:
                raise KeyError(f"Option not set and has no default: {key}")
        elif key in self.DEPRECATED_OPTIONS:
            return self.get(self.DEPRECATED_OPTIONS[key])
        else:
            raise KeyError(f"Invalid option: {key}")

    def get_data(self, key: str) -> str:
        if not self.config.has_section("data"):
            self.config.add_section("data")
            data = self.token_manager.data
            for k, v in data.items():
                self.config["data"][k] = v
        return self.config["data"][key]

    @overload
    def get_token(self, key: str, full_token: Literal[False] = ...) -> str:
        ...

    @overload
    def get_token(self, key: str, full_token: Literal[True]) -> Token:
        ...

    @overload
    def get_token(self, key: str, full_token: bool) -> str | Token:
        ...

    def get_token(self, key: str, full_token: bool = False) -> str | Token:
        """Get the value of a token.

        Args:
            key (str): The name of the token.
            full_token (bool): Whether or not to return the full token. If
                False, only the token value will be returned.

        Returns:
            str: The value of the token.
        """
        return self.token_manager.get(key, full_token)

    def add_accepted_options(self, options: list[str]) -> None:
        """Add options to the list of accepted options.

        Args:
            options (list[str]): The list of options to add.
        """
        self.additional_accepted_options.extend(options)

    def add_deprecated_options(self, options: dict[str, str]) -> None:
        """Add options to the list of deprecated options.

        Args:
            options (dict[str, str]): The list of options to add.
        """
        self.additional_deprecated_options.update(options)

    def add_default_options(self, options: dict[str, str]) -> None:
        """Add options to the list of default options.

        Args:
            options (dict[str, str]): The list of options to add.
        """
        self.additional_default_options.update(options)

    def remove_accepted_options(self, options: list[str]) -> None:
        """Remove options from the list of accepted options.

        Args:
            options (list[str]): The list of options to remove.
        """
        for option in options:
            if option in self.additional_accepted_options:
                self.additional_accepted_options.remove(option)
            else:
                self._ACCEPTED_OPTIONS.remove(option)

    def remove_deprecated_options(self, options: list[str]) -> None:
        """Remove options from the list of deprecated options.

        Args:
            options (list[str]): The list of options to remove.
        """
        for option in options:
            if option in self.additional_deprecated_options:
                self.additional_deprecated_options.pop(option)
            else:
                self._DEPRECATED_OPTIONS.pop(option)

    def remove_default_options(self, options: list[str]) -> None:
        """Remove options from the list of default options.

        Args:
            options (list[str]): The list of options to remove.
        """
        for option in options:
            if option in self.additional_default_options:
                self.additional_default_options.pop(option)
            else:
                self._DEFAULT_OPTIONS.pop(option)
