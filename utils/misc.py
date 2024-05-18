import urllib.parse
from pydantic import BaseModel


class QueryParams(BaseModel):
    """
    A class representing the query parameters for setting up URLs for Facebook Marketplace.

    Attributes:
        city (str): The city for the marketplace search.
        query (str): The query string for the search.
        max_price (float): The maximum price for the search.
        itemCondition (str): The condition of the items for the search.
        headless (bool, optional): Whether to run the browser in headless mode. Defaults to True.
        strategy (str): The strategy for the search.
        llm_choice (str): The choice for the llm (low-level model) search.
        model_name (str): The name of the model.

    """

    city: str
    query: str
    max_price: float
    itemCondition: str
    headless: bool = True
    strategy: str
    llm_choice: str
    model_name: str


cities = {
    "Paris": "paris",
    "New York": "nyc",
    "Los Angeles": "la",
    "Las Vegas": "vegas",
    "Chicago": "chicago",
    "Houston": "houston",
    "San Antonio": "sanantonio",
    "Miami": "miami",
    "Orlando": "orlando",
    "San Diego": "sandiego",
    "Arlington": "arlington",
    "Balitmore": "baltimore",
    "Cincinnati": "cincinnati",
    "Denver": "denver",
    "Fort Worth": "fortworth",
    "Jacksonville": "jacksonville",
    "Memphis": "memphis",
    "Nashville": "nashville",
    "Philadelphia": "philly",
    "Portland": "portland",
    "San Jose": "sanjose",
    "Tucson": "tucson",
    "Atlanta": "atlanta",
    "Boston": "boston",
    "Columnbus": "columbus",
    "Detroit": "detroit",
    "Honolulu": "honolulu",
    "Kansas City": "kansascity",
    "New Orleans": "neworleans",
    "Phoenix": "phoenix",
    "Seattle": "seattle",
    "Washington DC": "dc",
    "Milwaukee": "milwaukee",
    "Sacremento": "sac",
    "Austin": "austin",
    "Charlotte": "charlotte",
    "Dallas": "dallas",
    "El Paso": "elpaso",
    "Indianapolis": "indianapolis",
    "Louisville": "louisville",
    "Minneapolis": "minneapolis",
    "Oaklahoma City": "oklahoma",
    "Pittsburgh": "pittsburgh",
    "San Francisco": "sanfrancisco",
    "Tampa": "tampa",
}


def setup_urls_facebook_marketplace(query, max_price, city, item_condition):
    """
    Set up URLs for Facebook Marketplace search.

    Args:
        query (str): The query string for the search.
        max_price (float): The maximum price for the search.
        city (str): The city for the marketplace search.
        item_condition (str): The condition of the items for the search.

    Returns:
        tuple: A tuple containing the login URL and the marketplace URL.

    """
    url_login = "https://www.facebook.com/login"
    base_url_marketplace = (
        f"https://www.facebook.com/marketplace/{city}/search/"
    )

    query_params = {
        "query": query,
        "maxPrice": max_price,
        "itemCondition": item_condition,
        "exact": "true",
    }
    encoded_query_params = urllib.parse.urlencode(query_params)
    url_marketplace = f"{base_url_marketplace}?{encoded_query_params}"

    return url_login, url_marketplace
