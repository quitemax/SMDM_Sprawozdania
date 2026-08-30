"""Wycinanie krótkich próbek audio per mówca (SPEAKER_XX) z surowej
transkrypcji — żeby dało się ręcznie zidentyfikować mówcę po głosie, zamiast
polegać wyłącznie na niepewnej propozycji modelu (patrz identify_speakers.py,
docs/PROJECT_MEMORY.md).

Dla każdego SPEAKER_XX wybiera jego najdłuższe wypowiedzi (po sklejeniu
sąsiednich segmentów tego samego mówcy — ta sama logika co
clean_transcript.merge_turns) i wycina z oryginalnego pliku audio krótkie
próbki (ffmpeg). Ścieżki do próbek zapisywane są w polu "audio_samples" w
<nazwa>.speakers.json (tworzonym, jeśli jeszcze nie istnieje) — do
odsłuchania i ręcznego uzupełnienia "proposed_name".

Plik <nazwa>.speakers.json jest współdzielony z identify_speakers.py i
scalany niezależnie od kolejności uruchamiania obu skryptów — ten skrypt
nigdy nie nadpisuje już uzupełnionych pól "proposed_name"/"confidence"/
"evidence", tylko dopisuje/aktualizuje "audio_samples".
"""

import argparse
import json
import subprocess
from pathlib import Path

from clean_transcript import merge_turns
from config import load_config

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".mp4", ".aac", ".ogg", ".wma"}
DEFAULT_SAMPLES_PER_SPEAKER = 2
MIN_SAMPLE_SECONDS = 3.0
MAX_SAMPLE_SECONDS = 20.0


def find_audio_file(transcript_path: Path, audio_root: Path, output_root: Path) -> Path:
    """Odtwarza ścieżkę do oryginalnego pliku audio na podstawie tego, gdzie
    transcribe.py zapisał transkrypcję (ten sam podkatalog daty w audio_root)."""
    stem = transcript_path.stem
    try:
        relative_subdir = transcript_path.resolve().parent.relative_to(output_root.resolve())
    except ValueError:
        relative_subdir = Path(".")

    for search_dir in (audio_root / relative_subdir, audio_root):
        matches = sorted(p for p in search_dir.glob(f"{stem}.*") if p.suffix.lower() in AUDIO_EXTENSIONS)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RuntimeError(f"Znaleziono kilka plików audio pasujących do '{stem}' w {search_dir}: {matches}")

    raise RuntimeError(
        f"Nie znaleziono pliku audio dla '{stem}' (szukano w {audio_root}). Podaj ścieżkę przez --audio."
    )


def pick_samples(turns: list[dict], speaker: str, count: int) -> list[dict]:
    """Wybiera `count` najdłuższych wypowiedzi danego mówcy (min.
    MIN_SAMPLE_SECONDS) — dłuższa, ciągła wypowiedź ułatwia rozpoznanie głosu."""
    candidates = [
        t
        for t in turns
        if t["speaker"] == speaker
        and t["start"] is not None
        and t["end"] is not None
        and (t["end"] - t["start"]) >= MIN_SAMPLE_SECONDS
    ]
    candidates.sort(key=lambda t: t["end"] - t["start"], reverse=True)
    return candidates[:count]


def cut_clip(audio_path: Path, start: float, duration: float, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{start:.2f}",
            "-i", str(audio_path),
            "-t", f"{duration:.2f}",
            "-ac", "1", "-ar", "16000",
            "-codec:a", "libmp3lame", "-qscale:a", "4",
            str(output_path),
        ],
        check=True,
    )


def load_speakers_file(speakers_path: Path) -> dict[str, dict]:
    if not speakers_path.exists():
        return {}
    data = json.loads(speakers_path.read_text(encoding="utf-8"))
    return {entry["speaker_label"]: entry for entry in data.get("speakers", [])}


def extract_samples(
    transcript_path: Path,
    audio_root: Path,
    output_root: Path,
    samples_per_speaker: int,
    audio_override: Path | None,
) -> None:
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    if not segments:
        raise RuntimeError("Transkrypcja nie zawiera segmentów.")

    audio_path = audio_override or find_audio_file(transcript_path, audio_root, output_root)
    turns = merge_turns(segments)
    speaker_labels = sorted({t["speaker"] for t in turns if t.get("speaker")})

    samples_dir = transcript_path.parent / f"{transcript_path.stem}.speaker_samples"
    speakers_path = transcript_path.with_name(f"{transcript_path.stem}.speakers.json")
    existing = load_speakers_file(speakers_path)

    print(f"Źródło audio: {audio_path}")

    for speaker in speaker_labels:
        samples = pick_samples(turns, speaker, samples_per_speaker)
        sample_paths = []
        for idx, turn in enumerate(samples, start=1):
            duration = min(turn["end"] - turn["start"], MAX_SAMPLE_SECONDS)
            out_path = samples_dir / f"{speaker}_{idx:02d}.mp3"
            cut_clip(audio_path, turn["start"], duration, out_path)
            sample_paths.append(str(out_path.relative_to(transcript_path.parent)))
            print(f"  {speaker}: {out_path.name} ({duration:.1f}s)")

        if not samples:
            print(f"  {speaker}: brak wystarczająco długiej wypowiedzi (min. {MIN_SAMPLE_SECONDS:.0f}s) — brak próbki")

        entry = existing.get(
            speaker,
            {"speaker_label": speaker, "proposed_name": None, "confidence": "brak", "evidence": ""},
        )
        entry["audio_samples"] = sample_paths
        existing[speaker] = entry

    result = {"speakers": [existing[label] for label in speaker_labels]}
    speakers_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nZapisano próbki audio: {samples_dir}")
    print(f"Zaktualizowano: {speakers_path}")
    print('Odsłuchaj próbki i uzupełnij "proposed_name" ręcznie w pliku .speakers.json.')
    print('Ustaw też "source": "manual" przy ręcznie potwierdzonych — wtedy clean_transcript.py')
    print("nie oznaczy etykiety znakiem zapytania (patrz docs/PROJECT_MEMORY.md).")


def main() -> None:
    config = load_config()
    paths_cfg = config.get("paths", {})

    parser = argparse.ArgumentParser(
        description="Wycina próbki audio per mówca (SPEAKER_XX) do ręcznej identyfikacji głosu."
    )
    parser.add_argument("transcript", type=Path, help="Ścieżka do pliku .json z transkrypcją (wynik transcribe.py).")
    parser.add_argument(
        "--audio", type=Path, default=None, help="Ścieżka do oryginalnego pliku audio (domyślnie wykrywana automatycznie)."
    )
    parser.add_argument(
        "--audio-root",
        type=Path,
        default=Path(paths_cfg.get("input_audio", "input/audio")),
        help="Katalog bazowy nagrań, używany do automatycznego wykrycia pliku audio (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(paths_cfg.get("output_transcripts", "output/transcripts")),
        help="Katalog wynikowy transkrypcji, używany do automatycznego wykrycia pliku audio (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--samples-per-speaker",
        type=int,
        default=DEFAULT_SAMPLES_PER_SPEAKER,
        help=f"Liczba próbek na mówcę (domyślnie {DEFAULT_SAMPLES_PER_SPEAKER}).",
    )
    args = parser.parse_args()

    extract_samples(args.transcript, args.audio_root, args.output_root, args.samples_per_speaker, args.audio)


if __name__ == "__main__":
    main()
