# Tilbakemelding på product brief

| | |
|---|---|
| **Gruppe** | G51 – G51-nesbakken |
| **Product brief** | `Product.brief.md` (commit `45f6ce9`) |
| **Tilbakemelding fra** | Faglærer i IBE160 (utarbeidet med KI-støtte) |
| **Dato** | 2026-10-06 |

Vurdert fil: `Product.brief.md` i repoets rot, som er den eneste briefen. Det finnes ennå ikke PRD, arkitektur eller epics.

## Samlet vurdering

- **Bør revideres før dere går videre.** Rett punktene markert «Endre» før dere lager PRD og arkitektur.

**Det som er bra:**

1. Ideen er original og godt formulert: «How can available time be turned into a purposeful walk without requiring the user to plan it themselves?» Kjerneflyten er tydelig (startpunkt, tid, tema → rundtur med stopp på kart), og det er presisert at tiden gjelder hele turen, inkludert tid ved stoppene.
2. Dere tar KI-risikoen på alvor. Kravet om at Jaunt heller skal foreslå et annet tema eller en kortere tur enn å finne på steder, og at KI-teksten skal bygge på kildemateriale med kildehenvisning, er et svært godt prinsipp. Avgrensningen til et testområde i indre Sydney gjør det mulig å kontrollere stoppene.

**De viktigste endringene:**

1. Dropp den automatisk innsamlede stedskatalogen i v1. «An automatically collected and processed catalogue of candidate places and sources» er i seg selv et stort prosjekt (henting, rensing, kategorisering og kildekontroll). Lag heller en håndkuratert liste med 30–50 steder i testområdet, med koordinater, tema og kildetekst. Da kan dere kontrollere at stoppene er ekte, og KI-delen får et trygt grunnlag.
2. Velg karttjeneste og forklar hvordan sensor kan kjøre appen. Ruteberegning og interaktivt kart krever en ekstern tjeneste, og mange krever API-nøkkel og har kostnader. Bestem hvilken tjeneste dere bruker (gjerne en med gratis nivå eller åpne data), og beskriv hvordan sensor kan kjøre appen uten deres nøkler, for eksempel med lagrede eksempelruter.
3. Beskriv hvordan ruten velges. Å finne en rundtur gjennom noen stopp innenfor en tidsramme er et optimeringsproblem. Skriv en enkel regel dere kan forstå og teste, for eksempel «velg de nærmeste relevante stoppene, legg til ett om gangen så lenge estimert total tid er under grensen». Ikke overlat dette til språkmodellen.

## Vanskelighetsgrad og gjennomførbarhet

### Vurdert vanskelighetsgrad

- **Vanskelig**

**Sammenlignbart med:** 3) KI-styrt simulering av prosjektledelse (vanskelig) når det gjelder kompleksitet: flere sammenhengende deler (stedsdata, KI-utvalg, ruteberegning med tidsbegrensning, kart og kildebasert tekst) som alle må virke sammen. Med håndkuratert katalog og enkel ruteregel kan v1 nærme seg middels, sammenlignbart med 7) Kurs-FAQ-chatbot med kildehenvisning.

**Begrunnelse:**

| Faktor | Nivå (lav / middels / høy) | Kommentar |
|---|---|---|
| Domenelogikk – hvor mange og hvor kompliserte regler og beregninger må stemme? | Høy | Utvalg av stopp under tidsbegrensning, rundtur tilbake til start, gangtid pluss tid ved stopp, og når turen skal avvises. |
| Datamodell – antall entiteter og relasjoner mellom dem | Middels | Sted, kilde, tema, rute og stopp i rekkefølge. |
| Brukere, roller og innlogging | Lav | Ingen kontoer i v1. |
| KI-funksjonalitet i appen, f.eks. kall til språkmodell, prompts i koden og håndtering av usikre svar | Høy | KI skal vurdere relevans og skrive tekst som er tro mot kildene, med ærlig avvisning. Krever god prompt-design og kontroll mot oppdiktet innhold. |
| Integrasjoner og eksterne tjenester, f.eks. API-er, betaling og e-post | Høy | Karttjeneste, rutetjeneste og språkmodell, pluss eventuelle kilder for automatisk innsamling. |
| Sanntid, samtidighet eller flere brukere som påvirker hverandre | Lav | Ingen. Posisjon i sanntid er bare en mulig utvidelse. |
| Filhåndtering, f.eks. opplasting, PDF-lesing og eksport | Lav til middels | Ingen opplasting, men innsamling og behandling av kildemateriale ligner filhåndtering. |
| Sikkerhet og personvern | Lav til middels | Startposisjon er en personopplysning hvis den lagres. Unngå å lagre posisjon i v1. |

