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


def extract_text_from_pdf(pdf_path: Path) -> tuple[str, int, int]:
    """
    Extract text using pypdf.

    Returns:
        full_text,
        total_pages,
        pages_with_text
    """

    reader = PdfReader(str(pdf_path))

    pages = []
    pages_with_text = 0

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = page.extract_text() or ""
        text = text.strip()

        if text:
            pages_with_text += 1
            pages.append(
                f"[PAGE {page_number}]\n{text}"
            )
        else:
            pages.append(
                f"[PAGE {page_number}]\n"
                "[NO TEXT EXTRACTED]"
            )

    full_text = "\n\n".join(pages)

    return (
        full_text,
        len(reader.pages),
        pages_with_text,
    )


def extract_text_with_ocr(pdf_path: Path) -> tuple[str, int]:
    """
    OCR fallback for scanned/image-only PDFs.

    Requires:
        pdf2image
        pytesseract
        Poppler
        Tesseract OCR
    """

    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies are missing. Install "
            "pdf2image and pytesseract."
        ) from exc

    try:
        images = convert_from_path(
            str(pdf_path),
            dpi=200,
        )
    except Exception as exc:
        raise RuntimeError(
            "PDF-to-image conversion failed. "
            "Make sure Poppler is installed and "
            "available on PATH."
        ) from exc

    pages = []

    for page_number, image in enumerate(
        images,
        start=1,
    ):
        text = pytesseract.image_to_string(
            image
        ).strip()

        if text:
            pages.append(
                f"[PAGE {page_number}]\n{text}"
            )
        else:
            pages.append(
                f"[PAGE {page_number}]\n"
                "[NO TEXT DETECTED BY OCR]"
            )

    return (
        "\n\n".join(pages),
        len(images),
    )


def save_outputs(
    pdf_path: Path,
    text: str,
    page_count: int,
    extracted_pages: int,
    extraction_method: str,
    output_dir: Path,
) -> None:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    base_name = pdf_path.stem

    text_path = (
        output_dir
        / f"{base_name}.txt"
    )

    metadata_path = (
        output_dir
        / f"{base_name}_metadata.json"
    )

    text_path.write_text(
        text,
        encoding="utf-8",
    )

    metadata = {
        "file_name": pdf_path.name,
        "page_count": page_count,
        "pages_with_text": extracted_pages,
        "characters_extracted": len(text),
        "extraction_method": extraction_method,
        "source_file": str(pdf_path),
        "status": (
            "text_extracted"
            if extraction_method == "pypdf"
            else "ocr_extracted"
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
    print(
        f"Extraction method : {extraction_method}"
    )
    print(f"Text output       : {text_path}")
    print(f"Metadata output   : {metadata_path}")
    print(
        "Status            : "
        + (
            "TEXT EXTRACTED"
            if extraction_method == "pypdf"
            else "OCR EXTRACTED"
        )
    )
    print("=" * 60)


def process_pdf(
    pdf_path: Path,
    output_dir: Path,
) -> None:

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Input file must have a .pdf extension."
        )

    print(
        f"Processing PDF: {pdf_path.name}"
    )

    text, page_count, pages_with_text = (
        extract_text_from_pdf(pdf_path)
    )

    extraction_method = "pypdf"

    # If no pages contain extractable text,
    # use OCR as a fallback.
    if pages_with_text == 0:
        print(
            "No extractable text detected."
        )
        print(
            "Switching to OCR fallback..."
        )

        text, page_count = (
            extract_text_with_ocr(pdf_path)
        )

        extracted_pages = sum(
            1
            for page in text.split("\n\n")
            if "[PAGE " in page
            and "[NO TEXT DETECTED BY OCR]"
            not in page
        )

        extraction_method = "ocr"

    else:
        extracted_pages = pages_with_text

    save_outputs(
        pdf_path=pdf_path,
        text=text,
        page_count=page_count,
        extracted_pages=extracted_pages,
        extraction_method=extraction_method,
        output_dir=output_dir,
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Extract contract text from PDF "
            "with OCR fallback."
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
    output_dir = Path(
        args.output_dir
    ).resolve()

    process_pdf(
        pdf_path,
        output_dir,
    )


if __name__ == "__main__":
    main()