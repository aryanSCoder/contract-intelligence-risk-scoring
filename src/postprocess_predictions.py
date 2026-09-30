import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = (
    BASE_DIR
    / "models"
    / "transformer_clause_classifier"
)

OUTPUT_FILE = MODEL_DIR / "postprocessing_rules.json"


RULES = {
    "Governing Law": [
        r"governing law",
        r"laws of",
        r"jurisdiction",
    ],
    "Termination": [
        r"terminate",
        r"termination",
        r"expiration",
    ],
    "Confidentiality": [
        r"confidential",
        r"non.?disclosure",
    ],
    "Insurance": [
        r"insurance",
        r"insured",
        r"coverage",
    ],
    "Exclusivity": [
        r"exclusive",
        r"exclusivity",
    ],
    "License Grant": [
        r"license",
        r"licence",
    ],
    "Audit Rights": [
        r"audit",
        r"inspection rights",
    ],
    "Anti-Assignment": [
        r"assign",
        r"assignment",
    ],
    "Indemnification": [
        r"indemnif",
    ],
    "Cap On Liability": [
        r"limitation of liability",
        r"liability shall not exceed",
        r"maximum liability",
    ],
    "Warranty": [
        r"warrant",
        r"warranty",
    ],
}


def apply_heuristics(text, predicted_label, confidence):
    text_lower = text.lower()

    adjusted_label = predicted_label
    adjusted_confidence = confidence
    matched_rule = None

    for label, patterns in RULES.items():

        for pattern in patterns:

            if re.search(pattern, text_lower):

                adjusted_label = label
                adjusted_confidence = min(
                    0.99,
                    max(confidence, confidence + 0.15),
                )

                matched_rule = pattern

                return {
                    "label": adjusted_label,
                    "confidence": round(
                        adjusted_confidence,
                        4,
                    ),
                    "rule_applied": True,
                    "matched_pattern": matched_rule,
                }

    return {
        "label": adjusted_label,
        "confidence": round(
            confidence,
            4,
        ),
        "rule_applied": False,
        "matched_pattern": None,
    }


def main():

    print("=" * 70)
    print("WEEK 2 POST-PROCESSING HEURISTICS")
    print("=" * 70)

    rules = {
        "rule_count": len(RULES),
        "rules": RULES,
        "confidence_adjustment": "+0.15",
        "maximum_confidence": 0.99,
        "purpose": (
            "Use clause-specific keyword patterns to refine "
            "transformer predictions and confidence."
        ),
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            rules,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nRules created : {len(RULES)}")
    print(f"Output        : {OUTPUT_FILE}")

    print("\nExample:")
    example = apply_heuristics(
        "This agreement may be terminated by either party.",
        "Other",
        0.42,
    )

    print(json.dumps(
        example,
        indent=2,
    ))

    print("\nPost-processing heuristics completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()