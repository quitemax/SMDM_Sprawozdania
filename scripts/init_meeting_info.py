"""Tworzy szablon pliku <nazwa>.meeting_info.json obok transkrypcji.

Zawiera dane, których nie da się wiarygodnie wyciągnąć z samego nagrania:
lista obecności (fizyczny załącznik — lista podpisów, nie plik cyfrowy),
kto protokołował, kto pełnił funkcję sekretarza/przewodniczącego na danym
zebraniu (funkcje rotują między spotkaniami i nie zawsze są ogłaszane wprost
w nagraniu). Do ręcznego uzupełnienia przed wygenerowaniem projektu
sprawozdania (patrz Etap 4, docs/ROADMAP.md).

Nigdy nie zgaduje wartości tych pól — to dane, które trafiają do oficjalnego
dokumentu spółdzielni, więc lepszy jest jawnie pusty szablon niż niepewna
propozycja modelu (ta sama zasada co przy identify_speakers.py, patrz
docs/PROJECT_MEMORY.md). Jedyne pole wypełniane automatycznie to "date" —
odczytywane z nazwy katalogu nadrzędnego (RRRR.MM.DD), czyli fakt znany na
pewno, a nie wywnioskowany.

Nie nadpisuje istniejącego pliku (żeby nie zgubić już uzupełnionych danych) —
użyj --force, żeby wymusić nadpisanie pustym szablonem.
"""

import argparse
import json
import re
from pathlib import Path

DATE_PATTERN = re.compile(r"(\d{4})[.\-](\d{2})[.\-](\d{2})")


def guess_date(transcript_path: Path) -> str | None:
    """Odczytuje datę spotkania z nazwy katalogu nadrzędnego (RRRR.MM.DD), jeśli pasuje."""
    match = DATE_PATTERN.search(transcript_path.parent.name)
    return "-".join(match.groups()) if match else None


def build_template(transcript_path: Path) -> dict:
    return {
        "date": guess_date(transcript_path),
        "protocol_number": None,
        "attendees": {
            "rada_nadzorcza": [],
            "zarzad": [],
            "inni": [],
        },
        "protokolant": None,
        "sekretarz": None,
        "przewodniczacy": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tworzy szablon <nazwa>.meeting_info.json do ręcznego uzupełnienia."
    )
    parser.add_argument("transcript", type=Path, help="Ścieżka do pliku .json z transkrypcją (wynik transcribe.py).")
    parser.add_argument("--force", action="store_true", help="Nadpisz istniejący plik pustym szablonem.")
    args = parser.parse_args()

    output_path = args.transcript.with_name(f"{args.transcript.stem}.meeting_info.json")
    if output_path.exists() and not args.force:
        print(f"Plik już istnieje, pomijam (użyj --force, żeby nadpisać): {output_path}")
        return

    template = build_template(args.transcript)
    output_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Utworzono szablon: {output_path}")
    print("Uzupełnij ręcznie: listę obecności, protokolanta, sekretarza i przewodniczącego zebrania.")


if __name__ == "__main__":
    main()
