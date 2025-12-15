import azure.functions as func
from azure.storage.blob import BlobServiceClient
import os
import json

# UPDATED FUNCTION: No longer calls "run_analysis()", now only reads cached data.
def main(req: func.HttpRequest) -> func.HttpResponse: 
    try:
        #Variables
        connection_string = os.environ["AzureWebJobsStorage"]
        blob_storage = BlobServiceClient.from_connection_string(connection_string)

        container = blob_storage.get_container_client("outputs")
        blob = container.download_blob("processed_data_with_metrics.csv")
        data = blob.readall().decode("utf-8")

        return func.HttpResponse(
            data, 
            mimetype = "text/csv",
            status_code = 200
        )
    
    except Exception as e:
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code = 500
        )

