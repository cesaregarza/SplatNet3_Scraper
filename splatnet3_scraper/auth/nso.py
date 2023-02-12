import base64
import hashlib
import json
import os
import re
from typing import cast

import requests

from splatnet3_scraper import __version__
from splatnet3_scraper.auth.exceptions import (
    FTokenException,
    NintendoException,
    SplatNetException,
)
from splatnet3_scraper.constants import (
    APP_VERSION_FALLBACK,
    DEFAULT_USER_AGENT,
    IMINK_URL,
    IOS_APP_URL,
    SPLATNET_URL,
    WEB_VIEW_VERSION_FALLBACK,
)
from splatnet3_scraper.logs import logger
from splatnet3_scraper.utils import get_splatnet_web_version, retry

version_re = re.compile(
    r"(?<=whats\-new\_\_latest\_\_version\"\>Version)\s+\d+\.\d+\.\d+"
)


class NSO:
    """The NSO class contains all the logic to proceed through the login flow.
    This class also holds various properties that are used to make requests to
    the Nintendo Switch Online API. Login flow is roughly as follows:

        1.  Initialize a requests session and store it.
        2.  Generate a random state and S256 code challenge that will be used
                to obtain the "session_token". Store them for later use.
        3.  Generate a login URL using the state and code challenge that the
                user will open in their browser. The user will then copy a link
                and feed it back to the program.
        4.  Parse the URI to obtain the session token code, then use it
                alongside the code challenge to obtain the "session_token".
                Store it for later use. The session token is valid for 2 years
                and can be revoked by the user.
        5.  Use the session token to obtain a user access response. Store it for
                later use. The user access response contains two tokens: an "id"
                token and a "user access" token.
        6.  Use the user access token to obtain the user information. This is
                required to obtain the "f" token. Store it for later use.
        7.  Use the user information to obtain an "f" token using the first
                hashing method. This will also return a request ID and a
                timestamp. These do not need to be stored.
        8.  Use the "f" token, user information, and the id token to obtain a
                splatoon token. This token will contain a new "id" token.
        9.  Use the new "id" token to obtain the g token using the second
                hashing method. Store it for later use. The g token is valid for
                6 hours and 30 minutes.
        10. Use the g token and user information to obtain a bullet token. This
                token is valid for 2 hours.

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
        self._gtoken: str | None = None
        self._user_info: dict[str, str] | None = None

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

        Returns:
            str: The current version of the NSO app.
        """
        if self._version is None:
            self._version = self.get_version()
        return self._version

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
            logger.log("Failed to get version from app store, using fallback")
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

    def header(self, user_agent: str) -> dict[str, str]:
        """Generates the headers used within the Nintendo Switch Online
        authentication flow. These are important to ensure that the requests do
        not get rejected by Nintendo's servers. The only value that this method
        does not set is the ``User-Agent`` header, as this is set by the user.

        The following is a list of the headers that are set by this method:

        >>> {
        ...     "Host": "accounts.nintendo.com",
        ...     "Connection": "keep-alive",
        ...     "Cache-Control": "max-age=0",
        ...     "Upgrade-Insecure-Requests": "1",
        ...     "User-Agent": user_agent,
        ...     "Accept": (
        ...         "text/html,"
        ...         + "application/xhtml+xml,"
        ...         + "application/xml;q=0.9,"
        ...         + "image/webp,"
        ...         + "image/apng,"
        ...         + "*/*;q=0.8"
        ...     ),
        ...     "Accept-Encoding": "gzip, deflate, br",
        ... }

        Args:
            user_agent (str): The user agent to use. Any user agent can be used,
            but it is recommended to use the default user agent provided by
            ``splatnet3_scraper.constants.DEFAULT_USER_AGENT``.

        Returns:
            dict[str, str]: The headers to use for the Nintendo Switch Online
            requests.
        """
        return {
            "Host": "accounts.nintendo.com",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": user_agent,
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

        header = self.header(
            user_agent=user_agent
            if user_agent is not None
            else DEFAULT_USER_AGENT
        )
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
            login_url, headers=header, params=params  # type: ignore
        )
        return response.url

    def parse_npf_uri(self, uri: str) -> str:
        """Parses the uri returned by the Nintendo login page and extracts the
        session token code. This is used to pass the challenge and verify that
        the user is who they say they are.

        Args:
            uri (str): The uri returned by the Nintendo login page.

        Returns:
            str: The session token code. This is *NOT* the session token, but is
            used to obtain the session token.
        """
        return uri.split("&")[1][len("session_token_code=") :]

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

    def get_user_access_token(self, session_token: str) -> requests.Response:
        """Obtains the user access token from the session token.

        This method will obtain the user access token from the session token.

        Args:
            session_token (str): The session token.

        Returns:
            requests.Response: The response from Nintendo's servers. This is
            *NOT* the user access token, the full response is returned since it
            contains more information than just the user access token that is
            used elsewhere in the authentication process, specifically the
            ``id_token`` which is used to obtain the user's gtoken.
        """
        header = {
            "Host": "accounts.nintendo.com",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "Content-Length": "436",
            "Accept": "application/json",
            "Connection": "Keep-Alive",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2)",
        }
        body = {
            "client_id": "71b963c1b7b6d119",
            "session_token": session_token,
            "grant_type": (
                "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token"
            ),
        }
        uri = "https://accounts.nintendo.com/connect/1.0.0/api/token"
        return self.session.post(uri, headers=header, json=body)

    def get_user_info(self, user_access_token: str) -> dict[str, str]:
        """Obtains the user information from the user access token.

        This method will obtain the user information from the user access token.
        This includes the user's set language, country, and birthday, which are
        used to obtain the user's gtoken.

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
        """Obtains the gtoken from the session token.

        The GameWebToken, or gtoken, is used to authenticate requests to the
        Nintendo Switch Online API. This method will obtain the gtoken from the
        session token. The process of obtaining a gtoken is as follows:

        1. Obtain the user access token from the session token.
        2. Obtain the user information from the user access token.
        3. Use the user information to obtain an ftoken from the provided ftoken
              url.
        4. Use the ftoken to obtain the gtoken.

        The ftoken generation url is provided by a third party. The methods
        within this class do not provide any additional identifying information
        to the ftoken generation URL other than the user's `id_token`, which
        cannot be used to identify the user without the user's access token,
        which is not provided to the ftoken generation URL. If you do not trust
        the ftoken generation URL, you can provide your own ftoken generation
        URL, or you can subclass this class to provide your own ftoken
        generation method. The default ftoken generation URL used by this
        library is provided by `imink <https://github.com/imink-app>`_.

        Args:
            session_token (str): The session token.
            f_token_url (str): The url to get the user access token from. This
                defaults to the ftoken generation url provided by `imink`.

        Raises:
            NintendoException: In the case that the user's access token cannot
                be obtained from the session token, or the user's information
                that is returned is invalid.

        Returns:
            str: The gtoken. This is used to authenticate requests to the
            Nintendo Switch Online API. This token is valid for 2 hours.
        """
        f_token_url = f_token_url if f_token_url is not None else IMINK_URL
        # Get user access token
        user_access_response = self.get_user_access_token(session_token)
        user_access_json = user_access_response.json()
        try:
            self._user_access_token = cast(
                str, user_access_json["access_token"]
            )
            self._id_token = user_access_json["id_token"]
        except (KeyError, TypeError, AttributeError):
            raise NintendoException(
                "Failed to get user access token. "
                + f"Response: {user_access_json}"
            )

        user_info = self.get_user_info(self._user_access_token)
        self._user_info = user_info
        splatoon_response = self.f_token_generation_step_1(
            user_access_response, user_info, f_token_url
        )
        id_token = splatoon_response.json()["result"]["webApiServerCredential"][
            "accessToken"
        ]
        gtoken = self.f_token_generation_step_2(id_token, f_token_url)
        self._gtoken = gtoken
        return gtoken

    def get_ftoken(
        self, f_token_url: str, id_token: str, step: int
    ) -> tuple[str, str, str]:
        """Given the f_token_url, id_token, and step, returns the f_token,
        request_id, and timestamp from the response.

        Note that this is a third party method, and is not officially
        sanctioned by Nintendo. The default ftoken generation URL used by this
        library is provided by `imink <https://github.com/imink-app>`_. In
        the interest of transparency, the following is the entirety of the
        request header sent to the ftoken generation URL:

        >>> {
        ...     "User-Agent": f"splatnet3_scraper/{__version__}",
        ...     "Content-Type": "application/json; charset=utf-8",
        ... }

        The following is the entirety of the request body sent to the ftoken
        generation URL:

        >>> {
        ...     "token": id_token,
        ...     "hash_method": step,
        ... }

        As you can see, the only identifying information sent to the ftoken
        generation URL is the user's `id_token`, which cannot be used to
        identify the user without the user's access token, which is not
        provided to the ftoken generation URL.

        Args:
            f_token_url (str): URL to use for f token generation. This package
                provides a default URL, but you can provide your own. The
                default URL is provided by `imink`.
            id_token (str): ID token from user access token response. This is
                obtained from the user access token response, and is used to
                identify the user. This cannot be used to identify the user
                without the user's access token, which is not provided to the
                ftoken generation URL.
            step (int): Step number, 1 or 2. This is used by the ftoken
                generation URL to determine which step to perform.

        Raises:
            FTokenException: In the case that the ftoken cannot be obtained
                from the ftoken generation URL.

        Returns:
            str: The f token.
            str: The request ID.
            str: The timestamp.
        """
        header = {
            "User-Agent": f"splatnet3_scraper/{__version__}",
            "Content-Type": "application/json; charset=utf-8",
        }
        body = {
            "token": id_token,
            "hash_method": step,
        }
        bodystr = json.dumps(body)
        response = self.session.post(f_token_url, headers=header, data=bodystr)
        response_json = response.json()
        try:
            f_token = response_json["f"]
            request_id = response_json["request_id"]
            timestamp = response_json["timestamp"]
        except (KeyError, TypeError, AttributeError):
            raise FTokenException(
                "Failed to get f token. " + f"Response: {response_json}"
            )
        return (f_token, request_id, timestamp)

    @retry(times=1, exceptions=(FTokenException, NintendoException, KeyError))
    def f_token_generation_step_1(
        self,
        user_access_response: requests.Response,
        user_info: dict[str, str],
        f_token_url: str,
    ) -> requests.Response:
        """Given the user access token response and the dictionary of user info
        returned by `get_user_info`, returns the response from the first step
        of the f token generation process. This step is retried once if it
        fails. This step is used to get the `splatoon_token` from Nintendo's
        servers, which is used to get the `gtoken`. This step is retried once if
        it fails before raising an exception.

        Args:
            user_access_response (requests.Response): The response from the user
                access token request. A different object can be passed in for
                this parameter, but it must have a `json` method that returns a
                dictionary with a `id_token` key that maps to the id token
                provided by Nintendo.
            user_info (dict[str, str]): The dictionary of user info returned by
                `get_user_info`. This must contain the keys `language`,
                `birthday`, and `country`.
            f_token_url (str): URL to use for f token generation. This package
                provides a default URL, but you can provide your own. The
                default URL is provided by `imink`.

        Returns:
            requests.Response: The response containing the `splatoon_token`.
            This response contains a JSON with the following path to the token:
            `result.webApiServerCredential.accessToken`.
        """
        id_token = user_access_response.json()["id_token"]
        f_token, request_id, timestamp = self.get_ftoken(
            f_token_url, id_token, 1
        )

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
        splatoon_response = self.get_splatoon_token(body)
        # Check if the response is valid
        splatoon_response.json()["result"]["webApiServerCredential"][
            "accessToken"
        ]
        return splatoon_response

    @retry(times=1, exceptions=(FTokenException, NintendoException, KeyError))
    def f_token_generation_step_2(
        self,
        id_token: str,
        f_token_url: str,
    ) -> str:
        """Final step of gtoken generation, which returns the gtoken. This step
        is retried once if it fails. This step obtains the second f token, which
        is passed to Nintendo's servers to get the gtoken. This step is retried
        once if it fails before raising an exception.

        Args:
            id_token (str): The id token from the first step of the f token
                generation process. This will be renamed in a future version of
                this package, so that it is not confused with the id token from
                the user access token response. As such, it is preferred to pass
                this parameter as a positional and not a keyword argument.
            f_token_url (str): URL to use for f token generation. This package
                provides a default URL, but you can provide your own. The
                default URL is provided by `imink`.

        Returns:
            str: The gtoken from the response.
        """
        f_token, request_id, timestamp = self.get_ftoken(
            f_token_url, id_token, 2
        )

        header = {
            "X-Platform": "Android",
            "X-ProductVersion": self.version,
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "391",
            "Accept-Encoding": "gzip",
            "User-Agent": f"com.nintendo.znca/{self.version}(Android/7.1.2)",
        }
        body = {
            "parameter": {
                "f": f_token,
                "id": 4834290508791808,
                "registrationToken": id_token,
                "requestId": request_id,
                "timestamp": timestamp,
            }
        }
        url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
        response = self.session.post(url, headers=header, json=body).json()
        gtoken = cast(str, response["result"]["accessToken"])
        return gtoken

    def get_splatoon_token(self, body: dict) -> requests.Response:
        """Given the body of the request to get the splatoon token, returns the
        response from Nintendo's servers containing the splatoon token.

        The body of the request must contain the following keys:
        >>> body = {
        ...     "parameter": {
        ...         "f": f_token,
        ...         "language": user_info["language"],
        ...         "naBirthday": user_info["birthday"],
        ...         "naCountry": user_info["country"],
        ...         "requestId": request_id,
        ...         "timestamp": timestamp,
        ...     }
        ... }

        Where `f_token`, `request_id`, and `timestamp` are the f token, request
        id, and timestamp returned by `get_ftoken`. The `user_info` dictionary
        must contain the keys `language`, `birthday`, and `country` and must
        align with the values set in the user's Nintendo account.

        Args:
            body (dict): The body of the request to get the splatoon token. This
                must be a dictionary with the keys `parameter` and `f` as shown
                above.

        Returns:
            requests.Response: The response from Nintendo's servers containing
            the splatoon token. This response contains a JSON with the following
            path to the token:
            `result.webApiServerCredential.accessToken`.
        """
        f_token = body["parameter"]["f"]
        header = {
            "X-Platform": "Android",
            "X-ProductVersion": self.version,
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(990 + len(f_token)),
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "com.nintendo.znca/"
            + self.version
            + "(Android/7.1.2)",
        }
        url = "https://api-lp1.znc.srv.nintendo.net/v3/Account/Login"
        return self.session.post(url, headers=header, json=body)

    def get_bullet_token(
        self,
        gtoken: str,
        user_info: dict,
        user_agent: str | None = None,
    ) -> str:
        """Given the gtoken and user information, send a request to SplatNet 3
        to obtain the bullet token. This token is required to make any requests
        to SplatNet 3, and is valid for 6 hours and 30 minutes after it is
        obtained.

        The gtoken is obtained by calling `get_gtoken` and the user information
        is obtained by calling `get_user_info`. The user information must
        contain the keys `language`, `birthday`, and `country` and must align
        with the values set in the user's Nintendo account. The user agent is
        optional, and if not provided, the default user agent will be used. It
        is not recommended to change the user agent from the default unless you
        know what you are doing.

        Args:
            gtoken (str): GameWebToken, also known as gtoken. Given by Nintendo.
                This token is required to make any requests to Nintendo Switch
                Online services and is valid for 2 hours after it is obtained.
            user_info (dict): Dictionary containing the user's information. This
                must contain the keys `language`, `birthday`, and `country` and
                must align with the values set in the user's Nintendo account.
                These values are verified by Nintendo, so if they do not align,
                no bullet token will be generated.
            user_agent (str | None): User agent to use for the request. This is
                optional, and if not provided, the default user agent will be
                used. It is not recommended to change the user agent from the
                default unless you know what you are doing. The default user
                agent can be found in `constants.py` as `DEFAULT_USER_AGENT`.
                Defaults to None.

        Raises:
            SplatNetException: Error 401, `ERROR_INVALID_GAME_WEB_TOKEN`. This
                indicates that the gtoken is invalid. This can happen if the
                gtoken is expired or if the provided gtoken was never valid.
            SplatNetException: Error 403 `ERROR_OBSOLETE_VERSION`. This
                indicates that the version provided in request header key
                `X-Web-View-Ver` is outdated. This can happen if the version
                provided is too old.
            SplatNetException: Error 204, `USER_NOT_REGISTERED`. This indicates
                that there is no game user associated with Splatoon 3, and that
                the user must play at least one match of Splatoon 3 before
                using this library.
            NintendoException: If the request does not fail with one of the
                above errors, this indicates that the request failed for some
                other reason and this exception will be raised to indicate that
                the request failed silently.

        Returns:
            str: The bullet token. This token is required to make any requests
            to SplatNet 3, and is valid for 6 hours and 30 minutes after it is
            obtained.
        """
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
        header key `X-Web-View-Ver` to indicate the version of the web view
        that is being used. This is required to make any requests to SplatNet
        3. If the version cannot be obtained, a fallback version will be used.

        Returns:
            str: The web view version for SplatNet 3.
        """
        if self._web_view_version is not None:
            return self._web_view_version
        try:
            web_version = get_splatnet_web_version()
            self._web_view_version = web_version
            return web_version
        except SplatNetException as e:
            logger.log(str(e), "warning")
            logger.log("Using fallback web view version", "warning")
            return WEB_VIEW_VERSION_FALLBACK
