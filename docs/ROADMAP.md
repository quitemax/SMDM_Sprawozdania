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
3. **Test na prawdziwym nagraniu z datą**:
   - uruchomienie `scripts/transcribe.py` (już z diaryzacją) na jednym
     z rzeczywistych nagrań z `input/audio/RRRR.MM.DD/`, nie tylko na
     `test.mp3`,
   - ocena jakości transkrypcji i diaryzacji na dłuższym, prawdziwym
     materiale.

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
- [ ] Spisanie testu instalacji (`docs/INSTALLATION.md`, sekcja 7) —
      minimalny skrypt/procedura potwierdzająca, że WhisperX, PyTorch+CUDA
      i Ollama działają poprawnie na danym komputerze.
- [ ] Utworzenie katalogów `scripts/` i `prompts/` (są w opisie struktury
      w README, ale jeszcze nie istnieją w repo).
- [ ] Ustalenie zawartości `config/` (obecnie pusty) — np. ścieżki
      wejścia/wyjścia, nazwa modelu Ollama, parametry WhisperX
      (język, diaryzacja, rozmiar modelu).

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
- [ ] Test na 1–2 rzeczywistych nagraniach z różną liczbą mówców i jakością
      dźwięku (patrz krok 3 planu sesji wyżej).

## Etap 3 — Przetwarzanie transkrypcji

- [ ] Oczyszczanie transkrypcji (usuwanie wypełniaczy, łączenie fragmentów
      tej samej wypowiedzi, korekta oczywistych błędów rozpoznawania).
- [ ] Ujednolicony format pośredni transkrypcji (np. mówca + znacznik
      czasu + tekst) jako wejście dla kolejnego etapu.

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
