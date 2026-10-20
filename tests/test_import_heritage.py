import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import import_heritage
from import_heritage import (
    build_local_records,
    build_record,
    build_state_records,
    load_seed,
    load_topic_overrides,
)


class TestBuildRecord(unittest.TestCase):
    def test_ready_when_coordinates_and_statement_present(self):
        seed_entry = {"statement_of_significance": "A real, verbatim statement."}
        record = build_record(123, "Test Item", -33.9, 151.18, "State", seed_entry)
        self.assertEqual(record["status"], "ready")
        self.assertEqual(record["source_excerpt"], "A real, verbatim statement.")
        self.assertEqual(record["source_type"], "nsw_state_heritage_inventory")
        self.assertEqual(record["source_title"], "Test Item")
        self.assertIn("itemId=123", record["source_url"])
        self.assertEqual(record["id"], "heritage/123")
        # Story 1.2: no default "heritage" tag at all - topics come only
        # from an explicit topic_override, never from a fallback here.
        self.assertEqual(record["topics"], [])
        self.assertIsNone(record["rejection_reason"])

    def test_topic_override_applied_verbatim(self):
        seed_entry = {"statement_of_significance": "A real, verbatim statement."}
        record = build_record(
            123, "Test Item", -33.9, 151.18, "State", seed_entry,
            topic_override={"topics": ["history", "architecture"]},
        )
        self.assertEqual(record["topics"], ["history", "architecture"])

    def test_missing_topic_override_defaults_to_empty_never_heritage(self):
        seed_entry = {"statement_of_significance": "A real, verbatim statement."}
        record = build_record(123, "Test Item", -33.9, 151.18, "State", seed_entry, topic_override=None)
        self.assertEqual(record["topics"], [])
        self.assertNotIn("heritage", record["topics"])

    def test_limited_when_statement_missing(self):
        record = build_record(123, "Test Item", -33.9, 151.18, "Local", None)
        self.assertEqual(record["status"], "limited")
        self.assertIsNone(record["source_excerpt"])
        self.assertIsNone(record["source_url"])
        self.assertIn("Statement of Significance", record["rejection_reason"])

    def test_limited_when_seed_entry_has_null_statement(self):
        seed_entry = {"statement_of_significance": None}
        record = build_record(123, "Test Item", -33.9, 151.18, "Local", seed_entry)
        self.assertEqual(record["status"], "limited")

    def test_rejected_when_coordinates_missing_even_with_statement(self):
        seed_entry = {"statement_of_significance": "Some text."}
        record = build_record(123, "Test Item", None, None, "State", seed_entry)
        self.assertEqual(record["status"], "rejected")
        self.assertEqual(record["rejection_reason"], "missing coordinates from ArcGIS")
        # Never surface a source for a place with no location, even if text exists.
        self.assertIsNone(record["source_excerpt"])

    def test_statement_never_rewritten(self):
        statement = "Line one.\nLine two - kept exactly, including this dash."
        seed_entry = {"statement_of_significance": statement}
        record = build_record(123, "Test Item", -33.9, 151.18, "State", seed_entry)
        self.assertEqual(record["source_excerpt"], statement)

    def test_significance_level_recorded(self):
        record = build_record(123, "Test Item", -33.9, 151.18, "State", None)
        self.assertEqual(record["significance_level"], "State")


class TestSourceTextValidation(unittest.TestCase):
    """A heritage record must become ready only when statement_of_significance
    is a string with at least one non-whitespace character. Stripping is for
    validation only - the stored excerpt is always the untouched original."""

    def test_whitespace_only_statement_is_limited(self):
        seed_entry = {"statement_of_significance": "   \n\t  "}
        record = build_record(123, "Test Item", -33.9, 151.18, "State", seed_entry)
        self.assertEqual(record["status"], "limited")
        self.assertIsNone(record["source_excerpt"])

    def test_empty_string_statement_is_limited(self):
        seed_entry = {"statement_of_significance": ""}
        record = build_record(123, "Test Item", -33.9, 151.18, "State", seed_entry)
        self.assertEqual(record["status"], "limited")

    def test_non_string_statement_is_limited(self):
        seed_entry = {"statement_of_significance": 12345}
        record = build_record(123, "Test Item", -33.9, 151.18, "State", seed_entry)
        self.assertEqual(record["status"], "limited")

    def test_statement_with_surrounding_whitespace_is_ready_and_stored_verbatim(self):
        statement = "  Real content with padding.  \n"
        seed_entry = {"statement_of_significance": statement}
        record = build_record(123, "Test Item", -33.9, 151.18, "State", seed_entry)
        self.assertEqual(record["status"], "ready")
        # Passed validation because of non-whitespace content, but the
        # surrounding whitespace itself must not be stripped from storage.
        self.assertEqual(record["source_excerpt"], statement)


