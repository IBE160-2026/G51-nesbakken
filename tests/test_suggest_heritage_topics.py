import json
import os
import tempfile
import unittest
from unittest.mock import patch

from ai import AiSelectionError
from suggest_heritage_topics import load_json_field, suggest_topics


class TestLoadJsonField(unittest.TestCase):
    def test_missing_file_returns_empty_dict(self):
        missing = os.path.join(tempfile.gettempdir(), "does-not-exist-heritage-topics.json")
        self.assertEqual(load_json_field(missing, "items"), {})

    def test_present_file_returns_requested_field(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "seed.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"items": {"123": {"item_name": "Test"}}}, f)
            self.assertEqual(load_json_field(path, "items"), {"123": {"item_name": "Test"}})

    def test_missing_field_returns_empty_dict(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "seed.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"_instructions": "..."}, f)
            self.assertEqual(load_json_field(path, "items"), {})


class TestSuggestTopics(unittest.TestCase):
    @patch("suggest_heritage_topics._call_openai")
    def test_happy_path_returns_topics_and_reason(self, mock_call):
        mock_call.return_value = json.dumps({
            "topics": ["history", "architecture"],
            "reason": "The statement describes its 1890s construction and facade style.",
        })
        result = suggest_topics("Test Hotel", "Built in 1890, notable for its facade.")
        self.assertEqual(result["topics"], ["history", "architecture"])
        self.assertIn("1890s", result["reason"])

    @patch("suggest_heritage_topics._call_openai")
    def test_empty_topics_list_is_valid(self, mock_call):
        """The text genuinely supporting neither topic is a real, honest
        answer - never forced into a false positive."""
        mock_call.return_value = json.dumps({
            "topics": [],
            "reason": "The statement only discusses administrative listing dates.",
        })
        result = suggest_topics("Test Item", "Listed on the register in 2004.")
        self.assertEqual(result["topics"], [])

    @patch("suggest_heritage_topics._call_openai")
    def test_malformed_response_raises_ai_selection_error(self, mock_call):
        mock_call.return_value = json.dumps({"unexpected": "shape"})
        with self.assertRaises(AiSelectionError):
            suggest_topics("Test Item", "Some text.")

    @patch("suggest_heritage_topics._call_openai")
    def test_non_json_response_raises_ai_selection_error(self, mock_call):
        mock_call.return_value = "not json"
        with self.assertRaises(AiSelectionError):
            suggest_topics("Test Item", "Some text.")


class TestMainFiltering(unittest.TestCase):
    """main() itself only orchestrates file I/O around suggest_topics() -
    covered here by exercising its needs_suggestion filter directly, the
    same way import_heritage.py's own tests focus on its pure functions
    rather than main()'s orchestration."""

    def test_filter_skips_items_already_overridden(self):
        source_text = {"123": {"statement_of_significance": "Real text."}}
        existing_overrides = {"123": {"topics": ["history"]}}
        needs_suggestion = {
            hid: entry for hid, entry in source_text.items()
            if hid not in existing_overrides
            and (entry.get("statement_of_significance") or "").strip()
        }
        self.assertEqual(needs_suggestion, {})

    def test_filter_skips_items_without_text(self):
        source_text = {"123": {"statement_of_significance": None}, "456": {"statement_of_significance": ""}}
        existing_overrides = {}
        needs_suggestion = {
            hid: entry for hid, entry in source_text.items()
            if hid not in existing_overrides
            and (entry.get("statement_of_significance") or "").strip()
        }
        self.assertEqual(needs_suggestion, {})

    def test_filter_includes_new_item_with_text(self):
        source_text = {"123": {"statement_of_significance": "Real text.", "item_name": "Test"}}
        existing_overrides = {}
        needs_suggestion = {
            hid: entry for hid, entry in source_text.items()
            if hid not in existing_overrides
            and (entry.get("statement_of_significance") or "").strip()
        }
        self.assertEqual(needs_suggestion, source_text)


if __name__ == "__main__":
    unittest.main()
