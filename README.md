# Short Clipper

Web app yang mengubah video podcast YouTube jadi beberapa klip pendek untuk media sosial secara otomatis, menggunakan AI untuk mencari momen paling menarik.

## Alur kerja

1. User tempel link YouTube di frontend
2. Backend download video (`yt-dlp`)
3. Backend transkrip audio jadi teks (`Whisper`)
4. Transkrip dikirim ke Claude (Anthropic API) untuk cari momen menarik
5. Video dipotong sesuai momen tersebut dan di-crop ke rasio vertikal 9:16 (`ffmpeg`)
6. Frontend menampilkan daftar klip yang bisa diunduh

## Yang perlu disiapkan di komputer kamu

- Python 3.10 atau lebih baru
- **ffmpeg** terinstall di sistem (bukan cuma library Python)
  - Windows: download dari ffmpeg.org, lalu tambahkan ke PATH
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- API key dari [console.anthropic.com](https://console.anthropic.com) (untuk fitur cari momen menarik)

## Cara menjalankan

### 1. Setup backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# lalu buka file .env dan isi ANTHROPIC_API_KEY dengan API key kamu

uvicorn main:app --reload --port 8000
```

Backend akan jalan di `http://localhost:8000`

### 2. Jalankan frontend

Cukup buka file `frontend/index.html` langsung di browser (double click), atau jalankan server statis sederhana:

```bash
cd frontend
python -m http.server 5500
```

Lalu buka `http://localhost:5500` di browser.

## Batasan versi MVP ini

- Diproses secara langsung/synchronous — untuk video panjang, request bisa memakan waktu beberapa menit, dan browser akan menunggu sampai selesai. Untuk penggunaan produksi/banyak user sekaligus, sebaiknya dipindah ke background job (misal pakai Celery + Redis) supaya user tidak perlu menunggu di satu halaman.
- Crop ke rasio vertikal masih crop tengah polos — belum ada deteksi wajah otomatis untuk memastikan subjek video tetap terlihat.
- Belum ada subtitle otomatis (burn-in caption) di video hasil potongan.
- Belum ada sistem user/login — semua orang yang punya akses ke URL backend bisa memakai API ini, jadi untuk publik perlu ditambah rate-limiting dan autentikasi dulu.
- Model Whisper `base` cukup ringan tapi kurang akurat untuk audio berisik — bisa dinaikkan ke `small`/`medium` di file `.env` kalau butuh akurasi lebih baik (tapi lebih lambat).

## Langkah selanjutnya (kalau mau dikembangkan lagi)

1. Tambah subtitle otomatis yang di-burn ke video
2. Ganti proses synchronous jadi background job + halaman status/progress
3. Tambah sistem akun & riwayat video yang sudah diproses
4. Baru masuk tahap deploy ke server (Railway/Render/VPS) supaya bisa diakses publik
