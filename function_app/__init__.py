import azure.functions as func
from data_analysis import run_analysis
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        summary = run_analysis()
        return func.HttpResponse(
            json.dumps(summary),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
