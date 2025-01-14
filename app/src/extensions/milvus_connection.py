from pymilvus import connections
from dotenv import load_dotenv
import os

def init_milvus():
    """Connect Milvus to the Flask app using env."""
    load_dotenv()
    host = os.getenv("MILVUS_HOST")
    port = os.getenv("MILVUS_PORT")
    connections.connect(
        alias="default",
        host=host,
        port=port
    )

