"""Sprint 1: confirm the routing provider actually returns pedestrian data.

The public OSRM demo server was tested manually and found to return
identical results for its 'foot' and 'driving' profiles (car-speed numbers
even when walking was requested) - see docs/architecture-plan.md. This
script checks OpenRouteService's foot-walking profile instead, using two
real points in the Newtown pilot area, and prints the implied walking
speed so the result can be sanity-checked before anything else depends on it.
"""

import os

import requests

ENV_PATH = ".env"
DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking"

# Two real points in Newtown.
START = (151.1793, -33.8983)  # (longitude, latitude)
END = (151.1730, -33.9022)


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


def main():
    load_env()
    api_key = os.environ.get("OPENROUTESERVICE_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENROUTESERVICE_API_KEY not found. Check your .env file at the project root."
        )

    # Sent as a header, not a URL query parameter, so the key doesn't end up
    # in server logs, browser history, or debugging output.
    params = {
        "start": f"{START[0]},{START[1]}",
        "end": f"{END[0]},{END[1]}",
    }
    response = requests.get(
        DIRECTIONS_URL, params=params, headers={"Authorization": api_key}, timeout=15
    )
    response.raise_for_status()
    summary = response.json()["features"][0]["properties"]["summary"]

    distance_m = summary["distance"]
    duration_s = summary["duration"]
    speed_kmh = (distance_m / duration_s) * 3.6

    print(f"Distance: {distance_m:.0f} m")
    print(f"Duration: {duration_s:.0f} s ({duration_s / 60:.1f} min)")
    print(f"Implied speed: {speed_kmh:.1f} km/h")

    if 3.0 <= speed_kmh <= 7.0:
        print("This looks like a real walking pace - routing provider confirmed.")
    else:
        print("WARNING: this does not look like a walking pace - check the profile/provider.")


if __name__ == "__main__":
    main()
