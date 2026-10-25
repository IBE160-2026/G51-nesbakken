# Stop photo coverage —2026-10-23

**Latest status —2026-10-25:** 17/159 ready stops now have verified local images (10.69%). The dated sections below preserve earlier audits; their1/159 and4/159 counts and pending Bank/St Peters/Dream notes are superseded by the latest batch at the end. Source evidence, exact asset hashes and changes for the13 new images are in `docs/photo-match-audit-2026-10-25.json`.

Initial catalogue audit:226 total records,159 ready. None carries verified photo/licence/creator metadata: stored usable coverage0/159. Existing Wikidata tags are not proof of reusable image rights. This is a metadata audit, not an exhaustive search for photographs of every stop.

## Audited image

- Ready stop: heritage/2420855, Newtown Post Office.
- Exact Commons filename: Newtown Post Office.jpg (lowercase extension; the uppercase JPG file is different).
- Primary description/source: https://commons.wikimedia.org/wiki/File:Newtown_Post_Office.jpg . Source states own work by Sardaka, dual-licensed GFDL and CC BY3.0; this project selects CC BY3.0.
- Licence: https://creativecommons.org/licenses/by/3.0/ . Show creator, licence and source links and indicate modifications.
- Original download: https://upload.wikimedia.org/wikipedia/commons/6/69/Newtown_Post_Office.jpg .2816x2112 JPEG,1286380 bytes. Original bytes copied unmodified to static/place-photos/newtown-post-office.jpg; browser displays proportionally without cropping. Visual inspection confirms the post office facade/clock tower.
- Asset SHA256: e4e9c2f967b31ec12ba56b56f36b3389cb59991c53375920597a88753cb99d83.
- Verified curated coverage after adding this manifest:1/159 (about0.63%). This is a lower bound, not a claim other stops lack eligible images. Photos remain a nice-to-have only where audited.

## Maintenance

Curate data/place_photos.json by stable place ID so catalogue importers cannot erase metadata. reviewed:true means a human/agent checked the actual primary file-description page, specific licence and matching subject; it is not automatic copyright detection. Store complete attribution and a local asset, with audit evidence here. Do not infer rights from a URL, OSM image tag, WikidataP18 or provider category. No automatic harvesting or generated substitute photos. Missing, incomplete, unreviewed or broken assets must render text-only with no placeholder. New licences/sources need their own primary evidence and accurate attribution.

## Additional photo candidates found —2026-10-25

Research only; no new assets have been downloaded, visually audited or joined to place IDs. Implemented coverage remains1/159.

- Bank Hotel: https://commons.wikimedia.org/wiki/File:Bank_Hotel,_Newtown.jpg — file-description page identifies Bank Hotel, Newtown, Sydney, own work by Sardaka and offers CC BY3.0 (also GFDL; CC BY3.0 would be selected). Original2816×2112,1091406bytes. Suitable candidate for exterior identification, subject to visual inspection and exact catalogue mapping before adding. Search index returned the primary file page; a later direct fetch missed the cache.
- Enmore Theatre: https://commons.wikimedia.org/wiki/File:Enmore_Theatre.jpg — primary page identifies Enmore Theatre, Enmore, Sydney, own work by Sardaka and offers CC BY3.0 (also GFDL). Original2816×2112,1288795bytes. File page directly checked. Same remaining visual/ID checks before adding.
- St Peters station has a Commons collection: https://commons.wikimedia.org/wiki/Category:St_Peters_railway_station,_Sydney . A category is not licence evidence for any individual image; no selected image approved here.

CC BY3.0 licence: https://creativecommons.org/licenses/by/3.0/ . Retain creator/source/licence links and accurate changes statement when integrating. These examples show more reusable candidates exist; no Google service, account or billing dependency is needed for this approach.

## Added and visually checked —2026-10-25

