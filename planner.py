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

import requests

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
MIN_REQUESTED_MINUTES = 30
MAX_REQUESTED_MINUTES = 120
# The canonical topic list (Story 1.4) - lives here, not in app.py or ai.py,
# since shortlist_candidates()'s own topic semantics already live in this
# module. "surprise_me" is the sentinel that skips topic filtering, not a
# real catalogue topic.
VALID_TOPICS = {"history", "architecture", "public_art", "surprise_me"}

# Revised 2026-10-18: the stop count no longer has one fixed ceiling - the
# PRD (FR-5) wants it to depend on time, dwell, and real candidate
# availability, not an arbitrary constant. ABSOLUTE_MAX_STOPS is a measured
# safety ceiling, not a target: compute_best_order() brute-forces every
# ordering of a combination (k! orderings), and direct timing against a
# 12-candidate shortlist showed this stays cheap only at small k - 5 stops
# ~0.06s, 6 ~0.45s, 7 ~2.9s, growing ~6-7x per added stop (so 8 would be
# roughly 15-20s, 10 several minutes - checked by extrapolation from the
# measured growth rate, not assumed). 7 is deliberately conservative, not
# the planner's permanent limit; going higher would need a real
# ordering-heuristic change, not just raising this number.
ABSOLUTE_MAX_STOPS = 7


