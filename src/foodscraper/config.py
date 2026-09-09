# created from promt to Claude
from pathlib import Path

# always points to the repo root, regardless of where you run the script from
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = ROOT_DIR / "data"
GOOGLE_MAPS_DATASETS = DATA_DIR / "google-maps-api"
SRC_DIR  = ROOT_DIR / "src"
PROMPTS_DIR = ROOT_DIR / "prompts"
