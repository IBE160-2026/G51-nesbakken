# Tilbakemelding på PRD

| | |
|---|---|
| **Gruppe** | G51 – G51-nesbakken |
| **PRD vurdert** | `_bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/prd.md` (status `final`, sist endret 2026-10-20, commit 300129f). Addendum i samme mappe er lest. |
| **Dato** | 2026-11-12 |
| **Type** | Formativ tilbakemelding, ikke karakter |

## 1. Samlet inntrykk

Dette er en PRD med tydelig eierskap: en klar tese (tid som førsteklasses input, ærlig avvisning heller enn svak rute), 24 nummererte FR-er med testbare konsekvenser, og uvanlig åpenhet om hva som ikke er bygget. Risikoen for veien videre er størrelsen: dokumentet er tungt (ca. 8 700 ord), Must-nivået hviler på flere deler som ennå ikke finnes, og det står ingenting om hvordan appen kan kjøres og testes uten nøkler og kostnader.

## 2. Dette fungerer godt

- **Tesen og ærligheten.** §1: «it would rather say "that doesn't quite work, try this instead" than manufacture a route out of weak or irrelevant stops». FR-9 gjør dette til testbare krav, blant annet at forslag til tidsjustering alltid må være *mer* tid, og at tjenestefeil skilles fra «ingen passende tur».
- **KI-kontroll.** FR-19 sier at grunnlag i kilder er en «design constraint and a checked process», og krever både automatisk kontroll og manuell stikkprøve, med definert reserveløsning når kontrollen feiler. Skillet mellom Source Excerpt og Contextual Source hindrer at generell kunnskap presenteres som fakta om ett bestemt sted.
- **Presise begreper og målemetoder.** De fire Stop Engagement States (Proposed / Opened / Visited / Favourited) holdes konsekvent fra glossar via FR-13, FR-16, FR-17 og FR-18. SM-2 har asymmetrisk toleranse (maks 25 % under, maks 10 % over), og SM-C1/SM-C2 er ekte motmål.

## 3. Oversikt per dimensjon

| Dimensjon | Vurdering | Kort begrunnelse |
|---|---|---|
| Beslutningsklarhet | god | Avveininger er synlige (f.eks. FR-5 stoppgrense målt til 7, FR-1 uten geofence), men OQ13 står både som «still open» og «resolved», og mange spørsmål er ryddet halvveis. |
| Substans | sterk | Innholdet er produktspesifikt og begrunnet; lite pynt. |
| Strategisk sammenheng | god | Tydelig tese, men Should-listen har ti punkter og gir delvis backlog-preg. |
| Testbarhet | god | De fleste FR-er har konsekvenser, men «genuinely relevant» og «sufficiently relevant» kan ikke testes, og SM-1/3/4/5/6 mangler terskler. |
| Scope og avgrensning | god | Non-goals og kjente hull er svært eksplisitte, men Must-nivået er stort og delvis uplanlagt (se 4.2). |
| Brukbarhet for neste fase | god | ID-er og glossar er stort sett konsistente, men krav, endringshistorikk og implementasjonsdetaljer er blandet. |
| Formtilpasning | god | UJ med navngitte hovedpersoner passer; dokumentet er likevel for langt til å brukes som oppslagsverk. |

## 4. Viktigste forbedringer

### 4.1 Testmodus, nøkler og kostnad er ikke omtalt
- **Alvorlighet:** høy
- **Hvor:** §7 Constraints, §6.1 Must; ingen FR eller NFR nevner det
- **Problem og hvorfor det betyr noe:** FR-5 og FR-19 bygger på rutetjeneste og språkmodell (og FR-19s verifiseringskall kan bli et ekstra modellkall). PRD-en sier ikke hvordan appen kjøres og testes uten nøkler, hva ett KI-kall koster, eller hva som skjer når kvoten er brukt. Dette var også et hovedpunkt i briefen. Uten krav kan ikke arkitektur og stories planlegge mock, cache eller fast eksempeldata.
- **Forslag:** Legg til et Must-krav, for eksempel: «FR-25: Appen kan kjøres i testmodus uten API-nøkler. Testmodus bruker lagrede rutematriser og ferdig genererte Stop-tekster for minst tre faste kombinasjoner av start, tid og Topic. Konsekvens: samme input gir samme Route; ingen nettverkskall til rute- eller språkmodelltjeneste skjer (verifiseres i test).» Legg også til en NFR om grense for KI-kall per forespørsel og hva brukeren ser når tjenesten er utilgjengelig (FR-9 dekker dette delvis for ruting).

### 4.2 Must-nivået er større enn det ser ut
- **Alvorlighet:** høy
- **Hvor:** §0 «Known planning gaps», FR-6 «Depends on route-geometry work not yet built», §9 OQ14
- **Problem og hvorfor det betyr noe:** §0 sier selv at frontend for oppsett og ruteoversikt ikke har noen sprint, at FR-6 ikke kan fullføres før rutegeometri er bygget, og at AI-innhold med grunnlagskontroll (FR-19) er «the largest unbuilt piece». Samtidig har dere 24 FR-er, hvorav ti Should. Dere beskriver problemet godt, men PRD-en sier ikke hva som er den minste versjonen som kan leveres hvis tiden blir knapp.
- **Forslag:** Definer «minimum gåbar V1» som en egen setning i §6.1, for eksempel: «Minimum gåbar V1 = FR-1, 2, 3, 5, 7, 8, 9, 12, 19, 20 med rette linjer mellom stopp i stedet for gangrute (FR-6 reduseres til: kart med stoppmarkører og total tid).» Flytt FR-14, 21, 22, 23 og 24 til én «Etter minimum»-liste uten rangering, så Should-listen ikke leses som en plan.

