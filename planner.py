"""Sprint 3: candidate shortlisting and the ordering/feasibility helper.

No AI yet - this is the deterministic half of route planning. Sprint 4 will
have AI choose a final subset of stops from the shortlist this module
produces; this module then checks whether that choice is actually walkable
in the requested time and finds the best order for it.
"""

import itertools
import json
import os

from import_places import haversine_meters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "sydney_places.json")

# V1 defaults - see docs/architecture-plan.md
SHORTLIST_RADIUS_METERS = 2000  # configurable straight-line pre-filter
SHORTLIST_CAP = 12
DWELL_MINUTES_PER_STOP = 5
MIN_STOPS = 2
MAX_STOPS = 5
MIN_REQUESTED_MINUTES = 30
MAX_REQUESTED_MINUTES = 120


def load_ready_places(data_path=DATA_PATH):
    with open(data_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    return [r for r in records if r.get("status") == "ready"]


def shortlist_candidates(start_lat, start_lon, topic, places=None):
    """topic: one of the catalogue's topic strings, or "surprise_me" to skip
    topic filtering entirely - candidates across all topics are kept so
    Sprint 4's AI can make the final cross-topic selection itself, rather
    than this step silently narrowing it to a single "most common" topic.
    """
    if places is None:
        places = load_ready_places()

    nearby = []
    for place in places:
        if place.get("status") != "ready":
            continue
        if place.get("latitude") is None or place.get("longitude") is None:
            continue
        distance = haversine_meters(
            start_lat, start_lon, place["latitude"], place["longitude"]
        )
        if distance <= SHORTLIST_RADIUS_METERS:
            nearby.append((distance, place))

    if topic != "surprise_me":
        nearby = [(d, p) for d, p in nearby if topic in p.get("topics", [])]

    nearby.sort(key=lambda pair: pair[0])  # closest first
    return [place for _, place in nearby[:SHORTLIST_CAP]]


def _round_trip_seconds(start_index, order, duration_matrix):
    """Sums start->first, each stop->next stop, and last stop->start.
    Returns None if any leg is missing (None) in the matrix - a missing
    connection makes that ordering infeasible, not free."""
    route = [start_index, *order, start_index]
    total = 0.0
    for a, b in zip(route, route[1:]):
        leg = duration_matrix[a][b]
        if leg is None:
            return None
        total += leg
    return total


def compute_best_order(start_index, stop_indices, duration_matrix):
    """Finds the order of stop_indices that minimises total round-trip
    walking time (start -> ... -> start), trying every possible order.

    Returns (best_order, total_seconds), or (None, None) if every ordering
    hits a missing connection in the matrix.
    """
    best_order = None
    best_seconds = None

    for perm in itertools.permutations(stop_indices):
        total = _round_trip_seconds(start_index, perm, duration_matrix)
        if total is None:
            continue
        if best_seconds is None or total < best_seconds:
            best_seconds = total
            best_order = list(perm)

    return best_order, best_seconds


def _infeasible(reason):
    return {
        "feasible": False,
        "reason": reason,
        "order": None,
        "total_minutes": None,
        "unused_minutes": None,
        "budget_usage_ratio": None,
    }


def check_feasibility(
    start_index,
    stop_indices,
    duration_matrix,
    requested_minutes,
    dwell_minutes_per_stop=DWELL_MINUTES_PER_STOP,
):
    """Checks whether a selection of stops can form a walk that fits within
    requested_minutes, using the fastest possible ordering. Total time is
    walking duration (the best round trip found) plus fixed dwell time for
    every selected stop.

    check_feasibility() is the single place that validates requested_minutes
    against the documented 30-120 minute V1 range - see docs/architecture-plan.md.
    It's the only function that currently receives this value, so this is
    deliberately the one place that checks it, rather than duplicating the
    same bounds check in a future caller.

    unused_minutes and budget_usage_ratio are informational only and do not
    affect `feasible` - a route remains feasible purely by fitting within the
    maximum budget. Whether a feasible-but-low-usage route (e.g. 15 minutes
    of a 60-minute request) is actually a *good* result is a Sprint 4
    AI-selection concern, not something this function judges.
    """
    if not (MIN_REQUESTED_MINUTES <= requested_minutes <= MAX_REQUESTED_MINUTES):
        return _infeasible(
            f"requested time must be between {MIN_REQUESTED_MINUTES} and "
            f"{MAX_REQUESTED_MINUTES} minutes"
        )

    if len(set(stop_indices)) != len(stop_indices):
        return _infeasible("duplicate stop selected")

    if not (MIN_STOPS <= len(stop_indices) <= MAX_STOPS):
        return _infeasible(f"stop count must be between {MIN_STOPS} and {MAX_STOPS}")

    order, walking_seconds = compute_best_order(start_index, stop_indices, duration_matrix)
    if order is None:
        return _infeasible("no walkable route exists between the selected stops")

    dwell_minutes = dwell_minutes_per_stop * len(stop_indices)
    total_minutes = (walking_seconds / 60.0) + dwell_minutes
    unused_minutes = requested_minutes - total_minutes
    budget_usage_ratio = total_minutes / requested_minutes

    if total_minutes > requested_minutes:
        return {
            "feasible": False,
            "reason": (
                f"estimated {total_minutes:.0f} min exceeds the requested "
                f"{requested_minutes} min"
            ),
            "order": order,
            "total_minutes": total_minutes,
            "unused_minutes": unused_minutes,
            "budget_usage_ratio": budget_usage_ratio,
        }

    return {
        "feasible": True,
        "reason": None,
        "order": order,
        "total_minutes": total_minutes,
        "unused_minutes": unused_minutes,
        "budget_usage_ratio": budget_usage_ratio,
    }


def _print_route_summary(shortlist, requested_minutes, result):
    """Demo-only: turns a check_feasibility() result into something a human
    can read and verify, instead of raw indices and a dict dump."""
    print(f"\nRequested time budget: {requested_minutes} min")

    if result["order"] is None:
        print(f"No route could be planned: {result['reason']}")
        return

    stop_names = [shortlist[i - 1]["name"] for i in result["order"]]
    dwell_minutes = DWELL_MINUTES_PER_STOP * len(result["order"])
    walking_minutes = result["total_minutes"] - dwell_minutes

    print("Route:")
    print("  Start")
    for name in stop_names:
        print(f"  -> {name}")
    print("  -> Start")
    print(f"\nWalking time:  {walking_minutes:.1f} min")
    print(f"Dwell time:    {dwell_minutes:.1f} min")
    print(f"Total time:    {result['total_minutes']:.1f} min")
    print(f"Unused time:   {result['unused_minutes']:.1f} min")
    print(f"Budget usage:  {result['budget_usage_ratio']:.0%}")
    print(f"Feasible within {requested_minutes} min budget? {'Yes' if result['feasible'] else 'No'}")
    if not result["feasible"]:
        print(f"Reason: {result['reason']}")


if __name__ == "__main__":
    from services import fetch_duration_matrix

    # A real Newtown start point, an explicit topic, and a 60-minute budget.
    start_lat, start_lon = -33.8983, 151.1793
    topic = "public_art"
    requested_minutes = 60

    shortlist = shortlist_candidates(start_lat, start_lon, topic)
    print(f"Shortlist for topic={topic!r} within {SHORTLIST_RADIUS_METERS}m: {len(shortlist)} candidates")
    for place in shortlist:
        print(f"  - {place['name']} {place['topics']}")

    points = [(start_lat, start_lon)] + [
        (p["latitude"], p["longitude"]) for p in shortlist
    ]
    matrix = fetch_duration_matrix(points)
    print(f"\nFetched a real {len(matrix)}x{len(matrix)} duration matrix (seconds).")

    if len(shortlist) >= MIN_STOPS:
        example_indices = list(range(1, 1 + MIN_STOPS))
        result = check_feasibility(0, example_indices, matrix, requested_minutes)
        _print_route_summary(shortlist, requested_minutes, result)
