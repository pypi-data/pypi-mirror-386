# ===========================
# File: dpe.py
# ===========================

"""
dpe.py — Dynamic Position Embedding (DPE)
Menyediakan embedding acak deterministik berdasarkan password hash.
"""

import random, hashlib

def generate_dpe_positions(width: int, height: int, password: str):
    """
    Menghasilkan urutan posisi embedding acak deterministik dari password.
    Hasil urutan akan selalu sama untuk password dan ukuran gambar yang sama.
    """
    total_pixels = width * height
    positions = list(range(total_pixels))
    seed = int(hashlib.sha256(password.encode('utf-8')).hexdigest(), 16)
    rng = random.Random(seed)
    rng.shuffle(positions)
    return positions
