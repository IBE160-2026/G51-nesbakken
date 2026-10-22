import unittest
from unittest.mock import patch

from ai import AiExhaustedError, AiFatalError, AiSelectionError
from planner import (
    ABSOLUTE_MAX_STOPS,
    AI_OPTION_MENU_SIZE,
    DWELL_MINUTES_PER_STOP,
    MIN_STOPS,
    SHORTLIST_CAP,
    _build_ai_options,
    _enumerate_feasible_combinations,
    check_feasibility,
    compute_best_order,
    max_stops_for_request,
    plan_route,
    shortlist_candidates,
)

START_LAT, START_LON = -33.900, 151.180


def make_place(id_, lat, lon, topics, status="ready"):
    return {
        "id": id_,
        "name": id_,
        "latitude": lat,
        "longitude": lon,
        "topics": topics,
        "status": status,
    }


class TestShortlisting(unittest.TestCase):
    def test_excludes_places_beyond_radius(self):
        near = make_place("near", -33.901, 151.181, ["history"])  # ~150m away
        far = make_place("far", -33.950, 151.230, ["history"])  # several km away
        result = shortlist_candidates(START_LAT, START_LON, "history", places=[near, far])
        ids = {p["id"] for p in result}
        self.assertIn("near", ids)
        self.assertNotIn("far", ids)

    def test_only_ready_places_considered(self):
        ready = make_place("ready1", -33.901, 151.181, ["history"], status="ready")
        limited = make_place("limited1", -33.901, 151.181, ["history"], status="limited")
        result = shortlist_candidates(
            START_LAT, START_LON, "history", places=[ready, limited]
        )
        self.assertEqual([p["id"] for p in result], ["ready1"])

    def test_explicit_topic_filters(self):
        art = make_place("art1", -33.901, 151.181, ["public_art"])
        history = make_place("history1", -33.901, 151.181, ["history"])
        result = shortlist_candidates(
            START_LAT, START_LON, "public_art", places=[art, history]
        )
        self.assertEqual([p["id"] for p in result], ["art1"])

    def test_surprise_me_keeps_all_topics(self):
        # Explicitly the clarified behaviour: no "most common topic" logic,
        # every topic stays in the shortlist for Sprint 4's AI to choose from.
        art = make_place("art1", -33.901, 151.181, ["public_art"])
        history = make_place("history1", -33.901, 151.181, ["history"])
        result = shortlist_candidates(
            START_LAT, START_LON, "surprise_me", places=[art, history]
        )
        self.assertEqual({p["id"] for p in result}, {"art1", "history1"})

    def test_cap_keeps_closest_first(self):
        places = [
            make_place(f"p{i}", START_LAT + i * 0.0005, START_LON, ["history"])
            for i in range(SHORTLIST_CAP + 5)
        ]  # p0 is closest to start, distance increases with i
        result = shortlist_candidates(START_LAT, START_LON, "history", places=places)
        self.assertEqual(len(result), SHORTLIST_CAP)
        self.assertEqual(result[0]["id"], "p0")
        kept_ids = {p["id"] for p in result}
        self.assertNotIn(f"p{SHORTLIST_CAP + 4}", kept_ids)

    def test_excluded_ids_filtered_out(self):
        # Story 1.7 (AD-5): excluded_ids is a hard filter applied here,
        # before topic/distance narrowing ever runs - a Re-Jaunted stop
        # must never reappear in a later shortlist.
        a = make_place("a", -33.901, 151.181, ["history"])
        b = make_place("b", -33.901, 151.181, ["history"])
        result = shortlist_candidates(
            START_LAT, START_LON, "history", places=[a, b], excluded_ids=["a"]
        )
        self.assertEqual([p["id"] for p in result], ["b"])

    def test_excluded_ids_defaults_to_no_exclusion(self):
        # None (the default) behaves exactly like today - nothing excluded.
        a = make_place("a", -33.901, 151.181, ["history"])
        result = shortlist_candidates(START_LAT, START_LON, "history", places=[a])
        self.assertEqual([p["id"] for p in result], ["a"])


