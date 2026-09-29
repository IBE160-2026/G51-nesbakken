import unittest
from unittest.mock import Mock, patch

from import_street_art import (
    CROSS_SOURCE_DUPLICATES,
    apply_manual_duplicate_overrides,
    build_record,
    geocode_address,
    geocode_query,
    in_pilot_bbox,
    normalize_suburb,
    usable_text,
)


def make_row(row_number=2, **overrides):
    row = {
        "row_number": row_number,
        "D": "Old School Funk",  # title
        "E": "2 McGill St, Lewisham",  # full address
        "F": "2 McGill St",  # street address
        "G": "Lewisham",  # suburb
        "J": 2014.0,  # year
        "L": "Robert Zanghi",  # artist
        "M": "This art pays homage to the roots of aerosol art.",  # statement
        "O": None,  # visibility status
        "P": None,  # visited date
        "Q": None,  # photo
        "R": None,  # km walked
    }
    row.update(overrides)
    return row


class TestUsableText(unittest.TestCase):
    def test_none_is_unusable(self):
        self.assertFalse(usable_text(None))

    def test_blank_is_unusable(self):
        self.assertFalse(usable_text("   "))

    def test_placeholder_values_are_unusable(self):
        for value in ("TBC", "tbc", "CARPARK", "*Title", "*title"):
            self.assertFalse(usable_text(value), value)

    def test_real_text_is_usable(self):
        self.assertTrue(usable_text("Old School Funk"))

    def test_untitled_is_usable(self):
        # A real, deliberate artwork title elsewhere in the sheet - distinct
        # from the "*Title" placeholder marker.
        self.assertTrue(usable_text("Untitled"))


class TestNormalizeSuburb(unittest.TestCase):
    def test_known_typos_fixed(self):
        self.assertEqual(normalize_suburb("Ashifield"), "Ashfield")
        self.assertEqual(normalize_suburb("Marrickvile"), "Marrickville")
        self.assertEqual(normalize_suburb("Marricvkville"), "Marrickville")
        self.assertEqual(normalize_suburb("Leichardt"), "Leichhardt")

    def test_correct_suburb_untouched(self):
        self.assertEqual(normalize_suburb("Newtown"), "Newtown")

    def test_none_passed_through(self):
        self.assertIsNone(normalize_suburb(None))


class TestGeocodeQuery(unittest.TestCase):
    def test_collapses_embedded_newlines(self):
        query = geocode_query("105 Victoria Road\n Marrickville NSW 2204", "Marrickville")
        self.assertNotIn("\n", query)

    def test_appends_suburb_when_missing(self):
        query = geocode_query("2 McGill St", "Lewisham")
        self.assertIn("Lewisham", query)

    def test_does_not_duplicate_suburb_already_present(self):
        query = geocode_query("2 McGill St, Lewisham", "Lewisham")
        self.assertEqual(query.count("Lewisham"), 1)


class TestGeocodeAddressCaching(unittest.TestCase):
    """Regression tests for the bug where failed geocodes were cached
    permanently, so a transient error could never be retried."""

    def test_successful_lookup_is_cached(self):
        cache = {}
        response = Mock(status_code=200)
        response.json.return_value = [{"lat": "-33.9", "lon": "151.18"}]
        with patch("import_street_art.requests.get", return_value=response) as mock_get, \
             patch("import_street_art.time.sleep"):
            lat, lon = geocode_address("2 McGill St", "Lewisham", cache)
        self.assertEqual((lat, lon), (-33.9, 151.18))
        self.assertEqual(mock_get.call_count, 1)
        query = geocode_query("2 McGill St", "Lewisham")
        self.assertIn(query, cache)

        # A second call for the same address must not hit the network again.
        with patch("import_street_art.requests.get") as mock_get_again:
            geocode_address("2 McGill St", "Lewisham", cache)
        mock_get_again.assert_not_called()

    def test_http_error_is_not_cached_and_is_retried(self):
        cache = {}
        error_response = Mock(status_code=503)
        with patch("import_street_art.requests.get", return_value=error_response) as mock_get, \
             patch("import_street_art.time.sleep"):
            lat, lon = geocode_address("Unreliable Ave", "Newtown", cache)
        self.assertEqual((lat, lon), (None, None))
        query = geocode_query("Unreliable Ave", "Newtown")
        self.assertNotIn(query, cache)

        # Retrying (e.g. on the next run) must make a new request, not reuse
        # a cached failure.
        ok_response = Mock(status_code=200)
        ok_response.json.return_value = [{"lat": "-33.9", "lon": "151.18"}]
        with patch("import_street_art.requests.get", return_value=ok_response) as mock_get_retry, \
             patch("import_street_art.time.sleep"):
            lat, lon = geocode_address("Unreliable Ave", "Newtown", cache)
        self.assertEqual(mock_get_retry.call_count, 1)
        self.assertEqual((lat, lon), (-33.9, 151.18))

    def test_no_results_is_not_cached(self):
        cache = {}
        empty_response = Mock(status_code=200)
        empty_response.json.return_value = []
        with patch("import_street_art.requests.get", return_value=empty_response), \
             patch("import_street_art.time.sleep"):
            lat, lon = geocode_address("Nowhere St", "Newtown", cache)
        self.assertEqual((lat, lon), (None, None))
        self.assertEqual(cache, {})


