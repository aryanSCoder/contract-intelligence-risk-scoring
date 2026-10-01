import json
import random
import shutil
from pathlib import Path

import spacy
from spacy.training import Example
from spacy.util import minibatch


BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = BASE_DIR / "data" / "processed" / "ner" / "baseline_train.jsonl"
VALID_FILE = BASE_DIR / "data" / "processed" / "ner" / "valid.jsonl"

MODEL_DIR = BASE_DIR / "models" / "ner_baseline"

EPOCHS = 2
BATCH_SIZE = 1
SEED = 42
DROPOUT = 0.2


def load_records(path):
    """Stream JSONL records without loading the complete dataset."""
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)


def count_records(path):
    return sum(1 for _ in load_records(path))


def get_labels(path):
    labels = set()

    for record in load_records(path):
        for entity in record.get("entities", []):
            label = entity.get("label")

            if label:
                labels.add(str(label))

    return sorted(labels)


def create_example(nlp, record):
    """Create one spaCy training example with aligned entities."""

    text = record.get("text", "")

    if not text:
        return None

    entities = []

    for entity in record.get("entities", []):

        try:
            start = int(entity["start"])
            end = int(entity["end"])
            label = str(entity["label"])
        except (ValueError, TypeError, KeyError):
            continue

        if start < 0:
            continue

        if end > len(text):
            continue

        if start >= end:
            continue

        entities.append((start, end, label))

    if not entities:
        return None

    doc = nlp.make_doc(text)

    valid_entities = []

    for start, end, label in entities:

        span = doc.char_span(
            start,
            end,
            label=label,
            alignment_mode="strict",
        )

        if span is not None:
            valid_entities.append((start, end, label))

    if not valid_entities:
        return None

    return Example.from_dict(
        doc,
        {
            "entities": valid_entities
        },
    )


def load_shuffled_records(path, seed):
    """Load records for one epoch and shuffle their order.

    Only raw JSON records are stored temporarily.
    spaCy Example objects are created batch-by-batch.
    """

    records = list(load_records(path))

    rng = random.Random(seed)
    rng.shuffle(records)

    return records


def main():

    random.seed(SEED)

    print("=" * 70)
    print("CUAD CONTRACT NER BASELINE TRAINING")
    print("=" * 70)

    print("\nChecking dataset...")

    train_count = count_records(TRAIN_FILE)
    valid_count = count_records(VALID_FILE)

    print(f"Training records   : {train_count}")
    print(f"Validation records : {valid_count}")

    print("\nCreating blank spaCy English model...")

    nlp = spacy.blank("en")

    # CUAD contains long contract text.
    nlp.max_length = 2_000_000

    ner = nlp.add_pipe("ner")

    labels = get_labels(TRAIN_FILE)

    print(f"NER labels         : {len(labels)}")

    for label in labels:
        ner.add_label(label)

    print("\nLabels loaded successfully.")

    print("\nInitializing model...")

    # Use one training example to initialize the pipeline.
    first_record = next(load_records(TRAIN_FILE))

    first_example = create_example(
        nlp,
        first_record,
    )

    if first_example is None:
        raise RuntimeError(
            "Could not create a valid initialization example."
        )

    optimizer = nlp.initialize(
        get_examples=lambda: [first_example]
    )

    print("\nStarting baseline NER training...")
    print("-" * 70)

    for epoch in range(1, EPOCHS + 1):

        print(
            f"\nEpoch {epoch}/{EPOCHS}"
        )

        records = load_shuffled_records(
            TRAIN_FILE,
            SEED + epoch,
        )

        losses = {}

        processed = 0
        skipped = 0

        batches = minibatch(
            records,
            size=BATCH_SIZE,
        )

        for batch in batches:

            examples = []

            for record in batch:

                try:
                    example = create_example(
                        nlp,
                        record,
                    )

                    if example is None:
                        skipped += 1
                        continue

                    examples.append(example)

                except Exception:
                    skipped += 1

            if not examples:
                continue

            nlp.update(
                examples,
                sgd=optimizer,
                drop=DROPOUT,
                losses=losses,
            )

            processed += len(examples)

            if processed % 500 < BATCH_SIZE:

                print(
                    f"  Processed: {processed}/{train_count} "
                    f"| Loss: {losses.get('ner', 0.0):.4f}"
                )

            del examples

        print(
            f"\nEpoch {epoch} completed"
        )

        print(
            f"  Processed : {processed}"
        )

        print(
            f"  Skipped   : {skipped}"
        )

        print(
            f"  Loss      : {losses.get('ner', 0.0):.4f}"
        )

        del records

    print("\nSaving trained baseline NER model...")

    if MODEL_DIR.exists():
        shutil.rmtree(MODEL_DIR)

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    nlp.to_disk(MODEL_DIR)

    print(
        f"Model saved to: {MODEL_DIR}"
    )

    print("\nBaseline NER training completed successfully.")

    print("=" * 70)


if __name__ == "__main__":
    main()