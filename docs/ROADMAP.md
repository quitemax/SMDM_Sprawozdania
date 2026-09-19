# Plan dalszych prac

Ten dokument opisuje kolejne etapy budowy systemu, w kolejności w jakiej
mają sens do realizacji. Stan na podstawie `README.md`, `docs/INSTALLATION.md`
i `docs/PROJECT_MEMORY.md`.

## Plan na najbliższą sesję (ustalone 2026-08-20)

Kolejność uzgodniona z użytkownikiem:

1. **Diaryzacja** (rozpoznawanie mówców) — zrobione 2026-08-21:
   - [x] token dostępu HF + akceptacja warunków modeli pyannote
     (`docs/INSTALLATION.md`, sekcja o tokenie HF),
   - [x] token przekazywany do skryptu przez zmienną środowiskową
     `HF_TOKEN`, nie hardkodowany w kodzie — zgodnie z `docs/AGENTS.md`,
   - [x] dodano do `scripts/transcribe.py` krok diaryzacji
     (`whisperx.diarize.DiarizationPipeline` + `whisperx.assign_word_speakers`),
     domyślnie włączony (`--no-diarize`, żeby wyłączyć); domyślny model
     pipeline'u to `pyannote/speaker-diarization-community-1` (nowy domyślny
     model w WhisperX 3.8.6, nie `speaker-diarization-3.1` jak pierwotnie
     zakładano — działa z tym samym tokenem, bez dodatkowej akceptacji),
   - [x] stare ostrzeżenia o `torchcodec`/TF32 nadal nieszkodliwe przy
     realnym użyciu diaryzacji. Pojawiło się nowe, osobne ostrzeżenie z
     `pyannote.audio` (`pooling.py`, `std(): degrees of freedom is <= 0`)
     przy pierwszym teście na krótkim pliku — do obserwacji na dłuższych,
     prawdziwych nagraniach (może nie występować przy dłuższym materiale).
   - [x] test na `input/audio/test.mp3` — poprawne etykiety `[SPEAKER_00]`
     (patrz `docs/HISTORY.md`).
2. **Instalacja Ollama i wybór modelu językowego** (zrobione 2026-08-21):
   - [x] instalacja Ollama (`docs/INSTALLATION.md`, sekcja 5),
   - [x] wybór modelu: `SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M` (6.7 GB
     na dysku, dobre wsparcie języka polskiego) — mieści się niemal
     w całości w 8 GB VRAM RTX 4060 Laptop (`ollama ps`: 19%/81%
     CPU/GPU przy kontekście 4096),
   - [x] podstawowy test na prostym prompcie w języku polskim — odpowiedź
     poprawna gramatycznie i merytorycznie (patrz `docs/HISTORY.md`).
   - [ ] docelowa długość kontekstu do analizy całego spotkania (model
     wspiera do 32K) może wymagać większego offloadu na CPU — do
     sprawdzenia przy realnym teście na dłuższej transkrypcji (Etap 4).
3. **Test na prawdziwym nagraniu z datą** — zrobione 2026-08-21:
   - [x] uruchomiono `scripts/transcribe.py` (z diaryzacją) na
     `input/audio/2025.06.27/250620_0233.MP3` (nagranie 90 min),
   - [x] ocena jakości: bardzo dobra — poprawnie rozpoznany przebieg
     zebrania (porządek obrad, głosowania), poprawnie rozróżnieni
     poszczególni mówcy w wielogłosowej dyskusji (1035 segmentów). Szczegóły
     treści nie są zapisywane w dokumentacji (dane poufne, patrz
     `docs/AGENTS.md`).
   - [x] czas przetwarzania odnotowany w `docs/HISTORY.md` — diaryzacja na
     długim materiale zajęła znacznie więcej niż na krótkim `test.mp3`
     (nieliniowo względem długości nagrania) — do uwzględnienia przy
     planowaniu pracy z dłuższymi nagraniami (Etap 4).

## Etap 0 — Porządkowanie danych wejściowych (zrobione)

- [x] Uporządkowanie `input/temp/` — katalog usunięty, nagrania rozłożone
      do `input/audio/RRRR.MM.DD/` wg daty spotkania.
- [x] Przygotowano `input/audio/test.mp3` — krótki plik do testów pipeline'u.
- [x] `input/historical_data/reports/` — uzupełnione historycznymi
      protokołami RN (2024-2026, .docx i miejscami dodatkowo .pdf tego
      samego dokumentu). Konwersja na Markdown (`input/historical_data/reports_md/`)
      nowym `scripts/docx_to_markdown.py` (zrobione 2026-08-30) — 18 plików,
      wszystkie natywne .docx (bez OCR, więc wyższa jakość niż konwersja
      PDF); duplikaty .pdf (ten sam protokół wyeksportowany też do PDF)
      pomijane, gdy istnieje odpowiadający .docx. Znane uproszczenia:
      pogrubienie/kursywa wykrywane tylko z formatowania wprost na
      fragmencie tekstu (nie ze stylu akapitu), listy numerowane
      renumerowane sekwencyjnie od 1 (bez odtwarzania formatu a/b/c
      z Worda).