class TestHeritageOsmCrossSourceDuplicates(unittest.TestCase):
    def test_each_approved_pair_rejects_the_osm_side(self):
        for osm_id, kept_id in import_heritage.CROSS_SOURCE_DUPLICATES.items():
            records_by_id = {
                osm_id: {"status": "ready", "rejection_reason": None},
                kept_id: {"status": "ready", "rejection_reason": None},
            }
            import_heritage.apply_manual_duplicate_overrides(records_by_id)
            record = records_by_id[osm_id]
            self.assertEqual(record["status"], "rejected")
            self.assertIn(kept_id, record["rejection_reason"])

    def test_osm_side_kept_when_replacement_is_not_ready(self):
        # Regression (Codex review, 2026-10-18): rejecting the OSM original
        # must not happen if the heritage replacement isn't actually ready
        # (e.g. its Statement of Significance hasn't been filled in yet) -
        # that would leave the place unusable from either source.
        osm_id, kept_id = next(iter(import_heritage.CROSS_SOURCE_DUPLICATES.items()))
        records_by_id = {
            osm_id: {"status": "ready", "rejection_reason": None},
            kept_id: {"status": "limited", "rejection_reason": "no seed text yet"},
        }
        import_heritage.apply_manual_duplicate_overrides(records_by_id)
        self.assertEqual(records_by_id[osm_id]["status"], "ready")

    def test_osm_side_kept_when_replacement_is_missing(self):
        osm_id = next(iter(import_heritage.CROSS_SOURCE_DUPLICATES))
        records_by_id = {osm_id: {"status": "ready", "rejection_reason": None}}
        import_heritage.apply_manual_duplicate_overrides(records_by_id)
        self.assertEqual(records_by_id[osm_id]["status"], "ready")

    def test_osm_side_is_restored_if_replacement_later_becomes_not_ready(self):
        # Regression (user-caught, 2026-10-20): a prior run rejected the OSM
        # record because the replacement was ready then. The replacement has
        # since become limited (e.g. its seed text was removed) - the OSM
        # record must come back to ready, not stay stuck rejected forever.
        osm_id, kept_id = next(iter(import_heritage.CROSS_SOURCE_DUPLICATES.items()))
        records_by_id = {
            osm_id: {
                "status": "rejected",
                "rejection_reason": f"duplicate of {kept_id} (reviewed cross-source match)",
            },
            kept_id: {"status": "limited", "rejection_reason": "no seed text yet"},
        }
        import_heritage.apply_manual_duplicate_overrides(records_by_id)
        self.assertEqual(records_by_id[osm_id]["status"], "ready")
        self.assertIsNone(records_by_id[osm_id]["rejection_reason"])

    def test_unrelated_rejection_reason_is_never_touched(self):
        # A record rejected for some other reason entirely (missing
        # coordinates, etc.) must never be "restored" by this function -
        # only a rejection this function itself applied is reversible.
        osm_id, kept_id = next(iter(import_heritage.CROSS_SOURCE_DUPLICATES.items()))
        records_by_id = {
            osm_id: {"status": "rejected", "rejection_reason": "missing coordinates"},
            kept_id: {"status": "limited", "rejection_reason": "no seed text yet"},
        }
        import_heritage.apply_manual_duplicate_overrides(records_by_id)
        self.assertEqual(records_by_id[osm_id]["status"], "rejected")
        self.assertEqual(records_by_id[osm_id]["rejection_reason"], "missing coordinates")

    def test_heritage_record_being_kept_is_never_touched(self):
        records_by_id = {
            "heritage/5045004": {"status": "ready", "rejection_reason": None},
            "way/548526874": {"status": "ready", "rejection_reason": None},
        }
        import_heritage.apply_manual_duplicate_overrides(records_by_id)
        self.assertEqual(records_by_id["heritage/5045004"]["status"], "ready")
        self.assertEqual(records_by_id["way/548526874"]["status"], "rejected")

    def test_non_ready_osm_record_untouched(self):
        records_by_id = {"way/548526874": {"status": "rejected", "rejection_reason": "some other reason"}}
        import_heritage.apply_manual_duplicate_overrides(records_by_id)
        self.assertEqual(records_by_id["way/548526874"]["rejection_reason"], "some other reason")

    def test_missing_osm_record_does_not_crash(self):
        import_heritage.apply_manual_duplicate_overrides({})


