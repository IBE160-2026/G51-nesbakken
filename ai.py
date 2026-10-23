"""AI's two jobs for Jaunt: selecting stops, and generating their content.

Selection (Sprint 4): given a menu of already-feasible walking-route options
planner.py has computed, choose the one that is most relevant and
interesting for the requested topic. AI never invents a place, never
computes routing arithmetic, and never decides feasibility - it only picks
among options planner.py has already proven walkable in the requested time
(see "Redesign after live testing" in docs/ai-development-log.md for why an
earlier version that asked AI to compute feasibility itself was replaced).

Content generation (Story 1.3): given a route's stops, each with its own
source excerpt and whatever Contextual Sources match the requested topic,
write short grounded content for each one, and check it with a rule-based
(non-LLM) grounding check before it's used. A stop whose generation or
grounding fails falls back to its own raw source excerpt - never fails the
whole route. See generate_stop_content().

Provider choice (OpenAI) is an implementation detail, not a permanent
architectural dependency - see docs/ai-development-log.md. Every
OpenAI-specific request/response detail is kept inside this module, so
switching providers later means rewriting this file only.
"""

import json
import os
import re

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
CONTEXTUAL_SOURCES_PATH = os.path.join(BASE_DIR, "data", "contextual_sources.json")

SYSTEM_PROMPT = (
    "You are selecting the stops for a short walking tour called Jaunt. "
    "You will be given a numbered list of walking-route options. Every "
    "option has already been checked by Python: its walking time, dwell "
    "time, and total are confirmed to fit within requested_minutes. You do "
    "not need to, and should not try to, recompute or second-guess that - "
    "treat every listed option as already feasible.\n\n"
    "Your job is a judgement call, not arithmetic: choose the option_key of "
    "the option whose stops form the most relevant and interesting walk for "
    "the requested topic, considering the continuous landmark/hidden-gem "
    "preference using each stop's name, topics and supplied source evidence. "
    "Keep relevance and suitability constraints; preference is soft guidance "
    "and source category is not popularity.\n\n"
    "You may only choose one of the option_keys actually listed - never "
    "invent one. Among options that are similarly relevant, interesting and "
    "suited to the preference, "
    "prefer the one with the higher budget_usage_ratio (closer to fully "
    "using the requested time), but relevance, interest and "
    "preference come first.\n\n"
    "If - and only if - none of the offered options are genuinely relevant "
    "or interesting for the requested topic, even though every one of them "
    "is already time-feasible, set selected_option to the literal string "
    "\"none_suitable\" instead of any option_key, and give a real one-line "
    "reason in none_suitable_reason. This is honesty, not a last resort - "
    "a mathematically feasible walk that doesn't actually suit the topic is "
    "a worse result than telling the user no suitable walk was found. When "
    "you do choose a real option_key, leave none_suitable_reason as an "
    "empty string.\n\n"
    "Respond using only the required JSON schema - no extra commentary."
)

# Forces the response into {"selected_option": "...", "none_suitable_reason":
# "..."} rather than free-form prose - and gives AI an explicit, always-
# valid way to reject every offered option as genuinely unsuitable (AD-7),
# rather than being structurally forced to pick one. none_suitable_reason
# is always present (strict-mode schemas require every property), meaningful
# only when selected_option is "none_suitable".
SELECTION_SCHEMA = {
    "name": "option_selection",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "selected_option": {"type": "string"},
            "none_suitable_reason": {"type": "string"},
        },
        "required": ["selected_option", "none_suitable_reason"],
        "additionalProperties": False,
    },
}

NONE_SUITABLE = "none_suitable"


class AiSelectionError(Exception):
    """Raised when the AI response can't be used - a failed request, or a
    response that isn't the expected JSON shape. planner.py treats this the
    same as an invalid selection: a reason to retry, not a fatal error."""


