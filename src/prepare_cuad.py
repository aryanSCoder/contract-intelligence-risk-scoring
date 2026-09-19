import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "CUADv1.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

PARAGRAPHS_FILE = OUTPUT_DIR / "cuad_paragraphs.jsonl"
QUESTIONS_FILE = OUTPUT_DIR / "cuad_questions.jsonl"
SUMMARY_FILE = OUTPUT_DIR / "cuad_summary.json"


def make_label(question: str) -> str:
    label = question.strip().lower()
    label = re.sub(r"[^a-z0-9]+", "_", label)
    return label.strip("_")


def load_cuad() -> dict:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"CUAD file not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def process_dataset(dataset: dict) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paragraph_count = 0
    question_count = 0
    answered_count = 0
    unanswered_count = 0

    contracts = set()
    clause_counts = Counter()

    with (
        PARAGRAPHS_FILE.open("w", encoding="utf-8") as paragraph_file,
        QUESTIONS_FILE.open("w", encoding="utf-8") as question_file,
    ):
        for contract_index, document in enumerate(
            dataset.get("data", [])
        ):
            contract_title = document.get(
                "title",
                f"contract_{contract_index:04d}",
            )

            contracts.add(contract_title)

            for paragraph_index, paragraph in enumerate(
                document.get("paragraphs", [])
            ):
                context = paragraph.get("context", "")

                if not context.strip():
                    continue

                paragraph_id = (
                    f"contract_{contract_index:04d}"
                    f"_paragraph_{paragraph_index:05d}"
                )

                paragraph_record = {
                    "paragraph_id": paragraph_id,
                    "contract_id": contract_title,
                    "context": context,
                }

                paragraph_file.write(
                    json.dumps(
                        paragraph_record,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                paragraph_count += 1

                for qa_index, qa in enumerate(
                    paragraph.get("qas", [])
                ):
                    question = qa.get("question", "").strip()

                    if not question:
                        continue

                    clause_type = make_label(question)
                    answers = qa.get("answers", [])

                    question_id = (
                        f"{paragraph_id}"
                        f"_qa_{qa_index:03d}"
                    )

                    if answers:
                        for answer_index, answer in enumerate(
                            answers
                        ):
                            answer_text = answer.get(
                                "text",
                                "",
                            )

                            answer_start = answer.get(
                                "answer_start",
                                -1,
                            )

                            record = {
                                "question_id": (
                                    f"{question_id}"
                                    f"_answer_{answer_index:02d}"
                                ),
                                "paragraph_id": paragraph_id,
                                "contract_id": contract_title,
                                "clause_type": clause_type,
                                "question": question,
                                "answer_text": answer_text,
                                "answer_start": answer_start,
                                "answer_end": (
                                    answer_start
                                    + len(answer_text)
                                    if answer_start >= 0
                                    else -1
                                ),
                                "has_answer": True,
                            }

                            question_file.write(
                                json.dumps(
                                    record,
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )

                            question_count += 1
                            answered_count += 1
                            clause_counts[clause_type] += 1
                    else:
                        record = {
                            "question_id": question_id,
                            "paragraph_id": paragraph_id,
                            "contract_id": contract_title,
                            "clause_type": clause_type,
                            "question": question,
                            "answer_text": "",
                            "answer_start": -1,
                            "answer_end": -1,
                            "has_answer": False,
                        }

                        question_file.write(
                            json.dumps(
                                record,
                                ensure_ascii=False,
                            )
                            + "\n"
                        )

                        question_count += 1
                        unanswered_count += 1
                        clause_counts[clause_type] += 1

    summary = {
        "dataset": "CUAD",
        "contracts": len(contracts),
        "paragraphs": paragraph_count,
        "questions": question_count,
        "answered_questions": answered_count,
        "unanswered_questions": unanswered_count,
        "clause_categories": len(clause_counts),
        "top_clause_categories": dict(
            clause_counts.most_common(10)
        ),
    }

    with SUMMARY_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return summary


def print_summary(summary: dict) -> None:
    print()
    print("=" * 60)
    print("CUAD PREPROCESSING SUMMARY")
    print("=" * 60)
    print(f"Contracts           : {summary['contracts']}")
    print(f"Unique paragraphs   : {summary['paragraphs']}")
    print(f"Questions           : {summary['questions']}")
    print(f"Answered questions  : {summary['answered_questions']}")
    print(f"Unanswered questions: {summary['unanswered_questions']}")
    print(f"Clause categories   : {summary['clause_categories']}")
    print()
    print("Top clause categories:")

    for label, count in summary[
        "top_clause_categories"
    ].items():
        print(f"  {count:5d}  {label}")

    print()
    print(f"Paragraph file : {PARAGRAPHS_FILE}")
    print(f"Question file  : {QUESTIONS_FILE}")
    print(f"Summary file   : {SUMMARY_FILE}")
    print("=" * 60)


def main() -> None:
    print("Loading CUAD dataset...")
    dataset = load_cuad()

    print("Building normalized CUAD dataset...")
    summary = process_dataset(dataset)

    print_summary(summary)


if __name__ == "__main__":
    main()