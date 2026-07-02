from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_PATH = BASE_DIR / "data" / "mus_schedule.db"
MEDIA_DIR = BASE_DIR / "media"
RESPONSES_DIR = BASE_DIR / "responses"

MUSEUM_PHOTO = MEDIA_DIR / "museum_photo.jpg"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it to .env file.")