class AiFatalError(AiSelectionError):
    """Raised for a request failure retrying cannot fix: invalid credentials
    (401), permission/model-access errors (403), or a quota-exhausted 429.
    planner.py stops immediately on this rather than spending its remaining
    attempts repeating an identical, doomed request."""


class AiExhaustedError(AiSelectionError):
    """Raised by planner.py (not ai.py itself) when every retry attempt
    failed with an ordinary (non-fatal) AiSelectionError and none ever
    produced a usable selection - a persistent, repeated failure to get
    any response from AI at all, not a judgement that no route is
    suitable. Codex review 2026-10-21: the retry-exhaustion fallthrough
    previously returned the same {"feasible": false} shape as ordinary
    infeasibility, masquerading a real technical problem as an honest "no
    suitable walk" - a caller (the UI) could wrongly suggest changing the
    request when the actual problem is an unavailable AI service."""


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


def build_prompt(options, topic, requested_minutes, feedback=None, preference=0.5):
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
        "preference": preference,
        "options": options,
    }

    prompt = "Choose one option_key for this walk.\n\n" + json.dumps(
        request_details, indent=2
    )
    prompt += (
        "\n\nThe continuous preference is 0 for well-known landmarks, 0.5 for Balanced, "
        "and 1 for hidden gems. Intermediate values express a gradual preference; "
        "do not round them into categories. Favour familiar landmarks toward 0 and "
        "lesser-known discoveries toward 1, balancing both at 0.5. "
        "Use supplied evidence and general knowledge of recognisability for prominence only. "
        "Unknown does not mean hidden. Strong preferences should noticeably favour "
        "matching options where available, before filling time. Keep mixed choices possible. "
        "Stories must remain grounded in supplied sources. Source category "
        "(source_type) is not popularity, and lesser-known does not mean low quality. "
        "Use caution with weak evidence; do not invent fame, obscurity or stories. "
        "This is soft guidance alongside relevance and interest, never a filter: "
        "preference alone must not require rejecting an otherwise suitable offered walk, "
        "even when only one kind of suitable stop is available."
    )

    if feedback:
        prompt += f"\n\nYour last response could not be used: {feedback}"

    return prompt


