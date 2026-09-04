"""Sprint 3: candidate shortlisting and the ordering/feasibility helper.
Sprint 4: plan_route() ties shortlisting, the routing matrix, and AI
selection together.

This module owns all deterministic arithmetic: narrowing candidates,
requesting the real matrix, and (since the Sprint 4 redesign - see
docs/ai-development-log.md) enumerating every feasible stop combination
itself rather than asking AI to compute feasibility. AI (ai.py) only judges
relevance and interest among options this module has already proven
feasible.
"""

import itertools
import json
import os

import ai
from import_places import haversine_meters
from services import fetch_duration_matrix

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

# Sprint 4 retry policy - see docs/ai-development-log.md.
MAX_AI_RETRIES = 2
# How many top-ranked feasible combinations are offered to AI per request -
# keeps AI's input small (see docs/architecture-plan.md) without excluding
# the only feasible option(s) when few or none rank highly on usage.
AI_OPTION_MENU_SIZE = 15


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


def _plan_failure(reason, attempts, attempts_log=None):
    return {
        "feasible": False,
        "reason": reason,
        "order": None,
        "total_minutes": None,
        "unused_minutes": None,
        "budget_usage_ratio": None,
        "shortlist": None,
        "selected_ids": None,
        "attempts": attempts,
        "attempts_log": attempts_log or [],
    }


def _enumerate_feasible_combinations(
    shortlist, matrix, requested_minutes, dwell_minutes_per_stop
):
    """Every feasible 2-5 stop combination from the shortlist, each already
    checked (via check_feasibility() - unchanged) for its best order and
    exact total time. This is the full feasible universe AI can be offered
    to choose among by relevance, rather than being asked to discover a
    feasible combination itself by guessing at arithmetic - see "Redesign
    after live testing" in docs/ai-development-log.md for why.

    At the shortlist cap (12), this is at most 1,573 combinations, each a
    cheap check_feasibility() call - negligible compute, no change to any
    arithmetic already covered by Sprint 3's tests.
    """
    feasible = []
    for size in range(MIN_STOPS, MAX_STOPS + 1):
        for combo in itertools.combinations(range(1, len(shortlist) + 1), size):
            result = check_feasibility(
                0, list(combo), matrix, requested_minutes, dwell_minutes_per_stop
            )
            if result["feasible"]:
                feasible.append(result)
    return feasible


def _build_ai_options(shortlist, feasible_combos):
    """Ranks feasible combinations by budget usage (closest to fully using
    the requested time first) and caps the menu at AI_OPTION_MENU_SIZE, so
    AI's input stays small regardless of how many combinations exist (see
    docs/architecture-plan.md). This is a plain top-N slice of every
    feasible combination, not a minimum-usage filter - it never excludes
    the only feasible option(s) just because their usage is low.

    Returns (ai_options, combos_by_key): ai_options is the provider-agnostic
    list handed to ai.select_stops(); combos_by_key maps each option_key
    back to its full check_feasibility() result, for resolving whichever
    key AI picks.
    """
    ranked = sorted(feasible_combos, key=lambda c: c["budget_usage_ratio"], reverse=True)
    menu = ranked[:AI_OPTION_MENU_SIZE]

    ai_options = []
    combos_by_key = {}
    for i, combo in enumerate(menu):
        option_key = f"option_{i + 1}"
        combos_by_key[option_key] = combo
        ai_options.append({
            "option_key": option_key,
            "stops": [
                {
                    "id": shortlist[idx - 1]["id"],
                    "name": shortlist[idx - 1]["name"],
                    "topics": shortlist[idx - 1].get("topics", []),
                    "source_excerpt": shortlist[idx - 1].get("source_excerpt"),
                }
                for idx in combo["order"]
            ],
            "total_minutes": round(combo["total_minutes"], 1),
            "budget_usage_ratio": round(combo["budget_usage_ratio"], 3),
        })
    return ai_options, combos_by_key


