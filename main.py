import os

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from backend.database import create_db_and_tables

from backend.routes import api_bp

from flask_cors import CORS


sentry_dsn = os.getenv("SENTRY_DSN")

if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FlaskIntegration()],
    )

app = Flask(
    __name__,
    static_folder="frontend_dist",
    static_url_path="",
)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Range"],
        }
    },
)

app.register_blueprint(api_bp)

if os.getenv("DATABASE_URL"):
    create_db_and_tables()


@app.get("/")
def frontend():
    return app.send_static_file("index.html")