import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from database import create_db_and_tables, get_engine
from flask import jsonify, request
from sqlmodel import Session, select

from models import Link
from urllib.parse import urlparse

from sqlalchemy.exc import IntegrityError


sentry_dsn = os.getenv("SENTRY_DSN")

if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FlaskIntegration()],
    )

app = Flask(__name__)

if os.getenv("DATABASE_URL"):
    create_db_and_tables()


@app.get("/ping")
def ping():
    return "pong"

def link_to_dict(link):
    base_url = os.getenv("BASE_URL") or request.host_url.rstrip("/")

    return {
        "id": link.id,
        "original_url": link.original_url,
        "short_name": link.short_name,
        "short_url": f"{base_url.rstrip('/')}/r/{link.short_name}",
    }

@app.get("/api/links")
def get_links():
    with Session(get_engine()) as session:
        links = session.exec(
            select(Link).order_by(Link.id)
        ).all()

    return jsonify([link_to_dict(link) for link in links])

@app.post("/api/links")
def create_link():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"detail": "Expected a JSON object"}), 422

    original_url = data.get("original_url")
    short_name = data.get("short_name")

    errors = {}

    if not isinstance(original_url, str) or not original_url.strip():
        errors["original_url"] = "URL is required"
    else:
        parsed_url = urlparse(original_url)
        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            errors["original_url"] = "Invalid URL"

    if not isinstance(short_name, str) or not short_name.strip():
        errors["short_name"] = "Short name is required"

    if errors:
        return jsonify({"detail": errors}), 422

    with Session(get_engine()) as session:
        link = Link(
            original_url=original_url,
            short_name=short_name,
        )

        session.add(link)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return jsonify({
                "detail": {
                    "short_name": "Short name already exists"
                }
            }), 422

        session.refresh(link)

        return jsonify(link_to_dict(link)), 201