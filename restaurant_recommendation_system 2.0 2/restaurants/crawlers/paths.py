from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent      # restaurants/
DATA_DIR = APP_DIR / "current"                        # restaurants/current/
DATA_DIR.mkdir(parents=True, exist_ok=True)

STORES_JSON  = DATA_DIR / "store_intros.json"
REVIEWS_JSON = DATA_DIR / "all_reviews.json"