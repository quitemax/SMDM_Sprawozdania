# Historia projektu

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