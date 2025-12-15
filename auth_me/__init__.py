import json
import logging

import azure.functions as func
import jwt  # from PyJWT

from shared.auth_utils import decode_token



def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("auth_me function called")

    auth_header = req.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return func.HttpResponse(
            json.dumps({"error": "missing or invalid Authorization header"}),
            status_code=401,
            mimetype="application/json",
        )

    token = auth_header.split(" ", 1)[1].strip()

    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError:
        return func.HttpResponse(
            json.dumps({"error": "invalid or expired token"}),
            status_code=401,
            mimetype="application/json",
        )

    resp = {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
    }

    return func.HttpResponse(
        json.dumps(resp),
        status_code=200,
        mimetype="application/json",
    )
