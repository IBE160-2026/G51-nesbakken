# Refleksjonsrapport - Programmering med KI

> **Om dette utkastet:** Faktuelle deler (hva som ble bygget, hvilke verktøy, konkrete hendelser med KI) er fylt ut basert på `docs/ai-development-log.md`, `docs/architecture-plan.md`, `ai-prompts.md` og PRD-prosessen i `_bmad-output/`. Subjektive vurderinger, meninger og personlig refleksjon er merket **[STUDENT SKRIVER]** — disse må være i din egen stemme, ikke generert av KI. Noen av disse seksjonene har et "Bevis å bygge på"-punkt med konkrete, verifiserbare hendelser du kan referere til eller bygge videre på i din egen vurdering.

## 1. Gruppeinformasjon

**Gruppenavn:** [STUDENT SKRIVER]

**Gruppemedlemmer:**
- Nesbakken - [Student-ID/E-post]

**Dato:** [STUDENT SKRIVER — DD.MM.ÅÅÅÅ for innlevering]

---

## 2. Utviklingsprosessen

### 2.1 Oversikt over prosjektet

Jaunt er en mobilvennlig webapplikasjon som gjør brukerens tilgjengelige tid om til en formålsrettet gåtur. Brukeren oppgir et startpunkt, hvor mye tid de har (30–120 minutter), og eventuelt et tema (historie, arkitektur, gatekunst, kulturminner, eller "overrask meg"). Jaunt foreslår en kort rundtur med 2–5 reelle stopp, hver med et kort KI-generert innhold (historie, faktum eller oppfordring) som er forankret i ekte kildemateriale.

Hovedmålet var ikke bare å bygge en kartapplikasjon, men å teste om KI kan brukes meningsfullt til to konkrete oppgaver: (1) å velge den mest relevante kombinasjonen av stopp fra et forhåndsfiltrert og verifisert sett med kandidater, og (2) å omsette lagret kildetekst til kort, engasjerende innhold — uten å finne på informasjon. Prosjektet er bevisst avgrenset til ett pilotområde (Newtown, Sydney) med et verifisert, offline-importert katalog av steder (OpenStreetMap, Wikipedia/Wikidata, et datasett for gatekunst fra Inner West Council, og en håndplukket liste over NSW-kulturminner).

### 2.2 Arbeidsmetodikk

[STUDENT SKRIVER — hvordan ble oppgaver fordelt, hvilke samarbeidsverktøy ble brukt og hvordan fungerte de (f.eks. Git, Teams)?]

**Fastsatt rollefordeling mellom KI-verktøyene** (dokumentert i `AGENTS.md`/`CLAUDE.md`, fulgt gjennom hele prosjektet):
- **Claude Code**: primært ansvarlig for implementasjon, funksjonsutvikling, UI/UX, produkttenkning og forklaring av implementasjonsvalg.
- **Codex (GPT)**: primært ansvarlig for kodegjennomgang, debugging av vanskelige problemer, sjekk mot krav, testing og identifisering av unødvendig kompleksitet.
- Eksplisitt regel gjennom prosjektet: ingen forslag fra ett KI-verktøy ble implementert uten vurdering (av den andre, eller av studenten selv) først.

### 2.3 Teknologi og verktøy

- **Backend:** Python (Flask). Ingen database — en lokal JSON-katalog pluss forespørselstilstand er tilstrekkelig for V1.
- **Frontend:** Vanilla JS med Leaflet-kart (OpenStreetMap-fliser). Mobilvennlig fra starten av, ikke tilpasset i etterkant.
- **Stedsdata:** OpenStreetMap Overpass API, Wikipedia/Wikidata, Inner West Council sitt "Perfect Match"-datasett for gatekunst (.xlsx), NSW sin offisielle Heritage MapServer (ArcGIS).
- **Ruting:** OpenRouteService (fot-profil), bekreftet direkte før bruk.
- **KI:** OpenAI API for (1) å velge beste rutealternativ fra en ferdig-filtrert og -validert meny, og (2) generere kort innhold fra lagrede kildeutdrag.
- **KI-verktøy i utviklingsprosessen:** Claude Code, Codex (GPT), samt BMAD-metoden (strukturert, agent-basert planleggingsprosess) for produktkravdokumentet (PRD).
- **Andre verktøy:** Git, pytest (168/168 tester bestått ved siste kjøring).

### 2.4 Utviklingsfaser

**Fase 1: Planlegging**

Planleggingen av Jaunt V1 fulgte: Produktidé → Produktbrief → Produktkrav (PRD) → (videre: UX → Arkitektur → Implementasjon). Produktbrief ble skrevet tidlig i prosjektet. Et strukturert PRD-dokument (`_bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/prd.md`) ble utarbeidet i etterkant av at store deler av koden allerede var skrevet (Sprint 1–6), nettopp for å formalisere kravene til hele V1 — både det som allerede var bygget, og det som gjensto (brukergrensesnitt for tid/tema-valg, rutevisning, og KI-generert stoppinnhold).

