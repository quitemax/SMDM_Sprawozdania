"""Generowanie PROJEKTU sprawozdania z posiedzenia Rady Nadzorczej z oczyszczonej transkrypcji.

Historia podejść (patrz docs/ROADMAP.md, Etap 4) — trzy kolejne wersje
próbowały odtworzyć DOKŁADNĄ strukturę historycznych protokołów (ścisłe
przypisanie każdej wypowiedzi do jednego z ponumerowanych punktów porządku
obrad) i za każdym razem to sztywne wymaganie powodowało błędy:
- v1: cała transkrypcja w jednym zapytaniu — przy dłuższych nagraniach
  (~27k+ tokenów) przekraczało to limit kontekstu, Ollama ucinała
  najstarszą część promptu (akurat początek z porządkiem obrad), model
  zmyślał resztę.
- v2: sztywne okna (CHUNK_SIZE wypowiedzi), każde streszczane od razu z
  przypisaniem do punktu — okna często przecinały dyskusję w połowie
  punktu, mieszając treść sąsiednich punktów.
- v3: osobny przebieg "tagujący" (przypisanie wypowiedzi do punktów) przed
  streszczaniem — model przypisywał zbyt szerokie, nakładające się zakresy
  (suma wypowiedzi per punkt przekraczała łączną liczbę wypowiedzi w
  nagraniu), przez co niemal każdy punkt "dziedziczył" cudze treści i
  fikcyjne uchwały.

**v4 (bieżąca)** rezygnuje z wymuszania ścisłego podziału na punkty
porządku obrad — decyzja projektowa 2026-09-17: priorytetem jest wierna,
kompletna relacja z przebiegu spotkania, nawet jeśli wynikowy dokument jest
dłuższy/mniej skompresowany niż historyczne protokoły, a nie imitacja ich
zwięzłej struktury. Zamiast wymuszać przynależność do konkretnego punktu:

1. **Porządek obrad** — jedno małe zapytanie o początkowy fragment
   transkrypcji, wyłącznie jako nagłówek informacyjny w dokumencie.
2. **Chronologiczna relacja** — transkrypcja dzielona na kawałki
   (CHUNK_SIZE wypowiedzi w kolejności czasowej); każdy kawałek daje: (a)
   wierny, rzeczowy akapit o tym, co się wydarzyło, (b) uchwały faktycznie
   podjęte w tym kawałku (z wynikiem głosowania), (c) sprawy załatwione
   nieformalnie (bez uchwały). Brak sztywnego przypisania do numeru punktu
   eliminuje ryzyko mieszania sąsiednich tematów — kawałki po prostu
   następują po sobie chronologicznie, tak jak przebiegało spotkanie.
3. **Renderowanie** — deterministyczne (czysty Python): akapity relacji
   sklejone w kolejności, uchwały ponumerowane sekwencyjnie (wg
   najwyższego dotychczas użytego numeru w danym roku kalendarzowym +
   kolejność wystąpienia), sprawy nieformalne zebrane w osobnej sekcji.

Znane, nie do końca rozwiązane ograniczenie: model czasem mimo instrukcji
kopiuje fragmenty dosłownych, nieformalnych wypowiedzi zamiast parafrazować
(częściowe zabezpieczenie: strip_verbatim_quotes) — projekt zawsze wymaga
redakcji przez człowieka przed użyciem.

Dane niemożliwe do wyciągnięcia z transkrypcji (lista obecności,
protokolant, sekretarz, przewodniczący) pochodzą z ręcznie uzupełnionego
<nazwa>.meeting_info.json (patrz scripts/init_meeting_info.py) — brakujące
pola zostają jako [DO UZUPEŁNIENIA].

Wynik to WYŁĄCZNIE projekt do weryfikacji przez pracownika (Etap 5) —
nigdy nie jest to gotowy, zatwierdzony dokument.
"""

import argparse
import difflib
import json
import re
from pathlib import Path

import requests

from config import load_config

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT = 900
CHUNK_NUM_CTX = 8192

# Wypowiedzi na kawałek — przy ~230 znakach/wypowiedź to ok. 4-5 tys.
# tokenów tekstu, z zapasem na instrukcje/schemat/odpowiedź w limicie
# CHUNK_NUM_CTX. Liczba wypowiedzi wziętych na wykrycie porządku obrad
# (zwykle odczytywany w pierwszych minutach nagrania).
CHUNK_SIZE = 45
AGENDA_EXCERPT_TURNS = 40

