# created from promt to Claude
from pathlib import Path

# always points to the repo root, regardless of where you run the script from
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = ROOT_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
GOOGLE_MAPS_DIR = DATA_DIR / "sources" / "google-maps-api"
SRC_DIR  = ROOT_DIR / "src"
PROMPTS_DIR = ROOT_DIR / "prompts"
