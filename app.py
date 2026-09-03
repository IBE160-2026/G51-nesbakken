"""Sprint 2: minimal end-to-end web flow.

Serves the Newtown pilot catalogue's `ready` stops to a Leaflet map in the
browser. No filtering, no AI, no time-budget logic yet - this sprint only
proves the plumbing (backend, frontend, map rendering, data serialization)
works before more logic is layered on in later sprints.
"""

import json
import os

from flask import Flask, jsonify, render_template

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


if __name__ == "__main__":
    app.run(debug=True)