RESOLUTION_PATTERN = re.compile(r"[Uu]chwał\w*\s*(?:Nr|nr)\s*(\d+)\s*/\s*R\s*/\s*(\d{2,4})")

# Zabezpieczenie na wypadek, gdyby model mimo instrukcji w prompcie i tak
# wypisał wprost, że w danym fragmencie nic się nie wydarzyło (zamiast po
# prostu zostawić pole puste) — taki tekst nie powinien trafić do relacji.
NEGATIVE_MENTION_PATTERN = re.compile(r"nie (ma|by[łl]o) (wzmianki|nic)|brak (wzmianki|istotnych)", re.IGNORECASE)

# Zabezpieczenie na wypadek, gdyby model mimo instrukcji w prompcie i tak
# skopiował dosłownie linijkę transkrypcji ("Imię Nazwisko: wypowiedź") do
# relacji zamiast parafrazować — usuwamy takie zdania na poziomie zdań, bo
# zwykle sąsiadują z poprawnie sparafrazowanym tekstem w tym samym fragmencie.
SPEAKER_QUOTE_SENTENCE = re.compile(r"^[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż-]*(?:\s[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż-]*){0,7}:\s")


def strip_verbatim_quotes(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = [s for s in sentences if not SPEAKER_QUOTE_SENTENCE.match(s)]
    return " ".join(kept).strip()


AGENDA_SCHEMA = {
    "type": "object",
    "properties": {
        "agenda_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "integer"},
                    "title": {"type": "string"},
                },
                "required": ["number", "title"],
            },
        },
    },
    "required": ["agenda_items"],
}

AGENDA_PROMPT_TEMPLATE = """\
Poniżej jest POCZĄTEK transkrypcji posiedzenia Rady Nadzorczej spółdzielni
mieszkaniowej. Na początku takiego spotkania przewodniczący/a zwykle
odczytuje porządek obrad — ponumerowaną listę punktów, które będą omawiane.

Znajdź tę listę i zwróć ją jako "agenda_items" (number = numer punktu,
title = treść punktu, możliwie blisko oryginalnego sformułowania). Jeśli
lista nie pojawia się w ogóle w tym fragmencie, zwróć pustą listę.

Transkrypcja (numer wypowiedzi, mówca, tekst):
{transcript}
"""

CHUNK_SCHEMA = {
    "type": "object",
    "properties": {
        "narrative": {"type": "string"},
        "resolutions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "members_present": {"type": ["integer", "null"]},
                    "votes_for": {"type": ["integer", "null"]},
                    "votes_against": {"type": ["integer", "null"]},
                    "votes_abstain": {"type": ["integer", "null"]},
                },
                "required": ["subject", "members_present", "votes_for", "votes_against", "votes_abstain"],
            },
        },
        "raised_matters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "decision": {"type": "string"},
                },
                "required": ["description", "decision"],
            },
        },
    },
    "required": ["narrative", "resolutions", "raised_matters"],
}