def max_stops_for_request(requested_minutes, dwell_minutes_per_stop):
    """The per-request upper bound on stop count: dwell time alone already
    rules out large combinations for a short request (e.g. 30 min / 5 min
    dwell can't fit more than 6 stops' worth of dwelling, before any
    walking time is even considered), so there's no need to brute-force
    sizes that could never be feasible anyway. Never below MIN_STOPS."""
    return max(MIN_STOPS, min(ABSOLUTE_MAX_STOPS, requested_minutes // dwell_minutes_per_stop))

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


def collect_eligible_candidates(start_lat, start_lon, topic, places=None, excluded_ids=None, retained_ids=None):
    """topic: one of the catalogue's topic strings, or "surprise_me" to skip
    topic filtering entirely - candidates across all topics are kept so
    Sprint 4's AI can make the final cross-topic selection itself, rather
    than this step silently narrowing it to a single "most common" topic.

    excluded_ids (Story 1.7, AD-5): a hard filter, applied here before any
    routing/AI call ever sees the candidates - a Re-Jaunted stop must never
    reappear, not merely be discouraged by an AI prompt hint.
    """
    if places is None:
        places = load_ready_places()
    # bmad-code-review 2026-10-22: was a list, making this an O(n*m) scan
    # over the whole catalogue for every excluded id - a set makes each
    # check O(1), same result either way.
    excluded_ids = set(excluded_ids) if excluded_ids else set()

    retained_ids = retained_ids or []
    retained = {p["id"]: p for p in places
                if p.get("status") == "ready" and p.get("id") in retained_ids
                and p.get("latitude") is not None and p.get("longitude") is not None
                and p.get("id") not in excluded_ids}
    nearby = []
    for place in places:
        if place.get("status") != "ready":
            continue
        if place.get("latitude") is None or place.get("longitude") is None:
            continue
        if place.get("id") in excluded_ids:
            continue
        distance = haversine_meters(
            start_lat, start_lon, place["latitude"], place["longitude"]
        )
        if distance <= SHORTLIST_RADIUS_METERS:
            nearby.append((distance, place))

    if topic != "surprise_me":
        nearby = [(d, p) for d, p in nearby if topic in p.get("topics", [])]

    nearby.sort(key=lambda pair: pair[0])  # closest first
    reserved = [retained[id_] for id_ in retained_ids if id_ in retained]
    alternatives = [p for _, p in nearby if p["id"] not in retained]
    return reserved + alternatives



def shortlist_candidates(start_lat, start_lon, topic, places=None, excluded_ids=None, retained_ids=None):
    """Preserve the nearest twelve contract for existing callers."""
    return collect_eligible_candidates(
        start_lat, start_lon, topic, places, excluded_ids, retained_ids
    )[:SHORTLIST_CAP]

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
    allow_single=False,
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

    minimum = 1 if allow_single else MIN_STOPS
    if not (minimum <= len(stop_indices) <= ABSOLUTE_MAX_STOPS):
        return _infeasible(
            f"stop count must be between {MIN_STOPS} and {ABSOLUTE_MAX_STOPS}"
        )

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
    shortlist, matrix, requested_minutes, dwell_minutes_per_stop,
    retained_ids=None, replacement_mode=False,
):
    """Every feasible stop combination from the shortlist (2 up to
    max_stops_for_request()'s per-request bound), each already checked (via
    check_feasibility() - unchanged) for its best order and exact total
    time. This is the full feasible universe AI can be offered to choose
    among by relevance, rather than being asked to discover a feasible
    combination itself by guessing at arithmetic - see "Redesign after live
    testing" in docs/ai-development-log.md for why.

    The upper bound is computed per request (FR-5, revised 2026-10-18) -
    see max_stops_for_request()'s own comment for why it isn't just
    ABSOLUTE_MAX_STOPS every time.
    """
    feasible = []
    max_size = max_stops_for_request(requested_minutes, dwell_minutes_per_stop)
    retained_indices = {i for i, p in enumerate(shortlist, 1)
                        if p["id"] in (retained_ids or [])}
    sizes = [len(retained_ids or []) + 1] if replacement_mode else range(MIN_STOPS, max_size + 1)
    for size in sizes:
        if size > max_size:
            continue
        for combo in itertools.combinations(range(1, len(shortlist) + 1), size):
            if replacement_mode and not retained_indices.issubset(combo):
                continue
            result = check_feasibility(
                0, list(combo), matrix, requested_minutes, dwell_minutes_per_stop,
                allow_single=replacement_mode,
            )
            if result["feasible"]:
                feasible.append(result)
    return feasible


def _build_ai_options(shortlist, feasible_combos, prefer_prefixes=False):
    """Ranks feasible combinations by budget usage (closest to fully using
    the requested time first) and caps the menu at AI_OPTION_MENU_SIZE, so
    AI's input stays small regardless of how many combinations exist (see
    docs/architecture-plan.md).

    AD-7 coverage pass (Story 1.4): a plain top-N-by-ratio slice could let a
    worthwhile stop vanish from every option AI ever sees, just because
    every combination containing it happened to rank outside the top N -
    starving later preference/variety features (Story 1.9/3.4) of any real
    stop to act on. So this first greedily adds the highest-ranked
    not-yet-covered-stop-containing combo until every stop appearing in any
    feasible combination is covered by at least one menu option (or the
    menu is full - with this module's own SHORTLIST_CAP/ABSOLUTE_MAX_STOPS
    constants, the universe of distinct stops across all feasible combos
    can never exceed AI_OPTION_MENU_SIZE, so full coverage is always
    achievable in practice, not just hoped for), then fills any remaining
    slots by budget-usage ratio exactly as before.

    Returns (ai_options, combos_by_key): ai_options is the provider-agnostic
    list handed to ai.select_stops(); combos_by_key maps each option_key
    back to its full check_feasibility() result, for resolving whichever
    key AI picks.
    """
    ranked = sorted(feasible_combos, key=lambda c: c["budget_usage_ratio"], reverse=True)

    needs_coverage = set()
    for combo in feasible_combos:
        needs_coverage.update(combo["order"])

    menu = []
    remaining = list(ranked)
    if prefer_prefixes:
        for size in range(MIN_STOPS, ABSOLUTE_MAX_STOPS + 1):
            prefix = set(range(1, size + 1))
            match = next((combo for combo in remaining if set(combo["order"]) == prefix), None)
            if match is not None:
                menu.append(match)
                remaining.remove(match)
    covered = {idx for combo in menu for idx in combo["order"]}
    i = 0
    while covered != needs_coverage and len(menu) < AI_OPTION_MENU_SIZE and i < len(remaining):
        combo = remaining[i]
        if not set(combo["order"]) <= covered:
            menu.append(combo)
            covered.update(combo["order"])
            remaining.pop(i)
        else:
            i += 1

    for combo in remaining:
        if len(menu) >= AI_OPTION_MENU_SIZE:
            break
        menu.append(combo)

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
                    "source_type": shortlist[idx - 1].get("source_type"),
                    "source_title": shortlist[idx - 1].get("source_title"),
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
    excluded_ids=None,
    retained_ids=None,
    replacement_mode=False,
    preference=0.5,
):
    """Sprint 4: shortlist real candidates, fetch a real duration matrix,
    deterministically enumerate every feasible stop combination (2 up to
    the per-request bound from max_stops_for_request()), and let
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

    excluded_ids (Story 1.7): passed straight through to
    shortlist_candidates() as the hard Re-Jaunt filter (AD-5). Normalized
    to [] here so callers/tests may pass either None or a list.
    """
    if excluded_ids is None:
        excluded_ids = []
    retained_ids = retained_ids or []
    shortlist_args = {"excluded_ids": excluded_ids}
    if replacement_mode:
        shortlist_args["retained_ids"] = retained_ids
    pool = collect_eligible_candidates(start_lat, start_lon, topic, **shortlist_args)
    if replacement_mode and not set(retained_ids).issubset({p["id"] for p in pool}):
        raise requests.RequestException("retained catalogue places are no longer available for routing")
    retained = [p for p in pool if p["id"] in retained_ids] if replacement_mode else []
    alternatives = [p for p in pool if p not in retained]
    slots = SHORTLIST_CAP - len(retained)
    if slots < 0:
        raise ai.AiExhaustedError("too many retained stops for the routing limit")
    nearest = retained + alternatives[:slots]
    shortlist = nearest
    needs_discovery = len(alternatives) > slots or (not replacement_mode and len(alternatives) >= 5)
    if needs_discovery:
        selected_ids = ai.discover_candidates(alternatives, topic, preference, min(slots, len(alternatives)))
        by_id = {p["id"]: p for p in alternatives}
        shortlist = retained + [by_id[id_] for id_ in selected_ids]
    result = _plan_shortlist(
        shortlist, start_lat, start_lon, topic, requested_minutes,
        dwell_minutes_per_stop, retained_ids, replacement_mode, preference,
        prefer_prefixes=needs_discovery,
    )
    if ((not result["feasible"] or result.get("replacement_outcome") == "retained_only")
            and {p["id"] for p in shortlist} != {p["id"] for p in nearest}):
        recovery = _plan_shortlist(
            nearest, start_lat, start_lon, topic, requested_minutes,
            dwell_minutes_per_stop, retained_ids, replacement_mode, preference,
        )
        recovery["attempts"] += result["attempts"]
        recovery["attempts_log"] = [
            dict(entry, shortlist=label)
            for label, attempt_result in (("discovery", result), ("nearest_recovery", recovery))
            for entry in attempt_result["attempts_log"]
        ]
        return recovery
    return result


