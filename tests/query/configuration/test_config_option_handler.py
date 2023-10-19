from unittest.mock import MagicMock, patch
import configparser

import pytest

from splatnet3_scraper.constants import TOKENS
from splatnet3_scraper.query.configuration.config_option import ConfigOption
from splatnet3_scraper.query.configuration.config_option_handler import (
    ConfigOptionHandler,
)

base_option_path = "splatnet3_scraper.query.configuration.config_option"
option_path = base_option_path + ".ConfigOption"
base_handler_path = (
    "splatnet3_scraper.query.configuration.config_option_handler"
)
handler_path = base_handler_path + ".ConfigOptionHandler"


class TestConfigOptionHandler:
    def test_init(self) -> None:
        mock_return = MagicMock()
        with patch(handler_path + ".build_option_reference") as mock_build:
            mock_build.return_value = mock_return
            handler = ConfigOptionHandler()
            mock_build.assert_called_once_with()
            assert handler._ADDITIONAL_OPTIONS == []
            assert handler.option_reference == mock_return
            assert handler.prefix is None
            for option in handler.OPTIONS:
                assert option.env_prefix is None

    def test_build_option_reference(self) -> None:
        num_options = 10
        num_deprecated = 5
        deprecated_nums = [0, 1, 2, 3, 4]
        count = 0

        # Generate options
        options = []
        for i in range(num_options):
            # First 5 options are deprecated
            if i >= num_deprecated:
                options.append(ConfigOption(name=f"test_{i}"))
            elif deprecated_nums[i] == 0:
                options.append(
                    ConfigOption(
                        name=f"test_{i}", deprecated_names="deprecated_0"
                    )
                )
                count += 1
            else:
                num_deprecated_names = deprecated_nums[i]
                lower = count
                upper = num_deprecated_names + lower

                deprecated_names = [
                    f"deprecated_{j}" for j in range(lower, upper)
                ]
                count += num_deprecated_names
                options.append(
                    ConfigOption(
                        name=f"test_{i}", deprecated_names=deprecated_names
                    )
                )

        with patch(handler_path + ".OPTIONS", new=options):
            handler = ConfigOptionHandler()
            option_reference = handler.build_option_reference()

        assert len(option_reference) == (num_options + sum(deprecated_nums) + 1)
        for i in range(num_options):
            assert f"test_{i}" in option_reference
            assert option_reference[f"test_{i}"].name == f"test_{i}"

        for i in range(sum(deprecated_nums)):
            assert f"deprecated_{i}" in option_reference

    def test_assign_prefix(self) -> None:
        prefix = "test"
        handler = ConfigOptionHandler()
        handler.assign_prefix_to_options(prefix)
        assert handler.prefix is None
        for option in handler.OPTIONS:
            assert option.env_prefix == prefix

    def test_OPTIONS(self) -> None:
        options = (1, 2, 3)
        add_options = [4, 5, 6]
        with (
            patch(handler_path + ".build_option_reference"),
            patch(handler_path + ".assign_prefix_to_options"),
        ):
            handler = ConfigOptionHandler()
            handler._OPTIONS = options
            handler._ADDITIONAL_OPTIONS = add_options
            assert handler.OPTIONS == list(options) + add_options

    def test_SUPPORTED_OPTIONS(self) -> None:
        option_reference = {
            f"test_{i}": MagicMock(name=f"test_{i}") for i in range(10)
        }
        handler = ConfigOptionHandler()
        handler.option_reference = option_reference
        assert handler.SUPPORTED_OPTIONS == list(option_reference.keys())

    def test_SECTIONS(self) -> None:
        breaks = [3, 3, 3]
        options = [
            MagicMock(section=f"section_{i}", name=f"test_{j}")
            for i, x in enumerate(breaks)
            for j in range(x)
        ]
        with patch(handler_path + ".OPTIONS", new=options):
            handler = ConfigOptionHandler()
            # SECTIONS can be in any order, so sort them
            assert sorted(handler.SECTIONS) == [
                f"section_{i}" for i in range(len(breaks))
            ]

    def test_tokens_property(self) -> None:
        def mock_get_value(self, name: str) -> str:
            if name == TOKENS.SESSION_TOKEN:
                return "session_token"
            elif name == TOKENS.GTOKEN:
                return "gtoken"
            elif name == TOKENS.BULLET_TOKEN:
                return "bullet_token"

        with patch(handler_path + ".get_value", new=mock_get_value) as mock_gv:
            tokens = ConfigOptionHandler().tokens
            assert tokens == {
                TOKENS.SESSION_TOKEN: "session_token",
                TOKENS.GTOKEN: "gtoken",
                TOKENS.BULLET_TOKEN: "bullet_token",
            }

    @pytest.mark.parametrize(
        "option_type",
        [
            "ConfigOption",
            "list",
        ],
        ids=[
            "ConfigOption",
            "list[ConfigOption]",
        ],
    )
    @pytest.mark.parametrize(
        "prefix",
        [
            "test",
            None,
        ],
        ids=[
            "prefix",
            "no prefix",
        ],
    )
    def test_add_options(self, option_type: str, prefix: str | None) -> None:
        option = MagicMock()
        if option_type == "list":
            option = [option]
            expected = option
        else:
            expected = [option]
        with (
            patch(handler_path + ".build_option_reference") as mock_build,
            patch(handler_path + ".assign_prefix_to_options") as mock_assign,
        ):
            handler = ConfigOptionHandler(prefix=prefix)
            mock_build.reset_mock()
            mock_assign.reset_mock()
            handler.add_options(option)
            assert handler._ADDITIONAL_OPTIONS == expected
            mock_build.assert_called_once_with()

            if prefix is not None:
                mock_assign.assert_called_once_with(prefix)
            else:
                mock_assign.assert_not_called()

    def test_get_option(self) -> None:
        test_option = MagicMock()
        option_reference = {
            "test": test_option,
        }
        handler = ConfigOptionHandler()
        handler.option_reference = option_reference
        assert handler.get_option("test") == test_option
        with pytest.raises(KeyError):
            handler.get_option("invalid")

    def test_get_value(self) -> None:
        test_option = MagicMock()
        test_option.get_value.return_value = "test"
        option_reference = {
            "test": test_option,
        }
        handler = ConfigOptionHandler()
        handler.option_reference = option_reference
        assert handler.get_value("test") == "test"

    def test_set_value(self) -> None:
        test_option = MagicMock()
        option_reference = {
            "test": test_option,
        }
        handler = ConfigOptionHandler()
        handler.option_reference = option_reference
        handler.set_value("test", "test")
        test_option.set_value.assert_called_once_with("test")

    def test_get_section(self) -> None:
        breaks = [3, 3, 3]
        options = [
            MagicMock(section=f"section_{i}", name=f"test_{j}")
            for i, x in enumerate(breaks)
            for j in range(x)
        ]
        with patch(handler_path + ".OPTIONS", new=options):
            handler = ConfigOptionHandler()
            assert handler.get_section("section_0") == options[:3]
            assert handler.get_section("section_1") == options[3:6]
            assert handler.get_section("section_2") == options[6:]

    def test_read_from_configparser(self) -> None:
        count = 0

        def mock_set_value(self, name: str) -> str:
            nonlocal count
            count += 1
            if count == 1:
                raise KeyError("test")
            return name

        mock_configp = MagicMock()
        mock_sections = [MagicMock()]
        mock_options = [MagicMock(), MagicMock(), MagicMock()]
        mock_configp.sections.return_value = mock_sections
        mock_configp.options.return_value = mock_options
        with patch(handler_path + ".set_value") as mock_set:
            mock_set.side_effect = mock_set_value
            handler = ConfigOptionHandler()
            handler.read_from_configparser(mock_configp)
            mock_configp.sections.assert_called_once_with()
            mock_configp.options.assert_called_once_with(mock_sections[0])
            assert mock_set.call_count == len(mock_options)