class TestBuildStateRecords(unittest.TestCase):
    """ArcGIS calls are mocked - these test the response-handling logic only,
    not live network access."""

    def test_found_state_item_becomes_a_record(self):
        fake_features = [{
            "attributes": {
                "HOITEMID": 5045479,
                "ITEMNAME": "St Stephen's Anglican Church and Cemetery",
                "Lat": -33.8946, "Long_": 151.1796,
            },
        }]
        with patch("import_heritage.query_layer", return_value=fake_features):
            records, missing = build_state_records(seed={})

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], "heritage/5045479")
        # The fake response only returned one of the approved ids - the rest
        # are correctly reported missing, since build_state_records checks
        # every approved id, not just whatever came back.
        self.assertNotIn(5045479, missing)
        self.assertEqual(missing, set(import_heritage.APPROVED_STATE_HOITEMIDS) - {5045479})

    def test_approved_id_not_returned_by_arcgis_is_reported_missing(self):
        with patch("import_heritage.query_layer", return_value=[]):
            records, missing = build_state_records(seed={})

        self.assertEqual(records, [])
        self.assertEqual(missing, set(import_heritage.APPROVED_STATE_HOITEMIDS))


class TestBuildLocalRecords(unittest.TestCase):
    def test_multi_point_item_deduplicated_by_heritage_item_id(self):
        # Same HeritageItemID appearing twice, as seen for real multi-point
        # items during research (e.g. "Brick paving").
        fake_features = [
            {"attributes": {"HeritageItemID": 2030465, "H_NAME": "Sly Fox Hotel"},
             "geometry": {"x": 151.1713, "y": -33.899}},
            {"attributes": {"HeritageItemID": 2030465, "H_NAME": "Sly Fox Hotel"},
             "geometry": {"x": 151.1714, "y": -33.8991}},
        ]
        with patch("import_heritage.query_layer", return_value=fake_features):
            records, missing = build_local_records(seed={})

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["latitude"], -33.899)  # the first point kept

    def test_missing_local_id_reported(self):
        with patch("import_heritage.query_layer", return_value=[]):
            records, missing = build_local_records(seed={})

        self.assertEqual(missing, set(import_heritage.APPROVED_LOCAL_HERITAGE_ITEM_IDS))


class TestQueryConstruction(unittest.TestCase):
    """Confirms State queries by HOITEMID against Layer 5 and Local queries
    by HeritageItemID against Layer 4 with the researched filters - mocking
    requests.get itself (not query_layer), so this actually exercises the
    real where-clause construction."""

    @staticmethod
    def _empty_response():
        response = Mock(status_code=200)
        response.json.return_value = {"features": []}
        response.raise_for_status = Mock()
        return response

    def test_state_query_uses_hoitemid_against_layer_5(self):
        with patch("import_heritage.requests.get", return_value=self._empty_response()) as mock_get:
            build_state_records(seed={})

        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/5/query"))
        where = kwargs["params"]["where"]
        self.assertTrue(where.startswith("HOITEMID IN ("))
        for hid in import_heritage.APPROVED_STATE_HOITEMIDS:
            self.assertIn(str(hid), where)

    def test_local_query_uses_heritage_item_id_against_layer_4_with_filters(self):
        with patch("import_heritage.requests.get", return_value=self._empty_response()) as mock_get:
            build_local_records(seed={})

        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/4/query"))
        where = kwargs["params"]["where"]
        self.assertTrue(where.startswith("HeritageItemID IN ("))
        self.assertIn("LAY_CLASS='Item - General'", where)
        self.assertIn("SIG='Local'", where)
        for hid in import_heritage.APPROVED_LOCAL_HERITAGE_ITEM_IDS:
            self.assertIn(str(hid), where)


class TestMainAbortsOnMissingApprovedIds(unittest.TestCase):
    """Simple, direct test of main()'s collaborators: if ArcGIS doesn't
    return every approved id, main() must abort before save_records() is
    ever called - never persist a partial import as though it succeeded."""

    def test_missing_id_aborts_without_saving(self):
        with patch("import_heritage.load_seed", return_value={}), \
             patch("import_heritage.load_topic_overrides", return_value={}), \
             patch("import_heritage.build_state_records", return_value=([], {5045479})), \
             patch("import_heritage.build_local_records", return_value=([], set())), \
             patch("import_heritage.load_existing", return_value={}), \
             patch("import_heritage.save_records") as mock_save, \
             patch("import_heritage.mark_duplicates") as mock_dedup:
            with self.assertRaises(SystemExit):
                import_heritage.main()

        mock_save.assert_not_called()
        mock_dedup.assert_not_called()

    def test_no_missing_ids_proceeds_to_save(self):
        fake_record = {"id": "heritage/1", "status": "ready", "rejection_reason": None}
        with patch("import_heritage.load_seed", return_value={}), \
             patch("import_heritage.load_topic_overrides", return_value={}), \
             patch("import_heritage.build_state_records", return_value=([fake_record], set())), \
             patch("import_heritage.build_local_records", return_value=([], set())), \
             patch("import_heritage.load_existing", return_value={}), \
             patch("import_heritage.save_records") as mock_save, \
             patch("import_heritage.mark_duplicates"):
            import_heritage.main()

        mock_save.assert_called_once()