class TestBestOrder(unittest.TestCase):
    def test_finds_shortest_of_two_distinct_routes(self):
        # A "ring" of stops (1,2,3) around the start is much cheaper than
        # cutting across the diagonal (1,3,2) - genuinely different cycles,
        # not just the same cycle walked backwards.
        matrix = [
            [0, 10, 50, 10],
            [10, 0, 10, 50],
            [50, 10, 0, 10],
            [10, 50, 10, 0],
        ]
        order, total = compute_best_order(0, [1, 2, 3], matrix)
        self.assertIn(order, ([1, 2, 3], [3, 2, 1]))  # same ring, either direction
        self.assertEqual(total, 40)

    def test_every_ordering_blocked_returns_none(self):
        matrix = [
            [0, 10, None],
            [10, 0, 10],
            [None, 10, 0],
        ]
        # 0->1->2->0 needs leg 2->0 (None); 0->2->1->0 needs leg 0->2 (None).
        order, total = compute_best_order(0, [1, 2], matrix)
        self.assertIsNone(order)
        self.assertIsNone(total)

    def test_partially_blocked_still_finds_the_valid_ordering(self):
        matrix = [
            [0, 10, 5],
            [10, 0, 20],
            [None, 8, 0],
        ]
        # 0->1->2->0 needs leg 2->0 (None) - blocked.
        # 0->2->1->0 = 5 + 8 + 10 = 23 - valid, and the only option.
        order, total = compute_best_order(0, [1, 2], matrix)
        self.assertEqual(order, [2, 1])
        self.assertEqual(total, 23)


class TestFeasibility(unittest.TestCase):
    def setUp(self):
        self.matrix = [
            [0, 600, 600, 600],
            [600, 0, 300, 300],
            [600, 300, 0, 300],
            [600, 300, 300, 0],
        ]

    def test_feasible_selection_within_time(self):
        result = check_feasibility(0, [1, 2], self.matrix, requested_minutes=60)
        self.assertTrue(result["feasible"])
        # best round trip = 1500s = 25 min walking + dwell 5*2 = 10 min = 35 min
        self.assertAlmostEqual(result["total_minutes"], 35.0)

    def test_budget_usage_fields_are_correct_when_feasible(self):
        result = check_feasibility(0, [1, 2], self.matrix, requested_minutes=60)
        # total_minutes=35, requested=60 -> unused=25, ratio=35/60
        self.assertAlmostEqual(result["unused_minutes"], 25.0)
        self.assertAlmostEqual(result["budget_usage_ratio"], 35.0 / 60.0)

    def test_low_budget_usage_still_counts_as_feasible(self):
        # Explicitly: feasible is purely "fits within the maximum budget" -
        # a route using a small fraction of a long request is still feasible.
        # (Whether that's a *good* result is a Sprint 4 concern, not this
        # function's - see docs/architecture-plan.md.)
        result = check_feasibility(0, [1, 2], self.matrix, requested_minutes=120)
        self.assertTrue(result["feasible"])
        self.assertLess(result["budget_usage_ratio"], 0.3)

    def test_infeasible_when_over_time_budget(self):
        # requested_minutes=30 is within the valid 30-120 range but still
        # less than the 35-minute total, so this exercises the "over budget"
        # path specifically, not the range-validation path.
        result = check_feasibility(0, [1, 2], self.matrix, requested_minutes=30)
        self.assertFalse(result["feasible"])
        self.assertIn("exceeds", result["reason"])
        # unused_minutes/budget_usage_ratio are still reported even when
        # infeasible due to exceeding the budget, since total_minutes exists.
        self.assertAlmostEqual(result["unused_minutes"], -5.0)

    def test_infeasible_when_matrix_has_no_route(self):
        matrix = [
            [0, 600, None],
            [600, 0, 300],
            [None, 300, 0],
        ]
        result = check_feasibility(0, [1, 2], matrix, requested_minutes=120)
        self.assertFalse(result["feasible"])
        self.assertIn("no walkable route", result["reason"])
        self.assertIsNone(result["unused_minutes"])
        self.assertIsNone(result["budget_usage_ratio"])

    def test_rejects_too_few_stops(self):
        result = check_feasibility(0, [1], self.matrix, requested_minutes=120)
        self.assertFalse(result["feasible"])
        self.assertIn("between", result["reason"])

    def test_rejects_duplicate_stop_indices(self):
        result = check_feasibility(0, [1, 1], self.matrix, requested_minutes=120)
        self.assertFalse(result["feasible"])
        self.assertIn("duplicate", result["reason"])

    def test_rejects_requested_minutes_below_range(self):
        result = check_feasibility(0, [1, 2], self.matrix, requested_minutes=29)
        self.assertFalse(result["feasible"])
        self.assertIn("between 30 and 120", result["reason"])

    def test_rejects_requested_minutes_above_range(self):
        result = check_feasibility(0, [1, 2], self.matrix, requested_minutes=121)
        self.assertFalse(result["feasible"])
        self.assertIn("between 30 and 120", result["reason"])

    def test_accepts_requested_minutes_at_range_boundaries(self):
        low = check_feasibility(0, [1, 2], self.matrix, requested_minutes=30)
        high = check_feasibility(0, [1, 2], self.matrix, requested_minutes=120)
        # Neither should be rejected specifically for being out of range.
        self.assertNotIn("between 30 and 120", low["reason"] or "")
        self.assertNotIn("between 30 and 120", high["reason"] or "")

    def test_rejects_too_many_stops(self):
        # Bounds are checked before the matrix is ever touched, so
        # out-of-range indices here don't matter. 8 exceeds the measured,
        # deliberately conservative ABSOLUTE_MAX_STOPS=7 ceiling (see
        # planner.py's comment on brute-force ordering cost).
        result = check_feasibility(0, [1, 2, 3, 4, 5, 6, 7, 8], self.matrix, requested_minutes=120)
        self.assertFalse(result["feasible"])
        self.assertIn("between", result["reason"])


