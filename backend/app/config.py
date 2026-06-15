"""Application settings. Tweak simulation speed here."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
AGENT_MODEL: str = os.getenv("AGENT_MODEL", "claude-sonnet-4-6")

TICK_SECONDS: float = 4.0          # one simulated event every N seconds
INCIDENT_RATIO: float = 0.35       # share of ticks that create an incident
SIM_AUTOSTART: bool = os.getenv("SIM_AUTOSTART", "true").lower() == "true"
MAX_AGENT_ITERATIONS: int = 8
MAX_TOKENS_PER_CALL: int = 1000

BACKEND_DIR = Path(__file__).resolve().parents[1]
BRANDS_FILE = BACKEND_DIR / "brands.json"
DB_FILE = BACKEND_DIR / "warroom.db"
