from bs4 import BeautifulSoup
import pandas as pd
import datetime
import logging

logger = logging.getLogger(__name__)


def parse_facebook_marketplace_listings(html, parsing_method="css"):
    soup = BeautifulSoup(html, "html.parser")

    logger.info("Getting HTML of all posts")
    soup_posts = soup.find_all(
        "div",
        class_="x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24",
    )

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

            if parsing_method == "llm":
                logger.info("Extracting post's data using LLM chain")
                try:
                    post_data = get_single_post_data_using_llm(
                        soup_single_post
                    )
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
                raise ValueError("Invalid parsing method")

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

        df = pd.DataFrame(result)

        if not df.empty:
            logger.info("Crawler returned data")

            filepath = f"data/results_bronze.csv"
            logger.info("Saving dataframe to CSV: Bronze")
            df.to_csv(filepath, index=False)

            logger.info("Saving dataframe to CSV: Silver")
            df = features_engineering(filepath)

            filepath = f"data/results_silver.csv"
            df.to_csv(filepath, index=False)
        return df
    else:
        logger.warn("No listing found")
        return pd.DataFrame()


def find_empty_html_divs(soup):
    div_tags = soup.find_all("div")
    empty_divs = [div for div in div_tags if not div.contents]
    return empty_divs


def get_single_post_data_using_css(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        item_div = soup.find("div", class_="x9f619")

        title_element = item_div.find(
            "span", class_="x1lliihq x6ikm8r x10wlt62 x1n2onr6"
        )
        title = (
            title_element.text.replace("\n", " ").strip()
            if title_element
            else "None"
        )

        price_element = item_div.find("span", class_="x193iq5w")
        price = price_element.text.strip() if price_element else "None"

        location_element = item_div.find("span", class_="x1nxh6w3")
        location = (
            location_element.text.strip() if location_element else "None"
        )

        item_number_element = item_div.find("a")
        item_number = (
            item_number_element["href"].split("/")[-2]
            if item_number_element
            else "None"
        )

        return title, price, location, item_number
    except Exception as e:
        print("An error occurred:", e)


def features_engineering(filepath):
    df = pd.read_csv(filepath)

    def clean_price(price):
        if "Gratuit" in price:
            return 0
        clean_price = (
            price.replace("€", "")
            .replace("$", "")
            .replace(" ", "")
            .replace(",", "")
        )
        return pd.to_numeric(clean_price, errors="coerce")

    df["cleaned_price"] = df["price"].apply(clean_price)

    prices = df["price"].str.extract(r"[$€]\s*([\d,]+)\s*[$€]?\s*([\d,]*)")
    df["price_before"] = pd.to_numeric(
        prices[1].str.replace(",", ""), errors="coerce"
    )
    df["price_after"] = pd.to_numeric(
        prices[0].str.replace(",", ""), errors="coerce"
    )

    df["price_difference"] = df["price_after"]
    df["price_difference"] = df["price_before"] - df["price_after"]
    return df
