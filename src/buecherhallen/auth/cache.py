import json
import logging

import requests
from common.constants import COOKIES_FILE
from requests.cookies import RequestsCookieJar


def cache_cookies(cookies: RequestsCookieJar):
    logging.info("Caching cookie jar")
    cookies_dict = requests.utils.dict_from_cookiejar(cookies)
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies_dict, f, indent=2)


def load_cookies() -> RequestsCookieJar | None:
    logging.info("Searching cookies jar in cache")
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies_dict = json.load(f)
        cookies_jar = requests.utils.cookiejar_from_dict(cookies_dict)
        return cookies_jar
    except FileNotFoundError:
        logging.info("No cookies jar found in cache")
        return None


def load_cached_cookies():
    cached_cookies = load_cookies()
    if cached_cookies:
        logging.info("Found cookie jar in cache")
    return cached_cookies
