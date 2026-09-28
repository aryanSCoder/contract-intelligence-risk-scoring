import json
import re
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parents[1]

SECTIONS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "sections"
    / "contract_sections.jsonl"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed" / "analysis"
OUTPUT_FILE = OUTPUT_DIR / "detected_clauses.json"


# High-value CUAD clause patterns.
# These are intentionally conservative to reduce false positives.
CLAUSE_PATTERNS: Dict[str, List[str]] = {
    "Anti-Assignment": [
        r"\bassign(?:ed|ment|ing)?\b",
        r"\btransfer(?:red|s)?\b",
        r"\bassignment\b",
    ],

    "Audit Rights": [
        r"\baudit\b",
        r"\baudit rights?\b",
        r"\binspect(?:ion)?\b",
        r"\bbooks and records\b",
    ],

    "Cap On Liability": [
        r"\blimit(?:ation)? of liability\b",
        r"\blimited liability\b",
        r"\bliability shall not exceed\b",
        r"\bmaximum liability\b",
    ],

    "Uncapped Liability": [
        r"\bunlimited liability\b",
        r"\buncapped liability\b",
        r"\bwithout limitation\b.*\bliability\b",
    ],

    "Change Of Control": [
        r"\bchange of control\b",
        r"\bchange in control\b",
        r"\bacquisition\b",
        r"\bmerger\b",
    ],

    "Insurance": [
        r"\binsurance\b",
        r"\binsured\b",
        r"\bcommercial general liability\b",
        r"\bworkers['’]? compensation\b",
    ],

    "Non-Compete": [
        r"\bnon[- ]compete\b",
        r"\bnoncompete\b",
        r"\bcompete with\b",
        r"\bcompetition\b",
    ],

    "No-Solicit Of Employees": [
        r"\bnon[- ]solicitation\b",
        r"\bnon[- ]solicit\b",
        r"\bsolicit(?:ation)? of employees\b",
        r"\bsolicit.*employees\b",
    ],

    "No-Solicit Of Customers": [
        r"\bsolicit.*customers\b",
        r"\bsolicit.*clients\b",
        r"\bnon[- ]solicit.*customers\b",
    ],

    "Non-Disparagement": [
        r"\bnon[- ]disparagement\b",
        r"\bdisparage\b",
        r"\bdisparaging\b",
    ],

    "Confidentiality": [
        r"\bconfidential(?:ity)?\b",
        r"\bconfidential information\b",
        r"\bnon[- ]disclosure\b",
        r"\bnda\b",
    ],

    "Termination For Convenience": [
        r"\btermination for convenience\b",
        r"\bterminate.*convenience\b",
        r"\bmay terminate.*without cause\b",
    ],

    "Notice Period To Terminate Renewal": [
        r"\bnotice period\b",
        r"\bnotice.*terminate\b",
        r"\bnotice.*renewal\b",
        r"\bprior written notice\b",
    ],

    "Renewal Term": [
        r"\brenew(?:al|ed|s)?\b",
        r"\brenewal term\b",
        r"\bautomatically renew\b",
    ],

    "Expiration Date": [
        r"\bexpiration date\b",
        r"\bexpire(?:s|d)?\b",
        r"\bexpiration\b",
    ],

    "Effective Date": [
        r"\beffective date\b",
        r"\beffective as of\b",
        r"\beffective on\b",
    ],

    "Governing Law": [
        r"\bgoverning law\b",
        r"\blaws of the state\b",
        r"\bgoverned by the laws\b",
        r"\bjurisdiction\b",
    ],

    "Liquidated Damages": [
        r"\bliquidated damages\b",
        r"\bliquidated damage\b",
    ],

    "Warranty Duration": [
        r"\bwarranty\b",
        r"\bwarranties\b",
        r"\bwarranty period\b",
    ],

    "Minimum Commitment": [
        r"\bminimum commitment\b",
        r"\bminimum purchase\b",
        r"\bminimum volume\b",
        r"\bminimum amount\b",
    ],

    "Volume Restriction": [
        r"\bvolume restriction\b",
        r"\bvolume limit\b",
        r"\bmaximum volume\b",
        r"\bminimum volume\b",
    ],

    "Exclusivity": [
        r"\bexclusive\b",
        r"\bexclusivity\b",
        r"\bexclusive right\b",
    ],

    "License Grant": [
        r"\blicense grant\b",
        r"\bgrants? .* license\b",
        r"\blicensed\b",
        r"\blicense to\b",
    ],

    "Ip Ownership Assignment": [
        r"\bintellectual property\b",
        r"\bIP ownership\b",
        r"\bownership of.*IP\b",
        r"\bassign.*intellectual property\b",
    ],

    "Joint Ip Ownership": [
        r"\bjoint ownership\b",
        r"\bjointly owned\b",
        r"\bjoint intellectual property\b",
    ],

    "Third Party Beneficiary": [
        r"\bthird[- ]party beneficiar(?:y|ies)\b",
        r"\bthird party beneficiary\b",
    ],

    "Covenant Not To Sue": [
        r"\bcovenant not to sue\b",
        r"\bagree not to sue\b",
    ],

    "Post-Termination Services": [
        r"\bpost[- ]termination\b",
        r"\bafter termination\b",
        r"\bservices.*termination\b",
    ],

    "Price Restrictions": [
        r"\bprice restriction\b",
        r"\bpricing restriction\b",
        r"\bprice shall not\b",
        r"\bpricing\b",
    ],

    "Revenue/Profit Sharing": [
        r"\brevenue sharing\b",
        r"\bprofit sharing\b",
        r"\bshare of revenue\b",
        r"\bshare of profits\b",
    ],

    "Most Favored Nation": [
        r"\bmost favored nation\b",
        r"\bmost-favored-nation\b",
        r"\bMFN\b",
    ],

    "Termination": [
        r"\btermination\b",
        r"\bterminate\b",
        r"\bterminated\b",
    ],

    "Parties": [
        r"\bbetween\b.*\band\b",
        r"\bparties\b",
        r"\bparty\b",
    ],
}


