import logging
import time
from typing import cast

import requests

from splatnet3_scraper.auth.exceptions import FTokenException, SplatNetException
from splatnet3_scraper.auth.graph_ql_queries import queries
from splatnet3_scraper.auth.nso import NSO
from splatnet3_scraper.auth.tokens.tokens import Token
from splatnet3_scraper.constants import (
    DEFAULT_USER_AGENT,
    GRAPH_QL_REFERENCE_URL,
    TOKENS,
)
from splatnet3_scraper.utils import retry

logger = logging.getLogger(__name__)


class TokenRegenerator:
    """Regenerates tokens. Only has static methods, so there is no need to
    instantiate this class.
    """

    @staticmethod
    def generate_gtoken(nso: NSO, f_token_urls: list[str]) -> Token:
        """Generates a gtoken from a list of ftoken urls.

        This method will try to generate a gtoken from each ftoken url in the
        list. If it fails to generate a gtoken from all of them, it will raise
        an exception. It will return the first gtoken it successfully generates.

        Args:
            nso (NSO): The NSO object to use to generate the gtoken.
            f_token_urls (list[str]): A list of ftoken urls to try to generate
                the gtoken from.

        Raises:
            FTokenException: If it fails to generate a gtoken from all of the
                ftoken urls.

        Returns:
            Token: The gtoken that was generated.
        """
        for f_token_url in f_token_urls:
            try:
                gtoken = nso.get_gtoken(nso.session_token, f_token_url)
                return Token(gtoken, TOKENS.GTOKEN, time.time())
            except FTokenException:
                continue
        raise FTokenException("Could not get gtoken from any ftoken url")

    @staticmethod
    @retry(times=1, exceptions=SplatNetException)
    def generate_bullet_token(
        nso: NSO, f_token_urls: list[str], user_agent: str = DEFAULT_USER_AGENT
    ) -> Token:
        """Generates a bullet token.

        This method will try to generate a bullet token. If a gtoken has not
        been generated, it will generate one from the list of ftoken urls. If
        the gtoken has been generated, it will attempt to use that to generate
        the bullet token. This method is wrapped in a retry decorator, so it
        will retry once if it fails the first time.

        Args:
            nso (NSO): The NSO object to use to generate the bullet token and
                any other tokens that are needed.
            f_token_urls (list[str]): A list of ftoken urls to try to generate
                the gtoken from if it has not already been generated.
            user_agent (str): The user agent to use when generating the bullet
                token. Defaults to DEFAULT_USER_AGENT.

        Returns:
            Token: The bullet token that was generated.
        """
        if nso._user_info is None:
            gtoken = TokenRegenerator.generate_gtoken(nso, f_token_urls).value
            user_info = cast(dict[str, str], nso._user_info)
        else:
            gtoken = cast(str, nso._gtoken)
            user_info = nso._user_info

        bullet_token = nso.get_bullet_token(gtoken, user_info, user_agent)
        return Token(bullet_token, TOKENS.BULLET_TOKEN, time.time())

    @staticmethod
    def generate_all_tokens(
        nso: NSO,
        f_token_urls: list[str],
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> dict[str, Token]:
        """
        Generates all tokens required for authentication.

        Args:
            nso (NSO): An instance of the NSO class.
            f_token_urls (list[str]): A list of URLs to fetch the f_token from.
            user_agent (str): The user agent string to use for the request.
                Defaults to DEFAULT_USER_AGENT.

        Returns:
            dict[str, Token]: A dictionary containing all the generated tokens.
        """
        logger.info("Generating all tokens")
        gtoken = TokenRegenerator.generate_gtoken(nso, f_token_urls)
        bullet_token = TokenRegenerator.generate_bullet_token(
            nso, f_token_urls, user_agent
        )
        return {TOKENS.GTOKEN: gtoken, TOKENS.BULLET_TOKEN: bullet_token}

    @staticmethod
    def validate_tokens(
        gtoken: Token,
        bullet_token: Token,
        nso: NSO,
        f_token_urls: list[str],
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> dict[str, Token]:
        """Validates the tokens.

        This method will check if the tokens are valid. If they are not valid,
        it will attempt to regenerate them. The tokens are returned in a
        dictionary with the token name as the key and the token as the value.

        Args:
            gtoken (Token): Gtoken to validate.
            bullet_token (Token): Bullet token to validate.
            nso (NSO): An instance of the NSO class. It must have the session
                token set.
            f_token_urls (list[str]): A list of URLs to fetch the f_token from.
            user_agent (str): The user agent string to use for the request.

        Returns:
            dict[str, Token]: A dictionary containing all the tokens.
        """
        logger.info("Testing tokens")
        if not gtoken.is_valid:
            gtoken = TokenRegenerator.generate_gtoken(nso, f_token_urls)
        if not bullet_token.is_valid:
            bullet_token = TokenRegenerator.generate_bullet_token(
                nso, f_token_urls, user_agent
            )

        header = queries.query_header(bullet_token.value, "en-US", user_agent)

        response = requests.post(
            GRAPH_QL_REFERENCE_URL,
            data=queries.query_body("HomeQuery"),
            headers=header,
            cookies={"_gtoken": gtoken.value},
        )
        if response.status_code != 200:
            return TokenRegenerator.generate_all_tokens(
                nso, f_token_urls, user_agent
            )
        return {TOKENS.GTOKEN: gtoken, TOKENS.BULLET_TOKEN: bullet_token}
