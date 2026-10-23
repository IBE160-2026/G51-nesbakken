import json
import os
import tempfile
import unittest
from unittest.mock import patch

import requests

import app as app_module
import ai
from tests.test_planner import FAKE_SHORTLIST, PLAN_MATRIX
from ai import AiExhaustedError, AiFatalError

FIXTURE_RECORDS = [
    {
        "id": "node/1",
        "name": "Ready Place",
        "latitude": -33.90,
        "longitude": 151.18,
        "osm_type": "node",
        "osm_tags": {"historic": "yes"},
        "topics": ["history"],
        "source_type": "wikipedia",
        "source_title": "Ready Place",
        "source_url": "https://en.wikipedia.org/wiki/Ready_Place",
        "source_excerpt": "A real place.",
        "status": "ready",
        "imported_at": "2026-01-01T00:00:00Z",
        "rejection_reason": None,
    },
    {
        "id": "node/2",
        "name": "Another Ready Place",
        "latitude": -33.91,
        "longitude": 151.17,
        "osm_type": "node",
        "osm_tags": {},
        "topics": ["public_art"],
        "source_type": "osm_tags",
        "source_title": None,
        "source_url": "https://www.openstreetmap.org/node/2",
        "source_excerpt": "By Someone.",
        "status": "ready",
        "imported_at": "2026-01-01T00:00:00Z",
        "rejection_reason": None,
    },
    {
        "id": "node/3",
        "name": "Limited Place",
        "latitude": -33.92,
        "longitude": 151.16,
        "osm_type": "node",
        "osm_tags": {},
        "topics": ["history"],
        "source_type": None,
        "source_title": None,
        "source_url": None,
        "source_excerpt": None,
        "status": "limited",
        "imported_at": "2026-01-01T00:00:00Z",
        "rejection_reason": "no usable source found",
    },
    {
        "id": "node/4",
        "name": None,
        "latitude": None,
        "longitude": None,
        "osm_type": "node",
        "osm_tags": {},
        "topics": [],
        "source_type": None,
        "source_title": None,
        "source_url": None,
        "source_excerpt": None,
        "status": "rejected",
        "imported_at": "2026-01-01T00:00:00Z",
        "rejection_reason": "missing name",
    },
]


class TestApiPlaces(unittest.TestCase):
    def setUp(self):
        self.original_data_path = app_module.DATA_PATH
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(FIXTURE_RECORDS, f)
        self.fixture_path = path
        app_module.DATA_PATH = path
        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.DATA_PATH = self.original_data_path
        os.remove(self.fixture_path)

    def test_only_ready_records_returned(self):
        response = self.client.get("/api/places")
        self.assertEqual(response.status_code, 200)
        places = response.get_json()
        self.assertEqual(len(places), 2)
        self.assertEqual({p["id"] for p in places}, {"node/1", "node/2"})

    def test_expected_fields_present_and_nothing_else(self):
        response = self.client.get("/api/places")
        places = response.get_json()
        expected_fields = {
            "id", "name", "latitude", "longitude", "topics",
            "source_type", "source_title", "source_url", "source_excerpt",
        }
        for place in places:
            self.assertEqual(set(place.keys()), expected_fields)

    def test_internal_fields_not_exposed(self):
        response = self.client.get("/api/places")
        places = response.get_json()
        for place in places:
            for internal_field in ("osm_tags", "status", "rejection_reason", "imported_at", "osm_type"):
                self.assertNotIn(internal_field, place)

class TestCatalogueErrorHandling(unittest.TestCase):
    def setUp(self):
        self.original_data_path = app_module.DATA_PATH
        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.DATA_PATH = self.original_data_path

    def _write_fixture(self, content):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        app_module.DATA_PATH = path

    def test_missing_catalogue_file_returns_controlled_error(self):
        app_module.DATA_PATH = os.path.join(tempfile.gettempdir(), "does_not_exist.json")
        response = self.client.get("/api/places")
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.get_json())

    def test_malformed_json_returns_controlled_error(self):
        self._write_fixture("{not valid json")
        response = self.client.get("/api/places")
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.get_json())

    def test_non_list_json_returns_controlled_error(self):
        self._write_fixture(json.dumps({"unexpected": "shape"}))
        response = self.client.get("/api/places")
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.get_json())

    def test_valid_empty_catalogue_returns_empty_list(self):
        self._write_fixture(json.dumps([]))
        response = self.client.get("/api/places")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])


