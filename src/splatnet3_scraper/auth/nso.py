from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Literal, TypeAlias, cast
from urllib.parse import parse_qsl, urlparse

import requests

from splatnet3_scraper import __version__
from splatnet3_scraper.auth.exceptions import (
    FTokenException,
    NintendoException,
    NXAPIAuthException,
    NXAPIInvalidTokenError,
    NXAPIRateLimitError,
    NXAPIServiceUnavailableError,
    SplatNetException,
)
from splatnet3_scraper.auth.nxapi_client import _sanitize_headers
from splatnet3_scraper.constants import (
    APP_VERSION_FALLBACK,
    CORAL_ACCOUNT_LOGIN_PATH,
    CORAL_API_URL,
    CORAL_GET_WEB_SERVICE_TOKEN_PATH,
    DEFAULT_USER_AGENT,
    IOS_APP_URL,
    NXAPI_CONFIG_CACHE_TTL,
    NXAPI_CONFIG_URL,
    NXAPI_DEFAULT_CLIENT_VERSION,
    NXAPI_DECRYPT_URL,
    NXAPI_ENCRYPT_URL,
    NXAPI_ZNCA_URL,
    SPLATNET_URL,
    ZNCA_PLATFORM_VERSION,
)
from splatnet3_scraper.utils import get_splatnet_version, retry

if TYPE_CHECKING:
    from splatnet3_scraper.auth.nxapi_client import NXAPIClient

version_re = re.compile(
    r"(?<=whats\-new\_\_latest\_\_version\"\>Version)\s+\d+\.\d+\.\d+"
)


@dataclass
class FTokenResult:
    """Result from an f-token generation request.

    Attributes:
        f: The f-token string.
        request_id: The request ID (may be None with
            encrypt_token_request flow).
        timestamp: The timestamp (may be None with
            encrypt_token_request flow).
        encrypted_request: Base64-decoded encrypted Coral request
            body, if the f endpoint returned one.
    """

    f: str
    request_id: str | None
    timestamp: str | int | None
    encrypted_request: bytes | None = None


FToken_Gen: TypeAlias = Callable[
    [str, str, Literal[1] | Literal[2], str, str | None],
    FTokenResult,
]

_NXAPI_HOST = urlparse(NXAPI_ZNCA_URL).netloc


