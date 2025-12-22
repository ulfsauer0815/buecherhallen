import os


class Options:
    def __init__(
            self,
            list_name: str,
            cache_cookies: bool,
            headless: bool,
            retries: int,
            workers: int,
    ):
        self.list_name = list_name
        self.cache_cookies = cache_cookies  # experimental, just for testing right now
        self.headless = headless
        self.retries = retries
        self.workers = workers


def retrieve_options() -> Options:
    list_name = __get_str_option('BH_LIST_NAME', "Merkliste")
    cache_cookies = __get_bool_option('BH_CACHE_COOKIES', False)
    headless = __get_bool_option('BH_HEADLESS', True)
    retries = __get_int_option('BH_RETRIES', 1)
    workers = __get_int_option('BH_WORKERS', 3)
    return Options(
        list_name=list_name,
        cache_cookies=cache_cookies,
        headless=headless,
        retries=retries,
        workers=workers,
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
    return value.lower() in ('1', 'true', 'yes')


def __get_int_option(env_name: str, default: int) -> int:
    value = os.getenv(env_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default
