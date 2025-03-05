import concurrent.futures

from auth.credentials import retrieve_credentials
from auth.login import login
from media.item import retrieve_item_details, Item
from media.watchlist import retrieve_watchlist_items
from ui.site import generate_website


def main():
    credentials = retrieve_credentials()

    cookies = login(credentials)

    item_ids = retrieve_watchlist_items(cookies)
    print(item_ids)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        items: list[Item] = list(executor.map(retrieve_item_details, item_ids))

    generate_website(items)


main()
