# Import necessary libraries
import asyncio
import datetime
import logging
import os
import random
import time
import urllib
import urllib.parse
from urllib.parse import urlparse

import pandas as pd
import uvicorn
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fake_useragent import UserAgent
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms.ollama import Ollama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from playwright.async_api import TimeoutError, async_playwright
from pydantic import BaseModel, Field, ValidationError
from rich import print

from tools.config import cities

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Define API endpoints
# ----------------------------------------------------------------------------

logger.info("Setup FastAPI")


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


# Root endpoint
@app.get("/")
def root():
    return {"message": "Hello, World!"}


# Crawler endpoint
@app.get("/crawler/")
async def crawler(
    city: str,
    query: str,
    max_price: int,
    headless: bool = False,
    item_condition: str = "used_like_new",
):
    return await handle_crawler_request(
        city, query, max_price, headless, item_condition
    )


# Function to process crawler response
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


async def handle_crawler_request(
    city, query, max_price, headless, item_condition
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
        )

        logger.info("END")
        return process_crawler_response(df_crawler, start_time)

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# Setup LMM parameters
# ----------------------------------------------------------------------------

logger.info("Setup LLM")


def get_prompt():
    llm_prompt = PromptTemplate(
        template="""
        Find and extract text of title, location, price, and item_number from HTML code of a Facebook marketplace post.
        Make sure to return the values in a string and arrange them in a JSON format, here are some examples :
        {json_example1}
        {json_example2}
        {json_example3}
        {json_example4} (default values)
        DISCLAIMER: DO NOT RETURN CODE OR EXPLANATION, ONLY RETURN A JSON WITH TEXT YOU EXTRACTED FROM HTML, EXCLUDE ANY WORDS OTHER THAN THE JSON, DO NOT EXPLAIN OR SAY 'HERE IS THE ...',

        Here is the HTML code:
        {HTML}
        """,
        input_variables=[
            "json_example1",
            "json_example2",
            "json_example3",
            "HTML",
        ],
    )
    return llm_prompt


def get_parser():
    class Post(BaseModel):
        title: str = Field(description="Title")
        location: str = Field(description="Location")
        price: str = Field(description="Price")
        item_number: str = Field(description="Number of the item")

    llm_parser = JsonOutputParser(pydantic_object=Post)
    return llm_parser


def get_model(model_name):
    if model_name == "ollama":
        llm_model = Ollama(model="llama3")
        return llm_model

    elif model_name == "gpt":
        load_dotenv()
        llm_model = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
        return llm_model

    else:
        raise ValueError(f"{model_name} is not a supported model name.")


llm_prompt = get_prompt()
llm_model = get_model(model_name="ollama")
llm_parser = get_parser()
chain = llm_prompt | llm_model | llm_parser

json_example1 = {
    "title": "MacBook Pro URGENT",
    "location": "Paris, IDF",
    "price": "€ 200",
    "item_number": "1927362054385880",
}

json_example2 = {
    "title": "Sony Camera",
    "location": "New York, NY",
    "price": "$ 300",
    "item_number": "1234567890123456",
}

json_example3 = {
    "title": "Furniture",
    "location": "Berlin, DE",
    "price": "€ 150",
    "item_number": "9876543210987654",
}

json_example4 = {
    "title": "",
    "location": "",
    "price": "",
    "item_number": "",
}


def get_single_post_data_using_llm(html_content):
    try:
        result = chain.invoke(
            {
                "HTML": html_content,
                "json_example1": json_example1,
                "json_example2": json_example2,
                "json_example3": json_example3,
                "json_example4": json_example4,
            }
        )
        logger.info("Answer from LLM chain: {}".format(result))
        return result
    except ValidationError as e:
        logger.error("Validation error: {}".format(e))
    except Exception as e:
        logger.error("Error: {}".format(e))


# ----------------------------------------------------------------------------
# Define Python Functions
# ----------------------------------------------------------------------------


def find_empty_html_divs(soup):
    """
    This function checks if there are empty <div> elements in the given HTML.

    Parameters:
    html (str): A string containing the HTML code to be checked.

    Returns:
    list: A list of empty <div> elements found in the HTML.
    """
    div_tags = soup.find_all("div")  # Find all div elements
    empty_divs = [
        div for div in div_tags if not div.contents
    ]  # Check if div has no contents

    return empty_divs


