from typing import Callable
from unittest.mock import MagicMock, patch

import pytest

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
            patch(handler_path + "._OPTIONS", new=options),
            patch(handler_path + ".build_option_reference"),
            patch(handler_path + ".assign_prefix_to_options"),
        ):
            handler = ConfigOptionHandler()
            handler._ADDITIONAL_OPTIONS = add_options
            assert handler.OPTIONS == list(options) + add_options

    def test_SUPPORTED_OPTIONS(self) -> None:
        option_reference = {
            f"test_{i}": MagicMock(name=f"test_{i}") for i in range(10)
        }
        handler = ConfigOptionHandler()
        handler.option_reference = option_reference
        assert handler.SUPPORTED_OPTIONS == list(option_reference.keys())