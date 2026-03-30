import base64
import json
import subprocess
from unittest.mock import MagicMock

import pytest

from splatnet3_scraper.auth.exceptions import (
    NXAPIAuthException,
    NXAPIError,
    NXAPIInvalidGrantError,
    NXAPIInvalidTokenError,
    NXAPIRateLimitError,
    NXAPIServiceUnavailableError,
)
from splatnet3_scraper.auth.nxapi_client import (
    NXAPIClient,
    _parse_error_response,
)

TOKEN_URL = "https://auth.example/token"
SCOPE = "ca:gf"


def _mock_response(
    access_token: str = "test-token", expires: int = 60, status: int = 200
):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = {
        "access_token": access_token,
        "expires_in": expires,
    }
    response.headers = {}
    return response


def _session_with_response(response: MagicMock) -> MagicMock:
    session = MagicMock()
    session.post.return_value = response
    return session


def _decode_b64url_json(segment: str) -> dict[str, object]:
    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def test_build_request_headers_uses_cached_token(monkeypatch) -> None:
    session = _session_with_response(_mock_response())

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent=None,
        client_version="1.0.0",
        session=session,
    )

    headers_first = client.build_request_headers()
    assert headers_first["Authorization"] == "Bearer test-token"
    assert headers_first["Client-Id"] == "client-id"
    # Falls back to default UA when none provided
    assert "splatnet3_scraper/" in headers_first["User-Agent"]
    session.post.assert_called_once()
    called_headers = session.post.call_args.kwargs["headers"]
    assert called_headers["X-znca-Client-Version"] == "1.0.0"

    # Second call should reuse the cached token without another POST
    headers_second = client.build_request_headers()
    assert headers_second == headers_first
    session.post.assert_called_once()

    # Forced refresh triggers another POST and new token adoption
    session.post.return_value = _mock_response("another-token", 120)
    client.get_access_token(force_refresh=True)
    assert session.post.call_count == 2
    refreshed_headers = client.build_request_headers()
    assert refreshed_headers["Authorization"] == "Bearer another-token"


def test_token_endpoint_failure_raises() -> None:
    response = _mock_response(status=400)
    response.json.return_value = {
        "error": "invalid_client",
        "error_description": "Client authentication failed",
    }
    response.headers = {}
    session = _session_with_response(response)

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="custom/1.0",
        client_version="1.0.0",
        session=session,
    )

    # Raises NXAPIError (structured) instead of NXAPIAuthException
    with pytest.raises(NXAPIError, match="invalid_client"):
        client.build_request_headers()
    called_headers = session.post.call_args.kwargs["headers"]
    assert called_headers["X-znca-Client-Version"] == "1.0.0"


def test_secret_or_assertion_optional() -> None:
    session = _session_with_response(_mock_response())

    client = NXAPIClient(
        client_id="client-id",
        client_secret=None,
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="custom/1.0",
        client_version="1.0.0",
        session=session,
    )

    headers = client.build_request_headers()
    assert headers["Client-Id"] == "client-id"
    assert headers["Authorization"].startswith("Bearer ")


def test_generated_client_assertion_populates_request_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _session_with_response(_mock_response())
    captured: dict[str, list[str] | bytes] = {}

    def _mock_run(*args, **kwargs):
        captured["command"] = list(args[0])
        captured["input"] = kwargs["input"]
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=b"signed-assertion",
            stderr=b"",
        )

    monkeypatch.setattr(
        "splatnet3_scraper.auth.nxapi_client.shutil.which",
        lambda name: "/usr/bin/openssl",
    )
    monkeypatch.setattr(
        "splatnet3_scraper.auth.nxapi_client.subprocess.run",
        _mock_run,
    )
    monkeypatch.setattr(
        "splatnet3_scraper.auth.nxapi_client.time.time",
        lambda: 1710000000,
    )
    monkeypatch.setattr(
        "splatnet3_scraper.auth.nxapi_client.uuid.uuid4",
        lambda: "uuid-1234",
    )

    client = NXAPIClient(
        client_id="client-id",
        client_assertion_private_key_path="/tmp/private.pem",
        client_assertion_jku="https://example.com/.well-known/jwks.json",
        client_assertion_kid="kid-1",
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="custom/1.0",
        client_version="1.0.0",
        session=session,
    )

    body = client._request_body(token_url=TOKEN_URL)

    assert body["client_assertion_type"] == (
        "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
    )
    assert captured["command"] == [
        "/usr/bin/openssl",
        "dgst",
        "-sha256",
        "-sign",
        "/tmp/private.pem",
    ]

    signing_input = captured["input"].decode("ascii")
    header_segment, payload_segment = signing_input.split(".")
    header = _decode_b64url_json(header_segment)
    payload = _decode_b64url_json(payload_segment)

    assert header == {
        "alg": "RS256",
        "kid": "kid-1",
        "jku": "https://example.com/.well-known/jwks.json",
    }
    assert payload == {
        "typ": "client_assertion",
        "aud": "https://auth.example",
        "iss": "client-id",
        "sub": "client-id",
        "iat": 1710000000,
        "exp": 1710000300,
        "jti": "uuid-1234",
    }
    assert body["client_assertion"].startswith(signing_input + ".")


