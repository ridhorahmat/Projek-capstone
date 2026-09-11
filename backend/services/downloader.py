"""
Tahap 1: Ambil video dari YouTube dan ekstrak file video + audio.
Menggunakan yt-dlp untuk download, disimpan sementara di folder jobs/<job_id>/
"""

import os
import yt_dlp


def download_video(youtube_url: str, job_dir: str) -> str:
    """
    Download video dari YouTube ke job_dir.
    Mengembalikan path lengkap file video hasil download.
    """
    os.makedirs(job_dir, exist_ok=True)

    output_template = os.path.join(job_dir, "source.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        # Nama file final setelah merge biasanya source.mp4
        downloaded_path = os.path.join(job_dir, "source.mp4")

    if not os.path.exists(downloaded_path):
        # fallback: cari file apapun yang berhasil diunduh
        for f in os.listdir(job_dir):
            if f.startswith("source."):
                downloaded_path = os.path.join(job_dir, f)
                break

    return downloaded_path, info.get("title", "video")