class TestMaxStopsForRequest(unittest.TestCase):
    """FR-5, revised 2026-10-18: stop count depends on time/dwell, not a
    fixed constant - see planner.py's comment on measured ordering cost."""

    def test_short_request_is_bounded_by_dwell_time_not_the_absolute_ceiling(self):
        # 30 min / 5 min dwell = 6, below ABSOLUTE_MAX_STOPS (7).
        self.assertEqual(max_stops_for_request(30, 5), 6)

    def test_long_request_is_capped_at_the_absolute_ceiling(self):
        # 120 min / 5 min dwell = 24, far above the measured-safe ceiling.
        self.assertEqual(max_stops_for_request(120, 5), ABSOLUTE_MAX_STOPS)

    def test_never_drops_below_min_stops(self):
        # Pathologically large dwell time would otherwise compute 0 or 1.
        self.assertEqual(max_stops_for_request(30, 50), MIN_STOPS)


FAKE_SHORTLIST = [
    make_place("a", -33.901, 151.181, ["public_art"]),
    make_place("b", -33.901, 151.181, ["public_art"]),
    make_place("c", -33.901, 151.181, ["public_art"]),
]
# start=0, a=1, b=2, c=3. Any two stops: 35 min total (25 walk + 10 dwell).
# All three stops: 45 min total (30 walk + 15 dwell). At 60 min requested,
# all 4 combinations (3 pairs + 1 triple) are feasible; at 30 min, none are.
PLAN_MATRIX = [
    [0, 600, 600, 600],
    [600, 0, 300, 300],
    [600, 300, 0, 300],
    [600, 300, 300, 0],
]

# c is unreachable except directly from the start - so only (a, b) is
# feasible from this shortlist, regardless of requested_minutes.
ONLY_ONE_FEASIBLE_MATRIX = [
    [0, 100, 100, 5000],
    [100, 0, 100, 5000],
    [100, 100, 0, 5000],
    [5000, 5000, 5000, 0],
]


def make_uniform_matrix(n, leg_seconds=100):
    """An (n+1)x(n+1) matrix (start + n stops) where every leg costs the
    same - used to cheaply generate more feasible combinations than
    AI_OPTION_MENU_SIZE, to test that the AI menu gets capped."""
    size = n + 1
    return [[0 if i == j else leg_seconds for j in range(size)] for i in range(size)]


BIG_SHORTLIST = [make_place(f"s{i}", -33.901, 151.181, ["public_art"]) for i in range(6)]
BIG_MATRIX = make_uniform_matrix(6)


