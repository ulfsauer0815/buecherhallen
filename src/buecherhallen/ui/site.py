import logging

from ui.index import render_index, create_env


def generate_website(items):
    logging.info("Generating website")
    env = create_env()
    index = render_index(env, items)
    with open("output/index.html", "w") as f:
        f.write(index)
