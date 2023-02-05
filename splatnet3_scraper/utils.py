import re
from functools import cache
from typing import Any, Callable, ParamSpec, Type, TypeVar

import requests

from splatnet3_scraper.constants import GRAPH_QL_REFERENCE_URL
from splatnet3_scraper.logs import logger

T = TypeVar("T")
P = ParamSpec("P")

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
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    logger.log(
                        f"{func.__name__} failed on attempt {i + 1} of "
                        f"{times + 1}, retrying."
                    )
                    if call_on_fail is not None:
                        logger.log(f"Calling {call_on_fail.__name__}...")
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
