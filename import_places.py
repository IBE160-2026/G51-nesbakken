"""Sprint 1: bulk-import candidate places for the Newtown pilot area.

Queries OpenStreetMap (via Overpass) for real, tagged places, assigns each a
broad topic using simple tag rules, looks up a short Wikipedia summary where
one exists, and writes the result to data/sydney_places.json.

Rerunning this script resumes from the existing catalogue: already-`ready`
records are reused as-is, but `limited` records are retried, since a `limited`
status can mean either "genuinely no source exists" or "the request failed" -
V1 does not distinguish those, so it is cheaper and safer to just retry.
"""

import json
import math
import os
import time
import urllib.parse

import requests

from pilot_config import LANGUAGE, PILOT_BBOX

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
WIKIPEDIA_SUMMARY_URL = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
USER_AGENT = "Jaunt-Student-Project/0.1 (IBE160 coursework)"

# OSM tags that carry real, attributable descriptive facts about a place,
# used as enrichment when no Wikipedia/Wikidata article exists.
OSM_DESCRIPTIVE_KEYS = ("inscription", "subject", "artist_name", "start_date")

OUTPUT_PATH = os.path.join("data", "sydney_places.json")

# Records with the same name within this distance are treated as the same
# physical place (e.g. a monument's node and the way around its base) and
# only the better-sourced one is kept. This is approximate, not exact
# OSM entity resolution.
DUPLICATE_DISTANCE_METERS = 75

OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:180];
(
  node["historic"]({bbox});
  way["historic"]({bbox});
  node["heritage"]({bbox});
  way["heritage"]({bbox});
  node["tourism"="artwork"]({bbox});
  way["tourism"="artwork"]({bbox});
  node["artwork_type"]({bbox});
  way["artwork_type"]({bbox});
  node["architect"]({bbox});
  way["architect"]({bbox});
  way["building"="church"]({bbox});
  way["building"="cathedral"]({bbox});
);
out center tags;
"""


def fetch_overpass_elements(bbox):
    south, west, north, east = bbox
    query = OVERPASS_QUERY_TEMPLATE.format(bbox=f"{south},{west},{north},{east}")
    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={"User-Agent": USER_AGENT},
        timeout=200,
    )
    response.raise_for_status()
    return response.json()["elements"]


def place_id(element):
    return f"{element['type']}/{element['id']}"


def coordinates(element):
    """Nodes have lat/lon directly; ways/relations need the 'center' Overpass adds."""
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    center = element.get("center")
    if center:
        return center["lat"], center["lon"]
    return None, None


def assign_topics(tags):
    """Simple, documented OSM-tag rules - see docs/architecture-plan.md.

    memorial (added for Story 4.3, 2026-10-30) is additive with history - a
    memorial stays history too, since a war memorial or a statue of a
    historical figure genuinely is history, not a separate interest
    (user's explicit call, checked against the 60% dilution this would
    otherwise cause - see commit history).

    sculpture is exclusive with public_art, not additive - checked
    directly against the real catalogue: sculptures/statues were 39% of
    all public_art results, which would bury anyone specifically looking
    for murals/street art under landmark statues. "statue" is folded into
    "sculpture" (a statue is a kind of sculpture in ordinary language).

    Known, accepted limitation: this tag-based rule cannot tell an
    "artsy" sculpture from a landmark/historical-figure statue - both are
    just artwork_type=sculpture|statue in OSM with no further distinction
    available (e.g. "Major General Lachlan Macquarie" and "Progress Pride
    Beacon" are tagged identically). Not solved here - flagged, not
    quietly ignored."""
    topics = set()
    if "historic" in tags or "heritage" in tags:
        topics.add("history")
    if tags.get("historic") == "memorial":
        topics.add("memorial")
    if tags.get("building") in ("church", "cathedral"):
        topics.add("architecture")
        topics.add("history")
    if "architect" in tags:
        topics.add("architecture")
    if tags.get("artwork_type") in ("sculpture", "statue"):
        topics.add("sculpture")
    elif tags.get("tourism") == "artwork" or "artwork_type" in tags:
        topics.add("public_art")
    return sorted(topics)


def parse_wikipedia_tag(wikipedia_tag):
    """Returns (language, title). OSM's wikipedia tag is usually
    'en:Some Title', occasionally just 'Some Title' (assumed to be in the
    pilot area's configured LANGUAGE)."""
    if ":" in wikipedia_tag:
        lang, title = wikipedia_tag.split(":", 1)
        return lang.strip().lower(), title.strip()
    return LANGUAGE, wikipedia_tag.strip()


def truncate_excerpt(text, max_length=500):
    """Cuts at the last sentence boundary within max_length where possible,
    rather than mid-sentence."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_period = truncated.rfind(". ")
    if last_period > 0:
        return truncated[: last_period + 1]
    return truncated.rstrip() + "..."


def fetch_wikipedia_summary(title):
    url = WIKIPEDIA_SUMMARY_URL.format(lang=LANGUAGE, title=urllib.parse.quote(title))
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    if response.status_code != 200:
        return None
    data = response.json()
    extract = data.get("extract")
    if not extract:
        return None
    return {
        "source_type": "wikipedia",
        "source_title": data.get("title", title),
        "source_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "source_excerpt": truncate_excerpt(extract),
    }


def fetch_wikidata_description(qid):
    """Wikidata's own short description in the pilot area's configured
    LANGUAGE - broader coverage than Wikipedia's notability bar, still a
    real, citable source."""
    params = {
        "action": "wbgetentities",
        "ids": qid,
        "props": "labels|descriptions",
        "languages": LANGUAGE,
        "format": "json",
    }
    response = requests.get(
        WIKIDATA_API_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=15
    )
    if response.status_code != 200:
        return None
    entity = response.json().get("entities", {}).get(qid)
    if not entity:
        return None
    description = entity.get("descriptions", {}).get(LANGUAGE, {}).get("value")
    if not description:
        return None
    label = entity.get("labels", {}).get(LANGUAGE, {}).get("value")
    return {
        "source_type": "wikidata",
        "source_title": label or qid,
        "source_url": f"https://www.wikidata.org/wiki/{qid}",
        "source_excerpt": description,
    }


# Words common enough to appear in a generic Wikidata category description
# AND coincidentally in a place's own name - matching on these alone proves
# nothing, so they're excluded from the "does it actually name this place"
# check below (Story 4.3 follow-up, 2026-10-30: walk summaries were
# silently failing grounding because a thin Wikidata description like
# "historic national heritage site in Sydney NSW" never names the specific
# place it's describing).
WIKIDATA_GENERIC_WORDS = {
    "church", "war", "memorial", "monument", "sculpture", "historic", "heritage",
    "site", "national", "museum", "building", "structure", "artwork", "roundabout",
    "nsw", "new", "south", "wales", "sydney", "australia", "cathedral", "chapel",
    "house", "park", "hotel", "theatre", "school", "office", "regimental", "royal",
}


def wikidata_description_names_place(excerpt, name):
    """True if excerpt contains at least one real, specific word from name -
    not just a generic category word every similar place's description
    would also contain. A category-only description ("war memorial in
    Sydney") doesn't confirm which specific war memorial this is."""
    if not excerpt or not name:
        return False
    words = [w.strip(".,").lower() for w in name.split() if len(w.strip(".,")) >= 4]
    words = [w for w in words if w not in WIKIDATA_GENERIC_WORDS]
    excerpt_lower = excerpt.lower()
    return any(w in excerpt_lower for w in words)


def build_osm_tag_excerpt(tags, record_id):
    """Composes a short factual excerpt directly from OSM's own descriptive
    tags - real, attributable data (an OSM contributor's entry, citable by
    the element's own URL), not generated text. Used only when neither
    Wikipedia nor Wikidata provided anything usable."""
    parts = []
    if tags.get("inscription"):
        parts.append(f'Inscription: "{tags["inscription"]}"')
    if tags.get("subject"):
        parts.append(f"Subject: {tags['subject']}")
    if tags.get("artist_name") and tags.get("start_date"):
        parts.append(f"By {tags['artist_name']}, {tags['start_date']}")
    elif tags.get("artist_name"):
        parts.append(f"By {tags['artist_name']}")
    elif tags.get("start_date"):
        parts.append(f"Dated {tags['start_date']}")

    if not parts:
        return None
    return {
        "source_type": "osm_tags",
        "source_title": None,
        "source_url": f"https://www.openstreetmap.org/{record_id}",
        "source_excerpt": ". ".join(parts) + ".",
    }


def build_record(element, existing):
    record_id = place_id(element)
    if record_id in existing:
        cached = existing[record_id]
        if cached.get("status") == "ready":
            return cached  # already has a real source, nothing to redo
        if (cached.get("rejection_reason") or "").startswith("duplicate of"):
            return cached  # already resolved as a duplicate, nothing to redo
        # otherwise (limited/rejected for another reason): retry below, since
        # a limited status can mean "no source exists" or "the request
        # failed", and V1 doesn't distinguish those - retrying is cheap.

    tags = element.get("tags", {})
    name = tags.get("name")
    lat, lon = coordinates(element)
    topics = assign_topics(tags)

    record = {
        "id": record_id,
        "name": name,
        "latitude": lat,
        "longitude": lon,
        "osm_type": element["type"],
        "osm_tags": tags,
        "topics": topics,
        "source_type": None,
        "source_title": None,
        "source_url": None,
        "source_excerpt": None,
        "status": "rejected",
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rejection_reason": None,
    }

    if not name or lat is None or lon is None or not topics:
        record["rejection_reason"] = "missing name, coordinates, or a matching topic"
        return record

    summary = None
    non_english_reason = None

    # 1. Wikipedia, in the pilot area's configured LANGUAGE only - the
    # richest source where it exists.
    wikipedia_tag = tags.get("wikipedia")
    if wikipedia_tag:
        lang, title = parse_wikipedia_tag(wikipedia_tag)
        if lang == LANGUAGE:
            try:
                summary = fetch_wikipedia_summary(title)
            except requests.RequestException:
                summary = None
            time.sleep(0.2)  # be polite to a free public API
        else:
            non_english_reason = f"wikipedia tag is in '{lang}', only '{LANGUAGE}' is supported in V1"

    # 2. Wikidata's short description - broader coverage than Wikipedia's
    # notability bar, for records with a wikidata tag but no usable article.
    if not summary:
        wikidata_id = tags.get("wikidata")
        if wikidata_id:
            try:
                summary = fetch_wikidata_description(wikidata_id)
            except requests.RequestException:
                summary = None
            time.sleep(0.2)
            # A generic category-only description ("church in New South
            # Wales") doesn't actually confirm this record IS that specific
            # place - not enough to call it ready, see
            # wikidata_description_names_place()'s own docstring.
            if summary and not wikidata_description_names_place(summary["source_excerpt"], name):
                summary = None

    # 3. OSM's own descriptive tags - real, attributable facts an OSM
    # contributor entered directly, used only if nothing above worked.
    if not summary:
        summary = build_osm_tag_excerpt(tags, record_id)

    if summary:
        record.update(summary)
        record["status"] = "ready"
    else:
        record["status"] = "limited"
        record["rejection_reason"] = (
            non_english_reason or "no usable Wikipedia, Wikidata, or OSM source found"
        )

    return record


def normalize_name(name):
    return name.strip().lower() if name else ""


def haversine_meters(lat1, lon1, lat2, lon2):
    radius = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def mark_duplicates(records):
    """Approximate: records with the same name within DUPLICATE_DISTANCE_METERS
    of a better-sourced record are marked as rejected duplicates rather than
    removed, so the catalogue stays auditable. Not exact entity resolution."""
    rank = {"ready": 2, "limited": 1, "rejected": 0}
    nameable = [
        r for r in records
        if normalize_name(r.get("name")) and r.get("latitude") is not None
    ]
    nameable.sort(key=lambda r: rank[r["status"]], reverse=True)

    kept = []
    for record in nameable:
        if (record.get("rejection_reason") or "").startswith("duplicate of"):
            continue  # resolved in an earlier run; leave it as-is
        match = None
        for other in kept:
            if normalize_name(record["name"]) != normalize_name(other["name"]):
                continue
            if haversine_meters(
                record["latitude"], record["longitude"],
                other["latitude"], other["longitude"],
            ) <= DUPLICATE_DISTANCE_METERS:
                match = other
                break
        if match is None:
            kept.append(record)
        else:
            record["status"] = "rejected"
            record["rejection_reason"] = f"duplicate of {match['id']}"
    return records


def load_existing():
    if not os.path.exists(OUTPUT_PATH):
        return {}
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        return {r["id"]: r for r in json.load(f)}


def save_records(records_by_id):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    temp_path = OUTPUT_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(list(records_by_id.values()), f, indent=2, ensure_ascii=False)
    os.replace(temp_path, OUTPUT_PATH)  # atomic: no partially-written file on interruption


def main():
    print("Querying Overpass for the Newtown pilot area...")
    elements = fetch_overpass_elements(PILOT_BBOX)
    print(f"Overpass returned {len(elements)} candidate elements.")

    existing = load_existing()
    records_by_id = dict(existing)

    for i, element in enumerate(elements, start=1):
        record = build_record(element, existing)
        records_by_id[record["id"]] = record
        if i % 10 == 0:
            save_records(records_by_id)
            print(f"  processed {i}/{len(elements)}...")

    mark_duplicates(list(records_by_id.values()))
    save_records(records_by_id)

    counts = {"ready": 0, "limited": 0, "rejected": 0}
    for r in records_by_id.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    print("\nImport complete.")
    print(f"  ready:    {counts['ready']}")
    print(f"  limited:  {counts['limited']}")
    print(f"  rejected: {counts['rejected']}")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
