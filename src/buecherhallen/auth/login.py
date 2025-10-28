import logging
import re
import time

from auth.bot_protection import solve_cloudflare
from auth.cache import cache_cookies, load_cookies, log_cookies
from auth.credentials import Credentials
from camoufox.sync_api import Camoufox
from common.constants import LOGIN_URL, BASE_HOSTNAME
from playwright.sync_api import (
    Page
)
from requests.cookies import RequestsCookieJar

log = logging.getLogger(__name__)

EXPIRY_BUFFER_SECONDS = 5 * 60  # 5 minutes


class LoginError(Exception):
    pass


def check_login_success(cookies: RequestsCookieJar):
    if 'luci_session' not in cookies:
        log.error("luci_session cookie not found after login")
        raise LoginError("luci_session cookie not found, login has failed")

    luci_session_cookie = get_cookie(cookies, 'luci_session')
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
                check_login_success(cached_cookies)
                return cached_cookies
            except LoginError:
                log.info("Cached cookies are invalid, proceeding to login")

    log.info("Starting login process")

    try:
        with Camoufox(os=["windows", "macos", "linux"], humanize=True, headless=headless) as browser:
            page = browser.new_page()
            __disable_cookie_banner(page)

            page.goto(LOGIN_URL)
            page.wait_for_load_state(state="domcontentloaded")
            page.wait_for_load_state('networkidle')

            solve_cloudflare(page)

            __enter_credentials_and_login(page, credentials)

            # wait for next page to load
            page.wait_for_url(re.compile(r'.*/user/account'), wait_until="commit")

            log.info("Login form submitted, checking cookies")

            cookie_jar = extract_cookie_jar(page)

            log.debug("Cookies after login (shortened):")
            for cookie in cookie_jar:
                # print cookie but shorten values
                log.debug(f"{cookie.name}: {cookie.value[:10]}...")

            check_login_success(cookie_jar)
            if use_cache:
                cache_cookies(cookie_jar)
            return cookie_jar
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


def extract_cookie_jar(page) -> RequestsCookieJar:
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


def get_cookie(cookies: RequestsCookieJar, name: str):
    for cookie in cookies:
        if cookie.name == name:
            return cookie
    return None
