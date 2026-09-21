import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LABEL_FILE = ROOT / "data" / "processed" / "cuad_clause_labels.jsonl"
PARAGRAPH_FILE = ROOT / "data" / "processed" / "cuad_paragraphs.jsonl"

OUTPUT_DIR = ROOT / "data" / "processed" / "ner"
TRAIN_FILE = OUTPUT_DIR / "train.jsonl"
VALID_FILE = OUTPUT_DIR / "valid.jsonl"
SUMMARY_FILE = OUTPUT_DIR / "ner_dataset_summary.json"

RANDOM_SEED = 42
VALIDATION_RATIO = 0.2


def load_paragraphs():
    paragraphs = {}

    with PARAGRAPH_FILE.open("r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue

            record = json.loads(line)

            paragraph_id = record.get("paragraph_id")

            if paragraph_id:
                paragraphs[paragraph_id] = record

    return paragraphs


def get_paragraph_id(question_id):
    """
    Example:
    contract_0000_paragraph_00000_qa_000_answer_00

    -> contract_0000_paragraph_00000
    """

    marker = "_qa_"

    if marker not in question_id:
        return None

    return question_id.split(marker)[0]


def load_answered_records():
    records = []

    with LABEL_FILE.open("r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue

            record = json.loads(line)

            if not record.get("is_answered"):
                continue

            if not record.get("answer_text"):
                continue

            if record.get("answer_start") is None:
                continue

            if record.get("answer_end") is None:
                continue

            if not record.get("clause_type"):
                continue

            records.append(record)

    return records


def build_ner_record(record, paragraphs):
    question_id = record["question_id"]

    paragraph_id = get_paragraph_id(question_id)

    if not paragraph_id:
        return None

    paragraph = paragraphs.get(paragraph_id)

    if not paragraph:
        return None

    text = paragraph.get("context", "")

    if not text:
        return None

    start = int(record["answer_start"])
    end = int(record["answer_end"])

    if start < 0 or end > len(text) or start >= end:
        return None

    answer_text = record["answer_text"]

    extracted_text = text[start:end]

    if extracted_text != answer_text:
        return None

    return {
        "text": text,
        "entities": [
            {
                "start": start,
                "end": end,
                "label": record["clause_type"],
            }
        ],
        "contract_id": record["contract_id"],
        "paragraph_id": paragraph_id,
        "question_id": question_id,
    }


def main():
    if not LABEL_FILE.exists():
        raise FileNotFoundError(f"Label file not found: {LABEL_FILE}")

    if not PARAGRAPH_FILE.exists():
        raise FileNotFoundError(
            f"Paragraph file not found: {PARAGRAPH_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading CUAD paragraphs...")
    paragraphs = load_paragraphs()

    print(f"Paragraphs loaded : {len(paragraphs)}")

    print("Loading answered CUAD records...")
    records = load_answered_records()

    print(f"Answered records  : {len(records)}")

    random.seed(RANDOM_SEED)
    random.shuffle(records)

    train_size = int(len(records) * (1 - VALIDATION_RATIO))

    train_records = records[:train_size]
    valid_records = records[train_size:]

    train_examples = []
    valid_examples = []

    skipped = 0
    label_counts = Counter()

    for record in train_records:
        example = build_ner_record(record, paragraphs)

        if example is None:
            skipped += 1
            continue

        train_examples.append(example)

        for entity in example["entities"]:
            label_counts[entity["label"]] += 1

    for record in valid_records:
        example = build_ner_record(record, paragraphs)

        if example is None:
            skipped += 1
            continue

        valid_examples.append(example)

    with TRAIN_FILE.open("w", encoding="utf-8") as outfile:
        for example in train_examples:
            outfile.write(
                json.dumps(example, ensure_ascii=False) + "\n"
            )

    with VALID_FILE.open("w", encoding="utf-8") as outfile:
        for example in valid_examples:
            outfile.write(
                json.dumps(example, ensure_ascii=False) + "\n"
            )

    labels = sorted(
        {
            entity["label"]
            for example in train_examples + valid_examples
            for entity in example["entities"]
        }
    )

    summary = {
        "source_answered_records": len(records),
        "paragraph_records": len(paragraphs),
        "train_examples": len(train_examples),
        "validation_examples": len(valid_examples),
        "skipped_records": skipped,
        "validation_ratio": VALIDATION_RATIO,
        "random_seed": RANDOM_SEED,
        "entity_label_count": len(labels),
        "entity_labels": labels,
        "training_label_counts": dict(
            sorted(label_counts.items())
        ),
    }

    SUMMARY_FILE.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8",
    )

    print()
    print(f"Training examples     : {len(train_examples)}")
    print(f"Validation examples   : {len(valid_examples)}")
    print(f"Skipped records       : {skipped}")
    print(f"NER labels            : {len(labels)}")
    print(f"Training output       : {TRAIN_FILE}")
    print(f"Validation output     : {VALID_FILE}")
    print(f"Summary output        : {SUMMARY_FILE}")

    print("\nNER labels:")
    for label in labels:
        print(f"  {label}")

    print("\nTop training labels:")

    for label, count in label_counts.most_common(15):
        print(f"  {label}: {count}")

    print("\n✅ NER dataset generation completed successfully.")


if __name__ == "__main__":
    main()