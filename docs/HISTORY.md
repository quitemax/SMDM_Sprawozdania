# Historia projektu

## 2026-09-17 (4)

- Zbudowano fundament Etapu 8, Kroku 2 (webowy interfejs) — Faza 0+1,
  zaplanowana wcześniej w trybie Plan Mode (kolejność faz i decyzje
  architektoniczne ustalone z użytkownikiem, patrz `docs/ROADMAP.md`,
  Etap 8, Krok 2). Nowy katalog `web/`: `web/backend/` (Symfony 7.4 +
  Doctrine ORM, scaffoldowany przez tymczasowy kontener `composer`),
  `web/frontend/` (Nuxt 4, scaffoldowany przez tymczasowy kontener
  `node`), `web/nginx/` (reverse proxy). Nowa nakładka
  `docker-compose.web.yml` (usługi `mariadb`, `php-fpm`, `nginx`, `nuxt`)
  — Krok 1 (`docker-compose.yml`, sam pipeline) zostaje nienaruszony.
- Zaimplementowano i zweryfikowano end-to-end (bezpośrednimi wywołaniami
  API): CRUD składu Rady Nadzorczej/Zarządu, `POST /api/meetings/rescan`
  (poprawnie zaimportował 3 realne, istniejące pliki
  `*.meeting_info.json` z prawidłowymi datami/numerami protokołów), oraz
  `GET/PUT /api/meetings/{id}/meeting-info` — zapis z UI generuje plik na
  dysku w formacie w 100% zgodnym z tym, co czyta
  `scripts/generate_report.py` (potwierdzone uruchomieniem
  `render_attendance()` na wygenerowanym pliku). Test zapisu zrobiono na
  osobnym, sztucznym spotkaniu (nie na prawdziwych danych 2025.06.27 /
  2026.06.22 / 2026.08.10), żeby nic nie nadpisać.
- Napotkane problemy przy budowie obrazów, po drodze naprawione: `npm ci`
  wymagało zgodnego `package-lock.json` (zmieniono na `npm install`),
  Node 20 nie spełniał wymagań silnika jednej z zależności (podbito do
  Node 22), composer.lock wyliczony pod PHP 8.4 (podbito bazowy obraz z
  `php:8.3-fpm` na `php:8.4-fpm-bookworm`). Usunięto automatycznie
  wygenerowane przez Symfony Flex `compose.yaml`/`compose.override.yaml`
  (stub pod PostgreSQL) jako niepotrzebny duplikat naszej własnej,
  świadomie innej architektury (MariaDB, jeden plik nakładki w korzeniu
  repo).
- Decyzja projektowa: `<nazwa>.meeting_info.json` na dysku zostaje
  źródłem prawdy (czytają go bezpośrednio skrypty CLI), baza danych to
  tylko indeks/cache do UI — zachowuje to działanie czystego workflow
  CLI (Krok 1) równolegle z nowym interfejsem webowym.
- Niezweryfikowane w tej sesji: rzeczywiste klikanie w formularzach Nuxt
  w przeglądarce (sprawdzona tylko warstwa API) oraz zachowanie przy
  przypisaniu tej samej osoby do dwóch ról specjalnych na raz (znane,
  udokumentowane ograniczenie — patrz `docs/DOCKER.md`).

## 2026-09-17 (3)

- Zweryfikowano konteneryzację Docker end-to-end na realnej maszynie
  użytkownika. Po drodze: WSL2 okazał się w ogóle niezainstalowany (nie
  tylko wymagający restartu, jak początkowo podejrzewano) — naprawione
  przez `wsl --install` w podniesionym PowerShell. Po naprawie: build
  obrazu (`docker compose build`, ~15 min z zimnym cache), oba kontenery
  wystartowane, GPU passthrough potwierdzony (`nvidia-smi` i
  `torch.cuda.is_available()` w kontenerze widzą RTX 4060), ffmpeg i
  tesseract (`pol`) obecne, Ollama osiągalna z kontenera `app`. Pełny
  łańcuch `transcribe.py` (z diaryzacją, prawdziwy token HF) →
  `identify_speakers.py` → `clean_transcript.py` → `generate_report.py`
  zakończony sukcesem na `input/audio/test.mp3` — wynik poprawnie widoczny
  na dysku hosta przez wolumeny bind-mount. Zaktualizowano `docs/DOCKER.md`
  (status, nowa sekcja rozwiązywania problemów z WSL2) i `docs/ROADMAP.md`
  (Etap 8, Krok 1 oznaczony jako zweryfikowany).

