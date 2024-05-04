# Import necessary libraries
import datetime
import logging
import os
import random
import time
import urllib
import urllib.parse
from urllib.parse import urlparse
from playwright.sync_api import TimeoutError
import pandas as pd
import uvicorn
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fake_useragent import UserAgent
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright, Playwright
from rich import print

from tools.config import cities

# Create an instance of the FastAPI class.
app = FastAPI()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Load environment variables from .env file")
load_dotenv()
email = os.getenv("email")
password = os.getenv("password")


def parse_facebook_marketplace_listings(html):
    """
    Parses Facebook Marketplace listings from the provided BeautifulSoup soup object.

    Parameters
    ----------
    soup : BeautifulSoup
        The BeautifulSoup soup object containing the HTML content of the Marketplace page.

    Returns
    -------
    DataFrame
        DataFrame containing parsed listing data.
    """
    logger.info("Parsing html of all listings' page")
    soup = BeautifulSoup(html, "html.parser")

    # Get all listings
    html_listings = soup.find_all(
        "div",
        class_="x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24",
    )
    # Create an empty list to store the parsed data
    result = []
    # Iterate through all listings
    for idx, listing in enumerate(html_listings):
        logger.info("Scraping data from post {}".format(idx))
        # print(listing)
        try:
            title = listing.find(
                "span", class_="x1lliihq x6ikm8r x10wlt62 x1n2onr6"
            ).text
        except Exception as e:
            title = None

        try:
            price = listing.find(
                "span",
                class_="x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x3x7a5m x1lkfr7t x1lbecb7 x1s688f xzsf02u",
            ).text
        except Exception as e:
            price = None
        try:
            location = listing.find(
                "span",
                class_="x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft",
            ).text
        except Exception as e:
            location = None
        try:
            url_post = "https://www.facebook.com" + listing.find("a").get(
                "href"
            )
        except Exception as e:
            url_post = None
        print(title, price, location, url_post)

        # Create a dictionary with the listing data
        dict_listing_data = {
            "title": title,
            "price": price,
            "location": location,
            "url": url_post,
            "date": datetime.date.today(),
        }

        result.append(dict_listing_data)

    # Convert list to DataFrame
    df = pd.DataFrame(result)
    df = df.dropna(subset=["url"])
    logger.info(f"{df.shape[0]} listings found")

    return df.sort_values(by="price", ascending=True)


def human_like_interactions(page):
    """Perform human-like interactions on the page."""
    logger.info("Mimic reading by scrolling and pausing")
    total_scroll = 0
    while total_scroll < 2000:
        scroll_length = random.randint(100, 500)
        page.mouse.wheel(0, scroll_length)
        time.sleep(random.uniform(0.5, 1.5))  # Short pause to mimic reading
        total_scroll += scroll_length

    logger.info("Click on non-interactive parts of the page")
    for _ in range(random.randint(2, 5)):  # Multiple random clicks
        page.click(
            "body",
            position={
                "x": random.randint(100, 300),
                "y": random.randint(200, 600),
            },
        )
        time.sleep(random.uniform(0.5, 1.5))  # Pause between clicks

    # Wait for some time after handling cookies
    page.wait_for_timeout(random.uniform(2000, 5000))


def handle_cookies_popup(page, button_txt="Allow all cookies"):
    """_summary_

    Parameters
    ----------
    page : _type_
        _description_
    """
    try:
        # Use a more specific selector that targets the button based on its role and name
        allow_all_cookies_button = page.locator(
            f"role=button[name='{button_txt}']"
        )
        # Wait for the button to be visible and enabled
        allow_all_cookies_button.wait_for(state="visible")
        allow_all_cookies_button.click()
        logger.info(f"Clicked on '{button_txt}' button")
    except Exception as e:
        logger.info(f"An error occurred while handling cookies popup: {e}")


