from io import StringIO

import pandas as pd
import requests
import streamlit as st
from rich import print

from tools.config import cities
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create a title for the web app.
st.title("Web Crawler & Scraper")
st.header("Facebook Marketplace")

# Add a list of supported cities.
supported_cities = list(cities.keys())

# Take user input for the city, query, and max price.
city = st.selectbox("City", supported_cities, 0)
query = st.text_input("Query", "Macbook Pro")
max_price = st.text_input("Max Price", "1000")

# Create a button to submit the form.
submit = st.button("Submit")

# If the button is clicked.
if submit:
    logger.info("Submitted!")

    # Create the request url.
    URL = f"http://127.0.0.1:8000/crawler?city={city}&query={query}&max_price={max_price}"

    logger.info("Request URL: {}".format(URL))
    response = requests.get(URL)

    logger.info("Response Code: {}".format(response.status_code))
    response_json = response.json()

    # Check the status code of the request.
    if response.status_code == 200:
        if response_json["data"] is None:
            st.write("No results found")
            df = None
        else:
            # Use StringIO to create a file-like object from the JSON string
            data_io = StringIO(response_json["data"])
            df = pd.read_json(data_io)
            st.write(df)
    else:
        logger.error(
            f"Request failed with status code: {response.status_code}"
        )
