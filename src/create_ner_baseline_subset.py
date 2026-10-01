import json
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "ner"
    / "train.jsonl"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "ner"
    / "baseline_train.jsonl"
)

SAMPLE_SIZE = 300
SEED = 42


def main():
    print("=" * 65)
    print("CREATE BASELINE NER TRAINING SUBSET")
    print("=" * 65)

    records = []

    print("\nLoading NER training records...")

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                record = json.loads(line)

                if record.get("entities"):
                    records.append(record)

    print(f"Records with entities : {len(records)}")

    if len(records) < SAMPLE_SIZE:
        raise RuntimeError(
            f"Not enough records for sample size {SAMPLE_SIZE}."
        )

    random.seed(SEED)

    random.shuffle(records)

    selected = records[:SAMPLE_SIZE]

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        for record in selected:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"Selected records     : {len(selected)}")
    print(f"Output                : {OUTPUT_FILE}")

    print("\nBaseline subset created successfully.")
    print("=" * 65)


if __name__ == "__main__":
    main()