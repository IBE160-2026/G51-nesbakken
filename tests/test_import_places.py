import unittest

from import_places import (
    assign_topics,
    build_osm_tag_excerpt,
    build_record,
    coordinates,
    haversine_meters,
    mark_duplicates,
    parse_wikipedia_tag,
    truncate_excerpt,
    wikidata_description_names_place,
)


class TestTopicAssignment(unittest.TestCase):
    def test_historic_tag_gives_history(self):
        self.assertEqual(assign_topics({"historic": "monument"}), ["history"])

    def test_heritage_tag_gives_history(self):
        self.assertEqual(assign_topics({"heritage": "2"}), ["history"])

    def test_church_gives_architecture_and_history(self):
        self.assertEqual(
            assign_topics({"building": "church"}), ["architecture", "history"]
        )

    def test_architect_tag_gives_architecture(self):
        self.assertEqual(assign_topics({"architect": "Jane Smith"}), ["architecture"])

    def test_artwork_tourism_gives_public_art(self):
        self.assertEqual(assign_topics({"tourism": "artwork"}), ["public_art"])

    def test_artwork_type_gives_public_art(self):
        self.assertEqual(assign_topics({"artwork_type": "mural"}), ["public_art"])

    def test_multiple_matching_tags_give_multiple_topics(self):
        self.assertEqual(
            assign_topics({"historic": "yes", "tourism": "artwork"}),
            ["history", "public_art"],
        )

    def test_no_matching_tags_gives_no_topics(self):
        self.assertEqual(assign_topics({"shop": "bakery"}), [])


class TestCoordinates(unittest.TestCase):
    def test_node_uses_lat_lon_directly(self):
        element = {"type": "node", "id": 1, "lat": -33.9, "lon": 151.18}
        self.assertEqual(coordinates(element), (-33.9, 151.18))

    def test_way_uses_center(self):
        element = {"type": "way", "id": 2, "center": {"lat": -33.9, "lon": 151.18}}
        self.assertEqual(coordinates(element), (-33.9, 151.18))

    def test_missing_coordinates_returns_none(self):
        element = {"type": "way", "id": 3}
        self.assertEqual(coordinates(element), (None, None))


class TestWikipediaTagParsing(unittest.TestCase):
    def test_english_prefix(self):
        self.assertEqual(
            parse_wikipedia_tag("en:Sydney Town Hall"), ("en", "Sydney Town Hall")
        )

    def test_missing_prefix_assumed_english(self):
        self.assertEqual(
            parse_wikipedia_tag("Sydney Town Hall"), ("en", "Sydney Town Hall")
        )

    def test_non_english_prefix_preserved(self):
        self.assertEqual(
            parse_wikipedia_tag("de:Rathaus Sydney"), ("de", "Rathaus Sydney")
        )


class TestExcerptTruncation(unittest.TestCase):
    def test_short_text_untouched(self):
        self.assertEqual(truncate_excerpt("Short text."), "Short text.")

    def test_long_text_cuts_at_sentence_boundary(self):
        text = "First sentence. Second sentence. " + "x" * 500
        result = truncate_excerpt(text, max_length=40)
        self.assertTrue(result.endswith("."))
        self.assertNotIn("x", result)


class TestBuildRecordCaching(unittest.TestCase):
    def test_ready_record_is_reused_without_rebuilding(self):
        element = {"type": "node", "id": 1, "tags": {"name": "Old Name"}}
        cached = {"id": "node/1", "name": "Cached Name", "status": "ready"}
        result = build_record(element, {"node/1": cached})
        self.assertIs(result, cached)

    def test_duplicate_marked_record_is_reused_without_rebuilding(self):
        element = {"type": "node", "id": 1, "tags": {"name": "Old Name"}}
        cached = {
            "id": "node/1",
            "name": "Old Name",
            "status": "rejected",
            "rejection_reason": "duplicate of node/2",
        }
        result = build_record(element, {"node/1": cached})
        self.assertIs(result, cached)

    def test_limited_record_is_retried_not_reused(self):
        # No wikipedia tag, so this never touches the network - it just
        # confirms build_record rebuilds from the element instead of
        # returning the stale cached "limited" record untouched.
        element = {
            "type": "node", "id": 1, "lat": -33.9, "lon": 151.18,
            "tags": {"name": "New Name", "historic": "yes"},
        }
        cached = {
            "id": "node/1", "name": "Old Name", "status": "limited",
            "rejection_reason": "no usable Wikipedia source found",
        }
        result = build_record(element, {"node/1": cached})
        self.assertIsNot(result, cached)
        self.assertEqual(result["name"], "New Name")

    def test_missing_name_is_rejected(self):
        element = {"type": "node", "id": 1, "tags": {"historic": "yes"}, "lat": -33.9, "lon": 151.18}
        result = build_record(element, {})
        self.assertEqual(result["status"], "rejected")

    def test_missing_coordinates_is_rejected(self):
        element = {"type": "way", "id": 1, "tags": {"name": "X", "historic": "yes"}}
        result = build_record(element, {})
        self.assertEqual(result["status"], "rejected")

    def test_no_wikipedia_tag_is_limited(self):
        element = {
            "type": "node", "id": 1, "lat": -33.9, "lon": 151.18,
            "tags": {"name": "X", "historic": "yes"},
        }
        result = build_record(element, {})
        self.assertEqual(result["status"], "limited")

    def test_non_english_wikipedia_tag_is_limited_with_reason(self):
        element = {
            "type": "node", "id": 1, "lat": -33.9, "lon": 151.18,
            "tags": {"name": "X", "historic": "yes", "wikipedia": "de:Something"},
        }
        result = build_record(element, {})
        self.assertEqual(result["status"], "limited")
        self.assertIn("de", result["rejection_reason"])


