from unittest.mock import mock_open, patch

import pytest
import pytest_mock
import requests

from splatnet3_scraper.scraper.config import Config
from splatnet3_scraper.scraper.main import SplatNet3_Scraper
from tests.mock import MockConfig, MockResponse

config_path = "splatnet3_scraper.scraper.config.Config"


class TestSplatNet3Scraper:
    def test_from_config_file(
        self, monkeypatch: pytest.MonkeyPatch, mocker: pytest_mock.MockerFixture
    ):

        # No config file
        with (
            monkeypatch.context() as m,
            patch(config_path + ".__init__") as mock_config,
        ):
            m.setattr(SplatNet3_Scraper, "__init__", lambda x, y: None)
            mock_config.return_value = None
            SplatNet3_Scraper.from_config_file()
            mock_config.assert_called_once()

        # Config file
        with (
            monkeypatch.context() as m,
            patch(config_path + ".__init__") as mock_config,
        ):
            m.setattr(SplatNet3_Scraper, "__init__", lambda x, y: None)
            mock_config.return_value = None
            SplatNet3_Scraper.from_config_file("test_config_path")
            mock_config.assert_called_once_with("test_config_path")
