from splatnet3_scraper.constants import DEFAULT_USER_AGENT, IMINK_URL


class ConfigOptions:
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
        "ftoken_url": "f_token_url",
    }

    _DEFAULT_OPTIONS = {
        "user_agent": DEFAULT_USER_AGENT,
        "f_gen": IMINK_URL,
        "export_path": "",
        "language": "en-US",
        "country": "US",
    }

    def __init__(self) -> None:
        self.additional_accepted_options: list[str] = []
        self.additional_deprecated_options: dict[str, str] = {}
        self.additional_default_options: dict[str, str] = {}

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

    @property
    def SUPPORTED_OPTIONS(self) -> list[str]:
        return self.ACCEPTED_OPTIONS + list(self.DEPRECATED_OPTIONS.keys())

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
