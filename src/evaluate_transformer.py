import json
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = (
    BASE_DIR
    / "models"
    / "transformer_clause_classifier"
)

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "cuad_clause_labels.jsonl"
)

SAMPLE_SIZE = 500


def load_records():
    records = []

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if not record.get("is_answered"):
                continue

            question = record.get("question", "").strip()
            label = record.get("clause_type", "").strip()

            if question and label:
                records.append(
                    {
                        "text": question,
                        "label": label,
                    }
                )

    return records


def main():
    print("=" * 70)
    print("WEEK 2 TRANSFORMER EVALUATION")
    print("=" * 70)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_DIR,
        use_fast=False,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_DIR
    )

    model.eval()

    records = load_records()

    label_to_id = model.config.label2id

    filtered = [
        record
        for record in records
        if record["label"] in label_to_id
    ]

    filtered = filtered[:SAMPLE_SIZE]

    print(f"\nEvaluation samples : {len(filtered)}")
    print(f"Classes             : {len(label_to_id)}")

    predictions = []
    actual = []

    for record in filtered:

        inputs = tokenizer(
            record["text"],
            return_tensors="pt",
            truncation=True,
            max_length=256,
        )

        with torch.no_grad():
            outputs = model(**inputs)

        prediction = int(
            torch.argmax(outputs.logits, dim=-1).item()
        )

        actual_id = label_to_id[record["label"]]

        predictions.append(prediction)
        actual.append(actual_id)

    accuracy = accuracy_score(
        actual,
        predictions,
    )

    precision, recall, f1, _ = precision_recall_fscore_support(
        actual,
        predictions,
        average="weighted",
        zero_division=0,
    )

    print("\nEvaluation Metrics")
    print("-" * 40)
    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")

    report = {
        "model": "google/bert_uncased_L-2_H-128_A-2",
        "evaluation_samples": len(filtered),
        "classes": len(label_to_id),
        "accuracy": accuracy,
        "precision_weighted": precision,
        "recall_weighted": recall,
        "f1_weighted": f1,
    }

    output_file = (
        MODEL_DIR
        / "evaluation_metrics.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    print(f"\nMetrics saved to:")
    print(output_file)

    print("=" * 70)
    print("TRANSFORMER EVALUATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()