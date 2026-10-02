import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "sections" / "contract_sections.jsonl"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "vector_index"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_sections():
    sections = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            text = record.get("text", "").strip()

            if not text:
                continue

            sections.append(record)

    return sections


def main():
    print("=" * 70)
    print("CONTRACT VECTOR INDEX BUILDER")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Section file not found: {INPUT_FILE}"
        )

    print(f"Input: {INPUT_FILE}")
    print(f"Model: {MODEL_NAME}")

    sections = load_sections()

    print(f"Sections loaded: {len(sections)}")

    if not sections:
        raise ValueError("No valid contract sections found.")

    print("\nLoading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    texts = [
        section["text"]
        for section in sections
    ]

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    embeddings = embeddings.astype("float32")

    dimension = embeddings.shape[1]

    print(f"Embedding dimension: {dimension}")

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index_file = OUTPUT_DIR / "contract_sections.faiss"
    metadata_file = OUTPUT_DIR / "metadata.json"

    faiss.write_index(index, str(index_file))

    metadata = {
        "model": MODEL_NAME,
        "embedding_dimension": dimension,
        "total_sections": len(sections),
        "metric": "cosine_similarity",
        "sections": sections,
    }

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("VECTOR INDEX CREATED SUCCESSFULLY")
    print("=" * 70)
    print(f"Sections indexed : {len(sections)}")
    print(f"Dimension        : {dimension}")
    print(f"FAISS index      : {index_file}")
    print(f"Metadata          : {metadata_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()