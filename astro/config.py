"""Central configuration and paths."""
import os
from pathlib import Path

try:  # optional dependency
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"
DATA_DIR = ROOT / "data"
DB_PATH = Path(os.getenv("ASTRO_DB_PATH", DATA_DIR / "astro_play.db"))
CHROMA_DIR = Path(os.getenv("ASTRO_CHROMA_DIR", DATA_DIR / "chroma"))
SETTINGS_PATH = Path(os.getenv("ASTRO_SETTINGS_PATH", DATA_DIR / "settings.json"))
KNOWLEDGE_DIR = DATA_DIR / "knowledge"

# ---- LLM (Gemini). Set GEMINI_API_KEY in .env.  Provider "none" = fully offline answers.
LLM_PROVIDER = os.getenv("ASTRO_LLM_PROVIDER", "gemini").lower()          # gemini | none
LLM_MODEL = os.getenv("ASTRO_LLM_MODEL", "gemini-flash-latest")
# tried in order if the model above is unavailable for your key/region
LLM_FALLBACK_MODELS = tuple(m.strip() for m in os.getenv("ASTRO_LLM_FALLBACKS", "gemini-2.5-flash,gemini-2.5-flash-lite").split(",") if m.strip())
LLM_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
if LLM_API_KEY.lower() in ("your-key-here", "your-gemini-key", "changeme"):   # untouched template value
    LLM_API_KEY = ""
LLM_TIMEOUT_S = float(os.getenv("ASTRO_LLM_TIMEOUT", "25"))

LOGO_NAMES = ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp")


def find_logo():
    """Return the path of the official logo if supplied, else None."""
    for name in LOGO_NAMES:
        p = ASSETS_DIR / name
        if p.exists():
            return p
    return None
