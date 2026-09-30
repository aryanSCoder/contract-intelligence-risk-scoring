import json
from pathlib import Path

from src.clause_detector import detect_clauses


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SECTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sections"
    / "contract_sections.jsonl"
)


def load_sections():
    sections = []

    with open(SECTIONS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                sections.append(json.loads(line))

    return sections


def test_clause_detector_returns_results():
    sections = load_sections()

    results = detect_clauses(sections)

    assert isinstance(results, list)
    assert len(results) > 0


def test_clause_detector_finds_expected_clause_types():
    sections = load_sections()

    results = detect_clauses(sections)

    clause_types = {
        result["clause_type"]
        for result in results
    }

    expected_types = {
        "Parties",
        "License Grant",
        "Exclusivity",
        "Governing Law",
    }

    assert expected_types.intersection(clause_types)


def test_clause_detection_contains_required_fields():
    sections = load_sections()

    results = detect_clauses(sections)

    required_fields = {
        "contract_id",
        "section_id",
        "section_title",
        "clause_type",
        "match_count",
        "matches",
    }

    for result in results:
        assert required_fields.issubset(result.keys())


def test_clause_detection_has_valid_matches():
    sections = load_sections()

    results = detect_clauses(sections)

    for result in results:
        assert isinstance(result["matches"], list)
        assert result["match_count"] == len(result["matches"])


def test_clause_detection_is_deterministic():
    sections = load_sections()

    first_run = detect_clauses(sections)
    second_run = detect_clauses(sections)

    assert first_run == second_run