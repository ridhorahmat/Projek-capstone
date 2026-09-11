"""
Tahap 4 & 5: Potong video sesuai timestamp, reformat ke rasio vertikal 9:16,
dan burn-in subtitle otomatis dari hasil transkrip.
"""

import os
import subprocess


def _format_srt_timestamp(seconds: float) -> str:
    """Ubah detik (float) jadi format waktu SRT: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def generate_srt_for_clip(segments: list[dict], clip_start: float, clip_end: float, srt_path: str) -> str:
    """
    Membuat file .srt berisi subtitle untuk rentang waktu klip tertentu.
    Timestamp di-geser supaya relatif terhadap awal klip (dimulai dari 0).
    """
    relevant = [s for s in segments if s["end"] > clip_start and s["start"] < clip_end]

    lines = []
    idx = 1
    for seg in relevant:
        start = max(seg["start"], clip_start) - clip_start
        end = min(seg["end"], clip_end) - clip_start
        if end <= start:
            continue

        lines.append(str(idx))
        lines.append(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(end)}")
        lines.append(seg["text"].strip())
        lines.append("")
        idx += 1

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return srt_path


def _escape_path_for_ffmpeg(path: str) -> str:
    """ffmpeg filter butuh format path khusus: pakai forward slash dan escape titik dua (:)"""
    path = path.replace("\\", "/")
    path = path.replace(":", "\\:")
    return path


def cut_and_reformat_clip(
    source_path: str,
    start: float,
    end: float,
    output_path: str,
    segments: list[dict] | None = None,
) -> str:
    """
    Memotong video dari source_path sesuai rentang waktu [start, end],
    crop ke rasio vertikal 9:16, dan (kalau segments diberikan) burn-in subtitle otomatis.
    """
    duration = end - start

    vf_parts = [
        "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'",
        "scale=1080:1920",
    ]

    srt_path = None
    if segments:
        srt_path = os.path.splitext(output_path)[0] + ".srt"
        generate_srt_for_clip(segments, start, end, srt_path)

        escaped_srt = _escape_path_for_ffmpeg(srt_path)
        style = (
            "FontName=Arial,FontSize=16,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,"
            "Alignment=2,MarginV=80"
        )
        vf_parts.append(f"subtitles='{escaped_srt}':force_style='{style}'")

    vf_filter = ",".join(vf_parts)

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