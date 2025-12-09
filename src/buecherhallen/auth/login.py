import logging
import re
import time

import playwright.sync_api
import requests
from camoufox.sync_api import Camoufox
from playwright.sync_api import (
    Page
)
from requests.cookies import RequestsCookieJar

from buecherhallen.auth.bot_protection import solve_cloudflare
from buecherhallen.auth.cache import cache_cookies, load_cookies
from buecherhallen.auth.credentials import Credentials
from buecherhallen.common.constants import LOGIN_URL, BASE_HOSTNAME

log = logging.getLogger(__name__)

EXPIRY_BUFFER_SECONDS = 5 * 60  # 5 minutes

# global variable to hold the next-action header value :S
__turnstile_login_action: str | None = None


class LoginError(Exception):
    pass


def __check_login_success(cookies: RequestsCookieJar):
    if 'luci_session' not in cookies:
        log.error("luci_session cookie not found after login")
        raise LoginError("luci_session cookie not found, login has failed")

    luci_session_cookie = __get_cookie(cookies, 'luci_session')
    expiry = luci_session_cookie.expires
    if expiry is None:
        log.warning("Cached luci_session cookie has no expiry, might be invalid")
        return

    current_time = time.time()
    log.debug(f"luci_session cookie expiry: {expiry}, in {expiry - current_time} seconds")
    is_expired = expiry is not None and (expiry - EXPIRY_BUFFER_SECONDS) < current_time
    if is_expired:
        log.info("luci_session cookie is expired")
        raise LoginError("luci_session cookie is expired, login has failed")


def login(credentials: Credentials, use_cache: bool = False, headless: bool = True) -> RequestsCookieJar:
    if use_cache:
        log.warning("Cache usage is experimental and might not work as expected!")
        log.info("Checking for cached cookies")
        cached_cookies = load_cookies()
        if cached_cookies:
            try:
                __check_login_success(cached_cookies)
                return cached_cookies
            except LoginError:
                log.info("Cached cookies are invalid, proceeding to login")

    log.info("Starting login process")

    turnstile_token = None
    try:
        with Camoufox(os=["windows", "macos", "linux"], humanize=True, headless=headless) as browser:
            page = browser.new_page()
            __disable_cookie_banner(page)
            page.on("response", __find_nextjs_next_action)

            page.goto(LOGIN_URL)
            page.wait_for_load_state(state="domcontentloaded")
            page.wait_for_load_state('networkidle')

            turnstile_token = solve_cloudflare(page)

        cookie_jar_after_login = __login_with_token(credentials, turnstile_token, __turnstile_login_action)

        if use_cache:
            cache_cookies(cookie_jar_after_login)
        return cookie_jar_after_login

    except Exception as e:
        log.error(f"Login failed: {str(e)}")
        raise LoginError("Login process failed") from e


def __disable_cookie_banner(page: Page):
    cookies = [{
        'name': 'luci_CC_28d4dc2f-692b-472b-870d-5e6c35c4ad26',
        'value': 'true',
        'domain': BASE_HOSTNAME,
        'path': '/',
    }, {
        'name': 'luci_gaConsent_28d4dc2f-692b-472b-870d-5e6c35c4ad26',
        'value': 'false',
        'domain': BASE_HOSTNAME,
        'path': '/',
    }]
    page.context.add_cookies(cookies)


def __enter_credentials_and_login(page: Page, credentials: Credentials) -> None:
    page.fill('input#bNumber', credentials.username)
    page.fill('input#pin', credentials.password)
    page.click('input#remember-me', force=True)

    # submit the form
    page.click('#main-content button[type="submit"]')


def extract_cookie_jar(page: Page) -> RequestsCookieJar:
    cookies = page.context.cookies()
    cookie_jar = RequestsCookieJar()
    for cookie in cookies:
        cookie_jar.set(
            name=cookie['name'],
            value=cookie['value'],
            domain=cookie.get('domain', ''),
            path=cookie.get('path', '/'),
            expires=cookie.get('expires'),
            secure=cookie.get('secure', False),
            rest={'HttpOnly': cookie.get('httpOnly', False)}
        )
    return cookie_jar


def __get_cookie(cookies: RequestsCookieJar, name: str):
    for cookie in cookies:
        if cookie.name == name:
            return cookie
    return None


def __find_nextjs_next_action(response: playwright.sync_api.Response):
    global __turnstile_login_action
    re_match = re.match(r'https://www2\.buecherhallen\.de/_next/static/chunks/app/layout-[a-z0-9]+\.js', response.url)

    if not re_match:
        return
    log.debug(f"Layout JS file response found: {response.url}")

    if not response.ok:
        log.error(f"Failed to load JS file for next-action determination: {response.status}")
        raise LoginError("Failed to load layout JS file for next-action determination")

    log.debug("Layout JS file loaded successfully")
    body = response.body()
    log.debug(f"Layout JS response: {body}")
    pattern = re.compile(rb'\("([a-f0-9]{42})",d.callServer,void 0,d.findSourceMapURL,"turnstileLogin"\)')
    match = pattern.search(body)
    if match:
        token = match.group(1).decode('utf-8')
        log.info(f"Found 'next-action' hash for the login: {token}")
        __turnstile_login_action = token
    else:
        log.error("Failed to find 'next-action' hash in layout JS file")


def __login_with_token(credentials: Credentials, turnstile_token: str, next_action: str) -> RequestsCookieJar:
    log.info("Submitting login form with Turnstile token")
    if not next_action:
        log.error("'next-action' hash is missing, cannot proceed with login")
        raise LoginError("'next-action' hash is missing, cannot proceed with login")

    payload = [{
        "userID": f"{credentials.username}",
        "password": credentials.password,
        "hvToken": turnstile_token,
        "keepIn": True
    }, False]

    response = requests.post(
        LOGIN_URL,
        headers={
            'next-action': next_action,
        },
        json=payload,
    )

    if response.status_code != 200:
        log.error(f"Login request failed with status code: {response.status_code}")
        raise LoginError(f"Login request failed with status code: {response.status_code}")

    log.info("Login request successful, extracting cookies")
    cookie_jar = response.cookies

    log.debug("Cookies after login (shortened):")
    for cookie in cookie_jar:
        log.debug(f"{cookie.name}: {cookie.value[:10]}...")

    __check_login_success(cookie_jar)
    return cookie_jar
