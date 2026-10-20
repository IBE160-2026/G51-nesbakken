"""Sprint 2: minimal end-to-end web flow (catalogue serving).
Story 1.4: the real stateless planning endpoint.

Serves the Newtown pilot catalogue's `ready` stops to the map in the
browser, and wraps the Planner + AI selection + content generation
pipeline into one POST /api/plan request/response (architecture AD-2 -
fully stateless, no server memory of a request survives past its
response).
"""

import json
import os

import requests
from flask import Flask, jsonify, render_template, request

import ai
import planner
import services

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "sydney_places.json")

app = Flask(__name__)


class CatalogueError(Exception):
    """Raised when the catalogue file is missing or not usable JSON."""

# The exact set of fields the frontend is allowed to see - deliberately
# excludes internal import-pipeline fields (osm_tags, status,
# rejection_reason, imported_at, osm_type).
PUBLIC_FIELDS = (
    "id",
    "name",
    "latitude",
    "longitude",
    "topics",
    "source_type",
    "source_title",
    "source_url",
    "source_excerpt",
)


def to_public_place(record):
    return {field: record.get(field) for field in PUBLIC_FIELDS}


def load_ready_places():
    if not os.path.exists(DATA_PATH):
        raise CatalogueError(f"catalogue file not found at {DATA_PATH}")
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            records = json.load(f)
    except json.JSONDecodeError as exc:
        raise CatalogueError(f"catalogue file is not valid JSON: {exc}") from exc
    if not isinstance(records, list):
        raise CatalogueError("catalogue file does not contain a JSON list")
    return [
        to_public_place(r) for r in records
        if isinstance(r, dict) and r.get("status") == "ready"
    ]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/places")
def api_places():
    try:
        places = load_ready_places()
    except CatalogueError as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify(places)


class PlanRequestError(Exception):
    """Raised for malformed/invalid /api/plan input - caught by the
    endpoint and turned into a 400, before any routing-provider or AI call
    is made (Story 1.4's own explicit requirement)."""


def _validate_plan_request(data):
    """Returns (start_lat, start_lon, topic, requested_minutes) if data is
    a well-formed plan request, else raises PlanRequestError with a
    human-readable reason. isinstance(x, bool) is excluded everywhere a
    number is expected - bool is a subclass of int in Python, so JSON
    `true`/`false` would otherwise silently pass as 1/0."""
    if not isinstance(data, dict):
        raise PlanRequestError("request body must be a JSON object")

    start_lat = data.get("start_lat")
    start_lon = data.get("start_lon")
    topic = data.get("topic")
    requested_minutes = data.get("requested_minutes")

    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    if not is_number(start_lat) or not (-90 <= start_lat <= 90):
        raise PlanRequestError("start_lat must be a number between -90 and 90")
    if not is_number(start_lon) or not (-180 <= start_lon <= 180):
        raise PlanRequestError("start_lon must be a number between -180 and 180")
    if topic not in planner.VALID_TOPICS:
        raise PlanRequestError(
            f"topic must be one of: {', '.join(sorted(planner.VALID_TOPICS))}"
        )
    if not is_number(requested_minutes) or not (
        planner.MIN_REQUESTED_MINUTES <= requested_minutes <= planner.MAX_REQUESTED_MINUTES
    ):
        raise PlanRequestError(
            f"requested_minutes must be a number between "
            f"{planner.MIN_REQUESTED_MINUTES} and {planner.MAX_REQUESTED_MINUTES}"
        )

    return start_lat, start_lon, topic, requested_minutes


@app.route("/api/plan", methods=["POST"])
def api_plan():
    """Stateless planning endpoint (Story 1.4, architecture AD-2): wraps
    planner.plan_route() + real route geometry + ai.generate_stop_content()
    into one request/response. No server memory of this request survives
    past the response it returns.

    Three distinct outcomes:
    - feasible route: 200, full route with generated content/attribution
      and (when available) real geometry.
    - honest "no suitable walk" (zero feasible combinations, or AI's own
      none_suitable judgement - AD-7): 200, {"feasible": false, "reason"}.
    - a genuine AI/service failure (ai.AiFatalError) or a routing-provider
      failure: a real non-2xx, never the {"feasible": false} shape.
    """
    try:
        start_lat, start_lon, topic, requested_minutes = _validate_plan_request(
            request.get_json(silent=True)
        )
    except PlanRequestError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        result = planner.plan_route(start_lat, start_lon, topic, requested_minutes)
    except ai.AiFatalError as exc:
        return jsonify({"error": str(exc)}), 503
    except requests.RequestException as exc:
        # A genuine routing-provider failure (fetch_duration_matrix) -
        # same "real service failure, not ordinary infeasibility" treatment
        # as an AI fatal error, mirroring the existing CatalogueError
        # pattern above.
        return jsonify({"error": f"routing service error: {exc}"}), 503

    if not result["feasible"]:
        return jsonify({"feasible": False, "reason": result["reason"]})

    ordered_stops = [result["shortlist"][i - 1] for i in result["order"]]

    try:
        ordered_points = (
            [(start_lat, start_lon)]
            + [(stop["latitude"], stop["longitude"]) for stop in ordered_stops]
            + [(start_lat, start_lon)]
        )
        geometry = services.fetch_route_geometry(ordered_points)
    except requests.RequestException as exc:
        # User's explicit choice (Story 1.4 spec): geometry is a nice-to-
        # have for display, not what makes a route valid - degrade, don't
        # fail an otherwise-good route over it (matches AD-3's existing
        # content-generation resilience philosophy).
        print(f"Route geometry fetch failed, continuing without it: {exc}")
        geometry = None

    content_results = ai.generate_stop_content(ordered_stops, topic)
    content_by_id = {c["id"]: c for c in content_results}

    stops_response = [
        {
            "id": stop["id"],
            "order": position,
            "content": content_by_id[stop["id"]]["content"],
            "attribution": content_by_id[stop["id"]]["attribution"],
        }
        for position, stop in enumerate(ordered_stops, start=1)
    ]

    return jsonify({
        "feasible": True,
        "total_minutes": result["total_minutes"],
        "unused_minutes": result["unused_minutes"],
        "geometry": geometry,
        "stops": stops_response,
    })


if __name__ == "__main__":
    app.run(debug=True)