class TestIndexRoute(unittest.TestCase):
    def test_index_returns_200(self):
        client = app_module.app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)


VALID_PLAN_BODY = {
    "start_lat": -33.898, "start_lon": 151.179, "topic": "history", "requested_minutes": 60,
}

FEASIBLE_RESULT = {
    "feasible": True,
    "reason": None,
    "order": [1, 2],
    "total_minutes": 45.0,
    "unused_minutes": 15.0,
    "budget_usage_ratio": 0.75,
    "shortlist": [
        {"id": "a", "name": "Stop A", "latitude": -33.899, "longitude": 151.180},
        {"id": "b", "name": "Stop B", "latitude": -33.897, "longitude": 151.178},
    ],
    "selected_ids": ["a", "b"],
    "attempts": 1,
    "attempts_log": [],
}

INFEASIBLE_RESULT = {
    "feasible": False, "reason": "no combination fits", "order": None,
    "total_minutes": None, "unused_minutes": None, "budget_usage_ratio": None,
    "shortlist": None, "selected_ids": None, "attempts": 0, "attempts_log": [],
}


def fake_content(stop_id, content="Generated content."):
    return {"id": stop_id, "content": content, "attribution": [
        {"source_type": "wikipedia", "source_title": "T", "source_url": "https://x"}
    ]}


