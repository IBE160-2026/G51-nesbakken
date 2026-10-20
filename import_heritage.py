"""Third candidate-place source, for a new `heritage` topic: a small, hand-
curated list of 29 real NSW heritage items (7 State Heritage Register, 22
locally-listed under a council LEP) in and around the Newtown pilot area.
See docs/ai-development-log.md for how this list was chosen.

Unlike import_places.py and import_street_art.py, this importer does not
scrape or fetch descriptive text automatically. NSW's official heritage
description text (Statement of Significance) lives only in an interactive
web application (hms.heritage.nsw.gov.au) protected by a WAF that blocks any
client identifying itself honestly as a script - confirmed directly, not
assumed. Spoofing a browser identity to get past that was explicitly ruled
out. Instead, source text is read from data/heritage_source_text.json, a
small file a human fills in by hand from the public HMS page for each
approved item. An item with no text recorded there stays `limited`, never
`ready` - this importer never falls back to Description/History and never
invents an excerpt.

Coordinates and item names come directly from the official ArcGIS Heritage
MapServer (Layer 5 for the State items, Layer 4 for the Local items) - no
geocoding needed. Rerunning this script is safe: it always rebuilds all 29
records from ArcGIS and the current seed file, so an edit to the seed file
takes effect on the next run without any stale-cache logic to reason about.
"""

import json
import os
import time

import requests

from import_places import USER_AGENT, load_existing, mark_duplicates, save_records

MAPSERVER_URL = "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/HMS/Heritage/MapServer"
LAYER_STATE_HERITAGE_REGISTER = f"{MAPSERVER_URL}/5"
LAYER_LOCAL_ENVIRONMENTAL_PLAN = f"{MAPSERVER_URL}/4"

SEED_PATH = os.path.join("data", "heritage_source_text.json")
HMS_URL_TEMPLATE = "https://www.hms.heritage.nsw.gov.au/App/Item/ViewItem?itemId={item_id}"

SOURCE_TYPE = "nsw_state_heritage_inventory"
TOPIC = "heritage"

# The 29 items approved after manual review of the ArcGIS structured data -
# see docs/ai-development-log.md for how these were chosen (geographic
# spread + type variety: pubs, theatres, rail infrastructure, churches,
# named houses/terraces, civic and commercial buildings).
APPROVED_STATE_HOITEMIDS = [
    5012123, 5045004, 5068106, 5045003, 5012222, 5045479, 5063046,
]
APPROVED_LOCAL_HERITAGE_ITEM_IDS = [
    2030465, 6002413, 2423037, 2420715, 2420858, 2030116, 2420318,
    2030085, 2420855, 2420716, 2030126, 2030281, 2030110, 2420005,
    2420851, 2030114, 2030147, 2421330, 2030138, 2030102, 2030377,
    2030108,
]

# Manually reviewed cross-source duplicates: the same real building exists in
# both import_places.py's OSM import and this heritage import. Unlike
# import_street_art.py's CROSS_SOURCE_DUPLICATES (where the OSM record is
# kept), the heritage record is kept here - it carries the official NSW
# Statement of Significance, whereas the OSM record's excerpt is at best a
# general-purpose Wikipedia/Wikidata summary, not a heritage-authority
# assessment. Keeping both would also let the same physical building appear
# twice in a "surprise_me" walk, which doesn't filter by topic.
CROSS_SOURCE_DUPLICATES = {
    "way/548526874": "heritage/5045004",  # Newtown Mission / Uniting Church and Pipe Organ
    "way/172735168": "heritage/5045479",  # St Stephen's Anglican Church / ...and Cemetery
}