The three originals below are now local, reviewed and joined by stable ready-stop IDs. Existing Post Office plus these give **4/159 ready stops (2.52%)**, including one public-art sculpture. This is verified stored coverage, not an exhaustive external-photo audit. Images appear inside stop details, not map/list thumbnails. Each original was visually inspected; proportional display and original bytes are retained. Hashes identify the exact downloaded file.

| Stop / ID | Creator / selected licence | Original asset / dimensions / bytes | SHA256 |
|---|---|---|---|
| Enmore Theatre / heritage/2030116 | Sardaka / CC BY3.0 | static/place-photos/enmore-theatre.jpg /2816×2112 /1288795 | ef870b1a7d893b5b8079eee9e68f85e2dd76ca15534e3fdc33d40de17e58fce8 |
| Cragos Flour Mill / heritage/2030114 | J Bar / CC BY-SA3.0 | static/place-photos/cragos-flour-mill.jpg /2560×1920 /1755721 | b63c5f75c63191c8fbf64519bb2aa0ce309ee4e9d2c97f0d3d106de2f21f36ec |
| The Trail / node/5301587126 | Paul McCarthy (Xxpaulm) / CC BY2.5 | static/place-photos/the-trail.jpg /2048×1536 /2536915 | d80254a2d4a5677747caed968aeb2c3dbade42c57b9e5fab7dfb06b0201d3676 |

Primary file pages (specific licences, not category-wide assumptions):
- https://commons.wikimedia.org/wiki/File:Enmore_Theatre.jpg ; original https://upload.wikimedia.org/wikipedia/commons/9/98/Enmore_Theatre.jpg ; licence https://creativecommons.org/licenses/by/3.0/ . Exterior facade/tower matches place, historical photograph, no claim it depicts current event signage.
- https://commons.wikimedia.org/wiki/File:Newtown_Crago_Flour_Mill_1.JPG ; original https://upload.wikimedia.org/wikipedia/commons/d/d5/Newtown_Crago_Flour_Mill_1.JPG ; licence https://creativecommons.org/licenses/by-sa/3.0/ . Shows mill lettering and rail-side brick facade. Retain the image licence; do not imply app code is licensed under it.
- https://commons.wikimedia.org/wiki/File:MichaelSnapeTheTrail1990SydneyPark.jpg ; original https://upload.wikimedia.org/wikipedia/commons/1/19/MichaelSnapeTheTrail1990SydneyPark.jpg ; licence https://creativecommons.org/licenses/by/2.5/ . Source identifies photographer Paul McCarthy/Xxpaulm and sculpture Michael Snape. Sculptor is credited in alt text and source page, photograph credit remains Paul McCarthy. Subject cross-check https://www.cityofsydney.nsw.gov.au/sculptures/the-trail . Artwork is a permanent public sculpture; Australian Copyright Act ss65/68 provides relevant photography/publication exceptions (https://www.legislation.gov.au/C1968A00063/2026-04-02/2026-04-02/text/original/pdf). Do not generalise this to murals.

### Still awaiting asset download

Bank Hotel (heritage/2420858), user confirms correct subject, primary licence/creator above. St Peters station (heritage/5012222), https://commons.wikimedia.org/wiki/File:St_Peters_Railway_Station_in_2018_--_01.jpg , Collywolly, CC BY-SA4.0 https://creativecommons.org/licenses/by-sa/4.0/ . Both are candidates only, not manifest entries. Wikimedia returned429; bounded retries respected Retry-After, last response requested600seconds, so further downloads stopped. Do not mark reviewed until bytes downloaded and visually inspected. Successful downloads above are already usable; no remote hotlink dependence was added.

## User-specified public-art sites —2026-10-25

