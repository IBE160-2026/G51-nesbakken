import json
import unittest
from unittest.mock import MagicMock, patch

import requests

from ai import SYSTEM_PROMPT, AiFatalError, AiSelectionError, build_prompt, select_stops

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
        self.assertIn("relevance and interest come first", SYSTEM_PROMPT)


class TestSelectStops(unittest.TestCase):
    def setUp(self):
        get_key_patcher = patch("ai.get_api_key", return_value="test-api-key")
        get_model_patcher = patch("ai.get_model", return_value="test-model")
        self.mock_get_api_key = get_key_patcher.start()
        self.mock_get_model = get_model_patcher.start()
        self.addCleanup(get_key_patcher.stop)
        self.addCleanup(get_model_patcher.stop)

    def test_returns_selected_option_from_valid_response(self):
        mock_response = make_mock_response(make_openai_response({"selected_option": "option_2"}))
        with patch("ai.requests.post", return_value=mock_response):
            result = select_stops(SAMPLE_OPTIONS, "public_art", 60)
        self.assertEqual(result, "option_2")

    def test_sends_authorization_header_and_model_and_schema(self):
        mock_response = make_mock_response(make_openai_response({"selected_option": "option_1"}))
        with patch("ai.requests.post", return_value=mock_response) as mock_post:
            select_stops(SAMPLE_OPTIONS, "public_art", 60)
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-api-key")
        self.assertEqual(kwargs["json"]["model"], "test-model")
        self.assertEqual(kwargs["json"]["response_format"]["type"], "json_schema")
        self.assertEqual(
            kwargs["json"]["response_format"]["json_schema"]["schema"]["required"],
            ["selected_option"],
        )

    def test_feedback_reaches_the_request_body(self):
        mock_response = make_mock_response(make_openai_response({"selected_option": "option_1"}))
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
        mock_response = make_mock_response(make_openai_response({"selected_option": 123}))
        with patch("ai.requests.post", return_value=mock_response):
            with self.assertRaises(AiSelectionError):
                select_stops(SAMPLE_OPTIONS, "public_art", 60)

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


if __name__ == "__main__":
    unittest.main()
