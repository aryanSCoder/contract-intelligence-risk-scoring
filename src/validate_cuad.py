import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PARAGRAPHS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cuad_paragraphs.jsonl"
)

QUESTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cuad_questions.jsonl"
)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {path.name} at line "
                    f"{line_number}: {exc}"
                ) from exc

    return records


def validate_paragraphs(paragraphs: list[dict]) -> dict:
    errors = []

    paragraph_ids = set()
    contract_ids = set()

    for index, record in enumerate(paragraphs, start=1):
        paragraph_id = record.get("paragraph_id")
        contract_id = record.get("contract_id")
        context = record.get("context")

        if not paragraph_id:
            errors.append(
                f"Paragraph {index}: missing paragraph_id"
            )
        elif paragraph_id in paragraph_ids:
            errors.append(
                f"Duplicate paragraph_id: {paragraph_id}"
            )
        else:
            paragraph_ids.add(paragraph_id)

        if not contract_id:
            errors.append(
                f"Paragraph {index}: missing contract_id"
            )
        else:
            contract_ids.add(contract_id)

        if not isinstance(context, str) or not context.strip():
            errors.append(
                f"Paragraph {index}: empty or invalid context"
            )

    return {
        "paragraph_ids": paragraph_ids,
        "contract_ids": contract_ids,
        "errors": errors,
    }


def validate_questions(
    questions: list[dict],
    paragraph_map: dict[str, str],
) -> dict:
    errors = []

    question_ids = set()
    clause_types = set()

    answered = 0
    unanswered = 0

    for index, record in enumerate(questions, start=1):
        question_id = record.get("question_id")
        paragraph_id = record.get("paragraph_id")
        clause_type = record.get("clause_type")
        question = record.get("question")
        answer_text = record.get("answer_text", "")
        answer_start = record.get("answer_start", -1)
        answer_end = record.get("answer_end", -1)
        has_answer = record.get("has_answer")

        if not question_id:
            errors.append(
                f"Question {index}: missing question_id"
            )
        elif question_id in question_ids:
            errors.append(
                f"Duplicate question_id: {question_id}"
            )
        else:
            question_ids.add(question_id)

        if paragraph_id not in paragraph_map:
            errors.append(
                f"Question {index}: invalid paragraph_id "
                f"{paragraph_id}"
            )
            continue

        if not clause_type:
            errors.append(
                f"Question {index}: missing clause_type"
            )
        else:
            clause_types.add(clause_type)

        if not isinstance(question, str) or not question.strip():
            errors.append(
                f"Question {index}: empty question"
            )

        context = paragraph_map[paragraph_id]

        if has_answer:
            answered += 1

            if not answer_text:
                errors.append(
                    f"Question {index}: has_answer=True "
                    "but answer_text is empty"
                )

            if not isinstance(answer_start, int) or answer_start < 0:
                errors.append(
                    f"Question {index}: invalid answer_start"
                )

            if not isinstance(answer_end, int) or answer_end < 0:
                errors.append(
                    f"Question {index}: invalid answer_end"
                )

            if (
                isinstance(answer_start, int)
                and isinstance(answer_end, int)
                and answer_start >= 0
                and answer_end >= answer_start
            ):
                if answer_end > len(context):
                    errors.append(
                        f"Question {index}: answer_end exceeds "
                        "context length"
                    )
                else:
                    extracted = context[
                        answer_start:answer_end
                    ]

                    if extracted != answer_text:
                        errors.append(
                            f"Question {index}: answer text "
                            "does not match source context"
                        )

        else:
            unanswered += 1

            if answer_text:
                errors.append(
                    f"Question {index}: has_answer=False "
                    "but answer_text is not empty"
                )

            if answer_start != -1 or answer_end != -1:
                errors.append(
                    f"Question {index}: unanswered record "
                    "has answer offsets"
                )

    return {
        "question_ids": question_ids,
        "clause_types": clause_types,
        "answered": answered,
        "unanswered": unanswered,
        "errors": errors,
    }


def main() -> None:
    print("Loading processed CUAD files...")

    paragraphs = load_jsonl(PARAGRAPHS_FILE)
    questions = load_jsonl(QUESTIONS_FILE)

    print("Validating paragraphs...")

    paragraph_validation = validate_paragraphs(
        paragraphs
    )

    paragraph_map = {
        record["paragraph_id"]: record["context"]
        for record in paragraphs
        if record.get("paragraph_id")
    }

    print("Validating questions and answers...")

    question_validation = validate_questions(
        questions,
        paragraph_map,
    )

    errors = (
        paragraph_validation["errors"]
        + question_validation["errors"]
    )

    print()
    print("=" * 60)
    print("CUAD VALIDATION REPORT")
    print("=" * 60)
    print(
        f"Paragraph records : {len(paragraphs)}"
    )
    print(
        f"Question records  : {len(questions)}"
    )
    print(
        f"Contracts         : "
        f"{len(paragraph_validation['contract_ids'])}"
    )
    print(
        f"Clause categories : "
        f"{len(question_validation['clause_types'])}"
    )
    print(
        f"Answered records  : "
        f"{question_validation['answered']}"
    )
    print(
        f"Unanswered records: "
        f"{question_validation['unanswered']}"
    )
    print(
        f"Validation errors : {len(errors)}"
    )
    print("=" * 60)

    if errors:
        print()
        print("FIRST VALIDATION ERRORS:")

        for error in errors[:20]:
            print(f"- {error}")

        if len(errors) > 20:
            print(
                f"... and {len(errors) - 20} more errors."
            )

        raise SystemExit(1)

    print()
    print("✅ CUAD validation passed successfully.")


if __name__ == "__main__":
    main()