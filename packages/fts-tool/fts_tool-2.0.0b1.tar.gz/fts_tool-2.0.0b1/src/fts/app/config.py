import os

from fts.config import APP_DIR as app_dir
from fts.core.logger import setup_logging

DISCOVERY_PORT = 6064
CHAT_PORT = 7064

SAVE_DIR = "Downloads//fts"

APP_DIR = app_dir+'/app'
os.makedirs(APP_DIR, exist_ok=True)

SEEN_IPS_FILE = os.path.join(APP_DIR, "seen_ips.json")
CONTACTS_FILE = os.path.join(APP_DIR, "contacts.json")
LOG_FILE      = os.path.join(APP_DIR, "log.txt")
DEBUG_FILE    = os.path.join(APP_DIR, "debug.txt")
MUTED_FILE    = os.path.join(APP_DIR, "muted.json")
CHAT_FILE     = os.path.join(APP_DIR, "chat.json")

LOGS = [LOG_FILE]

logger = setup_logging(verbose=True, id="APP", logfile=DEBUG_FILE)