CHUNK_PROMPT_TEMPLATE = """\
Dla kontekstu, znany porządek obrad tego posiedzenia Rady Nadzorczej
spółdzielni mieszkaniowej (nie musisz się do niego sztywno ograniczać —
poniższy fragment może dotyczyć jednego punktu, kilku naraz, albo żadnego):
{agenda}

Poniżej jest FRAGMENT transkrypcji (wypowiedzi {start}-{end} z {total}) —
kolejny wycinek spotkania w porządku chronologicznym.

Twoje zadanie: napisz WIERNĄ, rzeczową relację z tego, co się wydarzyło w
tym fragmencie — to fragment oficjalnego sprawozdania z posiedzenia.

Zasady dla "narrative" (bardzo ważne):
- Opisuj FAKTY: co zostało zaprezentowane/omówione, jakie padły wnioski,
  kandydatury, ustalenia, jakie decyzje zapadły. Możesz być tak
  szczegółowy, jak potrzeba — długość nie jest ograniczona, liczy się
  kompletność i wierność, a nie zwięzłość za wszelką cenę.
- ZAWSZE parafrazuj własnymi słowami, w stronie trzeciej. NIGDY nie
  kopiuj dosłownie linijek transkrypcji ze znacznikiem mówcy (np. "Jan
  Kowalski: ...") ani potocznych, nieformalnych zdań — to oficjalny
  dokument.
- NIGDY nie opisuj sporów osobistych, pretensji, żartów, wycieczek
  personalnych ani prywatnych wątków niezwiązanych z działalnością
  spółdzielni — nawet jeśli zajmowały dużo czasu w rozmowie.
- Jeśli w tym fragmencie nie wydarzyło się nic istotnego dla sprawozdania
  (powitania, sprawy techniczne typu "czy mnie słychać", przerwa), po
  prostu zostaw "narrative" jako pusty string — nie pisz o tym, że nic się
  nie wydarzyło.

Zasady dla "resolutions" (uchwały FAKTYCZNIE PODJĘTE w tym fragmencie):
- Dla każdej: krótki temat (do 15 słów) i liczby głosowania, jeśli podane
  (jeśli "jednogłośnie" + liczba obecnych, przyjmij votes_for = liczba
  obecnych, votes_against = 0, votes_abstain = 0; jeśli liczby w ogóle nie
  padają, zostaw jako null).
- Nie wymyślaj uchwał — tylko te naprawdę przegłosowane w tym fragmencie.

Zasady dla "raised_matters" (sprawy rozstrzygnięte NIEFORMALNIE, bez
uchwały — np. odpowiedź na pismo, decyzja organizacyjna, ustalenie terminu):
- Konkretna sprawa + jaka zapadła decyzja/ustalenie. Pomiń, jeśli nic
  takiego nie miało miejsca w tym fragmencie.

Fragment transkrypcji:
{transcript}
"""


def load_turns(clean_json_path: Path) -> list[dict]:
    data = json.loads(clean_json_path.read_text(encoding="utf-8"))
    return data.get("turns", [])


def format_transcript(turns: list[dict], indices) -> str:
    return "\n".join(f"[{i}] {t.get('speaker_display', t.get('speaker', '?'))}: {t['text']}" for i, t in zip(indices, turns))


def ollama_generate(prompt: str, schema: dict, model: str, num_ctx: int) -> dict:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "format": schema,
            "stream": False,
            "options": {"num_ctx": num_ctx, "temperature": 0.1},
        },
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()
    return json.loads(response.json()["response"])


def extract_agenda(turns: list[dict], model: str) -> list[dict]:
    excerpt = turns[:AGENDA_EXCERPT_TURNS]
    prompt = AGENDA_PROMPT_TEMPLATE.format(transcript=format_transcript(excerpt, range(len(excerpt))))
    result = ollama_generate(prompt, AGENDA_SCHEMA, model, CHUNK_NUM_CTX)
    return sorted(result.get("agenda_items", []), key=lambda i: i["number"])


def format_agenda(agenda_items: list[dict]) -> str:
    return "\n".join(f"{item['number']}. {item['title']}" for item in agenda_items) or "(nie wykryto)"


def extract_chunk(turns: list[dict], start: int, end: int, total: int, agenda_text: str, model: str) -> dict:
    chunk = turns[start:end]
    prompt = CHUNK_PROMPT_TEMPLATE.format(
        agenda=agenda_text,
        start=start,
        end=end - 1,
        total=total,
        transcript=format_transcript(chunk, range(start, end)),
    )
    return ollama_generate(prompt, CHUNK_SCHEMA, model, CHUNK_NUM_CTX)