class TestApiPlanValidation(unittest.TestCase):
    """Story 1.4: malformed/invalid input is rejected before any
    routing-provider or AI call is made - each case here asserts the
    external calls were never made, not just the status code."""

    def setUp(self):
        self.client = app_module.app.test_client()

    def _post(self, body):
        with patch("app.planner.plan_route") as mock_plan:
            response = self.client.post("/api/plan", json=body)
        return response, mock_plan

    def test_non_json_body_rejected(self):
        response = self.client.post("/api/plan", data="not json", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

    def test_invalid_preference_rejected_before_planning(self):
        for value in (True, False, None, "0.5", [], {}, float("nan"), float("inf"), -float("inf"), -0.01, 1.01):
            with self.subTest(value=value):
                response, mock_plan = self._post(dict(VALID_PLAN_BODY, preference=value))
                self.assertEqual(response.status_code, 400)
                mock_plan.assert_not_called()

    def test_preference_defaults_to_balanced_only_when_omitted(self):
        with patch("app.planner.plan_route", return_value=INFEASIBLE_RESULT) as mock_plan:
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_plan.call_args.kwargs["preference"], 0.5)

    def test_exact_preference_reaches_real_prompt_through_retry(self):
        # Only external boundaries are mocked: API, planner and prompt builder run.
        shortlist = [dict(place) for place in FAKE_SHORTLIST]
        shortlist[0].update(source_type="heritage_register", source_title="Register entry")
        shortlist[1].update(source_type="osm_tags", source_title=None)
        for value in (0, 0.5, 1, 0.37):
            with self.subTest(value=value), patch("planner.collect_eligible_candidates", return_value=shortlist), patch("planner.fetch_duration_matrix", return_value=PLAN_MATRIX), patch("ai._call_openai", side_effect=[
                ai.AiSelectionError("temporary failure"),
                json.dumps({"selected_option": ai.NONE_SUITABLE, "none_suitable_reason": "not relevant"}),
            ]) as provider:
                response = self.client.post("/api/plan", json=dict(VALID_PLAN_BODY, preference=value))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(provider.call_count, 2)
            for call in provider.call_args_list:
                details = json.JSONDecoder().raw_decode(call.args[0].split("\n\n", 1)[1])[0]
                self.assertEqual(details["preference"], value)
                evidence = {stop["id"]: stop for option in details["options"] for stop in option["stops"]}
                for place in shortlist:
                    self.assertEqual(evidence[place["id"]]["source_type"], place.get("source_type"))
                    self.assertEqual(evidence[place["id"]]["source_title"], place.get("source_title"))

    def test_exact_preference_can_produce_successful_offered_route(self):
        shortlist = [dict(place) for place in FAKE_SHORTLIST]
        shortlist[0].update(source_type="heritage_register", source_title="Register entry")
        shortlist[1].update(source_type="osm_tags", source_title=None)
        geometry = [[151.18, -33.9], [151.181, -33.901], [151.18, -33.9]]
        content = [{"id": place["id"], "content": "Grounded fixture text", "attribution": []}
                   for place in shortlist]
        for value in (0, 0.5, 1, 0.37):
            with self.subTest(value=value), patch("planner.collect_eligible_candidates", return_value=shortlist), patch("planner.fetch_duration_matrix", return_value=PLAN_MATRIX), patch("ai._call_openai", return_value=json.dumps({"selected_option": "option_1", "none_suitable_reason": ""})) as provider, patch("app.services.fetch_route_geometry", return_value=geometry), patch("app.ai.generate_stop_content", return_value=content):
                response = self.client.post("/api/plan", json=dict(VALID_PLAN_BODY, preference=value))
            self.assertEqual(response.status_code, 200)
            result = response.get_json()
            self.assertTrue(result["feasible"])
            self.assertEqual(result["geometry"], geometry)
            self.assertLessEqual(result["total_minutes"], VALID_PLAN_BODY["requested_minutes"])
            details = json.JSONDecoder().raw_decode(provider.call_args.args[0].split("\n\n", 1)[1])[0]
            self.assertEqual(details["preference"], value)
            offered = details["options"][0]["stops"]
            self.assertEqual([stop["id"] for stop in result["stops"]], [stop["id"] for stop in offered])
            for stop in result["stops"]:
                self.assertEqual(stop["content"], "Grounded fixture text")
            evidence = {stop["id"]: stop for stop in offered}
            for place in shortlist:
                stop = evidence[place["id"]]
                self.assertEqual(stop["source_type"], place.get("source_type"))
                self.assertEqual(stop["source_title"], place.get("source_title"))

    def test_missing_fields_rejected(self):
        response, mock_plan = self._post({"start_lat": -33.9})
        self.assertEqual(response.status_code, 400)
        mock_plan.assert_not_called()

    def test_out_of_range_latitude_rejected(self):
        body = dict(VALID_PLAN_BODY, start_lat=1000)
        response, mock_plan = self._post(body)
        self.assertEqual(response.status_code, 400)
        mock_plan.assert_not_called()

    def test_out_of_range_longitude_rejected(self):
        body = dict(VALID_PLAN_BODY, start_lon=-200)
        response, mock_plan = self._post(body)
        self.assertEqual(response.status_code, 400)
        mock_plan.assert_not_called()

    def test_non_numeric_coordinate_rejected(self):
        body = dict(VALID_PLAN_BODY, start_lat="not a number")
        response, mock_plan = self._post(body)
        self.assertEqual(response.status_code, 400)
        mock_plan.assert_not_called()

    def test_boolean_is_not_accepted_as_a_number(self):
        # bool is technically an int subclass in Python - must not silently
        # pass as 1/0 for a numeric field.
        body = dict(VALID_PLAN_BODY, requested_minutes=True)
        response, mock_plan = self._post(body)
        self.assertEqual(response.status_code, 400)
        mock_plan.assert_not_called()

    def test_time_outside_30_120_rejected(self):
        for minutes in (20, 150):
            body = dict(VALID_PLAN_BODY, requested_minutes=minutes)
            response, mock_plan = self._post(body)
            self.assertEqual(response.status_code, 400)
            mock_plan.assert_not_called()

    def test_unrecognized_topic_rejected(self):
        body = dict(VALID_PLAN_BODY, topic="gardening")
        response, mock_plan = self._post(body)
        self.assertEqual(response.status_code, 400)
        mock_plan.assert_not_called()

    def test_non_string_topic_rejected_not_a_crash(self):
        # Codex review 2026-10-21: `topic not in VALID_TOPICS` on a set used
        # to raise TypeError for an unhashable JSON value instead of a
        # controlled 400.
        for topic in ([], {}, 42, None):
            body = dict(VALID_PLAN_BODY, topic=topic)
            response, mock_plan = self._post(body)
            self.assertEqual(response.status_code, 400)
            mock_plan.assert_not_called()

    def test_non_integer_requested_minutes_rejected_not_a_crash(self):
        # Codex review 2026-10-21: a float like 30.0 passed the old range
        # check, then crashed range() deep inside the planner instead of
        # being rejected here.
        body = dict(VALID_PLAN_BODY, requested_minutes=60.0)
        response, mock_plan = self._post(body)
        self.assertEqual(response.status_code, 400)
        mock_plan.assert_not_called()

    def test_non_five_minute_increment_rejected(self):
        body = dict(VALID_PLAN_BODY, requested_minutes=61)
        response, mock_plan = self._post(body)
        self.assertEqual(response.status_code, 400)
        mock_plan.assert_not_called()

    def test_valid_topics_all_accepted(self):
        for topic in ("history", "architecture", "public_art", "surprise_me"):
            body = dict(VALID_PLAN_BODY, topic=topic)
            with patch("app.planner.plan_route", return_value=INFEASIBLE_RESULT) as mock_plan:
                response = self.client.post("/api/plan", json=body)
            self.assertEqual(response.status_code, 200)
            mock_plan.assert_called_once()

    def test_excluded_ids_omitted_defaults_to_empty_list(self):
        # Story 1.7: absent entirely (every request before the first
        # Re-Jaunt) must behave exactly as it does today, not require the
        # field.
        with patch("app.planner.plan_route", return_value=INFEASIBLE_RESULT) as mock_plan:
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_plan.call_args.kwargs.get("excluded_ids"), [])

    def test_valid_excluded_ids_list_accepted_and_threaded_through(self):
        body = dict(VALID_PLAN_BODY, excluded_ids=["node/1", "node/2"])
        with patch("app.planner.plan_route", return_value=INFEASIBLE_RESULT) as mock_plan:
            response = self.client.post("/api/plan", json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_plan.call_args.kwargs.get("excluded_ids"), ["node/1", "node/2"])

    def test_malformed_excluded_ids_rejected(self):
        # Same pattern as every other malformed field: a real 400 before
        # any routing/AI call, not a crash or a silent pass-through.
        for excluded_ids in ("abc", [1, 2], {"a": 1}, [None]):
            body = dict(VALID_PLAN_BODY, excluded_ids=excluded_ids)
            response, mock_plan = self._post(body)
            self.assertEqual(response.status_code, 400)
            mock_plan.assert_not_called()


