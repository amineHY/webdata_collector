import time

from fastapi import HTTPException
from playwright.async_api import TimeoutError, async_playwright

from core.logging import logger, setup_logging
from services.parser import parse_facebook_marketplace_listings
from utils.browser import (
    login_facebook,
    save_html,
    scrape_marketplace,
    setup_browser_context,
)
from utils.misc import cities, setup_urls_facebook_marketplace

logger = setup_logging()


async def handle_crawler_request(
    city,
    query,
    max_price,
    item_condition,
    headless,
    strategy,
    llm_choice,
    model_name,
):
    logger.info("START")
    start_time = time.time()

    try:
        logger.info("Running the crawler")
        df_crawler = await run_facebook_marketplace_crawler_and_parser(
            city_param=city,
            query_param=query,
            max_price_param=max_price,
            item_condition_param=item_condition,
            headless_param=headless,
            strategy_param=strategy,
            llm_choice_param=llm_choice,
            model_name_param=model_name,
        )

        logger.info("END")
        return process_crawler_response(df_crawler, start_time)

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def process_crawler_response(df_crawler, start_time):
    if not df_crawler.empty:
        logger.info("Crawler returned data")
        elapsed_time = round(time.time() - start_time, 2)
        logger.info(f"Elapsed time: {elapsed_time} seconds")
        return {
            "status": "ok",
            "data": df_crawler.to_json(orient="records"),
        }
    else:
        logger.info("No data found by the crawler")
        return {"status": "pok", "data": None}


async def run_facebook_marketplace_crawler_and_parser(
    city_param,
    query_param,
    max_price_param,
    item_condition_param,
    headless_param,
    strategy_param,
    llm_choice_param,
    model_name_param,
):
    logger.info("Loading cities dict")
    if city_param in cities:
        city = cities[city_param]
    else:
        raise ValueError(f"{city_param} is not supported.")

    logger.info("Setup urls")
    url_login, url_marketplace = setup_urls_facebook_marketplace(
        query_param, max_price_param, city, item_condition_param
    )
    param_dict = {
        "strategy": strategy_param,
        "model_name": model_name_param,
        "llm_choice": llm_choice_param,
    }

    async with async_playwright() as p:
        try:
            logger.info("Setup browser and context (Playwright)")
            browser, context = await setup_browser_context(p, headless_param)
            page = await context.new_page()
            await page.route(
                "**/*.{png,jpg,jpeg}", lambda route: route.abort()
            )

            logger.info(f"Navigating to login page: {url_login}")
            await login_facebook(page, url_login)

            logger.info(f"Navigating to marketplace: {url_marketplace}")
            html = await scrape_marketplace(page, url_marketplace)

            logger.info("Saving the HTML code")
            filepath = "data/posts_html.html"
            await save_html(html, filepath)

            logger.info("Parsing HTML of all posts' page")
            df = parse_facebook_marketplace_listings(html, param_dict)

        except TimeoutError:
            logger.error("Timeout occurred during the crawling process.")
            df = None
        finally:
            await context.close()
            await browser.close()

        return df