- https://newtowngraffitimap.com/ ; specific checked Dream page https://newtowngraffitimap.com/i-have-a-dream-juilee-pryor/ credits artists Juilee Pryor/Andrew Aiken and footer says All Rights Reserved. Relevant catalogue matches also include Promise (perfect_match/52), Housing Bubble (/34), Making All Things New (/32), Bring Back the Butterflies (/68), Sydney Park Hotel (/70). No verified reuse permission for the photographs or depicted murals, so none copied.
- https://www.innerwest.nsw.gov.au/perfect-match-street-art/artwork-gallery-2017-2022 has direct matches including Characters of Newtown (/133), A Rising Tide (/96), The Devine Within (/51), Nature Always Wins (/66), Familiar Form (/67), Mary (/69), Sydney Park Hotel (/70), Dire Straits (/71), Bring Back the Butterflies (/68), The Spirit of St Peters (/122). Artist/location credits and Council copyright appear, but no applicable photo reuse licence or photographer credits verified. Access policy https://www.innerwest.nsw.gov.au/access-information does not grant blanket gallery-image reuse. Do not apply terms from a separate Council consultation platform.
- City of Sydney Archives https://archives.cityofsydney.nsw.gov.au/nodes/view/587176 explicitly retains Juilee Pryor photograph copyright and notes artist permission may be needed for mural publication. Archive access alone does not clear rights.

These sources could supply many matched photos if the rights holders grant permission covering both photographs and artwork, public app display, local hosting and necessary sizing. Prepare a permission request for user review rather than sending it. No contact made; research findings are not legal assurance or permission. Retain no-photo presentation until a specific grant or open licence is recorded.


## Wikipedia follow-up —2026-10-25

User suggested Wikipedia. Wikipedia’s Newtown area graffiti and street art article provides further image leads: https://en.wikipedia.org/wiki/Newtown_area_graffiti_and_street_art . A concrete Dream mural candidate is https://commons.wikimedia.org/wiki/File:Newtown_area_graffiti_and_street_art_04.jpg : author Hpeterswald, CC BY-SA4.0, current original2593×1928, file page records VRT permission ticket2016080910018537 and says reuse is permitted under its licence. This is distinct from the photographer-retained archive image or the Newtown Graffiti Map copy. Thus needing permission for those copies does not mean every Dream photograph lacks an open-licence route.

Not integrated yet: file page and VRT notice verified, but original bytes/visual match and whether permission documentation covers the underlying mural as well as photograph remain to be established before reviewed:true. Private ticket contents were not accessed. Keep catalogue mapping node/6836072185 (ready), not rejected duplicate perfect_match/16. No blanket conclusion that Wikipedia display itself grants reuse. Coverage remains4/159.


## Latest completed batch —2026-10-25

Added13 individually matched and visually inspected photographs. Implemented coverage is now **17/159 ready stops (10.69%)**, superseding all earlier counts in this document. This is stored verified coverage, not a claim that the remaining142 places have no images elsewhere. Existing API/UI contracts and importer files are unchanged.