## 2026-09-17 (2)

- Przetestowano `scripts/generate_report.py` na prawdziwym przypadku bez
  gotowego sprawozdania (10.08.2026): ręczna identyfikacja mówców po głosie
  (10 mówców), uzupełnienie `meeting_info.json`, pełny przebieg pipeline'u.
  Wynik oceniony przez użytkownika jako dobry — jeden przykład zbędnego
  interpretacyjnego detalu odnotowany w `docs/ROADMAP.md` (Etap 5) do
  poprawy przy okazji porównania z wersją zredagowaną przez pracownika
  spółdzielni.
- Zaczęto konteneryzację (Docker) — ustalona z użytkownikiem kolejność:
  najpierw sam Docker z pracą przez CLI z kontenera, potem osobno webowy
  interfejs (nginx + PHP-FPM + backend API + Nuxt/Vue + baza danych).
  Dodano `Dockerfile`, `docker-compose.yml` (usługi `app` + `ollama`,
  rezerwacja GPU, wolumeny na `input/`/`output/`/`config/`/`prompts/` i
  pamięć podręczną modeli), `requirements.txt`, `.dockerignore`,
  `.env.example`. Sparametryzowano adres Ollamy w `identify_speakers.py` i
  `generate_report.py` (`config/config.yaml` → `ollama.host`, nadpisywalne
  `OLLAMA_HOST`) — instalacja natywna dalej działa bez zmian
  (`localhost`), Docker Compose ustawia nazwę usługi (`ollama`).
  **Nie przetestowano** — środowisko sesji nie miało zainstalowanego
  Dockera; do zweryfikowania przez użytkownika (patrz `docs/DOCKER.md`,
  `docs/ROADMAP.md` Etap 8).

## 2026-09-17

- Zbudowano `scripts/generate_report.py` — pierwszy działający generator
  PROJEKTU sprawozdania z posiedzenia RN (Etap 4), przetestowany na
  posiedzeniu 22.06.2026 (dla którego istnieje gotowe sprawozdanie
  `Protokół 8 RN 22.06.2026.md`, więc dało się bezpośrednio porównać wynik
  z rzeczywistością). Ręcznie zidentyfikowano mówców po głosie
  (`extract_speaker_samples.py`, `source: manual`) i uzupełniono
  `meeting_info.json` na podstawie gotowego protokołu — dobre wejście dla
  testu generatora.
- Cztery kolejne iteracje w jednej sesji, każda testowana na żywym
  przebiegu (Ollama, model 11B):
  1. Cała transkrypcja (~27k tokenów) w jednym zapytaniu — przekroczyła
     limit kontekstu, Ollama ucięła początek (porządek obrad), model
     kompletnie zmyślił 4 fałszywe punkty porządku obrad.
  2. Sztywne okna po 45 wypowiedzi, streszczane od razu z przypisaniem do
     punktu — poprawna agenda (7/7), ale mieszanie treści sąsiednich
     punktów i zgubiony wynik jednego głosowania.
  3. Osobny przebieg "tagujący" (przypisanie wypowiedzi do punktów przed
     streszczaniem) — pogorszenie: model przypisywał zbyt szerokie,
     nakładające się zakresy (suma przypisań: 529 wypowiedzi przy 406
     rzeczywistych), więc 6 z 7 punktów dostało fikcyjną uchwałę.
  4. Zmiana podejścia na sugestię użytkownika: rezygnacja z wymuszania
     ścisłego podziału na punkty porządku obrad na rzecz wiernej,
     kompletnej, chronologicznej relacji (decyzja projektowa, patrz
     `docs/PROJECT_MEMORY.md`) — praktycznie zero cytatów z dialogu, zero
     treści o sporach osobistych, bogata sekcja "Sprawy wniesione".
     Jedyny pozostały problem: duplikaty uchwał (ten sam temat wykryty w
     kilku kawałkach transkrypcji) — naprawione deduplikacją po
     podobieństwie tematu (`difflib.SequenceMatcher` ≥ 0.65). Finalny
     wynik: 4/4 uchwały zgodne z prawdziwym protokołem (temat i numeracja
     51-54/R/26).
