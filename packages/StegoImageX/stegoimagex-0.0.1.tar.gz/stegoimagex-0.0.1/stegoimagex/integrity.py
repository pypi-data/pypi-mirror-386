# ===========================
# File: integrity.py
# ===========================

"""
integrity.py — Sistem hashing dan integritas pesan (SHA-256).
"""

import hashlib, re

HASH_TAG_START = "[HASH]"
HASH_TAG_END = "[/HASH]"

def compute_hash(data: str) -> str:
    """Hitung hash SHA-256 dari string teks."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def embed_hash(message: str) -> str:
    """Tambahkan hash SHA-256 di awal pesan."""
    digest = compute_hash(message)
    return f"{HASH_TAG_START}{digest}{HASH_TAG_END}{message}"

def extract_and_verify_hash(payload: str):
    """
    Mengekstrak hash dari payload dan memverifikasi integritas pesan.
    Mengembalikan tuple:
    (verified_bool, message, hash_in_file, hash_now)
    """
    pattern = re.escape(HASH_TAG_START) + r"([0-9a-fA-F]+)" + re.escape(HASH_TAG_END)
    match = re.match(pattern, payload)
    if not match:
        return (False, payload, None, None)
    hash_in_file = match.group(1)
    message = payload[len(match.group(0)):]
    hash_now = compute_hash(message)
    return (hash_in_file == hash_now, message, hash_in_file, hash_now)
