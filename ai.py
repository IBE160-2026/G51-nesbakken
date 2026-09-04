"""Sprint 4 (part 1): AI final stop selection.

AI's role is bounded to one judgement call: given a menu of already-feasible
walking-route options planner.py has computed, choose the one that is most
relevant and interesting for the requested topic. AI never invents a place,
never computes routing arithmetic, and never decides feasibility - it only
picks among options planner.py has already proven walkable in the requested
time (see "Redesign after live testing" in docs/ai-development-log.md for
why an earlier version that asked AI to compute feasibility itself was
replaced).

Provider choice (OpenAI) is an implementation detail, not a permanent
architectural dependency - see docs/ai-development-log.md. Every
OpenAI-specific request/response detail is kept inside this module, behind
select_stops(), so switching providers later means rewriting this file only.
"""

import json
import os

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are selecting the stops for a short walking tour called Jaunt. "
    "You will be given a numbered list of walking-route options. Every "
    "option has already been checked by Python: its walking time, dwell "
    "time, and total are confirmed to fit within requested_minutes. You do "
    "not need to, and should not try to, recompute or second-guess that - "
    "treat every listed option as already feasible.\n\n"
    "Your job is a judgement call, not arithmetic: choose the option_key of "
    "the option whose stops form the most relevant and interesting walk for "
    "the requested topic, based on each stop's name, topics, and source "
    "excerpt.\n\n"
    "You may only choose one of the option_keys actually listed - never "
    "invent one. Among options that are similarly relevant and interesting, "
    "prefer the one with the higher budget_usage_ratio (closer to fully "
    "using the requested time), but relevance and interest come first.\n\n"
    "Respond using only the required JSON schema - no extra commentary."
)

# Forces the response into {"selected_option": "..."} rather than free-form
# prose that would need to be parsed hopefully-correctly.
SELECTION_SCHEMA = {
    "name": "option_selection",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "selected_option": {"type": "string"},
        },
        "required": ["selected_option"],
        "additionalProperties": False,
    },
}


class AiSelectionError(Exception):
    """Raised when the AI response can't be used - a failed request, or a
    response that isn't the expected JSON shape. planner.py treats this the
    same as an invalid selection: a reason to retry, not a fatal error."""


class AiFatalError(AiSelectionError):
    """Raised for a request failure retrying cannot fix: invalid credentials
    (401), permission/model-access errors (403), or a quota-exhausted 429.
    planner.py stops immediately on this rather than spending its remaining
    attempts repeating an identical, doomed request."""


NON_RETRYABLE_STATUS_CODES = {401, 403}


def _extract_error_detail(exc):
    """Pulls OpenAI's own error message/type out of a failed response, when
    available. The bare HTTPError text (e.g. "429 Client Error: Too Many
    Requests") doesn't say whether this is a transient rate limit or an
    account-level problem retrying can never fix - returns (detail_text,
    error_type), with error_type "" if it couldn't be determined."""
    response = getattr(exc, "response", None)
    if response is None:
        return str(exc), ""
    try:
        body = response.json()
    except ValueError:
        return str(exc), ""
    error = body.get("error") or {}
    message = error.get("message")
    error_type = error.get("type") or ""
    if message:
        return f"{exc} ({error_type or 'error'}: {message})", error_type
    return str(exc), error_type


def _is_non_retryable(status_code, error_type):
    if status_code in NON_RETRYABLE_STATUS_CODES:
        return True
    return status_code == 429 and "quota" in error_type.lower()


def load_env(path=ENV_PATH):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def get_api_key():
    load_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found. Check your .env file at the project root."
        )
    return api_key


def get_model():
    load_env()
    model = os.environ.get("OPENAI_MODEL")
    if not model:
        raise RuntimeError(
            "OPENAI_MODEL not found. Check your .env file at the project root."
        )
    return model


def build_prompt(options, topic, requested_minutes, feedback=None):
    """Builds the user-message text sent to AI: the request details and the
    pre-validated option menu planner.py computed. No raw duration matrix is
    sent - AI is not asked to do any routing arithmetic in this design.

    feedback: optional text describing what was wrong with a previous
    attempt (a failed request, or an option_key that wasn't offered), so a
    retry can ask AI to correct the specific problem rather than guess again
    from scratch.
    """
    request_details = {
        "topic": topic,
        "requested_minutes": requested_minutes,
        "options": options,
    }

    prompt = "Choose one option_key for this walk.\n\n" + json.dumps(
        request_details, indent=2
    )

    if feedback:
        prompt += f"\n\nYour last response could not be used: {feedback}"

    return prompt


def _call_openai(prompt):
    try:
        response = requests.post(
            CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {get_api_key()}",
                "Content-Type": "application/json",
            },
            json={
                "model": get_model(),
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": SELECTION_SCHEMA,
                },
            },
            timeout=60,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        detail, error_type = _extract_error_detail(exc)
        if _is_non_retryable(status_code, error_type):
            raise AiFatalError(f"OpenAI request failed: {detail}") from exc
        raise AiSelectionError(f"OpenAI request failed: {detail}") from exc
    except requests.RequestException as exc:
        raise AiSelectionError(f"OpenAI request failed: {exc}") from exc

    body = response.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise AiSelectionError(f"unexpected OpenAI response shape: {exc}") from exc


def select_stops(options, topic, requested_minutes, feedback=None):
    """Asks AI to choose one option_key from the pre-validated options list
    planner.py computed (each already confirmed feasible). Returns the raw
    string AI chose - not yet checked that it's actually one of the offered
    keys, that's planner.py's job.

    Raises AiSelectionError if the request fails or the response isn't
    valid JSON in the expected shape.
    """
    prompt = build_prompt(options, topic, requested_minutes, feedback)
    raw_content = _call_openai(prompt)

    try:
        parsed = json.loads(raw_content)
        selected_option = parsed["selected_option"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AiSelectionError(
            f"AI response was not the expected JSON shape: {exc}"
        ) from exc

    if not isinstance(selected_option, str):
        raise AiSelectionError("AI response 'selected_option' must be a string")

    return selected_option
