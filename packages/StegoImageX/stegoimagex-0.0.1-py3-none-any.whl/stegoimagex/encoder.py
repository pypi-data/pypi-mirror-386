# ===========================
# File: encoder.py
# ===========================

"""
encoder.py — Menyembunyikan teks dalam gambar menggunakan:
LSB multi-layer + AES + Hash + Kompresi + Dynamic Position Embedding (DPE) + Adaptive LSB (Pixel Intensity–Based)
"""

from PIL import Image
from .crypto import encrypt_message
from .integrity import embed_hash
from .dpe import generate_dpe_positions
from .compression import compress_message

def _get_adaptive_layers(r, g, b):
    """
    Hitung jumlah LSB yang digunakan berdasarkan intensitas pixel.
    Semakin terang pixel, semakin banyak bit yang dapat digunakan.
    """
    brightness = (r + g + b) / 3
    if brightness > 180:
        return 4
    elif brightness > 100:
        return 3
    elif brightness > 50:
        return 2
    else:
        return 1

def encode_text(input_path: str, output_path: str, secret_text: str,
                encrypted: bool=False, password: str=None,
                layers: int=1, dynamic: bool=True, compress: bool=False,
                adaptive: bool=True):
    """
    Encode teks ke gambar menggunakan LSB multi-layer adaptif.
    Dukung: Kompresi, Hash, Enkripsi, dan Dynamic Position Embedding.
    """
    if layers < 1 or layers > 4:
        raise ValueError("layers harus antara 1–4.")

    # Kompres pesan jika diaktifkan
    if compress:
        secret_text = "[CMP]" + compress_message(secret_text)
    else:
        secret_text = "[NOCMP]" + secret_text

    # Tambahkan hash integritas
    message_with_hash = embed_hash(secret_text)

    # Enkripsi pesan jika diperlukan
    if encrypted:
        if not password:
            raise ValueError("Password wajib diisi jika encrypted=True")
        payload = "[ENC]" + encrypt_message(message_with_hash, password)
    else:
        payload = "[PLN]" + message_with_hash

    # Tandai apakah adaptive aktif
    if adaptive:
        payload = "[ADP]" + payload
    else:
        payload = "[NOADP]" + payload

    # Konversi payload menjadi biner
    bits = ''.join(format(ord(c), '08b') for c in payload) + '1111111111111110'

    img = Image.open(input_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    width, height = img.size
    pixels = img.load()

    # Tentukan urutan posisi embedding (acak jika dynamic=True)
    if dynamic and password:
        positions = generate_dpe_positions(width, height, password)
    else:
        positions = list(range(width * height))

    idx = 0
    total_bits = len(bits)

    for pos in positions:
        if idx >= total_bits:
            break

        x = pos % width
        y = pos // width
        r, g, b = pixels[x, y]

        # Adaptive LSB: gunakan jumlah bit berdasarkan intensitas
        current_layers = _get_adaptive_layers(r, g, b) if adaptive else layers
        mask = (1 << current_layers) - 1

        # Sisipkan bit pada RGB channel
        for channel in range(3):
            if idx >= total_bits:
                break
            chunk = bits[idx:idx + current_layers].ljust(current_layers, '0')
            idx += current_layers

            val = int(chunk, 2)
            if channel == 0:
                r = (r & ~mask) | val
            elif channel == 1:
                g = (g & ~mask) | val
            else:
                b = (b & ~mask) | val

        pixels[x, y] = (r, g, b)

    # Simpan hasil gambar
    img.save(output_path)
