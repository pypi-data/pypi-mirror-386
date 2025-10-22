# ===========================
# File: batch.py
# ===========================

"""
batch.py — Batch processing untuk hide, extract, dan detect secara paralel.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from .core import hide_text, extract_text, detect_message_info

VALID_EXT = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')

def _list_images(folder):
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(VALID_EXT)]

def batch_hide_text(input_folder, output_folder, message, encrypted=False,
                    password=None, layers=1, dynamic=True, compress=False,
                    adaptive=True, max_workers=4):
    os.makedirs(output_folder, exist_ok=True)
    images = _list_images(input_folder)
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for img in images:
            out = os.path.join(output_folder, os.path.basename(img))
            fut = executor.submit(hide_text, img, out, message, encrypted, password, layers, dynamic, compress, adaptive, False)
            futures[fut] = img
        for fut in as_completed(futures):
            name = os.path.basename(futures[fut])
            try:
                fut.result()
                results.append((name, "✅"))
            except Exception as e:
                results.append((name, f"❌ {e}"))
    return results

def batch_extract_text(input_folder, password=None, layers=1, dynamic=True,
                       compress=True, adaptive=True, max_workers=4):
    images = _list_images(input_folder)
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for img in images:
            fut = executor.submit(extract_text, img, password, layers, dynamic, compress, adaptive, False)
            futures[fut] = img
        for fut in as_completed(futures):
            name = os.path.basename(futures[fut])
            try:
                msg = fut.result()
                results.append((name, msg))
            except Exception as e:
                results.append((name, f"❌ {e}"))
    return results

def batch_detect_messages(input_folder, layers=1, max_workers=4):
    images = _list_images(input_folder)
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for img in images:
            fut = executor.submit(detect_message_info, img, False, layers)
            futures[fut] = img
        for fut in as_completed(futures):
            name = os.path.basename(futures[fut])
            try:
                info = fut.result()
                detected = "🟢" if info["message_detected"] else "⚪"
                results.append((name, detected, info["probability_of_hidden_message"]))
            except Exception as e:
                results.append((name, f"❌ {e}", 0))
    return results
