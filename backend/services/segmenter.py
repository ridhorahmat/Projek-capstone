"""
Tahap 3: Kirim transkrip ke LLM (Claude) untuk mencari bagian paling menarik,
lalu kembalikan beberapa rentang waktu (timestamp) yang layak dijadikan klip pendek.
"""

import json
import os
from anthropic import Anthropic

MAX_CLIPS = 5
MIN_CLIP_SECONDS = 20
MAX_CLIP_SECONDS = 90


def _format_transcript(segments: list[dict]) -> str:
    lines = []
    for seg in segments:
        lines.append(f'[{seg["start"]:.1f}-{seg["end"]:.1f}] {seg["text"]}')
    return "\n".join(lines)


def _fallback_segments(segments: list[dict]) -> list[dict]:
    """
    Mode gratis tanpa AI: bagi video jadi beberapa bagian dengan jarak rata,
    lalu ambil potongan berdurasi tetap dari tiap bagian. Ini bukan pemilihan
    'momen menarik' yang sesungguhnya -- cuma buat testing pipeline download,
    transkrip, dan pemotongan video tanpa perlu API key berbayar.
    """
    if not segments:
        return []

    total_duration = segments[-1]["end"]
    num_clips = min(MAX_CLIPS, 3)
    clip_length = min(MAX_CLIP_SECONDS, max(MIN_CLIP_SECONDS, 30))

    clips = []
    for i in range(num_clips):
        start = (total_duration / (num_clips + 1)) * (i + 1)
        end = min(start + clip_length, total_duration)
        if end - start < MIN_CLIP_SECONDS:
            continue
        clips.append({
            "start": round(start, 1),
            "end": round(end, 1),
            "title": f"Klip {i + 1} (mode gratis)",
            "reason": "Dipilih otomatis secara merata -- bukan hasil analisis AI. "
                      "Isi ANTHROPIC_API_KEY di .env untuk pemilihan momen menarik yang sesungguhnya.",
        })
    return clips


def find_highlight_segments(segments: list[dict]) -> list[dict]:
    """
    Mengembalikan list klip terpilih:
    [{"start": float, "end": float, "title": str, "reason": str}, ...]

    Kalau ANTHROPIC_API_KEY belum diisi, otomatis pakai mode gratis
    (pembagian merata, bukan pemilihan momen menarik oleh AI).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_key_here":
        return _fallback_segments(segments)

    client = Anthropic(api_key=api_key)
    transcript_text = _format_transcript(segments)

    prompt = f"""Kamu adalah editor video yang ahli mencari momen menarik dari podcast untuk dijadikan klip pendek media sosial (TikTok/Reels/Shorts).

Berikut transkrip podcast dengan timestamp dalam format [mulai-selesai] teks:

{transcript_text}

Tugas kamu: pilih maksimal {MAX_CLIPS} segmen paling menarik untuk dijadikan klip pendek. Kriteria momen menarik: ada pernyataan kuat/kontroversial, insight yang berharga, cerita lucu, atau jawaban yang mengejutkan.

Aturan:
- Setiap klip durasinya antara {MIN_CLIP_SECONDS} sampai {MAX_CLIP_SECONDS} detik.
- Gunakan timestamp asli dari transkrip (jangan mengarang angka).
- Klip harus utuh secara makna, jangan motong di tengah kalimat penting.

Jawab HANYA dalam format JSON array seperti ini, tanpa teks tambahan apapun:
[
  {{"start": 12.3, "end": 45.6, "title": "Judul singkat klip", "reason": "Kenapa ini menarik"}}
]
"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        clips = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gagal parsing hasil AI jadi JSON: {e}\nOutput mentah: {raw_text}")

    return clips