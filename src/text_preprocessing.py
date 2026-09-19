import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONTRACTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contracts"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_contracts"
)


def clean_text(text: str) -> str:
    """Normalize extracted contract text."""

    text = text.replace("\x00", " ")

    # Remove page markers such as [PAGE 1].
    text = re.sub(
        r"\[PAGE\s+\d+\]",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Remove OCR/PDF extraction placeholders.
    text = re.sub(
        r"\[(?:NO TEXT EXTRACTED|NO TEXT DETECTED BY OCR)\]",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # Normalize common whitespace issues.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove spaces before punctuation.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    return text.strip()


def process_contract(text_path: Path) -> dict:
    raw_text = text_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    cleaned_text = clean_text(raw_text)

    output_path = OUTPUT_DIR / text_path.name

    output_path.write_text(
        cleaned_text,
        encoding="utf-8",
    )

    return {
        "file_name": text_path.name,
        "original_characters": len(raw_text),
        "cleaned_characters": len(cleaned_text),
        "characters_removed": (
            len(raw_text) - len(cleaned_text)
        ),
        "output_file": str(output_path),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    text_files = sorted(
        CONTRACTS_DIR.glob("*.txt")
    )

    if not text_files:
        raise FileNotFoundError(
            f"No extracted text files found in {CONTRACTS_DIR}"
        )

    results = []

    for text_path in text_files:
        print(
            f"Cleaning: {text_path.name}"
        )

        results.append(
            process_contract(text_path)
        )

    report_path = (
        OUTPUT_DIR
        / "cleaning_report.json"
    )

    report_path.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("TEXT CLEANING REPORT")
    print("=" * 60)
    print(f"Files processed: {len(results)}")

    for result in results:
        print(
            f"Original characters : "
            f"{result['original_characters']}"
        )
        print(
            f"Cleaned characters  : "
            f"{result['cleaned_characters']}"
        )
        print(
            f"Characters removed  : "
            f"{result['characters_removed']}"
        )
        print(
            f"Output file         : "
            f"{result['output_file']}"
        )

    print(f"Report file: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()