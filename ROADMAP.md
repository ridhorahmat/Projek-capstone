# Roadmap Short Clipper — Berbasis Hasil Kuesioner (n=7)

## Prinsip prioritas
Urutan dikerjakan berdasarkan **bukti dari responden**, bukan asumsi. Setiap item
di bawah mencantumkan dasar datanya.

---

## P0 — Sudah selesai

| Fitur | Dasar dari kuesioner |
|---|---|
| Deteksi momen menarik otomatis (LLM) | 7/7 responden menyebut "menonton ulang & mencari momen menarik" sebagai bagian paling melelahkan |
| Pemotongan otomatis + format vertikal 9:16 | 2/7 menyebut "mengubah ke format vertikal" memakan waktu |
| Subtitle otomatis (burn-in) | 2/7 menyebut "menambahkan subtitle" memakan waktu |
| Skor potensi viral + kategori | Mendukung prioritas #1 responden: akurasi memilih momen (4/7) |

---

## P1 — Diminta eksplisit oleh responden

| Fitur | Dasar dari kuesioner | Status |
|---|---|---|
| **Face tracking untuk podcast** | Diminta langsung di masukan terbuka | Sedang dikerjakan (OpenCV) |
| **Opsi resolusi**: portrait / landscape | Diminta langsung di masukan terbuka | Belum |
| **Opsi kualitas**: 720p / 1080p | Diminta langsung di masukan terbuka | Belum |
| **Subtitle on/off** | Diminta langsung di masukan terbuka | Belum |
| **Preview klip sebelum unduh** | Tidak diminta eksplisit, tapi mendukung "yg simple" | Belum |

---

## P2 — Peningkatan akurasi (prioritas #1 responden)

4 dari 7 responden memilih **"akurasi memilih momen menarik"** sebagai fitur
paling penting — mengalahkan kecepatan (1/7). Artinya usaha sebaiknya
diarahkan ke kualitas seleksi, bukan optimasi kecepatan.

- Perbaiki prompt seleksi (hook, struktur cerita, self-contained) — sudah diterapkan
- Tambah validasi otomatis: tolak klip yang terpotong di tengah kalimat
- Evaluasi manual: bandingkan pilihan AI vs pilihan manusia sebagai data pengujian laporan

---

## P3 — Pengembangan lanjutan (future work di laporan)

| Fitur | Catatan |
|---|---|
| Deteksi topik/keyword yang sedang tren | Diusulkan 1 responden; ia sendiri menilai ini masuk ranah personalisasi |
| Speaker diarization berbasis audio | Pengganti proksi "wajah terbesar" agar benar-benar mengikuti yang bicara |
| Subtitle animasi kata-per-kata | Meningkatkan keterbacaan tanpa suara |
| Caption & hashtag otomatis | Mempercepat proses posting |

---

## Catatan validitas untuk laporan
Jumlah responden (7) tergolong kecil. Hasil ini diposisikan sebagai
**indikasi awal kebutuhan**, bukan data yang dapat digeneralisasi ke seluruh
populasi kreator konten. Temuan terkuat yang layak dikutip adalah konsensus
7/7 pada pain point pencarian momen menarik.