def extract_facts(turns: list[dict], model: str) -> dict:
    print("  Etap 1/2: wykrywanie porządku obrad z początku nagrania...")
    agenda_items = extract_agenda(turns, model)
    if agenda_items:
        print(f"  Znaleziono {len(agenda_items)} punktów: " + "; ".join(i["title"] for i in agenda_items))
    else:
        print("  Nie wykryto porządku obrad — sekcja w dokumencie zostanie pusta, relacja i tak powstanie.")
    agenda_text = format_agenda(agenda_items)

    total = len(turns)
    narrative_paragraphs: list[str] = []
    resolutions: list[dict] = []
    raised_matters: list[dict] = []

    chunk_starts = list(range(0, total, CHUNK_SIZE))
    print("  Etap 2/2: chronologiczna relacja z przebiegu posiedzenia...")
    for chunk_idx, start in enumerate(chunk_starts, start=1):
        end = min(start + CHUNK_SIZE, total)
        print(f"    fragment {chunk_idx}/{len(chunk_starts)} (wypowiedzi {start}-{end - 1})...")
        result = extract_chunk(turns, start, end, total, agenda_text, model)

        narrative = result.get("narrative", "")
        if narrative and not NEGATIVE_MENTION_PATTERN.search(narrative):
            cleaned = strip_verbatim_quotes(narrative)
            if cleaned:
                narrative_paragraphs.append(cleaned)

        resolutions.extend(result.get("resolutions", []))

        for matter in result.get("raised_matters", []):
            description = strip_verbatim_quotes(matter.get("description", ""))
            decision = strip_verbatim_quotes(matter.get("decision", ""))
            if description or decision:
                raised_matters.append({"description": description, "decision": decision})

    deduped_resolutions = deduplicate_resolutions(resolutions)
    if len(deduped_resolutions) < len(resolutions):
        print(f"  Scalono {len(resolutions) - len(deduped_resolutions)} zduplikowanych uchwał (ten sam temat wykryty w kilku fragmentach).")

    return {
        "agenda_items": agenda_items,
        "narrative_paragraphs": narrative_paragraphs,
        "resolutions": deduped_resolutions,
        "raised_matters": raised_matters,
    }


# Próg podobieństwa tematów uchwał (SequenceMatcher.ratio) powyżej którego
# dwa wpisy uznajemy za tę samą uchwałę wykrytą dwukrotnie (np. bo dyskusja
# do tematu wróciła w innym kawałku transkrypcji) — dobrany empirycznie:
# 0.80 dla faktycznego duplikatu, 0.53 i 0.46 dla naprawdę różnych uchwał
# o zbliżonej strukturze zdania (np. dwóch "Zatwierdzenie ...").
RESOLUTION_DEDUP_THRESHOLD = 0.65


def deduplicate_resolutions(resolutions: list[dict]) -> list[dict]:
    """Ten sam temat bywa wykryty w kilku (niekoniecznie sąsiednich)
    kawałkach transkrypcji, np. gdy dyskusja do niego wraca później —
    scala wpisy o bardzo podobnym temacie w jeden, uzupełniając dane
    głosowania z duplikatu, jeśli oryginał ich nie miał."""
    kept: list[dict] = []
    for res in resolutions:
        subject = (res.get("subject") or "").strip().lower()
        match = next(
            (e for e in kept if difflib.SequenceMatcher(None, subject, (e.get("subject") or "").strip().lower()).ratio() >= RESOLUTION_DEDUP_THRESHOLD),
            None,
        )
        if match is None:
            kept.append(dict(res))
            continue
        for field in ("members_present", "votes_for", "votes_against", "votes_abstain"):
            if match.get(field) is None and res.get(field) is not None:
                match[field] = res[field]
    return kept


def get_next_resolution_number(reports_md_root: Path, year_suffix: str) -> int:
    """Skanuje reports_md w poszukiwaniu najwyższego użytego numeru uchwały
    dla danego roku (2-cyfrowy sufiks, np. "26") i zwraca kolejny wolny numer."""
    max_n = 0
    for md_file in reports_md_root.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        for num, year in RESOLUTION_PATTERN.findall(text):
            if year[-2:] == year_suffix:
                max_n = max(max_n, int(num))
    return max_n + 1


def format_attendee_group(label: str, names: list[str]) -> str | None:
    if not names:
        return None
    return f"- {label}: {', '.join(names)}"


def render_attendance(attendees: dict) -> list[str]:
    lines = []
    rada = attendees.get("rada_nadzorcza", [])
    zarzad = attendees.get("zarzad", [])
    inni = attendees.get("inni", [])

    if rada:
        lines.append(f"- członkowie Rady Nadzorczej wg listy obecności (załącznik nr 1): {', '.join(rada)}")
    else:
        lines.append("- członkowie Rady Nadzorczej wg listy obecności (załącznik nr 1): [DO UZUPEŁNIENIA]")

    group = format_attendee_group("Zarząd Spółdzielni", zarzad)
    if group:
        lines.append(group)

    # "inni" bywa zapisane jako "Imię Nazwisko (rola)" — grupujemy po roli.
    by_role: dict[str, list[str]] = {}
    for entry in inni:
        match = re.match(r"^(.*?)\s*\((.*?)\)\s*$", entry)
        if match:
            name, role = match.groups()
            by_role.setdefault(role.strip().capitalize(), []).append(name.strip())
        else:
            by_role.setdefault("Inni", []).append(entry)
    for role, names in by_role.items():
        lines.append(f"- {role}: {', '.join(names)}")

    return lines


