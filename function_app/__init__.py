import azure.functions as func
from azure.storage.blob import BlobServiceClient
import os
import pandas as pd
import json
import math

# UPDATED FUNCTION: HTTP Function reads cached data rather than running the entire calculation again.
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Query params
        diet = req.params.get("diet")
        keyword = req.params.get("q")
        page = int(req.params.get("page", 1))
        page_size = int(req.params.get("pageSize", 20))

        # Connect to storage
        conn = os.environ["AzureWebJobsStorage"]
        blob_service = BlobServiceClient.from_connection_string(conn)

        container = blob_service.get_container_client("outputs")
        blob = container.download_blob("processed_data_with_metrics.csv")
        df = pd.read_csv(blob)

        # ---- Filtering ----
        if diet:
            df = df[df["Diet_type"] == diet]

        if keyword:
            df = df[df.apply(
                lambda row: keyword.lower() in row.astype(str).str.lower().to_string(),
                axis=1
            )]

        # ---- Pagination ----
        total_rows = len(df)
        total_pages = math.ceil(total_rows / page_size)
        start = (page - 1) * page_size
        end = start + page_size

        paged_df = df.iloc[start:end]

        response = {
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
            "totalRows": total_rows,
            "data": paged_df.to_dict(orient="records")
        }

        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
