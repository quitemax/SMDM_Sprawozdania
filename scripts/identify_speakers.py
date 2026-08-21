"""Propozycja mapowania SPEAKER_XX -> imię i nazwisko na podstawie treści transkrypcji.

Szuka w transkrypcji fragmentów, gdzie ktoś się przedstawia lub zwraca do kogoś
po imieniu/nazwisku (np. "Panie Leonie"), i prosi lokalny model językowy
(Ollama) o wywnioskowanie, kim jest dany mówca. Wynik to WYŁĄCZNIE propozycja
do ręcznej weryfikacji przez pracownika (patrz docs/ROADMAP.md, Etap 5) —
transkrypcja nie jest automatycznie modyfikowana.
"""

import argparse
import json
import re
from pathlib import Path

import requests

from config import load_config

OLLAMA_URL = "http://localhost:11434/api/generate"

# Zwroty wskazujące, że w tym miejscu może paść czyjeś imię/nazwisko:
# przedstawianie się oraz zwroty grzecznościowe kierowane do konkretnej osoby.
NAME_CUE_PATTERN = re.compile(
    r"\b(nazywam się|tu mówi|"
    r"panie|pani|panu|panią|panowie)\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+",
    re.IGNORECASE,
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "speakers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "speaker_label": {"type": "string"},
                    "proposed_name": {"type": ["string", "null"]},
                    "confidence": {"type": "string", "enum": ["wysoka", "średnia", "niska", "brak"]},
                    "evidence": {"type": "string"},
                },
                "required": ["speaker_label", "proposed_name", "confidence", "evidence"],
            },
        }
    },
    "required": ["speakers"],
}

PROMPT_TEMPLATE = """\
Poniżej znajdują się fragmenty transkrypcji spotkania spółdzielni mieszkaniowej
z oznaczonymi mówcami (SPEAKER_XX). Fragmenty wybrano, bo w ich okolicy ktoś
mógł się przedstawić albo zwrócić do kogoś po imieniu/nazwisku.

Na tej podstawie oceń, kim może być każdy z mówców: {speaker_labels}.

Zasady:
- Jeśli mówca X zwraca się do "Panie Leonie" i zaraz po nim odpowiada inny
  mówca Y, to prawdopodobnie Y to Leon (ale nie zawsze — oceń ostrożnie).
- UWAGA: mówca, który wspomina czyjeś imię/nazwisko lub przekazuje od kogoś
  wiadomość (np. "dzwoniła Pani Ewa, kazała przeprosić") NIE JEST tą osobą —
  to co innego niż zwrócenie się do kogoś obecnego, kto zaraz odpowiada.
  Nie myl tych dwóch sytuacji.
- Jeśli nie ma wystarczających poszlak dla któregoś mówcy, podaj
  proposed_name: null i confidence: "brak". Jeśli confidence to "brak",
  proposed_name musi być null (nie podawaj samego tytułu grzecznościowego
  typu "Pani"/"Pan" bez nazwiska).
- Zwróć wynik dla WSZYSTKICH wymienionych mówców, nawet jeśli confidence to
  "brak".
- W polu evidence krótko uzasadnij (po polsku), na podstawie którego
  fragmentu wnioskujesz.

Fragmenty transkrypcji (numer segmentu, mówca, tekst):
{excerpts}
"""


def build_excerpts(segments: list[dict], context: int = 1, max_chars: int = 6000) -> str:
    """Wybiera segmenty w pobliżu zwrotów mogących zawierać imię/nazwisko."""
    match_indices = {
        idx for idx, seg in enumerate(segments) if NAME_CUE_PATTERN.search(seg.get("text", ""))
    }

    include_indices: set[int] = set()
    for idx in match_indices:
        for offset in range(-context, context + 1):
            neighbor = idx + offset
            if 0 <= neighbor < len(segments):
                include_indices.add(neighbor)

    lines = []
    total_chars = 0
    for idx in sorted(include_indices):
        seg = segments[idx]
        line = f"[{idx}] {seg.get('speaker', '?')}: {seg.get('text', '').strip()}"
        if total_chars + len(line) > max_chars:
            break
        lines.append(line)
        total_chars += len(line)

    return "\n".join(lines)


def identify_speakers(transcript_path: Path, model: str) -> dict:
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    segments = data.get("segments", [])

    speaker_labels = sorted({seg.get("speaker", "?") for seg in segments if seg.get("speaker")})
    excerpts = build_excerpts(segments)

    if not excerpts:
        return {
            "speakers": [
                {
                    "speaker_label": label,
                    "proposed_name": None,
                    "confidence": "brak",
                    "evidence": "Nie znaleziono fragmentów sugerujących imię/nazwisko w transkrypcie.",
                }
                for label in speaker_labels
            ]
        }

    prompt = PROMPT_TEMPLATE.format(speaker_labels=", ".join(speaker_labels), excerpts=excerpts)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "format": RESPONSE_SCHEMA,
            "stream": False,
            "options": {"num_ctx": 8192, "temperature": 0.1},
        },
        timeout=600,
    )
    response.raise_for_status()
    result = json.loads(response.json()["response"])

    # Model czasem zwraca dosłowny string "null" zamiast wartości JSON null.
    for speaker in result.get("speakers", []):
        if isinstance(speaker.get("proposed_name"), str) and speaker["proposed_name"].strip().lower() == "null":
            speaker["proposed_name"] = None

    return result


def main() -> None:
    config = load_config()
    ollama_cfg = config.get("ollama", {})

    parser = argparse.ArgumentParser(
        description="Propozycja mapowania SPEAKER_XX -> imię i nazwisko (do ręcznej weryfikacji)."
    )
    parser.add_argument("transcript", type=Path, help="Ścieżka do pliku .json z transkrypcją (wynik transcribe.py).")
    parser.add_argument("--model", default=ollama_cfg.get("model"), help="Nazwa modelu Ollama.")
    args = parser.parse_args()

    result = identify_speakers(args.transcript, args.model)

    output_path = args.transcript.with_suffix("").with_suffix(".speakers.json")
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Zapisano propozycję: {output_path}")
    print("Wymaga ręcznej weryfikacji (patrz docs/ROADMAP.md, Etap 5) przed użyciem w raporcie.")
    for speaker in result.get("speakers", []):
        print(f"  {speaker['speaker_label']}: {speaker['proposed_name']} ({speaker['confidence']})")


if __name__ == "__main__":
    main()
