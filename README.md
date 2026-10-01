# Short Clipper

Aplikasi web yang mengubah video podcast YouTube menjadi klip pendek siap unggah
secara otomatis: mencari momen menarik, memotong, memformat ulang, dan menambahkan subtitle.

## Fitur

- Deteksi momen menarik otomatis menggunakan LLM (Gemini) + skor potensi viral
- Smart reframe: crop mengikuti wajah pembicara dominan (OpenCV)
- Pilihan orientasi: Portrait 9:16 atau Landscape 16:9
- Pilihan kualitas: 720p atau 1080p
- Subtitle otomatis yang bisa diaktifkan/nonaktifkan
- Preview klip langsung di browser sebelum diunduh

## Prasyarat

- Python 3.10–3.12 (3.11 disarankan)
- **ffmpeg** terinstall di sistem dan terdaftar di PATH
- API key Gemini dari aistudio.google.com/apikey (opsional — tanpa key, sistem
  berjalan dalam mode gratis dengan pembagian klip merata)

## Cara menjalankan

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env          # lalu isi GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```

### Frontend
Buka `frontend/index.html` di browser, atau:
```bash
cd frontend
python -m http.server 5500
```

## Catatan: YouTube bot detection

Jika muncul error "Sign in to confirm you're not a bot":
1. Update yt-dlp: `pip install --upgrade yt-dlp`
2. Jika masih gagal, export cookies YouTube ke file `backend/cookies.txt`
   (extension "Get cookies.txt LOCALLY"), sistem otomatis memakainya jika ada.

File `cookies.txt` berisi sesi login — jangan diunggah ke GitHub (sudah masuk .gitignore).

## Keterbatasan yang perlu didokumentasikan

- **Smart reframe bukan speaker diarization**: sistem memakai wajah terbesar sebagai
  proksi pembicara utama, bukan analisis audio. Pada wide shot statis dengan dua orang
  berukuran sama, sistem cenderung bertahan di satu orang.
- **Seleksi momen berbasis teks**: LLM hanya membaca transkrip, tidak menangkap
  ekspresi wajah, nada suara, atau timing visual. Hasil tetap perlu direview manusia.
- **Proses synchronous**: satu request menunggu sampai seluruh pipeline selesai.
  Untuk banyak user bersamaan, perlu dipindah ke background job (Celery/RQ).