- [ ] `input/historical_data/transcripts/` wciąż puste.
- [x] Katalog `input/knowledge/` (regulaminy, uchwały, umowy — w większości
      skany) konwertowany na Markdown w `input/knowledge_md/` przez nowy
      `scripts/pdf_to_markdown.py` (zrobione 2026-08-22) — baza wiedzy do
      audytu i odwoływania się w sprawozdaniach. Strony bez warstwy
      tekstowej przechodzą przez OCR (Tesseract, `pol`); dokumenty
      (częściowo) rozpoznane przez OCR mają notkę ostrzegawczą na
      początku pliku `.md` (jakość dobra dla treści merytorycznej,
      słabsza przy podpisach/pieczątkach — patrz `docs/HISTORY.md`).
      Wykorzystanie tej bazy jako kontekstu dla modelu przy analizie
      treści spotkań — do ustalenia przy Etapie 4.
- [ ] Weryfikacja zawartości `examples/` — nadal zrzut niepowiązanych danych
      prywatnych (zdjęcia/SMS z 2020, katalog `Downloads/DCIM/...`), a nie
      przykładowe raporty spółdzielni opisane w README.

## Etap 1 — Dokończenie środowiska

- [x] PyTorch 2.8.0+cu128, WhisperX 3.8.6 zainstalowane w `.venv` (zgodnie
      z pinami w `docs/INSTALLATION.md`).
- [x] Instalacja i konfiguracja Ollama (`docs/INSTALLATION.md`, sekcja 5).
- [x] Wybór modelu językowego do analizy treści i generowania raportów —
      `SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M` (patrz plan sesji wyżej).
- [x] Token HuggingFace + akceptacja warunków modeli pyannote —
      wymagane przez WhisperX do diaryzacji (rozpoznawania mówców).
- [x] Spisanie testu instalacji (`docs/INSTALLATION.md`, sekcja 7) —
      minimalny skrypt/procedura potwierdzająca, że WhisperX, PyTorch+CUDA
      i Ollama działają poprawnie na danym komputerze.
- [x] Utworzenie katalogów `scripts/` i `prompts/` (są w opisie struktury
      w README).
- [x] Ustalenie zawartości `config/` — `config/config.yaml` (ścieżki
      wejścia/wyjścia, nazwa modelu Ollama, parametry WhisperX: język,
      diaryzacja, rozmiar modelu, batch size). Wczytywany przez
      `scripts/config.py`, używany jako domyślne wartości w
      `scripts/transcribe.py` (nadpisywalne parametrami CLI).

## Etap 2 — Transkrypcja i diaryzacja

- [x] Skrypt `scripts/transcribe.py` uruchamiający WhisperX na pliku audio
      z `input/audio/`, zapisujący transkrypcję (`.txt` + `.json` z
      segmentami) do `output/transcripts/`, z odtworzeniem struktury
      podkatalogów dat.
- [x] Pierwszy test na `input/audio/test.mp3` — zakończony sukcesem
      (8 segmentów), 2026-08-20.
- [x] Włączenie rozpoznawania mówców (diaryzacja, domyślnie włączona,
      `--no-diarize` żeby wyłączyć) i oznaczenie ich w transkrypcie —
      zrobione 2026-08-21, przetestowane na `test.mp3`.
- [x] Test na rzeczywistym nagraniu (`2025.06.27`, 90 min, wielu mówców) —
      wynik bardzo dobry (patrz krok 3 planu sesji wyżej).
- [x] Przetworzono całą zawartość `input/audio/` (17 nagrań, ~37h audio) —
      transkrypcja + diaryzacja + propozycja mówców + czyszczenie,
      zakończone 2026-08-26. Napotkane i rozwiązane problemy
      operacyjne (patrz `docs/HISTORY.md`):
      - model Ollamy pozostający załadowany w VRAM powodował timeout
        (600s) identyfikacji mówców przy równoległym przetwarzaniu —
        rozwiązanie: `ollama stop <model>` przed każdą transkrypcją,
      - jedno nagranie (`260415_0257`, 260 min) failowało z CUDA OOM przy
        domyślnym `--batch-size 16`, mimo że dłuższe nagranie (288 min)
        przeszło bez problemu — naprawione przez `--batch-size 8` dla
        tego pliku; przyczyna nieznana (prawdopodobnie fragmentacja
        pamięci CUDA przy długim pojedynczym przebiegu, nie sama
        długość nagrania).
