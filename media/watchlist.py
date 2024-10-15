import requests
from bs4 import BeautifulSoup


def retrieve_watchlist_items(cookies: requests.cookies.RequestsCookieJar) -> list[str]:
    get_login_page = requests.get('https://www.buecherhallen.de/merkliste.html', cookies=cookies)
    soup = BeautifulSoup(get_login_page.text, "html.parser")
    items = soup.select(".search-results-watchlist-item")
    item_ids = [item['id'] for item in items]
    return item_ids
