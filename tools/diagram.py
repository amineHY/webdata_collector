# diagram.py
from diagrams import Diagram
from diagrams import Cluster, Diagram, Edge

# from diagrams.custom import Custom
from diagrams.programming.framework import Fastapi
from diagrams.saas.social import Facebook
from diagrams.onprem.client import User, Client
from diagrams.generic.storage import Storage
from diagrams import Cluster
from diagrams.onprem.compute import Server


# from diagrams.generic.process import Process
graph_attr = {"fontsize": "45"}
with Diagram(
    "Crawler and Scraper Architecture",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    filename="assets/media/diagram",
):
    # Define the Streamlit dashboard as a user interface
    user = User("User")

    with Cluster("Flows"):
        with Cluster("Webapp"):
            # Define
            client = Client("Dashboard")

            # Define the FastAPI backend
            fast_api = Fastapi("Fast API Backend")
        with Cluster("Target Website"):

            # Define the Facebook Marketplace crawler
            facebook_crawler = Facebook("Crawler")

        with Cluster("Data Processing"):
            # Define the data processing component
            data_processing = Server("Processing Engine")

            # Define the CSV file storage
            csv_storage = Storage("Data Storage")

    # Define the connections

    client >> Edge(color="black", style="bold") << fast_api
    (fast_api >> Edge(color="black", style="bold") << facebook_crawler)
    user >> Edge(color="black", style="bold") >> client
    data_processing - csv_storage
    # (csv_storage >> Edge(color="black", style="bold") >> client)
    fast_api >> Edge(color="black", style="bold") >> data_processing
