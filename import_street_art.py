"""Second candidate-place source for the public_art topic: Inner West
Council's "Perfect Match" street art dataset (data/raw/perfect-match-street-art.xlsx),
merged into the same catalogue import_places.py writes to
(data/sydney_places.json). See docs/ai-development-log.md for how this
dataset's real problems (a broken Number column, placeholder "TBC"/"CARPARK"
values, typo'd suburbs) were found and handled.

Like import_places.py, this script is resumable. Unlike import_places.py's
OSM records, every street-art record is rebuilt from the spreadsheet on
every run rather than reusing a cached `ready` record as-is: the source
spreadsheet has a friend's visibility notes that can genuinely change after
a record has already been marked `ready` (a mural found to be gone), and a
stale-ready shortcut would hide that. Only geocoding is cached (in
data/geocode_cache.json, keyed by address) - a successful lookup is reused
without a new request; a failed one is retried on the next run, since a
failure can be transient (network/HTTP error), not just "no such address".

Two things this dataset adds that import_places.py's OSM source doesn't have:

1. Coordinates aren't in the source - each artwork's Full Address is
   geocoded once via Nominatim (OpenStreetMap's geocoder), at the 1
   request/second its usage policy requires.
2. A friend annotated some rows with a Status column ("Visible" / "No
   Longer Visible"). That is not council data and must never be quoted as a
   source, so it is kept in its own `field_notes` field with its own source
   label - not in app.py's PUBLIC_FIELDS allowlist, so never sent to the
   frontend. The friend's other columns (Visited Date, Photo, KM Walked) are
   personal tracking data Jaunt has no use for and are deliberately never
   written into the catalogue at all - not even into field_notes.
"""

import json
import os
import time

import openpyxl
import requests

from import_places import (
    PILOT_BBOX,
    USER_AGENT,
    load_existing,
    mark_duplicates,
    save_records,
)

RAW_XLSX_PATH = os.path.join("data", "raw", "perfect-match-street-art.xlsx")
SHEET_NAME = "Perfect Match - Street Art"

GEOCODE_CACHE_PATH = os.path.join("data", "geocode_cache.json")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GEOCODE_DELAY_SECONDS = 1.0  # Nominatim's usage policy: max 1 request/second.

SOURCE_TYPE = "inner_west_perfect_match"
SOURCE_URL = "https://experience.arcgis.com/experience/d73d36937dfa4c829a81e5a661619fd6"
TOPIC = "public_art"

# Column letters in the source sheet, fixed by direct inspection rather than
# by header text: the sheet has two columns both labelled "Ward" (B and C -
# council ward and its Aboriginal-language name), and a derived, redundant
# column (K, "Artwork Title, by... social media and statement") that just
# concatenates D/L/M/N. Reading by column letter sidesteps both.
COL_NUMBER = "A"
COL_TITLE = "D"
COL_FULL_ADDRESS = "E"
COL_STREET_ADDRESS = "F"
COL_SUBURB = "G"
COL_YEAR = "J"
COL_ARTIST = "L"
COL_STATEMENT = "M"
COL_STATUS = "O"
# The sheet also has Visited Date (P), Photo (Q), and KM Walked (R) - the
# friend's personal tracking columns. Jaunt has no use for them, so they are
# deliberately not read at all (not even into field_notes).

# Suburb names entered inconsistently in the source spreadsheet.
SUBURB_TYPO_FIXES = {
    "ashifield": "Ashfield",
    "marrickvile": "Marrickville",
    "marricvkville": "Marrickville",
    "leichardt": "Leichhardt",
}

# Literal placeholder text found in the Artwork Title / Statement columns
# during inspection - not real content, and must not be treated as one.
# "*title" is the council's own "no title recorded" marker (distinct from
# "Untitled", which is a real, deliberate artwork title used elsewhere in
# the same sheet and is left alone).
PLACEHOLDER_VALUES = {"tbc", "carpark", "*title"}

# Manually reviewed cross-source duplicates: the same real artwork exists in
# both this dataset and import_places.py's OSM import, confirmed by matching
# artist and year, but far enough apart (~160-200m) that mark_duplicates()'s
# 75m radius - tuned for OSM's own node-vs-way duplicates, not for comparing
# an address-level geocode against a precisely placed OSM node - doesn't
# catch them. Found by cross-matching normalized names between the two
# "ready" sets (see docs/ai-development-log.md), not by widening the radius
# globally. The OSM record is kept in each pair: it has a more precise
# coordinate than this dataset's geocoded address.
CROSS_SOURCE_DUPLICATES = {
    "perfect_match/16": "node/6836072185",  # "I Have a Dream", Andrew Aiken/Aitken, 1991
    "perfect_match/147": "node/13876170704",  # "Block Party", Sharon Billinge, 2023
}

