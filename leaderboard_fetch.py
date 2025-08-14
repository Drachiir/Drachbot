import os
import json
import logging
import requests
from datetime import datetime

# ---------- Config ----------
CALLS = 400
BASE_DIR = "/shared2/leaderboard"
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SECRETS_PATH = "Files/json/Secrets.json"
# ----------------------------

today = datetime.today()
date = today.strftime("%d-%m-%y")
month_str = today.strftime("-%m-%y")  # e.g., "-08-25" for Aug 2025

# Ensure dirs (so logging + listdir won't blow up)
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- Logging (per month) ----------
log_file = os.path.join(LOGS_DIR, f"leaderboard{month_str}.log")
logger = logging.getLogger("leaderboard")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers if script is run multiple times in same process
if not logger.handlers:
    fh = logging.FileHandler(log_file, encoding="utf-8")
    ch = logging.StreamHandler()
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)

logger.info("Script started")
logger.info(f"Run date={date}, month_str={month_str}")
# ----------------------------------------

# Early bail if a parsed file for this month already exists
parsed_dir = BASE_DIR
existing = [
    f for f in os.listdir(parsed_dir)
    if f.startswith("leaderboard_parsed_") and f.endswith(".json") and month_str in f
]
if existing:
    logger.info(f"Found existing parsed file for current month: {existing[0]}. Exiting early.")
    raise SystemExit(0)

# Load API key
try:
    with open(SECRETS_PATH, "r") as f:
        secret_file = json.load(f)
    apikey = secret_file.get("apikey")
    if not apikey:
        logger.error("API key missing in Secrets.json")
        raise SystemExit(1)
    logger.info("Secrets.json loaded.")
except FileNotFoundError:
    logger.error(f"Secrets.json not found at {SECRETS_PATH}")
    raise SystemExit(1)
except Exception as e:
    logger.exception(f"Failed to load Secrets.json: {e}")
    raise SystemExit(1)

headers = {"x-api-key": apikey}

leaderboard_dir = os.path.join(DATA_DIR, f"leaderboard_{date}")
os.makedirs(leaderboard_dir, exist_ok=True)
logger.info(f"Data directory: {leaderboard_dir}")

# Fetch pages
saved_files = 0
for i in range(CALLS):
    url = (
        "https://apiv2.legiontd2.com/players/stats"
        f"?limit=1000&offset={i * 1000}&sortBy=overallElo&sortDirection=-1"
    )
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            logger.warning(f"API {i+1}/{CALLS} HTTP {resp.status_code} — skipping.")
            continue
        data = resp.json()
        out_path = os.path.join(leaderboard_dir, f"leaderboard_data{i}.json")
        with open(out_path, "w") as f:
            json.dump(data, f)
        saved_files += 1
        if (i + 1) % 10 == 0 or i == 0:
            logger.info(f"Saved {i+1}/{CALLS} -> {out_path}")
    except Exception as e:
        logger.exception(f"API {i+1}/{CALLS} failed: {e}")

logger.info(f"Fetch phase complete. Saved files: {saved_files}/{CALLS}")

# Parse
parsed_data = []
entries = 0
logger.info("Starting parse step...")
for fname in os.listdir(leaderboard_dir):
    if not fname.endswith(".json"):
        continue
    fpath = os.path.join(leaderboard_dir, fname)
    try:
        with open(fpath, "r") as f:
            data = json.load(f)
        for player in data:
            try:
                elo = player["overallElo"]
                wins = player["rankedWinsThisSeason"]
                losses = player["rankedLossesThisSeason"]
            except Exception:
                continue
            if wins + losses == 0:
                continue
            parsed_data.append([elo, wins, losses])
            entries += 1
    except Exception as e:
        logger.exception(f"Failed to parse {fpath}: {e}")

parsed_path = os.path.join(parsed_dir, f"leaderboard_parsed_{date}.json")
try:
    with open(parsed_path, "w") as f:
        json.dump(parsed_data, f)
    logger.info(f"Parsed data saved: {parsed_path} (entries={entries})")
except Exception as e:
    logger.exception(f"Failed to write parsed file: {e}")
    raise SystemExit(1)

# Cleanup raw files
logger.info("Cleaning up raw data files...")
deleted = 0
for fname in os.listdir(leaderboard_dir):
    fpath = os.path.join(leaderboard_dir, fname)
    try:
        os.remove(fpath)
        deleted += 1
    except Exception as e:
        logger.warning(f"Error deleting {fpath}: {e}")
logger.info(f"Cleanup complete. Deleted {deleted} files from {leaderboard_dir}")

logger.info("Script completed successfully.")