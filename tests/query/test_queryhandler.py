from unittest.mock import MagicMock, patch

import pytest

from splatnet3_scraper.auth.exceptions import SplatNetException
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.query.handler import QueryHandler
from splatnet3_scraper.query.responses import QueryResponse
from tests.mock import MockConfig, MockNSO, MockResponse, MockTokenManager

base_handler_path = "splatnet3_scraper.query.handler"
config_path = base_handler_path + ".Config"
handler_path = base_handler_path + ".QueryHandler"
queries_path = base_handler_path + ".queries"
query_response_path = base_handler_path + ".QueryResponse"


class TestSplatNetQueryHandler:
    def test_init(self) -> None:
        config = MagicMock()
        handler = QueryHandler(config)
        assert handler.config == config

    def test_from_config_file(self) -> None:
        config = MagicMock()
        prefix = MagicMock()
        with patch(config_path) as mock_config:
            mock_config.from_file.return_value = config
            handler = QueryHandler.from_config_file("test", prefix=prefix)
            mock_config.from_file.assert_called_once_with("test", prefix=prefix)
            assert handler.config == config

    def test_from_tokens(self) -> None:
        config = MagicMock()
        session_token = MagicMock()
        gtoken = MagicMock()
        bullet_token = MagicMock()
        prefix = MagicMock()

        with patch(config_path) as mock_config:
            mock_config.from_tokens.return_value = config
            handler = QueryHandler.from_tokens(
                session_token,
                gtoken=gtoken,
                bullet_token=bullet_token,
                prefix=prefix,
            )
            mock_config.from_tokens.assert_called_once_with(
                session_token=session_token,
                gtoken=gtoken,
                bullet_token=bullet_token,
                prefix=prefix,
            )
            assert handler.config == config

    def test_from_session_token(self) -> None:
        config = MagicMock()
        session_token = MagicMock()
        prefix = MagicMock()

        with patch(config_path) as mock_config:
            mock_config.from_tokens.return_value = config
            handler = QueryHandler.from_session_token(
                session_token,
                prefix=prefix,
            )
            mock_config.from_tokens.assert_called_once_with(
                session_token=session_token,
                prefix=prefix,
            )
            config.regenerate_tokens.assert_called_once_with()
            assert handler.config == config

    def test_new_instance(self) -> None:
        config = MagicMock()
        prefix = MagicMock()

        with patch(config_path) as mock_config:
            mock_config.from_empty_handler.return_value = config
            handler = QueryHandler.new_instance(prefix=prefix)
            mock_config.from_empty_handler.assert_called_once_with(
                prefix=prefix
            )
            assert handler.config == config

    def test_from_s3s_config(self) -> None:
        config = MagicMock()
        prefix = MagicMock()
        with patch(config_path) as mock_config:
            mock_config.from_s3s_config.return_value = config
            handler = QueryHandler.from_s3s_config("test", prefix=prefix)
            mock_config.from_s3s_config.assert_called_once_with(
                "test", prefix=prefix
            )
            assert handler.config == config

    @pytest.mark.parametrize(
        "language",
        [
            "en-US",
            None,
        ],
        ids=[
            "with_language",
            "without_language",
        ],
    )
    def test_raw_query(self, language: str | None) -> None:
        config = MagicMock()
        expected_return = MagicMock()
        variables = MagicMock()
        handler = QueryHandler(config)
        getvalue_return = config.get_value.return_value

        with patch(queries_path) as mock_queries:
            mock_queries.query.return_value = expected_return
            ret = handler.raw_query(
                "test", language=language, variables=variables
            )
            mock_queries.query.assert_called_once_with(
                "test",
                getvalue_return,
                getvalue_return,
                language or getvalue_return,
                getvalue_return,
                variables=variables,
            )
            assert ret == expected_return

    @pytest.mark.parametrize(
        "language",
        [
            "en-US",
            None,
        ],
        ids=[
            "with_language",
            "without_language",
        ],
    )
    def test_raw_query_hash(self, language: str | None) -> None:
        config = MagicMock()
        expected_return = MagicMock()
        variables = MagicMock()
        handler = QueryHandler(config)
        getvalue_return = config.get_value.return_value

        with patch(queries_path) as mock_queries:
            mock_queries.query_hash.return_value = expected_return
            ret = handler.raw_query_hash(
                "test", language=language, variables=variables
            )
            mock_queries.query_hash.assert_called_once_with(
                "test",
                getvalue_return,
                getvalue_return,
                language or getvalue_return,
                getvalue_return,
                variables=variables,
            )
            assert ret == expected_return

    @pytest.mark.parametrize(
        "response",
        [
            "200",
            "200 with error",
            "400",
        ],
        ids=[
            "Valid",
            "Valid with error",
            "Invalid",
        ],
    )
    def test_query_hash(self, response: str) -> None:
        config = MagicMock()
        language = MagicMock()
        variables = MagicMock()
        invalid_response = MagicMock()
        valid_response = MagicMock()
        invalid_response.status_code = 400
        valid_response.status_code = 200
        if response in ("200", "400"):
            valid_response.json.return_value = {"data": {"test": "test"}}
        else:
            valid_response.json.return_value = {"errors": ["test"]}

        counter = 1 if response == "400" else 0
        total_counter = counter + 1

        def raw_query_hash(*args, **kwargs):
            nonlocal counter
            if counter == 0:
                return valid_response
            else:
                counter -= 1
                return invalid_response

        with (
            patch(handler_path + ".raw_query_hash") as mock_raw_query_hash,
            patch(base_handler_path + ".json") as mock_json,
            patch(query_response_path) as mock_query_response,
        ):
            mock_raw_query_hash.side_effect = raw_query_hash
            handler = QueryHandler(config)
            mock_json.dumps.return_value = "test"
            if response == "200 with error":
                with pytest.raises(
                    SplatNetException,
                    match=(
                        "Query was successful but returned at least one error. "
                        "Errors: test"
                    ),
                ):
                    handler.query_hash("test")
                return

            ret = handler.query_hash(
                "test", language=language, variables=variables
            )
            mock_query_response.assert_called_once_with(data={"test": "test"})
            assert ret == mock_query_response.return_value
            if response == "200":
                mock_raw_query_hash.assert_called_once_with(
                    "test", language, variables
                )
                config.regenerate_tokens.assert_not_called()
            else:
                assert mock_raw_query_hash.call_count == 2
                config.regenerate_tokens.assert_called_once_with()