class TestApiPlanOutcomes(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_infeasible_result_returns_200_with_reason(self):
        with patch("app.planner.plan_route", return_value=INFEASIBLE_RESULT), \
             patch("app.services.fetch_route_geometry") as mock_geo, \
             patch("app.ai.generate_stop_content") as mock_content:
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertFalse(body["feasible"])
        self.assertEqual(body["reason"], "no combination fits")
        # Infeasible means no stops were ever selected - neither geometry
        # nor content generation have anything to run against.
        mock_geo.assert_not_called()
        mock_content.assert_not_called()

    def test_ai_fatal_error_returns_503_not_the_feasible_false_shape(self):
        with patch("app.planner.plan_route", side_effect=AiFatalError("invalid API key")):
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.get_json())
        self.assertNotIn("feasible", response.get_json())

    def test_routing_provider_failure_returns_503(self):
        with patch("app.planner.plan_route", side_effect=requests.exceptions.ConnectionError("boom")):
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.get_json())

    def test_ai_exhausted_error_returns_503_not_the_feasible_false_shape(self):
        # Codex review 2026-10-21: exhausted AiSelectionError retries used
        # to collapse into the same {"feasible": False} shape as an honest
        # "no suitable walk" - indistinguishable from genuine infeasibility.
        with patch("app.planner.plan_route", side_effect=AiExhaustedError("AI did not return a usable option after 3 attempts")):
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.get_json())
        self.assertNotIn("feasible", response.get_json())

    def test_feasible_route_returns_full_response(self):
        with patch("app.planner.plan_route", return_value=FEASIBLE_RESULT), \
             patch("app.services.fetch_route_geometry", return_value=[[151.179, -33.898]]), \
             patch("app.ai.generate_stop_content", return_value=[fake_content("a"), fake_content("b")]):
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["feasible"])
        self.assertEqual(body["total_minutes"], 45.0)
        self.assertEqual(body["geometry"], [[151.179, -33.898]])
        self.assertEqual(len(body["stops"]), 2)
        self.assertEqual(body["stops"][0], {
            "id": "a", "order": 1,
            "name": "Stop A", "latitude": -33.899, "longitude": 151.180, "topics": [],
            "content": "Generated content.",
            "attribution": [{"source_type": "wikipedia", "source_title": "T", "source_url": "https://x"}],
        })
        self.assertEqual(body["stops"][1]["order"], 2)
        self.assertEqual(body["stops"][1]["name"], "Stop B")

    def test_geometry_failure_degrades_gracefully_not_a_request_failure(self):
        # User's explicit choice (Story 1.4 spec): a geometry-fetch failure
        # never fails the whole request - the route, stops, and content
        # are still good.
        with patch("app.planner.plan_route", return_value=FEASIBLE_RESULT), \
             patch("app.services.fetch_route_geometry", side_effect=requests.exceptions.ConnectionError("boom")), \
             patch("app.ai.generate_stop_content", return_value=[fake_content("a"), fake_content("b")]):
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["feasible"])
        self.assertIsNone(body["geometry"])
        self.assertEqual(len(body["stops"]), 2)  # route/content still intact

    def test_malformed_geometry_response_degrades_gracefully(self):
        # Codex review 2026-10-21: a malformed-but-200 provider response
        # (e.g. an empty "features" array) raises KeyError/IndexError in
        # fetch_route_geometry, which the old `except requests.RequestException`
        # alone did not catch.
        with patch("app.planner.plan_route", return_value=FEASIBLE_RESULT), \
             patch("app.services.fetch_route_geometry", side_effect=IndexError("list index out of range")), \
             patch("app.ai.generate_stop_content", return_value=[fake_content("a"), fake_content("b")]):
            response = self.client.post("/api/plan", json=VALID_PLAN_BODY)
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["feasible"])
        self.assertIsNone(body["geometry"])
        self.assertEqual(len(body["stops"]), 2)

    def test_content_generation_called_with_ordered_stops_and_requested_topic(self):
        with patch("app.planner.plan_route", return_value=FEASIBLE_RESULT), \
             patch("app.services.fetch_route_geometry", return_value=None), \
             patch("app.ai.generate_stop_content", return_value=[fake_content("a"), fake_content("b")]) as mock_content:
            self.client.post("/api/plan", json=VALID_PLAN_BODY)
        args, _ = mock_content.call_args
        stops_arg, topic_arg = args
        self.assertEqual([s["id"] for s in stops_arg], ["a", "b"])  # walking order
        self.assertEqual(topic_arg, "history")

    def test_geometry_fetched_in_start_stops_start_order(self):
        with patch("app.planner.plan_route", return_value=FEASIBLE_RESULT), \
             patch("app.services.fetch_route_geometry", return_value=None) as mock_geo, \
             patch("app.ai.generate_stop_content", return_value=[fake_content("a"), fake_content("b")]):
            self.client.post("/api/plan", json=VALID_PLAN_BODY)
        points_arg = mock_geo.call_args.args[0]
        self.assertEqual(points_arg[0], (VALID_PLAN_BODY["start_lat"], VALID_PLAN_BODY["start_lon"]))
        self.assertEqual(points_arg[-1], (VALID_PLAN_BODY["start_lat"], VALID_PLAN_BODY["start_lon"]))
        self.assertEqual(points_arg[1], (-33.899, 151.180))  # Stop A
        self.assertEqual(points_arg[2], (-33.897, 151.178))  # Stop B