def parse_facebook_marketplace_listings(html, parsing_method = 'css'):
    logger.info("Parsing HTML of all posts' page")
    soup = BeautifulSoup(html, "html.parser")

    logger.info("Getting HTML of all posts")
    soup_posts = soup.find_all(
        "div",
        class_="x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24",
    )

    # Create an empty list to store the parsed data
    result = []
    posts_count = len(soup_posts)

    if posts_count > 0:
        logger.info("Iterating through {} posts".format(posts_count))
        for idx, soup_single_post in enumerate(soup_posts):
            print("# ----------------------------------------------------")

            empty_divs = find_empty_html_divs(soup_single_post)
            if empty_divs:
                print("There are empty divs in the HTML.")
                continue
            else:
                print("No empty divs found in the HTML.")

            logger.info(
                "Extracting metadata from a single HTML post %d", idx + 1
            )

            try:
                url_post = "https://www.facebook.com" + soup_single_post.find(
                    "a"
                ).get("href")
                print(url_post)
            except:
                print(soup_single_post)
                url_post = ""
            
            if parsing_method == 'llm':
                logger.info("Extracting post's data using LLM chain")
                try:
                    post_data = get_single_post_data_using_llm(soup_single_post)
                    title = post_data.get("title")
                    price = post_data.get("price")
                    location = post_data.get("location")
                    item_number = post_data.get("item_number")
                except:
                    title = "None"
                    price = "None"
                    location = "None"
                    item_number = "None"

            elif parsing_method == "css":
                logger.info("Extracting post's data using CSS Extractor")
                html_content = soup_single_post.prettify()
                title, price, location, item_number = (
                    get_single_post_data_using_css(html_content)
                )
            else:

            logger.info("Update dictionary with extracted listing data")
            result.append(
                {
                    "title": title,
                    "price": price,
                    "location": location,
                    "item_number": item_number,
                    "url": url_post,
                    "date": datetime.date.today(),
                }
            )

        # Convert list to DataFrame
        df = pd.DataFrame(result)

        if not df.empty:
            logger.info("Crawler returned data")

            # df = df.dropna(subset=["url"])
            # df = df[df["url"].astype(bool)]

            filepath = f"data/results_bronze.csv"

            logger.info("Saving dataframe to CSV: Bronze")
            df.to_csv(filepath, index=False)

            logger.info("Saving dataframe to CSV: Silver")
            df = features_engineering(filepath)

            filepath = f"data/results_silver.csv"
            df.to_csv(filepath, index=False)
        return df  # .sort_values(by="price", ascending=True)
    else:
        logger.warn("No listing found")
        return pd.DataFrame()


def get_single_post_data_using_css(html):

    try:
        # Parse the HTML
        soup = BeautifulSoup(html, "html.parser")

        # Find the relevant div containing the item details
        item_div = soup.find("div", class_="x9f619")

        # Extract title
        title_element = item_div.find(
            "span", class_="x1lliihq x6ikm8r x10wlt62 x1n2onr6"
        )
        title = (
            title_element.text.replace("\n", " ").strip()
            if title_element
            else "None"
        )

        # Extract price
        price_element = item_div.find("span", class_="x193iq5w")
        price = price_element.text.strip() if price_element else "None"

        # Extract location
        location_element = item_div.find("span", class_="x1nxh6w3")
        location = (
            location_element.text.strip() if location_element else "None"
        )

        # Extract item number from href attribute
        item_number_element = item_div.find("a")
        item_number = (
            item_number_element["href"].split("/")[-2]
            if item_number_element
            else "None"
        )

        return title, price, location, item_number
    except Exception as e:
        print("An error occurred:", e)


def get_post_info_from_html_css(soup):

    parent_div = soup.find("div", class_="xyamay9 x1pi30zi x18d9i69 x1swvt13")
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

    publication_time_element = parent_div.find("span", class_="html-span")
    if publication_time_element:
        publication_time = publication_time_element.get_text(strip=True)
    else:
        publication_time = ""

    location_elements = parent_div.select("div div div div span a")
    if location_elements:
        location_element = location_elements[0].text.strip()
    else:
        location_element = ""

    condition_div = soup.find("span", class_="x1e558r4 xp4054r x3hqpx7")
    if condition_div:
        condition_spans = condition_div.select("span")
        if len(condition_spans) > 1:
            condition_element = condition_spans[1].text.strip()
        else:
            condition_element = ""
    else:
        condition_element = ""
    return (
        title_element,
        price_element,
        location_element,
        condition_element,
        publication_time,
    )