- Zaktualizowano `docs/ROADMAP.md` (Etap 4) i `docs/PROJECT_MEMORY.md` o
  architekturę, odrzucone podejścia i uzasadnienie decyzji projektowej.

## 2026-08-30 (2)

- Przeanalizowano parę transkrypcja↔protokół (posiedzenie 27.06.2025) pod
  kątem Etapu 4 (generowanie projektu sprawozdania). Wniosek: protokół to
  silnie skompresowana, sformalizowana wersja przebiegu — dyskusje
  osobiste są całkowicie pomijane, zostaje tylko treść proceduralna wg
  powtarzalnych formuł. Przy okazji znaleziono realny przypadek błędnej
  propozycji `identify_speakers.py` (etykieta mówcy niezgodna z
  nazwiskiem w podpisie odpowiadającego protokołu historycznego) —
  potwierdza to znane ograniczenie modelu 11B opisane w
  `docs/PROJECT_MEMORY.md`. Szczegóły ustaleń: `docs/ROADMAP.md`, Etap 4.
- W odpowiedzi na to dodano dwa nowe skrypty:
  - `scripts/extract_speaker_samples.py` — wycina dla każdego SPEAKER_XX
    najdłuższe wypowiedzi z oryginalnego audio jako krótkie próbki .mp3,
    żeby pracownik mógł rozpoznać mówcę po głosie zamiast (albo obok)
    polegać na modelu. Przetestowano na posiedzeniu 27.06.2025 — poprawnie
    wycięło próbki dla wszystkich 8 mówców.
  - `scripts/init_meeting_info.py` — tworzy szablon
    `<nazwa>.meeting_info.json` (lista obecności, protokolant, sekretarz,
    przewodniczący) na dane niemożliwe do wiarygodnego wyciągnięcia z
    samego nagrania.
  Plik `<nazwa>.speakers.json` zyskał pole `source` ("model"/"manual")
  rozróżniające propozycję modelu od ręcznie potwierdzonego wpisu;
  `identify_speakers.py` i `extract_speaker_samples.py` scalają się
  wzajemnie (nie nadpisują wpisów `manual`, zachowują `audio_samples`
  niezależnie od kolejności uruchamiania) — zweryfikowano testem
  jednostkowym funkcji scalającej. `clean_transcript.py` pokazuje wpisy
  `manual` bez znaku zapytania w etykiecie.

## 2026-08-30

- Dodano `scripts/docx_to_markdown.py`: konwersja historycznych protokołów
  RN z `input/historical_data/reports/` (.docx, natywny tekst Worda, bez
  OCR) na Markdown w `input/historical_data/reports_md/`. Zachowuje
  kolejność akapitów/tabel, pogrubienia/kursywę (wykrywane per fragment
  tekstu, z łączeniem sąsiednich fragmentów o tym samym formatowaniu —
  Word często dzieli jeden pogrubiony ciąg na kilka fragmentów) i listy
  numerowane (renumerowane sekwencyjnie, bez odtwarzania formatu Worda
  typu a/b/c). Gdy dla protokołu istnieje zarówno .docx jak i .pdf (ten
  sam dokument wyeksportowany dwa razy), .pdf jest pomijany — .docx daje
  wyższą jakość bez OCR; .pdf używany tylko jako fallback (przez
  `scripts/pdf_to_markdown.py`), gdy .docx nie istnieje. Przekonwertowano
  18 protokołów (2024-12 – 2026-06.22). Katalog wynikowy `reports_md/`
  gitignorowany tak jak źródłowy `reports/` (dane poufne).
- Dodano do `input/audio/` 13 nowych nagrań (2025.01.22 – 2026.06.22,
  łącznie ~18h). Zweryfikowano ponownie token HF (nowy, poprzedni nie był
  nigdzie zapisany zgodnie z zasadami poufności) — dostęp do wszystkich
  trzech modeli pyannote potwierdzony (200). Uruchomiono pełne
  przetwarzanie (transkrypcja + diaryzacja + propozycja mówców +
  czyszczenie) w tle, partiami wg rosnącego czasu trwania, z
  `ollama stop` przed każdą transkrypcją (patrz `docs/INSTALLATION.md`,
  znany problem z VRAM).

