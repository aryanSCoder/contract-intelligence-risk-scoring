from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
ZIP_PATH = RAW_DIR / "cuad_data.zip"

CUAD_URL = (
    "https://github.com/The-Atticus-Project/cuad"
    "/raw/refs/heads/main/data.zip"
)


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    print("Downloading CUAD dataset...")

    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    with urlopen(request) as response:
        with destination.open("wb") as file:
            while True:
                chunk = response.read(1024 * 1024)

                if not chunk:
                    break

                file.write(chunk)

    print("Download complete.")


def extract_dataset(zip_path: Path, output_dir: Path) -> None:
    print("Extracting CUAD dataset...")

    with ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(output_dir)

    print("Extraction complete.")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if not ZIP_PATH.exists():
        download_file(CUAD_URL, ZIP_PATH)
    else:
        print("CUAD ZIP already exists. Skipping download.")

    extract_dataset(ZIP_PATH, RAW_DIR)

    print()
    print("CUAD dataset setup complete.")
    print(f"Dataset location: {RAW_DIR}")


if __name__ == "__main__":
    main()