def test_generated_client_assertion_requires_openssl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _session_with_response(_mock_response())
    monkeypatch.setattr(
        "splatnet3_scraper.auth.nxapi_client.shutil.which",
        lambda name: None,
    )

    client = NXAPIClient(
        client_id="client-id",
        client_assertion_private_key_path="/tmp/private.pem",
        client_assertion_jku="https://example.com/.well-known/jwks.json",
        client_assertion_kid="kid-1",
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="custom/1.0",
        session=session,
    )

    with pytest.raises(NXAPIAuthException, match="OpenSSL"):
        client._request_body(token_url=TOKEN_URL)


def test_client_version_defaults_when_empty() -> None:
    from splatnet3_scraper.constants import NXAPI_DEFAULT_CLIENT_VERSION

    session = _session_with_response(_mock_response())

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="custom/1.0",
        client_version="",
        session=session,
    )
    assert client.client_version == NXAPI_DEFAULT_CLIENT_VERSION


def test_client_version_defaults_when_none() -> None:
    from splatnet3_scraper.constants import NXAPI_DEFAULT_CLIENT_VERSION

    session = _session_with_response(_mock_response())

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="custom/1.0",
        session=session,
    )
    assert client.client_version == NXAPI_DEFAULT_CLIENT_VERSION


# ============================================================================
# Error Parsing Tests
# ============================================================================


def _mock_error_response(
    error: str,
    description: str | None = None,
    debug_id: str | None = None,
    status: int = 400,
) -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.json.return_value = {
        "error": error,
        "error_description": description,
    }
    response.headers = {"X-Trace-Id": debug_id} if debug_id else {}
    return response


def test_parse_error_response_invalid_token() -> None:
    response = _mock_error_response(
        "invalid_token", "Token has expired", "trace-123", status=401
    )
    exc = _parse_error_response(response)
    assert isinstance(exc, NXAPIInvalidTokenError)
    assert exc.error_code == "invalid_token"
    assert exc.error_description == "Token has expired"
    assert exc.debug_id == "trace-123"
    assert exc.http_status == 401


def test_parse_error_response_invalid_grant() -> None:
    response = _mock_error_response("invalid_grant", "Refresh token invalid")
    exc = _parse_error_response(response)
    assert isinstance(exc, NXAPIInvalidGrantError)
    assert exc.error_code == "invalid_grant"


def test_parse_error_response_rate_limit() -> None:
    response = _mock_error_response(
        "rate_limit", "Too many requests", status=429
    )
    exc = _parse_error_response(response)
    assert isinstance(exc, NXAPIRateLimitError)
    assert exc.http_status == 429


def test_parse_error_response_service_unavailable() -> None:
    response = _mock_error_response(
        "service_unavailable", "No workers available", status=503
    )
    exc = _parse_error_response(response)
    assert isinstance(exc, NXAPIServiceUnavailableError)


def test_parse_error_response_unknown_error() -> None:
    response = _mock_error_response("some_new_error", "Unknown error type")
    exc = _parse_error_response(response)
    # Falls back to base NXAPIError
    assert type(exc) is NXAPIError
    assert exc.error_code == "some_new_error"