def _plan_shortlist(shortlist, start_lat, start_lon, topic, requested_minutes,
                    dwell_minutes_per_stop, retained_ids, replacement_mode, preference,
                    prefer_prefixes=False):
    """One bounded matrix/feasibility/selection attempt; technical errors propagate."""
    if replacement_mode and not set(retained_ids).issubset({p["id"] for p in shortlist}):
        raise requests.RequestException("retained catalogue places are no longer available for routing")
    if not replacement_mode and len(shortlist) < MIN_STOPS:
        return _plan_failure(
            f"only {len(shortlist)} candidate place(s) found near this start "
            f"point - at least {MIN_STOPS} are needed",
            attempts=0,
        )

    points = [(start_lat, start_lon)] + [
        (p["latitude"], p["longitude"]) for p in shortlist
    ]
    if not shortlist:
        return _plan_failure("no suitable replacement found", attempts=0)
    matrix = fetch_duration_matrix(points)

    def no_replacement(reason, attempts=0, attempts_log=None):
        if not replacement_mode or not retained_ids:
            return _plan_failure(reason, attempts, attempts_log)
        indices_by_id = {p["id"]: i for i, p in enumerate(shortlist, 1)}
        order = [indices_by_id[id_] for id_ in retained_ids]
        walking = _round_trip_seconds(0, order, matrix)
        total = None if walking is None else walking / 60 + len(order) * dwell_minutes_per_stop
        if total is None or total > requested_minutes:
            # This is an unverified retained draft, not permission to discard
            # accepted places or offer a route with unsupported totals.
            raise requests.RequestException("retained route could not be verified within the requested time")
        return {"feasible": True, "reason": None, "order": order,
                "total_minutes": total, "unused_minutes": requested_minutes - total,
                "budget_usage_ratio": total / requested_minutes, "shortlist": shortlist,
                "selected_ids": retained_ids, "attempts": attempts,
                "attempts_log": attempts_log or [], "replacement_outcome": "retained_only"}

    feasible_combos = _enumerate_feasible_combinations(
        shortlist, matrix, requested_minutes, dwell_minutes_per_stop,
        retained_ids=retained_ids, replacement_mode=replacement_mode,
    )
    if not feasible_combos:
        max_size = max_stops_for_request(requested_minutes, dwell_minutes_per_stop)
        return no_replacement(
            f"no combination of {MIN_STOPS}-{max_size} stops from the "
            f"shortlist fits within {requested_minutes} min",
            attempts=0,
        )

    ai_options, combos_by_key = _build_ai_options(shortlist, feasible_combos, prefer_prefixes=prefer_prefixes)

    feedback = None
    attempts_used = 0
    attempts_log = []

    for _ in range(1 + MAX_AI_RETRIES):
        attempts_used += 1
        try:
            selection = ai.select_stops(
                ai_options, topic, requested_minutes, feedback=feedback, preference=preference
            )
        except ai.AiFatalError:
            # Invalid credentials, permission errors, or exhausted quota -
            # a genuine service failure, never ordinary infeasibility.
            # Story 1.4: re-raise rather than collapse into _plan_failure()'s
            # {"feasible": false} shape - a caller must be able to tell this
            # apart from an honest "no suitable walk" (mirrors how
            # CatalogueError already propagates to its own caller). Retrying
            # an unmodified request cannot fix any of these causes, so this
            # also correctly stops immediately instead of spending the rest
            # of the retry budget on a doomed request.
            raise
        except ai.AiSelectionError as exc:
            feedback = str(exc)
            attempts_log.append({
                "attempt": attempts_used, "selected_option": None,
                "outcome": "ai_error", "reason": str(exc),
            })
            continue

        selected_option = selection["selected_option"]

        if selected_option == ai.NONE_SUITABLE:
            # AD-7: AI judged every offered option time-feasible but none
            # genuinely relevant/interesting - a distinct, honest outcome,
            # never forced into picking a weak option. Same wire shape as
            # "zero feasible combinations" (both are honest, non-fatal
            # 200s) - the real reason text is what tells them apart to a
            # reader; nothing in this story's AC asks for a separate
            # machine-readable field between the two.
            attempts_log.append({
                "attempt": attempts_used, "selected_option": selected_option,
                "outcome": "none_suitable", "reason": selection["none_suitable_reason"],
            })
            return no_replacement(
                "Among the candidates checked: " + (selection["none_suitable_reason"] or "no offered option was genuinely suitable"),
                attempts=attempts_used, attempts_log=attempts_log,
            )

        if selected_option not in combos_by_key:
            reason = f"'{selected_option}' is not one of the offered option keys"
            feedback = (
                f"your previous answer was '{selected_option}': {reason}. "
                f"Choose one of: {', '.join(combos_by_key)}, or \"{ai.NONE_SUITABLE}\" "
                f"if none are genuinely suitable."
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
            **({"replacement_outcome": "replacement_found"} if replacement_mode else {}),
            "shortlist": shortlist,
            "selected_ids": [shortlist[i - 1]["id"] for i in result["order"]],
            "attempts": attempts_used,
            "attempts_log": attempts_log,
        }

    # Codex review 2026-10-21: every attempt failed without ever producing
    # a usable selection (an "accepted" or "none_suitable" outcome would
    # have returned already, above) - a persistent, repeated failure to
    # get anything usable from AI, not a judgement that no route is
    # suitable. Raising ai.AiExhaustedError (re-raised the same way
    # AiFatalError already is) keeps this out of _plan_failure()'s
    # {"feasible": false} shape, so a caller can't mistake "AI kept
    # failing" for an honest "no suitable walk" and suggest the wrong fix.
    raise ai.AiExhaustedError(
        f"AI did not return a usable option after {attempts_used} attempts"
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
