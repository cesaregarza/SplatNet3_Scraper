import hashlib
import os
from unittest.mock import patch

import pytest
import requests

from splatnet3_scraper.auth.exceptions import (
    FTokenException,
    NintendoException,
    SplatNetException,
)
from splatnet3_scraper.auth.nso import NSO, FTokenResult
from splatnet3_scraper.constants import (
    APP_VERSION_FALLBACK,
    NXAPI_DEFAULT_CLIENT_VERSION,
    NXAPI_ZNCA_URL,
)
from tests.mock import MockResponse

nso_path = "splatnet3_scraper.auth.nso.NSO"
nso_mangled = "splatnet3_scraper.auth.nso.NSO._NSO"


class TestNSO:
    mock_user_data = {
        "language": "test_language",
        "country": "test_country",
        "birthday": "test_birthday",
        "id": "test_id",
    }

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
            elif key == "_f_token_function":
                assert nso_variables[key] == nso.get_ftoken
            elif key == "logger":
                assert nso_variables[key].name == "splatnet3_scraper.auth.nso"
            else:
                assert nso_variables[key] is None

    def test_generate_version(self, monkeypatch: pytest.MonkeyPatch):
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

    def test_app_version_override(self) -> None:
        nso = NSO.new_instance()
        nso.set_app_version_override("9.9.9")
        assert nso.version == "9.9.9"

        nso.set_app_version_override(None)
        assert nso.version == APP_VERSION_FALLBACK

    # def test_version_property(self, monkeypatch: pytest.MonkeyPatch):
    #     test_string = 'whats-new__latest__version">Version    5.0.0</span>'

    #     def mock_get(*args, **kwargs):
    #         return MockResponse(200, text=test_string)

    #     monkeypatch.setattr(requests.Session, "get", mock_get)
    #     nso = NSO.new_instance()
    #     version = nso.version
    #     assert version == "5.0.0"
    #     assert nso._version == "5.0.0"

    #     # Test short circuit
    #     def mock_get(*args, **kwargs):
    #         raise Exception

    #     monkeypatch.setattr(requests.Session, "get", mock_get)
    #     version = nso.version
    #     assert version == "5.0.0"
    #     assert nso._version == "5.0.0"

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

    @pytest.mark.parametrize(
        "uri",
        [
            "npf71b963c1b7b6d119://auth#session_token_code=test_code&state=abc",
            "npf71b963c1b7b6d119://auth#state=abc&session_token_code=test_code",
            "npf71b963c1b7b6d119://auth?session_token_code=test_code&state=abc",
            (
                "npf71b963c1b7b6d119://auth?foo=bar"
                "#state=abc&session_token_code=test_code"
            ),
        ],
    )
    def test_parse_npf_uri(self, uri: str):
        nso = self.get_new_nso()
        assert nso.parse_npf_uri(uri) == "test_code"

    def test_parse_npf_uri_missing(self):
        nso = self.get_new_nso()
        with pytest.raises(ValueError):
            nso.parse_npf_uri("npf71b963c1b7b6d119://auth#state=abc")

    def test_get_session_token(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            return MockResponse(200, json={"session_token": "test"})

        monkeypatch.setattr(requests.Session, "post", mock_get)
        nso = self.get_new_nso(version="5.0.0", verifier="test_verifier")
        assert nso._session_token is None
        session_token = nso.get_session_token("session_code")
        assert session_token == "test"

    def test_get_user_access_token(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            return MockResponse(200, json={"access_token": "test"})

        monkeypatch.setattr(requests.Session, "post", mock_get)
        nso = self.get_new_nso()

        access_token = nso.get_user_access_token("test")
        assert isinstance(access_token, dict)
        assert access_token["access_token"] == "test"

    def test_user_info(self, monkeypatch: pytest.MonkeyPatch):
        def mock_get(*args, **kwargs):
            return MockResponse(200, json={"test": "test"})

        monkeypatch.setattr(requests.Session, "get", mock_get)
        nso = self.get_new_nso()
        user_info = nso.get_user_info("test")
        assert user_info == {"test": "test"}

    @pytest.mark.parametrize(
        "step, coral, xfail",
        [
            (1, True, False),
            (1, False, False),
            (2, True, False),
            (2, False, True),
        ],
        ids=["step1_coral", "step1", "step2_coral", "step2"],
    )
    def test_get_ftoken(
        self,
        step: int,
        coral: bool,
        xfail: bool,
        monkeypatch: pytest.MonkeyPatch,
    ):
        def mock_post(*args, **kwargs):
            out_json = {
                "f": "test_f",
                "request_id": "test_request_id",
                "timestamp": "test_timestamp",
            }
            return MockResponse(200, json=out_json)

        def mock_post_fail(*args, **kwargs):
            return MockResponse(400, json={})

        nso = self.get_new_nso()
        monkeypatch.setattr(requests.Session, "post", mock_post)
        args = ["test", "test", step, "test", "test" if coral else None]
        if xfail:
            with pytest.raises(ValueError):
                nso.get_ftoken(*args)
        else:
            result = nso.get_ftoken(*args)
            assert isinstance(result, FTokenResult)
            assert result.f == "test_f"
            assert result.request_id == "test_request_id"
            assert result.timestamp == "test_timestamp"
            assert result.encrypted_request is None
            monkeypatch.setattr(requests.Session, "post", mock_post_fail)
            # Fail on request
            with pytest.raises(FTokenException):
                nso.get_ftoken(*args)

    def test_get_ftoken_optional_fields(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that get_ftoken handles missing request_id/timestamp."""

        def mock_post(*args, **kwargs):
            return MockResponse(200, json={"f": "test_f"})

        nso = self.get_new_nso()
        monkeypatch.setattr(requests.Session, "post", mock_post)
        result = nso.get_ftoken("test", "test", 1, "test", None)
        assert result.f == "test_f"
        assert result.request_id is None
        assert result.timestamp is None
        assert result.encrypted_request is None

    def test_get_ftoken_encrypted_token_request(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test encrypt_token_request flow returns encrypted body."""
        import base64

        encrypted_data = b"\x00\x01\x02encrypted"
        b64_data = base64.b64encode(encrypted_data).decode()

        def mock_post(*args, **kwargs):
            return MockResponse(
                200,
                json={
                    "f": "test_f",
                    "encrypted_token_request": b64_data,
                },
            )

        nso = self.get_new_nso()
        monkeypatch.setattr(requests.Session, "post", mock_post)
        result = nso.get_ftoken("test", "test", 1, "test", None)
        assert result.f == "test_f"
        assert result.request_id is None
        assert result.timestamp is None
        assert result.encrypted_request == encrypted_data

    def test_get_ftoken_includes_client_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured_headers: dict[str, str] = {}

        def mock_post(*args, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return MockResponse(
                200,
                json={
                    "f": "test_f",
                    "request_id": "test_request_id",
                    "timestamp": "test_timestamp",
                },
            )

        monkeypatch.setattr(requests.Session, "post", mock_post)

        nso = self.get_new_nso()

        class DummyNXAPIClient:
            client_version = "2.3.4"

            def build_request_headers(self):
                return {
                    "Authorization": "Bearer fake",
                    "Client-Id": "client",
                    "User-Agent": "custom/1.0",
                    "X-znca-Client-Version": self.client_version,
                }

            def get_nso_version(self, config_url, cache_ttl):
                return None

        nso.set_nxapi_client(DummyNXAPIClient())

        result = nso.get_ftoken(NXAPI_ZNCA_URL, "id", 1, "na", None)
        assert isinstance(result, FTokenResult)
        assert captured_headers["X-znca-Client-Version"] == "2.3.4"

    def test_get_ftoken_retries_with_default_client_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen_versions: list[str] = []

        def mock_post(*args, **kwargs):
            seen_versions.append(kwargs["headers"]["X-znca-Client-Version"])
            if len(seen_versions) == 1:
                response = MockResponse(
                    400,
                    json={
                        "error": "invalid_request",
                        "error_description": (
                            "Invalid X-znca-Client-Version header"
                        ),
                    },
                )
                response.headers = {"X-Trace-Id": "trace-1"}
                return response
            return MockResponse(
                200,
                json={
                    "f": "test_f",
                    "request_id": "test_request_id",
                    "timestamp": "test_timestamp",
                },
            )

        monkeypatch.setattr(requests.Session, "post", mock_post)

        nso = self.get_new_nso()

        class DummyNXAPIClient:
            def __init__(self) -> None:
                self.client_version = "stale-client-version"

            def build_request_headers(self):
                return {
                    "Authorization": "Bearer fake",
                    "Client-Id": "client",
                    "User-Agent": "custom/1.0",
                    "X-znca-Client-Version": self.client_version,
                }

            def get_nso_version(self, config_url, cache_ttl):
                return None

        client = DummyNXAPIClient()
        nso.set_nxapi_client(client)

        result = nso.get_ftoken(NXAPI_ZNCA_URL, "id", 1, "na", None)

        assert isinstance(result, FTokenResult)
        assert seen_versions == [
            "stale-client-version",
            NXAPI_DEFAULT_CLIENT_VERSION,
        ]
        assert client.client_version == NXAPI_DEFAULT_CLIENT_VERSION

    def test_get_web_service_access_token_pass(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        def mock_post(*args, **kwargs):
            out_json = {
                "result": {
                    "webApiServerCredential": {"accessToken": "test_token"},
                    "user": {"id": "test_id"},
                }
            }
            return MockResponse(200, json=out_json)

        nso = self.get_new_nso(version="5.0.0")
        monkeypatch.setattr(requests.Session, "post", mock_post)

        access_token, coral_id = nso.get_web_service_access_token(
            "test_id_token",
            self.mock_user_data,
            "test_f_token",
            "test_request_id",
            "test_timestamp",
        )
        assert access_token == "test_token"
        assert coral_id == "test_id"

    def test_get_web_service_access_token_fail(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        def mock_post(*args, **kwargs):
            return MockResponse(400, json={})

        nso = self.get_new_nso(version="5.0.0")
        monkeypatch.setattr(requests.Session, "post", mock_post)

        with pytest.raises(NintendoException):
            nso.get_web_service_access_token(
                "test_id_token",
                self.mock_user_data,
                "test_f_token",
                "test_request_id",
                "test_timestamp",
            )

    def test_get_gtoken_request_pass(self, monkeypatch: pytest.MonkeyPatch):
        def mock_post(*args, **kwargs):
            out_json = {
                "result": {
                    "accessToken": "test_token",
                }
            }
            return MockResponse(200, json=out_json)

        nso = self.get_new_nso(version="5.0.0")
        monkeypatch.setattr(requests.Session, "post", mock_post)

        gtoken = nso.get_gtoken_request(
            "test_wsat",
            "test_f_token",
            "test_request_id",
            "test_timestamp",
        )
        assert gtoken == "test_token"

    def test_get_gtoken_request_fail(self, monkeypatch: pytest.MonkeyPatch):
        def mock_post(*args, **kwargs):
            return MockResponse(400, json={})

        nso = self.get_new_nso(version="5.0.0")
        monkeypatch.setattr(requests.Session, "post", mock_post)

        with pytest.raises(NintendoException):
            nso.get_gtoken_request(
                "test_wsat",
                "test_f_token",
                "test_request_id",
                "test_timestamp",
            )

    def test_g_token_generation_phase_1(self):
        nso = self.get_new_nso()

        with (
            patch.object(nso, "_f_token_function") as mock_f_token_function,
            patch(nso_path + ".get_web_service_access_token") as mock_get_wsat,
        ):
            mock_f_token_function.return_value = FTokenResult(
                f="test_f_token",
                request_id="test_request_id",
                timestamp="test_timestamp",
            )
            mock_get_wsat.return_value = "test_access_token"
            wsat = nso.g_token_generation_phase_1(
                "test_id_token",
                self.mock_user_data,
                "test_id",
                "test_f_token_url",
            )
            assert wsat == "test_access_token"
            mock_f_token_function.assert_called_once_with(
                "test_f_token_url", "test_id_token", 1, "test_id", None
            )
            mock_get_wsat.assert_called_once_with(
                "test_id_token",
                self.mock_user_data,
                "test_f_token",
                "test_request_id",
                "test_timestamp",
                encrypted_body=None,
            )

    def test_g_token_generation_phase_2(self):
        nso = self.get_new_nso()

        with (
            patch.object(nso, "_f_token_function") as mock_f_token_function,
            patch(nso_path + ".get_gtoken_request") as mock_get_gtoken,
        ):
            mock_f_token_function.return_value = FTokenResult(
                f="test_f_token",
                request_id="test_request_id",
                timestamp="test_timestamp",
            )
            mock_get_gtoken.return_value = "test_gtoken"
            wsat = nso.g_token_generation_phase_2(
                "test_wsat", "test_na_id", "test_coral_id", "test_f_token_url"
            )
            assert wsat == "test_gtoken"
            mock_f_token_function.assert_called_once_with(
                "test_f_token_url",
                "test_wsat",
                2,
                "test_na_id",
                "test_coral_id",
            )
            mock_get_gtoken.assert_called_once_with(
                "test_wsat",
                "test_f_token",
                "test_request_id",
                "test_timestamp",
                encrypted_body=None,
            )

    @pytest.mark.parametrize(
        "f_token_url",
        [
            "test_url",
            None,
        ],
        ids=[
            "url_provided",
            "url_not_provided",
        ],
    )
    def test_get_gtoken(self, f_token_url):
        expected_url = NXAPI_ZNCA_URL if f_token_url is None else f_token_url
        # User Access Failure
        with (
            patch(nso_path + ".get_user_access_token") as mock_guat,
            pytest.raises(NintendoException),
        ):
            mock_guat.return_value = None
            nso = self.get_new_nso()
            nso.get_gtoken("test")

        # Success
        with (
            patch(nso_path + ".get_user_access_token") as mock_guat,
            patch(nso_path + ".get_user_info") as mock_gui,
            patch(nso_path + ".g_token_generation_phase_1") as mock_gtp1,
            patch(nso_path + ".g_token_generation_phase_2") as mock_gtp2,
        ):
            mock_guat.return_value = {
                "access_token": "test_user_access_token",
                "id_token": "test_id_token",
            }
            mock_gui.return_value = self.mock_user_data
            mock_gtp1.return_value = ("test_wsat", "test_coral_id")
            mock_gtp2.return_value = "test_gtoken"

            gtoken = nso.get_gtoken("test_session_token", f_token_url)
            assert gtoken == "test_gtoken"
            mock_guat.assert_called_once_with("test_session_token")
            mock_gui.assert_called_once_with("test_user_access_token")
            mock_gtp1.assert_called_once_with(
                "test_id_token",
                self.mock_user_data,
                "test_id",
                f_token_url=expected_url,
            )
            mock_gtp2.assert_called_once_with(
                "test_wsat",
                "test_id",
                "test_coral_id",
                f_token_url=expected_url,
            )
            assert nso._user_access_token == "test_user_access_token"
            assert nso._id_token == "test_id_token"
            assert nso._user_info == self.mock_user_data
            assert nso._gtoken == "test_gtoken"

    def test_get_bullet_token(self, monkeypatch: pytest.MonkeyPatch):
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
        generate_and_mock_post(401, {}, SplatNetException)
        generate_and_mock_post(403, {}, SplatNetException)
        generate_and_mock_post(204, {}, SplatNetException)
        generate_and_mock_post(200, {}, NintendoException)

        # Success
        nso = self.get_new_nso(web_view_version="5.0.0")

        def mock_post(*args, **kwargs):
            assert "cookies" in kwargs
            return MockResponse(200, json={"bulletToken": "bullet_token"})

        monkeypatch.setattr(requests.Session, "post", mock_post)
        bullet_token = nso.get_bullet_token("gtoken", user_info)
        assert bullet_token == "bullet_token"

    def test_set_new_f_token_function(self):
        nso = NSO.new_instance()
        assert nso._f_token_function == nso.get_ftoken

        def new_function(*args, **kwargs):
            return "new_function"

        # Set
        nso.set_new_f_token_function(new_function)
        assert nso._f_token_function == new_function
        # Reset
        nso.set_new_f_token_function()
        assert nso._f_token_function == nso.get_ftoken

    # TODO: cgarza - test splatnet_web_version. This is tricky because it's a
    # decorated function, so we need to mock the underlying function without
    # mocking the decorator.
