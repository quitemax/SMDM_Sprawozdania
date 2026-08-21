"""Transkrypcja nagrania audio przy użyciu WhisperX, z diaryzacją (rozpoznawaniem mówców)."""

import argparse
import json
import logging
import os
import warnings
from pathlib import Path

# Nieszkodliwe ostrzeżenia z pyannote.audio (używanego wewnętrznie przez WhisperX do VAD
# i diaryzacji), potwierdzone jako niegroźne również przy realnym użyciu diaryzacji:
# - brak torchcodec/FFmpeg pod Windows — WhisperX i tak przekazuje audio już wczytane
#   do pamięci, więc ścieżka dekodowania przez torchcodec nigdy nie jest używana,
# - wyłączenie TF32 — świadoma decyzja pyannote na rzecz powtarzalności wyników.
warnings.filterwarnings("ignore", message=r"\ntorchcodec is not installed correctly.*", category=UserWarning)
warnings.filterwarnings("ignore", message=r".*TensorFloat-32.*", category=UserWarning)

# Informacja (nie ostrzeżenie) o automatycznym, tymczasowym upgrade'zie checkpointu
# WhisperX/pyannote przy każdym uruchomieniu. Trwały upgrade pliku wymagałby wyłączenia
# `weights_only` w torch.load (ryzyko bezpieczeństwa), więc zamiast tego wyciszamy log.
logging.getLogger("lightning.pytorch.utilities.migration.utils").setLevel(logging.WARNING)

import torch
import whisperx
from whisperx.diarize import DiarizationPipeline

from config import load_config


def print_progress(stage: str):
    """Zwraca progress_callback wypisujący procent postępu danego etapu w jednej linii."""

    def callback(percent: float) -> None:
        end = "\n" if percent >= 100 else ""
        print(f"\r{stage}: {percent:5.1f}%{end}", end="", flush=True)

    return callback


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
    diarize: bool,
    min_speakers: int | None,
    max_speakers: int | None,
) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    model = whisperx.load_model(model_name, device, compute_type=compute_type, language=language)
    audio = whisperx.load_audio(str(audio_path))
    result = model.transcribe(audio, batch_size=batch_size, progress_callback=print_progress("Transkrypcja"))

    align_model, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(
        result["segments"],
        align_model,
        metadata,
        audio,
        device,
        return_char_alignments=False,
        progress_callback=print_progress("Wyrównanie"),
    )

    if diarize:
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            raise RuntimeError(
                "Diaryzacja wymaga tokena Hugging Face w zmiennej środowiskowej HF_TOKEN "
                "(patrz docs/INSTALLATION.md, sekcja o tokenie i dostępie do modeli pyannote). "
                "Użyj --no-diarize, żeby zrobić transkrypcję bez rozpoznawania mówców."
            )
        diarize_model = DiarizationPipeline(token=hf_token, device=device)
        diarize_segments = diarize_model(
            audio,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
            progress_callback=print_progress("Diaryzacja"),
        )
        result = whisperx.assign_word_speakers(diarize_segments, result)

    output_dir = resolve_output_dir(audio_path, output_root, input_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = audio_path.stem

    json_path = output_dir / f"{stem}.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    txt_path = output_dir / f"{stem}.txt"
    if diarize:
        lines = [f"[{segment.get('speaker', '?')}] {segment['text'].strip()}" for segment in result["segments"]]
    else:
        lines = [segment["text"].strip() for segment in result["segments"]]
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Segmentów: {len(result['segments'])}")
    print(f"Zapisano: {txt_path}")
    print(f"Zapisano: {json_path}")


def main() -> None:
    config = load_config()
    whisperx_cfg = config.get("whisperx", {})
    paths_cfg = config.get("paths", {})

    parser = argparse.ArgumentParser(description="Transkrypcja nagrania audio przy użyciu WhisperX.")
    parser.add_argument("audio", type=Path, help="Ścieżka do pliku audio.")
    parser.add_argument(
        "--model",
        default=whisperx_cfg.get("model", "large-v3"),
        help="Nazwa modelu Whisper (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--language",
        default=whisperx_cfg.get("language", "pl"),
        help="Kod języka nagrania (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=whisperx_cfg.get("batch_size", 16),
        help="Rozmiar batcha (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(paths_cfg.get("output_transcripts", "output/transcripts")),
        help="Katalog wynikowy (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path(paths_cfg.get("input_audio", "input/audio")),
        help="Katalog bazowy nagrań, względem którego odtwarzana jest struktura podkatalogów w output-dir (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--diarize",
        dest="diarize",
        action="store_true",
        default=whisperx_cfg.get("diarize", True),
        help="Rozpoznawanie mówców (domyślnie z config/config.yaml). Wymaga zmiennej środowiskowej HF_TOKEN.",
    )
    parser.add_argument(
        "--no-diarize",
        dest="diarize",
        action="store_false",
        help="Wyłącz rozpoznawanie mówców (transkrypcja bez etykiet mówców, bez tokena HF).",
    )
    parser.add_argument("--min-speakers", type=int, default=None, help="Minimalna liczba mówców (opcjonalnie).")
    parser.add_argument("--max-speakers", type=int, default=None, help="Maksymalna liczba mówców (opcjonalnie).")
    args = parser.parse_args()

    transcribe(
        args.audio,
        args.output_dir,
        args.input_root,
        args.model,
        args.language,
        args.batch_size,
        args.diarize,
        args.min_speakers,
        args.max_speakers,
    )


if __name__ == "__main__":
    main()
