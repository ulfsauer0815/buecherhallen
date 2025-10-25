from enum import Enum

import requests
from bs4 import BeautifulSoup


class Availability:
    def __init__(self, location: str, count: int, max_count: int, shelf: str):
        self.location = location
        self.count = count
        self.max_count = max_count
        self.shelf = shelf

    def is_available(self) -> bool:
        return self.count > 0

    def __repr__(self):
        return f"Availability({self.location}, {self.count}, {self.max_count} at {self.shelf})"


class Availabilities:
    def __init__(self, availabilities: list[Availability]):
        self.availabilities: dict[str, Availability] = {availability.location: availability for availability in
                                                        availabilities}

    def is_available(self, location: str) -> bool:
        return self.availabilities[location].is_available()

    def __getitem__(self, location: str) -> Availability:
        return self.availabilities[location]

    def items(self) -> list[tuple[str, Availability]]:
        return list(self.availabilities.items())

    def __repr__(self):
        return f"Availabilities({self.availabilities})"


class Item:
    def __init__(self, url, title, availabilities):
        self.url = url
        self.title = title
        self.availabilities = availabilities

    def is_available(self, location: str) -> bool:
        return self.availabilities.is_available(location)

    def __repr__(self):
        return f"Item({self.title}, {self.availabilities}, {self.url})"


class Severity(Enum):
    WARN = "WARN"
    ERROR = "ERROR"


class ItemParseError(Exception):
    def __init__(self, message: str, severity: Severity = Severity.ERROR):
        super().__init__(message)
        self.severity = severity
        self.message = message

    def __str__(self):
        return f"[{self.severity.value}] {self.message}"

    def is_error(self) -> bool:
        return self.severity == Severity.ERROR

    def is_warn(self) -> bool:
        return self.severity == Severity.WARN


def get_availability_fields(availability: BeautifulSoup):
    location_tag = availability.select_one(".medium-availability-item-title-location")
    count_tag = availability.select_one(".medium-availability-item-title-count")
    shelf_tag = availability.select_one(".item-data-shelfmark")
    if not location_tag or not count_tag or not shelf_tag:
        raise ItemParseError("Missing availability fields", Severity.ERROR)
    location = location_tag.text
    count = count_tag.text
    count_split = count.split("/")
    if len(count_split) != 2:
        raise ItemParseError(f"Count field malformed: {count_tag.text}", Severity.ERROR)
    try:
        count_int = int(count_split[0])
        max_count_int = int(count_split[1])
    except ValueError:
        raise ItemParseError(f"Count values are not integers: {count_split}", Severity.ERROR)
    shelf = shelf_tag.text
    return location, count_int, max_count_int, shelf


def parse_availability(availability: BeautifulSoup) -> Availability:
    try:
        location, count_int, max_count_int, shelf = get_availability_fields(availability)
        return Availability(location, count_int, max_count_int, shelf)
    except Exception as e:
        raise ItemParseError(f"Error parsing availability: {e}", Severity.ERROR)


def get_availabilities(soup: BeautifulSoup):
    availabilities_html = soup.select(".medium-availability-item")

    if not soup:
        raise ItemParseError("No availabilities", Severity.ERROR)

    availabilities_text = soup.select_one(".medium-availability-title + .text_container > p")
    if availabilities_text:
        stripped_text = availabilities_text.text.strip()
        severity = Severity.WARN if "Dieser Titel wird digital angeboten" in stripped_text else Severity.ERROR
        raise ItemParseError(f"No availabilities: {stripped_text}", severity)

    availability_message = soup.select_one(".availability-message")
    if availability_message:
        stripped_text = availability_message.text.strip()
        severity = Severity.WARN if "Es sind zur Zeit keine Daten zur Verfügbarkeit abrufbar. Bitte wenden Sie sich an das Bibliothekspersonal" in stripped_text else Severity.ERROR
        raise ItemParseError(f"No availabilities: {stripped_text}", severity)

    return availabilities_html


def get_title_tag(soup: BeautifulSoup) -> str:
    title_tag = soup.select_one(".medium-detail-title")
    if not title_tag:
        h1 = soup.select_one(".mod_resultreader > h1")
        if h1:
            raise ItemParseError(f"Title not found in item detail page: {h1.text.strip()}", Severity.ERROR)
        raise ItemParseError("Title not found in item detail page", Severity.ERROR)
    return title_tag.text.strip()


def retrieve_item_details(id: str) -> Item:
    url = f"https://www.buecherhallen.de/suchergebnis-detail/medium/{id}.html"
    try:
        page = requests.get(url).text
        soup = BeautifulSoup(page, "html.parser")
        title = get_title_tag(soup)
        availabilities_html = get_availabilities(soup)
        availabilities = Availabilities(list(map(parse_availability, availabilities_html)))
        return Item(url=url, title=title, availabilities=availabilities)
    except Exception as e:
        if isinstance(e, ItemParseError):
            raise e
        raise ItemParseError(f"Error retrieving item details for {id}: {e}", Severity.ERROR)
