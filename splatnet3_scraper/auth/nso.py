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
        """Creates a new instance of the NSO class.

        The NSO class contains all the logic for obtaining an auth token from
        Nintendo. It also contains the session object that is used to make
        requests to the Nintendo Switch Online API, as well as the auth state
        and S256 code challenge used to obtain the auth token.

        Returns:
            NSO: A new instance of the NSO class.
        """
        session = requests.Session()
        return NSO(session=session)

    @property
    def version(self) -> str:
        """Returns the current version of the NSO app. Necessary to get the
        session token.

        Returns:
            str: The current version of the NSO app.
        """
        if self._version is None:
            self._version = self.get_version()
        return self._version

    @retry(times=2, exceptions=ValueError)
    def get_version(self) -> str:
        """Gets the current version of the NSO app. Necessary to access the API.
        Retries twice if the version cannot be obtained, in case the ios app
        store site is down or slow.

        Returns:
            str: The current version of the NSO app.
        """
        response = self.session.get(IOS_APP_URL)
        version = version_re.search(response.text)
        if version is None:
            logger.log("Failed to get version from app store, using fallback")
            return APP_VERSION_FALLBACK
        return version.group(0).strip()

    @property
    def state(self) -> bytes:
        """Returns a base64url encoded random 36 byte string for the auth state.

        Returns:
            bytes: The auth state.
        """
        if self._state is None:
            self._state = self.generate_new_state()
        return self._state

    def generate_new_state(self) -> bytes:
        """Generates a new state.

        Returns:
            bytes: The auth state.
        """
        return base64.urlsafe_b64encode(os.urandom(36))

    @property
    def verifier(self) -> bytes:
        """Returns a base64url encoded random 32 byte string for the code
        verifier. This is used to generate the S256 code challenge. To align
        with node.js's crypto module, padding is removed.

        Returns:
            bytes: The code verifier, without padding.
        """
        if self._verifier is None:
            self._verifier = self.generate_new_verifier()
        return self._verifier

    def generate_new_verifier(self) -> bytes:
        """Generates a new verifier without padding.

        Returns:
            bytes: The code verifier, without padding.
        """
        verifier_ = base64.urlsafe_b64encode(os.urandom(32))
        return verifier_.replace(b"=", b"")

    @property
    def session_token(self) -> str:
        if self._session_token is None:
            raise ValueError("Session token is not set.")
        return self._session_token

    def header(self, user_agent: str) -> dict[str, str]:
        """Returns the headers for the session.

        Args:
            user_agent (str): The user agent to use.

        Returns:
            dict[str, str]: The headers.
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
        """Log in to a Nintendo account and returns a session token.

        Args:
            user_agent (str): The user agent to use. Defaults to the default
                user agent found in constants.py.

        Returns:
            str: The session token.
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
            str: The session token code.
        """
        return uri.split("&")[1][len("session_token_code=") :]

    def get_session_token(self, session_token_code: str) -> str:
        """Gets the session token from the session token code.

        Args:
            session_token_code (str): The session token code.

        Returns:
            str: The session token.
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
        """Gets the user access token from the session token.

        Args:
            session_token (str): The session token.

        Returns:
            requests.Response: The response.
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
        """Gets the user information from the session token.

        Args:
            user_access_token (str): The user access token.

        Returns:
            dict[str, str]: The user information.
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
        """Gets the gtoken from the user access token.

        Args:
            f_token_url (str): The url to get the user access token from.
            session_token (str): The session token.

        Raises:
            NintendoException: If the user access token could not be retrieved.

        Returns:
            str: The gtoken.
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

        Args:
            f_token_url (str): URL to use for f token generation.
            id_token (str): ID token from user access token response.
            step (int): Step number, 1 or 2.

        Raises:
            FTokenException: If the f token cannot be retrieved.

        Returns:
            tuple:
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
        """Given the user access token response and user information, returns
        the response from the first step of f token generation. This step
        is retried once if it fails.

        Args:
            user_access_response (requests.Response): The response from the
                user access token request.
            user_info (dict[str, str]): The user information.
            f_token_url (str): The url to get the f token from.

        Returns:
            requests.Response: The response.
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
        """Final step of gtoken generation. This step is retried once if it
        fails.

        Args:
            id_token (str): splatoon id token
            f_token_url (str): The url to get the f token from.

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
        """Given the gtoken and user information, returns the bullet token.

        Bullet token is given by Splatnet and is required to access Splatnet.

        Args:
            gtoken (str): GameWebToken, also known as gtoken. Given by Nintendo.
            user_info (dict): User information. Given by Nintendo.
            user_agent (str | None): User agent. If None, the default user agent
                will be used. Defaults to None.

        Raises:
            SplatNetException: If the provided gtoken is invalid.
            SplatNetException: If the version of Splatnet is obsolete.
            SplatNetException: If no content is returned, indicating that the
                user has not accessed online services before.
            NintendoException: If Nintendo returns an invalid response.

        Returns:
            str: The bullet token.
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
            raise SplatNetException("Invalid gtoken")
        elif response.status_code == 403:
            raise SplatNetException("Obsolete Version")
        elif response.status_code == 204:
            raise SplatNetException("No Content")

        try:
            return response.json()["bulletToken"]
        except KeyError:
            raise NintendoException("Invalid response from Nintendo")

    @property
    def splatnet_web_version(self) -> str:
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
