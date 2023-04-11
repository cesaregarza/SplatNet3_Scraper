import logging
import re
from functools import cache, wraps
from typing import Any, Callable, ParamSpec, Type, TypeAlias, TypeVar, cast

import requests

from splatnet3_scraper.constants import GRAPH_QL_REFERENCE_URL

T = TypeVar("T")
P = ParamSpec("P")

PathType: TypeAlias = str | int | tuple[str | int, ...]

json_splitter_re = re.compile(r"[\;\.]")


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
        Callable[[Callable[P, T]], Callable[P, T]]: Decorator.
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


@cache
def get_splatnet_web_version() -> str:
    """Gets the web view version from the GraphQL reference.

    Returns:
        str: The web view version.
    """
    response = requests.get(GRAPH_QL_REFERENCE_URL)
    return response.json()["version"]


def linearize_json(
    json_data: dict[str, Any]
) -> tuple[tuple[str, ...], list[Any]]:
    """Linearizes a JSON object.

    Args:
        json_data (dict[str, Any]): The JSON object to linearize.

    Returns:
        tuple:
            tuple[str, ...]: The keys of the JSON object.
            list[Any]: The values of the JSON object.
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
    """Delinearizes a JSON object.

    Args:
        keys (list[str]): The keys of the JSON object.
        values (list[Any]): The values of the JSON object.

    Returns:
        dict[str, Any]: The JSON object.
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

    Args:
        data (dict | list | Any): The data to enumerate.

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

    The match_partial_path algorithm searches for all paths in a dictionary that
    match the given partial path. The ``partial_path`` can be a string, integer
    or a tuple of strings/integers that represents the path to an item in the
    dictionary. For example, the path ``("key1", "key2", 2)`` corresponds to
    ``...["key1"]["key2"][2]`` in the dictionary. The algorithm returns a list
    of all paths that match the ``partial_path``. Each path in the result is
    represented as a tuple of strings and integers where strings correspond to
    dictionary keys and integers correspond to list indices.

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

    And if ``match_partial_path(data, [(0, "key3"), "key2"])`` is called, the
    result will be:

    >>> [
    ...     ("key1", "key2", 0, "key3"),
    ...     ("key1", "key2"),
    ...     ("key4", "key5", 0, "key3"),
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

    # If the partial path is empty, return an empty list
    paths = enumerate_all_paths(data)
    out: list[tuple[str | int, ...]] = []

    for path in paths:
        if path[-len(partial_path) :] == partial_path:
            out.append(path)

    return out