FIELD_NOTES_SOURCE = "Friend's personal visit tracking - not Inner West Council data"


def usable_text(value):
    """True if value is real content: not blank, and not a known placeholder."""
    if not value:
        return False
    cleaned = str(value).strip()
    if not cleaned:
        return False
    return cleaned.lower() not in PLACEHOLDER_VALUES


def normalize_suburb(raw_suburb):
    if not raw_suburb:
        return raw_suburb
    cleaned = raw_suburb.strip()
    return SUBURB_TYPO_FIXES.get(cleaned.lower(), cleaned)


def load_rows(path=RAW_XLSX_PATH, sheet_name=SHEET_NAME):
    """One dict per artwork, keyed by its row number in the sheet.

    The row number - not the sheet's own "Number" column - is used as the
    record id's stable suffix, because Number has real data-entry bugs:
    three values are duplicated across different artworks, and four rows
    contain the literal text "##" (an Excel overflow artifact) instead of a
    number. The row number has neither problem.

    Rows below the real data (blank rows, then a totals/summary block) have
    no Number value at all and are skipped by the `by_col.get(COL_NUMBER)`
    check - this is what drops the ~13 junk rows at the end of the sheet.
    """
    workbook = openpyxl.load_workbook(path, data_only=True)
    sheet = workbook[sheet_name]
    rows = []
    for row_number, row in enumerate(sheet.iter_rows(min_row=2), start=2):
        by_col = {cell.column_letter: cell.value for cell in row}
        if not by_col.get(COL_NUMBER):
            continue
        by_col["row_number"] = row_number
        rows.append(by_col)
    return rows


def load_geocode_cache(path=GEOCODE_CACHE_PATH):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_geocode_cache(cache, path=GEOCODE_CACHE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, path)  # atomic, same pattern as import_places.save_records


def geocode_query(full_address, suburb):
    """Collapses embedded newlines (a few Full Address cells have them) and
    appends NSW/Australia for disambiguation, since the source doesn't."""
    cleaned = " ".join(str(full_address).split())
    parts = [cleaned]
    if suburb and suburb.lower() not in cleaned.lower():
        parts.append(suburb)
    parts.append("NSW, Australia")
    return ", ".join(parts)


def geocode_address(full_address, suburb, cache):
    """Returns (lat, lon), or (None, None) if the address has no match.

    Only a successful lookup is cached, so a rerun makes no new request for
    an address already resolved. A failure is never cached - an HTTP error
    or network problem can be transient, and even a clean "no results"
    answer is cheap enough (one request, at most twice per street-art row)
    to just ask again next run rather than freeze it as permanent."""
    if not full_address:
        return None, None

    query = geocode_query(full_address, suburb)
    if query in cache:
        cached = cache[query]
        return cached["latitude"], cached["longitude"]

    lat, lon = None, None
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if response.status_code == 200:
            results = response.json()
            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
    except requests.RequestException:
        lat, lon = None, None
    finally:
        time.sleep(GEOCODE_DELAY_SECONDS)

    if lat is not None and lon is not None:
        cache[query] = {"latitude": lat, "longitude": lon}
    return lat, lon


def build_record(row_data, geocode_cache):
    row_number = row_data["row_number"]
    record_id = f"perfect_match/{row_number}"

    raw_title = row_data.get(COL_TITLE)
    name = raw_title.strip() if isinstance(raw_title, str) else raw_title
    full_address = row_data.get(COL_FULL_ADDRESS)
    street_address = row_data.get(COL_STREET_ADDRESS)
    suburb = normalize_suburb(row_data.get(COL_SUBURB))
    raw_statement = row_data.get(COL_STATEMENT)
    year = row_data.get(COL_YEAR)
    visibility_status = row_data.get(COL_STATUS)

    field_notes = {
        "status": visibility_status,
        "source": FIELD_NOTES_SOURCE,
    }

    record = {
        "id": record_id,
        "name": name if usable_text(name) else None,
        "latitude": None,
        "longitude": None,
        "topics": [TOPIC],
        "artist": row_data.get(COL_ARTIST),
        "year": int(year) if isinstance(year, (int, float)) else year,
        "suburb": suburb,
        "source_type": None,
        "source_title": None,
        "source_url": None,
        "source_excerpt": None,
        "status": "rejected",
        "imported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rejection_reason": None,
        "field_notes": field_notes,
    }

    if not usable_text(name):
        record["rejection_reason"] = "missing or placeholder artwork title"
        return record

    lat, lon = geocode_address(full_address, suburb, geocode_cache)
    if (lat is None or lon is None) and street_address and street_address != full_address:
        # Full Address often carries a venue-name prefix (e.g. "IGA Wall, 259
        # King St, Newtown") that trips up Nominatim. Street Address is the
        # council's own cleaner alternate for the same real location - not a
        # different or guessed address - so it's a reasonable fallback query.
        lat, lon = geocode_address(street_address, suburb, geocode_cache)
    record["latitude"] = lat
    record["longitude"] = lon

    no_longer_visible = (visibility_status or "").strip().lower() == "no longer visible"

    if no_longer_visible:
        record["rejection_reason"] = "marked 'No Longer Visible' in the friend's field notes"
    elif lat is None or lon is None:
        record["rejection_reason"] = "address could not be geocoded"
    elif usable_text(raw_statement):
        record["source_type"] = SOURCE_TYPE
        record["source_title"] = name
        record["source_url"] = SOURCE_URL
        record["source_excerpt"] = raw_statement  # verbatim - not stripped
        record["status"] = "ready"
    else:
        record["status"] = "limited"
        record["rejection_reason"] = "no usable Statement in the council data"

    return record