class TestEnumerateFeasibleCombinations(unittest.TestCase):
    def test_finds_every_feasible_combination(self):
        # 3 pairs + 1 triple, all feasible at 60 min with PLAN_MATRIX.
        combos = _enumerate_feasible_combinations(FAKE_SHORTLIST, PLAN_MATRIX, 60, DWELL_MINUTES_PER_STOP)
        self.assertEqual(len(combos), 4)
        self.assertTrue(all(c["feasible"] for c in combos))

    def test_returns_empty_list_when_nothing_fits(self):
        combos = _enumerate_feasible_combinations(FAKE_SHORTLIST, PLAN_MATRIX, 30, DWELL_MINUTES_PER_STOP)
        self.assertEqual(combos, [])

    def test_finds_the_single_feasible_combination_when_others_are_blocked(self):
        combos = _enumerate_feasible_combinations(
            FAKE_SHORTLIST, ONLY_ONE_FEASIBLE_MATRIX, 60, DWELL_MINUTES_PER_STOP
        )
        self.assertEqual(len(combos), 1)
        self.assertEqual(combos[0]["order"], [1, 2])  # a, b

    def test_a_long_request_can_reach_more_than_five_stops(self):
        # FR-5, revised 2026-10-18: no fixed 5-stop ceiling. 120 min against
        # a uniform-cost 6-place shortlist should reach the full 6-stop combo.
        combos = _enumerate_feasible_combinations(BIG_SHORTLIST, BIG_MATRIX, 120, DWELL_MINUTES_PER_STOP)
        sizes = {len(c["order"]) for c in combos}
        self.assertIn(6, sizes)

    def test_a_short_request_never_tries_sizes_dwell_time_alone_rules_out(self):
        # 30 min / 5 min dwell = 6 max by max_stops_for_request, but the
        # real walking-time check should still rule out anything that large
        # here - this asserts no 6-stop combo is ever returned as feasible.
        combos = _enumerate_feasible_combinations(BIG_SHORTLIST, BIG_MATRIX, 30, DWELL_MINUTES_PER_STOP)
        sizes = {len(c["order"]) for c in combos}
        self.assertNotIn(6, sizes)


class TestBuildAiOptions(unittest.TestCase):
    def test_ranks_options_by_budget_usage_descending(self):
        combos = _enumerate_feasible_combinations(FAKE_SHORTLIST, PLAN_MATRIX, 60, DWELL_MINUTES_PER_STOP)
        ai_options, _ = _build_ai_options(FAKE_SHORTLIST, combos)
        ratios = [opt["budget_usage_ratio"] for opt in ai_options]
        self.assertEqual(ratios, sorted(ratios, reverse=True))

    def test_every_offered_option_is_feasible(self):
        combos = _enumerate_feasible_combinations(FAKE_SHORTLIST, PLAN_MATRIX, 60, DWELL_MINUTES_PER_STOP)
        _, combos_by_key = _build_ai_options(FAKE_SHORTLIST, combos)
        self.assertTrue(all(combo["feasible"] for combo in combos_by_key.values()))

    def test_stop_ids_in_each_option_align_with_the_shortlist(self):
        combos = _enumerate_feasible_combinations(FAKE_SHORTLIST, PLAN_MATRIX, 60, DWELL_MINUTES_PER_STOP)
        ai_options, combos_by_key = _build_ai_options(FAKE_SHORTLIST, combos)
        for option in ai_options:
            combo = combos_by_key[option["option_key"]]
            expected_ids = [FAKE_SHORTLIST[i - 1]["id"] for i in combo["order"]]
            actual_ids = [stop["id"] for stop in option["stops"]]
            self.assertEqual(actual_ids, expected_ids)

    def test_ad7_coverage_pass_rescues_a_low_ranked_stop(self):
        """AD-7 (Story 1.4): a stop whose only feasible combination has a
        low budget_usage_ratio must still get a menu slot, not silently
        vanish because a plain top-N-by-ratio slice filled up on other
        combos first. Hand-constructed combos (not real routing math) for
        full control over exactly which stop would be excluded without the
        fix, since real combinatorics are hard to predict by hand."""
        shortlist = [make_place(f"s{i}", -33.901, 151.181, ["public_art"]) for i in range(16)]

        def fake_combo(order, ratio):
            return {"feasible": True, "reason": None, "order": order,
                    "total_minutes": ratio * 60, "unused_minutes": (1 - ratio) * 60,
                    "budget_usage_ratio": ratio}

        # 15 high-ranked pairs covering stops 1-15 (never 16) - already
        # exactly fills AI_OPTION_MENU_SIZE on its own, pre-fix.
        high_ranked = [fake_combo([i, i + 1], 0.9) for i in range(1, 15)]
        high_ranked.append(fake_combo([1, 3], 0.9))  # 15th combo, still never touches 16
        # Stop 16's only feasible combination - ranks last.
        low_ranked = fake_combo([16], 0.1)
        combos = high_ranked + [low_ranked]
        self.assertEqual(len(high_ranked), AI_OPTION_MENU_SIZE)

        ai_options, _ = _build_ai_options(shortlist, combos)

        self.assertEqual(len(ai_options), AI_OPTION_MENU_SIZE)
        covered_ids = {stop["id"] for opt in ai_options for stop in opt["stops"]}
        self.assertIn("s15", covered_ids)  # shortlist index 16 -> id "s15"

    def test_caps_the_menu_at_ai_option_menu_size(self):
        combos = _enumerate_feasible_combinations(BIG_SHORTLIST, BIG_MATRIX, 120, DWELL_MINUTES_PER_STOP)
        self.assertGreater(len(combos), AI_OPTION_MENU_SIZE)  # 57 feasible combinations (56 at sizes 2-5, +1 new size-6 combo since the FR-5 dynamic-stop-count change)
        ai_options, _ = _build_ai_options(BIG_SHORTLIST, combos)
        self.assertEqual(len(ai_options), AI_OPTION_MENU_SIZE)

    def test_never_excludes_the_only_feasible_option_even_if_low_usage(self):
        combos = _enumerate_feasible_combinations(
            FAKE_SHORTLIST, ONLY_ONE_FEASIBLE_MATRIX, 60, DWELL_MINUTES_PER_STOP
        )
        ai_options, _ = _build_ai_options(FAKE_SHORTLIST, combos)
        self.assertEqual(len(ai_options), 1)
        self.assertLess(ai_options[0]["budget_usage_ratio"], 0.5)


