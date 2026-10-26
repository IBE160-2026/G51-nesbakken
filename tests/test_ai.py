import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

import ai
from ai import (
    SYSTEM_PROMPT,
    AiFatalError,
    AiSelectionError,
    build_prompt,
    check_grounding,
    check_grounding_semantic,
    generate_stop_content,
    generate_walk_summary,
    get_contextual_sources,
    load_contextual_sources,
    select_stops,
)

SAMPLE_OPTIONS = [
    {
        "option_key": "option_1",
        "stops": [{"id": "node/1", "name": "Place One", "topics": ["public_art"], "source_excerpt": "By Someone."}],
        "total_minutes": 35.0,
        "budget_usage_ratio": 0.583,
    },
    {
        "option_key": "option_2",
        "stops": [
            {"id": "node/1", "name": "Place One", "topics": ["public_art"], "source_excerpt": "By Someone."},
            {"id": "node/2", "name": "Place Two", "topics": ["history"], "source_excerpt": "Built in 1900."},
        ],
        "total_minutes": 45.0,
        "budget_usage_ratio": 0.75,
    },
]


def make_openai_response(content_obj):
    return {"choices": [{"message": {"content": json.dumps(content_obj)}}]}


def make_mock_response(json_body):
    mock_response = MagicMock()
    mock_response.json.return_value = json_body
    mock_response.raise_for_status = MagicMock()
    return mock_response


