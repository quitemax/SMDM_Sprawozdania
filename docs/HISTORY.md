# Historia projektu

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