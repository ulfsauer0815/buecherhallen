import os


class Options:
    def __init__(self, cache_cookies: bool, headless: bool) -> None:
        self.cache_cookies = cache_cookies  # experimental, just for testing right now
        self.headless = headless


def retrieve_options() -> Options:
    cache_cookies = __get_bool_option('BH_CACHE_COOKIES', False)
    headless = __get_bool_option('BH_HEADLESS', True)
    return Options(cache_cookies=cache_cookies, headless=headless)


def __get_bool_option(env_name: str, default: bool) -> Options:
    value = os.getenv(env_name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes')
