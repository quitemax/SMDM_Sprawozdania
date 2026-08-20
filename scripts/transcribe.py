"""Transkrypcja nagrania audio przy użyciu WhisperX (bez diaryzacji)."""

import argparse
import json
import logging
import warnings
from pathlib import Path

# Nieszkodliwe ostrzeżenia z pyannote.audio (używanego wewnętrznie przez WhisperX do VAD):
# - brak torchcodec/FFmpeg pod Windows — WhisperX i tak przekazuje audio już wczytane
#   do pamięci, więc ścieżka dekodowania przez torchcodec nigdy nie jest używana,
# - wyłączenie TF32 — świadoma decyzja pyannote na rzecz powtarzalności wyników.
# Trzeba to zweryfikować ponownie przy wdrażaniu diaryzacji (docs/ROADMAP.md, Etap 1).
warnings.filterwarnings("ignore", message=r"\ntorchcodec is not installed correctly.*", category=UserWarning)
warnings.filterwarnings("ignore", message=r".*TensorFloat-32.*", category=UserWarning)

# Informacja (nie ostrzeżenie) o automatycznym, tymczasowym upgrade'zie checkpointu
# WhisperX/pyannote przy każdym uruchomieniu. Trwały upgrade pliku wymagałby wyłączenia
# `weights_only` w torch.load (ryzyko bezpieczeństwa), więc zamiast tego wyciszamy log.
logging.getLogger("lightning.pytorch.utilities.migration.utils").setLevel(logging.WARNING)

import torch
import whisperx


def resolve_output_dir(audio_path: Path, output_root: Path, input_root: Path) -> Path:
    """Odzwierciedla podkatalog nagrania (np. datę spotkania) w katalogu wynikowym."""
    try:
        relative_subdir = audio_path.resolve().relative_to(input_root.resolve()).parent
    except ValueError:
        relative_subdir = Path(".")
    return output_root / relative_subdir


def transcribe(
    audio_path: Path,
    output_root: Path,
    input_root: Path,
    model_name: str,
    language: str,
    batch_size: int,
) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    model = whisperx.load_model(model_name, device, compute_type=compute_type, language=language)
    audio = whisperx.load_audio(str(audio_path))
    result = model.transcribe(audio, batch_size=batch_size)

    align_model, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], align_model, metadata, audio, device, return_char_alignments=False)

    output_dir = resolve_output_dir(audio_path, output_root, input_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = audio_path.stem

    json_path = output_dir / f"{stem}.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    txt_path = output_dir / f"{stem}.txt"
    lines = [segment["text"].strip() for segment in result["segments"]]
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Segmentów: {len(result['segments'])}")
    print(f"Zapisano: {txt_path}")
    print(f"Zapisano: {json_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Transkrypcja nagrania audio przy użyciu WhisperX.")
    parser.add_argument("audio", type=Path, help="Ścieżka do pliku audio.")
    parser.add_argument("--model", default="large-v3", help="Nazwa modelu Whisper (domyślnie: large-v3).")
    parser.add_argument("--language", default="pl", help="Kod języka nagrania (domyślnie: pl).")
    parser.add_argument("--batch-size", type=int, default=16, help="Rozmiar batcha (domyślnie: 16).")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/transcripts"),
        help="Katalog wynikowy (domyślnie: output/transcripts).",
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("input/audio"),
        help="Katalog bazowy nagrań, względem którego odtwarzana jest struktura podkatalogów w output-dir (domyślnie: input/audio).",
    )
    args = parser.parse_args()

    transcribe(args.audio, args.output_dir, args.input_root, args.model, args.language, args.batch_size)


if __name__ == "__main__":
    main()
