import json
import logging
import pathlib
import re
import time
from functools import lru_cache, wraps
from typing import Any, Callable, ParamSpec, Type, TypeAlias, TypeVar, cast

import requests

from splatnet3_scraper.constants import GRAPH_QL_REFERENCE_URL

T = TypeVar("T")
P = ParamSpec("P")

PathType: TypeAlias = str | int | tuple[str | int, ...]

json_splitter_re = re.compile(r"[\;\.]")

fallback_path = pathlib.Path(__file__).parent / "splatnet3_webview_data.json"


def retry(
    times: int,
    exceptions: tuple[Type[Exception], ...] | Type[Exception] = Exception,
    call_on_fail: Callable[[], None] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that retries a function a specified number of times if it
    raises a specific exception or tuple of exceptions.

    Args:
        times (int): Max number of times to retry the function before raising
            the exception.
        exceptions (tuple[Type[Exception], ...] | Type[Exception]): Exception
            or tuple of exceptions to catch. Defaults to Exception.
        call_on_fail (Callable[[], None] | None): Function to call if the
            function fails. If None, nothing will be called. Defaults to None.

    Returns:
        Callable[[Callable[P, T]], Callable[P, T]]: The decorated function,
            which will retry the function if it raises an exception.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    logging.warning(
                        "%s failed on attempt %d of %d, retrying.",
                        func.__name__,
                        i + 1,
                        times + 1,
                    )
                    if call_on_fail is not None:
                        logging.debug("Calling %s...", call_on_fail.__name__)
                        call_on_fail()

            return func(*args, **kwargs)

        return wrapper

    return decorator


def linearize_json(
    json_data: dict[str, Any]
) -> tuple[tuple[str, ...], list[Any]]:
    """Linearizes a JSON object. Given a JSON object, this function will
    return a tuple of keys and values. Turns a JSON object into a table.

    Given a JSON object, this function will return a tuple of keys and values.
    The keys will be a tuple of strings, and the values will be a list of
    values. The keys will be the path to the value in the JSON object, and the
    values will be the values of the JSON object. For example, given the
    following JSON object:

    >>> json_data = {
    ...     "a": 1,
    ...     "b": {
    ...         "c": 2,
    ...         "d": 3,
    ...     },
    ...     "e": [4, 5],
    ... }

    The function will return the following tuple:

    >>> linearize_json(json_data)
    ... (
    ...     ("a", "b.c", "b.d", "e;0", "e;1"),
    ...     [1, 2, 3, 4, 5],
    ... )

    Args:
        json_data (dict[str, Any]): The JSON object to linearize.

    Returns:
        tuple[str, ...]: The keys of the JSON object. The keys are in the
            format of "key1.key2;index1.key3" where the semicolon indicates a
            list and the period indicates a nested object.
        list[Any]: The values of the JSON object. The values are in the same
            order as the keys.
    """
    keys = []
    values = []

    for key, value in json_data.items():
        if isinstance(value, dict):
            sub_keys, sub_values = linearize_json(value)
            keys.extend([(key + "." + sub_key) for sub_key in sub_keys])
            values.extend(sub_values)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    sub_keys, sub_values = linearize_json(item)
                    keys.extend(
                        [
                            (key + ";" + str(i) + "." + sub_key)
                            for sub_key in sub_keys
                        ]
                    )
                    values.extend(sub_values)
                else:
                    keys.append(key + ";" + str(i))
                    values.append(item)
        else:
            keys.append(key)
            values.append(value)

    # Turn the keys into an immutable tuple so it can be hashed
    out_keys = tuple(keys)
    return out_keys, values


def delinearize_json(
    keys: list[str] | tuple[str, ...], values: list[Any]
) -> dict[str, Any]:
    """Delinearizes a JSON object. Given a list of keys and a list of values,
    this function will return a JSON object. Turns a table into a JSON object.

    Given a list of keys and a list of values, this function will return a
    JSON object. The keys are expected to be in the format of
    "key1.key2;index1.key3" where the semicolon indicates a list and the
    period indicates a nested object. The values are expected to be in the
    same order as the keys.

    Args:
        keys (list[str]): The keys of the JSON object. The keys are expected
            to be in the format of "key1.key2;index1.key3" where the semicolon
            indicates a list and the period indicates a nested object.
        values (list[Any]): The values of the JSON object. The values are
            expected to be in the same order as the keys.

    Returns:
        dict[str, Any]: The JSON object created from the keys and values.
    """
    json_data = {}

    # Sort the keys by depth
    depths = [len(json_splitter_re.split(key)) for key in keys]
    kvd = list(zip(keys, values, depths))
    kvd = sorted(kvd, key=lambda x: (x[2], x[0]))
    keys, values, _ = list(zip(*kvd))

    # Delinearize
    for key, value in zip(keys, values):
        # If the key is split by a period, it's a nested object. If it's split
        # by a semicolon, it's a list. Check which one is first.
        subkeys = json_splitter_re.split(key)
        splitters = json_splitter_re.findall(key)
        if len(subkeys) == 1:
            json_data[key] = value
            continue
        # If the key is split by a semicolon, turn the next key value into an
        # integer
        for i, splitter in enumerate(splitters):
            if splitter == ";":
                subkeys[i + 1] = int(subkeys[i + 1])

        current = json_data
        for i, splitter in enumerate(splitters):
            # If the key already exists, move on to the next key
            if isinstance(current, (list, dict)):
                chosen_subkey = subkeys[i]
                if isinstance(current, list):
                    condition = len(current) > chosen_subkey
                elif isinstance(current, dict):
                    condition = chosen_subkey in current

                if condition:
                    next_obj = current[chosen_subkey]
                    # Next object might be None as an artifact of header merging
                    if next_obj is not None:
                        current = next_obj
                        continue
            new_obj: dict | list = {} if (splitter == ".") else []

            # Append or assign the new object to the current object depending
            # on type.
            if isinstance(current, list):
                current.append(new_obj)
            elif isinstance(current, dict):
                current[subkeys[i]] = new_obj
            # Mypy doesn't like that this is dynamically typed, so we have to
            # ignore it. This is python, not C.
            current = new_obj  # type: ignore
        if isinstance(current, list):
            current.append(value)
        else:
            current[subkeys[-1]] = value

    return json_data


def enumerate_all_paths(data: dict | list | Any) -> list[tuple[str | int, ...]]:
    """Recursively enumerates all paths in the given data.

    Given a dictionary or list, returns a list of all paths in the data. For
    example, given the following data:

    >>> data = {
    ...     "a": 1,
    ...     "b": {
    ...         "c": 2,
    ...         "d": [3, 4],
    ...     },
    ... }

    The following paths would be returned:

    >>> enumerate_all_paths(data)
    ... [
    ...     ("a",),
    ...     ("b",),
    ...     ("b", "c"),
    ...     ("b", "d"),
    ...     ("b", "d", 0),
    ...     ("b", "d", 1),
    ... ]

    If the given data is not a dictionary or list, an empty list is returned.

    Args:
        data (dict | list | Any): The data to enumerate. If the data is not a
            dictionary or list, an empty list is returned. Otherwise, the
            function recurses into the data.

    Returns:
        list[tuple[str | int, ...]]: A list of all paths in the given data.
    """
    paths: list[tuple[str | int, ...]] = []

    if not isinstance(data, (dict, list)):
        return paths

    members = data.items() if isinstance(data, dict) else enumerate(data)

    for key, value in members:
        key_tuple = (cast(str | int, key),)
        paths.append(key_tuple)
        subpaths = enumerate_all_paths(value)
        for subpath in subpaths:
            paths.append(key_tuple + subpath)

    return paths


def match_partial_path(
    data: dict[str, Any] | list, partial_path: PathType | list[PathType]
) -> list[tuple[str | int, ...]]:
    """Returns a list of all paths in the given data that match the given
    partial path. For example, if partial_path is ``(0, "key1")``, this will
    return all paths in the data that match ``...[0]["key1"]``. If fed a list
    of partial paths, this will return all paths that match any of the partial
    paths. Do not confuse tuples with lists, as they are treated differently.

    The ":" string can be added to the partial path input to match all list
    indices that match it. This is useful for JSONs with a repeating structure.

    The match_partial_path algorithm searches for all paths in a dictionary that
    match the given partial path. The ``partial_path`` can be a string, integer,
    a special ":" string, or a tuple of strings/integers that represents the
    path to an item in the dictionary. For example, the path
    ``("key1", "key2", 2)`` corresponds to ``...["key1"]["key2"][2]`` in the
    dictionary. The algorithm returns a list of all paths that match the
    ``partial_path``. Each path in the result is represented as a tuple of
    strings and integers where strings correspond to dictionary keys and
    integers correspond to list indices.

    For instance, if ``data`` is:

    >>> data = {
    ...     "key1": {
    ...         "key2": [
    ...             {"key3": 1},
    ...             {"key3": 2},
    ...         ]
    ...     },
    ...     "key4": {
    ...         "key5": [
    ...             {"key3": 3},
    ...             {"key3": 4},
    ...         ]
    ...     }
    ... }

    Then ``match_partial_path(data, (0, "key3"))`` will return:

    >>> [
    ...     ("key1", "key2", 0, "key3"),
    ...     ("key4", "key5", 0, "key3"),
    ... ]

    If ``match_partial_path(data, "key3")`` is called, the result will be:

    >>> [
    ...     ("key1", "key2", 0, "key3"),
    ...     ("key1", "key2", 1, "key3"),
    ...     ("key4", "key5", 0, "key3"),
    ...     ("key4", "key5", 1, "key3"),
    ... ]

    If ``match_partial_path(data, [(0, "key3"), "key2"])`` is called, the result
    will be:

    >>> [
    ...     ("key1", "key2", 0, "key3"),
    ...     ("key4", "key5", 0, "key3"),
    ...     ("key1", "key2"),
    ... ]

    If ``match_partial_path(data, ("key1", "key2", ":", "key3"))`` is called,
    the result will be:

    >>> [
    ...     ("key1", "key2", 0, "key3"),
    ...     ("key1", "key2", 1, "key3"),
    ... ]

    Args:
        data (dict[str, Any] | list): The dictionary or list to search.
        partial_path (PathType | list[PathType]): The partial path to match. If
            the partial path is a tuple, this function will treat it as a path.
            For example, a ``partial_path`` argument of ``(0, "key1")`` will be
            treated  as ``...[0]["key1"]``. If the partial path is a string,
            this function will treat it as a key in a dictionary. Integers will
            be treated as indices in a list. If the partial path is a list, this
            function will return all paths that match any of the partial paths.
            The special ":" string can be used to match all list indices that
            match the rest of the partial path. This is useful to get all paths
            in a list that match a given partial path.

    Returns:
        list[tuple[str | int, ...]]: A list of all paths that match the given
            partial path. Each path is represented as a tuple of strings and
            integers, where strings correspond  to dictionary keys and integers
            correspond to list indices.
    """
    if isinstance(partial_path, list):
        short_circuit: list[tuple[str | int, ...]] = []
        for path in partial_path:
            short_circuit.extend(match_partial_path(data, path))
        return short_circuit

    if isinstance(partial_path, (str, int)):
        partial_path = (partial_path,)
    partial_path = tuple(partial_path)

    # Check if the partial path contains the ":" character, which is used to
    # denote to allow all indices in a list. If it does, then we need to
    # enumerate all paths in the data and filter out the ones that match the
    # partial path.
    branching_points = len([i for i, x in enumerate(partial_path) if x == ":"])

    # If the partial path is empty, return an empty list
    paths = enumerate_all_paths(data)
    out: list[tuple[str | int, ...]] = []

    if branching_points == 0:
        for path in paths:
            if path[-len(partial_path) :] == partial_path:
                out.append(path)

        return out

    # If the partial path contains the ":" character, then we need to
    # enumerate all paths in the data and filter out the ones that match the
    # partial path.
    for path in paths:
        add_path = True
        truncated_path = path[-len(partial_path) :]
        if len(truncated_path) < len(partial_path):
            continue
        for idx, value in enumerate(partial_path):
            if value == truncated_path[idx]:
                continue
            elif value == ":":
                if isinstance(truncated_path[idx], int):
                    continue

            add_path = False
            break
        if add_path:
            out.append(path)

    return out


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
