# diagram.py
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.framework import Fastapi
from diagrams.saas.social import Facebook
from diagrams.onprem.client import User, Client
from diagrams.generic.storage import Storage
from diagrams.onprem.compute import Server

# Define the attributes for the graph
graph_attr = {"fontsize": "45"}

# Create the diagram
with Diagram(
    "",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    filename="assets/media/diagram",
):
    # Define the user interface component
    user = User("User")

    # Define the connection style
    edge = Edge(color="black", style="bold")

    # Define the clusters for the architecture components
    with Cluster("Flows"):
        with Cluster("Webapp"):
            # Define the client dashboard
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

    # Define the relationships between components
    user >> edge >> client
    client >> edge >> fast_api
    fast_api >> edge >> facebook_crawler
    fast_api >> edge >> data_processing
    data_processing - csv_storage