**Hva vanskelighetsgraden betyr for dere:**

- _Vanskelig:_ Et vanskelig prosjekt gir større mulighet for toppkarakter, men også større risiko. Definer en minimal versjon som sikkert kan bli ferdig, og legg resten i tydelige trinn etterpå.

### Gjennomførbarhet med BMAD og Claude Code

| Spørsmål | Vurdering (OK / risiko / stor risiko) | Kommentar |
|---|---|---|
| **Tid og omfang** – kan v1 realistisk bli ferdig og stabil i løpet av semesteret, med tid til flere iterasjoner? | Stor risiko | Som beskrevet er v1 svært omfattende for én person. Med håndkuratert katalog og enkel ruteregel blir det realistisk. |
| **BMAD-flyten** – er briefen konkret nok til at PRD, arkitektur og stories kan lages uten store hull, og blir det overkommelig mange stories? | Risiko | Brukeropplevelsen er konkret, men de store beslutningene (datainnsamling, rutevalg, karttjeneste) er åpne. De må tas før arkitekturen. |
| **Egnet for Claude Code** – bruker løsningen en vanlig, godt dokumentert teknologistakk som Claude Code håndterer godt, eller krever den nisjeteknologi, spesialmaskinvare eller mye manuell konfigurasjon? | Risiko | Webkart og API-kall er godt dokumentert, men integrasjon mot flere eksterne tjenester krever manuelt oppsett og feilsøking. |
| **Kontroll på KI-ens arbeid** – kan gruppen selv avgjøre om koden gjør det riktige? Krever domenet kunnskap gruppen ikke har, f.eks. avanserte beregninger eller fagregler, så er det vanskelig å kvalitetssikre. | Risiko | Dere kan gå rutene selv, og det er en styrke. Men om KI-teksten stemmer med kildene og om stoppene er relevante, må sjekkes systematisk. |
| **Testbarhet** – finnes det tydelige regler og forventede resultater som tester kan skrives mot? | Risiko | Tidsberegning og ruteregel kan testes med faste eksempler. «Reasonably close to the requested time» og «worth taking» må gjøres målbare, for eksempel innenfor ±15 % av ønsket tid. |
| **Kjørbar for sensor** – kan appen kjøres lokalt etter README, uten gruppens nøkler, betalte kontoer eller egen infrastruktur? | Stor risiko | Kart, ruter og KI krever trolig nøkler. Uten testmodus eller lagrede eksempelruter kan sensor ikke prøve kjernefunksjonen. |
| **Avhengigheter og kostnader** – krever løsningen betalte API-er, f.eks. språkmodeller, og finnes det en plan for kostnad, testmodus eller mock-data? | Risiko | Tre typer eksterne tjenester, ingen plan for kostnad ennå. Velg tjenester med gratis nivå og bufre resultater. |

**Konklusjon om gjennomførbarhet:**

- **Gjennomførbart med justert omfang.** Se forslagene under.

**Forslag til justering av omfang eller vanskelighetsgrad:**

1. Minimal v1: håndkuratert katalog med 30–50 steder i ett eller to av nabolagene, ett tema (for eksempel historie), enkel ruteregel og KI-tekst generert fra kildeteksten. Legg flere temaer, flere nabolag og «surprise me» i neste trinn.
2. Flytt automatisk innsamling av steder til visjonen, eller til et eget trinn helt til slutt. Lag også en testmodus der appen bruker lagrede ruter og ferdige tekster, slik at sensor kan prøve den uten nøkler.

## Hvorfor product brief er viktig for mappen

Product brief er utgangspunktet for PRD, arkitektur, stories og til slutt koden. Del 1 av mappen vurderes blant annet på om sensor kan følge en sporbar vei fra plan til ferdig app. Den vurderes også på om appen gjør det dere har beskrevet, om den er testet, om den er godt designet, og om den kan kjøres etter README. Et uklart, for stort eller for lite brief gjør alt dette vanskeligere senere. Det er mye enklere å rette nå enn sent i semesteret.

## 1. Gjennomgang av briefens deler

