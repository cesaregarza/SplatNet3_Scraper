import configparser

from s3s_express.constants import DEFAULT_USER_AGENT, IMINK_URL


class Config:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        try:
            self.options = self.config.options("options")
        except configparser.NoSectionError:
            self.config.add_section("options")
        self.manage_options()
        # save changes
        with open(config_path, "w") as configfile:
            self.config.write(configfile)

    def manage_options(self) -> None:
        """Manage the options in the config file.

        This function will move invalid options to the "unknown" section and
        move deprecated options to the "deprecated" section while replacing them
        with the new option name.
        """
        for option in self.options:
            if option not in self.ACCEPTED_OPTIONS:
                if not self.config.has_section("unknown"):
                    self.config.add_section("unknown")
                self.config["unknown"][option] = self.config["options"][option]
                self.config.remove_option("options", option)
                continue
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

    ACCEPTED_OPTIONS = [
        "user_agent",
        "log_level",
        "log_file",
        "export_path",
        "language",
        "lang",
        "country",
        "stat.ink_api_key",
        "stat_ink_api_key",
        "statink_api_key",
        "f_token_url",
    ]

    DEPRECATED_OPTIONS = {
        "api_key": "stat.ink_api_key",
        "f_gen": "f_token_url",
    }

    DEFAULT_OPTIONS = {
        "user_agent": DEFAULT_USER_AGENT,
        "f_gen": IMINK_URL,
        "export_path": "",
    }

    def get(self, key: str) -> str:
        """Get the value of an option. If the option is not set, the default
        value will be returned.

        Args:
            key (str): The name of the option.

        Returns:
            str: The value of the option.
        """
        if key in self.ACCEPTED_OPTIONS:
            if key in self.config["options"]:
                return self.config["options"][key]
            else:
                return self.DEFAULT_OPTIONS[key]
        else:
            raise KeyError(f"Invalid option: {key}")
