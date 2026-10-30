"""Automated first-pass photo matching against Wikimedia Commons.

User's explicit, informed choice (2026-10-30): unlike every other source
in this project, this script publishes directly into data/place_photos.json
(reviewed: true, visible immediately) rather than writing to a separate
unreviewed suggestions file first - the user does spot-checks afterward
and reports back what to remove, instead of checking before publish.

What stays non-negotiable even in this workflow:
- A real license is checked via Commons' own extmetadata for every
  candidate - never inferred from a URL, filename or category.
- Only licenses that are actually free to reuse with attribution
  (CC BY/CC BY-SA/CC0/public domain) are accepted - never "all rights
  reserved", non-commercial-only, or no-derivatives-only licenses.
- A real, specific word from the place's own name must appear in the
  candidate's title or description - not just any image in the right
  general category.
- Every match is logged to docs/photo-match-audit-<date>.json with full
  evidence (the exact fields above) so a human spot-check is actually
  fast, not a re-investigation from scratch.

Resumable like the other importers: a place already in place_photos.json
is left untouched and skipped.
"""

import json
import os
import re
import time
import unicodedata
import urllib.parse
from datetime import date

import requests

from import_places import USER_AGENT

COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
CATALOGUE_PATH = os.path.join("data", "sydney_places.json")
MANIFEST_PATH = os.path.join("data", "place_photos.json")
ASSET_DIR = os.path.join("static", "place-photos")
AUDIT_PATH = os.path.join("docs", f"photo-match-audit-{date.today().isoformat()}.json")

MIN_DIMENSION_PX = 500
MAX_CANDIDATES_PER_PLACE = 5

# Only reusable-with-attribution licenses - never NC/ND/all-rights-reserved.
ACCEPTABLE_LICENSES = {
    "cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "public domain": "https://en.wikipedia.org/wiki/Public_domain",
    "cc by 2.0": "https://creativecommons.org/licenses/by/2.0/",
    "cc by 2.5": "https://creativecommons.org/licenses/by/2.5/",
    "cc by 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "cc by 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "cc by-sa 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "cc by-sa 2.5": "https://creativecommons.org/licenses/by-sa/2.5/",
    "cc by-sa 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "cc by-sa 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
}

# Same reasoning as import_places.py's WIKIDATA_GENERIC_WORDS: words common
# enough to appear in many unrelated photo titles, so matching on them
# alone proves nothing about whether this specific photo IS this place.
GENERIC_WORDS = {
    "church", "war", "memorial", "monument", "sculpture", "historic",
    "heritage", "site", "national", "museum", "building", "structure",
    "artwork", "nsw", "new", "south", "wales", "sydney", "australia",
    "cathedral", "chapel", "house", "park", "hotel", "theatre", "school",
    "office", "street", "road", "the", "and", "of",
}


def slugify(name):
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "place"


def name_words(name):
    words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in name.split()]
    return [w for w in words if len(w) >= 4 and w not in GENERIC_WORDS]


def mentions_place(text, name):
    if not text:
        return False
    text_lower = text.lower()
    return any(w in text_lower for w in name_words(name))


def strip_html(value):
    return re.sub(r"<[^>]+>", "", value or "").strip()


def _get_with_retry(url, params, timeout=20):
    """Commons' API rate-limits bursts harder than a single politeness
    sleep accounts for (found in testing, 2026-10-30) - a short backoff and
    retry on a 429 specifically, not on every error."""
    last_exc = None
    for wait_seconds in (0, 4, 10):
        if wait_seconds:
            time.sleep(wait_seconds)
        try:
            response = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=timeout)
            if response.status_code == 429:
                last_exc = requests.HTTPError("429 Too Many Requests", response=response)
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_exc = exc
    raise last_exc


def search_candidates(name):
    response = _get_with_retry(COMMONS_API_URL, {
        "action": "query", "list": "search", "srnamespace": "6",
        "srsearch": name, "srlimit": str(MAX_CANDIDATES_PER_PLACE), "format": "json",
    })
    return [r["title"] for r in response.json().get("query", {}).get("search", [])]


def fetch_image_info(title):
    response = _get_with_retry(COMMONS_API_URL, {
        "action": "query", "titles": title, "prop": "imageinfo|categories",
        "iiprop": "url|size|extmetadata", "format": "json",
    })
    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        info = (page.get("imageinfo") or [None])[0]
        if info:
            info["categories"] = [c.get("title", "") for c in page.get("categories", [])]
            return info
    return None


# A plain word match (e.g. "Uplift", "Beacon", "Block Party") is not nearly
# enough on its own - Commons has millions of unrelated photos worldwide,
# and short/evocative names for real Sydney artworks coincidentally match
# photos of a Japanese earthquake or a UK village. Requiring a real
# geographic signal somewhere caught every bad match found in testing
# (2026-10-30) - without this, roughly all early test matches were wrong.
# "nsw"/"australia" alone were too broad - a rock formation near Mathoura
# (hundreds of km from Sydney) passed that check (found in testing,
# 2026-10-30). Tightened to Sydney itself plus the actual inner-Sydney
# suburbs this pilot area covers (pilot_config.py), not the whole state.
PLACE_SIGNAL_WORDS = (
    "sydney", "newtown", "erskineville", "st peters", "camperdown",
    "glebe", "redfern", "alexandria", "waterloo", "surry hills",
    "darlinghurst", "paddington", "pyrmont", "ultimo", "annandale",
    "leichhardt", "marrickville",
)