class TestOsmTagExcerpt(unittest.TestCase):
    def test_no_descriptive_tags_returns_none(self):
        self.assertIsNone(build_osm_tag_excerpt({}, "node/1"))

    def test_artist_and_start_date(self):
        result = build_osm_tag_excerpt(
            {"artist_name": "Jane Doe", "start_date": "2019"}, "node/1"
        )
        self.assertEqual(result["source_type"], "osm_tags")
        self.assertIn("Jane Doe", result["source_excerpt"])
        self.assertIn("2019", result["source_excerpt"])
        self.assertEqual(result["source_url"], "https://www.openstreetmap.org/node/1")

    def test_artist_only(self):
        result = build_osm_tag_excerpt({"artist_name": "Jane Doe"}, "node/1")
        self.assertIn("Jane Doe", result["source_excerpt"])

    def test_inscription_only(self):
        result = build_osm_tag_excerpt({"inscription": "Lest we forget"}, "node/1")
        self.assertIn("Lest we forget", result["source_excerpt"])

    def test_subject_only(self):
        result = build_osm_tag_excerpt({"subject": "local history"}, "node/1")
        self.assertIn("local history", result["source_excerpt"])


class TestBuildRecordEnrichmentPriority(unittest.TestCase):
    def test_osm_tags_used_when_no_wikipedia_or_wikidata_tag(self):
        element = {
            "type": "node", "id": 1, "lat": -33.9, "lon": 151.18,
            "tags": {"name": "Some Mural", "tourism": "artwork", "artist_name": "Jane Doe"},
        }
        result = build_record(element, {})
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["source_type"], "osm_tags")

    def test_still_limited_with_no_source_at_all(self):
        element = {
            "type": "node", "id": 1, "lat": -33.9, "lon": 151.18,
            "tags": {"name": "Plain Mural", "tourism": "artwork"},
        }
        result = build_record(element, {})
        self.assertEqual(result["status"], "limited")
        self.assertIsNone(result["source_type"])


class TestDuplicateDetection(unittest.TestCase):
    def test_haversine_zero_distance_for_same_point(self):
        self.assertAlmostEqual(haversine_meters(-33.9, 151.18, -33.9, 151.18), 0.0)

    def test_nearby_same_name_records_marked_duplicate(self):
        records = [
            {"id": "way/1", "name": "Test Monument", "latitude": -33.9000,
             "longitude": 151.1800, "status": "ready", "rejection_reason": None},
            {"id": "node/2", "name": "Test Monument", "latitude": -33.9001,
             "longitude": 151.1801, "status": "limited", "rejection_reason": None},
        ]
        mark_duplicates(records)
        statuses = {r["id"]: r["status"] for r in records}
        self.assertEqual(statuses["way/1"], "ready")
        self.assertEqual(statuses["node/2"], "rejected")

    def test_distant_same_name_records_not_marked_duplicate(self):
        records = [
            {"id": "way/1", "name": "Test Mural", "latitude": -33.900,
             "longitude": 151.180, "status": "ready", "rejection_reason": None},
            {"id": "node/2", "name": "Test Mural", "latitude": -33.950,
             "longitude": 151.230, "status": "limited", "rejection_reason": None},
        ]
        mark_duplicates(records)
        statuses = {r["id"]: r["status"] for r in records}
        self.assertEqual(statuses["way/1"], "ready")
        self.assertEqual(statuses["node/2"], "limited")

    def test_different_names_not_marked_duplicate(self):
        records = [
            {"id": "way/1", "name": "Alpha", "latitude": -33.900,
             "longitude": 151.180, "status": "ready", "rejection_reason": None},
            {"id": "node/2", "name": "Beta", "latitude": -33.9001,
             "longitude": 151.1801, "status": "limited", "rejection_reason": None},
        ]
        mark_duplicates(records)
        statuses = {r["id"]: r["status"] for r in records}
        self.assertEqual(statuses["way/1"], "ready")
        self.assertEqual(statuses["node/2"], "limited")


class TestWikidataDescriptionNamesPlace(unittest.TestCase):
    def test_specific_word_match_passes(self):
        self.assertTrue(
            wikidata_description_names_place("church in Newtown, New South Wales", "Newtown Baptist Church")
        )

    def test_generic_category_only_fails(self):
        self.assertFalse(
            wikidata_description_names_place(
                "historic national heritage site in Sydney NSW", "First Government House"
            )
        )

    def test_shared_generic_words_dont_count_as_a_match(self):
        """'war' and 'memorial' appear in both the name and the excerpt,
        but neither is specific to this particular memorial."""
        self.assertFalse(
            wikidata_description_names_place(
                "war memorial in Martin Place, Sydney", "The Cenotaph War Memorial"
            )
        )

    def test_empty_excerpt_or_name_fails(self):
        self.assertFalse(wikidata_description_names_place("", "Some Place"))
        self.assertFalse(wikidata_description_names_place("a description", ""))
        self.assertFalse(wikidata_description_names_place(None, "Some Place"))


if __name__ == "__main__":
    unittest.main()