def _selection(option_key, none_suitable_reason=""):
    """ai.select_stops()'s real return shape (Story 1.4) - a dict, not a
    bare string. Use this everywhere a test mocks ai.select_stops()."""
    return {"selected_option": option_key, "none_suitable_reason": none_suitable_reason}


class TestPlanRoute(unittest.TestCase):
    """Sprint 4 redesign: Python enumerates every feasible combination up
    front (see TestEnumerateFeasibleCombinations/TestBuildAiOptions above)
    and AI only picks an option_key from that pre-validated menu - it can no
    longer propose an infeasible or arithmetically-wrong selection. See
    "Redesign after live testing" in docs/ai-development-log.md."""

    def setUp(self):
        shortlist_patcher = patch("planner.shortlist_candidates", return_value=FAKE_SHORTLIST)
        matrix_patcher = patch("planner.fetch_duration_matrix", return_value=PLAN_MATRIX)
        self.mock_shortlist = shortlist_patcher.start()
        self.mock_matrix = matrix_patcher.start()
        self.addCleanup(shortlist_patcher.stop)
        self.addCleanup(matrix_patcher.stop)

    def test_accepts_ai_choosing_the_first_offered_option(self):
        # option_1 is the highest-usage feasible combo: the 3-stop one
        # (45/60 = 75%), ranked ahead of the three tied 2-stop pairs.
        with patch("ai.select_stops", return_value=_selection("option_1")) as mock_select:
            result = plan_route(START_LAT, START_LON, "public_art", 60)
        self.assertTrue(result["feasible"])
        self.assertEqual(set(result["selected_ids"]), {"a", "b", "c"})
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(mock_select.call_count, 1)

    def test_every_offered_option_key_yields_a_feasible_result(self):
        # Directly demonstrates the fix: no matter which offered option AI
        # picks, the result is always feasible - AI can no longer produce
        # the "guess again" failure mode the live test hit.
        for option_key in ["option_1", "option_2", "option_3", "option_4"]:
            with patch("ai.select_stops", return_value=_selection(option_key)):
                result = plan_route(START_LAT, START_LON, "public_art", 60)
            self.assertTrue(result["feasible"], f"{option_key} should be feasible")

    def test_options_passed_to_ai_are_the_full_ranked_feasible_menu(self):
        with patch("ai.select_stops", return_value=_selection("option_1")) as mock_select:
            plan_route(START_LAT, START_LON, "public_art", 60)
        options_arg = mock_select.call_args.args[0]
        self.assertEqual(len(options_arg), 4)
        ratios = [opt["budget_usage_ratio"] for opt in options_arg]
        self.assertEqual(ratios, sorted(ratios, reverse=True))

    def test_retries_when_ai_returns_an_option_key_not_offered(self):
        with patch("ai.select_stops", side_effect=[_selection("option_99"), _selection("option_1")]) as mock_select:
            result = plan_route(START_LAT, START_LON, "public_art", 60)
        self.assertTrue(result["feasible"])
        self.assertEqual(result["attempts"], 2)
        second_call_feedback = mock_select.call_args_list[1].kwargs["feedback"]
        self.assertIn("option_99", second_call_feedback)
        self.assertIn("not one of the offered", second_call_feedback)

    def test_exhausted_retries_raises_instead_of_an_honest_fallback(self):
        # Codex review 2026-10-21: exhausting every retry without AI ever
        # producing a usable selection is a persistent technical problem,
        # not an honest "no suitable walk" - must not share _plan_failure()'s
        # {"feasible": false} shape (the same reasoning AiFatalError already
        # gets).
        with patch("ai.select_stops", return_value=_selection("option_99")) as mock_select:
            with self.assertRaises(AiExhaustedError) as cm:
                plan_route(START_LAT, START_LON, "public_art", 60)
        self.assertIn("3 attempts", str(cm.exception))
        self.assertEqual(mock_select.call_count, 3)

    def test_ai_selection_error_is_treated_as_invalid_attempt_and_retried(self):
        with patch("ai.select_stops", side_effect=[AiSelectionError("boom"), _selection("option_1")]) as mock_select:
            result = plan_route(START_LAT, START_LON, "public_art", 60)
        self.assertTrue(result["feasible"])
        self.assertEqual(result["attempts"], 2)

    def test_fatal_ai_error_propagates_without_retrying(self):
        # Invalid credentials, permission errors, or exhausted quota can
        # never succeed by retrying an unmodified request - and, since
        # Story 1.4, this is no longer collapsed into _plan_failure()'s
        # {"feasible": false} shape at all. plan_route() re-raises so a
        # caller can map it to a real non-2xx distinct from ordinary
        # infeasibility (mirrors how CatalogueError already propagates).
        with patch("ai.select_stops", side_effect=AiFatalError("invalid API key")) as mock_select:
            with self.assertRaises(AiFatalError) as cm:
                plan_route(START_LAT, START_LON, "public_art", 60)
        self.assertIn("invalid API key", str(cm.exception))
        self.assertEqual(mock_select.call_count, 1)

    def test_none_suitable_is_an_honest_fallback_not_a_retry(self):
        # AD-7: AI can honestly reject every offered option as not genuinely
        # suitable, even though all are time-feasible - distinct from an
        # unrecognized option_key (which retries) and from a fatal error
        # (which propagates).
        with patch("ai.select_stops", return_value=_selection("none_suitable", "none fit the mood")) as mock_select:
            result = plan_route(START_LAT, START_LON, "public_art", 60)
        self.assertFalse(result["feasible"])
        self.assertEqual(result["reason"], "none fit the mood")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(mock_select.call_count, 1)
        self.assertEqual(result["attempts_log"][0]["outcome"], "none_suitable")

    def test_no_feasible_combination_short_circuits_without_calling_ai(self):
        # Nothing fits in 30 min with PLAN_MATRIX - detected up front,
        # rather than spending 3 AI calls discovering it one guess at a time.
        with patch("ai.select_stops") as mock_select:
            result = plan_route(START_LAT, START_LON, "public_art", 30)
        mock_select.assert_not_called()
        self.assertFalse(result["feasible"])
        self.assertIn("no combination", result["reason"])
        self.assertEqual(result["attempts"], 0)
        self.assertEqual(result["attempts_log"], [])

    def test_too_few_shortlist_candidates_short_circuits_without_calling_ai(self):
        self.mock_shortlist.return_value = [FAKE_SHORTLIST[0]]
        with patch("ai.select_stops") as mock_select:
            result = plan_route(START_LAT, START_LON, "public_art", 60)
        mock_select.assert_not_called()
        self.assertFalse(result["feasible"])
        self.assertIn("at least", result["reason"])
        self.assertEqual(result["attempts"], 0)
        self.assertEqual(result["attempts_log"], [])

    def test_excluded_ids_passed_through_to_shortlisting(self):
        # Story 1.7: plan_route() is purely a pass-through to
        # shortlist_candidates() for excluded_ids - the actual hard-filter
        # enforcement lives in shortlist_candidates() itself (see
        # TestShortlisting.test_excluded_ids_filtered_out).
        with patch("ai.select_stops", return_value=_selection("option_1")):
            plan_route(START_LAT, START_LON, "public_art", 60, excluded_ids=["x", "y"])
        self.assertEqual(
            self.mock_shortlist.call_args.kwargs.get("excluded_ids"), ["x", "y"]
        )

    def test_excluded_ids_none_normalizes_to_empty_list(self):
        # Callers/tests may omit excluded_ids entirely (the default,
        # None) - must behave exactly like passing [], never crash on a
        # `in excluded_ids` check downstream.
        with patch("ai.select_stops", return_value=_selection("option_1")):
            plan_route(START_LAT, START_LON, "public_art", 60)
        self.assertEqual(self.mock_shortlist.call_args.kwargs.get("excluded_ids"), [])