## 2026-08-26

- Zakończono przetwarzanie całej zawartości `input/audio/` (17 nagrań,
  ~37h audio): transkrypcja + diaryzacja + propozycja mówców + czyszczenie
  dla każdego. Uruchamiane partiami w tle (rosnąco wg długości), z
  przerwami spowodowanymi przez usypianie/wyłączenie laptopa w nocy —
  transcribe.py zapisuje wynik dopiero na końcu, więc przerwania nie
  zostawiły uszkodzonych plików, wystarczyło wznowić od nowa dla
  przerwanych plików.
- Napotkane i rozwiązane problemy operacyjne, opisane w
  `docs/INSTALLATION.md` (Rozwiązywanie problemów):
  - timeout (600s) identyfikacji mówców przy równoległym uruchamianiu
    z transkrypcją innego pliku — model Ollamy zostawał załadowany w
    VRAM i kolidował z WhisperX. Rozwiązanie: `ollama stop <model>`
    przed każdą transkrypcją w pętli wsadowej,
  - `260415_0257` (260 min) failowało z CUDA OOM przy domyślnym
    `--batch-size 16`, mimo że dłuższe nagranie (288 min) przeszło bez
    problemu tuż obok — naprawione przez `--batch-size 8` dla tego
    pliku; przyczyna niepewna (prawdopodobnie fragmentacja pamięci CUDA
    przy długim przebiegu, nie sama długość nagrania).

## 2026-08-25

- Naprawiono błąd w `scripts/identify_speakers.py` i `scripts/clean_transcript.py`:
  ścieżka do pliku `<nazwa>.speakers.json` była liczona przez
  `path.with_suffix("").with_suffix(".speakers.json")`, co dla nazw
  zawierających więcej niż jedną kropkę przed `.json` (np. `10.08.2026.json`,
  `18.12.2025 r- spotkanie.json`) ucinało zbyt dużo — `Path.with_suffix()`
  usuwa fragment po OSTATNIEJ kropce w całej nazwie, nie tylko rozszerzenie.
  Efekt: `10.08.2026.json` → błędnie `10.08.speakers.json` zamiast
  `10.08.2026.speakers.json`. Poprawka: `path.with_name(f"{path.stem}.speakers.json")`.
  Skutek uboczny w praktyce: dwa różne nagrania w `input/audio/2025.12.18/`
  (`18.12.2025 r- RN` i `18.12.2025 r- spotkanie`) ucinały się do tej samej
  błędnej nazwy `18.12.speakers.json` — drugie przetworzone nadpisało
  propozycję pierwszego. Nie dało się ustalić z samej treści, czyje dane
  przetrwały (identyczne etykiety SPEAKER_00–09 w obu), więc obie propozycje
  wygenerowano od nowa z poprawionym kodem, tak samo dla `10.08.2026`
  (tu nie było kolizji, tylko zła nazwa pliku).
- Uruchomiono przetwarzanie (transkrypcja + diaryzacja + identyfikacja
  mówców + czyszczenie) pozostałych nagrań z `input/audio/` w tle, w
  dwóch partiach posortowanych rosnąco wg długości: batch 1 (4 najkrótsze,
  do 84 min) zakończony; batch 2 (12 pozostałych, do 288 min) w trakcie.

## 2026-08-22

- Dodano `scripts/pdf_to_markdown.py` — konwersja PDF-ów z
  `input/knowledge/` na Markdown w `input/knowledge_md/` (ta sama
  struktura katalogów), z myślą o audycie i odwoływaniu się do tych
  dokumentów w sprawozdaniach (Etap 0/4). Dla stron bez warstwy
  tekstowej robi OCR (Tesseract 5.5.3 + pakiet `pol`, zainstalowany przez
  `winget install tesseract-ocr.tesseract`; Python: `pymupdf==1.28.2`,
  `pytesseract==0.3.13`). Domyślnie pomija pliki, których `.md` jest już
  aktualniejszy niż źródłowy `.pdf` (`--force` wymusza pełną ponowną
  konwersję).
