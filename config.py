import os

# ── Poll content ──────────────────────────────────────────────────────────────
QUESTION = "How many browser tabs open is still reasonable?"

ANSWERS = [
    "1 – 5   (minimalist)",
    "6 – 15  (normal)",
    "16 – 30 (power user)",
    "30+     (send help)",
]

# ── Security ──────────────────────────────────────────────────────────────────
# Set the RESET_TOKEN environment variable on PythonAnywhere for security.
# Falls back to the hard-coded value when running locally.
RESET_TOKEN = os.environ.get("RESET_TOKEN", "secret123")

# Flask session signing key – override via environment variable in production.
SECRET_KEY = os.environ.get("SECRET_KEY", "changeme-in-production-32chars!!")

# ── Storage ───────────────────────────────────────────────────────────────────
# Path to the JSON file that persists vote counts.
import pathlib
BASE_DIR = pathlib.Path(__file__).parent
VOTES_FILE = BASE_DIR / "votes.json"
