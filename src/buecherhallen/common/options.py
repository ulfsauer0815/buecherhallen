import os


class Options:
    def __init__(self, cache_cookies: bool):
        self.cache_cookies = cache_cookies  # experimental, just for testing right now


def retrieve_options() -> Options:
    cache_cookies = get_bool_option('BH_CACHE_COOKIES', 'false')
    return Options(cache_cookies=cache_cookies)


def get_bool_option(env_name: str, default: bool) -> Options:
    value = os.getenv(env_name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes')
