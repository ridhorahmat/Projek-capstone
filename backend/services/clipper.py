"""
Tahap 4 & 5: Potong video sesuai timestamp, reformat sesuai orientasi & kualitas
yang dipilih user, dengan opsi smart reframe (mengikuti wajah) dan subtitle.
"""

from services.timing import stage

import os
import subprocess

from services.reframe import get_smart_crop_x_expression

# Resolusi output per kombinasi orientasi + kualitas
RESOLUTIONS = {
    ("portrait", "720"): (720, 1280),
    ("portrait", "1080"): (1080, 1920),
    ("landscape", "720"): (1280, 720),
    ("landscape", "1080"): (1920, 1080),
}

# Ukuran font subtitle disesuaikan dengan resolusi supaya proporsional
SUBTITLE_FONT_SIZE = {"720": 14, "1080": 18}


def _format_srt_timestamp(seconds):
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

MAX_SUBTITLE_CHARS = 42   # batas karakter per blok subtitle


def _split_long_segment(text, start, end, max_chars=MAX_SUBTITLE_CHARS):
    """
    Pecah satu segmen panjang jadi beberapa blok subtitle pendek.
    Waktu dibagi proporsional terhadap jumlah karakter tiap blok.
    """
    words = text.split()
    if not words:
        return []

    blocks = []
    current = ""
    for word in words:
        calon = f"{current} {word}".strip()
        if len(calon) > max_chars and current:
            blocks.append(current)
            current = word
        else:
            current = calon
    if current:
        blocks.append(current)

    if len(blocks) == 1:
        return [(start, end, blocks[0])]

    total_chars = sum(len(b) for b in blocks)
    hasil = []
    t = start
    for b in blocks:
        durasi = (end - start) * (len(b) / total_chars)
        hasil.append((t, min(t + durasi, end), b))
        t += durasi
    return hasil

def generate_srt_for_clip(segments, clip_start, clip_end, srt_path):
    relevant = [s for s in segments if s["end"] > clip_start and s["start"] < clip_end]

    lines = []
    idx = 1
    for seg in relevant:
        start = max(seg["start"], clip_start) - clip_start
        end = min(seg["end"], clip_end) - clip_start
        if end <= start:
            continue

        for b_start, b_end, b_text in _split_long_segment(seg["text"].strip(), start, end):
            lines.append(str(idx))
            lines.append(f"{_format_srt_timestamp(b_start)} --> {_format_srt_timestamp(b_end)}")
            lines.append(b_text)
            lines.append("")
            idx += 1

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return srt_path


def _escape_path_for_ffmpeg(path):
    return path.replace("\\", "/").replace(":", "\\:")


def _get_video_dimensions(video_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        video_path,
    ]
    with stage('baca dimensi video'):
        result = subprocess.run(cmd, capture_output=True, text=True)
    width, height = result.stdout.strip().split("x")
    return int(width), int(height)


def _build_video_filter(source_path, start, end, orientation, quality, smart_reframe):
    """Susun rantai filter ffmpeg untuk crop/scale sesuai orientasi & kualitas."""
    out_w, out_h = RESOLUTIONS[(orientation, quality)]

    if orientation == "landscape":
        # Sumber sudah landscape: cukup scale, tidak perlu crop
        return [f"scale={out_w}:{out_h}"], out_w, out_h

    # Portrait: crop kolom 9:16 dari sumber landscape
    frame_w, frame_h = _get_video_dimensions(source_path)
    crop_w = frame_h * 9 / 16

    if crop_w >= frame_w:
        # Sumber sudah portrait/sempit, tidak perlu crop horizontal
        return [f"scale={out_w}:{out_h}"], out_w, out_h

    crop_x_expr = None
    if smart_reframe:
        with stage('deteksi wajah dan hitung crop'):
            crop_x_expr = get_smart_crop_x_expression(source_path, start, end, crop_w)

    if crop_x_expr:
        # Crop mengikuti posisi wajah dominan (x dinamis)
        crop_filter = f"crop='min(iw,ih*9/16)':'ih':x='{crop_x_expr}':y=0"
    else:
        # Fallback: crop tengah statis
        crop_filter = "crop='min(iw,ih*9/16)':'ih':x='(iw-min(iw,ih*9/16))/2':y=0"

    return [crop_filter, f"scale={out_w}:{out_h}"], out_w, out_h


def cut_and_reformat_clip(
    source_path,
    start,
    end,
    output_path,
    segments=None,
    orientation="portrait",
    quality="1080",
    burn_subtitle=True,
    smart_reframe=True,
):
    """
    Memotong video [start, end] lalu memformatnya sesuai pilihan user.

    orientation    : "portrait" (9:16) atau "landscape" (16:9)
    quality        : "720" atau "1080"
    burn_subtitle  : True untuk menanam subtitle ke video
    smart_reframe  : True untuk crop mengikuti wajah (hanya berlaku di portrait)
    """
    if (orientation, quality) not in RESOLUTIONS:
        raise ValueError(f"Kombinasi orientasi/kualitas tidak didukung: {orientation}/{quality}")

    duration = end - start

    with stage('persiapan filter (termasuk deteksi wajah)'):
        vf_parts, _, _ = _build_video_filter(
            source_path, start, end, orientation, quality, smart_reframe
        )

    if burn_subtitle and segments:
        srt_path = os.path.splitext(output_path)[0] + ".srt"
        with stage('pembuatan subtitle'):
            generate_srt_for_clip(segments, start, end, srt_path)

        escaped_srt = _escape_path_for_ffmpeg(srt_path)
        font_size = SUBTITLE_FONT_SIZE.get(quality, 18)
        style = (
            f"FontName=Arial,FontSize={font_size},PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,"
            "Alignment=2,MarginV=80"
        )
        vf_parts.append(f"subtitles='{escaped_srt}':force_style='{style}'")

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-i", source_path,
        "-t", str(duration),
        "-vf", ",".join(vf_parts),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-movflags", "+faststart",
        output_path,
    ]

    with stage('ekspor FFmpeg'):
        result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg gagal memproses klip: {result.stderr[-800:]}")

    return output_path
