# ===========================
# File: logger.py
# ===========================

"""
logger.py — Logging aktivitas dan pembuatan laporan CSV/JSON.
"""

import os, csv, json
from datetime import datetime

LOG_DIR = "logs"

def _ensure_log_dir():
    """Pastikan direktori log tersedia."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

def _log_file():
    """Mendapatkan nama file log berdasarkan tanggal."""
    _ensure_log_dir()
    return os.path.join(LOG_DIR, f"stegoimagex_{datetime.now().strftime('%Y%m%d')}.log")

def write_log(action: str, details: str):
    """
    Tulis aktivitas ke file log.
    Format: [timestamp] [ACTION] detail
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _ensure_log_dir()
    with open(_log_file(), "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [{action}] {details}\n")

def export_report(data: list, path: str):
    """
    Ekspor hasil batch ke CSV atau JSON.
    Jika path diakhiri .json → format JSON.
    Selain itu → format CSV.
    """
    _ensure_log_dir()
    if not data:
        return

    if path.endswith(".json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    else:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