def parse_facebook_marketplace_post_metadata(page, df):
    """
    Parameters
    ----------
    page : Playwright Page object
        The page object representing the current webpage.
    df : pandas.DataFrame
        The DataFrame containing the URLs of the Facebook Marketplace listings.

    Returns
    -------
    pandas.DataFrame
        The updated DataFrame with the parsed metadata for each listing.
    """
    if df.shape[0] > 0:
        for index, row in df.iterrows():
            try:
                logger.info(
                    f"Navigate to item {index} page's URL : {row['url']}"
                )
                page.goto(row["url"])
                page.wait_for_load_state("networkidle")
                logger.info(f"Getting {index}-th post content")
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")
                parent_div = soup.find(
                    "div", class_="xyamay9 x1pi30zi x18d9i69 x1swvt13"
                )

                if parent_div:
                    title_elements = parent_div.select("h1")
                    if title_elements:
                        title_element = title_elements[0].text.strip()
                    else:
                        title_element = ""

                    price_elements = parent_div.select("div div div div span")
                    if len(price_elements) > 1:
                        price_element = price_elements[1].text.strip()
                    else:
                        price_element = ""

                    publication_time_element = parent_div.find(
                        "span", class_="html-span"
                    )
                    if publication_time_element:
                        publication_time = publication_time_element.get_text(
                            strip=True
                        )
                    else:
                        publication_time = ""

                    location_elements = parent_div.select(
                        "div div div div span a"
                    )
                    if location_elements:
                        location_element = location_elements[0].text.strip()
                    else:
                        location_element = ""

                    condition_div = soup.find(
                        "span", class_="x1e558r4 xp4054r x3hqpx7"
                    )
                    if condition_div:
                        condition_spans = condition_div.select("span")
                        if len(condition_spans) > 1:
                            condition_element = condition_spans[1].text.strip()
                        else:
                            condition_element = ""
                    else:
                        condition_element = ""

                    df.loc[index, "title"] = title_element
                    df.loc[index, "price"] = price_element
                    df.loc[index, "condition"] = condition_element
                    df.loc[index, "publication_time"] = publication_time
                    df.loc[index, "location"] = location_element
                    df.loc[index, "url"] = row["url"]
                else:
                    logger.warning(f"Parent div not found for item {index}")
            except Exception as e:
                logger.error(
                    f"An error occurred while parsing item {index}: {e}"
                )

        return df
    else:
        logger.info("No listing found")
        return None


def crawle_facebook_marketplace(headless_param, url_login, url_marketplace, p):
    """
    Parameters
    ----------
    headless_param : bool
        Determines whether the browser should be launched in headless mode or not.
    url_login : str
        The URL of the Facebook login page.
    url_marketplace : str
        The URL of the Facebook Marketplace.
    p : Playwright object
        The Playwright instance.

    Returns
    -------
    browser : Playwright.Browser
        The browser instance.
    page : Playwright.Page
        The page instance.
    html : str
        The HTML content of the marketplace page.
    """
    logger.info("Launching browser")
    browser = p.webkit.launch(headless=headless_param)

    # Set the viewport size to a random width and height between 800x600 and 1600x1200
    viewport_width = random.randint(800, 1600)
    viewport_height = random.randint(600, 1200)

    # Set a fake user agent to avoid being blocked
    ua = UserAgent()
    user_agent = ua.random

    # Define a browser context with the specified viewport size and user agent
    context = browser.new_context(
        user_agent=user_agent,
        # locale='fr-FR',
        # timezone_id='Europe/Paris',
        locale="en-US",  # Set language
        timezone_id="Europe/Paris",  # Emulate timezone
        viewport={"width": viewport_width, "height": viewport_height},
    )
    page = context.new_page()
    page.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())

    logger.info(f"Navigating to login page: {url_login}")
    try:
        page.goto(
            url_login, timeout=60000
        )  # Increase the timeout to 60 seconds (60000 ms)
    except TimeoutError:
        logger.error("Timeout occurred while navigating to the login page.")
        context.close()
        browser.close()
        return None, None, None

    page.wait_for_load_state("networkidle")
    logger.info(f"Checking login page loaded : {page.title()}")
    assert "Facebook" in page.title()

    # Check if the cookie popup is visible and click the accept button
    handle_cookies_popup(page, button_txt="Allow all cookies")
    human_like_interactions(page)

    logger.info("Filling login form")
    page.wait_for_selector('input[name="email"]').fill(email)
    page.wait_for_selector('input[name="pass"]').fill(password)

    logger.info("Clicking login button")
    page.wait_for_selector('button[name="login"]').click()
    page.wait_for_load_state("networkidle")

    logger.info(f"Navigating to marketplace : {url_marketplace}")
    page.goto(url_marketplace)
    page.wait_for_load_state("networkidle")

    logger.info(f"Checking marketplace page loaded : {page.title()}")
    page.wait_for_load_state("networkidle")
    # assert "Marketplace" in page.title()

    logger.info("Mimic reading by scrolling and pausing")
    total_scroll = 0
    while total_scroll < 8000:
        scroll_length = random.randint(100, 500)
        page.mouse.wheel(0, scroll_length)
        time.sleep(random.uniform(0.5, 1.5))  # Short pause to mimic reading
        total_scroll += scroll_length

    logger.info("Getting page content")
    html = page.content()

    return browser, page, html


