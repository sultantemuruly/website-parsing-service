import os


def env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(int(raw_value), minimum)
    except ValueError:
        return default


CRAWL_MAX_IN_FLIGHT = env_int("CRAWL_MAX_IN_FLIGHT", 1, minimum=1)
CRAWL_QUEUE_TIMEOUT_MS = env_int("CRAWL_QUEUE_TIMEOUT_MS", 1_000, minimum=1)
