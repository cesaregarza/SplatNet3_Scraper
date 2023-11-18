import json
import logging
import pathlib
import time
from functools import lru_cache

import requests

from splatnet3_scraper.constants import GRAPH_QL_REFERENCE_URL

fallback_path = (
    pathlib.Path(__file__).parent.parent / "splatnet3_webview_data.json"
)


@lru_cache()
def get_hash_data(
    url: str | None = None, ttl_hash: int | None = None
) -> tuple[dict, str]:
    """Gets the hash data for the GraphQL queries with a time-to-live (TTL)
    cache.

    Uses requests to get the `imink` GraphQL query hash map JSON file and
    parses it to get the hashes for the queries. The initial request
    response contains two keys: ``hash_map`` and ``version``. Both of these
    are returned as a tuple, with the first element being the ``hash_map``
    and the second element being the ``version``.

    Args:
        url (str | None): The URL to get the hash data from. If None, the
            default URL will be used, from `imink`. This can be found in the
            ``GRAPH_QL_REFERENCE_URL`` variable. Defaults to None.
        ttl_hash (int | None): The hash to use for the TTL cache. This is used
            to determine if the cache should be used or not. The hash is
            calculated by dividing the current time by the expiry time in
            seconds and rounding to the nearest integer. If None, the default
            expiry time of 15 minutes will be used. Note that this method of TTL
            caching does not guarantee that the cache will be invalidated after
            the expiry time, but it is a good enough approximation. Defaults to
            None.

    Returns:
        dict[str, str]: The hash map for the GraphQL queries.
        str: The version of the hash map.
    """
    del ttl_hash

    request_url = url or GRAPH_QL_REFERENCE_URL
    response = requests.get(request_url).json()
    return response["graphql"]["hash_map"], response["version"]


def get_ttl_hash(expiry_time_seconds: float = 15 * 60) -> int:
    return round(time.time() / expiry_time_seconds)


@lru_cache()
def get_fallback_hash_data() -> tuple[dict, str]:
    """Gets the fallback hash data for the GraphQL queries.

    Loads the fallback hash data from the ``splatnet3_webview_data.json`` file
    and parses it to get the hashes for the queries.

    Returns:
        tuple[dict, str]:
            dict: The hash map for the GraphQL queries.
            str: The version of the hash map.
    """
    with open(fallback_path, "r") as f:
        FALLBACK_DATA = json.load(f)

    return FALLBACK_DATA["graphql"]["hash_map"], FALLBACK_DATA["version"]


def get_splatnet_hashes(url: str | None = None) -> dict[str, str]:
    """Gets the hashes for the GraphQL queries.

    Uses requests to get the `imink` GraphQL query hash map JSON file and
    parses it to get the hashes for the queries. The initial request
    response contains two keys: ``hash_map`` and ``version``. The
    ``hash_map`` key is the dictionary that contains the hashes for the
    queries and is what is returned by this method. The `version` key is the
    version of the hashes and is used to check if the hashes are up to date,
    it is used elsewhere in this package, but is not used here.

    Args:
        url (str | None): The URL to get the hash data from. If None, the
            default URL will be used, from `imink`. This can be found in the
            ``GRAPH_QL_REFERENCE_URL`` constant.

    Returns:
        dict[str, str]: The hashes for the GraphQL queries. The keys are
            the names of the queries and the values are the most up to date
            hashes for the queries.

    # noqa: DAR401 ValueError
    """
    try:
        hash_data, _ = get_hash_data(url, get_ttl_hash())
        # If the hash data is empty, use the fallback
        if not hash_data:
            raise ValueError("Hash data is empty")
    except Exception as e:
        logging.warning(f"Failed to get hash data: {e}")
        logging.warning("Using fallback")
        return get_fallback_hash_data()[0]
    return hash_data


def get_splatnet_version(url: str | None = None) -> str:
    """Gets the version of the GraphQL queries.

    Uses requests to get the `imink` GraphQL query hash map JSON file and
    parses it to get the version of the queries. The initial request
    response contains two keys: ``hash_map`` and ``version``. The
    ``version`` key is the version of the hashes and is what is returned by
    this method. The `hash_map` key is the dictionary that contains the
    hashes for the queries and is used elsewhere in this package, but is not
    used here.

    Args:
        url (str | None): The URL to get the hash data from. If None, the
            default URL will be used, from `imink`. This can be found in the
            ``GRAPH_QL_REFERENCE_URL`` constant.

    Returns:
        str: The version of the GraphQL queries.

    # noqa: DAR401 ValueError
    """
    try:
        hash_data, version = get_hash_data(url, get_ttl_hash())
        # If the hash data is empty, use the fallback
        if not hash_data:
            raise ValueError("Hash data is empty")
    except Exception as e:
        logging.warning(f"Failed to get hash data: {e}")
        logging.warning("Using fallback")
        return get_fallback_hash_data()[1]
    return version
