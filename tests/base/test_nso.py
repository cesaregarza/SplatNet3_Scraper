import hashlib
import os

import pytest
import requests

from splatnet3_scraper.base.tokens.nso import (
    NSO,
    FTokenException,
    NintendoException,
    SplatnetException,
)
from splatnet3_scraper.constants import APP_VERSION_FALLBACK
from tests.mock import MockResponse


class TestNSO:
    def get_new_nso(
        self,
        state: str | None = None,
        verifier: str | None = None,
        version: str | None = None,
        web_view_version: str | None = None,
        user_access_token: str | None = None,
        id_token: str | None = None,
        gtoken: str | None = None,
        user_info: dict | None = None,
    ) -> NSO:
        nso = NSO.new_instance()
        nso._state = state
        nso._verifier = verifier
        nso._version = version
        nso._web_view_version = web_view_version
        nso._user_access_token = user_access_token
        nso._id_token = id_token
        nso._gtoken = gtoken
        nso._user_info = user_info
        return nso

    def test_new_instance(self):
        nso = NSO.new_instance()

        nso_variables = nso.__dict__
        for key in nso_variables:
            if key == "session":
                assert isinstance(nso_variables[key], requests.Session)
            else:
                assert nso_variables[key] is None

    def test_generate_version(self, monkeypatch):
        test_string = 'whats-new__latest__version">Version    5.0.0</span>'

        def mock_get(*args, **kwargs):
            return MockResponse(200, text=test_string)

        monkeypatch.setattr(requests.Session, "get", mock_get)
        nso = NSO.new_instance()
        version = nso.get_version()
        assert version == "5.0.0"

        # Test fallback
        def mock_get(*args, **kwargs):
            return MockResponse(200, text="")

        monkeypatch.setattr(requests.Session, "get", mock_get)
        version = nso.get_version()
        assert version == APP_VERSION_FALLBACK

    def test_version_property(self, monkeypatch):
        test_string = 'whats-new__latest__version">Version    5.0.0</span>'

        def mock_get(*args, **kwargs):
            return MockResponse(200, text=test_string)

        monkeypatch.setattr(requests.Session, "get", mock_get)
        nso = NSO.new_instance()
        version = nso.version
        assert version == "5.0.0"
        assert nso._version == "5.0.0"

        # Test short circuit
        def mock_get(*args, **kwargs):
            raise Exception

        monkeypatch.setattr(requests.Session, "get", mock_get)
        version = nso.version
        assert version == "5.0.0"
        assert nso._version == "5.0.0"

    def test_generate_new_state(
        self,
        monkeypatch,
        urand36: bytes,
        urand36_expected: bytes,
    ):
        def mock_urandom(*args, **kwargs):
            return urand36

        monkeypatch.setattr(os, "urandom", mock_urandom)
        nso = NSO.new_instance()
        encoded_str = urand36_expected
        assert nso.generate_new_state() == encoded_str

    def test_state_property(
        self,
        monkeypatch,
        urand36: bytes,
        urand36_expected: bytes,
    ):
        def mock_urandom(*args, **kwargs):
            return urand36

        monkeypatch.setattr(os, "urandom", mock_urandom)
        nso = NSO.new_instance()
        assert nso._state is None
        encoded_str = urand36_expected
        assert nso.state == encoded_str
        assert nso._state == encoded_str

        # Test short circuit
        def mock_urandom(*args, **kwargs):
            raise Exception

        monkeypatch.setattr(os, "urandom", mock_urandom)
        assert nso.state == encoded_str
        assert nso._state == encoded_str

    def test_generate_new_verifier(
        self,
        monkeypatch,
        urand36: bytes,
        urand32_expected: bytes,
    ):
        def mock_urandom(*args, **kwargs):
            return urand36[:32]

        monkeypatch.setattr(os, "urandom", mock_urandom)
        nso = NSO.new_instance()
        encoded_str = urand32_expected
        assert nso.generate_new_verifier() == encoded_str
        assert b"=" not in encoded_str

    def test_verifier_property(
        self,
        monkeypatch,
        urand36: bytes,
        urand32_expected: bytes,
    ):
        def mock_urandom(*args, **kwargs):
            return urand36[:32]

        monkeypatch.setattr(os, "urandom", mock_urandom)
        nso = NSO.new_instance()
        assert nso._verifier is None
        encoded_str = urand32_expected
        assert nso.verifier == encoded_str
        assert nso._verifier == encoded_str

        # Test short circuit
        def mock_urandom(*args, **kwargs):
            raise Exception

        monkeypatch.setattr(os, "urandom", mock_urandom)
        assert nso.verifier == encoded_str
        assert nso._verifier == encoded_str

    def test_session_token(self):
        nso = NSO.new_instance()
        assert nso._session_token is None
        with pytest.raises(ValueError):
            nso.session_token

        nso._session_token = "test"
        assert nso.session_token == "test"

    def test_login_url(
        self,
        monkeypatch,
        urand36: bytes,
    ):
        def mock_generate_new_state(*args, **kwargs):
            return b"test_state"

        def mock_generate_new_verifier(*args, **kwargs):
            return b"test_verifier"

        class HashlibMock:
            def update(self, *args, **kwargs):
                pass

            def digest(self, *args, **kwargs):
                return urand36

        def mock_hashlib_sha256(*args, **kwargs):
            return HashlibMock()

        def mock_get(*args, **kwargs):
            return MockResponse(200, url="https://test.com/")

        monkeypatch.setattr(NSO, "generate_new_state", mock_generate_new_state)
        monkeypatch.setattr(
            NSO, "generate_new_verifier", mock_generate_new_verifier
        )
        monkeypatch.setattr(hashlib, "sha256", mock_hashlib_sha256)
        monkeypatch.setattr(requests.Session, "get", mock_get)
        nso = NSO.new_instance()
        assert nso.generate_login_url() == "https://test.com/"

    def test_get_session_token(self, monkeypatch):
        def mock_get(*args, **kwargs):
            return MockResponse(200, json={"session_token": "test"})

        monkeypatch.setattr(requests.Session, "post", mock_get)
        nso = self.get_new_nso(version="5.0.0", verifier="test_verifier")
        assert nso._session_token is None
        session_token = nso.get_session_token("session_code")
        assert session_token == "test"

    def test_get_user_access_token(self, monkeypatch):
        def mock_get(*args, **kwargs):
            return requests.Response()

        monkeypatch.setattr(requests.Session, "post", mock_get)
        nso = self.get_new_nso()

        access_token = nso.get_user_access_token("test")
        assert isinstance(access_token, requests.Response)

    def test_user_info(self, monkeypatch):
        def mock_get(*args, **kwargs):
            return MockResponse(200, json={"test": "test"})

        monkeypatch.setattr(requests.Session, "get", mock_get)
        nso = self.get_new_nso()
        user_info = nso.get_user_info("test")
        assert user_info == {"test": "test"}

    def test_get_ftoken(self, monkeypatch):
        def mock_post(*args, **kwargs):
            out_json = {
                "f": "test_f",
                "request_id": "test_request_id",
                "timestamp": "test_timestamp",
            }
            return MockResponse(200, json=out_json)

        nso = self.get_new_nso()
        monkeypatch.setattr(requests.Session, "post", mock_post)

        ftoken, request_id, timestamp = nso.get_ftoken("test", "test", "test")
        assert ftoken == "test_f"
        assert request_id == "test_request_id"
        assert timestamp == "test_timestamp"

        # Fail
        def mock_post(*args, **kwargs):
            return MockResponse(400, json={})

        monkeypatch.setattr(requests.Session, "post", mock_post)
        with pytest.raises(FTokenException):
            nso.get_ftoken("test", "test", "test")

    def test_get_splatoon_token(self, monkeypatch):
        def mock_post(*args, **kwargs):
            return MockResponse(200, json={})

        nso = self.get_new_nso(version="5.0.0")
        monkeypatch.setattr(requests.Session, "post", mock_post)

        splatoon_token = nso.get_splatoon_token({"parameter": {"f": "test"}})
        assert isinstance(splatoon_token, MockResponse)
        assert splatoon_token.json() == {}

    def test_f_token_generation_step_1(self, monkeypatch):
        user_access_response = MockResponse(200, json={"id_token": "id_token"})

        def mock_get_ftoken(*args, **kwargs):
            # Make sure it's using the correct hash method
            assert args[3] == 1
            return "f_token", "request_id", "timestamp"

        def generate_mock_get_splatoon_token(out_json):
            def mock_get_splatoon_token(self, body):
                assert "parameter" in body
                assert body["parameter"]["f"] == "f_token"
                assert body["parameter"]["language"] == "language"
                assert body["parameter"]["naBirthday"] == "birthday"
                assert body["parameter"]["naCountry"] == "country"
                assert body["parameter"]["naIdToken"] == "id_token"
                assert body["parameter"]["requestId"] == "request_id"
                assert body["parameter"]["timestamp"] == "timestamp"

                return MockResponse(200, json=out_json)

            return mock_get_splatoon_token

        valid_json = {
            "result": {
                "webApiServerCredential": {
                    "accessToken": "access_token",
                }
            }
        }
        mock_get_splatoon_token = generate_mock_get_splatoon_token(valid_json)
        monkeypatch.setattr(NSO, "get_ftoken", mock_get_ftoken)
        monkeypatch.setattr(NSO, "get_splatoon_token", mock_get_splatoon_token)

        nso = self.get_new_nso()

        user_info = {
            "language": "language",
            "birthday": "birthday",
            "country": "country",
        }

        ftoken = nso.f_token_generation_step_1(
            user_access_response, user_info, "test_url"
        )
        assert isinstance(ftoken, MockResponse)
        assert (
            ftoken.json()["result"]["webApiServerCredential"]["accessToken"]
            == "access_token"
        )

        # Fail
        invalid_json = {"result": {}}
        mock_get_splatoon_token = generate_mock_get_splatoon_token(invalid_json)
        monkeypatch.setattr(NSO, "get_splatoon_token", mock_get_splatoon_token)
        with pytest.raises(KeyError):
            nso.f_token_generation_step_1(
                user_access_response, user_info, "test_url"
            )

    def test_f_token_generation_step_2(self, monkeypatch):
        def mock_get_ftoken(*args, **kwargs):
            # Make sure it's using the correct hash method
            assert args[3] == 2
            return "f_token", "request_id", "timestamp"

        def mock_post(*args, **kwargs):
            # Make sure it's using the correct id
            assert kwargs["json"]["parameter"]["id"] == 4834290508791808
            out_json = {
                "result": {
                    "accessToken": "gtoken",
                }
            }
            return MockResponse(200, json=out_json)

        monkeypatch.setattr(NSO, "get_ftoken", mock_get_ftoken)
        monkeypatch.setattr(requests.Session, "post", mock_post)

        nso = self.get_new_nso(version="5.0.0")
        gtoken = nso.f_token_generation_step_2("test_id", "test_url")
        assert gtoken == "gtoken"

    def test_get_gtoken(self, monkeypatch):
        # User access failure
        def mock_get_user_access_token(*args, **kwargs):
            return MockResponse(400, json={})

        monkeypatch.setattr(
            NSO, "get_user_access_token", mock_get_user_access_token
        )
        nso = self.get_new_nso()
        with pytest.raises(NintendoException):
            nso.get_gtoken("test")

        def mock_get_user_access_token(*args, **kwargs):
            out_json = {
                "id_token": "id_token",
                "access_token": "user_access_token",
            }
            return MockResponse(200, json=out_json)

        monkeypatch.setattr(
            NSO, "get_user_access_token", mock_get_user_access_token
        )

        def mock_get_user_info(*args, **kwargs):
            return {
                "language": "language",
                "birthday": "birthday",
                "country": "country",
            }

        monkeypatch.setattr(NSO, "get_user_info", mock_get_user_info)

        def mock_f_token_generation_step_1(*args, **kwargs):
            out_json = {
                "result": {
                    "webApiServerCredential": {
                        "accessToken": "access_token",
                    }
                }
            }
            return MockResponse(200, json=out_json)

        monkeypatch.setattr(
            NSO, "f_token_generation_step_1", mock_f_token_generation_step_1
        )

        def mock_f_token_generation_step_2(*args, **kwargs):
            assert args[1] == "access_token"
            return "gtoken"

        monkeypatch.setattr(
            NSO, "f_token_generation_step_2", mock_f_token_generation_step_2
        )

        nso = self.get_new_nso()
        gtoken = nso.get_gtoken("test")
        assert gtoken == "gtoken"
        assert nso._user_access_token == "user_access_token"
        assert nso._id_token == "id_token"
        assert nso._user_info["language"] == "language"
        assert nso._user_info["birthday"] == "birthday"
        assert nso._user_info["country"] == "country"
        assert nso._gtoken == "gtoken"

    def test_get_bullet_token(self, monkeypatch):
        user_info = {
            "language": "language",
            "birthday": "birthday",
            "country": "country",
        }

        def generate_and_mock_post(status_code, out_json, exception):
            nso = self.get_new_nso(web_view_version="5.0.0")

            def mock_post(*args, **kwargs):
                assert "cookies" in kwargs
                return MockResponse(status_code, json=out_json)

            monkeypatch.setattr(requests.Session, "post", mock_post)
            with pytest.raises(exception):
                nso.get_bullet_token("gtoken", user_info)

        # Failures
        generate_and_mock_post(401, {}, SplatnetException)
        generate_and_mock_post(403, {}, SplatnetException)
        generate_and_mock_post(204, {}, SplatnetException)
        generate_and_mock_post(200, {}, NintendoException)

        # Success
        nso = self.get_new_nso(web_view_version="5.0.0")

        def mock_post(*args, **kwargs):
            assert "cookies" in kwargs
            return MockResponse(200, json={"bulletToken": "bullet_token"})

        monkeypatch.setattr(requests.Session, "post", mock_post)
        bullet_token = nso.get_bullet_token("gtoken", user_info)
        assert bullet_token == "bullet_token"

    # TODO: cgarza - test splatnet_web_version. This is tricky because it's a
    # decorated function, so we need to mock the underlying function without
    # mocking the decorator.
