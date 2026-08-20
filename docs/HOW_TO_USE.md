# Instrukcja obsługi

Dokument jest w budowie — opisuje kolejne elementy pipeline'u w miarę ich
powstawania (patrz `docs/ROADMAP.md`). Docelowo ma zawierać pełną instrukcję
krok po kroku: od nagrania do gotowego projektu raportu.

## Transkrypcja nagrania (WhisperX)

Skrypt: `scripts/transcribe.py`. Zamienia plik audio na transkrypcję tekstową
(bez rozpoznawania mówców — diaryzacja zostanie dodana w kolejnym kroku).

### Uruchomienie

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\transcribe.py "input\audio\test.mp3"
```

Dla nagrania z konkretnej daty spotkania:

```powershell
python scripts\transcribe.py "input\audio\2026.08.10\10.08.2026.MP3"
```

Przy pierwszym uruchomieniu pobierany jest model `large-v3` (kilka GB) z
Hugging Face — zajmuje to chwilę, później model jest przechowywany lokalnie
w pamięci podręcznej.

### Parametry opcjonalne

| Parametr | Domyślna wartość | Opis |
|---|---|---|
| `--model` | `large-v3` | Nazwa modelu Whisper. |
| `--language` | `pl` | Kod języka nagrania. |
| `--batch-size` | `16` | Rozmiar batcha przetwarzania. |
| `--output-dir` | `output/transcripts` | Katalog wynikowy. |
| `--input-root` | `input/audio` | Katalog bazowy nagrań — względem niego odtwarzana jest struktura podkatalogów (np. daty) w katalogu wynikowym. |

### Wynik

Dla pliku `input/audio/2026.08.10/10.08.2026.MP3` powstają:

- `output/transcripts/2026.08.10/10.08.2026.txt` — sam tekst transkrypcji,
- `output/transcripts/2026.08.10/10.08.2026.json` — segmenty ze znacznikami
  czasu (do dalszego przetwarzania).

Plik bezpośrednio w `input/audio/` (np. `test.mp3`, bez podkatalogu z datą)
trafia płasko do `output/transcripts/` (np. `output/transcripts/test.txt`).
