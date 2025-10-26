import logging
import re
from random import randint

from auth.credentials import Credentials
from playwright.sync_api import (
    Page, Error as PlaywrightError
)


def solve_cloudflare(page: Page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightError:
        pass

    bounding_box = None

    iframe = page.frame(url=re.compile(r'challenges.cloudflare.com/cdn-cgi/challenge-platform/.*'))
    logging.info(f"Cloudflare iframe found: {iframe is not None}")

    if iframe is not None:
        logging.info("Wait for iframe")
        iframe.wait_for_load_state(state="domcontentloaded")
        iframe.wait_for_load_state("networkidle")
        bounding_box = iframe.frame_element().bounding_box()
        logging.debug(f"iframe bounding box: {bounding_box}")

    # Fallback: try to find the challenge box directly on the page
    if not bounding_box:
        logging.info(f"Fallback, try to find directly on page")
        try:
            bounding_box = page.locator(
                "#cf_turnstile div, #cf-turnstile div, .turnstile > div > div").last.bounding_box(timeout=5000)
            logging.debug(f"Fallback bounding box: {bounding_box}")
        except Exception as e:
            logging.error(f"Failed to get fallback bounding box: {e}")
            logging.info("Fallback to just wait for completion")
            page.wait_for_timeout(3000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightError:
                pass
            page.wait_for_load_state(state="load")
            page.wait_for_load_state(state="domcontentloaded")
            logging.info("Cloudflare challenge solved?")
            return

    # If bounding box is found, click the challenge box
    box_x = bounding_box["x"] + randint(26, 28)
    box_y = bounding_box["y"] + randint(25, 27)
    logging.debug(f"Clicking box: (x={box_x}, y={box_y})")
    page.mouse.click(box_x, box_y, button="left", delay=60)

    logging.info("Wait for network idle after click")
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightError:
        logging.info("Initial network idle timeout, continuing...")

    logging.info("Wait for completion")
    page.wait_for_timeout(3000)

    logging.info("Wait for another network idle")
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightError:
        logging.info("Network idle timeout, maybe challenge is solved?")

    logging.info("Wait for page load")
    page.wait_for_load_state(state="load")
    page.wait_for_load_state(state="domcontentloaded")

    # check turnstile value
    value = page.locator('input[name="cf-turnstile-response"]').get_attribute('value')

    if not value:
        logging.error("Failed to retrieve Cloudflare turnstile response value")
        return

    logging.debug(f"Turnstile value: {value[:10]}...")
    logging.info("Cloudflare captcha is solved")
