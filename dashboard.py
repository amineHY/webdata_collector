import logging
from io import StringIO

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from utils.misc import cities

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_data(
    city,
    query,
    max_price,
    item_condition,
    headless,
    strategy,
    llm_choice,
    model_name,
):
    url = (
        f"http://127.0.0.1:8000/crawler/?"
        f"city={city}&query={query}&max_price={max_price}&itemCondition={item_condition}&headless={headless}&strategy={strategy}&llm_choice={llm_choice}&model_name={model_name}"
    )
    logger.info(f"Request URL: {url}")
    response = requests.get(url)

    logger.info(f"Response Code: {response.status_code}")

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(
            f"Request failed with status code: {response.status_code}"
        )
        return None


def choose_strategy(strategy):
    if strategy == "LLM":
        llm_choice = st.sidebar.selectbox(
            "Choose between OpenAI or Ollama", ["OpenAI", "Ollama"]
        )
        model_name = st.sidebar.selectbox(
            (
                "Choose OpenAI model name"
                if llm_choice == "OpenAI"
                else "Choose Ollama model"
            ),
            (
                ["gpt-4", "gpt-3.5-turbo"]
                if llm_choice == "OpenAI"
                else ["llama2", "llama3"]
            ),
        )
    elif strategy == "CSS":
        llm_choice, model_name = None, None
    return strategy, llm_choice, model_name


# Streamlit app setup
st.title("Web Crawler & Scraper")
st.header("Facebook Marketplace")

# Get supported cities
supported_cities = list(cities.keys())

# Sidebar user inputs
st.sidebar.title("Search options")
city = st.sidebar.selectbox("City", supported_cities, 0)
query = st.sidebar.text_input("Product Name", "Macbook Pro")
max_price = st.sidebar.text_input("Max Price", "1000")
selected_condition = st.sidebar.selectbox(
    "Condition", ["new", "used_like_new", "used_good", "used_fair"], index=1
)

# Create an expander for the sidebar menu
with st.sidebar.expander("Parameters", expanded=True):
    headless = st.selectbox("Headless Browser", [True, False], index=0)
    choice = st.selectbox("Choose between CSS or LLM", ("CSS", "LLM"))
    # You would need to define your choose_strategy function
    strategy, llm_choice, model_name = choose_strategy(choice)

submit = st.sidebar.button("Submit")

if submit:
    logger.info("Form Submitted")
    response_json = fetch_data(
        city,
        query,
        max_price,
        selected_condition,
        headless,
        strategy,
        llm_choice,
        model_name,
    )

    if response_json:
        data = response_json.get("data")
        if data is None:
            st.write("No results found")
        else:
            # Convert JSON response to DataFrame
            try:
                data_io = StringIO(data)
                df = pd.read_json(data_io)
                st.write(df)

                # Plot: Group by Location and Count
                location_counts = df["location"].value_counts().reset_index()
                location_counts.columns = ["Location", "Count"]

                fig1 = px.bar(
                    location_counts,
                    x="Location",
                    y="Count",
                    title="Number of Items Listed per Location",
                )
                st.plotly_chart(fig1)

                # Plot: Price Distribution
                fig2 = px.histogram(
                    df,
                    x="cleaned_price",
                    nbins=10,
                    title="Price Distribution of Listed Items",
                )
                st.plotly_chart(fig2)

                # Plot: Average Price per Location
                avg_price_per_location = (
                    df.groupby("location")["cleaned_price"]
                    .mean()
                    .reset_index()
                )
                fig3 = px.bar(
                    avg_price_per_location,
                    x="location",
                    y="cleaned_price",
                    title="Average Price per Location",
                )
                st.plotly_chart(fig3)

                # Additional plots suggestions
                # 1. Distribution of items per price range
                fig4 = px.histogram(
                    df,
                    x="cleaned_price",
                    title="Distribution of Items per Price Range",
                    labels={"cleaned_price": "Price (€)"},
                )
                st.plotly_chart(fig4)

                # 2. Box plot to show the spread and outliers of prices per location
                fig5 = px.box(
                    df,
                    x="location",
                    y="cleaned_price",
                    title="Price Spread per Location",
                    labels={
                        "cleaned_price": "Price (€)",
                        "location": "Location",
                    },
                )
                st.plotly_chart(fig5)
            except ValueError as e:
                logger.error(f"Error reading JSON data: {e}")
                st.error(
                    "Error reading data. Please check the format of the returned data."
                )
    else:
        st.write("Failed to retrieve data. Please try again.")
