"""
Tahap 1: Ambil video dari YouTube dan ekstrak file video + audio.
Menggunakan yt-dlp untuk download, disimpan sementara di folder jobs/<job_id>/
Resolusi dibatasi maksimal 1080p. Kalau ada file cookies.txt (hasil export manual
dari browser), dipakai untuk menghindari deteksi bot YouTube.
"""

import os
import yt_dlp

BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
COOKIES_FILE = os.path.join(BACKEND_DIR, "cookies.txt")


def download_video(youtube_url: str, job_dir: str) -> str:
    os.makedirs(job_dir, exist_ok=True)

    output_template = os.path.join(job_dir, "source.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best[height<=1080]",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    # Kalau file cookies.txt ada di folder backend, pakai itu supaya tidak dianggap bot
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
    except yt_dlp.utils.DownloadError as e:
        hint = (
            "Tidak ditemukan file cookies.txt di folder backend. "
            if not os.path.exists(COOKIES_FILE)
            else "File cookies.txt ada tapi mungkin sudah kedaluwarsa, coba export ulang. "
        )
        raise RuntimeError(
            f"Gagal download video dari YouTube: {e}\n{hint}"
            f"Lihat panduan export cookies.txt untuk mengatasi ini."
        )

    downloaded_path = os.path.join(job_dir, "source.mp4")

    if not os.path.exists(downloaded_path):
        for f in os.listdir(job_dir):
            if f.startswith("source."):
                downloaded_path = os.path.join(job_dir, f)
                break

    return downloaded_path, info.get("title", "video")
