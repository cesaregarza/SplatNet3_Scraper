import random
from unittest.mock import patch

import pytest
import pytest_mock

from splatnet3_scraper.auth.exceptions import SplatnetException
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.scraper.main import SplatNet3_Scraper
from splatnet3_scraper.scraper.query_map import QueryMap
from splatnet3_scraper.scraper.responses import QueryResponse
from tests.mock import MockConfig, MockNSO, MockResponse, MockTokenManager

config_path = "splatnet3_scraper.scraper.config.Config"
query_response_path = "splatnet3_scraper.scraper.responses.QueryResponse"
nso_path = "splatnet3_scraper.auth.nso.NSO"
token_manager_path = "splatnet3_scraper.auth.token_manager.TokenManager"


class TestQueryMap:
    def test_get(self):
        # Valid
        assert QueryMap.get("ANARCHY") == QueryMap.ANARCHY
        # lowercase
        assert QueryMap.get("anarchy") == QueryMap.ANARCHY
        # Invalid
        with pytest.raises(AttributeError):
            QueryMap.get("invalid")


class TestSplatNet3Scraper:
    def test_from_config_file(self, monkeypatch: pytest.MonkeyPatch):

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

    def test_generate_session_token_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)

        (
            url,
            state,
            verifier,
        ) = SplatNet3_Scraper.generate_session_token_url()
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
            SplatNet3_Scraper.from_session_token("test_token")
            mock_from_token.assert_called_once_with("test_token")
            mock_generate.assert_called_once()

    def test_from_env(self):
        with patch(config_path + ".from_env") as mock_from_env:
            mock_from_env.return_value = MockConfig()
            SplatNet3_Scraper.from_env()
            mock_from_env.assert_called_once()

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

    def test_get_mode_summary(self):
        scraper = SplatNet3_Scraper(MockConfig())

        # Invalid mode
        with pytest.raises(ValueError):
            scraper.get_mode_summary("invalid")

        # Valid mode, not detailed
        with (
            patch.object(scraper, "_SplatNet3_Scraper__get_query") as mock_get,
            patch(query_response_path + ".__init__") as mock_query_response,
        ):
            mock_query_response.return_value = None
            get_return_value = {"test_key": "test_value"}
            mock_get.return_value = get_return_value

            scraper.get_mode_summary("anarchy", detailed=False)
            mock_get.assert_called_once_with(QueryMap.get("anarchy"))
            mock_query_response.assert_called_once_with(data=get_return_value)

        # Valid mode, detailed
        with (
            patch.object(
                scraper, "_SplatNet3_Scraper__vs_with_details"
            ) as mock_get,
            patch(query_response_path + ".__init__") as mock_query_response,
        ):
            mock_query_response.return_value = None
            get_return_summary = {"test_key": "test_value"}
            get_return_detailed = []
            mock_get.return_value = (get_return_summary, get_return_detailed)

            scraper.get_mode_summary("anarchy", detailed=True)
            mock_get.assert_called_once_with(QueryMap.get("anarchy"), None)
            mock_query_response.assert_called_once_with(
                data=get_return_summary, additional_data=get_return_detailed
            )

    def test__vs_with_details(self):
        scraper = SplatNet3_Scraper(MockConfig())

        def generate_return_value(num_groups: int, num_per_group: int) -> dict:
            return {
                "results": {
                    "historyGroups": {
                        "nodes": [
                            {
                                "historyDetails": {
                                    "nodes": [
                                        {"id": f"test_id_{i}_{j}"}
                                        for j in range(num_per_group)
                                    ]
                                }
                            }
                            for i in range(num_groups)
                        ]
                    }
                }
            }

        # No limit
        with (
            patch.object(scraper, "_SplatNet3_Scraper__get_query") as mock_get,
            patch.object(
                scraper, "_SplatNet3_Scraper__get_detailed_query"
            ) as mock_get_detailed,
        ):
            num_groups = random.randint(3, 8)
            num_per_group = random.randint(10, 20)
            num_total = num_groups * num_per_group
            mock_get.return_value = generate_return_value(
                num_groups, num_per_group
            )
            mock_get_detailed.return_value = 0
            (
                query_result,
                game_details,
            ) = scraper._SplatNet3_Scraper__vs_with_details("anarchy")
            assert len(game_details) == num_total
            assert mock_get_detailed.call_count == num_total
            assert mock_get.call_count == 1
            assert query_result == mock_get.return_value

        # Limit
        with (
            patch.object(scraper, "_SplatNet3_Scraper__get_query") as mock_get,
            patch.object(
                scraper, "_SplatNet3_Scraper__get_detailed_query"
            ) as mock_get_detailed,
        ):
            num_groups = random.randint(3, 8)
            num_per_group = random.randint(10, 20)
            num_total = num_groups * num_per_group
            limit = random.randint(10, num_total)
            mock_get.return_value = generate_return_value(
                num_groups, num_per_group
            )
            mock_get_detailed.return_value = 0
            (
                query_result,
                game_details,
            ) = scraper._SplatNet3_Scraper__vs_with_details("anarchy", limit)
            assert len(game_details) == limit
            assert mock_get_detailed.call_count == limit
            assert mock_get.call_count == 1
            assert query_result == mock_get.return_value

    def test_query(self):
        scraper = SplatNet3_Scraper(MockConfig())
        mock_json = {"data": "test_data"}
        # 200 response
        with (
            patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get,
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
            patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get,
            patch.object(
                MockTokenManager, "generate_all_tokens"
            ) as mock_generate,
        ):
            mock_get.return_value = MockResponse(
                200, json={"errors": "test_error"}
            )
            with pytest.raises(SplatnetException):
                scraper.query("test_query")
            mock_get.assert_called_once_with("test_query", {})
            mock_generate.assert_not_called()

        # Not 200 response
        with (
            patch.object(scraper, "_SplatNet3_Scraper__query") as mock_get,
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