class TestPlanRouteExcludedIdsEndToEnd(unittest.TestCase):
    """Story 1.7: with real (unmocked) shortlisting, excluding the stops
    of the only feasible combination genuinely removes it - plan_route()
    returns a different/no route, not the same one it would without
    exclusion."""

    def setUp(self):
        places_patcher = patch("planner.load_ready_places", return_value=FAKE_SHORTLIST)
        matrix_patcher = patch("planner.fetch_duration_matrix", return_value=ONLY_ONE_FEASIBLE_MATRIX)
        places_patcher.start()
        matrix_patcher.start()
        self.addCleanup(places_patcher.stop)
        self.addCleanup(matrix_patcher.stop)

    def test_no_exclusion_finds_the_only_feasible_combination(self):
        with patch("ai.select_stops", return_value=_selection("option_1")):
            result = plan_route(START_LAT, START_LON, "public_art", 60)
        self.assertTrue(result["feasible"])
        self.assertEqual(set(result["selected_ids"]), {"a", "b"})

    def test_excluding_the_feasible_combinations_stops_leaves_no_route(self):
        # "a" and "b" are the only feasible combination's stops (AD-5:
        # Re-Jaunt excludes every stop of the whole rejected route) -
        # excluding both leaves only "c", which alone can't form a
        # 2-stop walk at all.
        with patch("ai.select_stops") as mock_select:
            result = plan_route(START_LAT, START_LON, "public_art", 60, excluded_ids=["a", "b"])
        mock_select.assert_not_called()
        self.assertFalse(result["feasible"])


