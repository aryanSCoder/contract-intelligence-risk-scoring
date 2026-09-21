import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data" / "processed" / "cuad_questions.jsonl"
OUTPUT_FILE = ROOT / "data" / "processed" / "cuad_clause_labels.jsonl"
SUMMARY_FILE = ROOT / "data" / "processed" / "cuad_clause_labels_summary.json"


def extract_clause_type(question: str) -> str:
    """
    Extract the short clause/category name from a CUAD question.
    """

    question = question.strip()

    # CUAD questions commonly contain the clause name in quotation marks.
    patterns = [
        r'"([^"]+)"',
        r"“([^”]+)”",
        r"'([^']+)'",
    ]

    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            value = match.group(1).strip()
            if 2 <= len(value) <= 100:
                return value

    # Fallback cleanup if no quoted category is found.
    cleaned = re.sub(
        r"^(highlight|find|identify|extract|list|provide|locate)\s+",
        "",
        question,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"^(the\s+)?parts?\s+(of|that|which)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    return cleaned.strip(" .:;?")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    category_counts = Counter()
    answered_counts = Counter()

    total_records = 0
    answered_records = 0

    with INPUT_FILE.open("r", encoding="utf-8") as infile, \
            OUTPUT_FILE.open("w", encoding="utf-8") as outfile:

        for line in infile:
            if not line.strip():
                continue

            record = json.loads(line)

            question = record.get("question", "")
            clause_type = extract_clause_type(question)

            normalized = {
                "contract_id": record.get("contract_id"),
                "question_id": record.get("question_id"),
                "question": question,
                "clause_type": clause_type,
                "answer_text": record.get("answer_text"),
                "answer_start": record.get("answer_start"),
                "answer_end": record.get("answer_end"),
                "is_answered": bool(
                    record.get("answer_text")
                    and str(record.get("answer_text")).strip()
                ),
            }

            outfile.write(
                json.dumps(normalized, ensure_ascii=False) + "\n"
            )

            total_records += 1
            category_counts[clause_type] += 1

            if normalized["is_answered"]:
                answered_records += 1
                answered_counts[clause_type] += 1

    summary = {
        "total_questions": total_records,
        "answered_questions": answered_records,
        "unanswered_questions": total_records - answered_records,
        "unique_clause_categories": len(category_counts),
        "clause_categories": [
            {
                "clause_type": category,
                "total": count,
                "answered": answered_counts.get(category, 0),
                "unanswered": count - answered_counts.get(category, 0),
            }
            for category, count in sorted(category_counts.items())
        ],
    }

    SUMMARY_FILE.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Questions processed       : {total_records}")
    print(f"Answered questions        : {answered_records}")
    print(f"Unanswered questions      : {total_records - answered_records}")
    print(f"Unique clause categories  : {len(category_counts)}")
    print(f"Labels output             : {OUTPUT_FILE}")
    print(f"Summary output            : {SUMMARY_FILE}")

    print("\nClause categories:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")

    print("\n✅ CUAD clause-label normalization completed successfully.")


if __name__ == "__main__":
    main()