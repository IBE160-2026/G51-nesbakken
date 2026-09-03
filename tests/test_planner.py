import unittest

from planner import (
    SHORTLIST_CAP,
    check_feasibility,
    compute_best_order,
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
        # out-of-range indices here don't matter.
        result = check_feasibility(0, [1, 2, 3, 4, 5, 6], self.matrix, requested_minutes=120)
        self.assertFalse(result["feasible"])
        self.assertIn("between", result["reason"])


if __name__ == "__main__":
    unittest.main()
