# Instrukcja obsługi

Dokument jest w budowie — opisuje kolejne elementy pipeline'u w miarę ich
powstawania (patrz `docs/ROADMAP.md`). Docelowo ma zawierać pełną instrukcję
krok po kroku: od nagrania do gotowego projektu raportu.

## Transkrypcja nagrania (WhisperX)

Skrypt: `scripts/transcribe.py`. Zamienia plik audio na transkrypcję
tekstową z rozpoznawaniem mówców (diaryzacja, domyślnie włączona).

Diaryzacja wymaga tokena Hugging Face w zmiennej środowiskowej `HF_TOKEN`
(patrz `docs/INSTALLATION.md`, sekcja o tokenie i dostępie do modeli
pyannote).

### Uruchomienie

```powershell
.\.venv\Scripts\Activate.ps1
$env:HF_TOKEN = "hf_..."
python scripts\transcribe.py "input\audio\test.mp3"
```

Postęp każdego etapu (transkrypcja, wyrównanie, diaryzacja) jest wypisywany
w procentach na bieżąco w konsoli.

Bez rozpoznawania mówców (nie wymaga tokena):

```powershell
python scripts\transcribe.py "input\audio\test.mp3" --no-diarize
```

Jeśli znana jest przybliżona liczba mówców, można ją podać — poprawia to
jakość diaryzacji:

```powershell
python scripts\transcribe.py "input\audio\test.mp3" --min-speakers 2 --max-speakers 5
```

Dla nagrania z konkretnej daty spotkania:

```powershell
python scripts\transcribe.py "input\audio\2026.08.10\10.08.2026.MP3"
```

Przy pierwszym uruchomieniu pobierany jest model `large-v3` (kilka GB) z
Hugging Face — zajmuje to chwilę, później model jest przechowywany lokalnie
w pamięci podręcznej.

### Parametry opcjonalne

Wartości domyślne pochodzą z `config/config.yaml` — poniżej aktualna
zawartość tego pliku. Każdy parametr można nadpisać flagą CLI.

| Parametr | Domyślna wartość | Opis |
|---|---|---|
| `--model` | `large-v3` | Nazwa modelu Whisper. |
| `--language` | `pl` | Kod języka nagrania. |
| `--batch-size` | `16` | Rozmiar batcha przetwarzania. |
| `--output-dir` | `output/transcripts` | Katalog wynikowy. |
| `--input-root` | `input/audio` | Katalog bazowy nagrań — względem niego odtwarzana jest struktura podkatalogów (np. daty) w katalogu wynikowym. |
| `--diarize` / `--no-diarize` | `--diarize` (włączone) | Rozpoznawanie mówców. Wymaga `HF_TOKEN`. |
| `--min-speakers` | brak | Minimalna liczba mówców (opcjonalnie, poprawia jakość diaryzacji). |
| `--max-speakers` | brak | Maksymalna liczba mówców (opcjonalnie). |

### Wynik

Dla pliku `input/audio/2026.08.10/10.08.2026.MP3` powstają:

- `output/transcripts/2026.08.10/10.08.2026.txt` — tekst transkrypcji,
  z etykietą mówcy na początku każdej linii (np. `[SPEAKER_00] ...`), o ile
  diaryzacja jest włączona,
- `output/transcripts/2026.08.10/10.08.2026.json` — segmenty ze znacznikami
  czasu (i etykietą mówcy przy każdym segmencie/słowie) do dalszego
  przetwarzania.

Plik bezpośrednio w `input/audio/` (np. `test.mp3`, bez podkatalogu z datą)
trafia płasko do `output/transcripts/` (np. `output/transcripts/test.txt`).

## Czyszczenie transkrypcji

Skrypt: `scripts/clean_transcript.py`. Skleja kolejne segmenty tego samego
mówcy (oddalone o mniej niż 2 sekundy) w jedną wypowiedź i usuwa segmenty
będące wyłącznie izolowanym wypełniaczem (np. samo "yyy"). Nie poprawia
błędów w środku zdań.

```powershell
python scripts\identify_speakers.py "output\transcripts\2026.08.10\10.08.2026.json"
python scripts\clean_transcript.py "output\transcripts\2026.08.10\10.08.2026.json"
```

Wynik: `<nazwa>.clean.txt` (czytelny format `[HH:MM:SS] MÓWCA: tekst`,
wygodny do przeglądu) i `<nazwa>.clean.json` (`{"turns": [...]}`, do
dalszego przetwarzania — wejście dla analizy treści, Etap 4).

## Propozycja identyfikacji mówców

Skrypt: `scripts/identify_speakers.py`. Na podstawie pliku `.json` z
transkrypcją (wynik `transcribe.py`) szuka fragmentów, gdzie ktoś się
przedstawia albo zwraca do kogoś po imieniu, i prosi model Ollama o
wywnioskowanie, kim może być każdy `SPEAKER_XX`.

```powershell
ollama serve  # jeśli usługa Ollama nie działa już w tle
python scripts\identify_speakers.py "output\transcripts\2026.08.10\10.08.2026.json"
```

Wynik zapisywany jest jako `<nazwa>.speakers.json` obok transkrypcji —
**wyłącznie propozycja do ręcznej weryfikacji przez pracownika**,
transkrypcja nie jest automatycznie modyfikowana. Model bywa niedokładny
(patrz `docs/HISTORY.md`, `docs/PROJECT_MEMORY.md`) — zawsze sprawdzić
przed użyciem.
