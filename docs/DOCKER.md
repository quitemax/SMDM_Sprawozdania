# Uruchomienie przez Docker

Alternatywa dla ręcznej instalacji opisanej w `docs/INSTALLATION.md` —
zamiast instalować Python/CUDA/WhisperX/Ollama bezpośrednio na komputerze,
całość działa w kontenerach. Na razie obejmuje to samo, co instalacja
natywna: pracę przez CLI, jednym skryptem na raz (`docker compose exec`).
Webowy interfejs i baza danych to kolejny, osobny etap (patrz
`docs/ROADMAP.md`, Etap 8).

**Status: zweryfikowane end-to-end na realnej maszynie (2026-09-17)** —
build obrazu, GPU passthrough (`torch.cuda.is_available()` → `True`,
RTX 4060 widoczna), ffmpeg + tesseract (`pol`), Ollama osiągalna z
kontenera `app`, pełny przebieg `transcribe.py` (z diaryzacją) →
`identify_speakers.py` → `clean_transcript.py` → `generate_report.py`,
wynik poprawnie widoczny na dysku hosta przez wolumeny. Jedyny problem po
drodze: Docker Desktop wymagał wcześniej ręcznej instalacji WSL2
(`wsl --install` w PowerShell jako Administrator) — bez tego kontener
silnika w ogóle się nie uruchamiał (patrz sekcja „Rozwiązywanie
problemów” niżej).

## Wymagania

- Windows 11 + Docker Desktop (backend WSL2).
- Karta NVIDIA + aktualny sterownik (jak w instalacji natywnej).
- W Docker Desktop: **Settings → Resources → WSL Integration** oraz
  wsparcie GPU (Docker Desktop 4.x+ wykrywa GPU NVIDIA w WSL2 automatycznie,
  bez osobnej instalacji NVIDIA Container Toolkit na Windows — sam sterownik
  Windows wystarczy).
- Token Hugging Face (jak w `docs/INSTALLATION.md`) — potrzebny do diaryzacji.

## Pierwsze uruchomienie

```powershell
copy .env.example .env
notepad .env   # wklej prawdziwy HF_TOKEN

docker compose build
docker compose up -d
```

Weryfikacja, że GPU jest widoczne w kontenerze:

```powershell
docker compose exec app python -c "import torch; print(torch.cuda.is_available())"
```

Powinno wypisać `True`. Jeśli `False` — sprawdź w Docker Desktop, czy WSL2
i wsparcie GPU są włączone (Settings → Resources), i czy `nvidia-smi`
działa w samym WSL2 (poza kontenerem).

Model językowy dla Ollamy trzeba pobrać raz, do kontenera `ollama`:

```powershell
docker compose exec ollama ollama pull SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M
```

## Praca z CLI

Kontener `app` działa w tle (`sleep infinity`) — komendy uruchamia się
przez `docker compose exec`, ścieżki takie same jak przy instalacji
natywnej (`input/`, `output/`, `config/` są zamontowane jako wolumeny,
czyli pliki widoczne są też bezpośrednio na dysku hosta):

```powershell
docker compose exec app python scripts/transcribe.py "input/audio/2026.08.10/10.08.2026.MP3"
docker compose exec app python scripts/identify_speakers.py "output/transcripts/2026.08.10/10.08.2026.json"
docker compose exec app python scripts/clean_transcript.py "output/transcripts/2026.08.10/10.08.2026.json"
docker compose exec app python scripts/generate_report.py "output/transcripts/2026.08.10/10.08.2026.clean.json"
```

Albo wejść do powłoki kontenera i pracować interaktywnie:

```powershell
docker compose exec app bash
```

## Ollama — adres w kontenerze

Skrypty (`identify_speakers.py`, `generate_report.py`) łączą się z Ollamą
pod adresem z `config/config.yaml` (`ollama.host`), nadpisywalnym zmienną
środowiskową `OLLAMA_HOST`. `docker-compose.yml` ustawia
`OLLAMA_HOST=http://ollama:11434` (nazwa usługi w sieci compose) — nie
trzeba nic zmieniać ręcznie, to działa automatycznie inaczej niż przy
instalacji natywnej (tam zostaje domyślny `http://localhost:11434`).

## Pamięć podręczna modeli

Modele WhisperX/Hugging Face (`large-v3`, model wyrównania) i modele
Ollamy zajmują po kilka GB — żeby nie pobierać ich od nowa przy każdym
`docker compose down`/`up`, są trzymane w nazwanych wolumenach Dockera
(`model_cache`, `ollama_data`), a nie w samym obrazie. Wolumeny przeżywają
usunięcie i odtworzenie kontenerów (`docker compose down` bez `-v`);
`docker compose down -v` skasuje je razem z pobranymi modelami.

## Rozwiązywanie problemów

### Docker Desktop w kółko się restartuje / `wslexec` error

Jeśli po starcie Docker Desktop widać powtarzający się błąd w stylu
`running wslexec: ... wsl.exe --version: exit status 1`, WSL2 nie jest
w ogóle zainstalowany (nie tylko nieaktywny) — samo dodanie funkcji
Windows przy instalacji Docker Desktop może nie wystarczyć. Napraw przez:

```powershell
# W PowerShell uruchomionym JAKO ADMINISTRATOR:
wsl --install
```

Zwykle nie wymaga to kolejnego restartu, ale jeśli `wsl --status` dalej
zwraca błąd, zrestartuj system i spróbuj ponownie.

### `docker`/`docker compose` „nie rozpoznano” w terminalu

Świeżo zainstalowany Docker Desktop może nie być jeszcze w `PATH` bieżącej
sesji terminala (podobnie jak przy instalacji Ollamy, patrz
`docs/INSTALLATION.md`) — otwórz nowe okno terminala. Gdyby to nie
pomogło, pełna ścieżka do CLI to zwykle:

```
%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin\docker.exe
```

## Znane ograniczenia

- `tesseract-ocr-pol` w Debianie (obraz bazowy) może być starszą wersją
  pakietu językowego niż ta z `winget` używana w instalacji natywnej —
  jakość OCR może się nieznacznie różnić (nieprzetestowane porównawczo).
- Rozmiar obrazu i czas pierwszego builda nie zostały dokładnie zmierzone
  (build z zimnym cache pip trwał orientacyjnie ~15 minut).