- Użytkownik dodał do `input/knowledge/` sporo nowych dokumentów
  (regulaminy szczegółowe, STATUT itd.) — łącznie 40 plików PDF, 339
  stron. Wszystkie strony okazały się skanami bez warstwy tekstowej —
  100% przeszło przez OCR.
- Wynik: jakość bardzo dobra dla treści merytorycznej (sprawdzone m.in.
  na `STATUT.md` — poprawnie odczytane paragrafy statutu). Słabsza,
  spodziewana jakość na: spisach treści z kropkowanymi liniami numeracji
  stron (np. `STATUT.pdf`), oraz przy podpisach/pieczątkach w umowach —
  te fragmenty są niskiej wartości informacyjnej, więc nie stanowi to
  problemu praktycznego. Każdy plik `.md` (częściowo) rozpoznany przez
  OCR ma na początku notkę ostrzegawczą.
- `clean_transcript.py`, `identify_speakers.py` niezmienione w tym
  wpisie — dotyczy wyłącznie nowej bazy wiedzy z dokumentów, nie
  transkrypcji spotkań.

## 2026-08-21 (7)

- `scripts/clean_transcript.py` — jeśli obok transkrypcji istnieje
  `<nazwa>.speakers.json` (z `identify_speakers.py`), wykryte imiona są
  teraz od razu podstawiane w etykiecie mówcy (`speaker_display`) w
  `.clean.txt`/`.clean.json`, zawsze oznaczone jako niepotwierdzona
  propozycja (np. `Leon (SPEAKER_07?)`) — surowa etykieta `SPEAKER_XX`
  zachowana osobno w polu `speaker`. Mówcy bez propozycji
  (`proposed_name: null`) zostają jako `SPEAKER_XX`. Utrzymuje to zasadę
  „tylko propozycja do weryfikacji” (`docs/PROJECT_MEMORY.md`), ułatwiając
  jednocześnie przegląd. Test na `2025.06.27` pokazał to w praktyce —
  łącznie ze znanym błędnym dopasowaniem (SPEAKER_03), które dzięki
  oznaczeniu `?` jest od razu widoczne jako wymagające sprawdzenia.

## 2026-08-21 (6)

- Dodano `scripts/clean_transcript.py` (Etap 3, dokończony) — skleja
  kolejne segmenty tego samego mówcy oddalone o mniej niż 2 sekundy w
  jedną „turę" (mówca + zakres czasu + tekst) i usuwa segmenty będące
  wyłącznie izolowanym wypełniaczem. Świadomie nie poprawia błędów
  rozpoznawania ani nie usuwa wypełniaczy wplecionych w zdanie (np. "no")
  — bez pełnej analizy językowej za duże ryzyko zniekształcenia sensu.
  Zapisuje ujednolicony format pośredni: `<nazwa>.clean.json`
  (`{"turns": [...]}`) i czytelny `<nazwa>.clean.txt`
  (`[HH:MM:SS] MÓWCA: tekst`).
- Test na prawdziwej transkrypcji (`2025.06.27`): 1035 segmentów → 346
  tur po sklejeniu. Wynik bardzo czytelny, spójne, sensowne wypowiedzi
  bez utraty kontekstu (treść — dane poufne — nie jest tu cytowana,
  patrz `docs/AGENTS.md`). To domyka Etap 3 z `docs/ROADMAP.md`.

## 2026-08-21 (5)

- Dodano `scripts/identify_speakers.py` — propozycja mapowania
  `SPEAKER_XX` → imię/nazwisko na podstawie treści transkrypcji.
  Heurystyka (regex) wybiera fragmenty, gdzie ktoś może się przedstawiać
  albo zwracać do kogoś po imieniu, i przekazuje je modelowi Ollama
  (`SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M`) z prośbą o wywnioskowanie
  tożsamości — przez HTTP API Ollamy, z wymuszonym schematem JSON
  odpowiedzi. Wynik to osobny plik `<nazwa>.speakers.json`, wyłącznie
  propozycja do ręcznej weryfikacji (nigdy automatyczna podmiana w
  transkrypcie) — decyzja zapisana w `docs/PROJECT_MEMORY.md`.
