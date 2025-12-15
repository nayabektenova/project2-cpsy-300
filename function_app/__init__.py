import azure.functions as func
from azure.storage.blob import BlobServiceClient
import os
import pandas as pd
import json
import time
import io

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        start = time.time()

        # Query params (MATCH HTML)
        diet = req.params.get("diet")
        keyword = req.params.get("filter")

        # Blob connection
        conn = os.environ["AzureWebJobsStorage"]
        blob_service = BlobServiceClient.from_connection_string(conn)
        container = blob_service.get_container_client("outputs")

        # Read cached processed CSV (blob.readall() returns bytes; wrap in BytesIO for pandas)
        blob = container.download_blob("processed_data_with_metrics.csv")
        raw = blob.readall()
        df = pd.read_csv(io.BytesIO(raw))

        # Filtering (vectorized — fast)
        if diet:
            df = df[df["Diet_type"].str.lower() == diet.lower()]

        if keyword:
            keyword = keyword.lower()
            df = df[df.apply(
                lambda row: keyword in " ".join(row.astype(str)).lower(),
                axis=1
            )]

        elapsed_ms = int((time.time() - start) * 1000)

        response = {
            "rows_processed": len(df),
            "processing_time_ms": elapsed_ms,
            "uploaded_files": [
                "avg_macros_bar_chart.png",
                "macronutrient_heatmap.png",
                "top5_protein_scatter.png"
            ]
        }

        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
