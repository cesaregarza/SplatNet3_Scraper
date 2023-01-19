import hashlib
import os
from unittest import mock

import pytest
import requests
from pytest_lazyfixture import lazy_fixture

from splatnet3_scraper.base.tokens.nso import (
    NSO,
    FTokenException,
    NintendoException,
    SplatnetException,
)
from splatnet3_scraper.constants import (
    APP_VERSION_FALLBACK,
    DEFAULT_USER_AGENT,
    IMINK_URL,
    IOS_APP_URL,
    SPLATNET_URL,
    WEB_VIEW_VERSION_FALLBACK,
)


class TestNSO:
    class MockResponse:
        def __init__(
            self,
            status_code: int,
            text: str = "",
            json: dict = {},
            url: str = "",
        ) -> None:
            self._status_code = status_code
            self.status_code_counter = 0
            self._text = text
            self.text_counter = 0
            self._json = json
            self.json_counter = 0
            self._url = url
            self.url_counter = 0

        @property
        def status_code(self):
            self.status_code_counter += 1
            return self._status_code

        @property
        def text(self):
            self.text_counter += 1
            return self._text

        def json(self):
            self.json_counter += 1
            return self._json

        @property
        def url(self):
            self.url_counter += 1
            return self._url

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

    def test_generate_version(self, monkeypatch: pytest.MonkeyPatch):
        test_string = 'whats-new__latest__version">Version    5.0.0</span>'

        def mock_get(*args, **kwargs):
            return TestNSO.MockResponse(200, text=test_string)

        monkeypatch.setattr(requests.Session, "get", mock_get)
        nso = NSO.new_instance()
        version = nso.get_version()
        assert version == "5.0.0"

        # Test fallback
        def mock_get(*args, **kwargs):
            return TestNSO.MockResponse(200, text="")

        monkeypatch.setattr(requests.Session, "get", mock_get)
        version = nso.get_version()
        assert version == APP_VERSION_FALLBACK

    def test_version_property(self, monkeypatch: pytest.MonkeyPatch):
        test_string = 'whats-new__latest__version">Version    5.0.0</span>'

        def mock_get(*args, **kwargs):
            return TestNSO.MockResponse(200, text=test_string)

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
        monkeypatch: pytest.MonkeyPatch,
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
        monkeypatch: pytest.MonkeyPatch,
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
        monkeypatch: pytest.MonkeyPatch,
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
        monkeypatch: pytest.MonkeyPatch,
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
        monkeypatch: pytest.MonkeyPatch,
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
            return TestNSO.MockResponse(200, url="https://test.com/")

        monkeypatch.setattr(NSO, "generate_new_state", mock_generate_new_state)
        monkeypatch.setattr(
            NSO, "generate_new_verifier", mock_generate_new_verifier
        )
        monkeypatch.setattr(hashlib, "sha256", mock_hashlib_sha256)
        monkeypatch.setattr(requests.Session, "get", mock_get)
        nso = NSO.new_instance()
        assert nso.generate_login_url() == "https://test.com/"

    def test_get_session_token(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            return TestNSO.MockResponse(200, json={"session_token": "test"})

        monkeypatch.setattr(requests.Session, "post", mock_get)
        nso = self.get_new_nso(version="5.0.0", verifier="test_verifier")
        assert nso._session_token is None
        session_token = nso.get_session_token("session_code")
        assert session_token == "test"

    def test_get_user_access_token(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            return requests.Response()

        monkeypatch.setattr(requests.Session, "post", mock_get)
        nso = self.get_new_nso()

        access_token = nso.get_user_access_token("test")
        assert isinstance(access_token, requests.Response)

    def test_user_info(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            return TestNSO.MockResponse(200, json={"test": "test"})

        monkeypatch.setattr(requests.Session, "get", mock_get)
        nso = self.get_new_nso()
        user_info = nso.get_user_info("test")
        assert user_info == {"test": "test"}

    def test_get_ftoken(self, monkeypatch: pytest.MonkeyPatch):
        def mock_post(*args, **kwargs):
            out_json = {
                "f": "test_f",
                "request_id": "test_request_id",
                "timestamp": "test_timestamp",
            }
            return TestNSO.MockResponse(200, json=out_json)

        nso = self.get_new_nso()
        monkeypatch.setattr(requests.Session, "post", mock_post)

        ftoken, request_id, timestamp = nso.get_ftoken("test", "test", "test")
        assert ftoken == "test_f"
        assert request_id == "test_request_id"
        assert timestamp == "test_timestamp"

        # Fail
        def mock_post(*args, **kwargs):
            return TestNSO.MockResponse(400, json={})

        monkeypatch.setattr(requests.Session, "post", mock_post)
        with pytest.raises(FTokenException):
            nso.get_ftoken("test", "test", "test")
