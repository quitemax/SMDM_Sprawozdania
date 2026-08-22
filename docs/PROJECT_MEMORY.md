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