- Test na prawdziwej transkrypcji (`2025.06.27`, 11 mówców): mechanizm
  działa i realnie znajduje sygnał (poprawnie wskazał mówcę adresowanego
  per „Panie Leonie”), ale ujawnił wyraźne ograniczenia lokalnego modelu
  11B (Q4_K_M): (1) myli osobę, o której się mówi/cytuje jej wiadomość,
  z faktycznym mówcą — nawet po dodaniu jawnej instrukcji w prompcie
  ostrzegającej dokładnie przed tym błędem, i nawet gdy własne uzasadnienie
  modelu (`evidence`) samo sobie przeczy z wnioskiem; (2) mimo instrukcji
  „zwróć wynik dla wszystkich mówców” pominął część z nich. Naprawiono
  też osobny drobny błąd: model czasem zwracał dosłowny string `"null"`
  zamiast wartości JSON `null` — znormalizowane w kodzie po stronie
  skryptu. Dalsze poprawki promptu uznane za mało opłacalne przy tym
  rozmiarze modelu — do rewizji przy Etapie 4 (większy model lub
  weryfikacja dwuprzebiegowa). Treść transkrypcji — dane poufne — nie
  jest tu cytowana, patrz `docs/AGENTS.md`.

## 2026-08-21 (4)

- Dokończono drobiazgi z Etapu 1 (`docs/ROADMAP.md`):
  - utworzono katalog `prompts/` (na przyszłe szablony promptów, Etap 4),
  - dodano `config/config.yaml` (ścieżki, parametry WhisperX, nazwa modelu
    Ollama) wczytywany przez nowy `scripts/config.py`; `scripts/transcribe.py`
    używa go jako domyślnych wartości CLI (nadpisywalnych parametrami),
  - uzupełniono `docs/INSTALLATION.md`, sekcja 7 (Test instalacji) —
    skonsolidowana weryfikacja GPU/CUDA, WhisperX+diaryzacja, Ollama.

## 2026-08-21 (3)

- Dodano wypisywanie procentowego postępu (transkrypcja, wyrównanie,
  diaryzacja) w `scripts/transcribe.py`, korzystając z wbudowanego
  `progress_callback` w WhisperX/pyannote — przydatne przy długich
  nagraniach idących w tle.
- Pierwszy test transkrypcji + diaryzacji na prawdziwym nagraniu:
  `input/audio/2025.06.27/250620_0233.MP3` (90 min). Wynik: 1035
  segmentów, jakość transkrypcji i rozróżnienia mówców bardzo dobra
  (treść — dane poufne — nie jest tu opisywana, patrz `docs/AGENTS.md`).
  Czas przetwarzania: VAD + transkrypcja + wyrównanie ok. 17,5 min,
  diaryzacja ok. 56 min (łącznie ok. 1h 14min) — diaryzacja skaluje się
  nieliniowo względem długości nagrania (na `test.mp3`, kilkanaście
  sekund, trwała kilkadziesiąt sekund). Do uwzględnienia przy planowaniu
  pracy z dłuższymi nagraniami.

## 2026-08-21 (2)

- Skonfigurowano token dostępu Hugging Face (typ Read) i zaakceptowano
  warunki użytkowania modeli `pyannote/segmentation-3.0` i
  `pyannote/speaker-diarization-3.1` — opisane w `docs/INSTALLATION.md`
  (nowa sekcja o tokenie HF). Zweryfikowano przez `curl` (kod `200` na
  pobranie `config.yaml` obu modeli).
- Dodano diaryzację (rozpoznawanie mówców) do `scripts/transcribe.py`
  (`whisperx.diarize.DiarizationPipeline` + `whisperx.assign_word_speakers`),
  domyślnie włączoną (`--no-diarize`, żeby wyłączyć; opcjonalnie
  `--min-speakers`/`--max-speakers`). Domyślny model pipeline'u w
  WhisperX 3.8.6 to `pyannote/speaker-diarization-community-1`, nie
  `speaker-diarization-3.1` jak pierwotnie zakładano w `docs/ROADMAP.md` —
  działa z tym samym tokenem, bez dodatkowej akceptacji warunków.
