class NintendoException(Exception):
    """Base class for all Nintendo exceptions."""

    pass


class FTokenException(Exception):
    """Base class for all Imink exceptions."""

    pass


class SplatNetException(Exception):
    """Base class for all Splatnet exceptions."""

    pass


class NXAPIAuthException(SplatNetException):
    """Raised when nxapi-auth client authentication fails."""

    pass


class NXAPIError(SplatNetException):
    """Base class for structured NXAPI API errors.

    Attributes:
        error_code: The error code string from the NXAPI response.
        error_description: Optional description from the error response.
        debug_id: The debug_id from X-Trace-Id header for troubleshooting.
        http_status: The HTTP status code of the response.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        error_description: str | None = None,
        debug_id: str | None = None,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.error_description = error_description
        self.debug_id = debug_id
        self.http_status = http_status


class NXAPIInvalidTokenError(NXAPIError):
    """Token invalid or expired (401 invalid_token).

    The access token is no longer valid. Client should refresh the token
    or request a new one using client credentials.
    """

    pass


class NXAPIInvalidGrantError(NXAPIError):
    """OAuth invalid_grant error.

    The refresh token is invalid or expired. Client should fall back to
    requesting a new token using client credentials.
    """

    pass


class NXAPIInsufficientScopeError(NXAPIError):
    """Token scope does not allow endpoint (403 insufficient_scope).

    The access token's scope does not permit the requested operation.
    """

    pass


class NXAPIRateLimitError(NXAPIError):
    """Rate limited (429 rate_limit).

    The client has exceeded the rate limit. Should implement backoff.
    """

    pass


class NXAPIServiceUnavailableError(NXAPIError):
    """Worker unavailable (503 service_unavailable).

    Could not connect to a worker device. Should retry with backoff.
    """

    pass


class NXAPIIncompatibleClientError(NXAPIError):
    """X-znca-Client-Version incompatible (400 incompatible_client).

    The client version is not compatible with the requested Coral version.
    Client needs updating.
    """

    pass


class NXAPIUnsupportedVersionError(NXAPIError):
    """X-znca-Version not supported (406 unsupported_version).

    The requested NSO app version is not supported. Use /api/znca/config
    to discover supported versions.
    """

    pass


class AccountCooldownException(SplatNetException):
    """Raised when an account is cooling down and cannot be used."""

    pass


class RateLimitException(SplatNetException):
    """Raised when SplatNet responds with a rate limiting status code."""

    pass