def has_place_signal(info):
    haystack = " ".join([
        strip_html(info.get("extmetadata", {}).get("ImageDescription", {}).get("value", "")),
        " ".join(info.get("categories", [])),
    ]).lower()
    return any(word in haystack for word in PLACE_SIGNAL_WORDS)


def evaluate_candidate(title, name):
    """Returns a match dict if this candidate passes every real check, else
    None with a reason. Never guesses past what Commons' own metadata says."""
    try:
        info = fetch_image_info(title)
    except requests.RequestException as exc:
        return None, f"request failed: {exc}"
    if not info:
        return None, "no imageinfo returned"

    width, height = info.get("width", 0), info.get("height", 0)
    if width < MIN_DIMENSION_PX or height < MIN_DIMENSION_PX:
        return None, f"too small ({width}x{height})"

    meta = info.get("extmetadata", {})
    license_short = (meta.get("LicenseShortName", {}).get("value") or "").strip()
    license_key = license_short.lower()
    if license_key not in ACCEPTABLE_LICENSES:
        return None, f"license not reusable with attribution: {license_short!r}"

    description = strip_html(meta.get("ImageDescription", {}).get("value", ""))
    if not mentions_place(title, name) and not mentions_place(description, name):
        return None, "neither title nor description names this specific place"

    if not has_place_signal(info):
        return None, "no Sydney/NSW/Australia signal in description or categories"

    artist = strip_html(meta.get("Artist", {}).get("value", "")) or "Unknown"
    file_page_title = title.replace(" ", "_")
    return {
        "title": title,
        "image_url": info["url"],
        "source_url": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(file_page_title)}",
        "creator": artist,
        "license": license_short,
        "license_url": ACCEPTABLE_LICENSES[license_key],
        "width": width,
        "height": height,
        "description": description,
    }, None


def download_asset(image_url, slug):
    extension = os.path.splitext(image_url)[1].lower() or ".jpg"
    if extension not in (".jpg", ".jpeg", ".png", ".webp"):
        extension = ".jpg"
    filename = f"{slug}{extension}"
    # upload.wikimedia.org rate-limits bursts of requests (429) - a short
    # backoff and retry is enough since this script already paces its own
    # requests with time.sleep() between candidates.
    last_exc = None
    for attempt, wait_seconds in enumerate((0, 3, 8)):
        if wait_seconds:
            time.sleep(wait_seconds)
        try:
            response = requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=30)
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            last_exc = exc
    else:
        raise last_exc
    os.makedirs(ASSET_DIR, exist_ok=True)
    with open(os.path.join(ASSET_DIR, filename), "wb") as f:
        f.write(response.content)
    return filename


def load_catalogue():
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        return {"_instructions": "", }
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest):
    temp_path = MANIFEST_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, MANIFEST_PATH)


def main(limit=None):
    catalogue = load_catalogue()
    manifest = load_manifest()
    audit = []

    ready = [r for r in catalogue if r["status"] == "ready" and r["id"] not in manifest]
    if limit:
        ready = ready[:limit]
    print(f"Attempting photo matches for {len(ready)} ready place(s) without an existing photo...")

    matched, rejected = 0, 0
    for record in ready:
        name = record.get("name") or ""
        if not name:
            continue
        try:
            candidates = search_candidates(name)
        except requests.RequestException as exc:
            print(f"  {name}: search failed - {exc}")
            continue
        time.sleep(0.8)

        found = None
        reasons = []
        for title in candidates:
            match, reason = evaluate_candidate(title, name)
            time.sleep(0.8)
            if match:
                found = match
                break
            reasons.append(f"{title}: {reason}")

        if not found:
            rejected += 1
            audit.append({"id": record["id"], "name": name, "status": "no_match", "candidates_tried": reasons})
            continue

        slug = slugify(name)
        try:
            filename = download_asset(found["image_url"], slug)
        except requests.RequestException as exc:
            print(f"  {name}: download failed - {exc}")
            audit.append({"id": record["id"], "name": name, "status": "download_failed", "error": str(exc)})
            continue

        alt = found["description"] or f"{name}, photograph"
        manifest[record["id"]] = {
            "reviewed": True,
            "url": f"/static/place-photos/{filename}",
            "source_url": found["source_url"],
            "creator": found["creator"],
            "license": found["license"],
            "license_url": found["license_url"],
            "alt": alt[:300],
            "changes": "Unmodified photograph.",
        }
        audit.append({
            "id": record["id"], "name": name, "status": "matched",
            "commons_title": found["title"], "source_url": found["source_url"],
            "creator": found["creator"], "license": found["license"],
            "dimensions": f"{found['width']}x{found['height']}", "asset": filename,
        })
        matched += 1
        print(f"  MATCHED {name} -> {found['title']} ({found['license']}, by {found['creator']})")
        # Saved after every match, not just at the end - this can run for a
        # long time against a slow/rate-limited API, and whatever has
        # already matched must survive being stopped early.
        save_manifest(manifest)
        save_audit(audit)

    save_manifest(manifest)
    save_audit(audit)
    print(f"\nDone. Matched {matched}, rejected/no-match {rejected}.")
    print(f"Audit log for your spot-check: {AUDIT_PATH}")


def save_audit(audit):
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "_instructions": (
                "Bot-matched photos (published live, reviewed:true) pending your "
                "spot-check. For each 'matched' entry, open source_url and confirm "
                "it's actually a photo of this place and the license is correctly "
                "read. Tell me which ids to remove if wrong - I'll delete them from "
                "data/place_photos.json and the downloaded asset."
            ),
            "entries": audit,
        }, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import sys
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit=limit_arg)
