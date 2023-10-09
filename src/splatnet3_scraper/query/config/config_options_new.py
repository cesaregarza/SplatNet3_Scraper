from __future__ import annotations

from typing import Callable

from splatnet3_scraper.constants import (
    DEFAULT_F_TOKEN_URL,
    DEFAULT_USER_AGENT,
    TOKENS,
)
from splatnet3_scraper.query.config.callbacks import (
    log_level_callback,
    session_token_callback,
)


class ConfigOption:
    """Represents a configuration option with associated attributes.

    This class is used to represent a configuration option. It contains
    attributes for the option's name, default value, deprecated names, and
    callback function. The callback function is called whenever the option's
    value is set and is passed the new value as an argument. It should not
    return anything.
    """

    def __init__(
        self,
        name: str,
        default: str | None = None,
        deprecated_names: list[str] | str | None = None,
        deprecated_section: str | None = None,
        callback: Callable[[str | None], None] | None = None,
        section: str = "Options",
    ) -> None:
        """Initializes the class.

        Args:
            name (str): The name of the option.
            default (str | None): The default value of the option. If None, the
                option does not have a default value. Defaults to None.
            deprecated_names (list[str] | str | None): The deprecated names of
                the option. If None, the option does not have any deprecated
                names. If a string is provided, it will be converted to a list
                with one element. These names will be used to look up the
                option, but the new name will be used for any output. Defaults
                to None.
            deprecated_section (str | None): The deprecated section of the
                option. This should be used if the option was moved to a
                different section. If None, the option will be assumed to be in
                the same section. Defaults to None.
            callback (Callable[[str  |  None], None] | None): The callback
                function to call when the option's value is set. It should take
                one argument, the new value, and return nothing. Defaults to
                None.
            section (str): The section of the option. Defaults to "Options".
        """
        self.name = name
        self.default = default
        self.deprecated_names = deprecated_names
        self.deprecated_section = deprecated_section
        self.callback = callback
        self.section = section
        self.value: str | None = None

    def set_value(self, value: str | None) -> None:
        """Sets the value of the option. If a callback function is set, it will
        be called with the new value as an argument BEFORE the value is set.

        Args:
            value (str | None): The new value of the option.
        """
        if self.callback is not None:
            self.callback(value)
        self.value = value or self.default

    def get_value(self) -> str | None:
        """Gets the value of the option. If the value is not set and there is no
        default value, a ValueError will be raised.

        Raises:
            ValueError: If the value is not set and there is no default value.

        Returns:
            str | None: The value of the option.
        """
        if self.value is not None:
            return self.value
        elif self.default is not None:
            return self.default
        else:
            raise ValueError("No value set for option")


class ConfigOptions:
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
        ),
        ConfigOption(
            name=TOKENS.GTOKEN,
            default=None,
            section="Tokens",
        ),
        ConfigOption(
            name=TOKENS.BULLET_TOKEN,
            default=None,
            section="Tokens",
        ),
        ConfigOption(
            name="user_agent",
            default=DEFAULT_USER_AGENT,
            section="Options",
        ),
        ConfigOption(
            name="f_token_url",
            default=DEFAULT_F_TOKEN_URL,
            section="Options",
            deprecated_names=["f_gen", "ftoken_url"],
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
        ),
        ConfigOption(
            name="country",
            default="US",
            section="Options",
        ),
        ConfigOption(
            "log_level",
            default="INFO",
            section="Logging",
            callback=log_level_callback,
        ),
        ConfigOption(
            "log_file",
            default=None,
            section="Logging",
        ),
    )

    _ADDITIONAL_OPTIONS: list[ConfigOption]

    def __init__(self) -> None:
        """Initializes the class.

        This method initializes the class and sets up the additional options
        attribute. It also builds the option reference dictionary.
        """
        self._ADDITIONAL_OPTIONS = []
        self.option_reference = self.build_option_reference()

    def build_option_reference(self) -> dict[str, ConfigOption]:
        """Builds the option reference dictionary.

        This method builds the option reference dictionary. It maps the option
        names to the option objects. It also maps any deprecated names to the
        option objects.

        Returns:
            dict[str, ConfigOption]: The option reference dictionary.
        """
        reference = {option.name: option for option in self.OPTIONS}
        deprecated_reference = {
            deprecated_name: option
            for option in self.OPTIONS
            for deprecated_name in (option.deprecated_names or [])
        }
        return {**reference, **deprecated_reference}

    @property
    def OPTIONS(self) -> list[ConfigOption]:
        """The list of options.

        Returns the list of set options as well as any additional options that
        have been added.

        Returns:
            list[ConfigOption]: The list of options.
        """
        return self._OPTIONS + self._ADDITIONAL_OPTIONS

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
        if isinstance(options, ConfigOption):
            options = [options]
        self._ADDITIONAL_OPTIONS.extend(options)

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
            raise ValueError(f"Option {name} is not supported.")

    def get_value(self, name: str) -> str | None:
        """Gets the value of an option.

        Args:
            name (str): The name of the option to get.

        Returns:
            str | None: The value of the option.
        """
        return self.get_option(name).get_value()

    def get_section(self, section: str) -> list[ConfigOption]:
        """Gets all the options in a section.

        Args:
            section (str): The section to get the options from.

        Returns:
            list[ConfigOption]: The list of options in the section.
        """
        return [option for option in self.OPTIONS if option.section == section]
