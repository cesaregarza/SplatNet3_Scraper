import random
from unittest.mock import patch

import pytest
import pytest_mock

from splatnet3_scraper.auth.exceptions import SplatNetException
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.query.handler import SplatNet_QueryHandler
from splatnet3_scraper.query.responses import QueryResponse
from tests.mock import MockConfig, MockNSO, MockResponse, MockTokenManager

config_path = "splatnet3_scraper.query.config.Config"
query_response_path = "splatnet3_scraper.query.responses.QueryResponse"
nso_path = "splatnet3_scraper.auth.nso.NSO"
token_manager_path = "splatnet3_scraper.auth.token_manager.TokenManager"


class TestSplatNetQueryHandler:
    def test_from_config_file(self, monkeypatch: pytest.MonkeyPatch):

        # No config file
        with (
            monkeypatch.context() as m,
            patch(config_path + ".__init__") as mock_config,
        ):
            m.setattr(SplatNet_QueryHandler, "__init__", lambda x, y: None)
            mock_config.return_value = None
            SplatNet_QueryHandler.from_config_file()
            mock_config.assert_called_once()

        # Config file
        with (
            monkeypatch.context() as m,
            patch(config_path + ".__init__") as mock_config,
        ):
            m.setattr(SplatNet_QueryHandler, "__init__", lambda x, y: None)
            mock_config.return_value = None
            SplatNet_QueryHandler.from_config_file("test_config_path")
            mock_config.assert_called_once_with("test_config_path")

    def test_generate_session_token_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)

        (
            url,
            state,
            verifier,
        ) = SplatNet_QueryHandler.generate_session_token_url()
        assert url == "test_url"
        assert state == b"test_state"
        assert verifier == b"test_verifier"

    def test_from_session_token(self):
        with (
            patch(
                token_manager_path + ".from_session_token"
            ) as mock_from_token,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
            patch(config_path + ".__init__") as mock_config,
        ):
            mock_from_token.return_value = MockTokenManager()
            mock_config.return_value = None
            SplatNet_QueryHandler.from_session_token("test_token")
            mock_from_token.assert_called_once_with("test_token")
            mock_generate.assert_called_once()

    def test_from_env(self):
        with patch(config_path + ".from_env") as mock_from_env:
            mock_from_env.return_value = MockConfig()
            SplatNet_QueryHandler.from_env()
            mock_from_env.assert_called_once()

    def test_query(self):
        scraper = SplatNet_QueryHandler(MockConfig())
        mock_json = {"data": "test_data"}
        # 200 response
        with (
            patch.object(scraper, "_SplatNet_QueryHandler__query") as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(200, json=mock_json)
            assert scraper.query("test_query") == QueryResponse(
                mock_json["data"]
            )
            mock_get.assert_called_once_with("test_query", {})
            mock_generate.assert_not_called()

        # 200 response, with errors
        with (
            patch.object(scraper, "_SplatNet_QueryHandler__query") as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(
                200, json={"errors": "test_error"}
            )
            with pytest.raises(SplatNetException):
                scraper.query("test_query")
            mock_get.assert_called_once_with("test_query", {})
            mock_generate.assert_not_called()

        # Not 200 response
        with (
            patch.object(scraper, "_SplatNet_QueryHandler__query") as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(404, json=mock_json)
            assert scraper.query("test_query") == QueryResponse(
                mock_json["data"]
            )
            assert mock_get.call_count == 2
            mock_generate.assert_called_once()

    def test_query_hash(self):
        scraper = SplatNet_QueryHandler(MockConfig())
        mock_json = {"data": "test_data"}
        # 200 response
        with (
            patch.object(
                scraper, "_SplatNet_QueryHandler__query_hash"
            ) as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(200, json=mock_json)
            assert scraper.query_hash("test_query") == QueryResponse(
                mock_json["data"]
            )
            mock_get.assert_called_once_with("test_query", {})
            mock_generate.assert_not_called()

        # 200 response, with errors
        with (
            patch.object(
                scraper, "_SplatNet_QueryHandler__query_hash"
            ) as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(
                200, json={"errors": "test_error"}
            )
            with pytest.raises(SplatNetException):
                scraper.query_hash("test_query")
            mock_get.assert_called_once_with("test_query", {})
            mock_generate.assert_not_called()

        # Not 200 response
        with (
            patch.object(
                scraper, "_SplatNet_QueryHandler__query_hash"
            ) as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(404, json=mock_json)
            assert scraper.query_hash("test_query") == QueryResponse(
                mock_json["data"]
            )
            assert mock_get.call_count == 2
            mock_generate.assert_called_once()
