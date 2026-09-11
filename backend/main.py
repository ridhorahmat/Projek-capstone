"""
Aplikasi utama: menerima link YouTube dari frontend, lalu menjalankan seluruh pipeline
1. Download video      -> services/downloader.py
2. Transkripsi          -> services/transcriber.py
3. Cari momen menarik   -> services/segmenter.py
4. Potong & reformat    -> services/clipper.py

Untuk MVP, semua job diproses secara synchronous (langsung dalam satu request).
Untuk versi produksi nanti, sebaiknya dipindah ke background task/queue (misal Celery)
karena proses ini bisa memakan waktu beberapa menit per video.
"""

import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.downloader import download_video
from services.transcriber import transcribe
from services.segmenter import find_highlight_segments
from services.clipper import cut_and_reformat_clip

load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
JOBS_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(JOBS_DIR, exist_ok=True)

app = FastAPI(title="Short Clipper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=JOBS_DIR), name="files")


class ProcessRequest(BaseModel):
    youtube_url: str


@app.post("/api/process")
def process_video(req: ProcessRequest):
    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(JOBS_DIR, job_id)

    try:
        source_path, title = download_video(req.youtube_url, job_dir)

        segments = transcribe(source_path, model_name=WHISPER_MODEL)
        if not segments:
            raise HTTPException(status_code=400, detail="Tidak ada suara terdeteksi di video ini.")

        highlights = find_highlight_segments(segments)
        if not highlights:
            raise HTTPException(status_code=400, detail="AI tidak menemukan momen menarik di video ini.")

        clips_result = []
        for i, clip in enumerate(highlights):
            output_filename = f"clip_{i + 1}.mp4"
            output_path = os.path.join(job_dir, output_filename)
            cut_and_reformat_clip(source_path, clip["start"], clip["end"], output_path, segments=segments)

            clips_result.append({
                "title": clip.get("title", f"Klip {i + 1}"),
                "reason": clip.get("reason", ""),
                "hook": clip.get("hook", ""),
                "category": clip.get("category", ""),
                "virality_score": clip.get("virality_score"),
                "start": clip["start"],
                "end": clip["end"],
                "download_url": f"/files/{job_id}/{output_filename}",
            })

        return {
            "job_id": job_id,
            "video_title": title,
            "clips": clips_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health_check():
    return {"status": "ok"}