def _call_openai(prompt, schema=None, system_prompt=None):
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
                    {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": schema or SELECTION_SCHEMA,
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

    try:
        body = response.json()
    except ValueError as exc:
        raise AiSelectionError(f"OpenAI response was not valid JSON: {exc}") from exc
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AiSelectionError(f"unexpected OpenAI response shape: {exc}") from exc


def select_stops(options, topic, requested_minutes, feedback=None, preference=0.5):
    """Asks AI to choose one option_key from the pre-validated options list
    planner.py computed (each already confirmed feasible) - or the literal
    string NONE_SUITABLE if none are genuinely relevant (AD-7). Returns
    {"selected_option": str, "none_suitable_reason": str} - not yet checked
    that selected_option is actually one of the offered keys, that's
    planner.py's job. none_suitable_reason is always a string (possibly
    empty); only meaningful when selected_option == NONE_SUITABLE.

    Raises AiSelectionError if the request fails or the response isn't
    valid JSON in the expected shape.
    """
    prompt = build_prompt(options, topic, requested_minutes, feedback, preference=preference)
    raw_content = _call_openai(prompt)

    try:
        parsed = json.loads(raw_content)
        selected_option = parsed["selected_option"]
        none_suitable_reason = parsed["none_suitable_reason"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AiSelectionError(
            f"AI response was not the expected JSON shape: {exc}"
        ) from exc

    if not isinstance(selected_option, str):
        raise AiSelectionError("AI response 'selected_option' must be a string")
    if not isinstance(none_suitable_reason, str):
        raise AiSelectionError("AI response 'none_suitable_reason' must be a string")

    return {"selected_option": selected_option, "none_suitable_reason": none_suitable_reason}


MAX_DISCOVERY_CANDIDATES = 200
MAX_DISCOVERY_PROMPT_CHARS = 100000
DISCOVERY_SYSTEM_PROMPT = (
    "Choose routing candidate IDs only from the offered eligible places. Python owns "
    "eligibility and walking feasibility. Select exactly the requested count of unique IDs. "
    "Use the continuous preference: 0=well-known landmarks, 0.5=balanced, 1=hidden gems; "
    "do not round intermediate values. Strong preferences should noticeably favour matching "
    "places where available, with ordinary alternatives to fill remaining slots. Order IDs by "
    "preference match, strongest matches first. "
    "Use general knowledge of recognisability for prominence only; unknown does not mean hidden, "
    "and source category is not popularity. Keep balanced/mixed choices possible. "
    "Do not invent places, IDs or stories. Return only the required JSON."
)
DISCOVERY_SCHEMA = {
    "name": "candidate_discovery", "strict": True,
    "schema": {"type": "object", "properties": {
        "candidate_ids": {"type": "array", "items": {"type": "string"}}},
        "required": ["candidate_ids"], "additionalProperties": False},
}


def discover_candidates(candidates, topic, preference, count):
    """At most two provider attempts; malformed discovery is a service error."""
    if len(candidates) > MAX_DISCOVERY_CANDIDATES:
        raise AiExhaustedError("candidate discovery exceeds the 200-place service limit")
    compact = [{"id": p["id"], "name": str(p.get("name") or "")[:120],
                "topics": p.get("topics", []),
                "latitude": p.get("latitude"), "longitude": p.get("longitude"),
                "source_title": str(p.get("source_title") or "")[:160],
                "source_excerpt": str(p.get("source_excerpt") or "")[:320]}
               for p in candidates]
    prompt = json.dumps({"location_context": "Sydney, Australia pilot", "topic": topic, "preference": preference,
                         "count": count, "candidates": compact}, ensure_ascii=False)
    if len(prompt) > MAX_DISCOVERY_PROMPT_CHARS:
        raise AiExhaustedError("candidate discovery exceeds the prompt service limit")
    offered = {p["id"] for p in candidates}
    for attempt in range(2):
        try:
            raw = _call_openai(prompt, schema=DISCOVERY_SCHEMA,
                               system_prompt=DISCOVERY_SYSTEM_PROMPT)
            try:
                parsed = json.loads(raw)
                ids = parsed["candidate_ids"]
            except (ValueError, KeyError, TypeError) as exc:
                raise AiSelectionError("invalid discovery response shape") from exc
            if (not isinstance(parsed, dict) or set(parsed) != {"candidate_ids"}
                    or not isinstance(ids, list) or len(ids) != count
                    or any(not isinstance(id_, str) for id_ in ids)
                    or len(set(ids)) != len(ids) or not set(ids) <= offered):
                raise AiSelectionError("discovery must return exactly the requested unique offered IDs")
            return ids
        except AiFatalError:
            raise
        except AiSelectionError as exc:
            if attempt == 1:
                raise AiExhaustedError("candidate discovery failed after 2 attempts") from exc
            feedback = "\nPrevious response failed: " + str(exc)[:200] + ". Return exactly the requested count of unique offered IDs."
            if len(prompt) + len(feedback) > MAX_DISCOVERY_PROMPT_CHARS:
                raise AiExhaustedError("candidate discovery retry exceeds the prompt service limit") from exc
            prompt += feedback


# =====================================================================
# CONTENT GENERATION (Story 1.3, architecture AD-3)
# =====================================================================

CONTENT_SYSTEM_PROMPT = (
    "You write short content for stops on a walking tour called Jaunt. "
    "You will be given a list of stops, each with its own name and its own "
    "evidence list - source material for that stop and nothing else.\n\n"
    "Ground every stop's content ONLY in that stop's own evidence. Never "
    "invent a name, date, number, or fact that isn't in that stop's own "
    "evidence - and never borrow a detail from a different stop, even one "
    "listed elsewhere in this same request. If a stop's evidence is very "
    "short, keep its content short and simple too - never pad it out with "
    "invented detail just to sound fuller.\n\n"
    "Some evidence entries are general background, not specific to any one "
    "stop (you can tell because they describe something broader than the "
    "stop itself, e.g. a whole suburb or a whole architectural style). If "
    "you use one, keep its information phrased as general context - never "
    "imply it is a fact specifically known about that particular stop.\n\n"
    "Write in a warm, engaging, plain voice: a short story, an interesting "
    "fact, or an observation prompt, 2-4 sentences.\n\n"
    "Each evidence entry has its own evidence_id. Along with each stop's "
    "content, list the evidence_ids you actually drew from in used_evidence_ids "
    "- every evidence_id your content's facts or phrasing came from, not every "
    "evidence_id you were merely given. Always include \"own\" (that stop's own "
    "source) unless you genuinely used nothing from it.\n\n"
    "Respond using only the required JSON schema - no extra commentary."
)

# Forces one content string per requested stop_id, keyed explicitly - keeps
# per-stop evidence scoped in the request itself, not just checked after
# the fact (see generate_stop_content()'s module-level note on cross-stop
# leakage). used_evidence_ids (Codex review 2026-10-20) makes attribution
# reflect sources actually drawn from, not merely offered - without this,
# a stop generated purely from its own excerpt could still get credited
# with an unrelated Contextual Source just because one happened to be
# available for that topic.
CONTENT_SCHEMA = {
    "name": "stop_content_batch",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "stops": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "stop_id": {"type": "string"},
                        "content": {"type": "string"},
                        "used_evidence_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["stop_id", "content", "used_evidence_ids"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["stops"],
        "additionalProperties": False,
    },
}


def load_contextual_sources(path=CONTEXTUAL_SOURCES_PATH):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("sources", [])
    except (json.JSONDecodeError, OSError, AttributeError) as exc:
        # Codex review 2026-10-21: a corrupted/malformed file must degrade
        # the same way a missing one already does (no contextual sources
        # available), not crash generate_stop_content() before it even
        # reaches its own try/except - that would break the "never raises"
        # guarantee over a file this function doesn't control the content
        # of. AttributeError covers a valid-JSON-but-wrong-shape file (e.g.
        # a bare list instead of an object with "sources").
        print(f"Could not read {path}, treating as no Contextual Sources available: {exc}")
        return []


def get_contextual_sources(stop, topic):
    """Given a Stop and the requested Topic, returns a list of candidate
    Contextual Source entries whose own topics include the requested Topic
    - a fixed contract (architecture AD-3) deliberately kept behind this one
    function. V1's body is a simple filter over the small, human-curated
    data/contextual_sources.json seed file; a later real retrieval system
    (vector search, live web/API search) can replace only this function's
    internals without touching content generation, the grounding check, the
    payload shape, or any caller. `stop` is accepted (not just `topic`) to
    keep that door open even though V1's filter doesn't use it yet.
    """
    sources = load_contextual_sources()
    matches = [s for s in sources if topic in s.get("topics", [])]
    return [
        {
            "id": s["id"],
            "source_type": s["source_type"],
            "source_title": s["source_title"],
            "source_url": s["source_url"],
            "text": s["text"],
        }
        for s in matches
    ]


_NUMBER_PATTERN = re.compile(r"\b\d{3,4}\b")


def _extract_numbers(text):
    return set(_NUMBER_PATTERN.findall(text))


def _extract_capitalized_phrases(text):
    """Runs of 2+ consecutive capitalized words - likely a specific named
    entity (a person, a place, an organisation). A lone capitalized word is
    usually just a sentence-opener ("Take a moment...") or an ordinary
    capitalized noun, not a specific claim - validated against real
    generated content and hand-fabricated bad examples before this design
    was settled on, not assumed (see the implementation spec's Design
    Notes). Sentence-ending punctuation (.!?) breaks a run, so a new
    sentence's capitalized opener never merges with the previous sentence's
    real phrase; a comma does not break a run, so "Newtown, New South
    Wales" stays one phrase.
    """
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]*|[.!?]", text)
    phrases = set()
    run = []
    for tok in tokens:
        if tok in ".!?":
            if len(run) >= 2:
                phrases.add(" ".join(run))
            run = []
        elif tok[0].isupper():
            run.append(tok)
        else:
            if len(run) >= 2:
                phrases.add(" ".join(run))
            run = []
    if len(run) >= 2:
        phrases.add(" ".join(run))
    return phrases


