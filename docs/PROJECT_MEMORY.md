# Pamięć projektu

Ten dokument zawiera ważne ustalenia, decyzje projektowe oraz informacje,
które powinny zostać zachowane podczas dalszego rozwoju projektu.

## Cel projektu

Celem projektu jest stworzenie lokalnego systemu umożliwiającego:

1. Przyjęcie nagrania spotkania w formacie audio.
2. Automatyczną transkrypcję nagrania.
3. Rozpoznanie i oznaczenie poszczególnych mówców.
4. Przetworzenie i uporządkowanie transkrypcji.
5. Analizę treści spotkania przez lokalny model językowy.
6. Przygotowanie projektu długiego, narracyjnego raportu.
7. Weryfikację raportu przez pracownika.

## Założenia

- System ma działać lokalnie.
- Nagrania spotkań nie powinny być wysyłane do zewnętrznych usług AI.
- Projekt ma być możliwy do odtworzenia na innym komputerze.
- Konfiguracja środowiska powinna być udokumentowana.
- Istotne decyzje projektowe powinny być zapisywane w tym dokumencie.

## Dane historyczne

Do projektu zostaną wykorzystane wcześniejsze raporty przygotowane przez pracowników.

Dla części materiałów dostępne są również odpowiadające im nagrania spotkań.

Materiały te będą wykorzystywane jako przykłady sposobu opracowywania raportów.

## Sprzęt używany podczas tworzenia projektu

- ASUS Zenbook Pro 14 Duo UX8402VV
- NVIDIA GeForce RTX 4060 Laptop
- 32 GB RAM

## Model językowy

Do analizy treści spotkań i generowania raportów wybrano
`SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M` (Ollama) — dobre wsparcie
języka polskiego, kwantyzacja Q4_K_M mieści się niemal w całości w 8 GB
VRAM dostępnego GPU. W razie problemów z jakością lub wydajnością przy
dłuższych transkrypcjach do rozważenia alternatywy: mniejszy kwant tego
modelu albo modele uniwersalne (Llama 3.1, Mistral, Gemma 2).

## Identyfikacja mówców (SPEAKER_XX → imię/nazwisko)

Decyzja projektowa: mapowanie mówców na imiona/nazwiska, wnioskowane przez
model językowy z kontekstu transkrypcji, jest zapisywane WYŁĄCZNIE jako
osobna propozycja do ręcznej weryfikacji (`<nazwa>.speakers.json`),
nigdy nie podmienia automatycznie etykiet w transkrypcji. Powód: model
11B (Q4_K_M) w testach popełniał wyraźne błędy wnioskowania (mylenie
osoby, o której mowa, z faktycznym mówcą) mimo jawnych instrukcji w
prompcie — zbyt duże ryzyko błędnego przypisania wypowiedzi w oficjalnym
dokumencie spółdzielni, żeby robić to bez nadzoru człowieka.

Potwierdzone realnym przykładem (posiedzenie 27.06.2025): model przypisał
etykietę na podstawie mylącego poszlaki w rozmowie, podczas gdy faktyczna
tożsamość osoby prowadzącej zebranie (widoczna dopiero w podpisie
odpowiadającego protokołu historycznego) była inna. Stąd rozszerzenie
2026-08-30: `scripts/extract_speaker_samples.py` wycina dla każdego
SPEAKER_XX krótkie próbki audio (najdłuższe wypowiedzi danego mówcy) do
pola `audio_samples` w tym samym `<nazwa>.speakers.json` — żeby
pracownik mógł odsłuchać głos i wpisać imię/nazwisko ręcznie, zamiast
polegać wyłącznie na wnioskowaniu modelu z treści. Plik rozróżnia teraz
źródło wpisu przez pole `source`:
- `"model"` (albo brak pola — starsze pliki) — propozycja modelu,
  `clean_transcript.py` zawsze pokazuje ją ze znakiem zapytania
  (`Leon (SPEAKER_07?)`),
- `"manual"` — potwierdzone przez człowieka po odsłuchaniu próbki,
  wyświetlane bez znaku zapytania.

`identify_speakers.py` i `extract_speaker_samples.py` współdzielą ten sam
plik i scalają się niezależnie od kolejności uruchomienia: żaden z nich
nie nadpisuje wpisu ze `source: "manual"`, a pole `audio_samples` jest
zawsze zachowywane przy ponownym uruchomieniu `identify_speakers.py`.

## Metadane spotkania spoza transkrypcji (meeting_info.json)

Decyzja projektowa (2026-08-30, przy planowaniu Etapu 4 — generowania
projektu sprawozdania): część danych wymaganych w oficjalnym protokole RN
nie da się wiarygodnie odtworzyć z samego nagrania:
- **lista obecności** — to fizyczna lista podpisów (załącznik), nie plik
  cyfrowy; identyfikacja mówców z nagrania obejmuje tylko osoby, które
  faktycznie coś powiedziały, i to z niepewnością (patrz wyżej),
