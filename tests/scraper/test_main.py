from unittest.mock import mock_open, patch

import pytest
import pytest_mock
import requests

from splatnet3_scraper.base.tokens import TokenManager
from splatnet3_scraper.scraper.config import Config
from splatnet3_scraper.scraper.main import SplatNet3_Scraper, QueryMap
from tests.mock import MockConfig, MockResponse, MockTokenManager

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

    def test__get_query(self):

        scraper = SplatNet3_Scraper(MockConfig())

        # 200 response
        with patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get:
            json = {"data": {"test_key": "test_value"}}
            mock_get.return_value = MockResponse(200, json=json)
            assert (
                scraper._SplatNet3_Scraper__get_query("test_url")
                == json["data"]
            )
            mock_get.assert_called_once_with("test_url")

        # Not 200 response
        with (
            patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(404)
            with pytest.raises(KeyError):
                scraper._SplatNet3_Scraper__get_query("test_url")
            assert mock_get.call_count == 2
            mock_generate.assert_called_once()

    def test__get_detailed_query(self):
        scraper = SplatNet3_Scraper(MockConfig())

        # versus True 200 response
        with patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get:
            json = {"data": {"test_key": "test_value"}}
            mock_get.return_value = MockResponse(200, json=json)
            assert (
                scraper._SplatNet3_Scraper__get_detailed_query("test_game_id")
                == json["data"]
            )
            expected_variables = {"vsResultId": "test_game_id"}
            mock_get.assert_called_once_with(
                QueryMap.VS_DETAIL, variables=expected_variables
            )

        # versus True not 200 response
        with (
            patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(404)
            with pytest.raises(KeyError):
                scraper._SplatNet3_Scraper__get_detailed_query("test_game_id")
            assert mock_get.call_count == 2
            expected_variables = {"vsResultId": "test_game_id"}
            mock_get.assert_called_with(
                QueryMap.VS_DETAIL, variables=expected_variables
            )
            mock_generate.assert_called_once()

        # versus False 200 response
        with patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get:
            json = {"data": {"test_key": "test_value"}}
            mock_get.return_value = MockResponse(200, json=json)
            assert (
                scraper._SplatNet3_Scraper__get_detailed_query(
                    "test_game_id", versus=False
                )
                == json["data"]
            )
            expected_variables = {"coopHistoryDetailId": "test_game_id"}
            mock_get.assert_called_once_with(
                QueryMap.SALMON_DETAIL, variables=expected_variables
            )

        # versus False not 200 response
        with (
            patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(404)
            with pytest.raises(KeyError):
                scraper._SplatNet3_Scraper__get_detailed_query(
                    "test_game_id", versus=False
                )
            assert mock_get.call_count == 2
            expected_variables = {"coopHistoryDetailId": "test_game_id"}
            mock_get.assert_called_with(
                QueryMap.SALMON_DETAIL, variables=expected_variables
            )
            mock_generate.assert_called_once()
