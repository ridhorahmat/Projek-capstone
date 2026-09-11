"""
Tahap 3: Kirim transkrip ke LLM (Gemini) untuk mencari bagian paling menarik,
lalu kembalikan beberapa rentang waktu (timestamp) yang layak dijadikan klip pendek.
"""

import json
import os
import google.generativeai as genai

MAX_CLIPS = 5
MIN_CLIP_SECONDS = 20
MAX_CLIP_SECONDS = 90


def _format_transcript(segments: list[dict]) -> str:
    lines = []
    for seg in segments:
        lines.append(f'[{seg["start"]:.1f}-{seg["end"]:.1f}] {seg["text"]}')
    return "\n".join(lines)


def _fallback_segments(segments: list[dict]) -> list[dict]:
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
                      "Isi GEMINI_API_KEY di .env untuk pemilihan momen menarik yang sesungguhnya.",
            "virality_score": None,
        })
    return clips


def find_highlight_segments(segments: list[dict]) -> list[dict]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_key_here":
        return _fallback_segments(segments)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    transcript_text = _format_transcript(segments)

    prompt = f"""Kamu adalah content strategist profesional yang spesialis membuat klip pendek viral (TikTok/Reels/Shorts) dari podcast panjang. Kamu paham betul pola konten yang membuat orang berhenti scroll dan menonton sampai habis.

Berikut transkrip podcast dengan timestamp dalam format [mulai-selesai] teks:

{transcript_text}

TUGAS:
Analisis transkrip ini dan pilih maksimal {MAX_CLIPS} segmen dengan potensi paling viral untuk dijadikan klip pendek.

KRITERIA WAJIB untuk tiap klip yang dipilih:
1. **Hook kuat di 3-5 detik pertama** -- kalimat pembuka klip harus langsung menarik perhatian (pertanyaan provokatif, pernyataan mengejutkan, atau klaim berani). JANGAN pilih klip yang mulai dengan basa-basi atau kalimat pengantar yang lambat.
2. **Cerita/argumen utuh** -- klip harus punya awal-tengah-akhir yang jelas (setup dan payoff/punchline), jangan terpotong di tengah pemikiran.
3. **Nilai emosional atau intelektual yang kuat** -- pilih dari kategori berikut:
   - Kontroversial/berani (pendapat yang memicu perdebatan)
   - Plot twist/mengejutkan (jawaban di luar dugaan)
   - Actionable insight (tips/wawasan yang bisa langsung dipakai penonton)
   - Emosional (cerita personal yang related/menyentuh)
   - Humor (momen lucu yang natural, bukan dipaksakan)
4. **Self-contained** -- penonton harus paham konteksnya tanpa perlu nonton video aslinya.

Setiap klip durasinya antara {MIN_CLIP_SECONDS} sampai {MAX_CLIP_SECONDS} detik. Gunakan timestamp asli dari transkrip (jangan mengarang angka).

Untuk tiap klip, berikan:
- "virality_score": angka 1-10 (seberapa besar potensi viral, 10 = paling tinggi)
- "category": salah satu dari [kontroversial, plot_twist, actionable_insight, emosional, humor]
- "hook": kalimat pembuka klip (harus persis dari transkrip, ini yang menentukan apakah orang berhenti scroll)
- "title": judul singkat untuk klip
- "reason": alasan spesifik kenapa ini berpotensi viral

Urutkan hasil dari virality_score TERTINGGI ke terendah. Jawab HANYA dalam format JSON array seperti ini, tanpa teks tambahan apapun, tanpa markdown code block:
[
  {{
    "start": 12.3,
    "end": 45.6,
    "title": "Judul singkat klip",
    "hook": "Kalimat pembuka yang jadi hook",
    "category": "plot_twist",
    "virality_score": 8,
    "reason": "Alasan spesifik kenapa ini menarik"
  }}
]
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        clips = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gagal parsing hasil AI jadi JSON: {e}\nOutput mentah: {raw_text}")

    clips.sort(key=lambda c: c.get("virality_score", 0), reverse=True)

    return clips