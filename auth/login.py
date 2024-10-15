import requests
from bs4 import BeautifulSoup

from auth.credentials import Credentials


def login(credentials: Credentials) -> requests.cookies.RequestsCookieJar:
    get_login_page = requests.get('https://www.buecherhallen.de/login.html')
    cookies = get_login_page.cookies
    soup = BeautifulSoup(get_login_page.text, "html.parser")
    request_token = soup.select_one('input[name="REQUEST_TOKEN"]')['value']
    payload = {
        'FORM_SUBMIT': 'tl_login',
        'REQUEST_TOKEN': request_token,
        'username': credentials.username,
        'password': credentials.password
    }
    login_result_page = requests.post('https://www.buecherhallen.de/login.html', data=payload, cookies=cookies)
    return login_result_page.cookies
