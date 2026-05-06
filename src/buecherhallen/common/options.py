import os
from typing import Optional


class Options:
    def __init__(
        self,
        list_name: str,
        cache_cookies: bool,
        headless: bool,
        retries: int,
        workers: int,
        video_dir: Optional[str],
    ):
        self.list_name = list_name
        self.cache_cookies = cache_cookies  # experimental, just for testing right now
        self.headless = headless
        self.retries = retries
        self.workers = workers
        self.video_dir = video_dir


def retrieve_options() -> Options:
    list_name = __get_str_option("BH_LIST_NAME", "Merkliste")
    cache_cookies = __get_bool_option("BH_CACHE_COOKIES", False)
    headless = __get_bool_option("BH_HEADLESS", True)
    retries = __get_int_option("BH_RETRIES", 1)
    workers = __get_int_option("BH_WORKERS", 3)
    raw_video_dir = __get_optional_str_option("BH_VIDEO_DIR")
    video_dir = __resolve_video_dir(raw_video_dir) if raw_video_dir else None
    return Options(
        list_name=list_name,
        cache_cookies=cache_cookies,
        headless=headless,
        retries=retries,
        workers=workers,
        video_dir=video_dir,
    )


def __get_str_option(env_name: str, default: str) -> str:
    value = os.getenv(env_name)
    if value is None:
        return default
    return value


def __get_bool_option(env_name: str, default: bool) -> bool:
    value = os.getenv(env_name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes")


def __get_int_option(env_name: str, default: int) -> int:
    value = os.getenv(env_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def __get_optional_str_option(env_name: str) -> Optional[str]:
    value = __get_str_option(env_name, "").strip()
    return value if value else None


def __resolve_video_dir(value: str) -> str:
    if os.path.isdir(value):
        if not os.access(value, os.W_OK):
            raise ValueError(f"Directory '{value}' is not writable")
        return value

    parent = os.path.dirname(os.path.abspath(value))
    if not parent or not os.path.isdir(parent):
        raise ValueError(f"Neither '{value}' nor its parent directory exist")

    try:
        os.makedirs(value, exist_ok=True)
    except OSError as e:
        raise ValueError(f"Failed to create directory '{value}': {e}") from e

    return value
