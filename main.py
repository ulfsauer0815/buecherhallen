from auth.credentials import retrieve_credentials
from media.item import retrieve_item_details
from auth.login import login
from media.watchlist import retrieve_watchlist_items


def main():
    credentials = retrieve_credentials()

    cookies = login(credentials)

    item_ids = retrieve_watchlist_items(cookies)
    print(item_ids)

    items_details = list(map(retrieve_item_details, item_ids))

    print("Eimsbüttel:")
    for item in items_details:
        if item.is_available("Eimsbüttel"):
            print(f"  {item.title}: {item.url}")
    print()

    print("Zentralbibliothek:")
    for item in items_details:
        if item.is_available("Zentralbibliothek"):
            print(f"  {item.title}: {item.url}")


main()