PRD-prosessen (BMAD-metoden) ble brukt slik:
- KI fungerte som fasilitator, ikke beslutningstaker: den stilte åpne spørsmål for å hente ut produktvisjonen, i stedet for å foreslå løsninger først.
- KI brukte paralelle underoppgaver ("subagents") til å: lese og hente ut relevant informasjon fra eksisterende dokumentasjon (produktbrief, arkitekturplan, utviklingslogg), gjøre nettsøk for å vurdere gjennomførbarheten av geografisk utvidelse (automatisk stedsoppdagelse i Oslo, Molde, Nice sammenlignet med Sydney), og gjennomføre uavhengige kvalitetsgjennomganger av det ferdige dokumentet (en "rubrikk"-gjennomgang, en gjennomgang av gjennomførbarhet/tidsbruk, og sammenligning mot kildedokumentene for å finne informasjon som hadde falt bort underveis).
- Flere runder med korreksjon fra studenten endret reelle krav i dokumentet — se `ai-prompts.md` for alle promptene ordrett, datert 2026-09-29 til 2026-10-02. Eksempler: kravet om at KI-generert innhold aldri skal finne på informasjon (FR-19) ble justert fra en absolutt påstand til et krav om en reell automatisert sjekk pluss manuell stikkprøvekontroll; definisjonen av "besøkt" stopp ble presisert til å kreve en eksplisitt handling, ikke bare det å ha åpnet innholdet; og en antakelse om at mangel på kildetekst for kulturminner i Newtown var en grunnleggende begrensning for temaet "kulturminner" generelt, ble korrigert til å gjelde kun den ene NSW-datakilden.

**Fase 2: Utvikling**

Basert på `docs/ai-development-log.md` og `docs/architecture-plan.md`, ble utviklingen gjennomført i nummererte sprinter, hver med en kort "known limitations"-seksjon skrevet etter fullføring:

- **Sprint 1** — Importpipeline mot Newtown-pilotområdet (24 kandidater fra Overpass → 11 klare, 7 begrensede, 6 avviste), samt bekreftelse av fot-rutingprofil.
- **Sprint 2** — Minimal fungerende web-flyt (kart + klikk-for-startpunkt + visning av steder), ingen KI eller tidsbudsjett-logikk ennå.
- **Sprint 3** — Shortlisting av kandidater, henting av reell avstandsmatrise, brute-force ruteordning og gjennomførbarhetssjekk.
- **Sprint 4** — KI-basert valg av endelig stoppkombinasjon, fra en Python-forhåndsfiltrert og -validert meny (se utfordring under punkt 3.1).
- **Sprint 5** — Andre datakilde for gatekunst (Inner West Council), uavhengig fra OSM.
- **Sprint 6** — Nytt tema "kulturminner" fra NSWs offisielle Heritage MapServer, med en bevisst etisk avgjørelse om ikke å omgå et tilgangshinder (se punkt 3.3).

Gjenstående arbeid ved slutten av Sprint 6 (identifisert og formalisert i PRD-prosessen i Fase 1): KI-generering av stoppinnhold (Sprint 7), og kobling av frontend til planleggings-/KI-pipelinen (del av Sprint 8) — altså selve brukerflyten for å velge tid/tema og se den foreslåtte ruten.

---

## 3. Utfordringer og løsninger

### 3.1 Tekniske utfordringer

**Utfordring 1: KI kunne ikke pålitelig gjøre rutingmatematikk selv**

- **Problem:** Den opprinnelige utformingen ga KI den rå avstandsmatrisen og ba den selv beregne om en foreslått rute passet innenfor brukerens tidsbudsjett. Levende testing (ikke bare automatiserte tester) viste at modellen produserte selvmotsigende resultater — to ulike forslag med 5 stopp ble begge påstått å ta "75 minutter", noe som ikke stemte.
- **Løsning:** Arkitekturen ble endret slik at Python forhåndsberegner *alle* gjennomførbare kombinasjoner av 2–5 stopp (med brute-force-ruteordning), rangerer dem, og gir KI en avgrenset meny å velge fra. KI gjør ikke lenger noen regning selv — den velger kun hvilket alternativ som passer best til det etterspurte temaet.
- **KI sin rolle:** Både Claude og Codex var involvert — Codex diagnostiserte at problemet var en designfeil i hvordan oppgaven var gitt til KI (ikke en grunnleggende begrensning i modellens evner), og Claude vurderte og implementerte løsningen etter egen gjennomgang av forslaget.