- [ ] 2026-08-30: dodano 13 nowych nagrań do `input/audio/` (m.in.
      2025.01.22–2025.06.03, 2025.12.10 x6, 2026.06.01, 2026.06.22,
      łącznie ~18h) — przetwarzanie (transkrypcja + diaryzacja +
      propozycja mówców + czyszczenie) uruchomione w tle wg rosnącego
      czasu trwania, w toku.

## Etap 3 — Przetwarzanie transkrypcji

- [x] Propozycja mapowania SPEAKER_XX → imię/nazwisko —
      `scripts/identify_speakers.py` (zrobione 2026-08-21). Szuka w
      transkrypcie fragmentów, gdzie ktoś się przedstawia albo zwraca do
      kogoś po imieniu (heurystyka regex), i prosi model Ollama o
      wywnioskowanie tożsamości mówców z kontekstu. Wynik zapisywany jako
      osobny plik `<nazwa>.speakers.json` obok transkrypcji — **wyłącznie
      propozycja do ręcznej weryfikacji** (Etap 5), transkrypcja nie jest
      automatycznie modyfikowana (decyzja projektowa, patrz
      `docs/PROJECT_MEMORY.md`).
      Znane ograniczenia (model 11B, kwantyzacja Q4_K_M) — patrz
      `docs/HISTORY.md`: model czasem myli osobę, o której się mówi/cytuje
      jej wiadomość, z faktycznym mówcą (mimo jawnej instrukcji w
      prompcie), i nie zawsze zwraca wynik dla wszystkich mówców mimo
      takiego polecenia. Nie warto dalej optymalizować promptu bez
      większego modelu — do rewizji przy Etapie 4.
      Docelowo (świadomie odłożone): wykorzystanie `input/knowledge/` i
      `input/historical_data/` jako dodatkowego kontekstu (znani
      członkowie Zarządu/Rady) do poprawy trafności.
- [x] Oczyszczanie transkrypcji i ujednolicony format pośredni —
      `scripts/clean_transcript.py` (zrobione 2026-08-21). Skleja kolejne
      segmenty tego samego mówcy oddalone o mniej niż 2 sekundy w jedną
      „turę" (mówca + zakres czasu + tekst) i usuwa segmenty będące
      wyłącznie izolowanym wypełniaczem (np. samo "yyy", "eee"). Nie
      poprawia błędów rozpoznawania w środku zdań ani nie usuwa
      wypełniaczy typu "no" wplecionych w zdanie — bez pełnej analizy
      językowej ryzyko zniekształcenia sensu wypowiedzi jest zbyt duże
      (świadomie odłożone/pominięte). Wynik: `<nazwa>.clean.json`
      (`{"turns": [...]}`) i `<nazwa>.clean.txt` (`[HH:MM:SS] MÓWCA: tekst`)
      obok transkrypcji. Test na prawdziwym nagraniu (`2025.06.27`):
      1035 segmentów → 346 tur, wynik czytelny i spójny (patrz
      `docs/HISTORY.md`).
      Aktualizacja 2026-08-21: jeśli obok istnieje `<nazwa>.speakers.json`
      (z `identify_speakers.py`), wykryte imiona są od razu podstawiane w
      etykiecie mówcy w `.clean.txt`/`.clean.json` (pole `speaker_display`),
      zawsze oznaczone jako propozycja, np. `Leon (SPEAKER_07?)` — surowa
      etykieta `speaker` (SPEAKER_XX) zostaje zachowana osobno w JSON.
      Utrzymuje to zasadę „tylko propozycja do weryfikacji” z
      `docs/PROJECT_MEMORY.md`, ale ułatwia przegląd bez ręcznego
      zerkania do osobnego pliku.
- [x] Ręczna identyfikacja mówców po głosie — `scripts/extract_speaker_samples.py`
      (zrobione 2026-08-30). Wycina dla każdego SPEAKER_XX 2 najdłuższe
      wypowiedzi (do 20s) z oryginalnego pliku audio i dopisuje ścieżki do
      `<nazwa>.speakers.json` (pole `audio_samples`) — do odsłuchania i
      ręcznego uzupełnienia `proposed_name` (`source: "manual"`, wtedy
      `clean_transcript.py` nie oznacza etykiety znakiem zapytania). Ten
      sam plik jest współdzielony z `identify_speakers.py` i scalany
      niezależnie od kolejności uruchamiania — żaden ze skryptów nie
      nadpisuje wpisu potwierdzonego ręcznie. Motywacja: realny przypadek
      błędnej propozycji modelu w parze z posiedzeniem 27.06.2025 (patrz
      `docs/PROJECT_MEMORY.md`).
