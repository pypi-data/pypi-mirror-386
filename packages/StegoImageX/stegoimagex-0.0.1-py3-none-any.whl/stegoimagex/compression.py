# ===========================
# File: compression.py
# ===========================

"""
compression.py — Sistem kompresi & dekompresi pesan (zlib + base64)
"""

import zlib
import base64

def compress_message(message: str) -> str:
    """
    Kompres string teks menjadi base64 string.
    Menggunakan zlib untuk kompresi, dan base64 agar aman disimpan di dalam LSB.
    """
    compressed = zlib.compress(message.encode('utf-8'))
    return base64.b64encode(compressed).decode('utf-8')

def decompress_message(message: str) -> str:
    """
    Dekompresi base64 string menjadi teks asli.
    Digunakan otomatis ketika payload memiliki tag [CMP].
    """
    try:
        compressed = base64.b64decode(message)
        return zlib.decompress(compressed).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Gagal dekompresi pesan: {e}")