def apply_manual_duplicate_overrides(records_by_id):
    """Applies CROSS_SOURCE_DUPLICATES after the automatic mark_duplicates()
    pass. Only rejects a still-`ready` street-art record - never overrides
    another rejection reason (e.g. "No Longer Visible") already present."""
    for street_art_id, kept_id in CROSS_SOURCE_DUPLICATES.items():
        record = records_by_id.get(street_art_id)
        if record is None or record["status"] != "ready":
            continue
        record["status"] = "rejected"
        record["rejection_reason"] = f"duplicate of {kept_id} (reviewed cross-source match)"


def in_pilot_bbox(record):
    if record.get("latitude") is None or record.get("longitude") is None:
        return False
    south, west, north, east = PILOT_BBOX
    return south <= record["latitude"] <= north and west <= record["longitude"] <= east


def main():
    print(f"Reading {RAW_XLSX_PATH} ...")
    rows = load_rows()
    print(f"Found {len(rows)} artwork rows (junk/totals rows already excluded).")

    existing = load_existing()
    records_by_id = dict(existing)
    geocode_cache = load_geocode_cache()

    street_art_ids = []
    for i, row_data in enumerate(rows, start=1):
        record = build_record(row_data, geocode_cache)
        records_by_id[record["id"]] = record
        street_art_ids.append(record["id"])
        if i % 10 == 0:
            # Only the geocode cache is safe to save mid-run: it's just
            # address -> coordinates, unaffected by dedup. The catalogue
            # itself is saved once at the end, after mark_duplicates() and
            # apply_manual_duplicate_overrides() below - saving it here too
            # would let an interrupted run leave duplicates on disk that
            # were never actually checked.
            save_geocode_cache(geocode_cache)
            print(f"  processed {i}/{len(rows)}...")

    mark_duplicates(list(records_by_id.values()))
    apply_manual_duplicate_overrides(records_by_id)
    save_records(records_by_id)
    save_geocode_cache(geocode_cache)

    street_art_records = [records_by_id[rid] for rid in street_art_ids]

    counts = {"ready": 0, "limited": 0, "rejected": 0}
    no_longer_visible_count = 0
    no_title_count = 0
    cross_source_duplicate_count = 0
    failed_geocodes = []
    for r in street_art_records:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        reason = r.get("rejection_reason") or ""
        if "No Longer Visible" in reason:
            no_longer_visible_count += 1
        if "missing or placeholder artwork title" in reason:
            no_title_count += 1
        if "reviewed cross-source match" in reason:
            cross_source_duplicate_count += 1
        if reason == "address could not be geocoded":
            failed_geocodes.append(r["id"])

    ready_in_bbox = sum(1 for r in street_art_records if r["status"] == "ready" and in_pilot_bbox(r))

    print("\nStreet art import complete.")
    print(f"  ready:    {counts['ready']}")
    print(f"  limited:  {counts['limited']}")
    print(f"  rejected: {counts['rejected']}")
    print(f"    of which 'No Longer Visible': {no_longer_visible_count}")
    print(f"    of which missing/placeholder title: {no_title_count}")
    print(f"    of which a reviewed cross-source duplicate: {cross_source_duplicate_count}")
    print(f"    of which failed geocoding: {len(failed_geocodes)}")
    print(f"  ready records inside the Newtown pilot bbox: {ready_in_bbox}")
    if failed_geocodes:
        print("\nFailed geocodes (address could not be resolved - not guessed):")
        for rid in failed_geocodes:
            print(f"  {rid}")
    print(f"\nSaved to {os.path.join('data', 'sydney_places.json')}")


if __name__ == "__main__":
    main()
