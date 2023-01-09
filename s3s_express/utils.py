import time
import warnings
from typing import Callable, ParamSpec, Type, TypeVar

from s3s_express import logger

T = TypeVar("T")
P = ParamSpec("P")


def retry(
    times: int,
    exceptions: tuple[Type[Exception], ...] | Type[Exception] = Exception,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that retries a function a specified number of times if it
    raises a specific exception or tuple of exceptions.

    Args:
        times (int): Max number of times to retry the function before raising
            the exception.
        exceptions (tuple[Type[Exception], ...] | Type[Exception]): Exception
            or tuple of exceptions to catch. Defaults to Exception.

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
            return func(*args, **kwargs)

        return wrapper

    return decorator


def expiring_property(
    *args: int | float | None,
    seconds: int | float | None = None,
    minutes: int | float | None = None,
    hours: int | float | None = None,
    days: int | float | None = None,
    behavior: str = "raise",
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that makes a property expire after a specific amount of time.
    Only accepts one positional argument which will be interpreted as seconds.

    Given a property, this decorator will make it expire after a user-specified
    amount of time. The behavior of the property after it expires can be
    specified by the user. The following behaviors are available:
        raise (default): Raises a TimeoutError
        return: Returns None
        warn: Raises a warning
        log: Logs a message and returns None
        ignore: Does nothing, functionally equivalent to "return"

    Args:
        seconds (int | float | None): Number of seconds before timeout
            occurs. Defaults to None.
        minutes (int | float | None): Number of minutes before timeout
            occurs. Defaults to None.
        hours (int | float | None): Number of hours before timeout occurs.
            Defaults to None.
        days (int | float | None): Number of days before timeout occurs.
            Defaults to None.
        behavior (str): Behavior when the property is accessed after the
            expiration time. Defaults to "raise". Other options are "return",
            "warn", "log", and "ignore".

    Raises:
        ValueError: If more than one positional argument is passed.
        ValueError: If no arguments are passed.
        ValueError: If both positional and keyword arguments are passed.
        ValueError: Unforeseen error, this should never happen but is here
            to help debug if it does.

    Returns:
        Callable[[Callable[P, T]], Callable[P, T]: Decorator.
    """

    behavior = behavior.lower()
    if behavior not in ("return", "warn", "log", "raise", "ignore"):
        raise ValueError(
            "behavior must be one of 'return', 'warn', 'log', 'raise', or"
            " 'ignore'."
        )
    if len(args) > 1:
        raise ValueError(
            "expiring_property takes at most 1 positional argument."
        )

    num_args = 4 - (seconds, minutes, hours, days).count(None)

    if num_args == 0 and len(args) == 0:
        raise ValueError("expiring_property takes at least 1 argument.")

    if len(args) == 1 and num_args >= 1:
        raise ValueError(
            "Positional and keyword arguments cannot be used together."
        )
    elif len(args) == 1 and args[0] is not None:
        expiration = args[0]
    elif num_args >= 1:
        time_mults: list[tuple[int | float | None, int]] = [
            (seconds, 1),
            (minutes, 60),
            (hours, 60 * 60),
            (days, 60 * 60 * 24),
        ]
        expiration = 0
        for arg, mult in time_mults:
            if arg is not None:
                expiration += arg * mult
    else:
        raise ValueError("Unknown error. (This should never happen.)")

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # metadata = {"expiration": expiration, "timestamp": time.time()}
        timestamp = time.time()

        @property
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if time.time() - timestamp < expiration:
                return func(*args, **kwargs)
            else:
                msg = f"Property {func.__name__} has expired."
                if behavior == "return":
                    return None
                elif behavior == "warn":
                    warnings.warn(msg)
                elif behavior == "log":
                    logger.log(msg)
                elif behavior == "raise":
                    raise TimeoutError(msg)
                elif behavior == "ignore":
                    pass

        return wrapper

    return decorator
