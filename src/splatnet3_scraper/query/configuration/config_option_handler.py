from __future__ import annotations

from splatnet3_scraper.constants import (
    DEFAULT_F_TOKEN_URL,
    DEFAULT_USER_AGENT,
    TOKENS,
)
from splatnet3_scraper.query.configuration.callbacks import (
    f_token_url_callback,
    log_level_callback,
    session_token_callback,
)
from splatnet3_scraper.query.configuration.config_option import ConfigOption


class ConfigOptionHandler:
    """Manages a collection of configuration options.

    This class is used to manage a collection of configuration options. The
    ``_OPTIONS`` attribute contains essential options that are tightly coupled
    with the library. The ``_ADDITIONAL_OPTIONS`` attribute is used to store
    any additional attributes that the user may need. When first initialized,
    the class will create a reference dictionary that maps the option names to
    the option objects. This is used to look up options by name, including any
    deprecated names an option may have.
    """

    _OPTIONS = (
        ConfigOption(
            name=TOKENS.SESSION_TOKEN,
            default=None,
            callback=session_token_callback,
            section="Tokens",
            env_var="SESSION_TOKEN",
        ),
        ConfigOption(
            name=TOKENS.GTOKEN,
            default=None,
            section="Tokens",
            env_var="GTOKEN",
        ),
        ConfigOption(
            name=TOKENS.BULLET_TOKEN,
            default=None,
            section="Tokens",
            env_var="BULLET_TOKEN",
        ),
        ConfigOption(
            name="user_agent",
            default=DEFAULT_USER_AGENT,
            section="Options",
            env_var="SPLATNET3_USER_AGENT",
        ),
        ConfigOption(
            name="f_token_url",
            default=DEFAULT_F_TOKEN_URL,
            callback=f_token_url_callback,
            section="Options",
            deprecated_names=["f_gen", "ftoken_url"],
            env_var="F_TOKEN_URL",
        ),
        ConfigOption(
            name="export_path",
            default="",
            section="Options",
        ),
        ConfigOption(
            name="language",
            default="en-US",
            section="Options",
            env_var="SPLATNET3_LANGUAGE",
        ),
        ConfigOption(
            name="country",
            default="US",
            section="Options",
            env_var="SPLATNET3_COUNTRY",
        ),
        ConfigOption(
            "log_level",
            default="INFO",
            section="Logging",
            callback=log_level_callback,
            env_var="LOG_LEVEL",
        ),
        ConfigOption(
            "log_file",
            default=None,
            section="Logging",
            env_var="LOG_FILE",
        ),
    )

    def __init__(self, prefix: str | None = None) -> None:
        """Initializes the class.

        This method initializes the class and sets up the additional options
        attribute. It also builds the option reference dictionary.
        """
        self._ADDITIONAL_OPTIONS: list[ConfigOption] = []
        self.option_reference = self.build_option_reference()
        self.prefix = prefix
        if prefix is not None:
            self.assign_prefix_to_options(prefix)

    def build_option_reference(self) -> dict[str, ConfigOption]:
        """Builds the option reference dictionary.

        This method builds the option reference dictionary. It maps the option
        names to the option objects. It also maps any deprecated names to the
        option objects.

        Returns:
            dict[str, ConfigOption]: The option reference dictionary.
        """
        reference = {option.name: option for option in self.OPTIONS}
        deprecated_reference = {}
        for option in self.OPTIONS:
            if isinstance(option.deprecated_names, str):
                deprecated_reference[option.deprecated_names] = option
                continue
            for deprecated_name in option.deprecated_names or []:
                deprecated_reference[deprecated_name] = option
        return {**reference, **deprecated_reference}

    def assign_prefix_to_options(self, prefix: str) -> None:
        """Assigns a prefix to the options.

        Does NOT assign the prefix to the object itself.

        Args:
            prefix (str): The prefix to assign to the options.
        """
        for option in self.OPTIONS:
            option.set_prefix(prefix)

    @property
    def OPTIONS(self) -> list[ConfigOption]:
        """The list of options.

        Returns the list of set options as well as any additional options that
        have been added.

        Returns:
            list[ConfigOption]: The list of options.
        """
        return list(self._OPTIONS) + self._ADDITIONAL_OPTIONS

    @property
    def SUPPORTED_OPTIONS(self) -> list[str]:
        """The list of supported options.

        Returns the list of supported options as well as any additional options
        that have been added.

        Returns:
            list[str]: The list of supported options.
        """
        return list(self.option_reference.keys())

    @property
    def SECTIONS(self) -> list[str]:
        """The list of sections.

        Returns the list of sections that the options are in.

        Returns:
            list[str]: The list of sections.
        """
        return list(set(option.section for option in self.OPTIONS))

    def add_options(self, options: ConfigOption | list[ConfigOption]) -> None:
        """Add options to the list of additional options.

        Args:
            options (ConfigOption | list[ConfigOption]): The list of options to
                add.
        """
        if not isinstance(options, list):
            options = [options]
        self._ADDITIONAL_OPTIONS.extend(options)
        self.option_reference = self.build_option_reference()
        if self.prefix is not None:
            self.assign_prefix_to_options(self.prefix)

    def get_option(self, name: str) -> ConfigOption:
        """Gets an option from the option reference dictionary.

        Args:
            name (str): The name of the option to get.

        Raises:
            ValueError: If the option is not defined.

        Returns:
            ConfigOption: The option that was retrieved.
        """
        try:
            return self.option_reference[name]
        except KeyError:
            raise KeyError(f"Option {name} is not supported.")

    def get_value(self, name: str) -> str | None:
        """Gets the value of an option.

        Args:
            name (str): The name of the option to get.

        Returns:
            str | None: The value of the option.
        """
        return self.get_option(name).get_value()

    def set_value(self, name: str, value: str | None) -> None:
        """Sets the value of an option.

        Args:
            name (str): The name of the option to set.
            value (str | None): The value to set the option to.
        """
        self.get_option(name).set_value(value)

    def get_section(self, section: str) -> list[ConfigOption]:
        """Gets all the options in a section.

        Args:
            section (str): The section to get the options from.

        Returns:
            list[ConfigOption]: The list of options in the section.
        """
        return [option for option in self.OPTIONS if option.section == section]
