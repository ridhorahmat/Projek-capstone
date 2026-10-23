"""
Aplikasi utama Short Clipper.

ALUR DUA TAHAP
1. POST /api/analyze : mengunduh, mentranskripsi, mencari kandidat klip.
                       Video BELUM dipotong pada tahap ini.
2. POST /api/render   : memotong hanya klip yang dipilih pengguna.
"""

from services.timing import stage, timed_request

import json
import os
import uuid
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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


class AnalyzeRequest(BaseModel):
    youtube_url: str
    clip_count: int = Field(default=5, ge=1, le=10)
    min_duration: int = Field(default=20, ge=10, le=180)
    max_duration: int = Field(default=90, ge=10, le=180)


class RenderRequest(BaseModel):
    job_id: str
    selected: list[int] = Field(default_factory=list)
    orientation: Literal["portrait", "landscape"] = "portrait"
    quality: Literal["720", "1080"] = "1080"
    burn_subtitle: bool = True
    smart_reframe: bool = True


def _job_dir(job_id: str) -> str:
    return os.path.join(JOBS_DIR, os.path.basename(job_id))


def _save_job(job_id: str, data: dict) -> None:
    with open(os.path.join(_job_dir(job_id), "job.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _load_job(job_id: str) -> dict:
    path = os.path.join(_job_dir(job_id), "job.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan atau sudah dihapus.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _transcript_excerpt(segments: list, start: float, end: float, limit: int = 400) -> str:
    texts = [s["text"] for s in segments if s["end"] > start and s["start"] < end]
    joined = " ".join(texts).strip()
    return joined if len(joined) <= limit else joined[:limit].rstrip() + "..."


@app.post("/api/analyze")
@timed_request("analisis")
def analyze_video(req: AnalyzeRequest):
    if req.max_duration <= req.min_duration:
        raise HTTPException(status_code=400, detail="Durasi maksimum harus lebih besar dari durasi minimum.")

    job_id = str(uuid.uuid4())[:8]
    job_dir = _job_dir(job_id)

    try:
        with stage('unduh video'):
            source_path, title = download_video(req.youtube_url, job_dir)

        with stage('transkripsi Whisper'):
            segments = transcribe(source_path, model_name=WHISPER_MODEL)
        if not segments:
            raise HTTPException(status_code=400, detail="Tidak ada suara terdeteksi pada video ini.")

        with stage('pemilihan kandidat klip'):
            candidates = find_highlight_segments(
                segments,
                max_clips=req.clip_count,
                min_seconds=req.min_duration,
                max_seconds=req.max_duration,
            )
        if not candidates:
            raise HTTPException(status_code=400, detail="Tidak ditemukan momen yang sesuai pada video ini.")

        with stage('simpan hasil analisis'):
            _save_job(job_id, {
                "job_id": job_id,
                "source_path": source_path,
                "video_title": title,
                "segments": segments,
                "candidates": candidates,
            })

        return {
            "job_id": job_id,
            "video_title": title,
            "candidates": [
                {
                    "index": i,
                    "title": c.get("title", f"Kandidat {i + 1}"),
                    "hook": c.get("hook", ""),
                    "category": c.get("category", ""),
                    "virality_score": c.get("virality_score"),
                    "reason": c.get("reason", ""),
                    "start": c["start"],
                    "end": c["end"],
                    "duration": round(c["end"] - c["start"], 1),
                    "transcript": _transcript_excerpt(segments, c["start"], c["end"]),
                }
                for i, c in enumerate(candidates)
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/render")
@timed_request("render")
def render_clips(req: RenderRequest):
    with stage('baca hasil analisis'):
        job = _load_job(req.job_id)
    candidates = job["candidates"]
    segments = job["segments"]
    source_path = job["source_path"]

    if not os.path.exists(source_path):
        raise HTTPException(status_code=410, detail="Berkas video sumber sudah tidak tersedia. Silakan analisis ulang.")

    chosen = req.selected or list(range(len(candidates)))
    invalid = [i for i in chosen if i < 0 or i >= len(candidates)]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Indeks kandidat tidak valid: {invalid}")

    job_dir = _job_dir(req.job_id)
    results = []

    try:
        for i in chosen:
            clip = candidates[i]
            output_filename = f"clip_{i + 1}.mp4"
            output_path = os.path.join(job_dir, output_filename)

            with stage(f"render {output_filename}"):
                cut_and_reformat_clip(
                    source_path,
                    clip["start"],
                    clip["end"],
                    output_path,
                    segments=segments,
                    orientation=req.orientation,
                    quality=req.quality,
                    burn_subtitle=req.burn_subtitle,
                    smart_reframe=req.smart_reframe,
                )

            results.append({
                "index": i,
                "title": clip.get("title", f"Klip {i + 1}"),
                "hook": clip.get("hook", ""),
                "category": clip.get("category", ""),
                "virality_score": clip.get("virality_score"),
                "reason": clip.get("reason", ""),
                "start": clip["start"],
                "end": clip["end"],
                "download_url": f"/files/{req.job_id}/{output_filename}",
            })

        return {
            "job_id": req.job_id,
            "video_title": job["video_title"],
            "settings": {
                "orientation": req.orientation,
                "quality": req.quality,
                "burn_subtitle": req.burn_subtitle,
                "smart_reframe": req.smart_reframe,
            },
            "clips": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health_check():
    return {"status": "ok"}