# Uruchomienie przez Docker

Alternatywa dla ręcznej instalacji opisanej w `docs/INSTALLATION.md` —
zamiast instalować Python/CUDA/WhisperX/Ollama bezpośrednio na komputerze,
całość działa w kontenerach.

Dwa niezależne poziomy:
- **Krok 1** (ten dokument, sekcje niżej) — sam pipeline przez CLI
  (`docker compose exec app python scripts/...`), dokładnie jak przy
  instalacji natywnej.
- **Krok 2** (sekcja „Webowy interfejs” niżej) — nakładka
  `docker-compose.web.yml` dodająca przeglądarkowy interfejs (Symfony +
  Nuxt + MariaDB) nad tym samym pipeline'em. Krok 1 działa dalej
  samodzielnie, bez Kroku 2.

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

## Webowy interfejs (Krok 2, Faza 0+1)

**Status: zweryfikowane end-to-end (2026-09-17)** — build obrazów, wszystkie
kontenery wystartowane, `/api/health` odpowiada przez pełny łańcuch
przeglądarka → nginx → php-fpm → Symfony, strony Nuxt (`/members`,
`/meetings`) serwowane przez nginx, CRUD składu Rady/Zarządu i edycja
`meeting_info.json` przetestowane bezpośrednimi wywołaniami API —
`meetings/rescan` poprawnie odczytał 3 istniejące realne pliki
`*.meeting_info.json` (z prawidłowymi datami i numerami protokołów), zapis
przez `PUT .../meeting-info` wygenerował plik w formacie w 100% zgodnym z
tym, czego oczekuje `scripts/generate_report.py` (`render_attendance()`
poprawnie sparsowała wynik, łącznie z etykietą „(radca prawny)”).
Weryfikacja samego frontendu (klikanie w formularzach w przeglądarce) nie
została zrobiona — zrobiona tylko warstwa API, którą frontend woła.

Zakres tej fazy, decyzje architektoniczne i pełna mapa kolejnych faz:
`docs/ROADMAP.md`, Etap 8, Krok 2. Model danych i endpointy: plan
`C:\Users\quite\.claude\plans\tender-bouncing-quail.md` (lokalny plik
planu, nie w repo).

### Uruchomienie

```powershell
copy .env.example .env
notepad .env   # uzupełnij HF_TOKEN, MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD

docker compose -f docker-compose.yml -f docker-compose.web.yml up -d --build

# Jednorazowo (albo po każdej zmianie encji Doctrine) — tworzy/aktualizuje
# tabele w MariaDB na podstawie src/Entity/*.php. Na razie zamiast
# formalnych migracji (Doctrine Migrations jest zainstalowane, ale
# nieużywane w tej fazie — celowo, żeby nie komplikować MVP):
docker compose -f docker-compose.yml -f docker-compose.web.yml exec php-fpm php bin/console doctrine:schema:update --force
```

Interfejs: **http://localhost:8080** (nginx — jeden punkt wejścia; `/api/*`
trafia do Symfony, reszta do Nuxt). Krok 1 (`docker compose up -d`, bez
nakładki) działa dalej niezależnie i nie jest tym dotknięty.

### Struktura

- `web/backend/` — Symfony 7.4 + Doctrine ORM (encje `Member`, `Meeting`,
  `MeetingAttendee`), kontrolery REST w `src/Controller/Api/`.
- `web/frontend/` — Nuxt 4 (tryb SPA, `ssr: false` — to wewnętrzne
  narzędzie administracyjne, nie potrzebuje SSR/SEO), tryb dev
  (`npm run dev`, hot reload) — build produkcyjny to temat na później.
- `web/nginx/default.conf` — reverse proxy: `/api/` → php-fpm (fastcgi),
  `/` → kontener `nuxt` (proxy_pass).
- `docker-compose.web.yml` — nakładka na `docker-compose.yml` (usługi
  `mariadb`, `php-fpm`, `nginx`, `nuxt`).

### Źródło prawdy

`<nazwa>.meeting_info.json` na dysku (`output/transcripts/<data>/`) zostaje
źródłem prawdy — czytają go bezpośrednio `clean_transcript.py` i
`generate_report.py`. Baza danych (`meetings`, `meeting_attendees`) to
indeks/cache do UI, synchronizowany przy każdym zapisie z interfejsu
(`PUT .../meeting-info`: najpierw plik, potem baza) oraz przez
`POST /api/meetings/rescan`. Skład Rady Nadzorczej/Zarządu
(tabela `members`) nie ma odpowiednika pliku — baza jest tu jedynym
źródłem prawdy.

### Znane ograniczenie: jedna osoba = jedna rola na spotkanie

Jeśli ta sama osoba zostanie przypisana do dwóch ról specjalnych
(protokolant/sekretarz/przewodniczący) na tym samym spotkaniu, druga
przypisana rola po cichu nadpisuje pierwszą (jeden wiersz
`meeting_attendees` ma tylko jedno pole `role`). W praktyce to zawsze trzy
różne osoby (potwierdzone we wszystkich 18 historycznych protokołach), więc
nie blokuje MVP — ale UI nie ostrzega, gdyby ktoś przez pomyłkę wybrał tę
samą osobę dwa razy.

## Faza 2 — Identyfikacja mówców i podgląd transkrypcji w przeglądarce

Zastępuje ręczne odsłuchiwanie próbek w Eksploratorze + edycję
`<nazwa>.speakers.json` w edytorze tekstu (patrz
`scripts/extract_speaker_samples.py`).

