import json
from pathlib import Path
from collections import Counter

import spacy


BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_FILE = BASE_DIR / "data" / "processed" / "ner" / "train.jsonl"
VALID_FILE = BASE_DIR / "data" / "processed" / "ner" / "valid.jsonl"


def normalize_entity(entity):
    """
    Supports both:
    [start, end, label]

    and:
    {"start": ..., "end": ..., "label": ...}
    """

    if isinstance(entity, dict):
        start = int(entity["start"])
        end = int(entity["end"])
        label = str(entity["label"])
    else:
        start = int(entity[0])
        end = int(entity[1])
        label = str(entity[2])

    return start, end, label


def check_file(path):
    print(f"\nChecking: {path.name}")
    print("-" * 60)

    nlp = spacy.blank("en")

    total_records = 0
    total_entities = 0
    aligned_entities = 0
    misaligned_entities = 0

    misaligned_labels = Counter()
    misaligned_examples = []

    with open(path, "r", encoding="utf-8") as f:

        for line in f:

            if not line.strip():
                continue

            record = json.loads(line)

            text = record.get("text", "")
            entities = record.get("entities", [])

            total_records += 1

            doc = nlp.make_doc(text)

            for entity in entities:

                try:
                    start, end, label = normalize_entity(entity)

                except (ValueError, TypeError, KeyError, IndexError):
                    misaligned_entities += 1

                    if len(misaligned_examples) < 10:
                        misaligned_examples.append({
                            "label": "INVALID_ENTITY_FORMAT",
                            "start": None,
                            "end": None,
                            "text": str(entity)[:200]
                        })

                    continue

                total_entities += 1

                span = doc.char_span(
                    start,
                    end,
                    label=label,
                    alignment_mode="strict"
                )

                if span is None:

                    misaligned_entities += 1
                    misaligned_labels[label] += 1

                    if len(misaligned_examples) < 10:
                        misaligned_examples.append({
                            "label": label,
                            "start": start,
                            "end": end,
                            "text": text[start:end][:200]
                        })

                else:
                    aligned_entities += 1

    alignment_rate = (
        aligned_entities / total_entities * 100
        if total_entities
        else 0
    )

    print(f"Records             : {total_records}")
    print(f"Total entities      : {total_entities}")
    print(f"Aligned entities    : {aligned_entities}")
    print(f"Misaligned entities : {misaligned_entities}")
    print(f"Alignment rate      : {alignment_rate:.2f}%")

    print("\nMisaligned labels:")

    if misaligned_labels:

        for label, count in misaligned_labels.most_common():
            print(f"  {label}: {count}")

    else:
        print("  None")

    print("\nSample misaligned entities:")

    if misaligned_examples:

        for item in misaligned_examples:
            print(
                f"  [{item['label']}] "
                f"{item['start']}:{item['end']} -> "
                f"{repr(item['text'])}"
            )

    else:
        print("  None")

    return {
        "records": total_records,
        "entities": total_entities,
        "aligned": aligned_entities,
        "misaligned": misaligned_entities,
        "alignment_rate": alignment_rate,
    }


def main():

    print("=" * 60)
    print("CUAD NER ENTITY ALIGNMENT CHECK")
    print("=" * 60)

    train_result = check_file(TRAIN_FILE)

    valid_result = check_file(VALID_FILE)

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    print(
        f"Training alignment   : "
        f"{train_result['alignment_rate']:.2f}%"
    )

    print(
        f"Validation alignment : "
        f"{valid_result['alignment_rate']:.2f}%"
    )

    total_entities = (
        train_result["entities"] +
        valid_result["entities"]
    )

    total_misaligned = (
        train_result["misaligned"] +
        valid_result["misaligned"]
    )

    overall_rate = (
        (total_entities - total_misaligned)
        / total_entities
        * 100
        if total_entities
        else 0
    )

    print(
        f"Overall alignment    : "
        f"{overall_rate:.2f}%"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()