def query_layer(layer_url, id_field, ids, extra_where=None):
    """Fetches exactly the given ids from an ArcGIS Heritage MapServer layer.
    Returns the raw list of ArcGIS features (attributes + geometry)."""
    where = f"{id_field} IN ({','.join(str(i) for i in ids)})"
    if extra_where:
        where = f"{where} AND {extra_where}"
    response = requests.get(
        f"{layer_url}/query",
        params={
            "where": where,
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"ArcGIS query error: {data['error']}")
    return data.get("features", [])


def load_seed(path=SEED_PATH):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("items", {})


def build_record(heritage_id, name, latitude, longitude, significance_level, seed_entry):
    record = {
        "id": f"heritage/{heritage_id}",
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "topics": [TOPIC],
        "significance_level": significance_level,
        "source_type": None,
        "source_title": None,
        "source_url": None,
        "source_excerpt": None,
        "status": "rejected",
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rejection_reason": None,
    }

    if latitude is None or longitude is None:
        record["rejection_reason"] = "missing coordinates from ArcGIS"
        return record

    statement = (seed_entry or {}).get("statement_of_significance")
    # Validation only - stripped just to check for real content. The stored
    # excerpt below is always the untouched original value, never stripped.
    has_usable_statement = isinstance(statement, str) and statement.strip() != ""

    if has_usable_statement:
        record["source_type"] = SOURCE_TYPE
        record["source_title"] = name
        record["source_url"] = HMS_URL_TEMPLATE.format(item_id=heritage_id)
        record["source_excerpt"] = statement
        record["status"] = "ready"
    else:
        record["status"] = "limited"
        record["rejection_reason"] = (
            "no verbatim Statement of Significance in data/heritage_source_text.json yet"
        )

    return record


def apply_manual_duplicate_overrides(records_by_id):
    """Applies CROSS_SOURCE_DUPLICATES after the automatic mark_duplicates()
    pass. Only rejects a still-`ready` OSM record - never overrides another
    rejection reason already present, and never touches the heritage record
    being kept.

    Checked 2026-10-18 (Codex review): also requires the replacement to
    actually be `ready` before rejecting the original. Without this, a
    heritage record whose Statement of Significance hasn't been filled in
    yet (data/heritage_source_text.json) would still cause its OSM
    duplicate to be rejected, leaving the place unusable from either
    source - not currently happening with today's two real pairs (both
    replacements are ready), but a real latent risk for any future entry
    added to CROSS_SOURCE_DUPLICATES before its seed text exists.

    Fixed 2026-10-20 (symmetric recovery, user-caught): the above guard
    stops a NEW rejection when the replacement isn't ready, but on a
    rerun the OSM record is loaded via load_existing() already carrying
    whatever status a PRIOR run gave it. If that prior run rejected it
    (replacement was ready then) and the replacement has since become
    `limited` (e.g. its seed text was removed), the old guard would
    leave the OSM record stuck `rejected` forever, with no path back to
    `ready` - the place becomes permanently unusable even though the
    override that caused it no longer applies. Every rejection this
    function makes is tagged with a specific, checkable reason string,
    so a record found in that exact state is recognized as "ours" and
    restored, never silently left wrong.
    """
    override_reason_for = lambda kept_id: f"duplicate of {kept_id} (reviewed cross-source match)"
    for osm_id, kept_id in CROSS_SOURCE_DUPLICATES.items():
        record = records_by_id.get(osm_id)
        if record is None:
            continue
        replacement = records_by_id.get(kept_id)
        replacement_ready = replacement is not None and replacement.get("status") == "ready"
        override_reason = override_reason_for(kept_id)
        currently_overridden = (
            record.get("status") == "rejected"
            and record.get("rejection_reason") == override_reason
        )
        if replacement_ready and record.get("status") == "ready":
            record["status"] = "rejected"
            record["rejection_reason"] = override_reason
        elif not replacement_ready and currently_overridden:
            record["status"] = "ready"
            record["rejection_reason"] = None


def build_state_records(seed):
    features = query_layer(LAYER_STATE_HERITAGE_REGISTER, "HOITEMID", APPROVED_STATE_HOITEMIDS)
    found_ids = set()
    records = []
    for feature in features:
        attrs = feature["attributes"]
        heritage_id = int(attrs["HOITEMID"])
        found_ids.add(heritage_id)
        records.append(build_record(
            heritage_id, attrs["ITEMNAME"], attrs["Lat"], attrs["Long_"],
            "State", seed.get(str(heritage_id)),
        ))
    missing = set(APPROVED_STATE_HOITEMIDS) - found_ids
    return records, missing


def build_local_records(seed):
    features = query_layer(
        LAYER_LOCAL_ENVIRONMENTAL_PLAN, "HeritageItemID", APPROVED_LOCAL_HERITAGE_ITEM_IDS,
        extra_where="LAY_CLASS='Item - General' AND SIG='Local'",
    )

    # Some real heritage items are mapped as several points sharing one
    # HeritageItemID (see docs/ai-development-log.md) - keep only the first
    # point seen per id, same rule used during candidate research.
    first_seen = {}
    for feature in features:
        heritage_id = int(feature["attributes"]["HeritageItemID"])
        first_seen.setdefault(heritage_id, feature)

    records = []
    for heritage_id, feature in first_seen.items():
        attrs = feature["attributes"]
        geometry = feature.get("geometry", {})
        records.append(build_record(
            heritage_id, attrs["H_NAME"], geometry.get("y"), geometry.get("x"),
            "Local", seed.get(str(heritage_id)),
        ))
    missing = set(APPROVED_LOCAL_HERITAGE_ITEM_IDS) - set(first_seen)
    return records, missing


def main():
    seed = load_seed()
    filled = sum(1 for entry in seed.values() if entry.get("statement_of_significance"))
    print(f"Loaded {SEED_PATH}: {len(seed)} entries, {filled} with a Statement of Significance.")

    print("Querying the State Heritage Register layer for the approved items...")
    state_records, missing_state = build_state_records(seed)

    print("Querying the Local Environmental Plan layer for the approved items...")
    local_records, missing_local = build_local_records(seed)

    if missing_state or missing_local:
        print(
            "\nAborting: ArcGIS did not return all approved heritage ids. "
            "Not saving data/sydney_places.json, so a partial import is never "
            "mistaken for a successful one."
        )
        for hid in sorted(missing_state):
            print(f"  missing State HOITEMID {hid}")
        for hid in sorted(missing_local):
            print(f"  missing Local HeritageItemID {hid}")
        raise SystemExit(1)

    records_by_id = dict(load_existing())
    for record in state_records + local_records:
        records_by_id[record["id"]] = record

    mark_duplicates(list(records_by_id.values()))
    apply_manual_duplicate_overrides(records_by_id)
    save_records(records_by_id)

    heritage_records = state_records + local_records
    counts = {"ready": 0, "limited": 0, "rejected": 0}
    missing_text = []
    for r in heritage_records:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        if r["status"] == "limited":
            missing_text.append(r["id"])

    print("\nHeritage import complete.")
    print(f"  ready:    {counts['ready']}")
    print(f"  limited:  {counts['limited']}")
    print(f"  rejected: {counts['rejected']}")

    if missing_text:
        print("\nMissing verbatim Statement of Significance (needs manual retrieval):")
        for rid in missing_text:
            print(f"  {rid}")

    print(f"\nSaved to {os.path.join('data', 'sydney_places.json')}")


if __name__ == "__main__":
    main()
