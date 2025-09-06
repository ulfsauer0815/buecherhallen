import requests
from bs4 import BeautifulSoup


class WatchlistParseError(Exception):
    pass


def get_watchlist_item_id(item):
    if not item.has_attr('id'):
        raise WatchlistParseError("Watchlist item missing 'id' attribute.")
    return item['id']


def retrieve_watchlist_items(cookies: requests.cookies.RequestsCookieJar) -> list[str]:
    try:
        get_login_page = requests.get('https://www.buecherhallen.de/merkliste.html', cookies=cookies)
        soup = BeautifulSoup(get_login_page.text, "html.parser")
        items = soup.select(".search-results-watchlist-item")
        if not items:
            raise WatchlistParseError("No watchlist items found or page structure changed.")
        item_ids = list(map(get_watchlist_item_id, items))
        return item_ids
    except Exception as e:
        raise WatchlistParseError(f"Error retrieving watchlist items: {e}")
