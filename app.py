"""Sprint 2: minimal end-to-end web flow (catalogue serving).
Story 1.4: the real stateless planning endpoint.

Serves the Newtown pilot catalogue's `ready` stops to the map in the
browser, and wraps the Planner + AI selection + content generation
pipeline into one POST /api/plan request/response (architecture AD-2 -
fully stateless, no server memory of a request survives past its
response).
"""

import json
import math
import os

import requests
from flask import Flask, jsonify, render_template, request

import ai
import planner
import services

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "sydney_places.json")

app = Flask(__name__)
# Codex review 2026-10-21 (follow-up): the spec promised oversized-body
# rejection, but nothing actually enforced a limit - a real request body
# here is 4 small fields (two floats, a short string, an int), so this is
# generous, not tight. Flask/Werkzeug reject anything over this before the
# body is even fully read into memory.
app.config["MAX_CONTENT_LENGTH"] = 4096


@app.errorhandler(413)
def _request_too_large(_exc):
    # Matches every other /api/plan error response's {"error": "..."}
    # shape, rather than Werkzeug's default HTML error page.
    return jsonify({"error": "request body too large"}), 413


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
    """Returns (start_lat, start_lon, topic, requested_minutes,
    excluded_ids) if data is a well-formed plan request, else raises
    PlanRequestError with a human-readable reason. isinstance(x, bool) is
    excluded everywhere a number is expected - bool is a subclass of int
    in Python, so JSON `true`/`false` would otherwise silently pass as
    1/0."""
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
    # Codex review 2026-10-21: `topic not in VALID_TOPICS` on a set raises
    # TypeError for an unhashable JSON value (a list or object) instead of
    # a controlled rejection - a real crash, not just a theoretical one.
    if not isinstance(topic, str) or topic not in planner.VALID_TOPICS:
        raise PlanRequestError(
            f"topic must be one of: {', '.join(sorted(planner.VALID_TOPICS))}"
        )
    # Codex review 2026-10-21: a float like 30.0 passed is_number() and
    # check_feasibility()'s own range check, but floor division on a float
    # (max_stops_for_request()) produces a float max_size, which then
    # crashes range() deep inside the planner instead of being rejected
    # here. Also enforces the same 5-minute increments the UI already
    # only ever sends (static/app.js's wheel picker), not just the 30-120
    # range, for the same defense-in-depth reasoning as that client-side
    # validation.
    if (
        not isinstance(requested_minutes, int)
        or isinstance(requested_minutes, bool)
        or not (planner.MIN_REQUESTED_MINUTES <= requested_minutes <= planner.MAX_REQUESTED_MINUTES)
        or requested_minutes % 5 != 0
    ):
        raise PlanRequestError(
            f"requested_minutes must be an integer between "
            f"{planner.MIN_REQUESTED_MINUTES} and {planner.MAX_REQUESTED_MINUTES}, "
            f"in 5-minute increments"
        )

    # Story 1.7: optional Re-Jaunt exclusion list (AD-5) - absent on
    # every request before the first Re-Jaunt, so it defaults to "exclude
    # nothing" rather than being required. Bounded the same defense-in-
    # depth way every other field here is (bmad-code-review 2026-10-22) -
    # the real catalogue has 226 places, so a legitimate client can never
    # need more than that many real, short ids.
    excluded_ids = data.get("excluded_ids", [])
    if (
        not isinstance(excluded_ids, list)
        or len(excluded_ids) > 500
        or not all(
            isinstance(item, str) and len(item) <= 200 for item in excluded_ids
        )
    ):
        raise PlanRequestError("excluded_ids must be a list of at most 500 strings, each at most 200 characters")

    replacement_mode = data.get("replacement_mode", False)
    if not isinstance(replacement_mode, bool):
        raise PlanRequestError("replacement_mode must be a boolean")
    retained_ids = data.get("retained_ids", [])
    if (not isinstance(retained_ids, list) or len(retained_ids) > 6
            or not all(isinstance(id_, str) and 0 < len(id_) <= 200 for id_ in retained_ids)
            or len(set(retained_ids)) != len(retained_ids)):
        raise PlanRequestError("retained_ids must contain at most six unique place IDs")
    if retained_ids and not replacement_mode:
        raise PlanRequestError("retained_ids requires replacement_mode")
    if set(retained_ids).intersection(excluded_ids):
        raise PlanRequestError("retained_ids cannot overlap excluded_ids")
    if retained_ids:
        ready_ids = {p["id"] for p in load_ready_places()}
        if not set(retained_ids).issubset(ready_ids):
            raise PlanRequestError("retained_ids must identify ready catalogue places")

    return start_lat, start_lon, topic, requested_minutes, excluded_ids, retained_ids, replacement_mode


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
        start_lat, start_lon, topic, requested_minutes, excluded_ids, retained_ids, replacement_mode = _validate_plan_request(
            request.get_json(silent=True)
        )
    except PlanRequestError as exc:
        return jsonify({"error": str(exc)}), 400
    except CatalogueError as exc:
        return jsonify({"error": str(exc)}), 503

    try:
        options = {"excluded_ids": excluded_ids}
        if replacement_mode:
            options.update(retained_ids=retained_ids, replacement_mode=True)
        result = planner.plan_route(
            start_lat, start_lon, topic, requested_minutes, **options
        )
    except ai.AiFatalError as exc:
        return jsonify({"error": str(exc)}), 503
    except ai.AiExhaustedError as exc:
        # Every retry attempt failed without AI ever producing a usable
        # selection - a persistent service/response problem, not an
        # honest "no suitable walk" (Codex review 2026-10-21).
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
    except (requests.RequestException, KeyError, IndexError, TypeError) as exc:
        # User's explicit choice (Story 1.4 spec): geometry is a nice-to-
        # have for display, not what makes a route valid - degrade, don't
        # fail an otherwise-good route over it (matches AD-3's existing
        # content-generation resilience philosophy). Codex review
        # 2026-10-21: a malformed-but-200 provider response (e.g. an empty
        # "features" array) raised KeyError/IndexError, which only the
        # RequestException catch here missed entirely - this is the same
        # "expected provider-shape failure" as a network error, not a real
        # programming bug, so it gets the same controlled degradation.
        if replacement_mode:
            return jsonify({"error": f"replacement route geometry could not be verified: {exc}"}), 503
        print(f"Route geometry fetch failed, continuing without it: {exc}")
        geometry = None

    if replacement_mode and not (
        isinstance(geometry, list) and len(geometry) >= 2
        and all(isinstance(point, (list, tuple)) and len(point) == 2
                and all(isinstance(value, (int, float)) and not isinstance(value, bool)
                        and math.isfinite(value) for value in point)
                and -180 <= point[0] <= 180 and -90 <= point[1] <= 90
                for point in geometry)
    ):
        return jsonify({"error": "replacement route geometry is unusable"}), 503

    content_results = ai.generate_stop_content(ordered_stops, topic)
    content_by_id = {c["id"]: c for c in content_results}

    # Codex review 2026-10-21: the response originally carried only id/
    # order/content/attribution - Route Review (Story 1.5) needs a name
    # and coordinates to show a marker/list entry at all, and would
    # otherwise have to separately fetch and join against /api/places
    # (which returns the whole catalogue, not a lookup by id) just to
    # render its own response. These four extra fields are already on
    # each stop dict at zero extra cost - no second request required.
    stops_response = [
        {
            "id": stop["id"],
            "order": position,
            "name": stop.get("name"),
            "latitude": stop.get("latitude"),
            "longitude": stop.get("longitude"),
            "topics": stop.get("topics", []),
            "content": content_by_id[stop["id"]]["content"],
            "attribution": content_by_id[stop["id"]]["attribution"],
        }
        for position, stop in enumerate(ordered_stops, start=1)
    ]

    return jsonify({
        "feasible": True,
        **({"replacement_outcome": result["replacement_outcome"]} if replacement_mode else {}),
        "total_minutes": result["total_minutes"],
        "unused_minutes": result["unused_minutes"],
        "geometry": geometry,
        "stops": stops_response,
    })


if __name__ == "__main__":
    app.run(debug=True)
