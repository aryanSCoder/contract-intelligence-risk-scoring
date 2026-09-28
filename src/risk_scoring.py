import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
    / "detected_clauses.json"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed" / "analysis"
OUTPUT_FILE = OUTPUT_DIR / "risk_report.json"


# Project-level risk rules.
# These are analytical scoring rules, not legal advice.
RISK_RULES = {
    "Uncapped Liability": 25,
    "Liquidated Damages": 20,
    "Non-Compete": 18,
    "Ip Ownership Assignment": 15,
    "Termination For Convenience": 12,
    "Anti-Assignment": 10,
    "Exclusivity": 10,
    "Minimum Commitment": 10,
    "Volume Restriction": 8,
    "Revenue/Profit Sharing": 8,
    "Change Of Control": 8,
    "Audit Rights": 6,
    "Insurance": 5,
    "Warranty Duration": 5,
    "Confidentiality": 5,
    "Non-Disparagement": 5,
    "No-Solicit Of Employees": 8,
    "No-Solicit Of Customers": 8,
    "Covenant Not To Sue": 10,
    "Post-Termination Services": 6,
    "Price Restrictions": 5,
    "Governing Law": 3,
    "Termination": 5,
    "Termination For Cause": 8,
    "Renewal Term": 4,
    "Notice Period To Terminate Renewal": 4,
    "Third Party Beneficiary": 3,
    "License Grant": 2,
    "Warranty": 3,
    "Effective Date": 0,
    "Expiration Date": 0,
    "Agreement Date": 0,
    "Document Name": 0,
    "Parties": 0,
}


def load_detections():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Clause detection file not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def calculate_risk(detections):
    """
    Calculate a consolidated contract risk score.

    Each clause type contributes at most twice its base score,
    regardless of how many sections or matches contain it.
    """

    clause_groups = {}

    # Consolidate detections by clause type.
    for detection in detections.get("detections", []):
        clause_type = detection["clause_type"]

        if clause_type not in clause_groups:
            clause_groups[clause_type] = {
                "clause_type": clause_type,
                "match_count": 0,
                "sections": [],
                "matches": [],
            }

        group = clause_groups[clause_type]

        group["match_count"] += detection.get("match_count", 1)

        section_id = detection.get("section_id")

        if section_id and section_id not in group["sections"]:
            group["sections"].append(section_id)

        group["matches"].extend(
            detection.get("matches", [])
        )

    total_score = 0
    risks = []

    for clause_type, group in clause_groups.items():

        base_score = RISK_RULES.get(clause_type, 0)

        if base_score <= 0:
            continue

        # A clause can contribute at most 2x its base score.
        contribution = min(
            base_score * group["match_count"],
            base_score * 2,
        )

        total_score += contribution

        risks.append(
            {
                "clause_type": clause_type,
                "risk_score": contribution,
                "base_score": base_score,
                "match_count": group["match_count"],
                "section_count": len(group["sections"]),
                "sections": group["sections"],
                "reason": get_reason(clause_type),
                "matches": group["matches"][:10],
            }
        )

    # Keep final score within 0–100.
    final_score = min(total_score, 100)

    if final_score >= 70:
        risk_level = "HIGH"
    elif final_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    risks.sort(
        key=lambda item: item["risk_score"],
        reverse=True,
    )

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "total_raw_score": total_score,
        "risk_count": len(risks),
        "risks": risks,
    }


def get_reason(clause_type):
    reasons = {
        "Uncapped Liability":
            "Potentially exposes a party to liability without a defined financial ceiling.",

        "Liquidated Damages":
            "May create predefined financial consequences following specified events.",

        "Non-Compete":
            "May restrict competitive activities during or after the agreement.",

        "Ip Ownership Assignment":
            "May transfer intellectual property ownership or rights to another party.",

        "Termination For Convenience":
            "May allow termination without requiring a specific breach or cause.",

        "Anti-Assignment":
            "May restrict the ability to transfer contractual rights or obligations.",

        "Exclusivity":
            "May limit the ability to work with alternative parties or suppliers.",

        "Minimum Commitment":
            "May create mandatory purchasing, payment, or volume commitments.",

        "Volume Restriction":
            "May restrict permitted transaction or usage volume.",

        "Revenue/Profit Sharing":
            "May create ongoing revenue or profit-sharing obligations.",

        "Change Of Control":
            "May trigger contractual consequences following ownership or control changes.",

        "Audit Rights":
            "May permit another party to inspect records or financial information.",

        "Insurance":
            "Creates insurance-related contractual obligations.",

        "Warranty Duration":
            "Creates obligations related to the duration of warranties.",

        "Confidentiality":
            "Creates obligations concerning confidential information.",

        "Non-Disparagement":
            "May restrict statements about another party.",

        "No-Solicit Of Employees":
            "May restrict recruitment or solicitation of employees.",

        "No-Solicit Of Customers":
            "May restrict solicitation of customers or clients.",

        "Covenant Not To Sue":
            "May restrict a party's ability to pursue certain legal claims.",

        "Post-Termination Services":
            "Creates obligations that may continue after contract termination.",

        "Price Restrictions":
            "May restrict pricing or commercial flexibility.",

        "Governing Law":
            "Determines the legal framework governing the agreement.",

        "Termination":
            "Defines conditions under which the contractual relationship may end.",

        "Renewal Term":
            "May automatically or contractually extend the agreement.",

        "Notice Period To Terminate Renewal":
            "Creates timing requirements for termination or renewal notices.",

        "Third Party Beneficiary":
            "May provide contractual rights to parties outside the primary agreement.",

        "License Grant":
            "Defines rights granted to use specified intellectual property or assets.",
    }

    return reasons.get(
        clause_type,
        "This clause may create contractual obligations or restrictions."
    )


def save_report(report):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )


def print_report(report):
    print()
    print("=" * 70)
    print("CONTRACT RISK SCORING")
    print("=" * 70)

    print(f"Risk Score : {report['risk_score']}/100")
    print(f"Risk Level : {report['risk_level']}")
    print(f"Risk Items : {report['risk_count']}")

    print()
    print("Risk breakdown:")

    if not report["risks"]:
        print("  No significant risk clauses detected.")
    else:
        for risk in report["risks"]:
            print(
                f"  {risk['clause_type']}: "
                f"+{risk['risk_score']} points"
            )

    print()
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 70)


def main():
    print("Loading detected clauses...")

    detections = load_detections()

    report = calculate_risk(detections)

    save_report(report)

    print_report(report)

    print()
    print("✅ Risk scoring completed successfully.")


if __name__ == "__main__":
    main()