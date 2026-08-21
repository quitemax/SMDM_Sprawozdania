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
- [ ] `input/historical_data/reports/` i `input/historical_data/transcripts/`
      wciąż puste — historyczne raporty/transkrypcje do dodania, gdy będą
      dostępne (potrzebne do Etapu 4 jako wzorce stylu).
- [ ] Nowy katalog `input/knowledge/` (regulaminy, uchwały, umowy) — do
      ustalenia, jak i czy ma być wykorzystywany jako kontekst dla modelu
      przy analizie treści spotkań (Etap 4).
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
- [ ] Test na kolejnym nagraniu, najlepiej o innej jakości dźwięku (dla
      porównania), gdy będzie potrzeba.

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

## Etap 4 — Analiza treści i generowanie raportu

- [ ] Prompty w `prompts/` do: (a) analizy/streszczenia przebiegu
      spotkania, (b) wygenerowania długiego, narracyjnego raportu w stylu
      zgodnym z wcześniejszymi raportami spółdzielni.
- [ ] Wykorzystanie danych historycznych (`input/historical_data/`) jako
      wzorców stylu i struktury raportu.
- [ ] Integracja skryptu z lokalnym modelem przez Ollama, zapis wyniku do
      `output/reports/`.

## Etap 5 — Weryfikacja przez pracownika

- [ ] Ustalenie formy weryfikacji projektu raportu (np. plik do edycji,
      prosty interfejs) — decyzja projektowa do zapisania w
      `docs/PROJECT_MEMORY.md`.
- [ ] Jasne oznaczenie w wygenerowanym pliku, że to **projekt** raportu
      wymagający sprawdzenia przez człowieka, nie wersja ostateczna.

## Etap 6 — Dokumentacja końcowa

- [ ] Uzupełnienie `docs/HOW_TO_USE.md` (celowo odłożone na koniec —
      instrukcja obsługi całego pipeline'u krok po kroku).
- [ ] Aktualizacja `README.md` (sekcja „Status”) po osiągnięciu działającego
      end-to-end przepływu.
- [ ] Wpis podsumowujący w `docs/HISTORY.md`.

## Etap 7 — Test end-to-end

- [ ] Pełny przebieg: nagranie → transkrypcja → analiza → projekt raportu,
      na rzeczywistym (uporządkowanym) nagraniu z `input/audio/`.
- [ ] Porównanie projektu raportu z odpowiadającym mu raportem historycznym
      (tam gdzie dostępne nagranie + gotowy raport) jako nieformalna miara
      jakości.

## Etap 8 — (opcjonalnie, rozważane) Konteneryzacja (Docker)

Pomysł zgłoszony 2026-08-21, jeszcze nie zaplanowany do realizacji.

- [ ] Cel: uprościć instalację na nowym komputerze — jeden `Dockerfile`/
      `docker-compose.yml` zamiast ręcznego dobierania wersji sterownika
      NVIDIA/CUDA/PyTorch/WhisperX (obecnie napięte na sztywno, patrz
      `docs/INSTALLATION.md`).
- [ ] Wymaga na Windows: Docker Desktop + WSL2 + NVIDIA Container Toolkit
      (dostęp kontenera do GPU) — dodatkowa warstwa konfiguracji, ale
      obecnie dobrze wspierana.
- [ ] Narzut na czas obliczeń (transkrypcja/inferencja) powinien być
      pomijalny — GPU passthrough jest niemal bezpośredni. Narzut dotyczy
      głównie rozmiaru obrazu (PyTorch+CUDA to kilka GB) i czasu builda.
- [ ] Cache modeli (WhisperX `large-v3`, kilka GB z Hugging Face) musi być
      zamontowanym wolumenem, nie wypiekany w obraz.
- [ ] Ollama najlepiej jako osobny kontener/serwis obok głównego.
- [ ] Do decyzji: czy warto teraz, czy dopiero po ustabilizowaniu pipeline'u
      (Etapy 1–7) — na razie odłożone.

## Uwagi

- Zgodnie z `docs/AGENTS.md`: żadne rzeczywiste nagrania, transkrypcje ani
  raporty nie trafiają do repozytorium Git ani do zewnętrznych usług.
- Ten plan należy aktualizować w miarę postępu prac i podejmowania decyzji
  projektowych (odznaczanie zrobionych punktów, dopisywanie nowych).
