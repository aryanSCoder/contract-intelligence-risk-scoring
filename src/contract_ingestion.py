import argparse
import json
from pathlib import Path

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contracts"
)


def extract_text_from_pdf(pdf_path: Path) -> tuple[str, int]:
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Input file must have a .pdf extension."
        )

    reader = PdfReader(str(pdf_path))

    pages = []
    extracted_pages = 0

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = page.extract_text() or ""
        text = text.strip()

        if text:
            extracted_pages += 1
            pages.append(
                f"[PAGE {page_number}]\n{text}"
            )
        else:
            pages.append(
                f"[PAGE {page_number}]\n"
                "[NO TEXT EXTRACTED]"
            )

    full_text = "\n\n".join(pages)

    return full_text, extracted_pages


def save_outputs(
    pdf_path: Path,
    text: str,
    page_count: int,
    extracted_pages: int,
    output_dir: Path,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    base_name = pdf_path.stem

    text_path = output_dir / f"{base_name}.txt"
    metadata_path = output_dir / f"{base_name}_metadata.json"

    text_path.write_text(
        text,
        encoding="utf-8",
    )

    metadata = {
        "file_name": pdf_path.name,
        "page_count": page_count,
        "pages_with_text": extracted_pages,
        "characters_extracted": len(text),
        "source_file": str(pdf_path),
        "status": (
            "text_extracted"
            if extracted_pages > 0
            else "ocr_required"
        ),
    }

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("PDF INGESTION REPORT")
    print("=" * 60)
    print(f"File              : {pdf_path.name}")
    print(f"Pages             : {page_count}")
    print(f"Pages with text   : {extracted_pages}")
    print(f"Characters        : {len(text)}")
    print(f"Text output       : {text_path}")
    print(f"Metadata output   : {metadata_path}")
    print(
        "Status            : "
        + (
            "TEXT EXTRACTED"
            if extracted_pages > 0
            else "OCR REQUIRED"
        )
    )
    print("=" * 60)


def process_pdf(
    pdf_path: Path,
    output_dir: Path,
) -> None:
    print(
        f"Processing PDF: {pdf_path.name}"
    )

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)

    text, extracted_pages = extract_text_from_pdf(
        pdf_path
    )

    save_outputs(
        pdf_path=pdf_path,
        text=text,
        page_count=page_count,
        extracted_pages=extracted_pages,
        output_dir=output_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract text and metadata from a contract PDF."
        )
    )

    parser.add_argument(
        "pdf",
        type=str,
        help="Path to the contract PDF",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for extracted outputs",
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    output_dir = Path(args.output_dir).resolve()

    process_pdf(
        pdf_path,
        output_dir,
    )


if __name__ == "__main__":
    main()