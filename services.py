"""The one live-at-runtime external call: routing.

Sprint 3 only needs the distance/duration matrix (for shortlist feasibility
checks). Final route geometry for the chosen stops is added in Sprint 6.
"""

import os

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
MATRIX_URL = "https://api.openrouteservice.org/v2/matrix/foot-walking"


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
