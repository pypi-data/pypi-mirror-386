# ===========================
# File: decoder.py
# ===========================

"""
decoder.py — Mengekstrak pesan dari gambar dengan LSB + AES + DPE + Kompresi + Adaptive LSB.
"""

from PIL import Image
from .crypto import decrypt_message
from .integrity import extract_and_verify_hash
from .dpe import generate_dpe_positions
from .compression import decompress_message

def _get_adaptive_layers(r, g, b):
    """
    Fungsi yang sama seperti di encoder.py.
    Menentukan jumlah bit yang digunakan berdasarkan intensitas pixel.
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

def decode_text(image_path: str, password: str=None, layers: int=1,
                dynamic: bool=True, compress: bool=True, adaptive: bool=True) -> str:
    """
    Mengekstrak teks dari gambar.
    Mendukung DPE, AES, Kompresi, dan Adaptive LSB (Pixel Intensity–Based Extraction).
    """
    if layers < 1 or layers > 4:
        raise ValueError("layers harus antara 1–4.")

    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    pixels = img.load()
    width, height = img.size

    # Tentukan urutan posisi embedding sesuai DPE
    if dynamic and password:
        positions = generate_dpe_positions(width, height, password)
    else:
        positions = list(range(width * height))

    binary_data = ""
    # Adaptive reading — menentukan jumlah bit per pixel sesuai brightness
    for pos in positions:
        x = pos % width
        y = pos // width
        r, g, b = pixels[x, y]

        # Tentukan jumlah layer yang digunakan
        current_layers = _get_adaptive_layers(r, g, b) if adaptive else layers
        mask = (1 << current_layers) - 1

        # Baca bit dari RGB
        binary_data += format(r & mask, f'0{current_layers}b')
        binary_data += format(g & mask, f'0{current_layers}b')
        binary_data += format(b & mask, f'0{current_layers}b')

    # Pisahkan setiap 8 bit menjadi karakter
    bytes_list = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    decoded_text = ""
    for byte in bytes_list:
        if byte == "11111110":  # terminator
            break
        decoded_text += chr(int(byte, 2))

    # Cek tag mode (ADP atau NOADP)
    adaptive_mode = decoded_text.startswith("[ADP]")
    no_adaptive_mode = decoded_text.startswith("[NOADP]")

    if adaptive_mode:
        decoded_text = decoded_text[5:]  # hapus tag
        adaptive = True
    elif no_adaptive_mode:
        decoded_text = decoded_text[7:]
        adaptive = False

    # Cek apakah terenkripsi atau tidak
    if decoded_text.startswith("[ENC]"):
        if not password:
            raise ValueError("Password diperlukan untuk dekripsi.")
        decrypted = decrypt_message(decoded_text[5:], password)
        verified, msg, h1, h2 = extract_and_verify_hash(decrypted)
    elif decoded_text.startswith("[PLN]"):
        verified, msg, h1, h2 = extract_and_verify_hash(decoded_text[5:])
    else:
        # Jika tidak ada tag, kemungkinan data mentah
        return decoded_text

    # Dekompresi jika diaktifkan dan pesan dikompres
    if msg.startswith("[CMP]"):
        msg = decompress_message(msg[5:])
    elif msg.startswith("[NOCMP]"):
        msg = msg[7:]

    # Verifikasi integritas hash
    if not verified:
        msg += "\n⚠️ PERINGATAN: Integritas pesan tidak valid!"

    return msg
