# ===========================
# File: core.py
# ===========================

"""
core.py — API utama StegoImageX v11.0 (Compression + DPE + AES + Hash + Adaptive LSB)
"""

from .encoder import encode_text
from .decoder import decode_text
from .detector import detect_message
from .batch import batch_hide_text, batch_extract_text, batch_detect_messages
from .logger import write_log, export_report

def hide_text(input_image, output_image, message, encrypted=False,
              password=None, layers=1, dynamic=True, compress=False,
              adaptive=True, logging=False):
    """
    Sembunyikan pesan ke dalam gambar dengan fitur:
    - Compression
    - Dynamic Position Embedding (DPE)
    - Adaptive LSB (berdasarkan intensitas pixel)
    """
    encode_text(input_image, output_image, message, encrypted, password, layers, dynamic, compress, adaptive)
    if logging:
        write_log("HIDE", f"{input_image} -> {output_image} | enc={encrypted} | cmp={compress} | dyn={dynamic} | adp={adaptive}")

def extract_text(image_path, password=None, layers=1, dynamic=True,
                 compress=True, adaptive=True, logging=False):
    """Ekstraksi pesan dari gambar (support DPE + Adaptive LSB)."""
    msg = decode_text(image_path, password, layers, dynamic, compress, adaptive)
    if logging:
        write_log("EXTRACT", f"{image_path} | len={len(msg)} | cmp={compress} | dyn={dynamic} | adp={adaptive}")
    return msg

def detect_message_info(image_path, logging=False, layers=1):
    """Analisis kemungkinan pesan tersembunyi di gambar."""
    info = detect_message(image_path, layers)
    if logging:
        write_log("DETECT", f"{image_path} | prob={info['probability_of_hidden_message']}")
    return info

def hide_text_batch(input_folder, output_folder, message, encrypted=False,
                    password=None, layers=1, dynamic=True, compress=False,
                    adaptive=True, max_workers=4, logging=False, report_path=None):
    res = batch_hide_text(input_folder, output_folder, message, encrypted, password, layers, dynamic, compress, adaptive, max_workers)
    if logging:
        for n, s in res:
            write_log("BATCH_HIDE", f"{n} | {s}")
    if report_path:
        export_report([{"filename": n, "status": s} for n, s in res], report_path)
    return res

def extract_text_batch(input_folder, password=None, layers=1, dynamic=True,
                       compress=True, adaptive=True, max_workers=4,
                       logging=False, report_path=None):
    res = batch_extract_text(input_folder, password, layers, dynamic, compress, adaptive, max_workers)
    if logging:
        for n, msg in res:
            write_log("BATCH_EXTRACT", f"{n} | len={len(msg)}")
    if report_path:
        export_report([{"filename": n, "message": m} for n, m in res], report_path)
    return res

def detect_message_batch(input_folder, layers=1, max_workers=4,
                         logging=False, report_path=None):
    res = batch_detect_messages(input_folder, layers, max_workers)
    if logging:
        for n, s, p in res:
            write_log("BATCH_DETECT", f"{n} | {s} | prob={p}")
    if report_path:
        export_report([{"filename": n, "status": s, "probability": p} for n, s, p in res], report_path)
    return res
