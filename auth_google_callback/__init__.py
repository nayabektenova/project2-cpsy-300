import os
import json
import uuid
import datetime
import urllib.parse
import logging
import requests
import azure.functions as func

from shared.cosmos_client import users_container
from shared.auth_utils import create_token

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("auth_google_callback called")

    code = req.params.get("code")
    if not code:
        return func.HttpResponse("Missing code", status_code=400)

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    frontend = os.environ.get("FRONTEND_BASE_URL")

    if not all([client_id, client_secret, redirect_uri, frontend]):
        return func.HttpResponse(
            "Missing one of GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET/GOOGLE_REDIRECT_URI/FRONTEND_BASE_URL",
            status_code=500
        )

    # 1) Exchange code for access token
    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )

    if token_res.status_code != 200:
        return func.HttpResponse(
            f"Token exchange failed: {token_res.text}",
            status_code=400
        )

    access_token = token_res.json().get("access_token")
    if not access_token:
        return func.HttpResponse("No access_token returned", status_code=400)

    # 2) Fetch profile info
    info_res = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )

    if info_res.status_code != 200:
        return func.HttpResponse(
            f"Userinfo failed: {info_res.text}",
            status_code=400
        )

    profile = info_res.json()
    email = (profile.get("email") or "").strip().lower()
    name = (profile.get("name") or "").strip() or "Google User"

    if not email:
        return func.HttpResponse("Google profile had no email", status_code=400)

    # 3) Upsert user in Cosmos (provider=google)
    query = "SELECT * FROM c WHERE c.email = @email"
    params = [{"name": "@email", "value": email}]
    existing = list(users_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
    ))

    now = datetime.datetime.utcnow().isoformat() + "Z"

    if existing:
        user = existing[0]
        user["name"] = name
        user["provider"] = "google"
        user["updatedAt"] = now
        users_container.upsert_item(user)
    else:
        user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": name,
            "provider": "google",
            "createdAt": now,
        }
        users_container.create_item(user)

    # 4) Create JWT and redirect back to your Static Web App
    token = create_token(user)

    frag = urllib.parse.urlencode({
        "token": token,
        "name": user.get("name", ""),
        "email": user.get("email", "")
    })

    redirect_url = f"{frontend}/#{frag}"
    return func.HttpResponse(status_code=302, headers={"Location": redirect_url})
