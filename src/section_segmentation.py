"""
Contract Section / Clause Segmentation

Reads cleaned contract text and splits it into meaningful sections/clauses.
Outputs structured JSONL records for downstream NLP, NER and risk scoring.
"""
from ftfy import fix_text
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = PROJECT_ROOT / "data" / "processed" / "cleaned_contracts"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "sections"

SECTIONS_FILE = OUTPUT_DIR / "contract_sections.jsonl"
REPORT_FILE = OUTPUT_DIR / "segmentation_report.json"


def normalize_line(line: str) -> str:
    """Normalize whitespace while preserving the original meaning."""
    return re.sub(r"\s+", " ", line).strip()


def is_heading(line: str) -> bool:
    """
    Detect likely contract section headings.
    """

    line = normalize_line(line)

    if not line:
        return False

    # Very long lines are unlikely to be headings.
    if len(line) > 120:
        return False

    # Common legal heading patterns.
    patterns = [
        r"^(ARTICLE|SECTION|PART)\s+[IVXLCDM0-9]+",
        r"^(ARTICLE|SECTION|PART)\s+[A-Z0-9]+[\s:.-]",
        r"^\d+[\.\)]\s+[A-Z]",
        r"^\d+\.\d+[\.\)]?\s+[A-Z]",
        r"^[A-Z]\.\s+[A-Z]",
        r"^WHEREAS[,:\s]",
        r"^NOW[,:\s]",
        r"^RECITALS?$",
        r"^DEFINITIONS?$",
        r"^TERMS?$",
        r"^AGREEMENT$",
        r"^INTRODUCTION$",
        r"^CONFIDENTIALITY$",
        r"^TERMINATION$",
        r"^INDEMNIFICATION$",
        r"^GOVERNING LAW$",
        r"^LIMITATION OF LIABILITY$",
        r"^REPRESENTATIONS AND WARRANTIES$",
        r"^INTELLECTUAL PROPERTY$",
        r"^LICENSE$",
        r"^PAYMENT$",
        r"^FEES?$",
        r"^NOTICES?$",
    ]

    for pattern in patterns:
        if re.match(pattern, line, re.IGNORECASE):
            return True


    return False

def repair_encoding(text: str) -> str:
    """
    Repair Unicode/mojibake artifacts produced by PDF extraction.
    """

    text = fix_text(text)

    # Handle malformed quote fragments that may remain after
    # automatic Unicode repair.
    text = text.replace("(?Chase?)", '("Chase")')
    text = text.replace("(?Affiliate?)", '("Affiliate")')

    return text


def clean_paragraph(paragraph: str) -> str:
    """Normalize and repair a paragraph."""
    paragraph = repair_encoding(paragraph)
    paragraph = paragraph.replace("\x00", "")
    paragraph = re.sub(r"\s+", " ", paragraph)
    return paragraph.strip()


def segment_contract(text: str, contract_id: str) -> list[dict]:
    """
    Split a contract into structured sections.

    Each section contains:
    - contract_id
    - section_id
    - section_title
    - text
    - character offsets
    """

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")

    sections = []
    current_title = "Preamble"
    current_lines = []
    current_start = 0
    section_counter = 1

    def flush_section(end_position: int):
        nonlocal current_lines
        nonlocal current_start
        nonlocal section_counter
        nonlocal current_title

        content = clean_paragraph("\n".join(current_lines))

        if not content:
            current_lines = []
            return

        sections.append(
            {
                "contract_id": contract_id,
                "section_id": f"{contract_id}_section_{section_counter:03d}",
                "section_number": section_counter,
                "section_title": current_title,
                "text": content,
                "char_start": current_start,
                "char_end": end_position,
                "character_count": len(content),
            }
        )

        section_counter += 1
        current_lines = []

    running_position = 0

    for line in lines:
        normalized = normalize_line(line)

        if is_heading(normalized):
            # Save the content accumulated before this heading.
            if current_lines:
                flush_section(running_position)

            current_title = normalized
            current_start = running_position

            # Keep heading as part of the section content.
            current_lines = [normalized]

        else:
            if normalized:
                current_lines.append(normalized)

        running_position += len(line) + 1

    # Save final section.
    flush_section(len(text))

    return sections


def process_contract(file_path: Path) -> tuple[list[dict], dict]:
    """Process one cleaned contract."""

    text = file_path.read_text(encoding="utf-8", errors="ignore")

    contract_id = file_path.stem

    sections = segment_contract(text, contract_id)

    report = {
        "file_name": file_path.name,
        "contract_id": contract_id,
        "original_characters": len(text),
        "sections_created": len(sections),
        "average_section_characters": (
            round(
                sum(section["character_count"] for section in sections)
                / len(sections),
                2,
            )
            if sections
            else 0
        ),
    }

    return sections, report


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    contract_files = sorted(INPUT_DIR.glob("*.txt"))

    if not contract_files:
        print(f"No cleaned contract files found in: {INPUT_DIR}")
        return

    all_sections = []
    reports = []

    for file_path in contract_files:
        print(f"Processing: {file_path.name}")

        sections, report = process_contract(file_path)

        all_sections.extend(sections)
        reports.append(report)

        print(f"  Sections created: {len(sections)}")

    with SECTIONS_FILE.open("w", encoding="utf-8") as output:
        for section in all_sections:
            output.write(json.dumps(section, ensure_ascii=False) + "\n")

    REPORT_FILE.write_text(
        json.dumps(reports, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("CONTRACT SECTION SEGMENTATION COMPLETE")
    print("=" * 60)
    print(f"Contracts processed : {len(contract_files)}")
    print(f"Total sections     : {len(all_sections)}")
    print(f"Sections output     : {SECTIONS_FILE}")
    print(f"Report output       : {REPORT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()