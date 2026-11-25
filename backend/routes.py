import json
import os

from flask import Blueprint, jsonify, redirect, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.database import get_engine
from backend.models import Link
from backend.schemas import validate_link_data


api_bp = Blueprint("api", __name__)

@api_bp.get("/ping")
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

@api_bp.get("/api/links")
def get_links():
    range_param = request.args.get("range")

    if range_param is not None:
        try:
            bounds = json.loads(range_param)

            if (
                not isinstance(bounds, list)
                or len(bounds) != 2
                or any(type(value) is not int for value in bounds)
                or bounds[0] < 0
                or bounds[1] < bounds[0]
            ):
                raise ValueError("Invalid range")

            start, end = bounds

        except (ValueError, TypeError):
            return jsonify({"detail": "Invalid range"}), 422

    with Session(get_engine()) as session:
        total = session.exec(
            select(func.count(Link.id))
        ).one()

        if range_param is None:
            start, end = 0, total

        start = min(start, total)
        end = min(end, total)

        links = session.exec(
            select(Link)
            .order_by(Link.id)
            .offset(start)
            .limit(end - start)
        ).all()

    response = jsonify([link_to_dict(link) for link in links])

    response.headers["Content-Range"] = f"links {start}-{end}/{total}"

    return response

@api_bp.post("/api/links")
def create_link():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "detail": {
                "body": "Expected a JSON object"
            }
        }), 422

    link_data, errors = validate_link_data(data)

    if errors is not None:
        return jsonify({"detail": errors}), 422

    original_url = link_data.original_url
    short_name = link_data.short_name

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


@api_bp.get("/api/links/<int:link_id>")
def get_link(link_id):
    with Session(get_engine()) as session:
        link = session.get(Link, link_id)

        if link is None:
            return jsonify({"detail": "Link not found"}), 404

        return jsonify(link_to_dict(link)), 200



@api_bp.put("/api/links/<int:link_id>")
def update_link(link_id):
    with Session(get_engine()) as session:
        link = session.get(Link, link_id)

        if link is None:
            return jsonify({"detail": "Link not found"}), 404

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "detail": {
                    "body": "Expected a JSON object"
                }
            }), 422

        link_data, errors = validate_link_data(data)

        if errors is not None:
            return jsonify({"detail": errors}), 422

        original_url = link_data.original_url
        short_name = link_data.short_name

        link.original_url = original_url
        link.short_name = short_name

        try:
            session.add(link)
            session.commit()
        except IntegrityError:
            session.rollback()
            return jsonify({
                "detail": {
                    "short_name": "Short name already exists"
                }
            }), 422

        session.refresh(link)

        return jsonify(link_to_dict(link)), 200

@api_bp.delete("/api/links/<int:link_id>")
def delete_link(link_id):
    with Session(get_engine()) as session:
        link = session.get(Link, link_id)

        if link is None:
            return jsonify({"detail": "Link not found"}), 404

        session.delete(link)
        session.commit()

    return "", 204

@api_bp.get("/r/<short_name>")
def redirect_link(short_name):
    with Session(get_engine()) as session:
        link = session.exec(
            select(Link).where(Link.short_name == short_name)
        ).first()

        if link is None:
            return jsonify({"detail": "Link not found"}), 404

        original_url = link.original_url

    return redirect(original_url, code=302)
