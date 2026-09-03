import json
import os
import tempfile
import unittest

import app as app_module

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


if __name__ == "__main__":
    unittest.main()
