import concurrent.futures
import sys
import traceback

from auth.credentials import retrieve_credentials
from auth.login import login, LoginError
from media.item import retrieve_item_details, Item, ItemParseError
from media.watchlist import retrieve_watchlist_items, WatchlistParseError
from ui.site import generate_website


class MainError(Exception):
    pass


def main():
    try:
        credentials = retrieve_credentials()
        try:
            cookies = login(credentials)
        except LoginError as e:
            raise MainError(f"Login failed: {e}")
        try:
            item_ids = retrieve_watchlist_items(cookies)
        except WatchlistParseError as e:
            raise MainError(f"Failed to retrieve watchlist: {e}")
        print(item_ids)
        items: list[Item] = []

        def safe_retrieve(item_id):
            try:
                return retrieve_item_details(item_id)
            except ItemParseError as e:
                print(f"Failed to retrieve item {item_id}: {e}")
                if e.is_error():
                    print("Exiting due to critical error in item retrieval")
                    raise MainError(f"Critical error in retrieval of item {item_id}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            items = list(filter(None, executor.map(safe_retrieve, item_ids)))
        generate_website(items)
    except Exception as e:
        print(f"Error: {e}\n")
        print(traceback.format_exc(), end='', file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