def features_engineering(filepath):

    df = pd.read_csv(filepath)

    def clean_price(price):
        if "Gratuit" in price:
            return 0  # Convert "Gratuit" to 0 or any other value you prefer
        # Remove currency symbols and spaces, then convert to numeric
        clean_price = (
            price.replace("€", "")
            .replace("$", "")
            .replace(" ", "")
            .replace(",", "")
        )
        return pd.to_numeric(clean_price, errors="coerce")

    # Apply the function to the price column
    df["cleaned_price"] = df["price"].apply(clean_price)

    # Regular expression to capture prices with optional comma separators
    prices = df["price"].str.extract(r"[$€]\s*([\d,]+)\s*[$€]?\s*([\d,]*)")

    # Remove commas and convert to numeric, coercing errors to NaN
    df["price_before"] = pd.to_numeric(
        prices[1].str.replace(",", ""), errors="coerce"
    )
    df["price_after"] = pd.to_numeric(
        prices[0].str.replace(",", ""), errors="coerce"
    )

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
    url_login = url_facebook + "/login/"

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


def count_lines_in_html_file(file_path):
    try:
        # Open the HTML file in read mode
        with open(file_path, "r", encoding="utf-8") as file:
            # Initialize a counter for the number of lines
            line_count = 0
            # Iterate through each line in the file
            for _ in file:
                # Increment the line count for each line
                line_count += 1
        return line_count
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# async def human_like_interactions(page):
#     """Perform human-like interactions on the page."""
#     logger.info("Mimic reading by scrolling and pausing")
#     total_scroll = 0
#     while total_scroll < 1000:
#         scroll_length = random.randint(100, 500)
#         await page.mouse.wheel(0, scroll_length)
#         await asyncio.sleep(random.uniform(0.5, 1.5))
#         total_scroll += scroll_length

#     logger.info("Click on non-interactive parts of the page")
#     for _ in range(random.randint(2, 5)):  # Multiple random clicks
#         await page.click(
#             "body",
#             position={
#                 "x": random.randint(100, 300),
#                 "y": random.randint(200, 600),
#             },
#         )
#         await asyncio.sleep(random.uniform(0.5, 1.5))  # Pause between clicks


async def handle_cookies_popup(page, button_txt):
    try:
        allow_all_cookies_button = page.locator(
            f"role=button[name='{button_txt}']"
        )
        # Attendre que le bouton soit visible et activé
        await allow_all_cookies_button.wait_for(state="visible")
        await allow_all_cookies_button.click()
        logger.info(f"Clicked on '{button_txt}' button")
    except Exception as e:
        logger.error(f"An error occurred while handling cookies popup: {e}")


async def setup_browser_context(p, headless):
    browser = await p.webkit.launch(headless=headless)
    viewport_width = random.randint(1600, 1800)
    viewport_height = random.randint(1200, 1400)
    ua = UserAgent()
    user_agent = ua.random
    context = await browser.new_context(
        user_agent=user_agent,
        locale="en-US",
        viewport={"width": viewport_width, "height": viewport_height},
    )
    return browser, context


async def login_facebook(page, url_login):
    await page.goto(url_login, timeout=60000)
    await asyncio.sleep(3)
    await page.wait_for_load_state("networkidle")
    await handle_cookies_popup(page, "Allow all cookies")
    await asyncio.sleep(2)

    email = os.getenv("email")
    password = os.getenv("password")
    email_input = await page.wait_for_selector(
        'input[name="email"]', timeout=60000
    )
    await email_input.fill(email)
    password_input = await page.wait_for_selector(
        'input[name="pass"]', timeout=60000
    )
    await password_input.fill(password)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(3)


async def save_html(html, filepath):
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(str(BeautifulSoup(html, "html.parser").prettify()))
    num_lines = count_lines_in_html_file(filepath)
    logger.info(f"Number of lines in '{filepath}': {num_lines}")


async def scrape_marketplace(page, url_marketplace):
    await page.goto(url_marketplace)
    await page.wait_for_load_state("networkidle")
    total_scroll = 0
    while total_scroll < 8000:
        scroll_length = random.randint(100, 500)
        await page.mouse.wheel(0, scroll_length)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        total_scroll += scroll_length
    await asyncio.sleep(random.uniform(0.5, 1.5))
    html = await page.content()
    return html


async def run_facebook_marketplace_crawler_and_parser(
    city_param,
    query_param,
    max_price_param,
    headless_param=True,
    item_condition_param="new",
):
    if city_param in cities:
        city = cities[city_param]
    else:
        raise ValueError(f"{city_param} is not supported.")

    url_login, url_marketplace = setup_urls_facebook_marketplace(
        query_param, max_price_param, item_condition_param, city
    )
    filepath = "data/posts_html.html"

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
            await save_html(html, filepath)

            df = parse_facebook_marketplace_listings(html)

        except TimeoutError:
            logger.error("Timeout occurred during the crawling process.")
            df = None
        finally:
            await context.close()
            await browser.close()

        return df


# ----------------------------------------------------------------------------
# # Run the server
# ----------------------------------------------------------------------------

if __name__ == "__main__":

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
