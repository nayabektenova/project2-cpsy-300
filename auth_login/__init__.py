import json
import logging

import azure.functions as func

from shared.cosmos_client import users_container
from shared.auth_utils import verify_password, create_token



def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("auth_login function called")


    try:
        body = req.get_json()
    except ValueError:
        body = {}

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return func.HttpResponse(
            json.dumps({"error": "email and password are required"}),
            status_code=400,
            mimetype="application/json",
        )

    query = "SELECT * FROM c WHERE c.email = @email"
    params = [{"name": "@email", "value": email}]
    users = list(users_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
    ))

    if not users:
        return func.HttpResponse(
            json.dumps({"error": "invalid credentials"}),
            status_code=401,
            mimetype="application/json",
        )

    user = users[0]

    if not verify_password(password, user["passwordHash"]):
        return func.HttpResponse(
            json.dumps({"error": "invalid credentials"}),
            status_code=401,
            mimetype="application/json",
        )

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
        status_code=200,
        mimetype="application/json",
    )