| Stop / stable ID | Creator and selected licence | Local asset | Stored dimensions / bytes |
|---|---|---|---|
| St Peters Railway Station group / heritage/5012222 | Collywolly / CC BY-SA 4.0 | static/place-photos/st-peters-station.jpg | 2816×2112 / 1586840 |
| I Have A Dream / node/6836072185 | Hpeterswald; mural by Andrew Aiken and Juilee Pryor / CC BY-SA 4.0 | static/place-photos/i-have-a-dream.jpg | 2593×1928 / 2515106 |
| Newtown Railway Station group and Former Newtown Tramway Depot / heritage/5012123 | Wykymania / CC BY-SA 3.0 | static/place-photos/newtown-station.jpg | 1600×1067 / 211664 |
| Uniting Church and Pipe Organ / heritage/5045004 | J Bar / CC BY 3.0 | static/place-photos/newtown-mission.jpg | 1920×2560 / 1706897 |
| Imperial Hotel, Erskineville / heritage/5068106 | Sardaka / CC BY-SA 4.0 | static/place-photos/imperial-hotel.jpg | 1460×1075 / 954375 |
| St Stephen's Anglican Church and Cemetery / heritage/5045479 | TTaylor / CC BY-SA 4.0 | static/place-photos/st-stephens-church.jpg | 1200×1600 / 512598 |
| Newtown Baptist Church / way/172735167 | Sardaka / CC BY-SA 4.0 | static/place-photos/newtown-baptist-church.jpg | 1280×1834 / 742569 |
| Erskineville Hotel / heritage/2420715 | J Bar / CC BY 3.0 | static/place-photos/erskineville-hotel.jpg | 2560×1920 / 1798168 |
| Bank Hotel / heritage/2420858 | Sardaka / CC BY 3.0 | static/place-photos/bank-hotel.jpg | 1280×960 / 212861 |
| Stead House (circa 1850s, also known as Frankfort Villa and Waterloo Villa), including interiors / heritage/2030138 | Sardaka / CC BY 3.0 | static/place-photos/stead-house.jpg | 1280×853 / 413748 |
| Erskineville Town Hall / heritage/2420716 | Sardaka / CC BY-SA 4.0 | static/place-photos/erskineville-town-hall.jpg | 1280×770 / 256288 |
| Former brickworks group / heritage/2421330 | Adam.J.W.C. (photograph); Ashton 29 (colour enhancement) / CC BY 3.0 | static/place-photos/sydney-park-brickworks.jpg | 1280×1083 / 424971 |
| Union Hotel / heritage/2423037 | Nick-D / CC BY-SA 3.0 | static/place-photos/union-hotel.jpg | 1280×853 / 321917 |

Each source page, licence URL, original/download URL, SHA256 and changes statement is preserved in docs/photo-match-audit-2026-10-25.json. All13 local assets were visually inspected against the catalogue names/locations and source descriptions. Seven new assets retain original published bytes; six use Commons' published1280px renditions. Attribution accurately states downscaling; source author credits retained. Baptist Church original was13,483,952bytes; stored rendition742,569bytes. No13MB image was added. Sydney Park brickworks credits both Adam.J.W.C. and colour enhancement by Ashton29; source modifications and downscaling disclosed. Proportions retained, no AI edits/crops. Older originals from the initial4-photo batch remain unchanged.

### Dream mural reuse basis

The added photograph is the exact Commons file https://commons.wikimedia.org/wiki/File:Newtown_area_graffiti_and_street_art_04.jpg , not a copy from Newtown Graffiti Map or City Archives. Commons identifies Hpeterswald, CC BY-SA4.0, and publicly states reuse under its licensing requirements is permitted with VRT permission-confirmation ticket2016080910018537. This selection relies on that specific published licence plus public permission notice. We did not access the private correspondence and do not claim independent knowledge of its contents or a blanket grant for all mural photographs. Visible credit includes photographer and mural artists Andrew Aiken/Juilee Pryor. The licence and source remain linked. Other murals without equivalent evidence remain text-only.

### Rejected or pending candidates

- The Commons Come out Hippo photo is NOT a match for node/12771471818: its coordinates(-33.951815,151.162757)/category place it in Brighton-Le-Sands, while Jaunt's Will Coles artwork is in Newtown(-33.8971631,151.1786346). No hippo image added.
- Wikipedia redirected Newington Manor search to Newington, Swale in the UK; unrelated imagery rejected. Newtown town halls/churches in the UK, Victoria and USA, unrelated PDFs/maps and images merely depicting a train/person were also rejected.
- Stanmore House's historic circa1900 photograph is a promising lead but has unknown original photographer and restored/source provenance requiring further checking. Not added under a generic unknown-author guess.
- Remaining ready art/heritage stops without a verified subject/right/image remain without a photo. Metadata searches paused at429; research and downloaded original queues in/private/tmp are temporary only. Durable evidence for every added asset is in the JSON audit; further broad searching is not represented as exhaustive.
- Additional sources remain available for future permission checks; no rights holders were contacted and the user's deletion of the permission-request draft was preserved.