class TestBuildRecordVisibility(unittest.TestCase):
    """Regression tests for the bug where a record already saved as `ready`
    stayed `ready` forever, even after the spreadsheet later marked it
    "No Longer Visible"."""

    def _ready_geocode_cache(self):
        query = geocode_query("2 McGill St, Lewisham", "Lewisham")
        return {query: {"latitude": -33.9, "longitude": 151.18}}

    def test_visible_row_with_statement_is_ready(self):
        row = make_row(O=None)
        record = build_record(row, self._ready_geocode_cache())
        self.assertEqual(record["status"], "ready")
        self.assertEqual(record["source_excerpt"], row["M"])

    def test_same_row_later_marked_no_longer_visible_is_rejected(self):
        # Same row_number (same real artwork), as if the friend updated the
        # spreadsheet's Status column between two runs of the importer.
        cache = self._ready_geocode_cache()
        first = build_record(make_row(O=None), cache)
        self.assertEqual(first["status"], "ready")

        second = build_record(make_row(O="No Longer Visible"), cache)
        self.assertEqual(second["status"], "rejected")
        self.assertIn("No Longer Visible", second["rejection_reason"])
        self.assertIsNone(second["source_excerpt"])

    def test_no_longer_visible_takes_priority_over_failed_geocode(self):
        # Empty cache -> geocode_address would hit the real network unless
        # mocked; simulate a clean "no results" answer so this test is
        # deterministic and never makes a live request.
        empty_response = Mock(status_code=200)
        empty_response.json.return_value = []
        with patch("import_street_art.requests.get", return_value=empty_response), \
             patch("import_street_art.time.sleep"):
            record = build_record(make_row(O="No Longer Visible"), {})
        self.assertEqual(record["status"], "rejected")
        self.assertIn("No Longer Visible", record["rejection_reason"])


class TestBuildRecordTitleAndStatement(unittest.TestCase):
    def test_missing_title_is_rejected_without_geocoding(self):
        cache = {}
        record = build_record(make_row(D=None), cache)
        self.assertEqual(record["status"], "rejected")
        self.assertEqual(record["rejection_reason"], "missing or placeholder artwork title")
        self.assertEqual(cache, {})  # no geocode attempted

    def test_placeholder_title_is_rejected(self):
        record = build_record(make_row(D="*Title"), {})
        self.assertEqual(record["status"], "rejected")
        self.assertEqual(record["rejection_reason"], "missing or placeholder artwork title")

    def test_missing_statement_is_limited_not_rejected(self):
        cache = self._geocode_cache_for(make_row(M=None))
        record = build_record(make_row(M=None), cache)
        self.assertEqual(record["status"], "limited")
        self.assertEqual(record["rejection_reason"], "no usable Statement in the council data")

    def test_placeholder_statement_is_limited(self):
        cache = self._geocode_cache_for(make_row(M="CARPARK"))
        record = build_record(make_row(M="CARPARK"), cache)
        self.assertEqual(record["status"], "limited")

    def test_statement_copied_verbatim_including_surrounding_whitespace(self):
        # Deliberately includes leading/trailing whitespace: usable_text()
        # may use .strip() to check there's real content, but the stored
        # excerpt must be the untouched original, padding and all.
        statement = "  Line one.\n Line two with an em dash - kept as-is.  \n"
        cache = self._geocode_cache_for(make_row(M=statement))
        record = build_record(make_row(M=statement), cache)
        self.assertEqual(record["source_excerpt"], statement)

    def _geocode_cache_for(self, row):
        query = geocode_query(row["E"], row["G"])
        return {query: {"latitude": -33.9, "longitude": 151.18}}


