"""Configuration for the current pilot area (NFR-5: the pilot-area boundary
and language must be kept as configuration, not inline literals, so a
second area or language is additive - pointing import_places.py at a new
place means editing the values below, not the pipeline's code.
"""

# Pilot area bounding box: south, west, north, east.
# Expanded 2026-10-30 (Story 4.2) from the original Newtown-only box
# (-33.910, 151.165, -33.892, 151.185) to cover inner Sydney more broadly -
# CBD, Pyrmont/Ultimo, Glebe, Annandale/Leichhardt, Surry Hills,
# Darlinghurst/Paddington, Redfern/Alexandria/Waterloo, and the inner-west
# suburbs around Newtown (Erskineville, St Peters, Camperdown, Marrickville).
# Does not cross the harbour to North Sydney. Only affects what the
# importers fetch next run - existing catalogue entries are untouched.
PILOT_BBOX = (-33.925, 151.140, -33.855, 151.235)

# Wikipedia/Wikidata language code used for this pilot area's sources.
LANGUAGE = "en"