def _normalize_letters(text):
    """Letters-only, lowercased, space-joined - so a phrase built by the
    letters-only extractor above ("newtown new south wales") still matches
    source text that has a comma in it ("Newtown, New South Wales"), since
    that's the same claim, not an unsupported one."""
    return " ".join(re.findall(r"[a-z']+", text.lower()))


def check_grounding(generated_text, source_texts):
    """Fast rule-based (non-LLM) PRE-FILTER: does generated_text contain any
    number or multi-word capitalized phrase that isn't present anywhere in
    source_texts? Deliberately generic (arbitrary text in, a list of
    arbitrary source texts in, bool out) - no assumption anywhere in here
    about a "Stop" shape.

    Validated against real generated content (including this story's own
    AC-named thin excerpts, "By Michael Snape." and "church in Newtown,
    New South Wales") and hand-fabricated bad examples with an invented
    date/name - 6/6 correct across three independent runs. See the
    implementation spec's Design Notes for the two bugs found and fixed
    during that process.

    NOT the sole grounding mechanism (Codex review 2026-10-20, confirmed
    with concrete counterexamples): this only catches fabricated dates and
    named entities. It cannot catch a fabricated CLAIM, EVENT, or
    RELATIONSHIP that introduces no new number or multi-word proper noun -
    e.g. against the source "By Michael Snape.", both "This sculpture
    commemorates workers killed in a factory fire." (no checkable tokens
    at all) and "Michael Snape designed this church." (the name is real,
    the relationship is invented) pass this check cleanly. This function
    now exists only as a cheap pre-filter: used to skip the real
    (LLM-based) check in check_grounding_semantic() for content that's
    already obviously bad, never as the final word that content is safe to
    show. See check_grounding_semantic() for the actual gate.
    """
    combined_source = " ".join(source_texts)
    source_normalized = _normalize_letters(combined_source)

    unsupported_numbers = _extract_numbers(generated_text) - _extract_numbers(combined_source)

    gen_phrases = _extract_capitalized_phrases(generated_text)
    unsupported_phrases = {
        p for p in gen_phrases if _normalize_letters(p) not in source_normalized
    }

    return not unsupported_numbers and not unsupported_phrases