def test_parse_error_response_debug_id_in_message() -> None:
    response = _mock_error_response(
        "invalid_token", "Token expired", "debug-xyz-123"
    )
    exc = _parse_error_response(response)
    assert "debug-xyz-123" in str(exc)


def test_parse_error_response_non_json() -> None:
    response = MagicMock()
    response.status_code = 500
    response.json.side_effect = ValueError("Not JSON")
    response.text = "Internal Server Error"
    response.headers = {}

    exc = _parse_error_response(response)
    assert exc.error_code == "unknown_error"
    assert "Internal Server Error" in (exc.error_description or "")


# ============================================================================
# Refresh Token Support Tests
# ============================================================================


def _mock_response_with_refresh(
    access_token: str = "test-token",
    refresh_token: str | None = None,
    expires: int = 60,
    status: int = 200,
) -> MagicMock:
    response = MagicMock()
    response.status_code = status
    payload = {"access_token": access_token, "expires_in": expires}
    if refresh_token:
        payload["refresh_token"] = refresh_token
    response.json.return_value = payload
    response.headers = {}
    return response


def test_refresh_token_stored_from_response() -> None:
    response = _mock_response_with_refresh(
        "access-1", refresh_token="refresh-abc", expires=60
    )
    session = _session_with_response(response)

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    client.get_access_token()
    assert client._refresh_token_value == "refresh-abc"


def test_refresh_token_used_when_available() -> None:
    # First response with refresh token
    first_response = _mock_response_with_refresh(
        "access-1",
        refresh_token="refresh-abc",
        expires=0,  # Expires immediately
    )
    # Second response using refresh token
    second_response = _mock_response_with_refresh(
        "access-2", refresh_token="refresh-def", expires=60
    )
    session = MagicMock()
    session.post.side_effect = [first_response, second_response]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    # First call uses client_credentials
    token1 = client.get_access_token()
    assert token1 == "access-1"
    first_call_body = session.post.call_args_list[0].kwargs["data"]
    assert first_call_body["grant_type"] == "client_credentials"

    # Second call should use refresh_token grant since token is expired
    token2 = client.get_access_token()
    assert token2 == "access-2"
    second_call_body = session.post.call_args_list[1].kwargs["data"]
    assert second_call_body["grant_type"] == "refresh_token"
    assert second_call_body["refresh_token"] == "refresh-abc"


def test_refresh_token_fallback_on_invalid_grant() -> None:
    # First response with refresh token
    first_response = _mock_response_with_refresh(
        "access-1",
        refresh_token="refresh-abc",
        expires=0,  # Expires immediately
    )
    # Refresh attempt fails with invalid_grant
    invalid_grant_response = _mock_error_response(
        "invalid_grant", "Token revoked"
    )
    # Fallback to client_credentials succeeds
    fallback_response = _mock_response_with_refresh("access-2", expires=60)

    session = MagicMock()
    session.post.side_effect = [
        first_response,
        invalid_grant_response,
        fallback_response,
    ]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    # First call
    client.get_access_token()
    assert client._refresh_token_value == "refresh-abc"

    # Second call should try refresh_token, fail, then use client_credentials
    token2 = client.get_access_token()
    assert token2 == "access-2"
    assert session.post.call_count == 3

    # Verify the refresh token was cleared after invalid_grant
    assert client._refresh_token_value is None


# ============================================================================
# Config Endpoint Tests
# ============================================================================

CONFIG_URL = "https://nxapi.example/api/znca/config"


def test_get_nso_version_success() -> None:
    token_response = _mock_response()
    config_response = MagicMock()
    config_response.status_code = 200
    config_response.json.return_value = {"nso_version": "2.5.0", "versions": []}

    session = MagicMock()
    session.post.return_value = token_response
    session.get.return_value = config_response

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    version = client.get_nso_version(CONFIG_URL)
    assert version == "2.5.0"
    session.post.assert_called_once()
    assert session.get.call_count == 2
    config_call = session.get.call_args_list[-1]
    assert config_call.args[0] == CONFIG_URL
    request_headers = config_call.kwargs["headers"]
    assert request_headers["Authorization"] == "Bearer test-token"
    assert request_headers["Client-Id"] == "client-id"