def render_vote(members_present, votes_for, votes_against, votes_abstain, action: str) -> str:
    against = votes_against or 0
    abstain = votes_abstain or 0

    if members_present is None or votes_for is None:
        return f"Rada Nadzorcza {action} [DO UZUPEŁNIENIA: dokładny wynik głosowania nieznany z transkrypcji]."

    unanimous = against == 0 and abstain == 0 and votes_for == members_present
    if unanimous:
        return f"Rada Nadzorcza w obecności {members_present} członków jednogłośnie {action}."

    against_txt = "brakiem głosów przeciw" if against == 0 else ("1 głosem przeciw" if against == 1 else f"{against} głosami przeciw")
    abstain_txt = (
        "brakiem głosów wstrzymujących się"
        if abstain == 0
        else ("1 głosem wstrzymującym się" if abstain == 1 else f"{abstain} głosami wstrzymującymi się")
    )
    return f"Rada Nadzorcza w obecności {members_present} członków, {votes_for} głosami za, {against_txt} oraz {abstain_txt} {action}."


def render_resolutions(resolutions: list[dict], reports_md_root: Path, year_suffix: str) -> list[str]:
    if not resolutions:
        return []

    lines = ["**Podjęte uchwały:**", ""]
    next_number = get_next_resolution_number(reports_md_root, year_suffix)
    for res in resolutions:
        number = next_number
        next_number += 1
        action = f"podjęła uchwałę Nr {number}/R/{year_suffix} w sprawie {res.get('subject', '[DO UZUPEŁNIENIA]')}"
        lines.append(
            render_vote(res.get("members_present"), res.get("votes_for"), res.get("votes_against"), res.get("votes_abstain"), action)
        )
        lines.append("Uchwała stanowi załącznik do niniejszego protokołu.")
        lines.append("")
    return lines


def render_raised_matters(raised_matters: list[dict]) -> list[str]:
    if not raised_matters:
        return []
    lines = ["**Sprawy wniesione i inne ustalenia:**", ""]
    for matter in raised_matters:
        lines.append(f"- {matter['description']} {matter['decision']}".strip())
    lines.append("")
    return lines


def render_report(meeting_info: dict, facts: dict, reports_md_root: Path) -> str:
    date = meeting_info.get("date") or "[DO UZUPEŁNIENIA]"
    protocol_number = meeting_info.get("protocol_number") or "[DO UZUPEŁNIENIA]"
    try:
        date_display = "-".join(reversed(date.split("-"))) if date != "[DO UZUPEŁNIENIA]" else date
        year_suffix = date.split("-")[0][-2:]
    except (IndexError, AttributeError):
        date_display = date
        year_suffix = "??"

    lines = [
        f"# Protokół {protocol_number} (PROJEKT)",
        "",
        "> **UWAGA: to jest automatycznie wygenerowany PROJEKT sprawozdania, wymagający",
        "> weryfikacji przez pracownika przed zatwierdzeniem (patrz docs/ROADMAP.md, Etap 5).",
        "> Relację z przebiegu posiedzenia wygenerował lokalny model językowy na podstawie",
        "> transkrypcji nagrania — może zawierać błędy lub pominięcia. Celowo priorytetem",
        "> jest wierność i kompletność opisu, nie zwięzłość — dokument może być dłuższy",
        "> niż typowy protokół.**",
        "",
        f"**Protokół nr {protocol_number}**",
        '**z posiedzenia Rady Nadzorczej SM „Doły-Marysińska” w Łodzi**',
        f"**z dnia {date_display} r.**",
        "",
        "**W posiedzeniu udział wzięli:**",
    ]
    lines += render_attendance(meeting_info.get("attendees", {}))
    lines.append("")

    agenda_items = facts.get("agenda_items", [])
    if agenda_items:
        lines.append("**Porządek obrad:**")
        for item in agenda_items:
            lines.append(f"{item['number']}. {item['title']}")
        lines.append("")

    lines.append("**Przebieg posiedzenia:**")
    lines.append("")
    narrative_paragraphs = facts.get("narrative_paragraphs", [])
    if narrative_paragraphs:
        for paragraph in narrative_paragraphs:
            lines.append(paragraph)
            lines.append("")
    else:
        lines.append("[DO UZUPEŁNIENIA: nie udało się wygenerować relacji z przebiegu posiedzenia]")
        lines.append("")

    lines += render_resolutions(facts.get("resolutions", []), reports_md_root, year_suffix)
    lines += render_raised_matters(facts.get("raised_matters", []))

    przewodniczacy = meeting_info.get("przewodniczacy") or "[DO UZUPEŁNIENIA]"
    protokolant = meeting_info.get("protokolant") or "[DO UZUPEŁNIENIA]"
    sekretarz = meeting_info.get("sekretarz") or "[DO UZUPEŁNIENIA]"

    lines += [
        f"Wobec wyczerpania spraw objętych porządkiem obrad, Przewodnicząca Rady Nadzorczej "
        f"{przewodniczacy} dokonała zamknięcia zebrania.",
        "",
        "PROTOKOŁOWAŁA SEKRETARZ PRZEWODNICZĄCA",
        "",
        f"*  {protokolant}                          {sekretarz}                             {przewodniczacy}*",
    ]

    return "\n".join(lines) + "\n"