| Del av brief | Status | Kommentar |
|---|---|---|
| Executive Summary – er det klart hva appen er, og hvilket problem den løser? | OK | Svært tydelig: tilgjengelig tid blir til en meningsfull gåtur med ekte stopp. |
| The Problem – er problemet konkret, med reelle situasjoner og brukere? | OK | Godt beskrevet, både for kjente og ukjente områder. |
| The Solution – beskriver løsningen brukeropplevelsen, ikke bare teknologi? | Juster | Beskriver opplevelsen godt, men sier lite om hvordan ruten faktisk velges. Legg til en enkel beskrivelse av regelen. |
| What Makes This Different – er vurderingen ærlig og realistisk? | OK | Ærlig: forskjellen er at turen starter med tiden, ikke med et mål. |
| Who This Serves – er primærbrukerne tydelige, og vet vi hva de trenger? | OK | To tydelige brukertyper, og mobilbruk er tatt hensyn til. |
| Success Criteria – kan kriteriene faktisk sjekkes eller testes? | Juster | Gode retninger, men «reasonably close», «relevant» og «worth taking» må få konkrete grenser og en metode for kontroll. |
| Scope – er det klart hva som er med i første versjon, og hva som ikke er det? | Endre | Klart beskrevet, men for stort for v1, særlig den automatisk innsamlede katalogen og fire temaer. Reduser som foreslått over. |
| Vision – henger visjonen sammen med resten uten å blåse opp omfanget? | OK | Flere steder, lyd og brukerbidrag er tydelig lagt etter v1. |

## 2. Utgangspunkt for del 1 av mappen

Punktene følger kriteriene i sensorveiledningen for del 1. Vektene i parentes viser hvor mye hvert kriterium teller i del 1.

| Kriterium i del 1 | Hva briefen bør legge til rette for | Status | Kommentar |
|---|---|---|---|
| **1. Prosess og KI-styring** (30 %) | Brief som er presis nok til at PRD og stories kan bygges direkte på den, slik at krav kan spores fra brief til kode. | Juster | Godt skrevet, men repoet har bare én opplasting. Commit jevnlig, bruk BMAD videre og lagre promptene. Ta de store beslutningene skriftlig før arkitekturen. |
| **2. Funksjonalitet og omfang** (20 %) | Realistisk omfang for gruppen og semesteret: en tydelig kjerneflyt som kan bli ferdig og stabil, og nok innhold til å vise reell funksjonalitet. | Endre | Ambisiøst og interessant, men for stort som beskrevet. En minimal v1 med kuratert katalog gir fortsatt mye å vise. |
| **3. Kvalitetssikring og testing** (15 %) | Suksesskriterier og funksjoner som er konkrete nok til å bli testtilfeller. | Juster | Planen om å sammenligne estimert og faktisk tid er god. Legg til faste testtilfeller for ruteregelen og en sjekkliste for KI-tekst mot kilde. |
| **4. Design og brukeropplevelse** (10 %) | Tydelige brukere og brukssituasjoner som designet kan bygges rundt, gjerne med de viktigste skjermbildene eller flytene skissert. | OK | Mobil-først og bruk under gåtur gir et tydelig designgrunnlag. Skisser startskjerm, kart og stoppvisning. |
| **5. Kodekvalitet og arkitektur** (10 %) | Teknologivalg som er begrunnet og ikke mer komplekse enn appen trenger. | Juster | Teknologi er ikke valgt ennå. Hold det enkelt: én webapp, én karttjeneste og en lokal datafil eller enkel database for katalogen. |
| **6. README og kjørbarhet** (10 %) | Løsning som andre kan kjøre lokalt uten betalte kontoer, og uten tilgang til gruppens egne tjenester og nøkler. | Endre | Kjernefunksjonen er avhengig av eksterne nøkler. Planlegg testmodus med lagrede ruter og tekster. |
| **7. Ryddighet i repoet** (5 %) | En plan for hvor hemmeligheter, testdata og dokumentasjon skal ligge. | Juster | Bestem hvor stedskatalogen og kildene ligger, og hold API-nøkler i `.env` utenfor Git. Vurder også lisens og bruksvilkår for kildematerialet. |

## 3. Neste steg for gruppen

1. Reduser v1: håndkuratert katalog, ett tema og ett avgrenset område. Oppdater Scope.
2. Velg karttjeneste og språkmodell, og beskriv testmodus for sensor (lagrede ruter og tekster).
3. Skriv ruteregelen og tidsberegningen inn i briefen, med to–tre eksempler på forventet resultat, før dere lager PRD.

Oppdater product brief i repoet når dere har gjort endringene, slik at historikken viser hvordan planen utviklet seg. Det er en del av prosessen sensor ser etter.
