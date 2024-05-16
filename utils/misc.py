import urllib.parse

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
