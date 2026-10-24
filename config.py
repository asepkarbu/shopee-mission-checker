import os
from pathlib import Path
from dotenv import load_dotenv

# Muat variabel dari file .env
load_dotenv()

BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR / "sessions"
OUTPUT_DIR = BASE_DIR
LOGS_DIR = BASE_DIR / "logs"

# API otomatis terbaca dari file .env
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "") # Tambahan untuk nomor HP

BOT_USERNAME = "@shp_tools_bot"

RESPONSE_TIMEOUT = 60
MAX_CONCURRENCY = 1
BATCH_DELAY = 5.0

def ensure_dirs():
    SESSIONS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)