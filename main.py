import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from database import create_db_and_tables, get_engine
from flask import jsonify, request
from sqlmodel import Session, select

from models import Link


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