- **kto protokołował / pełnił funkcję sekretarza / przewodniczącego** —
  funkcje rotują między spotkaniami i nie zawsze są ogłaszane wprost w
  nagraniu (w całym dostępnym korpusie historycznym protokołowała zawsze
  ta sama osoba — Aleksandra Cecotka — ale to obserwacja, nie pewnik na
  przyszłość).

Zamiast zgadywać te pola modelem, `scripts/init_meeting_info.py` tworzy
pusty szablon `<nazwa>.meeting_info.json` obok transkrypcji (jedyne pole
wypełniane automatycznie to `date`, odczytywane z nazwy katalogu — fakt
znany na pewno, nie wywnioskowany) do ręcznego uzupełnienia przez
pracownika przed wygenerowaniem projektu sprawozdania.

## Generowanie projektu sprawozdania (scripts/generate_report.py)

Decyzja projektowa (2026-09-17): priorytetem generatora jest wierna i
KOMPLETNA relacja z przebiegu spotkania, a nie imitacja zwięzłej,
sformalizowanej struktury historycznych protokołów. Wynikowy dokument może
być dłuższy niż typowy historyczny protokół — to świadomy wybór, nie wada.

Powód: trzy kolejne próby wymuszenia ścisłego przypisania każdej wypowiedzi
do jednego z ponumerowanych punktów porządku obrad (cała transkrypcja na
raz → sztywne okna czasowe → osobny przebieg "tagujący") kończyły się
błędami wynikającymi WŁAŚNIE z tego wymuszenia: ucinanie kontekstu,
mieszanie treści sąsiednich punktów, zawyżone/nakładające się zakresy
przypisań i fikcyjne uchwały. Rozwiązaniem nie było poprawianie promptów
w ramach tej architektury, tylko zmiana samego wymagania — zrezygnowanie
z sztywnego podziału na rzecz chronologicznej relacji, dzielonej na kawałki
tylko ze względu na limit kontekstu modelu (~45 wypowiedzi/kawałek),
bez wymuszania przynależności do konkretnego punktu. Szczegóły
architektury i porównanie wersji: `docs/ROADMAP.md`, Etap 4.

Pochodna decyzja: uchwały wykryte w kilku kawałkach transkrypcji (bo
dyskusja do tematu wraca później) są deduplikowane po podobieństwie tematu
(`difflib.SequenceMatcher` ≥ 0.65) przed nadaniem numeru — bez tego ten sam
temat dostawał kilka numerów pod rząd, przesuwając numerację kolejnych,
prawdziwych uchwał.

Test na posiedzeniu 22.06.2026 (dla którego istnieje gotowe sprawozdanie
`Protokół 8 RN 22.06.2026.md`, więc dało się bezpośrednio porównać): 4/4
uchwały trafione (temat i numeracja), pełna chronologiczna relacja, zero
treści o sporach osobistych. Nadal zdarzają się pojedyncze dosłowne cytaty
z transkrypcji zamiast parafrazy (częściowe zabezpieczenie w kodzie,
`strip_verbatim_quotes`) — stąd wynik to zawsze WYŁĄCZNIE projekt do
weryfikacji przez pracownika (Etap 5), nigdy gotowy dokument.

## Baza wiedzy z dokumentów spółdzielni (input/knowledge/)

Regulaminy, uchwały i umowy w `input/knowledge/` to w większości skany —
prawie bez warstwy tekstowej. `scripts/pdf_to_markdown.py` konwertuje je
na Markdown w `input/knowledge_md/` (ta sama struktura katalogów),
z OCR (Tesseract, `pol`) dla stron bez tekstu. Oba katalogi —
`input/knowledge/` (PDF) i `input/knowledge_md/` (Markdown) — są w
repozytorium Git (świadoma decyzja, patrz commit initial). Cel:
baza wiedzy do audytu i odwoływania się w sprawozdaniach (Etap 4).
Dokumenty (częściowo) rozpoznane przez OCR mają notkę ostrzegawczą w
pliku `.md` — jakość OCR jest dobra dla treści merytorycznej, ale
słabsza przy podpisach/pieczątkach/tabelach, więc kluczowe dane wymagają
weryfikacji przed użyciem w oficjalnym dokumencie.

## Repozytorium Git

Projekt jest wersjonowany w repozytorium GitHub:
https://github.com/quitemax/SMDM_Sprawozdania

## Uwagi

Ten dokument należy aktualizować w przypadku podjęcia istotnych decyzji
wpływających na sposób działania projektu.