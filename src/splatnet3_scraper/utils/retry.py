import logging
from functools import wraps
from typing import Callable, Literal, ParamSpec, Type, TypeAlias, TypeVar

T = TypeVar("T")
P = ParamSpec("P")

Backoff: TypeAlias = Literal["fixed", "exponential", "fibonacci"]


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
