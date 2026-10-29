"""Configuration for the current pilot area (NFR-5: the pilot-area boundary
and language must be kept as configuration, not inline literals, so a
second area or language is additive - pointing import_places.py at a new
place means editing the values below, not the pipeline's code.
"""

# Newtown, Sydney pilot area bounding box: south, west, north, east.
PILOT_BBOX = (-33.910, 151.165, -33.892, 151.185)

# Wikipedia/Wikidata language code used for this pilot area's sources.
LANGUAGE = "en"
