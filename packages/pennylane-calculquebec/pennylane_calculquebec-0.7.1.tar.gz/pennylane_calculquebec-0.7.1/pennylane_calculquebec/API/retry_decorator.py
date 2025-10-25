from time import sleep
import warnings


def retry(
    retries: int = 10,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
):
    """A decorator to retry a function call with exponential backoff.

    Args:
        retries (int): The maximum number of retries before giving up. Default is 10.
        initial_delay (float): The initial delay in seconds before the first retry. Default is 0.1 seconds.
        backoff_factor (float): The factor by which the delay increases after each retry. Default is 2.0.
    Returns:
        function: The decorated function that will be retried on failure.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay

            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < retries:
                        warnings.warn(
                            f"The request failed. \nThis was caused by inner exception: \n{e}\nRetrying in {delay} seconds...",
                            stacklevel=2,
                        )
                        sleep(delay)
                        delay *= backoff_factor
                    else:
                        warnings.warn(
                            f"The request failed after {retries} retries. \nThis was caused by inner exception: \n{e}",
                            stacklevel=2,
                        )
                        raise e
            return func(*args, **kwargs)

        return wrapper

    return decorator
