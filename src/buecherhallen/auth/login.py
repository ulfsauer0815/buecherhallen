import requests
from requests.cookies import RequestsCookieJar
from bs4 import BeautifulSoup

from auth.credentials import Credentials


class LoginError(Exception):
    pass


def check_login_success(soup_result: BeautifulSoup):
    logout_button = soup_result.select_one('.header-account-nav-logout')
    if not logout_button:
        error_message = soup_result.select_one('.formbody > .box')
        if error_message:
            raise LoginError(f"Page response: {error_message.text.strip()}")
        raise LoginError("Logout link not found")


def get_request_token(soup: BeautifulSoup):
    request_token_tag = soup.select_one('input[name="REQUEST_TOKEN"]')
    if not request_token_tag or not request_token_tag.has_attr('value'):
        raise LoginError("Page did not contain a REQUEST_TOKEN input")
    return request_token_tag['value']


def login(credentials: Credentials) -> RequestsCookieJar:
    get_login_page = requests.get('https://www.buecherhallen.de/login.html')
    cookies = get_login_page.cookies
    soup = BeautifulSoup(get_login_page.text, "html.parser")
    request_token = get_request_token(soup)
    payload = {
        'FORM_SUBMIT': 'tl_login',
        'REQUEST_TOKEN': request_token,
        'username': credentials.username,
        'password': credentials.password
    }
    login_result_page = requests.post('https://www.buecherhallen.de/login.html', data=payload, cookies=cookies)
    soup_result = BeautifulSoup(login_result_page.text, "html.parser")
    check_login_success(soup_result)
    return login_result_page.cookies
