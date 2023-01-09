import base64
import hashlib
import json
import os

import requests
from bs4 import BeautifulSoup

from s3s_express import __version__
from s3s_express.constants import DEFAULT_USER_AGENT, IOS_APP_URL
from s3s_express.utils import retry


class NintendoException(Exception):
    """Base class for all Nintendo exceptions."""

    pass


class IminkException(Exception):
    """Base class for all Imink exceptions."""

    pass


class NSO:
    def __init__(self, session: requests.Session) -> None:
        self.session = session
        self._state: bytes | None = None
        self._verifier: bytes | None = None
        self._version: str | None = None

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

    def get_version(self) -> str:
        """Gets the current version of the NSO app. Necessary to access the API.

        Returns:
            str: The current version of the NSO app.
        """
        response = self.session.get(IOS_APP_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        version = (
            soup.find("p", class_="whats-new__latest__version")
            .get_text()[7:]
            .strip()
        )
        return version

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
        response = self.session.get(login_url, headers=header, params=params)
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
        return response.json()["session_token"]

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

    def get_gtoken(self, f_token_url: str, session_token: str) -> str:
        """Gets the gtoken from the user access token.

        Args:
            f_token_url (str): The url to get the user access token from.
            session_token (str): The session token.

        Returns:
            str: The gtoken.
        """
        # Get user access token
        user_access_response = self.get_user_access_token(session_token)
        user_access_json = user_access_response.json()
        try:
            user_access_token = user_access_json["access_token"]
            id_token = user_access_json["id_token"]
        except (KeyError, TypeError, AttributeError):
            raise NintendoException(
                "Failed to get user access token. "
                + f"Response: {user_access_json}"
            )

        user_info = self.get_user_info(user_access_token)
        splatoon_response = self.f_token_generation_step_1(
            user_access_response, user_info, f_token_url
        )
        id_token = splatoon_response.json()["result"]["webApiServerCredential"][
            "accessToken"
        ]
        return id_token

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
            IminkException: If the f token cannot be retrieved.

        Returns:
            tuple:
                str: The f token.
                str: The request ID.
                str: The timestamp.
        """
        header = {
            "User-Agent": f"s3s_express/{__version__}",
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
            raise IminkException(
                "Failed to get f token. " + f"Response: {response_json}"
            )
        return (f_token, request_id, timestamp)

    @retry(times=1, exceptions=(IminkException, NintendoException, KeyError))
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

        Raises:
            IminkException: If the f token cannot be retrieved.

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