def make_http_error_response(status_code, error_type=None, message=None):
    """A response whose raise_for_status() raises an HTTPError carrying a
    real .response (status code + optional OpenAI-style error body), the
    same shape requests actually produces - not a bare HTTPError string."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    if error_type or message:
        mock_response.json.return_value = {"error": {"type": error_type, "message": message}}
    else:
        mock_response.json.side_effect = ValueError("no body")
    http_error = requests.exceptions.HTTPError(f"{status_code} error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    return mock_response


class TestBuildPrompt(unittest.TestCase):
    def test_continuous_preference_and_soft_evidence_guidance(self):
        for preference in (0, 0.5, 1, 0.37):
            prompt = build_prompt(SAMPLE_OPTIONS, "public_art", 60, "retry feedback", preference)
            details = json.JSONDecoder().raw_decode(prompt.split("\n\n", 1)[1])[0]
            self.assertEqual(details["preference"], preference)
            self.assertIn("retry feedback", prompt)
            self.assertIn("0 for well-known landmarks, 0.5 for Balanced", prompt)
            self.assertIn("1 for hidden gems", prompt)
            self.assertIn("source_type) is not popularity", prompt)
            self.assertIn("lesser-known does not mean low quality", prompt)
            self.assertIn("only one kind of suitable stop", prompt)
            self.assertIn("preference alone must not require rejecting an otherwise suitable offered walk", prompt)
            self.assertIn("do not invent fame, obscurity or stories", prompt)

    def test_includes_option_keys_topic_and_time(self):
        prompt = build_prompt(SAMPLE_OPTIONS, "public_art", 60)
        self.assertIn("option_1", prompt)
        self.assertIn("option_2", prompt)
        self.assertIn("public_art", prompt)
        self.assertIn("60", prompt)

    def test_includes_feedback_when_given(self):
        prompt = build_prompt(SAMPLE_OPTIONS, "public_art", 60, feedback="try a different option")
        self.assertIn("try a different option", prompt)

    def test_omits_feedback_text_when_none(self):
        prompt = build_prompt(SAMPLE_OPTIONS, "public_art", 60, feedback=None)
        self.assertNotIn("could not be used", prompt)

    def test_no_raw_matrix_is_sent(self):
        # This design gives AI no routing arithmetic to do - the options
        # menu carries pre-computed totals only, never a duration matrix.
        prompt = build_prompt(SAMPLE_OPTIONS, "public_art", 60)
        self.assertNotIn("walking_durations_seconds", prompt)


class TestSystemPromptContent(unittest.TestCase):
    """AI is told every option is already feasible and should not attempt
    its own arithmetic - see "Redesign after live testing" in
    docs/ai-development-log.md."""

    def test_states_options_are_already_checked(self):
        self.assertIn("already been checked by Python", SYSTEM_PROMPT)

    def test_tells_ai_not_to_recompute_feasibility(self):
        self.assertIn("should not try to", SYSTEM_PROMPT)
        self.assertIn("recompute", SYSTEM_PROMPT)

    def test_restricts_choice_to_listed_option_keys(self):
        self.assertIn("option_key", SYSTEM_PROMPT)
        self.assertIn("never invent one", SYSTEM_PROMPT)

    def test_states_budget_usage_as_a_secondary_preference(self):
        self.assertIn("budget_usage_ratio", SYSTEM_PROMPT)
        self.assertIn("relevance, interest and preference come first", SYSTEM_PROMPT)


class TestSelectStops(unittest.TestCase):
    def setUp(self):
        get_key_patcher = patch("ai.get_api_key", return_value="test-api-key")
        get_model_patcher = patch("ai.get_model", return_value="test-model")
        self.mock_get_api_key = get_key_patcher.start()
        self.mock_get_model = get_model_patcher.start()
        self.addCleanup(get_key_patcher.stop)
        self.addCleanup(get_model_patcher.stop)

    def test_returns_selected_option_from_valid_response(self):
        mock_response = make_mock_response(make_openai_response(
            {"selected_option": "option_2", "none_suitable_reason": ""}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = select_stops(SAMPLE_OPTIONS, "public_art", 60)
        self.assertEqual(result, {"selected_option": "option_2", "none_suitable_reason": ""})

    def test_sends_authorization_header_and_model_and_schema(self):
        mock_response = make_mock_response(make_openai_response(
            {"selected_option": "option_1", "none_suitable_reason": ""}
        ))
        with patch("ai.requests.post", return_value=mock_response) as mock_post:
            select_stops(SAMPLE_OPTIONS, "public_art", 60)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-api-key")
        self.assertEqual(kwargs["json"]["model"], "test-model")
        self.assertEqual(kwargs["json"]["response_format"]["type"], "json_schema")
        self.assertEqual(
            set(kwargs["json"]["response_format"]["json_schema"]["schema"]["required"]),
            {"selected_option", "none_suitable_reason"},
        )

    def test_feedback_reaches_the_request_body(self):
        mock_response = make_mock_response(make_openai_response(
            {"selected_option": "option_1", "none_suitable_reason": ""}
        ))
        with patch("ai.requests.post", return_value=mock_response) as mock_post:
            select_stops(SAMPLE_OPTIONS, "public_art", 60, feedback="option_9 was not offered")
        _, kwargs = mock_post.call_args
        user_message = kwargs["json"]["messages"][1]["content"]
        self.assertIn("option_9 was not offered", user_message)

    def test_malformed_json_content_raises_ai_selection_error(self):
        mock_response = make_mock_response({"choices": [{"message": {"content": "not json"}}]})
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_missing_selected_option_key_raises_ai_selection_error(self):
        mock_response = make_mock_response(make_openai_response({"wrong_key": "option_1"}))
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_non_string_selected_option_raises_ai_selection_error(self):
        mock_response = make_mock_response(make_openai_response(
            {"selected_option": 123, "none_suitable_reason": ""}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_non_string_none_suitable_reason_raises_ai_selection_error(self):
        mock_response = make_mock_response(make_openai_response(
            {"selected_option": "option_1", "none_suitable_reason": 123}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_none_suitable_outcome_is_returned_with_its_reason(self):
        mock_response = make_mock_response(make_openai_response(
            {"selected_option": "none_suitable", "none_suitable_reason": "no option fit the topic"}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = select_stops(SAMPLE_OPTIONS, "public_art", 60)
        self.assertEqual(result["selected_option"], "none_suitable")
        self.assertEqual(result["none_suitable_reason"], "no option fit the topic")

    def test_unexpected_response_shape_raises_ai_selection_error(self):
        mock_response = make_mock_response({"unexpected": "shape"})
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_null_choices_raises_ai_selection_error_not_type_error(self):
        # Regression: body["choices"][0] raised an uncaught TypeError when
        # "choices" was present but null, bypassing the retry/fallback path
        # in planner.py that only expects AiSelectionError/AiFatalError.
        mock_response = make_mock_response({"choices": None})
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_malformed_json_body_on_a_200_raises_ai_selection_error(self):
        # Regression (Codex review, 2026-10-18): a successful HTTP status
        # with a body that isn't valid JSON raised an uncaught
        # json.JSONDecodeError from response.json() - that call sat outside
        # the guarded try/except, so it bypassed AiSelectionError/retry
        # entirely. Reproduced without network access.
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = ValueError("not valid JSON")
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_http_failure_raises_ai_selection_error_not_swallowed(self):
        with patch("ai.requests.post", side_effect=requests.exceptions.ConnectionError("boom")):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_http_error_status_raises_ai_selection_error(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)


class TestNonRetryableFailures(unittest.TestCase):
    """401/403/quota-exhausted-429 responses can never succeed by retrying
    an unmodified request - planner.py needs to be able to tell these apart
    from a transient failure. See docs/architecture-plan.md."""

    def setUp(self):
        get_key_patcher = patch("ai.get_api_key", return_value="test-api-key")
        get_model_patcher = patch("ai.get_model", return_value="test-model")
        get_key_patcher.start()
        get_model_patcher.start()
        self.addCleanup(get_key_patcher.stop)
        self.addCleanup(get_model_patcher.stop)

    def test_401_raises_ai_fatal_error(self):
        mock_response = make_http_error_response(401, "invalid_api_key", "Incorrect API key provided")
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiFatalError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_403_raises_ai_fatal_error(self):
        mock_response = make_http_error_response(403, "permission_denied", "No access to this model")
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiFatalError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_429_with_quota_error_type_raises_ai_fatal_error(self):
        mock_response = make_http_error_response(429, "insufficient_quota", "You exceeded your current quota")
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiFatalError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_fatal_error_message_preserves_the_real_reason(self):
        mock_response = make_http_error_response(401, "invalid_api_key", "Incorrect API key provided")
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiFatalError) as cm:
                select_stops(SAMPLE_OPTIONS, "public_art", 60)
        self.assertIn("Incorrect API key provided", str(cm.exception))

    def test_429_without_quota_indication_stays_retryable(self):
        mock_response = make_http_error_response(429, "rate_limit_exceeded", "Rate limit reached")
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError) as cm:
                select_stops(SAMPLE_OPTIONS, "public_art", 60)
        self.assertNotIsInstance(cm.exception, AiFatalError)

    def test_500_stays_retryable_not_fatal(self):
        mock_response = make_http_error_response(500)
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError) as cm:
                select_stops(SAMPLE_OPTIONS, "public_art", 60)
        self.assertNotIsInstance(cm.exception, AiFatalError)


class TestMissingConfig(unittest.TestCase):
    def test_missing_api_key_raises_runtime_error(self):
        with patch("ai.load_env"), patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

    def test_missing_model_raises_runtime_error(self):
        with patch("ai.load_env"), patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            with self.assertRaises(RuntimeError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)


# =========================================================================
# STORY 1.3: content generation, grounding, Contextual Sources
# =========================================================================

SAMPLE_STOP_RICH = {
    "id": "heritage/5012123",
    "name": "Newtown Railway Station group",
    "source_type": "nsw_state_heritage_inventory",
    "source_title": "Newtown Railway Station group",
    "source_url": "https://example.org/5012123",
    "source_excerpt": "Newtown Railway Station is of state significance, representing three phases of NSW railway development, including the 1892 overhead booking office.",
    "topics": ["history", "architecture"],
}
SAMPLE_STOP_THIN = {
    "id": "node/5301587126",
    "name": "The Trail",
    "source_type": "osm_tags",
    "source_title": None,
    "source_url": "https://example.org/node/5301587126",
    "source_excerpt": "By Michael Snape.",
    "topics": ["public_art"],
}


class TestLoadAndGetContextualSources(unittest.TestCase):
    def test_missing_file_returns_empty_list_not_an_error(self):
        sources = load_contextual_sources(os.path.join(tempfile.gettempdir(), "does-not-exist.json"))
        self.assertEqual(sources, [])

    def test_reads_a_real_populated_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "sources.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"sources": [{"id": "x", "topics": ["history"], "source_type": "wikipedia",
                                         "source_title": "X", "source_url": "https://x", "text": "Some text."}]}, f)
            sources = load_contextual_sources(path)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["id"], "x")

    def test_filters_by_requested_topic(self):
        fake_sources = [
            {"id": "a", "topics": ["history"], "source_type": "t", "source_title": "A", "source_url": "u", "text": "A text"},
            {"id": "b", "topics": ["architecture"], "source_type": "t", "source_title": "B", "source_url": "u", "text": "B text"},
        ]
        with patch("ai.load_contextual_sources", return_value=fake_sources):
            result = get_contextual_sources(SAMPLE_STOP_RICH, "history")
        self.assertEqual([s["id"] for s in result], ["a"])

    def test_no_match_returns_empty_list_not_an_error(self):
        with patch("ai.load_contextual_sources", return_value=[]):
            result = get_contextual_sources(SAMPLE_STOP_THIN, "public_art")
        self.assertEqual(result, [])

    def test_returned_entries_have_the_fixed_contract_fields(self):
        fake_sources = [{"id": "a", "topics": ["history"], "source_type": "wikipedia",
                          "source_title": "A", "source_url": "https://a", "text": "A text"}]
        with patch("ai.load_contextual_sources", return_value=fake_sources):
            result = get_contextual_sources(SAMPLE_STOP_RICH, "history")
        entry = result[0]
        for key in ("source_type", "source_title", "source_url", "text"):
            self.assertIn(key, entry)


class TestCheckGroundingRuleBased(unittest.TestCase):
    """The cheap pre-filter - validated against real generated content
    during this story's prototyping (see the implementation spec's Design
    Notes), and pinned here as regression tests."""

    def test_rich_grounded_content_passes(self):
        content = ("Newtown Railway Station reflects three phases of NSW railway development, "
                   "including the 1892 overhead booking office.")
        self.assertTrue(check_grounding(content, [SAMPLE_STOP_RICH["source_excerpt"]]))

    def test_thin_excerpt_unembellished_passes(self):
        self.assertTrue(check_grounding("By Michael Snape.", ["By Michael Snape."]))

    def test_fabricated_date_fails(self):
        content = "Newtown Railway Station was designed in 1887 by architect Walter Liberty Vernon."
        self.assertFalse(check_grounding(content, [SAMPLE_STOP_RICH["source_excerpt"]]))

    def test_fabricated_multiword_name_fails(self):
        content = "This piece was created by Jane Smith Thompson in her studio."
        self.assertFalse(check_grounding(content, ["By Michael Snape."]))

    def test_comma_in_source_does_not_cause_a_false_positive(self):
        # Prototype bug #1 (fixed): a phrase spanning a comma in the source
        # ("Newtown, New South Wales") must still match content that states
        # it without the comma.
        content = "This is a church in Newtown New South Wales."
        self.assertTrue(check_grounding(content, ["church in Newtown, New South Wales"]))

    def test_sentence_boundary_does_not_merge_into_a_false_phrase(self):
        # Prototype bug #1 (fixed): a period must break a capitalized run,
        # so a new sentence's opener never merges with the real phrase
        # before it into something that fails to match.
        content = "Newtown Baptist Church is a church in Newtown, New South Wales. Pause here a moment."
        self.assertTrue(check_grounding(content, ["church in Newtown, New South Wales", "Newtown Baptist Church"]))

    def test_documented_gap_fabricated_relationship_with_no_new_entity_passes(self):
        # KNOWN LIMITATION (Codex review 2026-10-18→20, confirmed with real
        # counterexamples): this cheap check cannot catch a fabricated
        # claim/relationship that introduces no new number or multi-word
        # name. Pinned here deliberately - this is exactly why it's only a
        # pre-filter, never the final gate (see check_grounding_semantic).
        content = "This sculpture commemorates workers killed in a factory fire."
        self.assertTrue(check_grounding(content, ["By Michael Snape."]))

    def test_documented_gap_fabricated_relationship_reusing_real_name_passes(self):
        content = "Michael Snape designed this church."
        self.assertTrue(check_grounding(content, ["By Michael Snape."]))


class TestMalformedProviderResponses(unittest.TestCase):
    """Codex review 2026-10-21: the response-parsing code previously read
    the top-level shape inside its try/except guard, but iterated items and
    accessed per-item fields OUTSIDE it - a malformed individual entry
    (null list, missing key, wrong type) raised an uncaught TypeError/
    KeyError instead of the advertised AiSelectionError/excerpt fallback.
    Reproduced directly before fixing; pinned here as regression tests."""

    def setUp(self):
        for name, value in (("get_api_key", "test-key"), ("get_model", "test-model")):
            patcher = patch(f"ai.{name}", return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_content_generation_null_stops_list_raises_ai_selection_error(self):
        mock_response = make_mock_response(make_openai_response({"stops": None}))
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                ai._call_content_generation([], "history")

    def test_content_generation_entry_missing_content_is_skipped_not_a_crash(self):
        mock_response = make_mock_response(make_openai_response(
            {"stops": [{"stop_id": "x"}]}  # no "content" key at all
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_content_generation([], "history")
        self.assertEqual(result, {})  # skipped, not raised - caller's "missing" fallback applies

    def test_content_generation_numeric_content_is_skipped_not_a_crash(self):
        mock_response = make_mock_response(make_openai_response(
            {"stops": [{"stop_id": "x", "content": 123, "used_evidence_ids": []}]}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_content_generation([], "history")
        self.assertEqual(result, {})

    def test_content_generation_blank_content_is_skipped_not_treated_as_grounded(self):
        mock_response = make_mock_response(make_openai_response(
            {"stops": [{"stop_id": "x", "content": "   ", "used_evidence_ids": []}]}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_content_generation([], "history")
        self.assertEqual(result, {})

    def test_content_generation_one_bad_entry_does_not_lose_a_valid_sibling(self):
        mock_response = make_mock_response(make_openai_response({"stops": [
            {"stop_id": "bad"},
            {"stop_id": "good", "content": "Real content.", "used_evidence_ids": []},
        ]}))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_content_generation([], "history")
        self.assertEqual(set(result.keys()), {"good"})

    def test_content_generation_null_used_evidence_ids_degrades_to_empty_list(self):
        # Codex review 2026-10-21: `used_evidence_ids: null` crashed the
        # list comprehension with TypeError ('NoneType' object is not
        # iterable). A malformed citation declaration shouldn't discard
        # otherwise-good content - degrade to [] instead.
        mock_response = make_mock_response(make_openai_response(
            {"stops": [{"stop_id": "x", "content": "Real content.", "used_evidence_ids": None}]}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_content_generation([], "history")
        self.assertEqual(result["x"], {"content": "Real content.", "used_evidence_ids": []})

    def test_content_generation_non_string_item_in_used_evidence_ids_is_dropped(self):
        mock_response = make_mock_response(make_openai_response(
            {"stops": [{"stop_id": "x", "content": "Real content.", "used_evidence_ids": ["own", 42, None]}]}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_content_generation([], "history")
        self.assertEqual(result["x"]["used_evidence_ids"], ["own"])

    def test_grounding_batch_null_items_list_raises_ai_selection_error(self):
        mock_response = make_mock_response(make_openai_response({"items": None}))
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                ai._call_grounding_check_batch([("a", "content", ["evidence"])])

    def test_grounding_batch_entry_missing_supported_is_skipped_not_a_crash(self):
        mock_response = make_mock_response(make_openai_response({"items": [{"item_id": "a"}]}))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_grounding_check_batch([("a", "content", ["evidence"])])
        self.assertEqual(result, {})

    def test_corrupted_contextual_sources_file_degrades_to_no_sources(self):
        # Direct unit coverage of the actual fix: load_contextual_sources()
        # must degrade to [] for a corrupted file the same way it already
        # does for a missing one, never raise - this is the fix itself, and
        # it's also what every caller (get_contextual_sources(),
        # generate_stop_content()) relies on to stay crash-free, since none
        # of them separately guard against this exception class.
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "bad.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not valid json")
            result = load_contextual_sources(path)
        self.assertEqual(result, [])


class TestCallGroundingCheckBatch(unittest.TestCase):
    def setUp(self):
        for name, value in (("get_api_key", "test-key"), ("get_model", "test-model")):
            patcher = patch(f"ai.{name}", return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_per_item_verdicts_returned(self):
        mock_response = make_mock_response(make_openai_response(
            {"items": [{"item_id": "a", "supported": True}, {"item_id": "b", "supported": False}]}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_grounding_check_batch([("a", "content a", ["evidence a"]), ("b", "content b", ["evidence b"])])
        self.assertEqual(result, {"a": True, "b": False})

    def test_each_item_evidence_sent_separately_not_pooled(self):
        mock_response = make_mock_response(make_openai_response({"items": []}))
        with patch("ai.requests.post", return_value=mock_response) as mock_post:
            ai._call_grounding_check_batch([("a", "content a", ["evidence a"]), ("b", "content b", ["evidence b"])])
        _, kwargs = mock_post.call_args
        user_message = kwargs["json"]["messages"][1]["content"]
        self.assertIn("evidence a", user_message)
        self.assertIn("evidence b", user_message)

    def test_http_failure_raises_ai_selection_error(self):
        with patch("ai.requests.post", side_effect=requests.exceptions.ConnectionError("boom")):
            with self.assertRaises(AiSelectionError):
                ai._call_grounding_check_batch([("a", "content", ["evidence"])])

    def test_check_grounding_semantic_wraps_batch_with_one_item(self):
        mock_response = make_mock_response(make_openai_response(
            {"items": [{"item_id": "item", "supported": True}]}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = check_grounding_semantic("some content", ["some evidence"])
        self.assertTrue(result)

    def test_check_grounding_semantic_catches_the_rule_based_gap(self):
        # The exact counterexamples the cheap check misses - this is the
        # real gate that must catch them.
        mock_response = make_mock_response(make_openai_response(
            {"items": [{"item_id": "item", "supported": False}]}
        ))
        with patch("ai.requests.post", return_value=mock_response):
            result = check_grounding_semantic(
                "This sculpture commemorates workers killed in a factory fire.", ["By Michael Snape."]
            )
        self.assertFalse(result)


class TestGenerateStopContent(unittest.TestCase):
    """Orchestration tests - patch the two batched-call primitives directly
    rather than raw HTTP, since generate_stop_content()'s own job is the
    two-tier flow (cheap pre-filter -> real semantic gate -> fallback), not
    HTTP handling (already covered by the lower-level tests above)."""

    def _generated(self, content_by_id, used_evidence_ids=None):
        return {
            stop_id: {"content": content, "used_evidence_ids": (used_evidence_ids or {}).get(stop_id, [])}
            for stop_id, content in content_by_id.items()
        }

    def test_grounded_content_is_used_with_own_attribution(self):
        generated = self._generated({SAMPLE_STOP_RICH["id"]: "Newtown Railway Station reflects three phases of NSW railway development."})
        with patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch", return_value={SAMPLE_STOP_RICH["id"]: True}):
            results = generate_stop_content([SAMPLE_STOP_RICH], "history")
        self.assertEqual(len(results), 1)
        self.assertNotEqual(results[0]["content"], SAMPLE_STOP_RICH["source_excerpt"])
        self.assertEqual(results[0]["attribution"], [{
            "source_type": SAMPLE_STOP_RICH["source_type"],
            "source_title": SAMPLE_STOP_RICH["source_title"],
            "source_url": SAMPLE_STOP_RICH["source_url"],
        }])

    def test_semantic_check_rejection_falls_back_to_raw_excerpt(self):
        generated = self._generated({SAMPLE_STOP_THIN["id"]: "This sculpture commemorates workers killed in a factory fire."})
        with patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch", return_value={SAMPLE_STOP_THIN["id"]: False}):
            results = generate_stop_content([SAMPLE_STOP_THIN], "public_art")
        self.assertEqual(results[0]["content"], SAMPLE_STOP_THIN["source_excerpt"])
        self.assertEqual(len(results[0]["attribution"]), 1)

    def test_rule_based_prefilter_skips_the_semantic_call_entirely(self):
        # A fabricated date is caught by the cheap check already - no need
        # to spend the semantic call on content already known to be bad.
        generated = self._generated({SAMPLE_STOP_RICH["id"]: "Newtown Railway Station was designed in 1887 by Walter Liberty Vernon."})
        with patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch") as mock_semantic:
            results = generate_stop_content([SAMPLE_STOP_RICH], "history")
        mock_semantic.assert_not_called()
        self.assertEqual(results[0]["content"], SAMPLE_STOP_RICH["source_excerpt"])

    def test_whole_generation_call_failure_falls_every_stop_back(self):
        with patch("ai._call_content_generation", side_effect=AiSelectionError("boom")):
            results = generate_stop_content([SAMPLE_STOP_RICH, SAMPLE_STOP_THIN], "history")
        self.assertEqual(results[0]["content"], SAMPLE_STOP_RICH["source_excerpt"])
        self.assertEqual(results[1]["content"], SAMPLE_STOP_THIN["source_excerpt"])

    def test_semantic_call_failure_falls_candidates_back_not_trusting_the_prefilter(self):
        generated = self._generated({SAMPLE_STOP_RICH["id"]: "Newtown Railway Station reflects three phases of NSW railway development."})
        with patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch", side_effect=AiSelectionError("boom")):
            results = generate_stop_content([SAMPLE_STOP_RICH], "history")
        self.assertEqual(results[0]["content"], SAMPLE_STOP_RICH["source_excerpt"])

    def test_stop_missing_from_generation_response_falls_back(self):
        with patch("ai._call_content_generation", return_value={}), \
             patch("ai._call_grounding_check_batch") as mock_semantic:
            results = generate_stop_content([SAMPLE_STOP_RICH], "history")
        mock_semantic.assert_not_called()
        self.assertEqual(results[0]["content"], SAMPLE_STOP_RICH["source_excerpt"])

    def test_one_missing_stop_does_not_affect_the_other(self):
        generated = self._generated({SAMPLE_STOP_RICH["id"]: "Newtown Railway Station reflects three phases of NSW railway development."})
        with patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch", return_value={SAMPLE_STOP_RICH["id"]: True}):
            results = generate_stop_content([SAMPLE_STOP_RICH, SAMPLE_STOP_THIN], "history")
        by_id = {r["id"]: r for r in results}
        self.assertNotEqual(by_id[SAMPLE_STOP_RICH["id"]]["content"], SAMPLE_STOP_RICH["source_excerpt"])
        self.assertEqual(by_id[SAMPLE_STOP_THIN["id"]]["content"], SAMPLE_STOP_THIN["source_excerpt"])

    def test_cross_stop_leakage_stop_a_never_grounded_against_stop_b_evidence(self):
        # Hand-constructed: Stop A's "generated" content borrows a fact only
        # true of Stop B's evidence - deliberately with no number or
        # multi-word proper noun, so it passes the cheap pre-filter and
        # actually reaches the layer under test (the semantic call's
        # per-item evidence scoping), rather than getting caught a layer
        # earlier for an unrelated reason.
        stop_a = dict(SAMPLE_STOP_THIN, id="a", source_excerpt="By Michael Snape.")
        stop_b = dict(SAMPLE_STOP_RICH, id="b")
        generated = self._generated({
            "a": "This piece reflects major phases of railway development.",
            "b": "Newtown Railway Station reflects three phases of NSW railway development.",
        })
        # Confirm the premise: the cheap filter alone would wrongly pass
        # Stop A's borrowed claim (no checkable token), which is exactly
        # why the semantic layer - and its evidence scoping - matters here.
        self.assertTrue(check_grounding(generated["a"]["content"], [stop_a["source_excerpt"]]))

        captured_items = {}

        def fake_semantic_batch(items):
            # Record exactly what evidence each item was checked against.
            for item_id, _content, evidence_texts in items:
                captured_items[item_id] = evidence_texts
            return {"a": False, "b": True}

        # No Contextual Sources here - isolates the thing under test (stop-
        # to-stop leakage) from the separate, legitimate mechanism of a
        # Contextual Source being offered on purpose.
        with patch("ai.load_contextual_sources", return_value=[]), \
             patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch", side_effect=fake_semantic_batch):
            results = generate_stop_content([stop_a, stop_b], "history")

        # Stop A's evidence never contains text unique to Stop B's own
        # excerpt ("booking office" appears only in SAMPLE_STOP_RICH's
        # source_excerpt, nowhere in Stop A's).
        self.assertNotIn("booking office", " ".join(captured_items["a"]).lower())
        by_id = {r["id"]: r for r in results}
        self.assertEqual(by_id["a"]["content"], "By Michael Snape.")  # fell back

    def test_surprise_me_uses_each_stops_own_topics_for_contextual_lookup(self):
        fake_sources = [{"id": "hist", "topics": ["history"], "source_type": "wikipedia",
                          "source_title": "H", "source_url": "https://h", "text": "History text"}]
        generated = self._generated({SAMPLE_STOP_RICH["id"]: "content"})
        with patch("ai.load_contextual_sources", return_value=fake_sources), \
             patch("ai._call_content_generation", return_value=generated) as mock_gen, \
             patch("ai._call_grounding_check_batch", return_value={SAMPLE_STOP_RICH["id"]: True}):
            generate_stop_content([SAMPLE_STOP_RICH], "surprise_me")
        # The stop's own "history" topic should have surfaced the seed
        # entry even though the route-level topic was surprise_me.
        (stops_with_evidence, _topic), _kwargs = mock_gen.call_args
        evidence = stops_with_evidence[0][1]
        self.assertTrue(any(e.get("id") == "hist" for e in evidence))

    def test_unmatched_topic_gets_no_contextual_source_not_an_error(self):
        generated = self._generated({SAMPLE_STOP_THIN["id"]: "By Michael Snape."})
        with patch("ai.load_contextual_sources", return_value=[]), \
             patch("ai._call_content_generation", return_value=generated) as mock_gen, \
             patch("ai._call_grounding_check_batch", return_value={SAMPLE_STOP_THIN["id"]: True}):
            generate_stop_content([SAMPLE_STOP_THIN], "public_art")
        (stops_with_evidence, _topic), _kwargs = mock_gen.call_args
        evidence = stops_with_evidence[0][1]
        self.assertEqual(len(evidence), 1)  # own source only

    def test_attribution_reflects_declared_used_sources_not_every_offered_one(self):
        # Codex review 2026-10-20: a stop must not get credited with a
        # Contextual Source it was merely offered but never declared using.
        fake_sources = [{"id": "hist", "topics": ["history"], "source_type": "wikipedia",
                          "source_title": "H", "source_url": "https://h", "text": "History text"}]
        generated = self._generated(
            {SAMPLE_STOP_RICH["id"]: "Newtown Railway Station reflects three phases of NSW railway development."},
            used_evidence_ids={SAMPLE_STOP_RICH["id"]: ["own"]},  # explicitly did NOT use "hist"
        )
        with patch("ai.load_contextual_sources", return_value=fake_sources), \
             patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch", return_value={SAMPLE_STOP_RICH["id"]: True}):
            results = generate_stop_content([SAMPLE_STOP_RICH], "history")
        self.assertEqual(len(results[0]["attribution"]), 1)
        self.assertEqual(results[0]["attribution"][0]["source_url"], SAMPLE_STOP_RICH["source_url"])

    def test_grounding_check_scoped_to_cited_evidence_not_every_offered_source(self):
        # Codex review 2026-10-21: evidence_texts used to be built from ALL
        # offered evidence, not just the sources the model actually declared
        # using - so a fabricated claim could be wrongly "grounded" against
        # a Contextual Source the stop was merely offered but never cited.
        fake_sources = [{"id": "ctx", "topics": ["history"], "source_type": "wikipedia",
                          "source_title": "C", "source_url": "https://c",
                          "text": "Designed by Walter Liberty Vernon in 1887."}]
        generated = self._generated(
            {SAMPLE_STOP_RICH["id"]: "Designed by Walter Liberty Vernon in 1887."},
            used_evidence_ids={SAMPLE_STOP_RICH["id"]: ["own"]},  # did NOT cite "ctx"
        )
        with patch("ai.load_contextual_sources", return_value=fake_sources), \
             patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch") as mock_semantic:
            results = generate_stop_content([SAMPLE_STOP_RICH], "history")
        # The fabricated name/date aren't in the own excerpt and the source
        # that does contain them was never cited - must fall back, not pass
        # the rule-based check by accident, and never even reach the
        # semantic layer for an already-rejected candidate.
        mock_semantic.assert_not_called()
        self.assertEqual(results[0]["content"], SAMPLE_STOP_RICH["source_excerpt"])

    def test_declared_source_id_never_offered_is_ignored(self):
        generated = self._generated(
            {SAMPLE_STOP_THIN["id"]: "By Michael Snape."},
            used_evidence_ids={SAMPLE_STOP_THIN["id"]: ["own", "made_up_id_never_offered"]},
        )
        with patch("ai.load_contextual_sources", return_value=[]), \
             patch("ai._call_content_generation", return_value=generated), \
             patch("ai._call_grounding_check_batch", return_value={SAMPLE_STOP_THIN["id"]: True}):
            results = generate_stop_content([SAMPLE_STOP_THIN], "public_art")
        self.assertEqual(len(results[0]["attribution"]), 1)  # the bogus id never added a second entry


class TestBuildPromptVisitHistory(unittest.TestCase):
    """Story 3.4 (AD-6): a soft signal, same shape as preference above."""

    def test_visit_history_embedded_and_guidance_present_when_given(self):
        history = [{"id": "node/1", "state": "visited_completed", "favourited": False}]
        prompt = build_prompt(SAMPLE_OPTIONS, "public_art", 60, visit_history=history)
        details = json.JSONDecoder().raw_decode(prompt.split("\n\n", 1)[1])[0]
        self.assertEqual(details["visit_history"], history)
        self.assertIn("deprioritized", prompt)
        self.assertIn("never excluded", prompt)
        self.assertIn("never a hard", prompt)

    def test_no_visit_history_section_when_omitted_or_empty(self):
        for empty in (None, []):
            prompt = build_prompt(SAMPLE_OPTIONS, "public_art", 60, visit_history=empty)
            self.assertNotIn("visit_history", prompt)

    def test_select_stops_threads_visit_history_into_the_prompt(self):
        history = [{"id": "node/2", "state": "opened_engaged", "favourited": True}]
        mock_response = make_mock_response(make_openai_response(
            {"selected_option": "option_1", "none_suitable_reason": ""}
        ))
        with patch("ai.requests.post", return_value=mock_response) as mock_post:
            select_stops(SAMPLE_OPTIONS, "public_art", 60, visit_history=history)
        sent_prompt = mock_post.call_args.kwargs["json"]["messages"][1]["content"]
        self.assertIn("node/2", sent_prompt)


class TestGenerateWalkSummary(unittest.TestCase):
    """Orchestration tests - patch the call primitive and the grounding
    check directly, same style as TestGenerateStopContent above."""

    VISITED = [
        {"id": "node/1", "name": "Newtown Station", "content": "A historic railway station."},
        {"id": "node/2", "name": "Mural Lane", "content": "A laneway covered in street art."},
    ]

    def test_grounded_summary_is_returned(self):
        with patch("ai._call_walk_summary", return_value="You explored a historic station and a vibrant mural lane."), \
             patch("ai.check_grounding_semantic", return_value=True) as mock_check:
            result = generate_walk_summary(self.VISITED)
        self.assertEqual(result, "You explored a historic station and a vibrant mural lane.")
        # Grounded strictly in the visited stops' own content (FR-16).
        self.assertEqual(mock_check.call_args.args[1], [s["content"] for s in self.VISITED])

    def test_grounding_rejection_returns_none_not_the_ungrounded_text(self):
        with patch("ai._call_walk_summary", return_value="A fabricated claim."), \
             patch("ai.check_grounding_semantic", return_value=False):
            result = generate_walk_summary(self.VISITED)
        self.assertIsNone(result)

    def test_call_failure_returns_none(self):
        with patch("ai._call_walk_summary", side_effect=AiSelectionError("boom")), \
             patch("ai.check_grounding_semantic") as mock_check:
            result = generate_walk_summary(self.VISITED)
        self.assertIsNone(result)
        mock_check.assert_not_called()

    def test_zero_visited_stops_never_calls_ai_at_all(self):
        with patch("ai._call_walk_summary") as mock_call:
            result = generate_walk_summary([])
        self.assertIsNone(result)
        mock_call.assert_not_called()


class TestCallWalkSummary(unittest.TestCase):
    """Low-level HTTP-boundary tests, same style as the other _call_* tests."""

    def test_returns_summary_string_from_well_formed_response(self):
        mock_response = make_mock_response(make_openai_response({"summary": "A lovely afternoon walk."}))
        with patch("ai.requests.post", return_value=mock_response):
            result = ai._call_walk_summary([{"name": "A Place", "content": "Some content."}])
        self.assertEqual(result, "A lovely afternoon walk.")

    def test_empty_summary_raises_selection_error(self):
        mock_response = make_mock_response(make_openai_response({"summary": "   "}))
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                ai._call_walk_summary([{"name": "A Place", "content": "Some content."}])

    def test_malformed_response_shape_raises_selection_error(self):
        mock_response = make_mock_response({"choices": [{"message": {"content": "not json"}}]})
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                ai._call_walk_summary([{"name": "A Place", "content": "Some content."}])

    def test_non_retryable_http_error_raises_fatal_error(self):
        mock_response = make_http_error_response(401, error_type="invalid_api_key")
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiFatalError):
                ai._call_walk_summary([{"name": "A Place", "content": "Some content."}])


if __name__ == "__main__":
    unittest.main()
