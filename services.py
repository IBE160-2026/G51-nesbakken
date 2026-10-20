"""The routing live-at-runtime external calls (the other external call is
ai.py's OpenAI call, added in Sprint 4).

Sprint 3 needs the distance/duration matrix (for shortlist feasibility
checks). Story 1.4 adds the real route geometry for the chosen, ordered
stops - a separate OpenRouteService endpoint, not derivable from the
duration matrix alone (the matrix is point-to-point durations only, never
an actual walked path).
"""

import os

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
MATRIX_URL = "https://api.openrouteservice.org/v2/matrix/foot-walking"
# The /geojson variant - verified directly against the live API before this
# was written (not assumed) - returns a real GeoJSON LineString directly,
# vs. the plain endpoint's encoded polyline string that would need
# decoding on either side. Matches the frontend's existing MapLibre/GeoJSON
# rendering approach (architecture AD-1) with no extra conversion step.
DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking/geojson"


def load_env(path=ENV_PATH):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def get_api_key():
    load_env()
    api_key = os.environ.get("OPENROUTESERVICE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTESERVICE_API_KEY not found. Check your .env file at the project root."
        )
    return api_key


def fetch_duration_matrix(points):
    """points: a list of (lat, lon) tuples; the first is the start point.

    Returns a durations matrix (seconds) as a list of lists, same order as
    the input. An entry can be None where OpenRouteService found no walkable
    connection between two points - callers must handle that, not assume a
    number.
    """
    locations = [[lon, lat] for lat, lon in points]
    response = requests.post(
        MATRIX_URL,
        headers={"Authorization": get_api_key(), "Content-Type": "application/json"},
        json={"locations": locations, "metrics": ["duration"]},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["durations"]


def fetch_route_geometry(ordered_points):
    """ordered_points: a list of (lat, lon) tuples in the exact walked
    order (start -> stop 1 -> stop 2 -> ... -> start) - the real path for
    this specific route, not just pairwise durations.

    Returns the route's real walking-path geometry as a list of [lng, lat]
    coordinate pairs (a GeoJSON LineString's coordinates, ready to hand
    straight to MapLibre) - never a flat encoded polyline string requiring
    a decode step.

    Raises requests.RequestException/HTTPError on failure - Story 1.4's
    caller treats that as non-fatal to the overall route (geometry is a
    nice-to-have for display, not the thing that makes a route valid), but
    that degradation decision belongs to the caller, not this function.
    """
    coordinates = [[lon, lat] for lat, lon in ordered_points]
    response = requests.post(
        DIRECTIONS_URL,
        headers={"Authorization": get_api_key(), "Content-Type": "application/json"},
        json={"coordinates": coordinates},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["features"][0]["geometry"]["coordinates"]