class TestPlanRouteAttemptsLog(unittest.TestCase):
    """Diagnostic log of what AI proposed on every attempt, added after a
    live test produced "no suitable route" with no visibility into what
    the model actually tried - see docs/ai-development-log.md."""

    def setUp(self):
        shortlist_patcher = patch("planner.shortlist_candidates", return_value=FAKE_SHORTLIST)
        matrix_patcher = patch("planner.fetch_duration_matrix", return_value=PLAN_MATRIX)
        shortlist_patcher.start()
        matrix_patcher.start()
        self.addCleanup(shortlist_patcher.stop)
        self.addCleanup(matrix_patcher.stop)

    def test_records_one_entry_per_attempt_with_option_and_outcome(self):
        with patch("ai.select_stops", side_effect=[_selection("option_99"), _selection("option_1")]):
            result = plan_route(START_LAT, START_LON, "public_art", 60)
        log = result["attempts_log"]
        self.assertEqual(len(log), 2)
        self.assertEqual(log[0]["outcome"], "unknown_option")
        self.assertEqual(log[0]["selected_option"], "option_99")
        self.assertEqual(log[1]["outcome"], "accepted")
        self.assertEqual(log[1]["selected_option"], "option_1")
        self.assertIsNone(log[1]["reason"])

    def test_records_ai_errors_with_no_selected_option(self):
        with patch("ai.select_stops", side_effect=[AiSelectionError("boom"), _selection("option_1")]):
            result = plan_route(START_LAT, START_LON, "public_art", 60)
        log = result["attempts_log"]
        self.assertEqual(log[0]["outcome"], "ai_error")
        self.assertIsNone(log[0]["selected_option"])
        self.assertIn("boom", log[0]["reason"])



