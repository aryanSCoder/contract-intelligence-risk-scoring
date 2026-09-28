import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[1]

CLAUSE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
    / "detected_clauses.json"
)

RISK_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
    / "risk_report.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
)

FINAL_REPORT = OUTPUT_DIR / "contract_analysis_report.json"


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_report():
    clauses = load_json(CLAUSE_FILE)
    risk = load_json(RISK_FILE)

    detections = clauses.get("detections", [])

    report = {
        "project": "AI-Powered Contract Intelligence & Risk Scoring",
        "generated_at": datetime.now().isoformat(timespec="seconds"),

        "analysis_summary": {
            "sections_with_clauses": len(
                {
                    item.get("section_id")
                    for item in detections
                    if item.get("section_id")
                }
            ),
            "clause_detections": len(detections),
            "unique_clause_types": clauses.get(
                "unique_clause_types", 0
            ),
            "risk_items": risk.get("risk_count", 0),
        },

        "risk_assessment": {
            "risk_score": risk.get("risk_score", 0),
            "risk_level": risk.get("risk_level", "UNKNOWN"),
            "total_raw_score": risk.get(
                "total_raw_score", 0
            ),
        },

        "detected_clauses": detections,

        "risk_analysis": risk.get("risks", []),
    }

    return report


def save_report(report):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with FINAL_REPORT.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )


def print_summary(report):
    summary = report["analysis_summary"]
    assessment = report["risk_assessment"]

    print()
    print("=" * 70)
    print("CONTRACT INTELLIGENCE ANALYSIS")
    print("=" * 70)

    print()
    print("Analysis Summary")
    print("-" * 70)

    print(
        f"Sections with clauses : "
        f"{summary['sections_with_clauses']}"
    )

    print(
        f"Clause detections     : "
        f"{summary['clause_detections']}"
    )

    print(
        f"Unique clause types   : "
        f"{summary['unique_clause_types']}"
    )

    print(
        f"Risk items            : "
        f"{summary['risk_items']}"
    )

    print()
    print("Risk Assessment")
    print("-" * 70)

    print(
        f"Risk Score            : "
        f"{assessment['risk_score']}/100"
    )

    print(
        f"Risk Level            : "
        f"{assessment['risk_level']}"
    )

    print(
        f"Raw Risk Score        : "
        f"{assessment['total_raw_score']}"
    )

    print()
    print("Top Risk Factors")
    print("-" * 70)

    risks = report["risk_analysis"]

    if not risks:
        print("No risk factors detected.")
    else:
        for index, risk in enumerate(risks[:10], start=1):
            print(
                f"{index}. "
                f"{risk['clause_type']} "
                f"(+{risk['risk_score']})"
            )

    print()
    print(f"Final report: {FINAL_REPORT}")
    print("=" * 70)


def main():
    print("Loading clause detection and risk results...")

    report = build_report()

    save_report(report)

    print_summary(report)

    print()
    print(" Contract analysis report generated successfully.")


if __name__ == "__main__":
    main()