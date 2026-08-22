"""Konwersja PDF-ów z input/knowledge/ na pliki Markdown (input/knowledge_md/).

Dla każdej strony najpierw próbuje wyciągnąć bezpośredni tekst z PDF-a;
jeśli strona nie ma warstwy tekstowej (skan), robi OCR (Tesseract, pol)
na wyrenderowanym obrazie strony. Dokumenty (w całości lub częściowo)
rozpoznane przez OCR są oznaczone notką na początku pliku — OCR bywa
niedokładny, zwłaszcza przy podpisach i pieczątkach, więc wymaga
weryfikacji przed użyciem w audycie lub sprawozdaniu.
"""

import argparse
import io
import re
import shutil
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

from config import load_config

MIN_DIRECT_TEXT_CHARS = 20
OCR_DPI = 300
OCR_LANG = "pol"

DEFAULT_TESSERACT_PATH = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

OCR_NOTE = (
    "> **Uwaga:** ten dokument (w całości lub częściowo) został rozpoznany "
    "automatycznie z zeskanowanego obrazu (OCR). OCR bywa niedokładny, zwłaszcza "
    "przy podpisach, pieczątkach i tabelach — przed użyciem w audycie lub "
    "sprawozdaniu zweryfikuj kluczowe dane (daty, kwoty, nazwiska, numery uchwał)."
)


def resolve_tesseract_cmd() -> str:
    found = shutil.which("tesseract")
    if found:
        return found
    if DEFAULT_TESSERACT_PATH.exists():
        return str(DEFAULT_TESSERACT_PATH)
    raise RuntimeError(
        "Nie znaleziono tesseract.exe. Zainstaluj Tesseract OCR — patrz docs/INSTALLATION.md."
    )


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_page(page: "pymupdf.Page") -> tuple[str, bool]:
    """Zwraca (tekst, czy_użyto_ocr)."""
    direct = page.get_text().strip()
    if len(direct) >= MIN_DIRECT_TEXT_CHARS:
        return clean_text(direct), False

    pix = page.get_pixmap(dpi=OCR_DPI)
    image = Image.open(io.BytesIO(pix.tobytes("png")))
    ocr_text = pytesseract.image_to_string(image, lang=OCR_LANG)
    return clean_text(ocr_text), True


def convert_pdf(pdf_path: Path, output_path: Path) -> None:
    doc = pymupdf.open(pdf_path)
    pages: list[str] = []
    any_ocr = False

    for idx, page in enumerate(doc):
        text, used_ocr = extract_page(page)
        any_ocr = any_ocr or used_ocr
        print(f"  strona {idx + 1}/{doc.page_count} ({'OCR' if used_ocr else 'tekst'})")
        pages.append(text)

    lines = [f"# {pdf_path.stem}", ""]
    if any_ocr:
        lines += [OCR_NOTE, ""]

    if len(pages) > 1:
        for idx, text in enumerate(pages):
            lines += [f"## Strona {idx + 1}", "", text, ""]
    else:
        lines += [pages[0] if pages else "", ""]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def find_pdfs(input_root: Path) -> list[Path]:
    return sorted(input_root.rglob("*.pdf"))


def main() -> None:
    config = load_config()
    paths_cfg = config.get("paths", {})

    parser = argparse.ArgumentParser(description="Konwersja PDF-ów z input/knowledge/ na Markdown (z OCR dla skanów).")
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path(paths_cfg.get("input_knowledge", "input/knowledge")),
        help="Katalog z PDF-ami (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(paths_cfg.get("knowledge_md", "input/knowledge_md")),
        help="Katalog wynikowy na pliki .md (domyślnie z config/config.yaml).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Przetwórz ponownie nawet pliki, dla których .md jest nowszy niż źródłowy .pdf.",
    )
    args = parser.parse_args()

    pytesseract.pytesseract.tesseract_cmd = resolve_tesseract_cmd()

    pdf_paths = find_pdfs(args.input_root)
    print(f"Znaleziono {len(pdf_paths)} plików PDF w {args.input_root}")

    converted = 0
    skipped = 0
    for pdf_path in pdf_paths:
        relative = pdf_path.relative_to(args.input_root)
        output_path = (args.output_root / relative).with_suffix(".md")

        if not args.force and output_path.exists() and output_path.stat().st_mtime >= pdf_path.stat().st_mtime:
            skipped += 1
            continue

        print(f"{relative}")
        convert_pdf(pdf_path, output_path)
        converted += 1

    print(f"\nPrzekonwertowano: {converted}, pominięto (aktualne): {skipped}")


if __name__ == "__main__":
    main()
