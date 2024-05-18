import playwright
import asyncio

from playwright.async_api import Page

from core.config import settings
from core.logging import setup_logging

logger = setup_logging()


async def setup_browser_context(playwright, headless):
    """
    Set up a browser context using Playwright.

    Args:
        playwright (Playwright): The Playwright instance.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        Tuple: A tuple containing the browser and context objects.
    """
    try:
        if not isinstance(headless, bool):
            raise TypeError("headless must be a boolean value")

        browser = await playwright.webkit.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            locale="en-US",  # Setting the browser language to English
        )
        return browser, context
    except Exception as e:
        print(f"An error occurred during browser context setup: {e}")
        raise


async def handle_cookies_popup(page, button_txt, headless):
    try:
        allow_all_cookies_button = page.locator(
            f"role=button[name='{button_txt}']"
        )

        # Extra wait for headless mode
        if headless:
            await page.wait_for_timeout(
                1000
            )  # Wait for 1 second to ensure elements are fully loaded

        await allow_all_cookies_button.wait_for(state="visible")
        await allow_all_cookies_button.click()
        logger.info(f"Clicked on '{button_txt}' button")
    except Exception as e:
        if headless:
            # Take a screenshot and log HTML content in headless mode for debugging
            await page.screenshot(path="cookies_popup_error.png")
            html_content = await page.content()
            with open("cookies_popup_error.html", "w") as file:
                file.write(html_content)
        logger.error(f"An error occurred while handling cookies popup: {e}")


async def login_facebook(page, url_login):
    try:
        await page.goto(url_login)

        await handle_cookies_popup(page, "Allow all cookies", True)
        logger.info("Login")
        email_input = await page.wait_for_selector(
            'input[name="email"]', timeout=90000
        )
        await email_input.fill(settings.FACEBOOK_EMAIL)
        password_input = await page.wait_for_selector(
            'input[name="pass"]', timeout=90000
        )
        await password_input.fill(settings.FACEBOOK_PASSWORD)
        await page.click("button[name='login']")
        await page.wait_for_load_state("domcontentloaded")
        logger.info("Logged in Facebook")

    except Exception as e:
        logger.error(f"Error during Facebook login: {e}")
        raise


async def scrape_marketplace(page: Page, url_marketplace):
    await page.goto(url_marketplace)
    await asyncio.sleep(2)

    await page.wait_for_load_state("domcontentloaded")
    html = await page.content()
    await page.screenshot(path="data/marketplace_posts.png")

    return html


async def save_html(html, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
