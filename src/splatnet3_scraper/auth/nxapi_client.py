from __future__ import annotations

import base64
import json
import logging
import shutil
import subprocess
import time
import uuid
from typing import Any
from urllib.parse import urlparse

import requests

from splatnet3_scraper import __version__
from splatnet3_scraper.auth.exceptions import (
    NXAPIAuthException,
    NXAPIError,
    NXAPIIncompatibleClientError,
    NXAPIInsufficientScopeError,
    NXAPIInvalidGrantError,
    NXAPIInvalidTokenError,
    NXAPIRateLimitError,
    NXAPIServiceUnavailableError,
    NXAPIUnsupportedVersionError,
)
from splatnet3_scraper.constants import NXAPI_DEFAULT_CLIENT_VERSION

logger = logging.getLogger(__name__)


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Mask sensitive header values before logging."""
    sensitive = {
        "authorization",
        "client-id",
        "client_secret",
        "client-secret",
        "client-assertion",
    }
    sanitized = {}
    for key, value in headers.items():
        if key.lower() in sensitive:
            sanitized[key] = "***redacted***"
        else:
            sanitized[key] = value
    return sanitized


# Map NXAPI error codes to specific exception classes
_ERROR_CODE_MAP: dict[str, type[NXAPIError]] = {
    "invalid_token": NXAPIInvalidTokenError,
    "invalid_grant": NXAPIInvalidGrantError,
    "insufficient_scope": NXAPIInsufficientScopeError,
    "rate_limit": NXAPIRateLimitError,
    "service_unavailable": NXAPIServiceUnavailableError,
    "incompatible_client": NXAPIIncompatibleClientError,
    "unsupported_version": NXAPIUnsupportedVersionError,
}


def _parse_error_response(response: requests.Response) -> NXAPIError:
    """Parse an NXAPI error response into a specific exception type.

    Args:
        response: The HTTP response with status code >= 400

    Returns:
        NXAPIError: Specific exception subclass based on error code
    """
    debug_id = response.headers.get("X-Trace-Id")

    try:
        payload = response.json()
        error_code = payload.get("error", "unknown_error")
        error_description = payload.get("error_description")
    except ValueError:
        error_code = "unknown_error"
        error_description = response.text[:500] if response.text else None

    exc_class = _ERROR_CODE_MAP.get(error_code, NXAPIError)

    desc = error_description or "No description"
    message = f"NXAPI error ({error_code}): {desc}"
    if debug_id:
        message += f" [debug_id: {debug_id}]"

    return exc_class(
        message=message,
        error_code=error_code,
        error_description=error_description,
        debug_id=debug_id,
        http_status=response.status_code,
    )


class NXAPIClient:
    """Handles client-authenticated access to nxapi's hosted services."""

    _REFRESH_SKEW_SECONDS = 30
    _DEFAULT_TIMEOUT = 10
    _CLIENT_ASSERTION_TTL_SECONDS = 300

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str | None = None,
        client_assertion: str | None = None,
        client_assertion_private_key_path: str | None = None,
        client_assertion_jku: str | None = None,
        client_assertion_kid: str | None = None,
        client_assertion_type: str | None = None,
        scope: str,
        token_url: str,
        user_agent: str | None,
        client_version: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip() if client_secret else None
        self.client_assertion = (
            client_assertion.strip() if client_assertion else None
        )
        self.client_assertion_private_key_path = (
            client_assertion_private_key_path.strip()
            if client_assertion_private_key_path
            else None
        )
        self.client_assertion_jku = (
            client_assertion_jku.strip() if client_assertion_jku else None
        )
        self.client_assertion_kid = (
            client_assertion_kid.strip() if client_assertion_kid else None
        )
        default_assertion_type = (
            "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
        )
        self.client_assertion_type = (
            client_assertion_type.strip()
            if client_assertion_type
            else default_assertion_type
            if client_assertion or self._uses_generated_client_assertion()
            else None
        )
        self.scope = scope.strip()
        self.token_url = token_url
        self.user_agent = user_agent.strip() if user_agent else None
        resolved_version = (
            client_version.strip()
            if client_version
            else NXAPI_DEFAULT_CLIENT_VERSION
        )
        self.client_version = resolved_version
        self.session = session or requests.Session()

        self._access_token: str | None = None
        self._expires_at: float | None = None
        self._refresh_token_value: str | None = None

        # Config endpoint caching
        self._config_cache: dict[str, Any] | None = None
        self._config_cached_at: float | None = None

        # OAuth discovery caching
        self._discovered_token_url: str | None = None

        if not self.client_id:
            raise NXAPIAuthException("NXAPI client id is required")

        if not self.scope:
            raise NXAPIAuthException("NXAPI scope must be provided")

        if not self.user_agent:
            fallback = f"splatnet3_scraper/{__version__}"
            logger.warning(
                "NXAPI user agent missing, falling back to"
                " %s. Provide a descriptive UA via"
                " NXAPI_USER_AGENT to comply with nxapi's"
                " policy.",
                fallback,
            )
            self.user_agent = fallback

    def discover_auth_server(
        self, resource_url: str | None = None
    ) -> str | None:
        """Discover the token endpoint via OAuth Protected Resource
        Metadata.

        Fetches ``/.well-known/oauth-protected-resource`` from the
        resource server, then
        ``/.well-known/oauth-authorization-server`` from the
        authorization server found there, and returns the
        ``token_endpoint``.

        Results are cached for the lifetime of this client.

        Args:
            resource_url: Origin of the resource server. Defaults
                to the NXAPI znca API origin.

        Returns:
            str | None: The discovered token endpoint URL, or None
                on failure.
        """
        if self._discovered_token_url is not None:
            return self._discovered_token_url

        if resource_url is None:
            from splatnet3_scraper.constants import NXAPI_ZNCA_URL

            parsed = urlparse(NXAPI_ZNCA_URL)
            resource_url = f"{parsed.scheme}://{parsed.netloc}"

        try:
            resp = self.session.get(
                resource_url + "/.well-known/oauth-protected-resource",
                timeout=self._DEFAULT_TIMEOUT,
            )
            if resp.status_code != 200:
                return None
            resource_meta = resp.json()
            auth_servers = resource_meta.get("authorization_servers", [])
            if not auth_servers:
                return None

            auth_server = auth_servers[0]
            resp2 = self.session.get(
                auth_server + "/.well-known/oauth-authorization-server",
                timeout=self._DEFAULT_TIMEOUT,
            )
            if resp2.status_code != 200:
                return None
            auth_meta = resp2.json()
            token_endpoint = auth_meta.get("token_endpoint")
            if token_endpoint:
                self._discovered_token_url = token_endpoint
            return token_endpoint
        except (
            requests.RequestException,
            ValueError,
            KeyError,
        ):
            logger.debug("OAuth discovery failed, using configured token_url")
            return None

    def _is_token_valid(self) -> bool:
        if not self._access_token or self._expires_at is None:
            return False
        return time.time() < self._expires_at - self._REFRESH_SKEW_SECONDS

    def _request_body(
        self,
        grant_type: str = "client_credentials",
        token_url: str | None = None,
    ) -> dict[str, str]:
        """Build OAuth token request body.

        Args:
            grant_type: Either "client_credentials" or "refresh_token"

        Returns:
            dict containing the form-encoded request body parameters
        """
        body: dict[str, str] = {
            "grant_type": grant_type,
            "scope": self.scope,
            "client_id": self.client_id,
        }

        if grant_type == "refresh_token" and self._refresh_token_value:
            body["refresh_token"] = self._refresh_token_value
        assertion = self._resolve_client_assertion(token_url)
        if assertion:
            body.update(
                {
                    "client_assertion": assertion,
                    "client_assertion_type": self.client_assertion_type,
                }
            )
        elif self.client_secret:
            body["client_secret"] = self.client_secret

        return body

    def _uses_generated_client_assertion(self) -> bool:
        return self.client_assertion_private_key_path is not None

    @staticmethod
    def _b64url_encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _client_assertion_audience(token_url: str) -> str:
        parsed = urlparse(token_url)
        if not parsed.scheme or not parsed.netloc:
            raise NXAPIAuthException(
                f"Cannot derive NXAPI audience from token URL: {token_url}"
            )
        return f"{parsed.scheme}://{parsed.netloc}"

    def _sign_client_assertion(self, signing_input: bytes) -> bytes:
        if not self.client_assertion_private_key_path:
            raise NXAPIAuthException(
                "NXAPI client assertion signing key path is not configured"
            )

        openssl_bin = shutil.which("openssl")
        if openssl_bin is None:
            raise NXAPIAuthException(
                "OpenSSL is required to generate NXAPI client assertions"
            )

        result = subprocess.run(
            [
                openssl_bin,
                "dgst",
                "-sha256",
                "-sign",
                self.client_assertion_private_key_path,
            ],
            input=signing_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="ignore").strip()
            message = stderr or "unknown signing error"
            raise NXAPIAuthException(
                "Failed to sign NXAPI client assertion with OpenSSL: "
                f"{message}"
            )

        return result.stdout

    def _build_client_assertion(self, token_url: str) -> str:
        if not self.client_assertion_private_key_path:
            raise NXAPIAuthException(
                "Generated NXAPI client assertions require a private key path"
            )
        if not self.client_assertion_jku or not self.client_assertion_kid:
            raise NXAPIAuthException(
                "Generated NXAPI client assertions require both jku and kid"
            )

        now = int(time.time())
        header = {
            "alg": "RS256",
            "kid": self.client_assertion_kid,
            "jku": self.client_assertion_jku,
        }
        payload = {
            "typ": "client_assertion",
            "aud": self._client_assertion_audience(token_url),
            "iss": self.client_id,
            "sub": self.client_id,
            "iat": now,
            "exp": now + self._CLIENT_ASSERTION_TTL_SECONDS,
            "jti": str(uuid.uuid4()),
        }
        signing_input = ".".join(
            (
                self._b64url_encode(
                    json.dumps(header, separators=(",", ":")).encode("utf-8")
                ),
                self._b64url_encode(
                    json.dumps(payload, separators=(",", ":")).encode(
                        "utf-8"
                    )
                ),
            )
        ).encode("ascii")
        signature = self._sign_client_assertion(signing_input)
        return (
            signing_input.decode("ascii")
            + "."
            + self._b64url_encode(signature)
        )

    def _resolve_client_assertion(self, token_url: str | None) -> str | None:
        if self.client_assertion:
            return self.client_assertion
        if self._uses_generated_client_assertion():
            return self._build_client_assertion(token_url or self.token_url)
        return None

    def _resolve_token_url(self) -> str:
        """Return the token URL, preferring discovered endpoint."""
        discovered = self.discover_auth_server()
        if discovered:
            return discovered
        return self.token_url

    def _request_token(self, grant_type: str = "client_credentials") -> None:
        """Request a new token from the authorization server.

        Args:
            grant_type: Either "client_credentials" or
                "refresh_token"

        Raises:
            NXAPIAuthException: If the request fails.
            NXAPIInvalidGrantError: If the refresh token is
                invalid.
            NXAPIError: For other API errors.
        """
        effective_url = self._resolve_token_url()
        logger.debug(
            "Requesting nxapi access token with grant_type=%s",
            grant_type,
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "X-znca-Client-Version": self.client_version,
        }

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Posting to nxapi token endpoint %s with headers %s",
                effective_url,
                _sanitize_headers(headers),
            )

        try:
            response = self.session.post(
                effective_url,
                data=self._request_body(grant_type, effective_url),
                headers=headers,
                timeout=self._DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise NXAPIAuthException(
                f"Failed to contact nxapi-auth token endpoint: {exc}"
            ) from exc

        if response.status_code != 200:
            raise _parse_error_response(response)

        try:
            payload = response.json()
        except ValueError as exc:
            raise NXAPIAuthException(
                "Invalid JSON returned by nxapi-auth"
            ) from exc

        try:
            token = payload["access_token"]
        except KeyError as exc:
            raise NXAPIAuthException(
                "nxapi-auth response missing access_token"
            ) from exc

        expires_in = payload.get("expires_in", 0)
        try:
            expires_in_seconds = float(expires_in)
        except (TypeError, ValueError):
            expires_in_seconds = 0

        now = time.time()
        self._access_token = token
        self._expires_at = now + max(expires_in_seconds, 0)

        # Store refresh token if provided (may be None)
        self._refresh_token_value = payload.get("refresh_token")

        logger.debug(
            "Obtained nxapi access token expiring in %.2fs%s",
            expires_in_seconds,
            " (with refresh token)" if self._refresh_token_value else "",
        )

    def _refresh_access_token(self) -> None:
        """Refresh the access token.

        Tries refresh_token grant if available, falling back to
        client_credentials on invalid_grant error.
        """
        if self._refresh_token_value:
            try:
                self._request_token(grant_type="refresh_token")
                return
            except NXAPIInvalidGrantError:
                logger.info(
                    "Refresh token invalid, falling back to client_credentials"
                )
                self._refresh_token_value = None

        self._request_token(grant_type="client_credentials")

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Get a valid access token, refreshing if necessary.

        Args:
            force_refresh: If True, force a token refresh even if the current
                token appears valid.

        Returns:
            str: A valid access token.
        """
        if force_refresh or not self._is_token_valid():
            self._refresh_access_token()
        assert self._access_token is not None  # For type checkers
        return self._access_token

    def build_request_headers(self) -> dict[str, str]:
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.client_id,
            "User-Agent": self.user_agent,
            "X-znca-Client-Version": self.client_version,
        }

    def get_nso_version(
        self,
        config_url: str,
        cache_ttl: float = 3600.0,
    ) -> str | None:
        """Fetch the latest supported NSO version from /api/znca/config.

        Args:
            config_url: URL for the NXAPI config endpoint.
            cache_ttl: Cache time-to-live in seconds. Default is 1 hour.

        Returns:
            str: The latest NSO version string (e.g., "2.5.0"), or None
                if the request fails.
        """
        # Check cache
        now = time.time()
        if (
            self._config_cache is not None
            and self._config_cached_at is not None
            and (now - self._config_cached_at) < cache_ttl
        ):
            cached_version = self._config_cache.get("nso_version")
            if cached_version:
                return cached_version

        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "X-znca-Client-Version": self.client_version,
        }

        try:
            headers.update(self.build_request_headers())
        except (NXAPIAuthException, NXAPIError) as exc:
            logger.warning(
                "Failed to authenticate NXAPI config request for %s: %s",
                config_url,
                exc,
            )
            return None

        try:
            response = self.session.get(
                config_url,
                headers=headers,
                timeout=self._DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning(
                "Failed to fetch NXAPI config from %s: %s", config_url, exc
            )
            return None

        if response.status_code != 200:
            logger.warning(
                "NXAPI config endpoint returned status %d", response.status_code
            )
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.warning("NXAPI config endpoint returned invalid JSON")
            return None

        # Cache the response
        self._config_cache = payload
        self._config_cached_at = now

        nso_version = payload.get("nso_version")
        if nso_version:
            logger.debug(
                "Discovered NSO version from NXAPI config: %s",
                nso_version,
            )
        return nso_version

    def encrypt_request(
        self,
        encrypt_url: str,
        coral_url: str,
        token: str | None,
        data: str,
    ) -> bytes:
        """Encrypt a Coral API request body using NXAPI.

        Uses the encrypt-request endpoint. This is required for
        Coral API 3.0.1+ which uses encrypted request bodies.

        Args:
            encrypt_url: URL for the NXAPI encrypt-request endpoint.
            coral_url: The Coral API endpoint URL the request is destined for.
            token: The Bearer token for the Coral request, or None for endpoints
                that don't require auth (e.g., Account/Login).
            data: The JSON-encoded request body string to encrypt.

        Returns:
            bytes: The encrypted request body to send to the Coral API.

        Raises:
            NXAPIError: If the encryption request fails.
            NXAPIAuthException: If there's a network or authentication error.
        """
        headers = self.build_request_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/octet-stream"

        body = {
            "url": coral_url,
            "token": token,
            "data": data,
        }

        logger.debug("Encrypting request for %s", coral_url)

        try:
            response = self.session.post(
                encrypt_url,
                json=body,
                headers=headers,
                timeout=self._DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise NXAPIAuthException(
                f"Failed to contact NXAPI encrypt endpoint: {exc}"
            ) from exc

        if response.status_code != 200:
            raise _parse_error_response(response)

        return response.content

    def decrypt_response(
        self,
        decrypt_url: str,
        encrypted_data: bytes,
    ) -> str:
        """Decrypt a Coral API response using NXAPI decrypt-response endpoint.

        Args:
            decrypt_url: URL for the NXAPI decrypt-response endpoint.
            encrypted_data: The encrypted response bytes from the Coral API.

        Returns:
            str: The decrypted JSON response content.

        Raises:
            NXAPIError: If the decryption request fails.
            NXAPIAuthException: If there's a network or authentication error.
        """
        import base64

        headers = self.build_request_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "text/plain"

        body = {
            "data": base64.b64encode(encrypted_data).decode("ascii"),
        }

        logger.debug("Decrypting Coral API response")

        try:
            response = self.session.post(
                decrypt_url,
                json=body,
                headers=headers,
                timeout=self._DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise NXAPIAuthException(
                f"Failed to contact NXAPI decrypt endpoint: {exc}"
            ) from exc

        if response.status_code != 200:
            raise _parse_error_response(response)

        return response.text
