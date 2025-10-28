import json
import logging

from common.constants import COOKIES_FILE
from requests.cookies import RequestsCookieJar

log = logging.getLogger(__name__)


def cache_cookies(cookies: RequestsCookieJar):
    log.info("Caching cookie jar")

    cookies_list = []
    for cookie in cookies:
        cookies_list.append({
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path,
            "expires": cookie.expires,
            "secure": cookie.secure,
            "rest": cookie._rest,
        })

    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies_list, f, indent=2)


def load_cookies() -> RequestsCookieJar | None:
    log.info("Searching cookies jar in cache")
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies_list = json.load(f)
        cookies_jar = RequestsCookieJar()
        for cookie in cookies_list:
            cookies_jar.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain"),
                path=cookie.get("path"),
                expires=cookie.get("expires"),
                secure=cookie.get("secure", False),
                rest=cookie.get("rest", {}),
            )

        return cookies_jar
    except FileNotFoundError:
        log.info("No cookies jar found in cache")
        return None


def log_cookies(cookies: RequestsCookieJar):
    for cookie in cookies:
        log.debug(
            f"Cookie: {cookie.name}={cookie.value[:10]}...; Domain={cookie.domain}; Path={cookie.path}; Expires={cookie.expires}; Secure={cookie.secure}; Rest={cookie._rest}")