- `GET /api/meetings/{id}/speakers` — lista mówców z pliku `.speakers.json`.
- `PUT /api/meetings/{id}/speakers/{label}` — zapisuje `proposed_name`;
  zawsze ustawia `source: "manual"` (wpis z UI = potwierdzony przez
  człowieka, tak samo jak przy ręcznej edycji, patrz
  `docs/PROJECT_MEMORY.md`).
- `GET /api/meetings/{id}/speakers/{label}/sample/{n}` — strumieniuje plik
  `.mp3` (`BinaryFileResponse`, wsparcie dla zakresów HTTP "za darmo" —
  potrzebne, żeby `<audio>` w przeglądarce mogło przewijać).
- `GET /api/meetings/{id}/transcript` — zwraca treść `.clean.txt` do
  podglądu (tylko odczyt).

Strony Nuxt: `/meetings/{id}/speakers` (odtwarzacze audio + pole na
imię/nazwisko per mówca) i `/meetings/{id}/transcript` (podgląd tekstu).

**Zweryfikowane:** poprawność endpointów oraz — potwierdzone przez
użytkownika w przeglądarce (2026-09-19) — faktyczne odtwarzanie próbek
audio działa.

## Faza 2.5 — CRUD nagrań (upload, lista, usuwanie)

Pierwszy krok pipeline'u, zanim `scripts/transcribe.py` w ogóle wchodzi
do gry — miejsce na wgranie nowego nagrania z przeglądarki, zamiast
ręcznego kopiowania pliku do `input/audio/RRRR.MM.DD/`. Samo
uruchomienie transkrypcji z przeglądarki to Faza 3 (job runner).

- `GET /api/recordings` — skanuje `input/audio/**` (rozszerzenia mp3, m4a,
  wav, mp4, aac, ogg, wma), dla każdego pliku sprawdza, czy istnieje już
  transkrypcja (`has_transcript`).
- `POST /api/recordings` — upload wieloczęściowy (`date` w formacie
  RRRR-MM-DD, `file`); zapisuje pod `input/audio/RRRR.MM.DD/<nazwa>`, nie
  nadpisuje istniejącego pliku (dopisuje sufiks przy konflikcie nazw).
- `DELETE /api/recordings?path=...` — usuwa plik z dysku.

Strona Nuxt: `/recordings` (formularz uploadu + tabela z rozmiarem i
statusem transkrypcji).

Limity uploadu podniesione (nagrania bywają > 100 MB): PHP
`upload_max_filesize`/`post_max_size` = 1G (`web/backend/Dockerfile`),
nginx `client_max_body_size` = 1g (`web/nginx/default.conf`).

**Zweryfikowane:** lista (31 prawdziwych nagrań, poprawne `has_transcript`),
upload i usuwanie na pliku testowym. **Niezweryfikowane:** upload
naprawdę dużego (setki MB) pliku audio z przeglądarki — testowano tylko
małym plikiem przez `curl`.

## Rozwiązywanie problemów

### Zapytania do API całkowicie się zawieszają po `docker compose up --build php-fpm`/`nuxt`

**Znaleziona i potwierdzona przyczyna (2026-09-19):** nginx rozwiązuje
nazwę hosta w `fastcgi_pass php-fpm:9000;` / `proxy_pass http://nuxt:3000`
raz, przy starcie/reloadzie. Kiedy `php-fpm` albo `nuxt` zostaje odtworzony
(`docker compose up -d --build ...`, `up -d ...` po zmianie w
`docker-compose.web.yml` itp.), kontener dostaje NOWY adres IP w sieci
Dockera — ale nginx, jeśli sam nie został zrestartowany, nadal próbuje
łączyć się pod starym, martwym adresem. Objaw: żądanie wisi bez końca (30s+
i więcej), a w logu `php-fpm` w ogóle nie widać, żeby request dotarł.

**Zasada:** za każdym razem, gdy przebudowujesz/odtwarzasz `php-fpm` lub
`nuxt`, zrestartuj też `nginx`:

```powershell
docker compose -f docker-compose.yml -f docker-compose.web.yml restart nginx
```

Samo `nginx -s reload` czasem NIE wystarczyło w testach — pełny restart
kontenera (`restart`, nie `reload`) był niezawodny.

### Odpowiedzi API działają, ale są wolne (~5-7 sekund na zapytanie)

Po naprawieniu powyższego (restart nginx) zapytania przestają się wieszać,
ale nawet trywialny `/api/health` bez dostępu do bazy nadal trwa
kilka sekund — mimo że bezpośrednie połączenie PHP→MariaDB jest
błyskawiczne (~2ms) i żaden kontener nie pokazuje podwyższonego zużycia
CPU/RAM (`docker stats`). Nie zdiagnozowano ostatecznie źródła tego
resztkowego opóźnienia — podejrzenie pada na narzut Windows/WSL2 przy
operacjach plikowych w trybie dev Symfony (dużo małych odczytów/zapisów
przy sprawdzaniu świeżości cache kontenera DI). Wykluczenia w Windows
Defender (Wirus i zagrożenia → Ustawienia → Wykluczenia, dla
`%LOCALAPPDATA%\Docker\wsl\` i katalogu repozytorium) przetestowane, bez
wyraźnej poprawy — mimo to warto je zostawić. Dla wewnętrznego narzędzia
używanego okazjonalnie kilka sekund na żądanie nie blokuje pracy, ale
warto to zbadać dokładniej, jeśli stanie się to uciążliwe (np. profilowanie
przez `docker compose exec php-fpm php bin/console debug:container` albo
sprawdzenie, czy `APP_ENV=prod` zauważalnie przyspiesza).

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
