import json
import random
from pathlib import Path

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "cuad_clause_labels.jsonl"
)

OUTPUT_DIR = (
    BASE_DIR
    / "models"
    / "transformer_clause_classifier"
)

MODEL_NAME = "google/bert_uncased_L-2_H-128_A-2"

MAX_LENGTH = 256
SAMPLE_SIZE = 1000
SEED = 42


def load_records():
    records = []

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if not record.get("is_answered"):
                continue

            text = record.get("question", "").strip()
            label = record.get("clause_type", "").strip()

            if text and label:
                records.append(
                    {
                        "text": text,
                        "label": label,
                    }
                )

    return records


def main():
    print("=" * 70)
    print("WEEK 2 TRANSFORMER CLAUSE CLASSIFIER")
    print("=" * 70)

    random.seed(SEED)

    records = load_records()

    print(f"\nAnswered CUAD records : {len(records)}")

    random.shuffle(records)

    records = records[:SAMPLE_SIZE]

    labels = sorted(
        set(record["label"] for record in records)
    )

    label_to_id = {
        label: index
        for index, label in enumerate(labels)
    }

    id_to_label = {
        index: label
        for label, index in label_to_id.items()
    }

    print(f"Training samples      : {len(records)}")
    print(f"Clause categories     : {len(labels)}")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=False,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(labels),
        id2label=id_to_label,
        label2id=label_to_id,
    )

    texts = [
        record["text"]
        for record in records
    ]

    label_ids = [
        label_to_id[record["label"]]
        for record in records
    ]

    encodings = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
    )

    class ContractDataset:
        def __init__(self, encodings, labels):
            self.encodings = encodings
            self.labels = labels

        def __getitem__(self, index):
            item = {
                key: value[index]
                for key, value in self.encodings.items()
            }

            item["labels"] = self.labels[index]

            return item

        def __len__(self):
            return len(self.labels)

    split = int(len(records) * 0.8)

    train_dataset = ContractDataset(
        {
            key: value[:split]
            for key, value in encodings.items()
        },
        label_ids[:split],
    )

    valid_dataset = ContractDataset(
        {
            key: value[split:]
            for key, value in encodings.items()
        },
        label_ids[split:],
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=1,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        learning_rate=5e-5,
        logging_steps=25,
        save_strategy="no",
        report_to="none",
        fp16=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
    )

    print("\nStarting transformer training...")

    trainer.train()

    print("\nEvaluating transformer model...")

    metrics = trainer.evaluate()

    print("\nEvaluation results:")

    for key, value in metrics.items():
        print(f"{key}: {value}")

    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    with open(
        OUTPUT_DIR / "label_mapping.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "label_to_id": label_to_id,
                "id_to_label": id_to_label,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nTransformer model saved:")
    print(OUTPUT_DIR)

    print("=" * 70)
    print("TRANSFORMER TRAINING COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()