import os
from unittest import mock
import hashlib

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

        @property
        def json(self):
            self.json_counter += 1
            return self._json

        @property
        def url(self):
            self.url_counter += 1
            return self._url

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
