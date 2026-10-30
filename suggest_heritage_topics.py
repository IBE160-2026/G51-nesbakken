"""AI-assisted first pass for Story 1.2's human-reviewed heritage Topics.

Reads each heritage item that has real source text (data/heritage_source_text.json)
but no entry yet in data/heritage_topic_overrides.json, and asks AI to suggest
which of history/architecture its own Statement of Significance text actually
supports - with a one-line reason, so a person can check the suggestion
against the text quickly rather than deciding from scratch.

This never writes heritage_topic_overrides.json directly. Story 1.2's own
rule stands: a Topic only becomes real once a person puts it in that file.
This script only writes data/heritage_topic_suggestions.json, a separate,
clearly-unreviewed draft - import_heritage.py never reads it.
"""

import json
import os

from ai import AiFatalError, AiSelectionError, _call_openai

SOURCE_TEXT_PATH = os.path.join("data", "heritage_source_text.json")
OVERRIDES_PATH = os.path.join("data", "heritage_topic_overrides.json")
SUGGESTIONS_PATH = os.path.join("data", "heritage_topic_suggestions.json")

SYSTEM_PROMPT = (
    "You classify a single NSW heritage item's Topics from its own official "
    "Statement of Significance text only. Valid topics are 'history' and "
    "'architecture' - either, both, or neither if the text genuinely supports "
    "none. Never invent a topic the text doesn't support just to avoid an "
    "empty list. Give one short, concrete reason quoting or closely "
    "paraphrasing the text, so a human reviewer can check your answer "
    "against it quickly."
)

TOPIC_SUGGESTION_SCHEMA = {
    "name": "heritage_topic_suggestion", "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "topics": {
                "type": "array",
                "items": {"type": "string", "enum": ["history", "architecture"]},
            },
            "reason": {"type": "string"},
        },
        "required": ["topics", "reason"],
        "additionalProperties": False,
    },
}


def load_json_field(path, field):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get(field, {})


def suggest_topics(item_name, statement_of_significance):
    """Returns {"topics": [...], "reason": str}. Raises AiFatalError/
    AiSelectionError on failure - same error types ai.py's other callers use,
    left for main() to report rather than silently guessing a topic."""
    prompt = json.dumps({
        "item_name": item_name,
        "statement_of_significance": statement_of_significance,
    }, ensure_ascii=False)
    raw = _call_openai(prompt, schema=TOPIC_SUGGESTION_SCHEMA, system_prompt=SYSTEM_PROMPT)
    try:
        parsed = json.loads(raw)
        return {"topics": parsed["topics"], "reason": parsed["reason"]}
    except (ValueError, KeyError, TypeError) as exc:
        raise AiSelectionError("invalid heritage topic suggestion response shape") from exc


def main():
    source_text = load_json_field(SOURCE_TEXT_PATH, "items")
    existing_overrides = load_json_field(OVERRIDES_PATH, "overrides")

    needs_suggestion = {
        heritage_id: entry
        for heritage_id, entry in source_text.items()
        if heritage_id not in existing_overrides
        and (entry.get("statement_of_significance") or "").strip()
    }

    if not needs_suggestion:
        print(
            "Nothing to suggest: every heritage item with source text already "
            "has a human-reviewed topic override."
        )
        return

    print(f"Suggesting topics for {len(needs_suggestion)} item(s) not yet in {OVERRIDES_PATH}...")

    suggestions = {}
    failed = []
    for heritage_id, entry in needs_suggestion.items():
        name = entry.get("item_name", heritage_id)
        try:
            result = suggest_topics(name, entry["statement_of_significance"])
        except (AiFatalError, AiSelectionError) as exc:
            print(f"  {heritage_id} ({name}): AI call failed - {exc}")
            failed.append(heritage_id)
            continue
        suggestions[heritage_id] = {
            "item_name": name,
            "suggested_topics": result["topics"],
            "reason": result["reason"],
        }
        print(f"  {heritage_id} ({name}): {result['topics']} - {result['reason']}")

    os.makedirs(os.path.dirname(SUGGESTIONS_PATH), exist_ok=True)
    with open(SUGGESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "_instructions": (
                "AI-SUGGESTED, NOT YET REVIEWED. Read each item's 'reason' "
                "against its own Statement of Significance in "
                "heritage_source_text.json, then copy only the ones you agree "
                "with into heritage_topic_overrides.json's own 'overrides' "
                "object as {\"<id>\": {\"topics\": [...]}}. import_heritage.py "
                "never reads this file directly."
            ),
            "suggestions": suggestions,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(suggestions)} suggestion(s) to {SUGGESTIONS_PATH} for your review.")
    if failed:
        print(f"{len(failed)} item(s) failed and were skipped: {failed}")


if __name__ == "__main__":
    main()
