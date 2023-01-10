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