def plan_route(
    start_lat,
    start_lon,
    topic,
    requested_minutes,
    dwell_minutes_per_stop=DWELL_MINUTES_PER_STOP,
):
    """Sprint 4: shortlist real candidates, fetch a real duration matrix,
    deterministically enumerate every feasible 2-5 stop combination, and let
    AI choose the most relevant and interesting one from that pre-validated
    menu.

    Earlier Sprint 4 asked AI to propose raw candidate ids and compute
    feasibility itself; live testing across two models showed this
    arithmetic is unreliable (see "Redesign after live testing" in
    docs/ai-development-log.md). Python now owns all arithmetic -
    shortlisting, routing, and feasibility - via _enumerate_feasible_
    combinations(); AI's only job is the relevance/interest judgement among
    options Python has already proven walkable in the requested time. A
    genuinely impossible request (no feasible combination at all) is
    detected immediately, without spending any AI calls on it.

    Retries (up to MAX_AI_RETRIES) are now a safety net for the AI call
    failing or returning an option_key that wasn't offered - not, as
    before, a way to coach AI toward a mathematically valid answer, since
    every offered option is already guaranteed valid. "attempts_log"
    records every attempt's outcome, for diagnosing a failed request.
    """
    shortlist = shortlist_candidates(start_lat, start_lon, topic)
    if len(shortlist) < MIN_STOPS:
        return _plan_failure(
            f"only {len(shortlist)} candidate place(s) found near this start "
            f"point - at least {MIN_STOPS} are needed",
            attempts=0,
        )

    points = [(start_lat, start_lon)] + [
        (p["latitude"], p["longitude"]) for p in shortlist
    ]
    matrix = fetch_duration_matrix(points)

    feasible_combos = _enumerate_feasible_combinations(
        shortlist, matrix, requested_minutes, dwell_minutes_per_stop
    )
    if not feasible_combos:
        return _plan_failure(
            f"no combination of {MIN_STOPS}-{MAX_STOPS} stops from the "
            f"shortlist fits within {requested_minutes} min",
            attempts=0,
        )

    ai_options, combos_by_key = _build_ai_options(shortlist, feasible_combos)

    feedback = None
    attempts_used = 0
    attempts_log = []

    for _ in range(1 + MAX_AI_RETRIES):
        attempts_used += 1
        try:
            selected_option = ai.select_stops(
                ai_options, topic, requested_minutes, feedback=feedback
            )
        except ai.AiFatalError as exc:
            # Invalid credentials, permission errors, or exhausted quota -
            # retrying with an unmodified request cannot fix any of these,
            # so stop now instead of repeating a doomed request.
            attempts_log.append({
                "attempt": attempts_used, "selected_option": None,
                "outcome": "ai_fatal_error", "reason": str(exc),
            })
            return _plan_failure(str(exc), attempts=attempts_used, attempts_log=attempts_log)
        except ai.AiSelectionError as exc:
            feedback = str(exc)
            attempts_log.append({
                "attempt": attempts_used, "selected_option": None,
                "outcome": "ai_error", "reason": str(exc),
            })
            continue

        if selected_option not in combos_by_key:
            reason = f"'{selected_option}' is not one of the offered option keys"
            feedback = (
                f"your previous answer was '{selected_option}': {reason}. "
                f"Choose one of: {', '.join(combos_by_key)}."
            )
            attempts_log.append({
                "attempt": attempts_used, "selected_option": selected_option,
                "outcome": "unknown_option", "reason": reason,
            })
            continue

        attempts_log.append({
            "attempt": attempts_used, "selected_option": selected_option,
            "outcome": "accepted", "reason": None,
        })
        result = combos_by_key[selected_option]
        return {
            **result,
            "shortlist": shortlist,
            "selected_ids": [shortlist[i - 1]["id"] for i in result["order"]],
            "attempts": attempts_used,
            "attempts_log": attempts_log,
        }

    return _plan_failure(
        "AI did not return a usable option after all attempts",
        attempts=attempts_used,
        attempts_log=attempts_log,
    )


def _print_route_summary(shortlist, requested_minutes, result, start_lat, start_lon):
    """Demo-only: turns a check_feasibility() result into something a human
    can read and verify, instead of raw indices and a dict dump. Prints the
    start point's exact coordinates (not just the word "Start") so they can
    be copied straight into Google Maps/Maps.me for manual time checks."""
    print(f"\nRequested time budget: {requested_minutes} min")

    if result["order"] is None:
        print(f"No route could be planned: {result['reason']}")
        return

    start_label = f"Start: {start_lat:.6f}, {start_lon:.6f}"
    stop_names = [shortlist[i - 1]["name"] for i in result["order"]]
    dwell_minutes = DWELL_MINUTES_PER_STOP * len(result["order"])
    walking_minutes = result["total_minutes"] - dwell_minutes

    print("Route:")
    print(f"  {start_label}")
    for name in stop_names:
        print(f"  -> {name}")
    print(f"  -> {start_label}")
    print(f"\nWalking time:  {walking_minutes:.1f} min")
    print(f"Dwell time:    {dwell_minutes:.1f} min")
    print(f"Total time:    {result['total_minutes']:.1f} min")
    print(f"Unused time:   {result['unused_minutes']:.1f} min")
    print(f"Budget usage:  {result['budget_usage_ratio']:.0%}")
    print(f"Feasible within {requested_minutes} min budget? {'Yes' if result['feasible'] else 'No'}")
    if not result["feasible"]:
        print(f"Reason: {result['reason']}")


def _print_attempts_log(attempts_log):
    """Demo-only: shows what AI proposed on every attempt and why Python
    accepted or rejected it, not just the final outcome - the intermediate
    attempts are otherwise invisible once plan_route() returns."""
    if not attempts_log:
        print("\nNo AI attempts were made.")
        return

    print("\nAI attempt log:")
    for entry in attempts_log:
        option_display = entry["selected_option"] or "(request failed)"
        print(f"  #{entry['attempt']} [{entry['outcome']}] chose: {option_display}")
        if entry["reason"]:
            print(f"        reason: {entry['reason']}")


if __name__ == "__main__":
    # A real Newtown start point, an explicit topic, and a 60-minute budget.
    # This now calls plan_route() end-to-end: shortlist -> real ORS matrix ->
    # real OpenAI selection -> validation/retry -> final route. Requires both
    # OPENROUTESERVICE_API_KEY and OPENAI_API_KEY (plus OPENAI_MODEL) set in
    # .env.
    start_lat, start_lon = -33.8983, 151.1793
    topic = "surprise_me"
    requested_minutes = 40

    result = plan_route(start_lat, start_lon, topic, requested_minutes)
    shortlist = result["shortlist"] or shortlist_candidates(start_lat, start_lon, topic)

    _print_attempts_log(result["attempts_log"])
    _print_route_summary(shortlist, requested_minutes, result, start_lat, start_lon)
    print(f"\nAI attempts used: {result['attempts']}")
    if result["selected_ids"]:
        print(f"Selected ids: {result['selected_ids']}")