class NSO:
    """The NSO class contains all the logic to proceed through the login flow.
    This class also holds various properties that are used to make requests to
    the Nintendo Switch Online API. Login flow is roughly as follows, assuming
    the user has never generated a session token before:

        1.  Initialize a requests session and store it.
        2.  Generate a random state and S256 code challenge that will be used
            to obtain the "session_token". Store them for later use.
        3.  Generate a login URL using the state and code challenge that the
            user will open in their browser. The user will then copy a link and
            feed it back to the program.
        4.  Parse the URI to obtain the session token code, then use it
            alongside the code challenge to obtain the ``session_token``. Store
            it for later use. The session token is valid for 2 years and can be
            revoked by the user.
        5.  Use the session token to obtain a user access response from
            Nintendo. This response will contain an ``id_token`` and a user
            access token. Store both for later user.
        6.  Use the user access token to obtain the user information. This is
            required to obtain the first ``f_token``, for the Nintendo Switch
            Online API. This is a message authentication code generated from the
            timestamp and id token in an obscure manner and will be necessary
            to generate the API access token.
        7.  Use the Nintendo-obtained ``id_token`` to obtain the first
            ``f_token``, for the Nintendo Switch Online API. The ``f_token``
            will also return a timestamp and a request ID.
        8.  Use the first ``f_token``, the request ID, the timestamp, the user
            information, the ``id_token`` to obtain the
            ``web_service_access_token``.
        9.  Use the ``web_service_access_token`` to obtain the second
            ``f_token``. This is a message authentication code generated from
            the timestamp and id token in an obscure manner and will be
            necessary to generate the ``gtoken``. This step is distinct from
            step 7, make sure not to use the same ``f_token`` twice.
        10. Use the second ``f_token``, the request ID, the timestamp, and the
            ``web_service_access_token`` from step 9, and the id
            ``4834290508791808`` to obtain the ``gtoken``.
        11. Use the ``gtoken`` and user information to obtain a
            ``bullet_token``. This token is valid for 2 hours.

    Once the login flow is complete, the NSO class contains all the necessary
    values to regenerate the tokens. To minimize the number of objects to track,
    the NSO class only stores the tokens in memory. The TokenManager class
    handles the persistence of the tokens to disk.
    """

    def __init__(self, session: requests.Session) -> None:
        """Initializes the NSO class. The NSO class contains all the logic and
        holds all the necessary values to proceed through the login flow.

        The ``__init__`` method sets the following internal variables:

            -   ``session``: The requests session object that is used to make
                requests to the Nintendo Switch Online API. This is the only
                variable that is passed in to the ``__init__`` method.
            -   ``_state``: The internal state variable that is used to obtain
                the session token. This is a random string that is generated
                when the ``NSO.state`` property is first accessed, and is used
                to generate the login URL.
            -   ``_verifier``: The internal verifier variable that is used to
                obtain the session token. This is a random string that is
                generated when the ``NSO.verifier`` property is first accessed,
                and is used to generate the login URL. The verifier is also
                used to solve the code challenge, verifying to Nintendo that
                the user is who they say they are.
            -   ``_version``: The internal version variable that is used to
                verify the NSO app version. This is a string that is generated
                when the ``NSO.version`` property is first accessed, and is
                used to obtain the session token.
            -   ``_web_view_version``: The internal web view version variable
                that is used to verify the NSO app version. This is a string
                that is generated when the ``NSO.web_view_version`` property is
                first accessed, and is used to obtain the session token.
            -   ``_session_token``: A stored session token. This is required to
                generate all other tokens and information. This is obtained
                during the login flow and is valid for 2 years.
            -   ``_user_access_token``: A stored user access token. This is a
                token that is obtained during the login flow and is used to
                obtain the user information.
            -   ``_id_token``: A stored id token. This is a token that is
                obtained during the login flow and is used to obtain the gtoken.
            -   ``_gtoken``: A stored gtoken. This is a token that is obtained
                during the login flow and is used to obtain the bullet token. It
                is valid for 6 hours and 30 minutes.
            -   ``_user_info``: A stored user information dictionary. This is
                obtained during the login flow and is used to obtain the "f"
                token.
            -   ``_f_token_function``: A stored function that is used to obtain
                the "f" token. This function is set to the ``get_ftoken``
                method by default, and can be set with the
                ``set_new_f_token_function`` method to use a user-defined
                function if desired.


        Args:
            session (requests.Session): The NSO class uses a requests session
                to make requests to the Nintendo Switch Online API. The session
                object is passed in to the NSO class so that the same session
                object can be used to make requests to the SplatNet API.
        """
        self.session = session
        self._state: bytes | None = None
        self._verifier: bytes | None = None
        self._version: str | None = None
        self._web_view_version: str | None = None
        self._session_token: str | None = None
        self._user_access_token: str | None = None
        self._id_token: str | None = None
        self._nintendo_account_id: str | None = None
        self._coral_user_id: str | None = None
        self._gtoken: str | None = None
        self._user_info: dict[str, str] | None = None
        self._f_token_function: FToken_Gen = self.get_ftoken
        self._nxapi_client: NXAPIClient | None = None
        self.logger = logging.getLogger(__name__)
        self._app_version_override: str | None = None

    @staticmethod
    def new_instance() -> "NSO":
        """Creates a new instance of the NSO class with a new requests session.

        This is the recommended way to create a new instance of the NSO class,
        as it ensures that the session is a fresh session, however it is not
        absolutely necessary to instantiate a new NSO class using this method.
        Passing in a new session to the ``__init__`` method is perfectly fine.

        Returns:
            NSO: A new instance of the NSO class.
        """
        session = requests.Session()
        return NSO(session=session)

    @property
    def version(self) -> str:
        """Returns the current version of the NSO app. Necessary to get the
        session token. If the version has not been obtained yet, it will be
        obtained and stored. If the version cannot be obtained, a fallback
        version will be used.

        The version discovery priority is:
        1. Explicit override via set_app_version_override()
        2. NXAPI config endpoint (if NXAPI client is configured)
        3. Fallback version constant

        Returns:
            str: The current version of the NSO app.
        """
        if self._version is None:
            override = self._app_version_override
            if override:
                self._version = override
            else:
                # Try NXAPI config endpoint if client is configured
                if self._nxapi_client is not None:
                    nso_version = self._nxapi_client.get_nso_version(
                        config_url=NXAPI_CONFIG_URL,
                        cache_ttl=NXAPI_CONFIG_CACHE_TTL,
                    )
                    if nso_version:
                        self._version = nso_version
                        return self._version

                # Fall back to hardcoded version
                self._version = APP_VERSION_FALLBACK
        return self._version

    def set_app_version_override(self, version: str | None) -> None:
        """Overrides the NSO app version used in authentication requests.

        Args:
            version (str | None): The version string to force. If ``None`` or an
                empty string is provided, the override is cleared and the
                fallback behaviour is restored.
        """
        normalized = version.strip() if version else None
        self._app_version_override = normalized or None
        if self._app_version_override:
            self._version = self._app_version_override
        else:
            self._version = None

    @retry(times=2, exceptions=ValueError)
    def get_version(self) -> str:
        """Fetches the current version of the Nintendo Switch Online app from
        the iOS app store. This is necessary to access the API. This method
        retries twice if the version cannot be obtained, in case the iOS App
        Store site is down or slow. If the version cannot be obtained after
        three attempts, a fallback version defined in the ``constants.py`` file
        will be used.

        Returns:
            str: The current version of the NSO app.
        """
        # TODO: Replace the iOS app store method with a method that does not
        # require scraping a website with scraping protection.
        response = self.session.get(IOS_APP_URL)
        version = version_re.search(response.text)
        if version is None:
            self.logger.warning(
                "Failed to get version from app store, using fallback"
            )
            return APP_VERSION_FALLBACK
        return version.group(0).strip()

    @property
    def state(self) -> bytes:
        """Returns a base64url encoded random 36 byte string for the auth state.
        This is used to generate the login URL. To align with node.js's crypto
        module, padding is removed. If the state has not been obtained yet, it
        will be obtained and stored by creating a random 36 byte string and then
        base64url encoding it.

        Returns:
            bytes: The auth state, without padding. This is used within the
                login flow to verify that the user is who they say they are.
        """
        if self._state is None:
            self._state = self.generate_new_state()
        return self._state

    def generate_new_state(self) -> bytes:
        """Generates a new state.

        Returns:
            bytes: The auth state, without padding. A random 36 byte string
                that is base64url encoded.
        """
        return base64.urlsafe_b64encode(os.urandom(36))

    @property
    def verifier(self) -> bytes:
        """Returns a base64url encoded random 32 byte string for the code
        verifier. This is used to generate the S256 code challenge. To align
        with node.js's crypto module, padding is removed. If the verifier has
        not been obtained yet, it will be obtained and stored by creating a
        random 32 byte string and then base64url encoding it.

        Returns:
            bytes: The code verifier, without padding. This is used within the
                login flow to verify that the user is who they say they are.
        """
        if self._verifier is None:
            self._verifier = self.generate_new_verifier()
        return self._verifier

    def generate_new_verifier(self) -> bytes:
        """Generates a new code verifier, which is a random 32 byte string
        that is base64url encoded and with padding removed. This is used to
        generate the S256 code challenge.

        Returns:
            bytes: The code verifier, without padding.
        """
        verifier_ = base64.urlsafe_b64encode(os.urandom(32))
        return verifier_.replace(b"=", b"")

    @property
    def session_token(self) -> str:
        """Returns the session token. This cannot be generated and must be set
        by the user. If the session token has not been set, a ValueError will be
        raised.

        Raises:
            ValueError: The session token has not been set.

        Returns:
            str: The session token.
        """
        if self._session_token is None:
            raise ValueError("Session token is not set.")
        return self._session_token

    def generate_login_url(self, user_agent: str | None = None) -> str:
        """Generates the login URL that can be used to obtain the session token.

        This method will generate the login URL that is used to obtain the
        session token. For full details on how to obtain a session token, see
        the ``Obtaining a session token`` section of the documentation.

        Args:
            user_agent (str): The user agent to use. Defaults to the default
                user agent found in ``constants.py``.

        Returns:
            str: The login URL that can be used to obtain the session token.
        """
        # https://dev.to/mathewthe2/intro-to-nintendo-switch-rest-api-2cm7
        hash_ = hashlib.sha256()
        hash_.update(self.verifier)
        challenge = base64.urlsafe_b64encode(hash_.digest()).replace(b"=", b"")

        header = {
            "Host": "accounts.nintendo.com",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": user_agent
            if user_agent is not None
            else DEFAULT_USER_AGENT,
            "Accept": (
                "text/html,"
                + "application/xhtml+xml,"
                + "application/xml;q=0.9,"
                + "image/webp,"
                + "image/apng,"
                + "*/*;q=0.8n"
            ),
            "DNT": "1",
            "Accept-Encoding": "gzip,deflate,br",
        }
        params = {
            "state": self.state,
            "redirect_uri": "npf71b963c1b7b6d119://auth",
            "client_id": "71b963c1b7b6d119",
            "scope": ("openid user user.birthday user.mii user.screenName"),
            "response_type": "session_token_code",
            "session_token_code_challenge": challenge,
            "session_token_code_challenge_method": "S256",
            "theme": "login_form",
        }
        login_url = "https://accounts.nintendo.com/connect/1.0.0/authorize"
        response = self.session.get(
            login_url,
            headers=header,
            params=params,  # type: ignore
        )
        return response.url

    def parse_npf_uri(self, uri: str) -> str:
        """Parses the Nintendo callback URI and extracts the session token code.

        Args:
            uri (str): The uri returned by the Nintendo login page.

        Returns:
            str: The session token code. This is *NOT* the session token, but is
                used to obtain the session token.

        Raises:
            ValueError: The session token code could not be found in the URI.
        """
        parsed_uri = urlparse(uri)
        query_sources = [parsed_uri.fragment, parsed_uri.query]

        for source in query_sources:
            if not source:
                continue
            params = dict(parse_qsl(source))
            session_token_code = params.get("session_token_code")
            if session_token_code:
                return session_token_code

        raise ValueError("Session token code not found in callback URI.")

    def get_session_token(self, session_token_code: str) -> str:
        """Obtains the session token from the session token code.

        This method will obtain the session token from the session token code.
        It will use provide the session token code to Nintendo's servers
        alongside the session token code verifier. Nintendo will then verify
        that the user is who they say they are and return the session token.

        Args:
            session_token_code (str): The session token code. This is obtained
                by parsing the uri obtained at the URL returned by
                ``generate_login_url``.

        Returns:
            str: The session token. DO NOT SHARE THIS TOKEN WITH ANYONE.
        """
        header = {
            "User-Agent": f"OnlineLounge/{self.version} NASDKAPI Android",
            "Accept-Language": "en-US",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "540",
            "Host": "accounts.nintendo.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        params = {
            "client_id": "71b963c1b7b6d119",
            "session_token_code": session_token_code,
            "session_token_code_verifier": self.verifier,
        }
        uri = "https://accounts.nintendo.com/connect/1.0.0/api/session_token"
        response = self.session.post(uri, headers=header, data=params)
        session_token = response.json()["session_token"]
        self._session_token = session_token
        return session_token

    def get_user_access_token(self, session_token: str) -> dict:
        """Obtains the user access token from the session token.

        This method sends a request to Nintendo's servers containing the session
        token to obtain the user access token and the ``id_token``. The user
        access token is then used to obtain the user's data, while the
        ``id_token`` is used to obtain the user's gtoken.

        Args:
            session_token (str): The session token.

        Returns:
            dict: The response from Nintendo's servers. This contains two keys
                of interest: ``access_token`` and ``id_token``. The
                ``access_token`` is used to obtain the user's data, while the
                ``id_token`` is used to obtain the user's gtoken.
        """
        header = {
            "Host": "accounts.nintendo.com",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "Content-Length": "436",
            "Accept": "application/json",
            "Connection": "Keep-Alive",
            "User-Agent": (
                "Dalvik/2.1.0 "
                "(Linux; U; Android "
                + ZNCA_PLATFORM_VERSION
                + "; Pixel 7a Build/UQ1A.240105.004)"
            ),
        }
        body = {
            "client_id": "71b963c1b7b6d119",
            "session_token": session_token,
            "grant_type": (
                "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token"
            ),
        }
        uri = "https://accounts.nintendo.com/connect/1.0.0/api/token"
        return self.session.post(uri, headers=header, json=body).json()

    def get_user_info(self, user_access_token: str) -> dict[str, str]:
        """Obtains the user information from the user access token.

        This method will obtain the user information from the user access token.
        This includes the user's set language, country, and birthday, which are
        used to obtain the user's ``gtoken``.

        Args:
            user_access_token (str): The user access token.

        Returns:
            dict[str, str]: The user information. This includes the user's set
                language, country, and birthday.
        """
        # Get user information
        url = "https://api.accounts.nintendo.com/2.0.0/users/me"
        header = {
            "User-Agent": "NASDKAPI; Android",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {user_access_token}",
            "Host": "api.accounts.nintendo.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        response = self.session.get(url, headers=header)
        return response.json()

    def get_gtoken(
        self, session_token: str, f_token_url: str | None = None
    ) -> str:
        """Obtains the ``gtoken`` from the session token.

        The GameWebToken, or ``gtoken``, is used to authenticate requests to the
        Nintendo Switch Online API. This method will obtain the ``gtoken`` from
        the session token. The process of obtaining a ``gtoken`` is as follows:

        1. Obtain the user access token and the ``id_token`` from the session
                token.
        2. Use the user access token to obtain the user's information.
        3. Use the ``id_token`` and the user's information to obtain the first
                ``f_token``, the request ID, and the timestamp.
        4. Use the first ``f_token``, the request ID, the timestamp, and the
                ``id_token`` to obtain the ``web_service_access_token``.
        5. Use the ``web_service_access_token`` to obtain the second
                ``f_token``, request ID, and timestamp.
        6. Use the second ``f_token``, request ID, timestamp, and the
                ``web_service_access_token`` to obtain the ``gtoken``.

        By default, this method will use a third party's ``f_token`` generation
        API to obtain the ``f_token``. The API used by default is provided by
        the `NXAPI znca service <https://nxapi-znca-api.fancy.org.uk/>`_. If you
        do not trust this URL, you can provide your own URL through the
        ``f_token_url`` argument, or
        you can replace the ``f_token`` generation method used with your own
        through the use of the ``set_new_f_token_function`` method. See the
        documentation for that method for more information.

        Args:
            session_token (str): The session token.
            f_token_url (str): The url to get the user access token from. This
                defaults to the ftoken generation url provided by NXAPI.

        Raises:
            NintendoException: In the case that the user's access token cannot
                be obtained from the session token, or the user's information
                that is returned is invalid.

        Returns:
            str: The gtoken. This is used to authenticate requests to the
                Nintendo Switch Online API. This token is valid for 2 hours.
        """
        f_token_url = f_token_url if f_token_url is not None else NXAPI_ZNCA_URL
        # Get user access token
        self.logger.info("Getting user access token")
        user_access_response = self.get_user_access_token(session_token)
        try:
            self._user_access_token = cast(
                str, user_access_response["access_token"]
            )
            self._id_token = cast(str, user_access_response["id_token"])
        except (KeyError, TypeError, AttributeError):
            raise NintendoException(
                "Failed to get user access token. "
                + f"Response: {user_access_response}"
            )

        self.logger.info("Getting user info")
        user_info = self.get_user_info(self._user_access_token)
        self._user_info = user_info
        self._nintendo_account_id = user_info["id"]
        self.logger.info("Getting Web Service Access Token")
        (
            web_service_access_token,
            coral_user_id,
        ) = self.g_token_generation_phase_1(
            self._id_token,
            user_info,
            self._nintendo_account_id,
            f_token_url=f_token_url,
        )
        self.logger.info("Getting gtoken")
        self._coral_user_id = coral_user_id
        gtoken = self.g_token_generation_phase_2(
            web_service_access_token,
            self._nintendo_account_id,
            self._coral_user_id,
            f_token_url=f_token_url,
        )
        self._gtoken = gtoken
        return gtoken

    def set_new_f_token_function(
        self, new_function: FToken_Gen | None = None
    ) -> None:
        """Sets the function used to generate the ``f_token``.

        This method will set the function used to generate the ``f_token``. The
        function must take the following arguments:

        1. The ``f_token`` generation url.
        2. The user's token, either the ``id_token`` for step ``1``, or the
            ``web_service_access_token`` for step ``2``.
        3. The step number (either ``1`` or ``2``)

        The function must return a tuple containing the following:

        1. The ``f_token``.
        2. The request id.
        3. The timestamp.

        Args:
            new_function (FToken_Gen): The new function to use to generate the
                ftoken. This function must take the following arguments:

                1. The ``f_token`` generation url.
                2. The user's token, either the ``id_token`` for step ``1``, or
                    the ``web_service_access_token`` for step ``2``.
                3. The step number (either ``1`` or ``2``)

                The function must return a tuple containing the following:

                1. The ``f_token``.
                2. The request id.
                3. The timestamp.

            If this argument is not provided or is ``None``, the default
            ``f_token`` generation method will be restored.
        """
        if new_function is None:
            self.logger.info("Restoring default ftoken generation method")
            self._f_token_function = self.get_ftoken
        else:
            self.logger.info("Setting new ftoken generation method")
            self._f_token_function = new_function

    def set_nxapi_client(self, client: "NXAPIClient" | None) -> None:
        """Attach or detach the helper used for nxapi-auth requests."""
        self._nxapi_client = client

    @staticmethod
    def _is_nxapi_url(url: str) -> bool:
        try:
            return urlparse(url).netloc == _NXAPI_HOST
        except ValueError:
            return False

    def get_ftoken(
        self,
        f_token_url: str,
        id_token: str,
        step: Literal[1] | Literal[2],
        na_id: str,
        coral_user_id: str | None = None,
        *,
        encrypt_request: dict | None = None,
    ) -> FTokenResult:
        """Given the ``f_token_url``, ``id_token``, and ``step``, returns
        an ``FTokenResult`` containing the ``f_token`` and optionally
        the ``request_id``, ``timestamp``, and ``encrypted_request``.

        When the f endpoint supports ``encrypt_token_request``, the
        response may include an ``encrypted_token_request`` field
        containing a pre-built encrypted Coral request body. In that
        case ``request_id`` and ``timestamp`` may be ``None``.

        Args:
            f_token_url (str): URL to use for ``f_token`` generation.
            id_token (str): ID token or web service access token.
            step (Literal[1] | Literal[2]): The step number.
            na_id (str): The Nintendo Account ID of the user.
            coral_user_id (str | None): The Coral user ID (required
                for step 2).
            encrypt_request (dict | None): Optional Coral parameter
                template to pass to the f endpoint for the
                ``encrypt_token_request`` flow.

        Raises:
            ValueError: ``coral_user_id`` not provided for step 2.
            FTokenException: If the ftoken cannot be obtained.

        Returns:
            FTokenResult: The f-token result.
        """
        header = {
            "User-Agent": f"splatnet3_scraper/{__version__}",
            "Content-Type": "application/json; charset=utf-8",
            "X-znca-Platform": "Android",
            "X-znca-Version": self.version,
        }

        if self._is_nxapi_url(f_token_url):
            if self._nxapi_client is None:
                raise FTokenException(
                    "nxapi client authentication is not configured"
                )
            header["X-znca-Client-Version"] = self._nxapi_client.client_version
            try:
                nxapi_headers = self._nxapi_client.build_request_headers()
            except NXAPIAuthException as exc:
                raise FTokenException(
                    f"Failed to authenticate with nxapi-auth: {exc}"
                ) from exc

            user_agent_override = nxapi_headers.pop("User-Agent", None)
            if user_agent_override:
                header["User-Agent"] = user_agent_override
            header.update(nxapi_headers)
            if not header.get("X-znca-Client-Version"):
                raise FTokenException(
                    "NXAPI client version is required when using "
                    "the default ftoken provider."
                )

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(
                "Posting to %s with headers %s",
                f_token_url,
                _sanitize_headers(header),
            )

        body: dict = {
            "token": id_token,
            "hash_method": step,
            "na_id": na_id,
        }

        if coral_user_id is not None:
            body["coral_user_id"] = f"{coral_user_id}"
        elif step == 2:
            raise ValueError(
                "Coral user ID is required for step 2 of ftoken generation"
            )

        if encrypt_request is not None:
            body["encrypt_token_request"] = encrypt_request

        response = self.session.post(f_token_url, headers=header, json=body)

        # Handle NXAPI-specific error responses
        if response.status_code != 200 and self._is_nxapi_url(f_token_url):
            debug_id = response.headers.get("X-Trace-Id", "unknown")
            try:
                error_json = response.json()
                error_code = error_json.get("error", "unknown_error")
                error_description = error_json.get("error_description", "")
            except ValueError:
                error_code = "unknown_error"
                error_description = response.text[:500]

            if (
                error_code == "invalid_request"
                and "Invalid X-znca-Client-Version header"
                in error_description
                and self._nxapi_client is not None
                and self._nxapi_client.client_version
                != NXAPI_DEFAULT_CLIENT_VERSION
            ):
                stale_version = self._nxapi_client.client_version
                self.logger.warning(
                    "NXAPI rejected client version %s; retrying with %s",
                    stale_version,
                    NXAPI_DEFAULT_CLIENT_VERSION,
                )
                self._nxapi_client.client_version = (
                    NXAPI_DEFAULT_CLIENT_VERSION
                )
                return self.get_ftoken(
                    f_token_url,
                    id_token,
                    step,
                    na_id,
                    coral_user_id,
                    encrypt_request=encrypt_request,
                )

            if error_code == "invalid_token":
                raise NXAPIInvalidTokenError(
                    message=("NXAPI token invalid: " + error_description),
                    error_code=error_code,
                    error_description=error_description,
                    debug_id=debug_id,
                    http_status=response.status_code,
                )
            elif error_code == "rate_limit":
                raise NXAPIRateLimitError(
                    message=("NXAPI rate limited: " + error_description),
                    error_code=error_code,
                    error_description=error_description,
                    debug_id=debug_id,
                    http_status=response.status_code,
                )
            elif error_code == "service_unavailable":
                raise NXAPIServiceUnavailableError(
                    message=("NXAPI service unavailable: " + error_description),
                    error_code=error_code,
                    error_description=error_description,
                    debug_id=debug_id,
                    http_status=response.status_code,
                )
            else:
                raise FTokenException(
                    f"NXAPI ftoken request failed "
                    f"({error_code}): {error_description} "
                    f"[debug_id: {debug_id}]"
                )

        try:
            response_json = response.json()
        except ValueError as exc:
            response_snippet = response.text[:500]
            self.logger.error(
                "ftoken provider %s returned non-JSON response (status=%s): %s",
                f_token_url,
                response.status_code,
                response_snippet,
            )
            raise FTokenException(
                "Failed to decode ftoken provider response "
                "as JSON. "
                + f"Status: {response.status_code}. "
                + f"Body: {response_snippet}"
            ) from exc

        f_token = response_json.get("f")
        if not f_token:
            self.logger.error(
                "ftoken provider %s returned an unexpected payload: %s",
                f_token_url,
                response_json,
            )
            raise FTokenException(
                "Failed to get f token. " + f"Response: {response_json}"
            )

        request_id = response_json.get("request_id")
        timestamp = response_json.get("timestamp")

        encrypted_request: bytes | None = None
        raw_encrypted = response_json.get("encrypted_token_request")
        if raw_encrypted is not None:
            encrypted_request = base64.b64decode(raw_encrypted)

        return FTokenResult(
            f=f_token,
            request_id=request_id,
            timestamp=timestamp,
            encrypted_request=encrypted_request,
        )

    @retry(times=1, exceptions=(FTokenException, NintendoException, KeyError))
    def g_token_generation_phase_1(
        self,
        id_token: str,
        user_info: dict[str, str],
        na_id: str,
        f_token_url: str,
    ) -> tuple[str, str]:
        """First phase of the ``gtoken`` generation process.

        Obtains the first ``f_token`` and uses it (or the encrypted
        Coral request from the f endpoint) to call Account/Login and
        retrieve the web service access token.

        Args:
            id_token (str): ID token from user access token response.
            user_info (dict[str, str]): User info with ``language``,
                ``birthday``, and ``country``.
            na_id (str): The Nintendo Account ID of the user.
            f_token_url (str): URL for f token generation.

        Returns:
            str: The Web Service Credential Access Token.
            str: The Coral user ID.
        """
        coral_url = CORAL_API_URL + CORAL_ACCOUNT_LOGIN_PATH

        # Build encrypt_request template when calling the
        # default get_ftoken and NXAPI client is configured
        use_encrypt = (
            self._nxapi_client is not None
            and self._f_token_function is self.get_ftoken
        )

        if use_encrypt:
            encrypt_req: dict | None = {
                "url": coral_url,
                "parameter": {
                    "f": "",
                    "language": user_info["language"],
                    "naBirthday": user_info["birthday"],
                    "naCountry": user_info["country"],
                    "naIdToken": id_token,
                    "requestId": "",
                    "timestamp": "",
                },
            }
            ftoken_result = self.get_ftoken(
                f_token_url,
                id_token,
                1,
                na_id,
                None,
                encrypt_request=encrypt_req,
            )
        else:
            result = self._f_token_function(
                f_token_url,
                id_token,
                1,
                na_id,
                None,
            )
            # Support both FTokenResult and legacy tuple
            if isinstance(result, FTokenResult):
                ftoken_result = result
            else:
                f, r, t = result
                ftoken_result = FTokenResult(
                    f=f,
                    request_id=r,
                    timestamp=t,
                )

        return self.get_web_service_access_token(
            id_token,
            user_info,
            ftoken_result.f,
            ftoken_result.request_id,
            ftoken_result.timestamp,
            encrypted_body=ftoken_result.encrypted_request,
        )

    @retry(times=1, exceptions=(FTokenException, NintendoException, KeyError))
    def g_token_generation_phase_2(
        self,
        web_service_access_token: str,
        na_id: str,
        coral_user_id: str,
        f_token_url: str,
    ) -> str:
        """Final phase of the ``gtoken`` generation process.

        Obtains the second ``f_token`` and uses it (or the encrypted
        Coral request) to call GetWebServiceToken and retrieve the
        gtoken.

        Args:
            web_service_access_token (str): The Web Service
                Credential Access Token from phase 1.
            na_id (str): The Nintendo Account ID of the user.
            coral_user_id (str): The Coral user ID.
            f_token_url (str): URL for f token generation.

        Returns:
            str: The gtoken from the response.
        """
        coral_url = CORAL_API_URL + CORAL_GET_WEB_SERVICE_TOKEN_PATH

        use_encrypt = (
            self._nxapi_client is not None
            and self._f_token_function is self.get_ftoken
        )

        if use_encrypt:
            encrypt_req: dict | None = {
                "url": coral_url,
                "token": web_service_access_token,
                "parameter": {
                    "f": "",
                    "id": 4834290508791808,
                    "registrationToken": (web_service_access_token),
                    "requestId": "",
                    "timestamp": "",
                },
            }
            ftoken_result = self.get_ftoken(
                f_token_url,
                web_service_access_token,
                2,
                na_id,
                coral_user_id,
                encrypt_request=encrypt_req,
            )
        else:
            result = self._f_token_function(
                f_token_url,
                web_service_access_token,
                2,
                na_id,
                coral_user_id,
            )
            if isinstance(result, FTokenResult):
                ftoken_result = result
            else:
                f, r, t = result
                ftoken_result = FTokenResult(
                    f=f,
                    request_id=r,
                    timestamp=t,
                )

        return self.get_gtoken_request(
            web_service_access_token,
            ftoken_result.f,
            ftoken_result.request_id,
            ftoken_result.timestamp,
            encrypted_body=ftoken_result.encrypted_request,
        )

    def get_web_service_access_token(
        self,
        id_token: str,
        user_info: dict[str, str],
        f_token: str,
        request_id: str | None,
        timestamp: str | int | None,
        *,
        encrypted_body: bytes | None = None,
    ) -> tuple[str, str]:
        """Given the ``id_token``, user data, ``f_token``,
        ``request_id``, and ``timestamp``, returns the Web Service
        Credential Access Token.

        If ``encrypted_body`` is provided (from the f endpoint's
        ``encrypt_token_request`` flow), it is sent directly to the
        Coral API, bypassing local body construction and encryption.

        Args:
            id_token (str): The ``id_token`` from the user access
                response.
            user_info (dict[str, str]): User info with ``language``,
                ``birthday``, and ``country``.
            f_token (str): The ``f_token`` from step 1.
            request_id (str | None): The ``request_id`` (may be None
                with encrypt_token_request).
            timestamp (str | int | None): The ``timestamp`` (may be
                None with encrypt_token_request).
            encrypted_body (bytes | None): Pre-encrypted Coral
                request body from the f endpoint.

        Raises:
            NintendoException: If the token cannot be obtained.

        Returns:
            str: The Web Service Credential Access Token.
            str: The coral user ID.
        """
        import json

        url = CORAL_API_URL + CORAL_ACCOUNT_LOGIN_PATH

        android_ver = ZNCA_PLATFORM_VERSION
        ua = (
            "com.nintendo.znca/"
            + self.version
            + "(Android/"
            + android_ver
            + ")"
        )

        if encrypted_body is not None:
            # Pre-encrypted body from encrypt_token_request
            assert self._nxapi_client is not None
            header = {
                "X-Platform": "Android",
                "X-ProductVersion": self.version,
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(encrypted_body)),
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "User-Agent": ua,
            }
            raw_response = self.session.post(
                url,
                headers=header,
                data=encrypted_body,
            )
            decrypted = self._nxapi_client.decrypt_response(
                decrypt_url=NXAPI_DECRYPT_URL,
                encrypted_data=raw_response.content,
            )
            response = json.loads(decrypted)
        elif self._nxapi_client is not None:
            # Use encrypt/decrypt via NXAPI client
            body = {
                "parameter": {
                    "f": f_token,
                    "language": user_info["language"],
                    "naBirthday": user_info["birthday"],
                    "naCountry": user_info["country"],
                    "naIdToken": id_token,
                    "requestId": request_id,
                    "timestamp": timestamp,
                }
            }
            enc_body = self._nxapi_client.encrypt_request(
                encrypt_url=NXAPI_ENCRYPT_URL,
                coral_url=url,
                token=None,
                data=json.dumps(body),
            )
            header = {
                "X-Platform": "Android",
                "X-ProductVersion": self.version,
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(enc_body)),
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "User-Agent": ua,
            }
            raw_response = self.session.post(
                url,
                headers=header,
                data=enc_body,
            )
            decrypted = self._nxapi_client.decrypt_response(
                decrypt_url=NXAPI_DECRYPT_URL,
                encrypted_data=raw_response.content,
            )
            response = json.loads(decrypted)
        else:
            # Unencrypted request (backward compatibility)
            body = {
                "parameter": {
                    "f": f_token,
                    "language": user_info["language"],
                    "naBirthday": user_info["birthday"],
                    "naCountry": user_info["country"],
                    "naIdToken": id_token,
                    "requestId": request_id,
                    "timestamp": timestamp,
                }
            }
            header = {
                "X-Platform": "Android",
                "X-ProductVersion": self.version,
                "Content-Type": ("application/json; charset=utf-8"),
                "Content-Length": str(990 + len(f_token)),
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "User-Agent": ua,
            }
            response = self.session.post(
                url,
                headers=header,
                json=body,
            ).json()

        if "result" not in response:
            raise NintendoException(
                "Failed to get web service access token. "
                + f"Response: {response}"
            )
        response_result = response["result"]
        return (
            response_result["webApiServerCredential"]["accessToken"],
            response_result["user"]["id"],
        )

    def get_gtoken_request(
        self,
        web_service_access_token: str,
        f_token: str,
        request_id: str | None,
        timestamp: str | int | None,
        *,
        encrypted_body: bytes | None = None,
    ) -> str:
        """Given the ``web_service_access_token``, ``f_token``,
        ``request_id``, and ``timestamp``, returns the ``gtoken``.

        If ``encrypted_body`` is provided (from the f endpoint's
        ``encrypt_token_request`` flow), it is sent directly.

        Args:
            web_service_access_token (str): The web service access
                token from phase 1.
            f_token (str): The ``f_token`` from step 2.
            request_id (str | None): The ``request_id`` (may be
                None).
            timestamp (str | int | None): The ``timestamp`` (may be
                None).
            encrypted_body (bytes | None): Pre-encrypted Coral
                request body from the f endpoint.

        Raises:
            NintendoException: If the ``gtoken`` cannot be obtained.

        Returns:
            str: The ``gtoken``.
        """
        import json

        url = CORAL_API_URL + CORAL_GET_WEB_SERVICE_TOKEN_PATH

        android_ver = ZNCA_PLATFORM_VERSION
        ua = f"com.nintendo.znca/{self.version}(Android/{android_ver})"

        if encrypted_body is not None:
            assert self._nxapi_client is not None
            header = {
                "X-Platform": "Android",
                "X-ProductVersion": self.version,
                "Authorization": (f"Bearer {web_service_access_token}"),
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(encrypted_body)),
                "Accept-Encoding": "gzip",
                "User-Agent": ua,
            }
            raw_response = self.session.post(
                url,
                headers=header,
                data=encrypted_body,
            )
            decrypted = self._nxapi_client.decrypt_response(
                decrypt_url=NXAPI_DECRYPT_URL,
                encrypted_data=raw_response.content,
            )
            response = json.loads(decrypted)
        elif self._nxapi_client is not None:
            body = {
                "parameter": {
                    "f": f_token,
                    "id": 4834290508791808,
                    "registrationToken": (web_service_access_token),
                    "requestId": request_id,
                    "timestamp": timestamp,
                }
            }
            enc_body = self._nxapi_client.encrypt_request(
                encrypt_url=NXAPI_ENCRYPT_URL,
                coral_url=url,
                token=web_service_access_token,
                data=json.dumps(body),
            )
            header = {
                "X-Platform": "Android",
                "X-ProductVersion": self.version,
                "Authorization": (f"Bearer {web_service_access_token}"),
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(enc_body)),
                "Accept-Encoding": "gzip",
                "User-Agent": ua,
            }
            raw_response = self.session.post(
                url,
                headers=header,
                data=enc_body,
            )
            decrypted = self._nxapi_client.decrypt_response(
                decrypt_url=NXAPI_DECRYPT_URL,
                encrypted_data=raw_response.content,
            )
            response = json.loads(decrypted)
        else:
            body = {
                "parameter": {
                    "f": f_token,
                    "id": 4834290508791808,
                    "registrationToken": (web_service_access_token),
                    "requestId": request_id,
                    "timestamp": timestamp,
                }
            }
            header = {
                "X-Platform": "Android",
                "X-ProductVersion": self.version,
                "Authorization": (f"Bearer {web_service_access_token}"),
                "Content-Type": ("application/json; charset=utf-8"),
                "Content-Length": "391",
                "Accept-Encoding": "gzip",
                "User-Agent": ua,
            }
            response = self.session.post(
                url,
                headers=header,
                json=body,
            ).json()

        if "result" not in response:
            raise NintendoException(
                "Failed to get gtoken. " + f"Response: {response}"
            )
        return response["result"]["accessToken"]

    def get_bullet_token(
        self,
        gtoken: str,
        user_info: dict,
        user_agent: str | None = None,
    ) -> str:
        """Given the ``gtoken`` and user information, send a request to SplatNet
        3 to obtain the bullet token. This token is required to make any
        requests to SplatNet 3, and is valid for 6 hours and 30 minutes after it
        is obtained.

        The gtoken is obtained by calling ``get_gtoken`` and the user
        information is obtained by calling ``get_user_info``. The user
        information must contain the keys ``language``, ``birthday``, and
        ``country`` and must align with the values set in the user's Nintendo
        account. The user agent is optional, and if not provided, the default
        user agent will be used. It is not recommended to change the user agent
        from the default unless you know what you are doing.

        Args:
            gtoken (str): GameWebToken, also known as gtoken. Given by Nintendo.
                This token is required to make any requests to Nintendo Switch
                Online services and is valid for 2 hours after it is obtained.
            user_info (dict): Dictionary containing the user's information. This
                must contain the keys ``language``, ``birthday``, and
                ``country`` and must align with the values set in the user's
                Nintendo account. These values are verified by Nintendo, so if
                they do not align, no bullet token will be generated.
            user_agent (str | None): User agent to use for the request. This is
                optional, and if not provided, the default user agent will be
                used. It is not recommended to change the user agent from the
                default unless you know what you are doing. The default user
                agent can be found in ``constants.py`` as
                ``DEFAULT_USER_AGENT``. Defaults to None.

        Raises:
            SplatNetException: Error 401, ``ERROR_INVALID_GAME_WEB_TOKEN``. This
                indicates that the gtoken is invalid. This can happen if the
                gtoken is expired or if the provided gtoken was never valid.
            SplatNetException: Error 403 ``ERROR_OBSOLETE_VERSION``. This
                indicates that the version provided in request header key
                ``X-Web-View-Ver`` is outdated. This can happen if the version
                provided is too old.
            SplatNetException: Error 204, ``USER_NOT_REGISTERED``. This
                indicates that there is no game user associated with Splatoon 3,
                and that the user must play at least one match of Splatoon 3
                before using this library.
            NintendoException: If the request does not fail with one of the
                above errors, this indicates that the request failed for some
                other reason and this exception will be raised to indicate that
                the request failed silently.

        Returns:
            str: The bullet token. This token is required to make any requests
                to SplatNet 3, and is valid for 6 hours and 30 minutes after it
                is obtained.
        """
        self.logger.info("Getting bullet token")
        user_agent = (
            user_agent if user_agent is not None else DEFAULT_USER_AGENT
        )
        header = {
            "Content-Length": "0",
            "Content-Type": "application/json",
            "Accept-Language": user_info["language"],
            "User-Agent": user_agent,
            "X-Web-View-Ver": self.splatnet_web_version,
            "X-NACOUNTRY": user_info["country"],
            "Accept": "*/*",
            "Origin": SPLATNET_URL,
            "X-Requested-With": "com.nintendo.znca",
        }
        cookies = {
            "_gtoken": gtoken,
            "_dnt": "1",
        }
        url = SPLATNET_URL + "/api/bullet_tokens"
        response = self.session.post(url, headers=header, cookies=cookies)

        if response.status_code == 401:
            raise SplatNetException(
                "Error 401: Invalid Game Web Token (gtoken)"
            )
        elif response.status_code == 403:
            raise SplatNetException("Error 403: Outdated Version")
        elif response.status_code == 204:
            raise SplatNetException(
                "Error 204: User Not Registered. Please play at least one match"
                + " of Splatoon 3 before using this library."
            )

        try:
            return response.json()["bulletToken"]
        except KeyError:
            raise NintendoException("Invalid response from Nintendo")

    @property
    def splatnet_web_version(self) -> str:
        """Get the web view version for SplatNet 3. This is used in the request
        header key ``X-Web-View-Ver`` to indicate the version of the web view
        that is being used. This is required to make any requests to SplatNet
        3. If the version cannot be obtained, a fallback version will be used.

        Returns:
            str: The web view version for SplatNet 3.
        """
        if self._web_view_version is not None:
            return self._web_view_version

        web_version = get_splatnet_version()
        self._web_view_version = web_version
        return web_version
