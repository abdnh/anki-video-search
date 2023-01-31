from pathlib import Path

ADDON_NAME = "Video Search"
ADDON_PATH = Path(__file__).parent
VENDOR_DIR = ADDON_PATH / "vendor"
USERFILES_PATH = ADDON_PATH / "user_files"
MEDIA_PATH = USERFILES_PATH / "media"
DB_FILE = USERFILES_PATH / "media.db"
FIELD_FILTER = "video-search"