def load_sections() -> List[dict]:
    """Load segmented contract sections."""
    if not SECTIONS_FILE.exists():
        raise FileNotFoundError(
            f"Sections file not found: {SECTIONS_FILE}"
        )

    sections = []

    with SECTIONS_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            sections.append(json.loads(line))

    return sections


def detect_clauses(sections: List[dict]) -> List[dict]:
    """Detect CUAD-style clauses from contract sections."""
    detections = []

    for section in sections:
        text = section.get("text", "")

        if not text:
            continue

        section_id = section.get("section_id")
        title = section.get("title", "")
        contract_id = section.get("contract_id", "")

        for clause_type, patterns in CLAUSE_PATTERNS.items():

            matches = []

            for pattern in patterns:
                for match in re.finditer(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    start = match.start()
                    end = match.end()

                    # Capture a useful context window around the match.
                    context_start = max(0, start - 180)
                    context_end = min(len(text), end + 300)

                    context = text[context_start:context_end].strip()

                    matches.append(
                        {
                            "matched_text": match.group(0),
                            "start": start,
                            "end": end,
                            "context": context,
                        }
                    )

            if matches:
                # Remove duplicate matches caused by overlapping patterns.
                unique_matches = []
                seen = set()

                for match in matches:
                    key = (
                        match["start"],
                        match["end"],
                        match["matched_text"].lower(),
                    )

                    if key not in seen:
                        seen.add(key)
                        unique_matches.append(match)

                detections.append(
                    {
                        "contract_id": contract_id,
                        "section_id": section_id,
                        "section_title": title,
                        "clause_type": clause_type,
                        "match_count": len(unique_matches),
                        "matches": unique_matches,
                    }
                )

    return detections


def save_results(detections: List[dict]) -> None:
    """Save detected clauses to JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "source_file": str(SECTIONS_FILE),
        "total_detections": len(detections),
        "unique_clause_types": len(
            {item["clause_type"] for item in detections}
        ),
        "detections": detections,
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )


def print_summary(detections: List[dict]) -> None:
    """Print a readable detection summary."""
    print()
    print("=" * 70)
    print("CONTRACT CLAUSE DETECTION")
    print("=" * 70)

    print(f"Sections analyzed       : {len(set(d['section_id'] for d in detections))}")
    print(f"Clause detections       : {len(detections)}")
    print(
        f"Unique clause types     : "
        f"{len(set(d['clause_type'] for d in detections))}"
    )

    print()
    print("Detected clause types:")

    counts = {}

    for detection in detections:
        clause = detection["clause_type"]
        counts[clause] = counts.get(clause, 0) + detection["match_count"]

    for clause, count in sorted(
        counts.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"  {clause}: {count}")

    print()
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 70)


def main():
    print("Loading contract sections...")

    sections = load_sections()

    print(f"Sections loaded : {len(sections)}")

    detections = detect_clauses(sections)

    save_results(detections)

    print_summary(detections)

    print()
    print("✅ Clause detection completed successfully.")


if __name__ == "__main__":
    main()