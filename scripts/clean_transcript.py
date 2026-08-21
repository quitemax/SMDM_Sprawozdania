"""Czyszczenie transkrypcji: sklejanie wypowiedzi tego samego mówcy w jedną
turę oraz usuwanie segmentów będących wyłącznie wypełniaczem (np. "yyy").

Nie poprawia błędów rozpoznawania w środku zdań — bez pełnej analizy
językowej ryzyko zniekształcenia sensu wypowiedzi jest zbyt duże.
"""

import argparse
import json
import re
from pathlib import Path

FILLER_ONLY_PATTERN = re.compile(r"^(yy+|ee+|y|e|mhm+|aha+|hm+|no)[.,!?]?$", re.IGNORECASE)

# Segmenty tego samego mówcy oddalone o mniej niż tyle sekund sklejane są w jedną turę.
MAX_GAP_SECONDS = 2.0


def is_filler_only(text: str) -> bool:
    return bool(FILLER_ONLY_PATTERN.match(text.strip()))


def merge_turns(segments: list[dict]) -> list[dict]:
    turns: list[dict] = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text or is_filler_only(text):
            continue

        speaker = seg.get("speaker", "?")
        start = seg.get("start")
        end = seg.get("end")

        previous = turns[-1] if turns else None
        can_merge = (
            previous is not None
            and previous["speaker"] == speaker
            and start is not None
            and previous["end"] is not None
            and start - previous["end"] <= MAX_GAP_SECONDS
        )
        if can_merge:
            previous["text"] += " " + text
            previous["end"] = end
        else:
            turns.append({"speaker": speaker, "start": start, "end": end, "text": text})
    return turns


def format_timestamp(seconds) -> str:
    if seconds is None:
        return "?"
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def clean(transcript_path: Path) -> None:
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    turns = merge_turns(segments)

    output_dir = transcript_path.parent
    stem = transcript_path.stem

    json_path = output_dir / f"{stem}.clean.json"
    json_path.write_text(json.dumps({"turns": turns}, ensure_ascii=False, indent=2), encoding="utf-8")

    txt_path = output_dir / f"{stem}.clean.txt"
    lines = [f"[{format_timestamp(turn['start'])}] {turn['speaker']}: {turn['text']}" for turn in turns]
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wypowiedzi po sklejeniu: {len(turns)} (z {len(segments)} segmentów)")
    print(f"Zapisano: {txt_path}")
    print(f"Zapisano: {json_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Czyszczenie transkrypcji: sklejanie wypowiedzi tego samego mówcy, usuwanie wypełniaczy."
    )
    parser.add_argument("transcript", type=Path, help="Ścieżka do pliku .json z transkrypcją (wynik transcribe.py).")
    args = parser.parse_args()
    clean(args.transcript)


if __name__ == "__main__":
    main()
