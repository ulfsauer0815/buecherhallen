from datetime import datetime
from zoneinfo import ZoneInfo

from jinja2 import Environment, PackageLoader, select_autoescape

from buecherhallen.media.item import Item


def create_env() -> Environment:
    return Environment(
        loader=PackageLoader("ui"),
        autoescape=select_autoescape()
    )


def render_index(env: Environment, items: list[Item]) -> str:
    available_items_by_location: dict = {}
    for item in items:
        for location, availability in item.availabilities.availabilities.items():
            if availability.is_available():
                if location not in available_items_by_location:
                    available_items_by_location[location] = []
                available_items_by_location[location].append(item)

    current_time = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y %H:%M")
    template = env.get_template("index.j2")
    return template.render(location_mapping=available_items_by_location, current_time=current_time)