def generate(clean_json_path: Path, meeting_info_path: Path, output_path: Path, reports_md_root: Path, model: str) -> None:
    turns = load_turns(clean_json_path)
    if not turns:
        raise RuntimeError("Oczyszczona transkrypcja nie zawiera wypowiedzi.")

    meeting_info = {}
    if meeting_info_path.exists():
        meeting_info = json.loads(meeting_info_path.read_text(encoding="utf-8"))
    else:
        print(f"UWAGA: brak {meeting_info_path} — lista obecności/role będą puste (patrz init_meeting_info.py).")

    print(f"Ekstrakcja relacji z przebiegu posiedzenia przez model ({model})...")
    facts = extract_facts(turns, model)
    print(
        f"Zebrano {len(facts['narrative_paragraphs'])} akapitów relacji, "
        f"{len(facts['resolutions'])} uchwał, {len(facts['raised_matters'])} spraw wniesionych."
    )

    report = render_report(meeting_info, facts, reports_md_root)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    facts_path = output_path.with_name(f"{output_path.stem}.facts.json")
    facts_path.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Zapisano projekt: {output_path}")
    print(f"Zapisano surowe fakty (do debugowania): {facts_path}")
    print("To WYŁĄCZNIE projekt — wymaga weryfikacji przez pracownika przed użyciem (Etap 5).")


def main() -> None:
    config = load_config()
    paths_cfg = config.get("paths", {})
    ollama_cfg = config.get("ollama", {})

    parser = argparse.ArgumentParser(
        description="Generuje PROJEKT sprawozdania z posiedzenia RN z oczyszczonej transkrypcji (Etap 4, wymaga weryfikacji)."
    )
    parser.add_argument("clean_transcript", type=Path, help="Ścieżka do pliku .clean.json (wynik clean_transcript.py).")
    parser.add_argument(
        "--meeting-info",
        type=Path,
        default=None,
        help="Ścieżka do <nazwa>.meeting_info.json (domyślnie obok transkrypcji).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Ścieżka wynikowa .md (domyślnie output/reports/<data>/<nazwa>.draft.md).",
    )
    parser.add_argument(
        "--reports-md-root",
        type=Path,
        default=Path(paths_cfg.get("historical_reports_md", "input/historical_data/reports_md")),
        help="Katalog historycznych protokołów .md, używany do wyliczenia kolejnego numeru uchwały.",
    )
    parser.add_argument("--model", default=ollama_cfg.get("model"), help="Nazwa modelu Ollama.")
    args = parser.parse_args()

    stem = args.clean_transcript.name.removesuffix(".clean.json")
    meeting_info_path = args.meeting_info or args.clean_transcript.with_name(f"{stem}.meeting_info.json")

    if args.output:
        output_path = args.output
    else:
        output_root = Path(paths_cfg.get("output_reports", "output/reports"))
        date_subdir = args.clean_transcript.parent.name
        output_path = output_root / date_subdir / f"{stem}.draft.md"

    generate(args.clean_transcript, meeting_info_path, output_path, args.reports_md_root, args.model)


if __name__ == "__main__":
    main()