def features_engineering(filepath):
    """_summary_

    Parameters
    ----------
    df : _type_
        _description_
    """
    # Read the csv file
    df = pd.read_csv(filepath)

    # Clean price column and convert to numeric
    prices = df["price"].str.extract(r"(?:€\s*(\d+))?(?:€\s*(\d+))?")
    df["price_before"] = prices[1]
    df["price_after"] = prices[0]
    df["price_difference"] = df["price_after"]
    df["price_difference"] = df["price_before"].astype(float) - df[
        "price_after"
    ].astype(float)

    # Fill NaN with price after
    df["price_difference"] = df["price_difference"].fillna(df["price_after"])

    # Create a flag for price reduction
    df["price_reduction_flag"] = df["price_after"].astype(float) < df[
        "price_before"
    ].astype(float)

    # Calculate price reduction percentage
    df["price_reduction_pct"] = (
        df["price_difference"] / df["price_before"].astype(float)
    ) * 100

    df["url"] = df["url"].apply(
        lambda x: urlparse(x).scheme
        + "://"
        + urlparse(x).netloc
        + urlparse(x).path
    )
    df = df.sort_values("price_reduction_pct", ascending=False)
    return df


def setup_urls_facebook_marketplace(
    query_param, max_price_param, item_condition_param, city
):
    url_facebook = "https://www.facebook.com"
    url_login = url_facebook + "/login/device-based/regular/login/"

    base_url_marketplace = f"{url_facebook}/marketplace/{city}/search/"
    query_params = {
        "query": query_param,
        "maxPrice": max_price_param,
        "itemCondition": item_condition_param,
        "exact": "true",
    }
    encoded_query_params = urllib.parse.urlencode(query_params)
    url_marketplace = f"{base_url_marketplace}?{encoded_query_params}"
    return url_login, url_marketplace


def run_facebook_marketplace_crawler_and_parser(
    city_param,
    query_param,
    max_price_param,
    headless_param=True,
    item_condition_param="new",
):
    """_summary_

    Parameters
    ----------
    city_param : _type_
        _description_
    query_param : _type_
        _description_
    max_price_param : _type_
        _description_
    headless_param : bool, optional
        _description_, by default True

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    if city_param in cities:
        city = cities[city_param]
    else:
        raise ValueError(f"{city_param} is not supported.")

    url_login, url_marketplace = setup_urls_facebook_marketplace(
        query_param, max_price_param, item_condition_param, city
    )

    with sync_playwright() as p:

        browser, page, html = crawle_facebook_marketplace(
            headless_param, url_login, url_marketplace, p
        )
        df = parse_facebook_marketplace_listings(html)
        time.sleep(2)
        df = parse_facebook_marketplace_post_metadata(page, df)

        # Close the browser
        browser.close()

        return df


@app.get("/")
def root():
    return {"message": "Hello, World!"}


@app.get("/crawler/")
def main(
    city, query, max_price, headless=True, item_condition="used_like_new"
):
    """_summary_

    Parameters
    ----------
    city : _type_
        _description_
    query : _type_
        _description_
    max_price : _type_
        _description_
    headless : bool, optional
        _description_, by default True
    item_condition : str, optional
        _description_, by default 'used_like_new'

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    # TODO Add parameters validation
    logger.info("START")
    start_time = time.time()

    print_data = True
    save_data = True

    logger.info("Crawl listings")
    df_crawler = run_facebook_marketplace_crawler_and_parser(
        city_param=city,
        query_param=query,
        max_price_param=max_price,
        item_condition_param=item_condition,
        headless_param=headless,
    )
    # wrap up
    if df_crawler is not None:
        if print_data:
            logger.info("Print results")
            print(df_crawler)
        if save_data:
            logger.info("Saving results to CSV")
            if df_crawler.empty:
                raise ValueError("No data found")
            filepath = f"data/results_{city}_{query}_{max_price}.csv"
            df_crawler.to_csv(filepath, index=False)
            df_crawler = features_engineering(filepath)
            df_crawler.to_csv(filepath[:-4] + "_cleaned.csv", index=False)

        end_time = time.time()
        logger.info(f"Elapsed time: {round(end_time - start_time, 2)} seconds")

        return {"status": "ok", "data": df_crawler.to_json()}
    else:
        return {"status": "pok", "data": None}


# Run the server
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
