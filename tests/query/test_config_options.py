from splatnet3_scraper.query.config_options import ConfigOptions


class TestConfigOptions:
    add_accepted_options = [
        "test1",
        "test2",
    ]

    add_deprecated_options = {
        "test1": "test2",
        "test3": "test4",
    }

    add_default_options = {
        "test10": "test20",
        "test30": "test40",
    }

    def test_init(self) -> None:
        config_options = ConfigOptions()
        assert config_options.additional_accepted_options == []
        assert config_options.additional_deprecated_options == {}
        assert config_options.additional_default_options == {}

    def test_add_accepted_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_accepted_options(self.add_accepted_options)
        assert (
            config_options.additional_accepted_options
            == self.add_accepted_options
        )

    def test_add_deprecated_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_deprecated_options({**self.add_deprecated_options})
        assert (
            config_options.additional_deprecated_options
            == self.add_deprecated_options
        )

    def test_add_default_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_default_options({**self.add_default_options})
        assert (
            config_options.additional_default_options
            == self.add_default_options
        )

    def test_remove_accepted_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_accepted_options(self.add_accepted_options)
        config_options.remove_accepted_options(["test1"])
        assert config_options.additional_accepted_options == ["test2"]
        config_options.remove_accepted_options(["test2"])
        assert config_options.additional_accepted_options == []

    def test_remove_deperecated_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_deprecated_options({**self.add_deprecated_options})
        config_options.remove_deprecated_options(["test1"])
        assert config_options.additional_deprecated_options == {
            "test3": "test4"
        }
        config_options.remove_deprecated_options(["test3"])
        assert config_options.additional_deprecated_options == {}

    def test_remove_default_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_default_options({**self.add_default_options})
        config_options.remove_default_options(["test10"])
        assert config_options.additional_default_options == {"test30": "test40"}
        config_options.remove_default_options(["test30"])
        assert config_options.additional_default_options == {}

    def test_accepted_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_accepted_options(self.add_accepted_options)
        assert config_options.ACCEPTED_OPTIONS == (
            config_options._ACCEPTED_OPTIONS + self.add_accepted_options
        )

    def test_deprecated_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_deprecated_options({**self.add_deprecated_options})
        assert config_options.DEPRECATED_OPTIONS == {
            **config_options._DEPRECATED_OPTIONS,
            **self.add_deprecated_options,
        }

    def test_default_options(self) -> None:
        config_options = ConfigOptions()
        config_options.add_default_options({**self.add_default_options})
        assert config_options.DEFAULT_OPTIONS == {
            **config_options._DEFAULT_OPTIONS,
            **self.add_default_options,
        }