def test_get_nso_version_caching() -> None:
    token_response = _mock_response()
    config_response = MagicMock()
    config_response.status_code = 200
    config_response.json.return_value = {"nso_version": "2.5.0"}

    session = MagicMock()
    session.post.return_value = token_response
    session.get.return_value = config_response

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    # First call fetches from endpoint
    version1 = client.get_nso_version(CONFIG_URL, cache_ttl=3600)
    assert version1 == "2.5.0"

    # Second call should use cache
    version2 = client.get_nso_version(CONFIG_URL, cache_ttl=3600)
    assert version2 == "2.5.0"

    # The first call performs discovery plus the config fetch; the second
    # call should reuse the cached config without additional requests.
    assert session.get.call_count == 2
    assert session.post.call_count == 1


def test_get_nso_version_returns_none_on_error() -> None:
    token_response = _mock_response()
    error_response = MagicMock()
    error_response.status_code = 500

    session = MagicMock()
    session.post.return_value = token_response
    session.get.return_value = error_response

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    version = client.get_nso_version(CONFIG_URL)
    assert version is None


def test_get_nso_version_returns_none_on_invalid_json() -> None:
    token_response = _mock_response()
    config_response = MagicMock()
    config_response.status_code = 200
    config_response.json.side_effect = ValueError("Not JSON")

    session = MagicMock()
    session.post.return_value = token_response
    session.get.return_value = config_response

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    version = client.get_nso_version(CONFIG_URL)
    assert version is None


# ============================================================================
# Encryption/Decryption Tests
# ============================================================================

ENCRYPT_URL = "https://nxapi.example/api/znca/encrypt-request"
DECRYPT_URL = "https://nxapi.example/api/znca/decrypt-response"


def test_encrypt_request_success() -> None:
    token_response = _mock_response()
    encrypt_response = MagicMock()
    encrypt_response.status_code = 200
    encrypt_response.content = b"\x00\x01\x02encrypted-data"

    session = MagicMock()
    session.post.side_effect = [token_response, encrypt_response]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope="ca:gf ca:er ca:dr",
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    result = client.encrypt_request(
        encrypt_url=ENCRYPT_URL,
        coral_url="https://api-lp1.znc.srv.nintendo.net/v4/Account/Login",
        token=None,
        data='{"parameter": {"f": "abc"}}',
    )

    assert result == b"\x00\x01\x02encrypted-data"

    # Verify the encrypt request was made correctly
    encrypt_call = session.post.call_args_list[1]
    assert encrypt_call.args[0] == ENCRYPT_URL
    request_body = encrypt_call.kwargs["json"]
    assert (
        request_body["url"]
        == "https://api-lp1.znc.srv.nintendo.net/v4/Account/Login"
    )
    assert request_body["token"] is None
    assert request_body["data"] == '{"parameter": {"f": "abc"}}'


def test_encrypt_request_with_bearer_token() -> None:
    token_response = _mock_response()
    encrypt_response = MagicMock()
    encrypt_response.status_code = 200
    encrypt_response.content = b"encrypted"

    session = MagicMock()
    session.post.side_effect = [token_response, encrypt_response]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope="ca:gf ca:er ca:dr",
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    client.encrypt_request(
        encrypt_url=ENCRYPT_URL,
        coral_url="https://api-lp1.znc.srv.nintendo.net/v4/Game/GetWebServiceToken",
        token="bearer-token-xyz",
        data='{"parameter": {}}',
    )

    # Verify token is passed in the request body
    encrypt_call = session.post.call_args_list[1]
    request_body = encrypt_call.kwargs["json"]
    assert request_body["token"] == "bearer-token-xyz"


def test_encrypt_request_error_raises() -> None:
    token_response = _mock_response()
    error_response = _mock_error_response(
        "insufficient_scope", "Missing ca:er scope", status=403
    )

    session = MagicMock()
    session.post.side_effect = [token_response, error_response]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope="ca:gf",  # Missing ca:er
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    with pytest.raises(NXAPIError, match="insufficient_scope"):
        client.encrypt_request(
            encrypt_url=ENCRYPT_URL,
            coral_url="https://api-lp1.znc.srv.nintendo.net/v4/Account/Login",
            token=None,
            data="{}",
        )


