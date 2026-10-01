"""
Tahap 2: Transkripsi audio ke teks menggunakan Whisper (jalan lokal, tanpa internet).
Hasilnya berupa list segmen teks lengkap dengan timestamp mulai & selesai.
"""

import whisper

_model_cache = {}


def _get_model(model_name: str):
    """Load model Whisper sekali saja lalu simpan di cache (biar tidak load ulang tiap request)."""
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]


def transcribe(video_path: str, model_name: str = "base") -> list[dict]:
    """
    Mengembalikan list segmen: [{"start": float, "end": float, "text": str}, ...]
    """
    model = _get_model(model_name)
    result = model.transcribe(video_path, verbose=False)

    return [
        {
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
        }
        for seg in result["segments"]
    ]