- [x] Szablon metadanych spoza transkrypcji — `scripts/init_meeting_info.py`
      (zrobione 2026-08-30). Tworzy `<nazwa>.meeting_info.json` (lista
      obecności, protokolant, sekretarz, przewodniczący) do ręcznego
      uzupełnienia — te dane nie są wiarygodnie odtwarzalne z samego
      nagrania (patrz `docs/PROJECT_MEMORY.md`). Potrzebne jako wejście
      dla Etapu 4.

## Etap 4 — Analiza treści i generowanie raportu

- [x] Wstępna analiza par transkrypcja↔protokół (2026-08-30, na parze z
      27.06.2025): protokół to silnie skompresowana, sformalizowana
      wersja przebiegu — spory osobiste/dygresje całkowicie pomijane,
      zostaje tylko treść proceduralna. Stałe formuły (np. „Rada
      Nadzorcza w obecności X członków, Y głosami za... podjęła uchwałę
      Nr N/R/RR") powtarzające się we wszystkich 18 przekonwertowanych
      protokołach. Dwie niezależne numeracje w skali roku kalendarzowego:
      `Protokół nr N/R/RR` (per spotkanie) i `Uchwała Nr N/R/RR` (wspólny
      licznik przez wszystkie spotkania roku).
- [x] `scripts/generate_report.py` — generator PROJEKTU sprawozdania
      (zrobione 2026-09-17, przetestowane na posiedzeniu 22.06.2026, dla
      którego istnieje już gotowe sprawozdanie `Protokół 8 RN 22.06.2026.md`
      — pozwoliło to bezpośrednio porównać wynik z rzeczywistością).
      **Decyzja projektowa (2026-09-17):** zamiast wymuszać dokładne
      odtworzenie zwięzłej struktury historycznych protokołów (ścisłe
      przypisanie każdej wypowiedzi do jednego z ponumerowanych punktów
      porządku obrad), priorytetem jest wierna i kompletna relacja z
      przebiegu spotkania — nawet jeśli wynikowy dokument jest dłuższy niż
      typowy historyczny protokół. Decyzja podjęta po trzech nieudanych
      próbach wymuszenia ścisłego podziału (patrz niżej) — pokazały one,
      że to sztywne wymaganie samo w sobie generowało błędy.
      Architektura (patrz też docstring modułu):
      1. Porządek obrad — małe zapytanie o początek transkrypcji (tylko
         nagłówek informacyjny w dokumencie, bez wymuszania przypisania).
      2. Chronologiczna relacja — transkrypcja w kawałkach po ~45
         wypowiedzi (mieszczą się w kontekście modelu); każdy kawałek
         zwraca: wierny akapit o przebiegu, uchwały faktycznie podjęte (z
         wynikiem głosowania), sprawy załatwione nieformalnie.
      3. Deduplikacja uchwał (`deduplicate_resolutions`, próg podobieństwa
         tematów `difflib.SequenceMatcher` ≥ 0.65) — ten sam temat bywa
         wykryty w kilku, niekoniecznie sąsiednich kawałkach (np. gdy
         dyskusja do niego wraca później), co bez deduplikacji dawało
         zawyżoną liczbę „uchwał" i przesuwało numerację.
      4. Renderowanie — deterministyczne (czysty Python), stałe formuły
         głosowań/uchwał; numer kolejnej uchwały liczony automatycznie
         (skan `input/historical_data/reports_md/` w poszukiwaniu
         najwyższego użytego numeru w danym roku + 1).
      Wynik testu na posiedzeniu 22.06.2026: 4/4 uchwały zgodne z
      prawdziwym protokołem (temat i numeracja 51-54/R/26), pełna,
      chronologiczna i rzeczowa relacja z przebiegu, brak treści o
      sporach osobistych, sekcja „Sprawy wniesione" bogatsza niż w
      oryginale (19 pozycji vs. jedno zdanie w historycznym protokole).
      **Znane, nieusunięte do końca ograniczenie:** model czasem mimo
      instrukcji kopiuje fragmenty dosłownych, nieformalnych wypowiedzi
      zamiast parafrazować (częściowe zabezpieczenie:
      `strip_verbatim_quotes` w kodzie) — projekt zawsze wymaga redakcji
      przez człowieka przed użyciem, nigdy nie jest to gotowy dokument.
      Odrzucone wcześniejsze podejścia (i dlaczego):
      - cała transkrypcja w jednym zapytaniu — przy dłuższych nagraniach
        (~27k+ tokenów) przekraczało limit kontekstu, Ollama ucinała
        początek promptu (akurat porządek obrad), model zmyślał resztę;
      - sztywne okna czasowe streszczane od razu z przypisaniem do punktu
        porządku obrad — okna przecinały dyskusję w połowie punktu,
        mieszając treść sąsiednich punktów, czasem gubiąc wynik głosowania;
      - osobny przebieg „tagujący" przypisujący wypowiedzi do punktów
        przed streszczaniem — model przypisywał zbyt szerokie, nakładające
        się zakresy (suma przypisanych wypowiedzi przekraczała łączną
        liczbę wypowiedzi w nagraniu), więc niemal każdy punkt
        „dziedziczył" cudze treści i fikcyjne uchwały.
- [ ] Walidacja na kolejnych parach transkrypcja↔protokół (mamy więcej niż
      jedną — patrz `input/historical_data/reports_md/` i odpowiadające
      daty w `output/transcripts/`) — jedno udane porównanie to za mało,
      żeby uznać podejście za w pełni sprawdzone.
      Uwaga metodologiczna: `speakers.json` dla tamtej pary miał ręcznie
      potwierdzone (`source: manual`) etykiety mówców — przy meczach bez
      takiej ręcznej weryfikacji jakość wejścia (a więc i wyniku) może być
      niższa.
- [ ] Zapisanie ustaleń o strukturze/formułach protokołu jako plik
      referencyjny w `prompts/` (na razie tylko w kodzie i tutaj).
- [ ] Generowanie dla nagrania bez istniejącego sprawozdania (np.
      najnowsze RN z 10.08.2026) — dotąd testowane tylko na meczu z
      gotowym protokołem do porównania.

## Etap 5 — Weryfikacja przez pracownika

- [x] Jasne oznaczenie w wygenerowanym pliku, że to **projekt** raportu
      wymagający sprawdzenia przez człowieka, nie wersja ostateczna —
      ostrzeżenie na początku `output/reports/<data>/<nazwa>.draft.md`
      (patrz `scripts/generate_report.py`).
- [ ] Ustalenie formy weryfikacji projektu raportu (na razie: ręczna
      edycja pliku `.md`) — decyzja projektowa do zapisania w
      `docs/PROJECT_MEMORY.md`, jeśli dojdzie coś bardziej rozbudowanego.
- [ ] **Do zrobienia po otrzymaniu zredagowanej wersji od pracownika
      spółdzielni** (2026-09-17, dot. projektu z 10.08.2026): osobny krok
      porównania draftu z wersją zredagowaną przez człowieka, żeby
      dopracować prompt w `generate_report.py` pod kątem tego, co ludzie
      faktycznie uznają za zbędne. Zgłoszony konkretny przykład: zdanie
      „...jednak dyskutowano nad jego kompetencjami, szczególnie w
      kontekście kontaktów z mieszkańcami” — komentarz/wątpliwość co do
      kompetencji jest zbędny, powinien zostać sam fakt (rozważano
      przeniesienie na stanowisko). Ogólniej: model czasem dorzuca do
      streszczenia interpretacyjne niuanse/wątpliwości zamiast trzymać
      się gołych faktów i decyzji — do zawężenia instrukcji w
      `CHUNK_PROMPT_TEMPLATE`, gdy będzie więcej takich przykładów.

## Etap 6 — Dokumentacja końcowa

- [ ] Uzupełnienie `docs/HOW_TO_USE.md` (celowo odłożone na koniec —
      instrukcja obsługi całego pipeline'u krok po kroku).
- [ ] Aktualizacja `README.md` (sekcja „Status”) po osiągnięciu działającego
      end-to-end przepływu.
- [ ] Wpis podsumowujący w `docs/HISTORY.md`.

## Etap 7 — Test end-to-end

- [x] Porównanie projektu raportu z odpowiadającym mu raportem historycznym
      (posiedzenie 22.06.2026) — patrz Etap 4, 4/4 uchwał trafionych.
- [x] Pełny przebieg: nagranie → transkrypcja → identyfikacja mówców →
      metadane spotkania → projekt raportu, na rzeczywistym nagraniu bez
      gotowego raportu (10.08.2026, zrobione 2026-09-17) — pierwszy
      kompletny przebieg całego pipeline'u na „żywym” przypadku. Ocena
      użytkownika: dobra, jeden drobny przykład zbędnego detalu do
      poprawy przy okazji (patrz Etap 5).

## Etap 8 — Konteneryzacja (Docker) i docelowo webowy interfejs

Pomysł zgłoszony 2026-08-21 (wtedy odłożony do ustabilizowania pipeline'u —
Etapy 1-7 ukończone 2026-09-17, więc odblokowane). Rozszerzony
2026-09-17 o docelowy webowy interfejs — ustalona kolejność: najpierw
sam Docker (CLI z kontenera), interfejs webowy jako osobny, późniejszy
etap.

### Krok 1 — Docker, CLI z kontenera (zrobione i zweryfikowane 2026-09-17)

- [x] `Dockerfile` (`python:3.13-slim-bookworm` + ffmpeg + tesseract-ocr/pol
      + `requirements.txt` z indeksem `cu128` dla PyTorch).
- [x] `docker-compose.yml` — usługa `app` (pipeline) + `ollama` (osobny
      kontener, `ollama/ollama:latest`), obie z rezerwacją GPU (składnia
      Compose `deploy.resources.reservations.devices`, bez osobnej
      instalacji NVIDIA Container Toolkit na Windows — Docker Desktop 4.x+
      wykrywa GPU w WSL2 samodzielnie).
- [x] Wolumeny: `input/`, `output/`, `config/`, `prompts/` montowane z
      hosta (te same ścieżki co przy instalacji natywnej); `model_cache` i
      `ollama_data` jako nazwane wolumeny, żeby nie pobierać modeli od nowa
      przy każdym `docker compose down`/`up`.
- [x] Adres Ollamy sparametryzowany: `config/config.yaml` → `ollama.host`,
      nadpisywalny zmienną `OLLAMA_HOST` — `docker-compose.yml` ustawia
      `http://ollama:11434` (nazwa usługi), instalacja natywna zostaje przy
      `http://localhost:11434` bez żadnej zmiany.
- [x] `requirements.txt`, `.dockerignore`, `.env.example` (HF_TOKEN, wzorzec
      do skopiowania jako `.env` — gitignorowany, ale sam `.env.example`
      jawnie wyłączony z `.gitignore`, żeby trafił do repo).
- [x] Dokumentacja: `docs/DOCKER.md`.
- [x] **Weryfikacja end-to-end** (2026-09-17) — build obrazu, oba
      kontenery (`app` + `ollama`) wystartowane, GPU passthrough
      potwierdzony (`torch.cuda.is_available()` → `True`, RTX 4060
      widoczna także przez `nvidia-smi` w kontenerze), ffmpeg + tesseract
      (`pol`) obecne, Ollama osiągalna z `app` pod `http://ollama:11434`,
      pełny łańcuch `transcribe.py` (z diaryzacją) → `identify_speakers.py`
      → `clean_transcript.py` → `generate_report.py` zakończony sukcesem na
      `input/audio/test.mp3`, wynik poprawnie widoczny na dysku hosta przez
      wolumeny. Po drodze: na maszynie użytkownika WSL2 okazał się w ogóle
      niezainstalowany (nie tylko wymagający restartu) — naprawione przez
      `wsl --install` w podniesionym PowerShell. Szczegóły i rozwiązywanie
      problemów: `docs/DOCKER.md`.

### Krok 2 — Webowy interfejs

Stack ustalony z użytkownikiem (jego codzienny stack): nginx + PHP-FPM +
**Symfony** (backend API) + **Nuxt (Vue)** jako frontend + **MySQL/MariaDB**.
Kolejność faz ustalona z użytkownikiem: najpierw fundament (skład
Rady/Zarządu + edycja meeting_info), job runner (uruchamianie/ponawianie
akcji pipeline'u z przeglądarki, na wzór "deploy" w CI/CD) dopiero potem,
osobno planowany. Pełna architektura (decyzje o kolejce zadań, źródle
prawdy, kompozycji Dockera) i mapa wszystkich faz: plan zapisany podczas
sesji planistycznej 2026-09-17 (Plan Mode) — szczegóły odtworzone niżej i
w `docs/DOCKER.md`.

- [x] **Faza 0+1 — fundament** (zrobione i zweryfikowane 2026-09-17):
  - `web/backend/` — szkielet Symfony 7.4 + Doctrine ORM, encje `Member`,
    `Meeting`, `MeetingAttendee`; `web/frontend/` — szkielet Nuxt 4 (SPA,
    `ssr: false`); `web/nginx/` — reverse proxy (`/api/` → php-fpm,
    `/` → Nuxt); `docker-compose.web.yml` — nakładka na `docker-compose.yml`
    (usługi `mariadb`, `php-fpm`, `nginx`, `nuxt`; Krok 1 pozostaje
    nienaruszony i działa niezależnie).
  - CRUD składu Rady/Zarządu (`/api/members`) i edycja metadanych spotkania
    (`/api/meetings/{id}/meeting-info`) — **plik na dysku
    (`<nazwa>.meeting_info.json`) zostaje źródłem prawdy**, baza to
    indeks/cache do UI (decyzja architektoniczna — zachowuje działanie
    czystego CLI/Kroku 1 równolegle z UI).
    `POST /api/meetings/rescan` odczytuje istniejące pliki z dysku.
  - Zweryfikowane bezpośrednimi wywołaniami API (nie klikaniem w
    przeglądarce): `/api/health` end-to-end przez cały łańcuch proxy,
    CRUD members, `rescan` poprawnie zaimportował 3 realne istniejące
    `meeting_info.json` (z poprawnymi datami/numerami protokołów), zapis
    `PUT .../meeting-info` wygenerował plik w formacie w 100% zgodnym z
    `scripts/generate_report.py::render_attendance()` (w tym etykieta
    "(radca prawny)"). Test zrobiono na osobnym, testowym spotkaniu
    (`_webtest/`), nie na prawdziwych danych — po teście usunięty.
  - Migracje: na razie `doctrine:schema:update --force` zamiast formalnych
    Doctrine Migrations (zainstalowane, ale świadomie nieużywane w tej
    fazie — mniej narzutu przy jednoosobowym, lokalnym projekcie bez
    wielu środowisk).
  - Znane ograniczenie: jedna osoba przypisana do dwóch ról specjalnych
    (protokolant/sekretarz/przewodniczący) na tym samym spotkaniu — druga
    rola po cichu nadpisuje pierwszą (jeden wiersz `meeting_attendees` ma
    jedno pole `role`). Nieistotne w praktyce (zawsze trzy różne osoby w
    historycznych danych), ale UI o tym nie ostrzega.
  - Niezweryfikowane: rzeczywiste klikanie w formularzach w przeglądarce
    (sprawdzona tylko warstwa API, którą frontend woła).
- [x] **Faza 2 — identyfikacja mówców i podgląd transkrypcji** (zrobione
      2026-09-17): `GET/PUT /api/meetings/{id}/speakers` (edycja
      `proposed_name`, zawsze ustawia `source: "manual"`),
      `GET .../speakers/{label}/sample/{n}` (strumieniowanie próbek audio,
      `BinaryFileResponse` — wsparcie HTTP Range "za darmo", potrzebne do
      przewijania w `<audio>`), `GET .../transcript` (podgląd
      `.clean.txt`). Strony Nuxt: `/meetings/{id}/speakers`,
      `/meetings/{id}/transcript`. Zweryfikowano poprawność odczytu
      istniejącego, prawdziwego `.speakers.json` (posiedzenie 27.06.2025)
      przez API oraz (2026-09-19, potwierdzone przez użytkownika w
      przeglądarce) faktyczne odtwarzanie próbek audio.
      Napotkano poważny problem wydajności API (zapytania trwające
      niespójnie kilka-kilkanaście sekund, czasem się zawieszające) —
      **główna przyczyna znaleziona i naprawiona 2026-09-19**: nginx
      cache'uje adres IP kontenerów `php-fpm`/`nuxt` przy starcie i traci
      z nimi łączność po ich przebudowie, dopóki sam nie zostanie
      zrestartowany (nie wystarczy `reload`) — patrz `docs/DOCKER.md`.
      Po naprawie zostaje resztkowe ~5-7s na zapytanie, źródło
      niezdiagnozowane ostatecznie (podejrzenie: narzut Windows/WSL2 w
      trybie dev Symfony), ale niekrytyczne dla wewnętrznego narzędzia.
- [x] **Faza 2.5 — CRUD nagrań** (zrobione 2026-09-19): `RecordingController`
      — `GET/POST/DELETE /api/recordings` (lista `input/audio/**` z
      flagą `has_transcript`, upload wieloczęściowy do
      `input/audio/RRRR.MM.DD/`, usuwanie). Strona Nuxt `/recordings`.
      Podniesione limity uploadu (PHP + nginx, do 1 GB — nagrania bywają
      duże). Zweryfikowano: listę na 31 prawdziwych nagraniach (poprawne
      `has_transcript`), upload/usuwanie na pliku testowym.
      Niezweryfikowany: upload naprawdę dużego pliku z przeglądarki.
      Uruchomienie samej transkrypcji z przeglądarki zostaje w Fazie 3
      (job runner) — to celowe rozgraniczenie, nie przeoczenie.
- [x] **Faza 3 — job runner** (zbudowane 2026-09-19): tabela `jobs` +
      `scripts/job_worker.py` (nowy proces w kontenerze `app`, obok
      `sleep infinity`, żeby CLI zostało dostępne nawet gdyby worker padł)
      odpytujący kolejkę i uruchamiający te same skrypty CLI co dziś,
      dopisujący log na bieżąco. `JobController`
      (`GET/POST /api/jobs`, `GET /api/jobs/{id}`, `POST
      /api/jobs/{id}/retry`) — 5 typów zadań: `transcribe`,
      `identify_speakers`, `clean_transcript`, `init_meeting_info`,
      `generate_report`. `GET /api/recordings` rozszerzone o flagi
      pipeline'u (`has_speakers`, `has_clean`, `has_meeting_info`).
      Strony Nuxt: `/recordings` (przyciski kolejnych kroków per
      nagranie), `/jobs` (lista + podgląd logu na żywo + „Ponów”).
      Zależność `pymysql` w osobnym `requirements-web.txt` (osobna
      warstwa Dockera), żeby nie unieważniać cache'u warstwy
      torch/whisperx w głównym `Dockerfile`. Odrzucone alternatywy:
      montowanie `/var/run/docker.sock` do kontenera PHP (realny dostęp
      roota do hosta) i łączenie PHP-FPM z obrazem CUDA/PyTorch w jeden
      kontener (miesza cykle życia). Patrz `docs/DOCKER.md`.
      **Zweryfikowane end-to-end przez API** (wszystkie 5 typów zadań
      przez rzeczywistego workera, nie tylko wstawienie do kolejki):
      `transcribe` (na `input/audio/test.mp3`, z diaryzacją GPU),
      `identify_speakers` i `generate_report` (oba wywołały Ollamę),
      `clean_transcript`, `init_meeting_info`. Przy okazji realnie
      dokończono pierwszy krok pipeline'u dla nagrania
      `2026.07.17/20260717_091933` (pusty szablon `.meeting_info.json` +
      projekt sprawozdania wygenerowany na jego podstawie — sekcja
      obecności w projekcie będzie pusta, dopóki dane spotkania nie
      zostaną uzupełnione przez `/meetings` i raport nie zostanie
      wygenerowany ponownie). **Niezweryfikowane:** klikanie w
      przeglądarce (testowano samo API + worker), oraz wydajność UI przy
      wielu jednoczesnych zadaniach (worker przetwarza jedno na raz,
      celowo — pipeline i tak jest sekwencyjny).
- [x] **Uzupełnienie Fazy 1 — funkcje w Radzie/Zarządzie, migawka na
      spotkanie** (zbudowane 2026-09-19): `Member.roleLabel` (istniejące
      pole) odblokowane dla `rada_nadzorcza`/`zarzad`, nie tylko `inny` —
      podpowiedzi w UI (`/members`): Przewodniczący/Zastępca
      Przewodniczącego/Sekretarz Rady Nadzorczej, Członek Rady Nadzorczej
      delegowany do czasowego pełnienia funkcji Członka Zarządu, Prezes
      Zarządu, Członek Zarządu ds. technicznych, Członek Zarządu – Główna
      Księgowa (plus dowolny tekst — to podpowiedzi, nie sztywny enum).
      **Kluczowa zmiana:** nowe pole `MeetingAttendee::$roleLabel` —
      funkcja osoby zapisywana NIEZALEŻNIE dla każdego spotkania (migawka
      z dnia spotkania), już NIE odczyt na żywo z `Member::roleLabel`
      (wcześniej `namesForInny()` tak właśnie robił — cichy błąd
      historycznej dokładności, teraz naprawiony i ujednolicony dla
      wszystkich trzech grup w `namesForBody()`). `/meetings/{id}` pozwala
      teraz przypisać KAŻDĄ aktywną osobę do KAŻDEGO z trzech organów na
      danym spotkaniu (nie tylko do jej domyślnego) — to obsługuje
      dokładnie przypadek delegacji.
      **Zweryfikowano przez API** na spotkaniu testowym: zapisano Członka
      RN pod „Zarząd” z etykietą delegacji, potem zmieniono domyślną
      funkcję tej osoby w `/members` na pustą — ponowny odczyt spotkania
      dalej pokazywał zapisaną wcześniej etykietę delegacji (dowód, że
      historia jest odporna na późniejsze zmiany składu).
      **Przy okazji znaleziono realną lukę** (nie spowodowaną tą zmianą):
      spotkania zaimportowane przed Fazą 0+1 (np. `10.08.2026`) mają
      bogatą listę obecności W PLIKU, ale zero dopasowanych wierszy w
      bazie — otwarcie takiego spotkania w `/meetings/{id}` pokazuje
      wszystkie checkboxy jako puste, a zapisanie formularza bez ręcznego
      zaznaczenia nadpisałoby plik pustą listą (to samo ryzyko, które już
      raz uszkodziło dane `2026.06.22/260615_0262`, patrz Faza 2.5 w
      `docs/HISTORY.md`). Dodano zabezpieczenie: `/meetings/{id}`
      wykrywa ten stan i wymaga potwierdzenia (`confirm()`) przed zapisem
      pustej listy. **Niezweryfikowane:** klikanie w przeglądarce.
- [ ] **Faza 4** (zakres otwarty) — podgląd/edycja/eksport projektu
      sprawozdania z poziomu przeglądarki.

## Uwagi

- Zgodnie z `docs/AGENTS.md`: żadne rzeczywiste nagrania, transkrypcje ani
  raporty nie trafiają do repozytorium Git ani do zewnętrznych usług.
- Ten plan należy aktualizować w miarę postępu prac i podejmowania decyzji
  projektowych (odznaczanie zrobionych punktów, dopisywanie nowych).
