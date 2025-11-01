import os


class Options:
    def __init__(self, cache_cookies: bool, headless: bool, retries: int) -> None:
        self.cache_cookies = cache_cookies  # experimental, just for testing right now
        self.headless = headless
        self.retries = retries


def retrieve_options() -> Options:
    cache_cookies = __get_bool_option('BH_CACHE_COOKIES', False)
    headless = __get_bool_option('BH_HEADLESS', True)
    retries = __get_int_option('BH_RETRIES', 1)
    return Options(cache_cookies=cache_cookies, headless=headless, retries=retries)


def __get_bool_option(env_name: str, default: bool) -> bool:
    value = os.getenv(env_name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes')


def __get_int_option(env_name: str, default: int) -> int:
    value = os.getenv(env_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default
