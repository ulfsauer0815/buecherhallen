import logging
import re

from auth.bot_protection import solve_cloudflare
from auth.cache import cache_cookies, load_cookies
from auth.credentials import Credentials
from camoufox.sync_api import Camoufox
from common.constants import LOGIN_URL, BASE_HOSTNAME
from playwright.sync_api import (
    Page
)
from requests.cookies import RequestsCookieJar


class LoginError(Exception):
    pass


def check_login_success(cookies: RequestsCookieJar):
    if 'luci_session' not in cookies:
        log.error("luci_session cookie not found after login")
        raise LoginError("luci_session cookie not found, login has failed")


def login(credentials: Credentials, use_cache: bool = False) -> RequestsCookieJar:
    if use_cache:
        logging.warn("Cache usage is experimental and does not clean up expired cookies!")
        logging.info("Checking for cached cookies")
        cached_cookies = load_cookies()
        if cached_cookies:
            try:
                check_login_success(cached_cookies)
                return cached_cookies
            except LoginError:
                logging.info("Cached cookies are invalid, proceeding to login")

    logging.info("Starting login process")

    try:
        with Camoufox(os=["windows", "macos", "linux"], humanize=True, headless=False) as browser:
            page = browser.new_page()
            __disable_cookie_banner(page)

            page.goto(LOGIN_URL)
            page.wait_for_load_state(state="domcontentloaded")
            page.wait_for_load_state('networkidle')

            solve_cloudflare(page)

            __enter_credentials_and_login(page, credentials)

            # wait for next page to load
            page.wait_for_url(re.compile(r'.*/user/account'), wait_until="commit")

            logging.info("Login form submitted, checking cookies")

            cookie_jar = extract_cookie_jar(page)

            logging.debug("Cookies after login (shortened):")
            for cookie in cookie_jar:
                # print cookie but shorten values
                logging.debug(f"{cookie.name}: {cookie.value[:10]}...")

            check_login_success(cookie_jar)
            if use_cache:
                cache_cookies(cookie_jar)
            return cookie_jar
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
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
        cookie_jar.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
    return cookie_jar
