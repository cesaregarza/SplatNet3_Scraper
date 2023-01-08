import time
from typing import Callable, ParamSpec, TypeVar

from s3s_express import logger

T = TypeVar("T")
P = ParamSpec("P")


def retry(
    times: int, exceptions: tuple[Exception, ...] | Exception = Exception
) -> Callable[P, T]:
    """Decorator that retries a function a specified number of times if it
    raises a specific exception or tuple of exceptions.

    Args:
        times (int): Max number of times to retry the function before raising
            the exception.
        exceptions (tuple[Exception, ...] | Exception, optional): Exception or
            tuple of exceptions to catch. Defaults to Exception.

    Returns:
        Callable[P, T]: Decorated function.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    logger.log(
                        f"{func.__name__} failed on attempt {i + 1} of {times},"
                        " retrying."
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def expiring_property(
    *args: tuple,
    seconds: int | float | None = None,
    minutes: int | float | None = None,
    hours: int | float | None = None,
    days: int | float | None = None,
) -> Callable[P, T]:
    """Decorator that makes a property expire after a specific amount of time.

    Given a property, this decorator will make it expire after a user-specified
    amount of time. The property will raise a TimeoutError if it is accessed
    after the expiration time has passed.

    Args:
        seconds (int | float | None): Number of seconds before timeout
            occurs. Defaults to None.
        minutes (int | float | None): Number of minutes before timeout
            occurs. Defaults to None.
        hours (int | float | None): Number of hours before timeout occurs.
            Defaults to None.
        days (int | float | None): Number of days before timeout occurs.
            Defaults to None.

    Raises:
        ValueError: If more than one positional argument is passed.
        ValueError: If more than one keyword argument is passed.
        ValueError: If no arguments are passed.
        ValueError: If both positional and keyword arguments are passed.
        TimeoutError: If the property is accessed after the expiration time.

    Returns:
        Callable[P, T]: Decorated property.
    """
    if len(args) > 1:
        raise ValueError(
            "expiring_property takes at most 1 positional argument."
        )

    num_args = 4 - (seconds, minutes, hours, days).count(None)
    if num_args > 1:
        raise ValueError("expiring_property takes at most 1 keyword argument.")

    if num_args == 0 and len(args) == 0:
        raise ValueError("expiring_property takes at least 1 argument.")

    if len(args) == 1:
        if num_args == 1:
            raise ValueError(
                "Positional and keyword arguments cannot be used together."
            )
        expiration = args[0]
    elif seconds is not None:
        expiration = seconds
    elif minutes is not None:
        expiration = minutes * 60
    elif hours is not None:
        expiration = hours * 60 * 60
    elif days is not None:
        expiration = days * 60 * 60 * 24

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        metadata = {"expiration": expiration, "timestamp": time.time()}

        @property
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if time.time() - metadata["timestamp"] < metadata["expiration"]:
                return func(*args, **kwargs)
            else:
                raise TimeoutError("Property has expired.")

        return wrapper

    return decorator