GROUNDING_CHECK_SYSTEM_PROMPT = (
    "You are a strict fact-checker. You will be given a list of items, "
    "each with its own content and its own evidence. For each item, decide "
    "whether EVERY claim, relationship, and event in its content is "
    "directly stated or reasonably implied by its own evidence - not just "
    "whether the same words/names/dates appear.\n\n"
    "Mark an item unsupported if it invents or misstates what something "
    "is, what happened, who did what, why, or how something connects, "
    "even when it reuses real names or dates from the evidence in a new "
    "or incorrect way. Some evidence is general background, not specific "
    "to that item - if the content presents that general information as a "
    "specific fact about the item itself, mark it unsupported too.\n\n"
    "Judge each item only against its own evidence, never against another "
    "item's evidence in this same list.\n\n"
    "Respond using only the required JSON schema - no extra commentary."
)

GROUNDING_CHECK_SCHEMA = {
    "name": "grounding_check_batch",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string"},
                        "supported": {"type": "boolean"},
                    },
                    "required": ["item_id", "supported"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["items"],
        "additionalProperties": False,
    },
}


def _call_grounding_check_batch(items):
    """One batched OpenAI call checking every (item_id, content,
    source_texts) tuple in items, each against only its OWN source_texts -
    the same per-item isolation discipline as content generation, for the
    same reason (Codex review 2026-10-20: pooled evidence in one call must
    never let one item's content get verified against a different item's
    source material). Returns {item_id: bool}; an item_id missing from the
    response is simply absent from the returned dict - callers decide what
    that means (generate_stop_content() treats "no verdict" as
    unsupported, matching its "never show unless genuinely confirmed"
    policy).

    Raises AiSelectionError/AiFatalError the same way _call_openai() and
    _call_content_generation() do.
    """
    request_details = {
        "items": [
            {"item_id": item_id, "content": content, "evidence": source_texts}
            for item_id, content, source_texts in items
        ],
    }
    prompt = (
        "Check each item's content against its own evidence only.\n\n"
        + json.dumps(request_details, indent=2)
    )

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
                    {"role": "system", "content": GROUNDING_CHECK_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": GROUNDING_CHECK_SCHEMA,
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

    try:
        body = response.json()
        raw_content = body["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AiSelectionError(f"unexpected OpenAI response shape: {exc}") from exc

    try:
        parsed = json.loads(raw_content)
        result_items = parsed["items"]
        if not isinstance(result_items, list):
            raise AiSelectionError(f"AI response 'items' was not a list: {result_items!r}")
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AiSelectionError(f"AI response was not the expected JSON shape: {exc}") from exc

    # Same discipline as _call_content_generation(): a malformed individual
    # entry is skipped (missing from the returned dict), never a reason to
    # crash the whole batch.
    result = {}
    for item in result_items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("item_id")
        supported = item.get("supported")
        if not isinstance(item_id, str) or not isinstance(supported, bool):
            continue
        result[item_id] = supported
    return result


def check_grounding_semantic(generated_text, source_texts):
    """The real (LLM-based) grounding check, added after check_grounding()
    (the rule-based check) was proven insufficient (Codex review
    2026-10-20, confirmed with concrete counterexamples - see that
    function's docstring). A single-item convenience wrapper around
    _call_grounding_check_batch() - still exactly one API call - so this
    stays the simple, generic (text in, source list in, bool out) function
    Epic 3 can call unchanged for a single walk summary, while Story 1.3's
    own route-level use calls the batch primitive directly for real
    multi-stop efficiency (one call per route, not one per stop).

    Raises AiSelectionError/AiFatalError on a call failure - callers
    decide the fallback (generate_stop_content() falls back to the raw
    source excerpt, never showing content that couldn't be verified).
    """
    results = _call_grounding_check_batch([("item", generated_text, source_texts)])
    return results.get("item", False)


OWN_EVIDENCE_ID = "own"


def _own_source_fields(stop):
    return {
        "source_type": stop.get("source_type"),
        "source_title": stop.get("source_title"),
        "source_url": stop.get("source_url"),
    }


def _lookup_topics_for_stop(stop, topic):
    """Which topic(s) to use for this stop's Contextual Source lookup. For
    a named topic request, every stop in the route was selected for that
    topic, so the single requested topic is correct. For a surprise_me
    route, stops of any topic can appear and no seed entry is tagged
    "surprise_me" itself (Codex review 2026-10-20) - a literal single-topic
    lookup would silently return no context for every stop on that path.
    Falls back to the stop's own topics instead."""
    if topic == "surprise_me":
        return stop.get("topics") or []
    return [topic]


def _build_stop_evidence(stop, topic):
    """This stop's own evidence set - its own source fields plus whatever
    Contextual Sources match this stop's applicable topic(s) - and never
    another stop's, even in the same batched request. A heritage stop can
    carry more than one topic (Story 1.2), so matches across all of this
    stop's applicable topics are gathered and deduplicated by source id."""
    own_source = dict(_own_source_fields(stop), id=OWN_EVIDENCE_ID, text=stop.get("source_excerpt") or "")
    contextual = []
    seen_ids = set()
    for lookup_topic in _lookup_topics_for_stop(stop, topic):
        for source in get_contextual_sources(stop, lookup_topic):
            if source["id"] not in seen_ids:
                seen_ids.add(source["id"])
                contextual.append(source)
    return [own_source] + contextual


def _raw_fallback_content(stop):
    return {
        "id": stop["id"],
        "content": stop.get("source_excerpt") or "",
        "attribution": [_own_source_fields(stop)],
    }


def _call_content_generation(stops_with_evidence, topic):
    """One batched OpenAI call covering every stop in stops_with_evidence.
    Each stop is keyed by its own stop_id with its OWN evidence only -
    never another stop's - both so the model itself has no pooled text to
    blend across stops, and so the grounding check afterward has a clean
    per-stop boundary to check against (Codex review 2026-10-20: a pooled
    multi-stop batch could otherwise let one stop's content borrow a fact
    that's only true of a different stop's source material).

    Raises AiSelectionError/AiFatalError the same way _call_openai() does -
    generate_stop_content() is the one that decides what a failure means
    for content generation (always: fall back to raw excerpts), which is
    deliberately different from how planner.py treats a fatal selection
    error (there, no route exists at all without a successful selection;
    here, the route is already complete without content generation
    succeeding - AD-3's whole point is that a generation hiccup never
    costs the user an otherwise-good route).
    """
    request_details = {
        "topic": topic,
        "stops": [
            {"stop_id": stop["id"], "name": stop.get("name"), "evidence": evidence}
            for stop, evidence in stops_with_evidence
        ],
    }
    prompt = (
        "Write content for each stop below, grounded only in its own evidence.\n\n"
        + json.dumps(request_details, indent=2)
    )

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
                    {"role": "system", "content": CONTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": CONTENT_SCHEMA,
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

    try:
        body = response.json()
        raw_content = body["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AiSelectionError(f"unexpected OpenAI response shape: {exc}") from exc

    try:
        parsed = json.loads(raw_content)
        stops = parsed["stops"]
        if not isinstance(stops, list):
            raise AiSelectionError(f"AI response 'stops' was not a list: {stops!r}")
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AiSelectionError(f"AI response was not the expected JSON shape: {exc}") from exc

    # A malformed INDIVIDUAL entry (missing/non-string content, non-string
    # stop_id, blank content) is skipped, not a reason to fail the whole
    # batch (Codex review 2026-10-21: the former unguarded dict
    # comprehension raised an uncaught TypeError/KeyError on exactly this).
    # A skipped stop_id is simply absent below, which generate_stop_content()
    # already treats as "missing from the response" and falls back for -
    # no new fallback path needed, just not crashing on the way there.
    result = {}
    for s in stops:
        if not isinstance(s, dict):
            continue
        stop_id = s.get("stop_id")
        content = s.get("content")
        if not isinstance(stop_id, str) or not isinstance(content, str) or not content.strip():
            continue
        # Codex review 2026-10-21: used_evidence_ids: null (present but not
        # a list) raised an uncaught TypeError iterating it - a less
        # destructive degradation than discarding the whole entry, since
        # the content itself can still be perfectly good even if its
        # citation declaration is malformed; attribution always includes
        # the stop's own source regardless (see generate_stop_content()).
        raw_used_ids = s.get("used_evidence_ids", [])
        used_evidence_ids = [e for e in raw_used_ids if isinstance(e, str)] if isinstance(raw_used_ids, list) else []
        result[stop_id] = {"content": content, "used_evidence_ids": used_evidence_ids}
    return result


def generate_stop_content(stops, topic):
    """The real entry point future stories call: generates grounded,
    checked content for every stop in a route, one batched generation call
    plus (for whatever survives the cheap pre-filter) one batched semantic
    grounding call - never N per-stop calls of either kind. Never raises -
    every failure mode falls that stop back to its own raw source_excerpt,
    so a content-generation or grounding-check hiccup never fails an
    otherwise-feasible route (architecture AD-3). Content is only ever
    shown once check_grounding_semantic() has genuinely confirmed it - the
    cheap rule-based check_grounding() is a pre-filter only (Codex review
    2026-10-20: it cannot catch a fabricated claim/relationship that
    introduces no new date or name - see its own docstring), never the
    final word.

    Each stop's result: {"id", "content", "attribution"}, where attribution
    is a list of {"source_type", "source_title", "source_url"} covering
    only the evidence the model actually declared using - a stop generated
    purely from its own excerpt never gets credited with an unrelated
    Contextual Source just because one happened to be available. The
    stop's own source is always included unless the model explicitly used
    nothing from it; a declared id never actually offered to that stop is
    silently ignored, never trusted.
    """
    stops_with_evidence = [(stop, _build_stop_evidence(stop, topic)) for stop in stops]

    try:
        generated_by_id = _call_content_generation(stops_with_evidence, topic)
    except AiSelectionError:
        return [_raw_fallback_content(stop) for stop in stops]

    # First pass: the cheap pre-filter only decides who's even worth the
    # real check's cost - never who's safe to show.
    candidates = []  # (stop, evidence, generated_content, evidence_texts)
    fallback_stops = []
    for stop, evidence in stops_with_evidence:
        generated = generated_by_id.get(stop["id"])
        if generated is None:
            fallback_stops.append(stop)
            continue
        # Both grounding checks verify against exactly the evidence that
        # will actually be cited (used_evidence_ids, always including the
        # stop's own source) - never every source merely offered. Codex
        # review 2026-10-21: verifying against the full offered set while
        # attribution lists only declared-used sources let a claim
        # supported solely by an undeclared Contextual Source pass
        # verification while that source never appeared in its citations.
        # The stop's own real name is also legitimate grounding material -
        # referring to a place by its actual name isn't fabrication
        # (prototype bug #2, see Design Notes).
        used_ids = set(generated["used_evidence_ids"]) | {OWN_EVIDENCE_ID}
        cited_evidence = [e for e in evidence if e["id"] in used_ids]
        evidence_texts = [e["text"] for e in cited_evidence] + [stop.get("name") or ""]
        if not check_grounding(generated["content"], evidence_texts):
            fallback_stops.append(stop)
            continue
        candidates.append((stop, evidence, generated, evidence_texts))

    # Second pass: the real check, one batched call for everyone who
    # passed the pre-filter. Any failure to get an authoritative
    # "supported" verdict - a call failure, or an explicit "not
    # supported" - falls back, never defaults to trusting the cheap
    # filter alone.
    semantic_verdicts = {}
    if candidates:
        try:
            semantic_verdicts = _call_grounding_check_batch(
                [(stop["id"], generated["content"], evidence_texts)
                 for stop, _evidence, generated, evidence_texts in candidates]
            )
        except AiSelectionError:
            semantic_verdicts = {}

    results = []
    for stop, evidence, generated, _evidence_texts in candidates:
        if not semantic_verdicts.get(stop["id"], False):
            results.append(_raw_fallback_content(stop))
            continue
        used_ids = set(generated["used_evidence_ids"]) | {OWN_EVIDENCE_ID}
        attribution = [
            {k: e[k] for k in ("source_type", "source_title", "source_url")}
            for e in evidence
            if e["id"] in used_ids
        ]
        results.append({"id": stop["id"], "content": generated["content"], "attribution": attribution})
    results.extend(_raw_fallback_content(stop) for stop in fallback_stops)

    # Restore original stop order - the two passes above processed
    # candidates and fallbacks as separate groups.
    order = {stop["id"]: i for i, stop in enumerate(stops)}
    results.sort(key=lambda r: order[r["id"]])
    return results
