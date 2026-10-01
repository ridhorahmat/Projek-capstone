"""
Tahap 3: Mengirim transkrip ke LLM untuk mencari bagian paling menarik,
lalu mengembalikan beberapa rentang waktu yang layak dijadikan klip pendek.
Jumlah klip dan rentang durasi dapat ditentukan pengguna.
"""

import json
import os

import google.generativeai as genai

CLIP_COUNT_RANGE = (1, 10)
CLIP_DURATION_RANGE = (10, 180)


def _format_transcript(segments):
    return "\n".join(
        f'[{seg["start"]:.1f}-{seg["end"]:.1f}] {seg["text"]}' for seg in segments
    )


def _clamp(value, low, high):
    return max(low, min(value, high))


def _fallback_segments(segments, max_clips, min_seconds, max_seconds):
    """Mode tanpa AI: membagi video dengan jarak merata."""
    if not segments:
        return []

    total_duration = segments[-1]["end"]
    clip_length = min(max_seconds, max(min_seconds, 30))

    clips = []
    for i in range(max_clips):
        start = (total_duration / (max_clips + 1)) * (i + 1)
        end = min(start + clip_length, total_duration)
        if end - start < min_seconds:
            continue
        clips.append({
            "start": round(start, 1),
            "end": round(end, 1),
            "title": f"Klip {i + 1} (mode tanpa AI)",
            "hook": "",
            "category": "",
            "virality_score": None,
            "reason": "Dipilih dengan pembagian merata, bukan hasil analisis. "
                      "Isi GEMINI_API_KEY pada berkas .env untuk seleksi berbasis makna.",
        })
    return clips


def find_highlight_segments(segments, max_clips=5, min_seconds=20, max_seconds=90):
    max_clips = int(_clamp(max_clips, *CLIP_COUNT_RANGE))
    min_seconds = int(_clamp(min_seconds, *CLIP_DURATION_RANGE))
    max_seconds = int(_clamp(max_seconds, *CLIP_DURATION_RANGE))
    if max_seconds <= min_seconds:
        max_seconds = min(min_seconds + 10, CLIP_DURATION_RANGE[1])

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_key_here":
        print(f"[segmenter] MODE TANPA AI — kunci terbaca: {bool(api_key)}, "
              f"awalan: {api_key[:4] if api_key else None}")
        return _fallback_segments(segments, max_clips, min_seconds, max_seconds)

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    print(f"[segmenter] MODE AI — model: {model_name}")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    transcript_text = _format_transcript(segments)

    prompt = f"""Kamu adalah content strategist yang ahli membuat klip pendek dari podcast panjang untuk TikTok, Instagram Reels, dan YouTube Shorts.

Berikut transkrip podcast dengan penanda waktu dalam format [mulai-selesai] teks:

{transcript_text}

TUGAS:
Pilih {max_clips} segmen dengan potensi paling kuat untuk dijadikan klip pendek.

SYARAT DURASI (WAJIB DIPATUHI):
Setiap klip harus berdurasi antara {min_seconds} sampai {max_seconds} detik.
Jangan menghasilkan klip di luar rentang ini.

SYARAT ISI:
1. Kalimat pembuka klip harus langsung menarik perhatian dalam 3 sampai 5 detik pertama. Hindari memulai klip dari basa-basi atau kalimat pengantar yang lambat.
2. Klip harus utuh secara makna, memiliki awal dan penutup yang jelas, dan tidak terpotong di tengah gagasan.
3. Klip harus memiliki muatan yang kuat, yaitu salah satu dari: pendapat kontroversial, hal mengejutkan, wawasan yang bisa langsung dipakai, cerita yang menyentuh, atau humor yang wajar.
4. Penonton harus paham isinya tanpa perlu menonton video aslinya.

Gunakan penanda waktu asli dari transkrip, jangan mengarang angka.

Untuk setiap klip berikan:
- "virality_score": angka 1 sampai 10
- "category": salah satu dari [kontroversial, plot_twist, actionable_insight, emosional, humor]
- "hook": kalimat pembuka klip, disalin persis dari transkrip
- "title": judul singkat
- "reason": alasan spesifik mengapa klip ini berpotensi

Urutkan dari virality_score tertinggi. Jawab HANYA dengan JSON array, tanpa teks lain dan tanpa penanda blok kode:
[
  {{"start": 12.3, "end": 45.6, "title": "Judul singkat", "hook": "Kalimat pembuka", "category": "plot_twist", "virality_score": 8, "reason": "Alasan"}}
]
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()

    try:
        clips = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gagal membaca hasil AI sebagai JSON: {e}\nKeluaran mentah: {raw_text}")

    valid = []
    for c in clips:
        try:
            duration = float(c["end"]) - float(c["start"])
        except (KeyError, TypeError, ValueError):
            continue
        if min_seconds - 2 <= duration <= max_seconds + 2:
            valid.append(c)

    if not valid:
        valid = [c for c in clips if "start" in c and "end" in c]

    valid.sort(key=lambda c: c.get("virality_score") or 0, reverse=True)
    return valid[:max_clips]