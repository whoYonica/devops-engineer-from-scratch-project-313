import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from database import create_db_and_tables


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