class TestReplacementPlanning(unittest.TestCase):
    def setUp(self):
        self.places = [make_place(str(i), START_LAT + i * .00001, START_LON, ['history']) for i in range(14)]

    def plan(self, retained, selection='option_1', matrix=None):
        with patch('planner.load_ready_places', return_value=self.places), patch('planner.fetch_duration_matrix', return_value=matrix or [[0 if i == j else 60 for j in range(13)] for i in range(13)]), patch('ai.select_stops', return_value={'selected_option': selection, 'none_suitable_reason': 'unsuitable'}):
            return plan_route(START_LAT, START_LON, 'history', 60, excluded_ids=['0'], retained_ids=retained, replacement_mode=True)

    def test_retained_beyond_cap_is_reserved(self):
        shortlist = shortlist_candidates(START_LAT, START_LON, 'history', places=self.places, excluded_ids=['0'], retained_ids=['13'])
        self.assertEqual(len(shortlist), SHORTLIST_CAP)
        self.assertIn('13', [p['id'] for p in shortlist])

    def test_found_keeps_every_retained_and_exactly_one_new(self):
        result = self.plan(['13', '3'])
        self.assertEqual(result['replacement_outcome'], 'replacement_found')
        self.assertEqual(len(result['selected_ids']), 3)
        self.assertTrue({'13', '3'} <= set(result['selected_ids']))
        self.assertNotIn('0', result['selected_ids'])

    def test_none_suitable_preserves_order_and_refreshes_time(self):
        result = self.plan(['13', '3'], 'none_suitable')
        self.assertEqual(result['replacement_outcome'], 'retained_only')
        self.assertEqual(result['selected_ids'], ['13', '3'])
        self.assertEqual(result['total_minutes'], 13)

    def test_two_to_one_and_final_stop(self):
        shorter = self.plan(['13'], 'none_suitable')
        self.assertEqual(shorter['total_minutes'], 7)
        self.assertEqual(shorter['selected_ids'], ['13'])
        final = self.plan([])
        self.assertEqual(len(final['selected_ids']), 1)
        self.assertFalse(self.plan([], 'none_suitable')['feasible'])

    def test_seven_stop_replacement_stays_seven(self):
        self.assertEqual(len(self.plan(['1', '2', '3', '4', '5', '13'])['selected_ids']), 7)

    def test_no_time_feasible_completion_keeps_retained(self):
        matrix = [[0 if i == j else 3600 for j in range(13)] for i in range(13)]
        matrix[0][1] = matrix[1][0] = 60
        result = self.plan(['13'], matrix=matrix)
        self.assertEqual(result['replacement_outcome'], 'retained_only')
        self.assertEqual(result['total_minutes'], 7)

    def test_unverified_retained_route_is_technical_failure(self):
        import requests
        with self.assertRaises(requests.RequestException):
            self.plan(['13'], matrix=[[0 if i == j else None for j in range(13)] for i in range(13)])

class TestUnavailableRetainedPlaces(unittest.TestCase):
    def test_missing_or_coordinate_less_retained_record_fails_before_providers(self):
        import requests
        good = make_place('good', START_LAT, START_LON, ['history'])
        bad = make_place('retained', None, START_LON, ['history'])
        for places in ([good], [good, bad]):
            with self.subTest(places=places), patch('planner.load_ready_places', return_value=places), patch('planner.fetch_duration_matrix') as matrix, patch('ai.select_stops') as select:
                with self.assertRaises(requests.RequestException):
                    plan_route(START_LAT, START_LON, 'history', 60, retained_ids=['retained'], replacement_mode=True)
                matrix.assert_not_called()
                select.assert_not_called()


if __name__ == "__main__":
    unittest.main()
