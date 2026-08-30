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

Jeśli obok transkrypcji istnieje `<nazwa>.speakers.json` (wynik
`identify_speakers.py` i/lub `extract_speaker_samples.py` — patrz niżej),
wykryte imiona są od razu podstawiane w etykiecie mówcy. Propozycja modelu
jest ZAWSZE oznaczona jako niepotwierdzona, np. `Leon (SPEAKER_07?)` —
model bywa niedokładny (patrz `docs/PROJECT_MEMORY.md`), więc etykieta z
`?` wymaga sprawdzenia przy weryfikacji (Etap 5). Wpis potwierdzony
ręcznie po odsłuchaniu próbki audio (`"source": "manual"` w pliku
`.speakers.json`) wyświetlany jest bez `?`. Uruchom `identify_speakers.py`
i/lub `extract_speaker_samples.py` **przed** `clean_transcript.py`, żeby
podstawienie zadziałało:

```powershell
python scripts\identify_speakers.py "output\transcripts\2026.08.10\10.08.2026.json"
python scripts\clean_transcript.py "output\transcripts\2026.08.10\10.08.2026.json"
```

Wynik: `<nazwa>.clean.txt` (czytelny format
`[HH:MM:SS] MÓWCA (lub Imię (SPEAKER_XX?)): tekst`, wygodny do przeglądu)
i `<nazwa>.clean.json` (`{"turns": [...]}`, z surową etykietą `speaker`
i wyświetlaną `speaker_display` osobno — do dalszego przetwarzania,
wejście dla analizy treści, Etap 4).

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

## Ręczna identyfikacja mówców po głosie

Skrypt: `scripts/extract_speaker_samples.py`. Zamiast (albo obok) polegać
na propozycji modelu, można odsłuchać, jak brzmi każdy `SPEAKER_XX`.
Skrypt wycina z oryginalnego pliku audio 2 najdłuższe wypowiedzi każdego
mówcy (do 20s) i dopisuje ścieżki do nich w polu `audio_samples` w
`<nazwa>.speakers.json` (tworzy plik, jeśli jeszcze nie istnieje — nie
trzeba wcześniej uruchamiać `identify_speakers.py`).

```powershell
python scripts\extract_speaker_samples.py "output\transcripts\2026.08.10\10.08.2026.json"
```

Próbki trafiają do `<nazwa>.speaker_samples\SPEAKER_XX_01.mp3` (i `_02.mp3`)
obok transkrypcji. Po odsłuchaniu otwórz `<nazwa>.speakers.json` w edytorze
tekstu i uzupełnij ręcznie dla każdego mówcy:

```json
{
  "speaker_label": "SPEAKER_07",
  "proposed_name": "Leon Michał Malkiewicz",
  "confidence": "wysoka",
  "source": "manual",
  "evidence": "Rozpoznany po głosie",
  "audio_samples": ["10.08.2026.speaker_samples\\SPEAKER_07_01.mp3", "..."]
}
```

Pole `"source": "manual"` jest ważne — bez niego `clean_transcript.py`
traktuje wpis jak niepotwierdzoną propozycję modelu (znak zapytania w
etykiecie). Plik `.speakers.json` jest współdzielony z
`identify_speakers.py` — oba skrypty można uruchamiać w dowolnej
kolejności, żaden nie nadpisze już ręcznie potwierdzonego wpisu.

Automatyczne wykrywanie oryginalnego pliku audio zakłada domyślne ścieżki
z `config/config.yaml`; jeśli nie zadziała (np. plik audio przeniesiony),
podaj go wprost: `--audio "input\audio\...\plik.MP3"`.

## Szablon metadanych spotkania (poza transkrypcją)

Skrypt: `scripts/init_meeting_info.py`. Tworzy pusty szablon
`<nazwa>.meeting_info.json` obok transkrypcji — na dane, których nie da
się wiarygodnie wyciągnąć z nagrania: lista obecności, protokolant,
sekretarz i przewodniczący zebrania (patrz `docs/PROJECT_MEMORY.md`).
Jedyne pole wypełniane automatycznie to `date` (z nazwy katalogu).

```powershell
python scripts\init_meeting_info.py "output\transcripts\2026.08.10\10.08.2026.json"
```

Nie nadpisuje istniejącego pliku (żeby nie zgubić uzupełnionych danych) —
`--force`, żeby wymusić nadpisanie pustym szablonem.

## Konwersja dokumentów PDF na Markdown (baza wiedzy)

Skrypt: `scripts/pdf_to_markdown.py`. Konwertuje PDF-y z `input/knowledge/`
(regulaminy, uchwały, umowy) na pliki `.md` w `input/knowledge_md/`
(ta sama struktura katalogów), do wykorzystania jako baza wiedzy przy
audycie i pisaniu sprawozdań. Dla stron bez warstwy tekstowej (skany)
robi OCR (Tesseract, język polski).

```powershell
python scripts\pdf_to_markdown.py
```

Domyślnie przetwarza cały `input/knowledge/` i pomija pliki, dla których
`.md` jest już aktualniejszy niż źródłowy `.pdf` (żeby nie robić OCR od
nowa dla wszystkiego przy każdym uruchomieniu — 300+ stron potrafi
zająć sporo czasu). Wymuszenie ponownej konwersji wszystkiego:

```powershell
python scripts\pdf_to_markdown.py --force
```

Dokumenty rozpoznane (w całości lub częściowo) przez OCR mają na
początku pliku `.md` notkę ostrzegawczą — OCR bywa niedokładny, zwłaszcza
przy podpisach, pieczątkach i tabelach, więc kluczowe dane (daty, kwoty,
nazwiska, numery uchwał) warto zweryfikować przed użyciem.

## Konwersja historycznych protokołów DOCX na Markdown

Skrypt: `scripts/docx_to_markdown.py`. Konwertuje protokoły z
`input/historical_data/reports/` (.docx, natywny tekst Worda — bez OCR,
wyższa jakość niż konwersja skanów) na pliki `.md` w
`input/historical_data/reports_md/`. Gdy dla tego samego protokołu
istnieje zarówno `.docx` jak i `.pdf` (duplikat eksportu), `.pdf` jest
pomijany; używany jest tylko jako fallback (przez OCR), gdy `.docx` nie
istnieje.

```powershell
python scripts\docx_to_markdown.py
python scripts\docx_to_markdown.py --force   # wymuś ponowną konwersję wszystkiego
```
