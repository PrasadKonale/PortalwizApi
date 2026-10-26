import os
import cv2

# Disable PyTorch multithreading to prevent deadlocks in macOS background workers
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import torch
torch.set_num_threads(1)

import easyocr

_reader = None


def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def extract_text(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read the uploaded image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    reader = get_reader()
    results = reader.readtext(gray, detail=1)

    extracted_lines = []

    for result in results:
        text = result[1].strip()
        confidence = float(result[2])

        if text:
            extracted_lines.append({
                "text": text,
                "confidence": round(confidence, 3)
            })

    return extracted_lines