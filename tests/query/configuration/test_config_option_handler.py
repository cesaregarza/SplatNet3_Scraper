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
