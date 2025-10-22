# ===========================
# File: detector.py
# ===========================

"""
detector.py — Mendeteksi kemungkinan adanya pesan tersembunyi di gambar.
Menggunakan analisis statistik terhadap distribusi bit LSB (Least Significant Bit).
"""

from PIL import Image
import math

def detect_message(image_path: str, layers: int=1, sample_limit: int=50000) -> dict:
    """
    Analisis bit LSB untuk mendeteksi kemungkinan pesan tersembunyi.
    Mengembalikan dictionary hasil analisis.
    """
    if layers < 1 or layers > 4:
        raise ValueError("layers harus antara 1–4.")

    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    pixels = img.load()
    width, height = img.size

    mask = (1 << layers) - 1
    bit_data = ""
    total = 0

    # Kumpulkan sampel bit dari LSB pixel
    for y in range(height):
        for x in range(width):
            if total >= sample_limit:
                break
            r, g, b = pixels[x, y]
            bit_data += format(r & mask, f'0{layers}b')
            bit_data += format(g & mask, f'0{layers}b')
            bit_data += format(b & mask, f'0{layers}b')
            total += 3
        if total >= sample_limit:
            break

    # Cek apakah marker terminator ditemukan (11111110)
    has_marker = "11111110" in bit_data

    zeros, ones = bit_data.count('0'), bit_data.count('1')
    ratio = ones / (zeros + ones)
    randomness = abs(0.5 - ratio)

    # Hitung entropi bit
    entropy = 0
    for p in [zeros / (zeros + ones), ones / (zeros + ones)]:
        if p > 0:
            entropy -= p * math.log2(p)

    # Estimasi probabilitas pesan tersembunyi
    probability = round((1 - abs(0.5 - ratio)) * 100, 2)
    detected = has_marker or probability > 70

    return {
        "has_marker": has_marker,
        "entropy": round(entropy, 4),
        "bit_ratio": round(ratio, 4),
        "randomness_score": round(randomness, 4),
        "probability_of_hidden_message": probability,
        "message_detected": detected
    }