- Test na `input/audio/test.mp3` z diaryzacją zakończony sukcesem — 8
  segmentów, poprawne etykiety `[SPEAKER_00]` w `output/transcripts/test.txt`.
  Stare ostrzeżenia o `torchcodec`/TF32 nadal nieszkodliwe. Pojawiło się
  nowe, osobne ostrzeżenie z `pyannote.audio` (`pooling.py`, `std():
  degrees of freedom is <= 0`) — prawdopodobnie efekt bardzo krótkiego
  pliku testowego, do obserwacji przy teście na dłuższym, prawdziwym
  nagraniu.

## 2026-08-21

- Zainstalowano Ollama (`winget install Ollama.Ollama`, wersja 0.32.15) —
  opisane w `docs/INSTALLATION.md`, sekcja 5. Serwer startuje automatycznie
  jako usługa w tle po instalacji.
- Pobrano i przetestowano model językowy
  `SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M` (6.7 GB) — wybrany do
  analizy treści spotkań i generowania raportów (dobre wsparcie języka
  polskiego). `ollama ps` pokazuje 19%/81% CPU/GPU przy kontekście 4096 —
  model mieści się niemal w całości w 8 GB VRAM RTX 4060 Laptop. Test na
  prostym prompcie po polsku zakończony poprawną, sensowną odpowiedzią.

## 2026-08-20 (5)

- Utworzono i opublikowano repozytorium na GitHub:
  https://github.com/quitemax/SMDM_Sprawozdania
- Zaktualizowano `README.md` (sekcja „Szybki start”, link do
  `docs/HOW_TO_USE.md`).

## 2026-08-20 (4)

- Ustalono kolejność prac na kolejną sesję w `docs/ROADMAP.md`:
  1) diaryzacja, 2) instalacja Ollama i wybór modelu, 3) test transkrypcji
  na prawdziwym nagraniu z datą.

## 2026-08-20 (3)

- Wyciszono nieszkodliwe ostrzeżenia w `scripts/transcribe.py`:
  `torchcodec`/FFmpeg i TF32 z `pyannote.audio` (używane wewnętrznie przez
  WhisperX do VAD; WhisperX i tak przekazuje audio już wczytane do pamięci,
  więc dekodowanie przez torchcodec nie jest potrzebne) oraz komunikat
  `INFO` o automatycznym upgrade checkpointu Lightning (wyciszony przez
  poziom loggera — trwały upgrade pliku wymagałby wyłączenia
  `weights_only` w `torch.load`, czego świadomie unikamy ze względów
  bezpieczeństwa). Uruchomienie skryptu jest teraz czyste.

## 2026-08-20 (2)

- Dodano `scripts/transcribe.py` — pierwszy skrypt transkrypcji nagrań przy
  użyciu WhisperX (bez diaryzacji), z odtwarzaniem struktury podkatalogów
  dat z `input/audio/` w `output/transcripts/`.
- Przetestowano na `input/audio/test.mp3`. Podczas importu pojawiło się
  ostrzeżenie o brakującym `hf_xet` (wolniejsze pobieranie modeli z
  Hugging Face) — rozwiązane instalacją `hf_xet==1.6.0`, opisane w
  `docs/INSTALLATION.md`.
- Zaobserwowano też ostrzeżenie `pyannote.audio`/`torchcodec` o braku
  natywnych bibliotek do dekodowania audio pod Windows — nie blokuje
  samej transkrypcji, do naprawienia przy wdrażaniu diaryzacji
  (patrz `docs/ROADMAP.md`, Etap 1).
- Dodano `docs/HOW_TO_USE.md` — sekcja o uruchamianiu transkrypcji.

## 2026-08-20

- Dodano `docs/ROADMAP.md` z planem dalszych prac (porządkowanie danych,
  dokończenie środowiska, transkrypcja, analiza treści, weryfikacja,
  dokumentacja końcowa, test end-to-end).

## 2026-08-15

- Utworzono repozytorium projektu.
- Utworzono podstawową strukturę katalogów.
- Rozpoczęto przygotowanie dokumentacji.
- Rozpoczęto przygotowanie środowiska do lokalnej transkrypcji nagrań i generowania raportów.