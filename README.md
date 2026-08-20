# System automatycznego tworzenia raportów ze spotkań

Projekt dla Spółdzielni Mieszkaniowej „Doły-Marysińska”.

System służy do automatycznej transkrypcji nagrań spotkań oraz
przygotowywania na ich podstawie projektów raportów z wykorzystaniem
lokalnych modeli sztucznej inteligencji.

## Dokumentacja

- [Instrukcja obsługi](docs/HOW_TO_USE.md)
- [Instalacja i konfiguracja](docs/INSTALLATION.md)
- [Plan dalszych prac](docs/ROADMAP.md)
- [Historia zmian](docs/HISTORY.md)
- [Pamięć projektu i ustalenia](docs/PROJECT_MEMORY.md)
- [Instrukcje dla agentów AI](docs/AGENTS.md)

## Szybki start

Wymagania i instalacja środowiska opisane są w
[docs/INSTALLATION.md](docs/INSTALLATION.md). Po skonfigurowaniu środowiska:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\transcribe.py "input\audio\<data spotkania>\<plik>.mp3"
```

Wynik (tekst transkrypcji oraz segmenty ze znacznikami czasu) trafia do
`output/transcripts/`, z zachowaniem struktury podkatalogów dat z
`input/audio/`. Pełny opis parametrów i przykłady — patrz
[docs/HOW_TO_USE.md](docs/HOW_TO_USE.md).

## Struktura projektu

| Katalog | Zawartość |
|---|---|
| `config/` | Konfiguracja projektu |
| `docs/` | Dokumentacja |
| `examples/` | Przykładowe dane i raporty |
| `input/` | Dane wejściowe |
| `output/` | Wyniki działania |
| `prompts/` | Prompty dla modeli |
| `scripts/` | Kod projektu |

## Status

Projekt jest obecnie w fazie konfiguracji i budowy środowiska.