class TestBuildRecordFieldNotesSeparation(unittest.TestCase):
    def test_field_notes_present_and_not_a_source(self):
        cache = {geocode_query("2 McGill St, Lewisham", "Lewisham"):
                 {"latitude": -33.9, "longitude": 151.18}}
        record = build_record(make_row(O="Visible"), cache)
        self.assertEqual(record["field_notes"]["status"], "Visible")
        self.assertNotEqual(record["source_type"], record["field_notes"]["source"])
        self.assertIn("not Inner West Council data", record["field_notes"]["source"])

    def test_visited_date_photo_and_km_walked_never_reach_the_catalogue(self):
        # Personal tracking data Jaunt doesn't use - must never be written,
        # even when the spreadsheet row has real values for them.
        cache = {geocode_query("2 McGill St, Lewisham", "Lewisham"):
                 {"latitude": -33.9, "longitude": 151.18}}
        row = make_row(O="Visible", P="2025-06-07", Q="Purple Finch.HEIC", R=3.4)
        record = build_record(row, cache)
        self.assertNotIn("visited_date", record["field_notes"])
        self.assertNotIn("photo", record["field_notes"])
        self.assertNotIn("km_walked", record["field_notes"])
        # status - the one field Jaunt actually uses - is still retained.
        self.assertEqual(record["field_notes"]["status"], "Visible")


class TestGeocodeFallback(unittest.TestCase):
    def test_falls_back_to_street_address_when_full_address_fails(self):
        row = make_row(E="IGA Wall, 259 King St, Newtown", F="259 King St", G="Newtown")
        full_query = geocode_query(row["E"], row["G"])
        street_query = geocode_query(row["F"], row["G"])
        cache = {street_query: {"latitude": -33.9, "longitude": 151.18}}

        # The street_query is already cached (no request needed), but
        # full_query is not - simulate its real-world "no results" failure
        # deterministically instead of making a live Nominatim request.
        empty_response = Mock(status_code=200)
        empty_response.json.return_value = []
        with patch("import_street_art.requests.get", return_value=empty_response) as mock_get, \
             patch("import_street_art.time.sleep"):
            record = build_record(row, cache)

        mock_get.assert_called_once()  # only the uncached full_query hit "the network"
        self.assertEqual(record["latitude"], -33.9)
        self.assertNotIn(full_query, cache)


class TestApplyManualDuplicateOverrides(unittest.TestCase):
    def test_known_duplicate_rejected(self):
        street_art_id = next(iter(CROSS_SOURCE_DUPLICATES))
        kept_id = CROSS_SOURCE_DUPLICATES[street_art_id]
        records_by_id = {street_art_id: {"status": "ready", "rejection_reason": None}}
        apply_manual_duplicate_overrides(records_by_id)
        record = records_by_id[street_art_id]
        self.assertEqual(record["status"], "rejected")
        self.assertIn(kept_id, record["rejection_reason"])

    def test_non_ready_record_untouched(self):
        street_art_id = next(iter(CROSS_SOURCE_DUPLICATES))
        records_by_id = {
            street_art_id: {"status": "rejected", "rejection_reason": "no usable Statement in the council data"}
        }
        apply_manual_duplicate_overrides(records_by_id)
        self.assertEqual(
            records_by_id[street_art_id]["rejection_reason"],
            "no usable Statement in the council data",
        )

    def test_missing_record_does_not_crash(self):
        apply_manual_duplicate_overrides({})


class TestInPilotBbox(unittest.TestCase):
    def test_missing_coordinates_is_false(self):
        self.assertFalse(in_pilot_bbox({"latitude": None, "longitude": None}))

    def test_inside_bbox(self):
        self.assertTrue(in_pilot_bbox({"latitude": -33.898, "longitude": 151.179}))

    def test_outside_bbox(self):
        self.assertFalse(in_pilot_bbox({"latitude": -33.80, "longitude": 151.05}))


if __name__ == "__main__":
    unittest.main()
