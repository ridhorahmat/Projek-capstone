"""
Tahap 4 & 5: Potong video sesuai timestamp, lalu reformat ke rasio vertikal 9:16
(untuk MVP: crop di tengah, belum ada deteksi wajah otomatis).
"""

import os
import subprocess


def cut_and_reformat_clip(source_path: str, start: float, end: float, output_path: str):
    """
    Memotong video dari source_path sesuai rentang waktu [start, end],
    lalu crop ke rasio vertikal 9:16 (crop tengah).
    """
    duration = end - start

    # Filter ffmpeg: crop tengah ke rasio 9:16, lalu scale ke resolusi standar vertikal
    vf_filter = (
        "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',"
        "scale=1080:1920"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-i", source_path,
        "-t", str(duration),
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg gagal memproses klip: {result.stderr[-800:]}")

    return output_path
