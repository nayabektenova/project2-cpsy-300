import os
from azure.cosmos import CosmosClient

COSMOS_CONN_STRING = os.environ["COSMOS_CONN_STRING"]
COSMOS_DB_NAME = os.environ["COSMOS_DB_NAME"]
COSMOS_USERS_CONTAINER = os.environ["COSMOS_USERS_CONTAINER"]

_client = CosmosClient.from_connection_string(COSMOS_CONN_STRING)
_db = _client.get_database_client(COSMOS_DB_NAME)
users_container = _db.get_container_client(COSMOS_USERS_CONTAINER)
