import os
import urllib.parse
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

    if not client_id or not redirect_uri:
        return func.HttpResponse(
            "Missing GOOGLE_CLIENT_ID or GOOGLE_REDIRECT_URI in Function App settings",
            status_code=500
        )

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account"
    }

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return func.HttpResponse(status_code=302, headers={"Location": url})