class TestRequestBodySizeLimit(unittest.TestCase):
    """Follow-up from the Story 1.4 Codex review 2026-10-21: the spec
    promised oversized-body rejection but nothing enforced it."""

    def setUp(self):
        self.client = app_module.app.test_client()

    def test_oversized_body_rejected_with_json_error(self):
        oversized_topic = "x" * (app_module.app.config["MAX_CONTENT_LENGTH"] + 1)
        body = dict(VALID_PLAN_BODY, topic=oversized_topic)
        response = self.client.post("/api/plan", json=body)
        self.assertEqual(response.status_code, 413)
        self.assertIn("error", response.get_json())



class TestReplacementValidation(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        self.base = dict(start_lat=-33.9, start_lon=151.18, topic='history', requested_minutes=60, replacement_mode=True)

    def test_malformed_retention_rejected_before_planning(self):
        cases = [dict(retained_ids=None), dict(retained_ids=['node/1', 'node/1']),
                 dict(retained_ids=['unknown']), dict(retained_ids=['node/3']),
                 dict(retained_ids=['node/1'], excluded_ids=['node/1']),
                 dict(retained_ids=['node/1'], replacement_mode=False),
                 dict(retained_ids=[], replacement_mode='yes'), dict(retained_ids=[{}])]
        with patch('app.load_ready_places', return_value=FIXTURE_RECORDS[:2]), patch('planner.plan_route') as plan:
            for changes in cases:
                with self.subTest(changes=changes):
                    self.assertEqual(self.client.post('/api/plan', json={**self.base, **changes}).status_code, 400)
            plan.assert_not_called()

    def test_empty_retention_explicitly_threads_final_stop_mode(self):
        with patch('planner.plan_route', return_value={'feasible': False, 'reason': 'none'}) as plan:
            response = self.client.post('/api/plan', json={**self.base, 'retained_ids': [], 'excluded_ids': ['old']})
            self.assertEqual(response.status_code, 200)
        self.assertEqual(plan.call_args.kwargs, dict(excluded_ids=['old'], retained_ids=[], replacement_mode=True, preference=0.5))

    def test_retained_only_response_is_explicit_with_canonical_geometry(self):
        result = dict(feasible=True, shortlist=[FIXTURE_RECORDS[0]], order=[1], total_minutes=7, unused_minutes=53, replacement_outcome='retained_only')
        geometry = [[151.18, -33.9], [151.19, -33.91], [151.18, -33.9]]
        with patch('app.load_ready_places', return_value=FIXTURE_RECORDS[:2]), patch('planner.plan_route', return_value=result), patch('services.fetch_route_geometry', return_value=geometry), patch('ai.generate_stop_content', return_value=[dict(id='node/1', content='Grounded', attribution=[])]):
            response = self.client.post('/api/plan', json={**self.base, 'retained_ids': ['node/1']})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['replacement_outcome'], 'retained_only')
            self.assertEqual(response.json['geometry'], geometry)
            self.assertEqual(response.json['total_minutes'], 7)
            self.assertEqual(len(response.json['stops']), 1)

class TestReplacementGeometry(unittest.TestCase):
    def test_bad_geometry_is_technical_failure_before_content_generation(self):
        result = dict(FEASIBLE_RESULT, replacement_outcome='replacement_found')
        cases = [None, [], [[151, -33]], [[181, -33], [151, -33]],
                 [[151, -91], [151, -33]], [[True, -33], [151, -33]],
                 [[float('nan'), -33], [151, -33]], [[151, 'bad'], [151, -33]],
                 requests.ConnectionError('network'), KeyError('features'), IndexError('coordinates'), TypeError('malformed')]
        for geometry in cases:
            options = {'side_effect': geometry} if isinstance(geometry, Exception) else {'return_value': geometry}
            with self.subTest(geometry=geometry), patch('planner.plan_route', return_value=result), patch('services.fetch_route_geometry', **options), patch('ai.generate_stop_content') as content:
                response = app_module.app.test_client().post('/api/plan', json={**VALID_PLAN_BODY, 'replacement_mode': True, 'retained_ids': []})
                self.assertEqual(response.status_code, 503)
                self.assertIn('error', response.json)
                content.assert_not_called()


if __name__ == "__main__":
    unittest.main()