**Utfordring 2: For strengt importfilter ga nesten ingen brukbare steder**

- **Problem:** Det første importoppsettet krevde at et sted måtte ha en direkte Wikipedia-lenke for å bli beriket med kildetekst. Av 24 reelle kandidater i testområdet kvalifiserte bare 1.
- **Løsning:** Filteret ble utvidet til å også bruke Wikidata-beskrivelser og OSM sine egne beskrivende tagger (f.eks. kunstnernavn, byggeår) som gyldig — men fortsatt kun ekte, hentet tekst, aldri generert innhold.
- **KI sin rolle:** Feilen ble skrevet av KI og oppdaget gjennom faktisk testing mot levende data, ikke gjennom kodegjennomgang alene — et konkret eksempel på at manuell/praktisk testing avdekket noe automatiserte tester ikke ville fanget opp.

**Utfordring 3: Datakvalitetsproblemer i et eksternt regneark**

- **Problem:** Ved import av gatekunst-datasettet fra Inner West Council inneholdt kildefilen duplikate og plassholder-IDer (f.eks. bokstavelig "##"), "TBC"/"*Title"-plassholdere, og flere adresser som ikke lot seg geokode automatisk.
- **Løsning:** Radnummer i regnearket ble brukt som stabil ID (med en kjent begrensning hvis kildefilen noen gang sorteres om), useriøse rader ble filtrert bort før import, og mislykkede geokodinger ble rapportert eksplisitt i stedet for gjettet.
- **KI sin rolle:** Claude inspiserte rå XML-struktur i regnearket før koding startet og fant disse problemene selv, uten at de var nevnt i den opprinnelige oppgaven — og Codex reproduserte senere (ikke bare leste om) tre reelle feil i importscriptet: gjenbruk av utdatert mellomlagret data, permanent bufring av midlertidige feil ved geokoding, og en uoppdaget duplikat på tvers av datakilder.

### 3.2 Samarbeidsutfordringer

[STUDENT SKRIVER — utfordringer knyttet til teamarbeid og kommunikasjon, hvis relevant]

### 3.3 KI-spesifikke utfordringer

[STUDENT SKRIVER — din egen vurdering av dette]

*Bevis å bygge på (konkrete, verifiserbare hendelser):*
- KI foreslo i starten manuell stedskurering; dette ble avvist av studenten fordi det ville undergravd hele premisset om at katalogen skulle kunne vokse uten manuelt arbeid.
- Under PRD-arbeidet formulerte Claude et krav (FR-19) som lovet en absolutt garanti om at KI "aldri" ville finne på informasjon — en påstand ingen kan garantere om en språkmodell. Studenten fanget opp dette og ba om en mer presis, realistisk formulering (se `ai-prompts.md`, 2026-10-01, punkt 6).
- Senere introduserte Claude en intern selvmotsigelse i det samme kravet (ett sted lovet en automatisert kontrollmekanisme, et annet sted tillot kravet å være oppfylt med kun manuell stikkprøve) — denne selvmotsigelsen ble ikke fanget opp av studenten eller av Claude selv, men av en uavhengig KI-gjennomgangsagent satt opp spesifikt for å stressteste dokumentet.
- Samme uavhengige gjennomgang fant at et sitert tall (en målt unøyaktighet på 20–30 % i rutetidsestimater) var korrekt i sak, men feil kildehenvist til feil dokument av Claude.
- Et konkret selvopplevd eksempel fra denne økten: studenten hadde tidligere (2026-09-29) gitt en stående instruks om å logge alle substansielle prompts i `ai-prompts.md`. Under hele PRD-prosessen (flere dager, mange substansielle prompts) ble denne instruksen ikke fulgt — Claude loggførte i stedet til BMAD sitt interne, prosjekt-eksterne loggsystem, og oppdaget ikke selv at den stående instruksen ikke ble fulgt. Feilen ble kun oppdaget fordi studenten spurte direkte. Et konkret eksempel på at en KI-assistent kan følge én instruks (en prosessrutine) mens den mister en annen, stående instruks av syne over en lengre, flertrinns oppgave.
- Studenten korrigerte flere ganger forslag som ville ha utvidet omfanget av V1 unødvendig (f.eks. at brukerreiser i PRD-et i første utkast ga inntrykk av at "Should"-krav var nødvendige for kjerneflyten; at en "AI-oppsummering av turen"-funksjon i utgangspunktet ble koblet unødvendig tett til live GPS-sporing).

---

## 4. Kritisk vurdering av KI sin påvirkning

[STUDENT SKRIVER — dette kapittelet krever din egne, personlige vurdering. Bruk gjerne de konkrete hendelsene over (og i `docs/ai-development-log.md`/`ai-prompts.md`) som grunnlag, men konklusjonene må være dine.]

