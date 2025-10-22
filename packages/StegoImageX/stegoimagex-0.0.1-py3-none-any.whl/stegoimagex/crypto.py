# ===========================
# File: crypto.py
# ===========================

"""
crypto.py — Modul enkripsi & dekripsi menggunakan AES-256 CBC.
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib, base64

def _derive_key(password: str) -> bytes:
    """Membuat key 32-byte dari password menggunakan SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).digest()

def encrypt_message(message: str, password: str) -> str:
    """
    Mengenkripsi pesan teks menggunakan AES-256 CBC dan mengembalikan base64 string.
    Format output: IV + ciphertext
    """
    key = _derive_key(password)
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(message.encode('utf-8'), AES.block_size))
    return base64.b64encode(cipher.iv + ciphertext).decode('utf-8')

def decrypt_message(encrypted_message: str, password: str) -> str:
    """
    Mendekripsi pesan terenkripsi base64 (AES-256 CBC).
    Mengembalikan string plaintext asli.
    """
    key = _derive_key(password)
    data = base64.b64decode(encrypted_message)
    iv = data[:AES.block_size]
    ct = data[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ct), AES.block_size)
    return plaintext.decode('utf-8')
