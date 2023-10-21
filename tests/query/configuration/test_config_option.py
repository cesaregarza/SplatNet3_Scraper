from typing import Callable

import pytest

from splatnet3_scraper.query.config.config_option import ConfigOption


def callback(value: str | None) -> str | None:
    return value


def callback_add_one(value: str) -> str:
    return str(int(value) + 1)


class TestConfigOption:
    def test_option(self) -> None:

        option = ConfigOption(
            name="test",
            default=True,
            deprecated_names=["test2"],
            deprecated_section="test3",
            callback=callback,
            section="test4",
            env_var="test5",
            env_prefix="test6",
        )
        assert option.name == "test"
        assert option.default == True
        assert option.deprecated_names == ["test2"]
        assert option.deprecated_section == "test3"
        assert option.callback == callback
        assert option.section == "test4"
        assert option.env_var == "test5"
        assert option.env_prefix == "test6"
        assert option.value is None

    def test_env_key(self) -> None:
        option = ConfigOption(
            name="test",
            default=True,
            deprecated_names=["test2"],
            deprecated_section="test3",
            callback=None,
            section="test4",
            env_var="test5",
            env_prefix="test6",
        )
        assert option.env_key == "test6_test5"
        option.env_prefix = None
        assert option.env_key == "test5"
        option.env_var = None
        assert option.env_key is None

    @pytest.mark.parametrize(
        "callback",
        [
            None,
            callback_add_one,
            callback,
        ],
        ids=[
            "No callback",
            "With transform callback",
            "With callback",
        ],
    )
    @pytest.mark.parametrize(
        "value",
        [
            None,
            "1",
        ],
        ids=[
            "No value",
            "With value",
        ],
    )
    @pytest.mark.parametrize(
        "default",
        [
            None,
            "3",
        ],
        ids=[
            "No default",
            "With default",
        ],
    )
    def test_set_value(
        self,
        callback: Callable | None,
        value: str | None,
        default: str | None,
    ) -> None:
        option = ConfigOption(
            name="test",
            default=default,
            deprecated_names=["test2"],
            deprecated_section="test3",
            callback=callback,
            section="test4",
            env_var="test5",
            env_prefix="test6",
        )
        option.set_value(value)
        if callback is None:
            assert option.value == value or default
        elif value is None and default is None:
            assert option.value is None
        elif value is None:
            assert option.value == default
        else:
            assert option.value == callback(value) or default

    @pytest.mark.parametrize(
        "value",
        [
            None,
            "1",
        ],
        ids=[
            "No value",
            "With value",
        ],
    )
    @pytest.mark.parametrize(
        "default",
        [
            None,
            "3",
        ],
        ids=[
            "No default",
            "With default",
        ],
    )
    @pytest.mark.parametrize(
        "env_var",
        [
            None,
            "test",
        ],
        ids=[
            "No env var",
            "With env var",
        ],
    )
    def test_get_value(
        self,
        value: str | None,
        default: str | None,
        env_var: str | None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        option = ConfigOption(
            name="test",
            default=default,
            env_var="TEST_ENV_VAR",
        )
        if value is not None:
            option.set_value(value)

        with monkeypatch.context() as m:
            if env_var is not None:
                m.setenv("TEST_ENV_VAR", env_var)
            if (value is None) and (default is None) and (env_var is None):
                with pytest.raises(ValueError):
                    option.get_value()
                return

            return_value = option.get_value()
            if value is not None:
                assert return_value == value
            elif env_var is not None:
                assert return_value == env_var
                assert option.value == env_var
            else:
                assert return_value == default

    def test_set_prefix(self) -> None:
        option = ConfigOption(
            name="test",
            default=True,
            deprecated_names=["test2"],
            deprecated_section="test3",
            callback=callback,
            section="test4",
            env_var="test5",
            env_prefix="test6",
        )
        assert option.env_prefix == "test6"
        option.set_prefix("test7")
        assert option.env_prefix == "test7"