### 4.1 Fordeler med KI-assistanse
[STUDENT SKRIVER]

### 4.2 Begrensninger og ulemper
[STUDENT SKRIVER]

*Bevis å bygge på:* se punkt 3.3 over — flere konkrete tilfeller der KI tok feil (rutingmatematikk, et for strengt filter, en selvmotsigende kravformulering, en feilsitert kilde) og der feilen ble fanget opp enten gjennom praktisk testing, en annen KI-agent, eller direkte av deg.

### 4.3 Sammenligning: Med og uten KI
[STUDENT SKRIVER]

### 4.4 Samlet vurdering
[STUDENT SKRIVER]

---

## 5. Etiske implikasjoner

### 5.1 Ansvar og eierskap
[STUDENT SKRIVER]

### 5.2 Transparens
[STUDENT SKRIVER]

### 5.3 Påvirkning på læring og kompetanse
[STUDENT SKRIVER]

### 5.4 Arbeidsmarkedet
[STUDENT SKRIVER]

### 5.5 Datasikkerhet og personvern

Faktuelt grunnlag du kan bygge videre på:
- Jaunt V1 krever ingen brukerkonto for noen funksjon, inkludert favoritter og besøkshistorikk — disse lagres lokalt hos brukeren, ikke på en server.
- Live posisjonsdeling (dersom implementert) krever eksplisitt, tilbakekallbar tillatelse, og posisjonsdata sendes aldri til eller lagres på en server.
- API-nøkler (ruteplanlegging, KI) håndteres server-side i Flask, aldri eksponert til nettleseren.
- Ingen persondata om sluttbrukere ble delt med KI-verktøyene under utvikling — kun prosjektets egen kode, offentlig stedsdata, og kildetekst fra åpne/offentlige registre (Wikipedia, OSM, NSW sitt offisielle kulturminneregister).

[STUDENT SKRIVER — egen refleksjon rundt disse valgene]

---

## 6. Teknologiske implikasjoner

### 6.1 Kodekvalitet og vedlikehold
[STUDENT SKRIVER]

### 6.2 Standarder og beste praksis

Konkret eksempel på at KI *ikke* alltid foreslo beste praksis, og hvordan dette ble håndtert:
- Da NSWs offisielle kulturminneregister (Heritage MapServer) viste seg å blokkere skriptbaserte forespørsler (HTTP 403 for alt som identifiserte seg som et script), var studentens eksplisitte instruks at Claude *ikke* skulle late som en nettleser for å omgå denne sperren, selv om dataene i seg selv var offentlig tilgjengelige. Løsningen ble i stedet en liten, håndplukket og manuelt vedlikeholdt liste over kulturminner — en bevisst avveining mellom automatisering og respekt for datakildens egne tilgangsbegrensninger.
- Et tidlig utkast av frontend-koden hadde en usikker måte å sette inn tekst i kartets popup-vinduer på (potensiell XSS-sårbarhet via direkte strenginnsetting i HTML); dette ble fanget opp i kodegjennomgang og rettet før det ble en del av den fungerende applikasjonen.

[STUDENT SKRIVER — egen vurdering]

### 6.3 Fremtidig utvikling
[STUDENT SKRIVER]

---

## 7. Konklusjon og læring

### 7.1 Viktigste lærdommer
[STUDENT SKRIVER — forslag til stikkord du kan bygge videre på, basert på det faktiske prosjektforløpet:]
1. [STUDENT SKRIVER — f.eks. om å gi KI avgrensede, veldefinerte oppgaver fremfor åpne/sammensatte ("la Python eie regnestykket, la KI eie vurderingen")]
2. [STUDENT SKRIVER]
3. [STUDENT SKRIVER]

### 7.2 Hva ville dere gjort annerledes?
[STUDENT SKRIVER]

### 7.3 Anbefalinger
[STUDENT SKRIVER]

### 7.4 Personlig refleksjon (individuelt)

**Nesbakken:**
[STUDENT SKRIVER — personlig refleksjon over egen læring og utvikling]

---

## 8. Vedlegg (valgfritt)

- Skjermbilder av applikasjonen — [STUDENT LEGGER TIL]
- Lenke til GitHub repository — [STUDENT LEGGER TIL]
- `ai-prompts.md` — fullstendig, ordrett logg over substansielle prompts gjennom prosjektet
- `docs/ai-development-log.md` — detaljert utviklingslogg per sprint
- `_bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/` — produktkravdokument (PRD) og tilhørende beslutningslogg (`.memlog.md`)

---

**Ordantall:** [STUDENT SKRIVER]

**Forventet lengde:** 3000-5000 ord (avhengig av gruppestørrelse og prosjektets kompleksitet)
