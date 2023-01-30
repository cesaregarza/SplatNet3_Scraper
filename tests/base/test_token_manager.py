import pathlib
import time
from unittest.mock import mock_open, patch

import freezegun
import pytest
import pytest_mock
import requests

from splatnet3_scraper.base.graph_ql_queries import GraphQLQueries
from splatnet3_scraper.base.tokens.nso import (
    NSO,
    NintendoException,
    SplatnetException,
)
from splatnet3_scraper.base.tokens.token_manager import Token, TokenManager
from tests.mock import MockNSO


@freezegun.freeze_time("2023-01-01 00:00:00")
def mock_token(token_type):
    return Token(token_type, token_type, time.time())


base_path = pathlib.Path(__file__).parent.parent / "fixtures" / "config_files"
token_manager_path = "splatnet3_scraper.base.tokens.token_manager.TokenManager"


class TestToken:
    @freezegun.freeze_time("2023-01-01 00:00:00")
    def test_new_token(self):
        timestamp = time.time()
        token = Token("test", "test_type", timestamp)
        assert token.token == "test"
        assert token.token_type == "test_type"
        assert token.timestamp == timestamp
        assert token.expiration == timestamp + 1e10

    @freezegun.freeze_time("2023-01-01 00:00:00")
    def test_properties(self):
        token = mock_token("test")
        assert token.is_expired is False
        assert token.is_valid is True
        assert token.time_left == 1e10
        assert token.time_left_str == "basically forever"

        token = mock_token("gtoken")
        assert token.time_left_str == "6h 30m"

    @freezegun.freeze_time("2023-01-01 00:00:00")
    def test_repr(self):
        token = mock_token("test")
        spaces = " " * len("Token(")
        expected = (
            "Token("
            + "token=test...,\n"
            + spaces
            + "type=test,\n"
            + spaces
            + "expires in basically forever"
            + "\n)"
        )
        assert repr(token) == expected