### 4.3 Myke formuleringer i Must-krav og målinger
- **Alvorlighet:** høy
- **Hvor:** FR-5 «genuinely relevant», FR-9 «sufficiently relevant», SM-1 «worth taking», SM-3 «rated real and relevant»
- **Problem og hvorfor det betyr noe:** Disse kan ikke bli testtilfeller, og story-skriving og testing vil gjette terskelen. OQ6 (minste tidsbruk) er fortsatt åpen.
- **Forslag:** FR-5: «Hver foreslåtte Route har minst 2 Stops med Record Status `ready`; hvert Stop har valgt Topic (unntatt «surprise me»); gangtid + 5 min per Stop er ≤ ønsket tid. Testes på faste kombinasjoner av start, tid og Topic.» SM-1: «Minst 5 testpersoner; minst 4 av 5 gir 4 eller 5 av 5 på «verdt å gå».» Gjør tilsvarende for SM-3 til SM-6 (antall stopp vurdert, antall infeasible forespørsler i SM-6).

### 4.4 Krav, endringshistorikk og implementasjonsdetaljer er blandet
- **Alvorlighet:** medium
- **Hvor:** FR-1 («Revised 2026-10-18 (checked against the actual code…)»), FR-3, FR-5, §7 («168/168 passing»)
- **Problem og hvorfor det betyr noe:** Konsekvensene i FR-1 er et avsnitt med begrunnelse og filnavn (`planner.py`, `PILOT_BBOX`). Det gjør det vanskelig å se selve kravet og å skrive acceptance criteria. Historikken («Corrected…, independent review caught…») hører til i en endringslogg.
- **Forslag:** FR-1 kan bli: «En valgt startposisjon godtas uavhengig av Pilot Area. Hvis færre enn 2 `ready` Stops ligger innen rekkevidde, vises FR-9s fallback.» Flytt begrunnelse, målinger og revisjonsnotater til addendum, og testantall til en test-rapport.

### 4.5 Opprydding i status, spørsmål og begreper
- **Alvorlighet:** lav
- **Hvor:** frontmatter `status: final`; §9 OQ8 og OQ18 (overstrøket), OQ13; §3 «Jarrod»; §10
- **Problem og hvorfor det betyr noe:** Status `final` med 20 åpne spørsmål gir uklart signal. «Jarrod» (i Contextual Source og addendum) og «Jaunty»/«Jaunt character» er ikke definert i glossaret.
- **Forslag:** Flytt løste spørsmål til en egen «Resolved»-liste, del OQ13 i to, legg til Jaunt-karakteren og «Jarrod» i glossaret, og gjør §10 komplett.

## 5. Mekaniske funn

- FR-23 står mellom FR-6 og FR-7, og FR-24 foran FR-2 (rekkefølge i dokumentet følger ikke nummer). SM-7 står blant Primary uten at det gir feil, og det er forklart.
- §10 har tre oppføringer; oppføringen for FR-3 er en «superseded»-note uten tilsvarende inline `[ASSUMPTION]`. Kun §1 og FR-2 har inline-tagger.
- Referanser til `docs/product-brief.md` og `docs/architecture-plan.md`: kontroller at stiene stemmer med repoet i dag (briefen er `Product.brief.md` i rot).
- UJ-1 og UJ-2 har navngitte hovedpersoner; de er nesten like i flyt, men er knyttet til konkrete FR-er (FR-4), så de gjør nytte.

## 6. Før dere går videre

**Må avklares før UX, arkitektur og epics:**
- Testmodus og kostnadsgrenser (4.1).
- Minimum gåbar V1 og håndtering av FR-6 uten rutegeometri (4.2).
- Terskler for «relevant» og SM-ene (4.3).
- Metode for grunnlagskontroll i FR-19 (OQ10) og hva AI-teksten testes mot; OQ11 om tynne kildetekster bør avklares tidlig, siden det avgjør om innholdet er verdt å lese.
- OQ20 («X min left») fordi det kan skjule ny beregning.

**Kan vente:** OQ1, 3, 4, 5, 7, 9, 12, 16, 17 og FR-21 til FR-24.

**Oppfølging av briefen:** delvis. Ruteregelen er nå beskrevet (Shortlist, Option Menu, brute-force-ordning med målt stoppgrense), og tidsmålet har tall (SM-2). Rådet om mindre scope og håndkuratert katalog er bevisst ikke fulgt, og testmodus for sensor mangler fortsatt (4.1).

## 7. Refleksjonsspørsmål

1. Mange «Revised … caught an error»-notater viser at dere har lest KI-tekst kritisk mot faktisk kode. Hvordan sjekket dere hver gang at KI-en hadde rett, og hva gjør dere for at slike feil fanges før de havner i PRD-en?
2. FR-19 krever at KI-innhold sjekkes automatisk. Hvilket konkret eksempel på en feil tekst vil sjekken fange, og hvordan viser dere i en test at den faktisk gjør det?

_Vurdert mot kvalitetsrubrikken i bmad-prd. Dette er veiledning, ikke sensur._
