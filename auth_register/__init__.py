import json
import logging
import uuid

import azure.functions as func

from shared.cosmos_client import users_container
from shared.auth_utils import hash_password, create_token



def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("auth_register function called")

    try:
        body = req.get_json()
    except ValueError:
        body = {}

    email = body.get("email")
    password = body.get("password")
    name = body.get("name")

    if not email or not password or not name:
        return func.HttpResponse(
            json.dumps({"error": "email, password and name are required"}),
            status_code=400,
            mimetype="application/json",
        )

    if len(password) < 8:
        return func.HttpResponse(
            json.dumps({"error": "password must be at least 8 characters"}),
            status_code=400,
            mimetype="application/json",
        )

    # check if email already exists
    query = "SELECT * FROM c WHERE c.email = @email"
    params = [{"name": "@email", "value": email}]
    existing = list(users_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
    ))

    if existing:
        return func.HttpResponse(
            json.dumps({"error": "email already registered"}),
            status_code=409,
            mimetype="application/json",
        )

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "passwordHash": hash_password(password),
        "name": name,
        "provider": "local",
        "providerId": None,
        "createdAt": dt_now_iso(),
    }

    users_container.create_item(user)

    token = create_token(user)

    resp = {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
        },
    }

    return func.HttpResponse(
        json.dumps(resp),
        status_code=201,
        mimetype="application/json",
    )


def dt_now_iso():
    import datetime as dt
    return dt.datetime.utcnow().isoformat() + "Z"
