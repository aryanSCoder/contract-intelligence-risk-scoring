import json
import re
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

INDEX_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "vector_index"
    / "contract_sections.faiss"
)

METADATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "vector_index"
    / "metadata.json"
)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_section_title(section):
    title = section.get("title")

    if title:
        return title

    text = section.get("text", "").strip()

    match = re.match(r"^\s*(\d+\.\s+[^.\n]+)", text)

    if match:
        return match.group(1).strip()

    return "Untitled Section"


def load_resources():
    if not INDEX_FILE.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {INDEX_FILE}"
        )

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Metadata not found: {METADATA_FILE}"
        )

    index = faiss.read_index(str(INDEX_FILE))

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    model = SentenceTransformer(MODEL_NAME)

    return index, metadata, model


# Load resources once when this module is imported.
INDEX, METADATA, MODEL = load_resources()


def search(query, top_k=5):
    query_embedding = MODEL.encode(
        [query],
        normalize_embeddings=True,
    ).astype("float32")

    scores, indices = INDEX.search(
        query_embedding,
        top_k
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):

        if idx < 0:
            continue

        section = METADATA["sections"][int(idx)]

        results.append(
            {
                "rank": len(results) + 1,
                "score": round(float(score), 4),
                "section_id": section.get("section_id"),
                "title": get_section_title(section),
                "text": section.get("text", ""),
            }
        )

    return results


if __name__ == "__main__":

    import sys

    print("=" * 70)
    print("CONTRACT SEMANTIC SEARCH")
    print("=" * 70)

    if len(sys.argv) < 2:
        print(
            'Usage: python src\\search_contract.py '
            '"your search question"'
        )
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print(f"\nQuery: {query}")
    print("\nSearching contract...\n")

    results = search(query)

    if not results:
        print("No relevant sections found.")
        sys.exit(0)

    for result in results:

        print("-" * 70)

        print(
            f"#{result['rank']} | "
            f"Score: {result['score']} | "
            f"Section: {result['title']}"
        )

        print("-" * 70)

        print(result["text"][:1000])
        print()

    print("=" * 70)
    print(f"Results returned: {len(results)}")
    print("=" * 70)