def test_decrypt_response_success() -> None:
    token_response = _mock_response()
    decrypt_response = MagicMock()
    decrypt_response.status_code = 200
    decrypt_response.text = '{"result": {"accessToken": "gtoken-123"}}'

    session = MagicMock()
    session.post.side_effect = [token_response, decrypt_response]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope="ca:gf ca:er ca:dr",
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    result = client.decrypt_response(
        decrypt_url=DECRYPT_URL,
        encrypted_data=b"\x00\x01\x02encrypted-response",
    )

    assert result == '{"result": {"accessToken": "gtoken-123"}}'

    # Verify the decrypt request was made correctly
    decrypt_call = session.post.call_args_list[1]
    assert decrypt_call.args[0] == DECRYPT_URL
    request_body = decrypt_call.kwargs["json"]
    # Verify encrypted_data was base64 encoded
    import base64

    expected_b64 = base64.b64encode(b"\x00\x01\x02encrypted-response").decode(
        "ascii"
    )
    assert request_body["data"] == expected_b64


def test_decrypt_response_error_raises() -> None:
    token_response = _mock_response()
    error_response = _mock_error_response(
        "invalid_response", "Could not decrypt response", status=400
    )

    session = MagicMock()
    session.post.side_effect = [token_response, error_response]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope="ca:gf ca:er ca:dr",
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    with pytest.raises(NXAPIError, match="invalid_response"):
        client.decrypt_response(
            decrypt_url=DECRYPT_URL,
            encrypted_data=b"malformed-data",
        )


def test_encrypt_request_network_error() -> None:
    import requests

    token_response = _mock_response()

    session = MagicMock()
    session.post.side_effect = [
        token_response,
        requests.RequestException("Connection failed"),
    ]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope="ca:gf ca:er ca:dr",
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    with pytest.raises(NXAPIAuthException, match="encrypt endpoint"):
        client.encrypt_request(
            encrypt_url=ENCRYPT_URL,
            coral_url="https://api-lp1.znc.srv.nintendo.net/v4/Account/Login",
            token=None,
            data="{}",
        )


def test_decrypt_response_network_error() -> None:
    import requests

    token_response = _mock_response()

    session = MagicMock()
    session.post.side_effect = [
        token_response,
        requests.RequestException("Connection failed"),
    ]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope="ca:gf ca:er ca:dr",
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    with pytest.raises(NXAPIAuthException, match="decrypt endpoint"):
        client.decrypt_response(
            decrypt_url=DECRYPT_URL,
            encrypted_data=b"data",
        )


# ============================================================================
# OAuth Protected Resource Discovery Tests
# ============================================================================


def test_discover_auth_server_success() -> None:
    resource_response = MagicMock()
    resource_response.status_code = 200
    resource_response.json.return_value = {
        "authorization_servers": ["https://auth.example.com"]
    }

    auth_response = MagicMock()
    auth_response.status_code = 200
    auth_response.json.return_value = {
        "token_endpoint": "https://auth.example.com/oauth/token",
        "issuer": "https://auth.example.com",
    }

    session = MagicMock()
    session.post.return_value = _mock_response()
    session.get.side_effect = [resource_response, auth_response]

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    url = client.discover_auth_server("https://api.example.com")
    assert url == "https://auth.example.com/oauth/token"

    # Second call should use cache
    url2 = client.discover_auth_server("https://api.example.com")
    assert url2 == url
    assert session.get.call_count == 2  # Only first call


def test_discover_auth_server_failure_returns_none() -> None:
    error_response = MagicMock()
    error_response.status_code = 404

    session = MagicMock()
    session.post.return_value = _mock_response()
    session.get.return_value = error_response

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    url = client.discover_auth_server("https://api.example.com")
    assert url is None


def test_discover_auth_server_network_error_returns_none() -> None:
    import requests

    session = MagicMock()
    session.post.return_value = _mock_response()
    session.get.side_effect = requests.RequestException("fail")

    client = NXAPIClient(
        client_id="client-id",
        client_secret="secret",
        client_assertion=None,
        client_assertion_type=None,
        scope=SCOPE,
        token_url=TOKEN_URL,
        user_agent="test/1.0",
        client_version="1.0.0",
        session=session,
    )

    url = client.discover_auth_server("https://api.example.com")
    assert url is None
