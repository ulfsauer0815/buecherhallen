import logging

from ui.index import render_index, create_env

log = logging.getLogger(__name__)


def generate_website(items):
    log.info("Generating website")
    env = create_env()
    index = render_index(env, items)
    with open("output/index.html", "w") as f:
        f.write(index)