class TestLoadSeedAndEndToEnd(unittest.TestCase):
    """Regression coverage for a real report: all 29 seed entries were
    manually populated in the editor, but a rerun still showed every item as
    `limited` with no statement found. Debugging traced this to the file on
    disk still holding the original all-null template (an unsaved-editor
    issue, not a reading bug) - confirmed by checking the raw file content,
    not by assuming the code was at fault. These tests prove load_seed() and
    build_record() correctly turn a *genuinely* populated seed file into a
    ready record, so a real future regression in the reading path (a wrong
    key name, wrong nesting, an encoding problem) would be caught here
    instead of looking identical to "forgot to save the file"."""

    def test_load_seed_reads_a_real_populated_file(self):
        statement = "This building is of historical significance."
        with tempfile.TemporaryDirectory() as tmp_dir:
            seed_path = os.path.join(tmp_dir, "seed.json")
            with open(seed_path, "w", encoding="utf-8") as f:
                json.dump({
                    "items": {
                        "5045479": {
                            "item_name": "St Stephen's Anglican Church and Cemetery",
                            "statement_of_significance": statement,
                            "source_field": "significance",
                        }
                    }
                }, f)
            seed = load_seed(seed_path)

        self.assertEqual(seed["5045479"]["statement_of_significance"], statement)

    def test_missing_seed_file_returns_empty_dict_not_an_error(self):
        seed = load_seed(os.path.join(tempfile.gettempdir(), "does-not-exist-heritage-seed.json"))
        self.assertEqual(seed, {})

    def test_populated_seed_entry_produces_a_ready_record_end_to_end(self):
        statement = "This building is of historical significance. (Lucas 1975)"
        with tempfile.TemporaryDirectory() as tmp_dir:
            seed_path = os.path.join(tmp_dir, "seed.json")
            with open(seed_path, "w", encoding="utf-8") as f:
                json.dump({"items": {"5045479": {"statement_of_significance": statement}}}, f)
            seed = load_seed(seed_path)

        record = build_record(
            5045479, "St Stephen's Anglican Church and Cemetery", -33.8946, 151.1796,
            "State", seed.get("5045479"),
        )
        self.assertEqual(record["status"], "ready")
        self.assertEqual(record["source_excerpt"], statement)


class TestLoadTopicOverrides(unittest.TestCase):
    """Story 1.2: data/heritage_topic_overrides.json is the maintained
    override a routine rerun of this importer must keep reading - mirrors
    load_seed()'s own missing-file/real-file test coverage above."""

    def test_missing_override_file_returns_empty_dict_not_an_error(self):
        overrides = load_topic_overrides(
            os.path.join(tempfile.gettempdir(), "does-not-exist-topic-overrides.json")
        )
        self.assertEqual(overrides, {})

    def test_reads_a_real_populated_override_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "overrides.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"overrides": {"5045479": {"topics": ["architecture"]}}}, f)
            overrides = load_topic_overrides(path)

        self.assertEqual(overrides["5045479"]["topics"], ["architecture"])

    def test_the_real_shipped_override_file_covers_every_seed_id_with_no_heritage_tag(self):
        """Regression guard for this story's own acceptance criteria: every
        id in the real seed file has a real override entry, and none of
        them assign the retired 'heritage' topic."""
        seed = load_seed()
        overrides = load_topic_overrides()

        self.assertEqual(set(overrides.keys()), set(seed.keys()))
        for heritage_id, entry in overrides.items():
            self.assertNotIn("heritage", entry["topics"])

        history_count = sum(1 for e in overrides.values() if "history" in e["topics"])
        architecture_count = sum(1 for e in overrides.values() if "architecture" in e["topics"])
        self.assertGreaterEqual(history_count, 2)
        self.assertGreaterEqual(architecture_count, 2)


if __name__ == "__main__":
    unittest.main()