class TestTokenManager:
    def test_init(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)

        # Test init without arguments to ensure NSO is mocked
        token_manager = TokenManager()
        assert token_manager.nso._mocked is True

        # Test init with NSO, ensuring it is set correctly
        mock_nso = MockNSO()
        mock_nso.value = "test"
        token_manager = TokenManager(mock_nso)
        assert token_manager.nso.value == "test"

    def test_add_token(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)
        token_manager = TokenManager()

        # Test adding a token
        with freezegun.freeze_time("2023-01-01 00:00:00") as frozen_time:
            token_manager.add_token("test_token", "test_type")
            assert isinstance(token_manager._tokens["test_type"], Token)
            assert token_manager._tokens["test_type"].token == "test_token"
            assert token_manager._tokens["test_type"].token_type == "test_type"
            assert token_manager._tokens["test_type"].timestamp == time.time()

        # Test adding a token with a timestamp
        with freezegun.freeze_time("2023-01-01 00:00:00") as frozen_time:
            token_manager.add_token("test_token", "test_type", timestamp=123)
            assert isinstance(token_manager._tokens["test_type"], Token)
            assert token_manager._tokens["test_type"].token == "test_token"
            assert token_manager._tokens["test_type"].token_type == "test_type"
            assert token_manager._tokens["test_type"].timestamp == 123

        # Test adding a Token object
        with freezegun.freeze_time("2023-01-01 00:00:00") as frozen_time:
            token = Token("test_token", "test_type", time.time())
            token_manager.add_token(token)
            assert isinstance(token_manager._tokens["test_type"], Token)
            assert token_manager._tokens["test_type"].token == "test_token"

        # Test adding a token string without a type
        with pytest.raises(ValueError):
            token_manager.add_token("test_token")

    def test_get(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)
        token_manager = TokenManager()

        # Test getting a token that doesn't exist
        with pytest.raises(ValueError):
            token_manager.get("test_type")

        # Test getting a token that does exist
        token_manager.add_token("test_token", "test_type")
        assert token_manager.get("test_type") == "test_token"

        # Test getting full object
        token = token_manager.get("test_type", full_token=True)
        assert isinstance(token, Token)

    def test_data(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)
        token_manager = TokenManager()

        # Test getting data when no tokens exist
        assert token_manager.data == {}

        # Test getting data when tokens exist
        token_manager._data = {"test": "test"}
        assert token_manager.data == {"test": "test"}

    def test_add_session_token(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)
        token_manager = TokenManager()

        # Test adding a session token
        assert token_manager.nso._session_token is None
        token_manager.add_session_token("test_session_token")
        assert token_manager.nso._session_token == "test_session_token"

    def test_generate_gtoken(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)
        token_manager = TokenManager()

        # Test generating a gtoken without a session token
        with pytest.raises(ValueError):
            token_manager.generate_gtoken()

        token_manager.add_session_token("test_session_token")
        token_manager.generate_gtoken()
        expected_user_info = {
            "country": "test_country",
            "language": "test_language",
        }
        assert token_manager.data == expected_user_info
        assert "gtoken" in token_manager._tokens

    def test_generate_bullet_token(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)
        token_manager = TokenManager()

        # Test generating a bullet token without a session token
        with pytest.raises(ValueError):
            token_manager.generate_bullet_token()

        # Test generating a bullet token without a gtoken
        token_manager.add_session_token("test_session_token")
        assert "gtoken" not in token_manager._tokens
        token_manager.generate_bullet_token()
        assert "gtoken" in token_manager._tokens
        assert "bullet_token" in token_manager._tokens

        # Test invalid gtoken returned
        token_manager = TokenManager()
        token_manager.add_session_token("test_session_token")
        token_manager.nso._invalid_tokens = ["gtoken"]
        with pytest.raises(NintendoException):
            token_manager.generate_bullet_token()

        # Test valid gtoken, invalid bullet token
        token_manager = TokenManager()
        token_manager.add_session_token("test_session_token")
        token_manager.nso._invalid_tokens = ["bullet_token"]
        with pytest.raises(SplatnetException):
            token_manager.generate_bullet_token()

    def test_generate_all_tokens(self, monkeypatch: pytest.MonkeyPatch):
        counter = 0

        def mock_generate_token(*args, **kwargs):
            nonlocal counter
            counter += 1

        monkeypatch.setattr(
            TokenManager, "generate_gtoken", mock_generate_token
        )
        monkeypatch.setattr(
            TokenManager, "generate_bullet_token", mock_generate_token
        )

        token_manager = TokenManager()
        token_manager.generate_all_tokens()
        assert counter == 2

    def test_from_session_token(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)
        token_manager = TokenManager.from_session_token("test_session_token")
        assert token_manager.nso._session_token == "test_session_token"
        expected_origin = {"origin": "session_token", "data": None}
        assert token_manager._origin == expected_origin

    def test_from_config_file(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)
        counter = 0

        def mock_test_tokens(*args, **kwargs):
            return True

        def mock_generate_all_tokens(*args, **kwargs):
            nonlocal counter
            counter += 1

        monkeypatch.setattr(TokenManager, "test_tokens", mock_test_tokens)
        monkeypatch.setattr(
            TokenManager, "generate_all_tokens", mock_generate_all_tokens
        )

        # Test with no config file
        with pytest.raises(ValueError):
            TokenManager.from_config_file(".nonexistent")

        # Test with a valid config file
        path = str(base_path / ".valid")
        token_manager = TokenManager.from_config_file(path)
        assert token_manager.nso._session_token == "test_session_token"
        assert token_manager.nso._gtoken == "test_gtoken"
        assert token_manager.get("session_token") == "test_session_token"
        assert token_manager.get("gtoken") == "test_gtoken"
        assert token_manager.get("bullet_token") == "test_bullet_token"

        expected_data = {
            "country": "US",
            "language": "en-US",
        }
        assert token_manager.data == expected_data
        expected_origin = {
            "origin": "config_file",
            "data": path,
        }
        assert token_manager._origin == expected_origin

        # Test with a config file without a tokens section
        path = str(base_path / ".no_tokens_section")
        with pytest.raises(ValueError):
            TokenManager.from_config_file(path)

        # Test with a config without data
        path = str(base_path / ".no_data")
        token_manager = TokenManager.from_config_file(path)
        assert counter == 1

        # Test config with extra tokens
        path = str(base_path / ".extra_tokens")
        token_manager = TokenManager.from_config_file(path)
        assert token_manager.get("extra_token") == "test_extra_token"

    @pytest.mark.xfail
    def test_from_text_file(self, monkeypatch: pytest.MonkeyPatch):
        raise NotImplementedError

    def test_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)

        def mock_test_tokens(*args, **kwargs):
            return True

        monkeypatch.setattr(TokenManager, "test_tokens", mock_test_tokens)

        # Test with no environment variables
        with pytest.raises(ValueError):
            TokenManager.from_env()

        # Test with only session token
        monkeypatch.setenv("SN3S_SESSION_TOKEN", "test_session_token")
        token_manager = TokenManager.from_env()

        assert token_manager.nso._session_token == "test_session_token"
        assert token_manager.get("session_token") == "test_session_token"
        expected_origin = {"origin": "env", "data": None}
        assert token_manager._origin == expected_origin

        # Test with all environment variables
        monkeypatch.setenv("SN3S_GTOKEN", "test_gtoken")
        monkeypatch.setenv("SN3S_BULLET_TOKEN", "test_bullet_token")

        token_manager = TokenManager.from_env()
        assert token_manager.get("gtoken") == "test_gtoken"
        assert token_manager.get("bullet_token") == "test_bullet_token"

    def test_load(
        self, monkeypatch: pytest.MonkeyPatch, mocker: pytest_mock.MockFixture
    ):
        # No config files at all
        with monkeypatch.context() as m:
            m.setattr("os.path.exists", lambda x: False)
            with pytest.raises(ValueError):
                TokenManager.load()

        # Only "tokens.ini"
        with monkeypatch.context() as m:
            m.setattr("os.path.exists", lambda x: x == "tokens.ini")
            m.setattr(TokenManager, "from_config_file", lambda x: "config_file")
            assert TokenManager.load() == "config_file"

        # "tokens.ini" and environment variables (env takes precedence)
        with monkeypatch.context() as m:
            m.setattr("os.path.exists", lambda x: x == "tokens.ini")
            m.setattr(TokenManager, "from_config_file", lambda x: "config_file")
            m.setattr(TokenManager, "from_env", lambda: "env")
            m.setenv("SN3S_SESSION_TOKEN", "test_session_token")
            assert TokenManager.load() == "env"

        # "tokens.ini", environment variables, and ".splatnet3_scraper"
        # (.splatnet3_scraper takes precedence)
        with (
            monkeypatch.context() as m,
            patch(
                token_manager_path + ".from_config_file"
            ) as mock_from_config_file,
        ):

            def path_exists(path):
                return path in ("tokens.ini", ".splatnet3_scraper")

            m.setattr("os.path.exists", path_exists)
            m.setattr(TokenManager, "from_env", lambda: "env")
            m.setenv("SN3S_SESSION_TOKEN", "test_session_token")
            TokenManager.load()
            mock_from_config_file.assert_called_once_with(".splatnet3_scraper")

    def test_save(
        self, monkeypatch: pytest.MonkeyPatch, mocker: pytest_mock.MockFixture
    ):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)

        def mock_test_tokens(*args, **kwargs):
            return True

        monkeypatch.setattr(TokenManager, "test_tokens", mock_test_tokens)
        path = str(base_path / ".valid")
        out_path = str(base_path / ".out")
        token_manager = TokenManager.from_config_file(path)
        # mock ConfigParser.write
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("configparser.ConfigParser.write") as mock_write,
        ):
            token_manager.save(out_path)
            mock_file.assert_called_once_with(out_path, "w")

            mock_write.assert_called_once_with(mock_file.return_value)

    def test_token_is_valid(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)

        token_manager = TokenManager()
        assert token_manager.token_is_valid("session_token") is False
        token_manager.add_session_token("test_session_token")
        assert token_manager.token_is_valid("session_token") is True

    def test_test_tokens(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(NSO, "new_instance", MockNSO.new_instance)

        # Despite the seemingly high complexity of this function, it is easy
        # to test by letting the other functions do their job since they are
        # already tested. The only thing that needs to be tested is the unique
        # behavior of this function.
        token_manager = TokenManager()
        token_manager.add_session_token("test_session_token")
        token_manager.add_token("test_gtoken", "gtoken")
        token_manager.add_token("test_bullet_token", "bullet_token")
        token_manager._data = {"language": "test_language"}

        class MockResponse:
            def __init__(self, status_code):
                self.status_code = status_code

        def post_status_code(status_code):
            def mock_post(*args, **kwargs):
                return MockResponse(status_code)

            return mock_post

        def query_header(*args, **kwargs):
            return {}

        monkeypatch.setattr(GraphQLQueries, "query_header", query_header)

        # 200 status code
        with (
            patch(token_manager_path + ".generate_all_tokens") as mock_generate,
            monkeypatch.context() as m,
        ):
            m.setattr(requests, "post", post_status_code(200))
            token_manager.test_tokens()
            mock_generate.assert_not_called()

        # 400 status code
        with (
            patch(token_manager_path + ".generate_all_tokens") as mock_generate,
            monkeypatch.context() as m,
        ):
            m.setattr(requests, "post", post_status_code(400))
            token_manager.test_tokens()
            mock_generate.assert_called_once()
