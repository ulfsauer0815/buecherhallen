import logging
import re
from random import randint

from playwright.sync_api import (
    Page, Error as PlaywrightError
)

log = logging.getLogger(__name__)


class BotProtectionError(Exception):
    pass


def solve_cloudflare(page: Page) -> str:
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightError:
        pass

    bounding_box = None

    iframe = page.frame(url=re.compile(r'challenges.cloudflare.com/cdn-cgi/challenge-platform/.*'))
    log.info(f"Cloudflare iframe found: {iframe is not None}")

    if iframe is not None:
        log.info("Wait for iframe")
        iframe.wait_for_load_state(state="domcontentloaded")
        iframe.wait_for_load_state("networkidle")
        element = iframe.frame_element()
        element.scroll_into_view_if_needed()
        bounding_box = element.bounding_box()

        log.debug(f"iframe bounding box: {bounding_box}")

    # Fallback: try to find the challenge box directly on the page
    if not bounding_box:
        log.info(f"Fallback, try to find directly on page")
        try:
            bounding_box = page.locator(
                "#cf_turnstile div, #cf-turnstile div, .turnstile > div > div").last.bounding_box(timeout=5000)
            log.debug(f"Fallback bounding box: {bounding_box}")
        except Exception as e:
            log.error(f"Failed to get fallback bounding box: {e}")
            log.info("Fallback to just wait for completion")
            page.wait_for_timeout(3000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightError:
                pass
            page.wait_for_load_state(state="load")
            page.wait_for_load_state(state="domcontentloaded")
            log.info("Cloudflare challenge solved?")
            return extract_turnstile_token(page)

    # If bounding box is found, click the challenge box
    box_x = bounding_box["x"] + randint(26, 28)
    box_y = bounding_box["y"] + randint(25, 27)
    log.debug(f"Clicking box: (x={box_x}, y={box_y})")
    page.mouse.click(box_x, box_y, button="left", delay=60)

    log.info("Wait for network idle after click")
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightError:
        log.info("Initial network idle timeout, continuing...")

    log.info("Wait for completion")
    page.wait_for_timeout(3000)

    log.info("Wait for another network idle")
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightError:
        log.info("Network idle timeout, maybe challenge is solved?")

    log.info("Wait for page load")
    page.wait_for_load_state(state="load")
    page.wait_for_load_state(state="domcontentloaded")

    turnstile_token = extract_turnstile_token(page)

    log.debug(f"Turnstile value: {turnstile_token[:10]}...")
    log.info("Cloudflare captcha is solved")
    return turnstile_token


def extract_turnstile_token(page: Page) -> str:
    value = page.locator('input[name="cf-turnstile-response"]').get_attribute('value')

    if not value:
        log.error("Failed to retrieve Cloudflare turnstile response value")
        raise BotProtectionError("Failed to solve Cloudflare captcha: Cannot find turnstile response value")
    return value
