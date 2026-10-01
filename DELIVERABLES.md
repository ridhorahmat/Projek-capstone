# Pelacak Deliverable Capstone — Short Clipper

Disusun berdasarkan RPS Capstone Project (PG194) dan rubrik penilaiannya.

---

## Bobot penilaian vs status saat ini

| # | Aspek | Bobot | Status | Yang masih kurang |
|---|---|---|---|---|
| 1 | Identifikasi Masalah | 10% | Hampir siap | Kuesioner n=7 sudah ada; perlu ditulis jadi dokumen formal |
| 2 | Analisis Kebutuhan | 10% | Sebagian | Perlu daftar kebutuhan fungsional & non-fungsional yang tervalidasi stakeholder |
| 3 | Perancangan Solusi | 15% | Sebagian | Ada diagram alur; belum ada arsitektur sistem, ERD/struktur data, desain UI formal, WBS, analisis risiko |
| 4 | Implementasi Sistem | 20% | Berjalan | Fitur inti jalan; perlu bukti semua fitur sesuai spesifikasi |
| 5 | Pengujian dan Evaluasi | 10% | **Belum ada** | Unit testing, integration testing, UAT + analisis hasil |
| 6 | Dokumentasi Proyek | 10% | Sebagian | README ada; perlu dokumentasi teknis & manual pengguna |
| 7 | Laporan Akhir | 10% | **Belum ada** | Laporan ilmiah sistematis |
| 8 | Presentasi & Demonstrasi | 10% | **Belum ada** | Materi presentasi, poster, demo interaktif |
| 9 | Kerja Sama Tim | 5% | Perlu dicatat | Logbook mingguan + pembagian peran 3 anggota |

**Catatan penting:** implementasi hanya 20%. Aspek yang sama sekali belum
disentuh (pengujian, laporan akhir, presentasi) bernilai **30%** — lebih besar
daripada porsi ngoding.

---

## Peta 16 minggu (dari RPS)

| Minggu | Topik | Deliverable | Status |
|---|---|---|---|
| 1 | Pengantar Capstone | Pemahaman alur & etika | Selesai |
| 2 | Identifikasi Masalah | Rumusan masalah berbasis kebutuhan stakeholder | Draft ada |
| 3-4 | Perencanaan & Desain Solusi | Dokumen perancangan, WBS, jadwal, analisis risiko | **Prioritas terdekat** |
| 5-8 | Implementasi Fase 1 | Modul inti + dokumentasi teknis (milestone 1) | Sudah berjalan duluan |
| 9 | Evaluasi Proyek | Laporan kemajuan | Belum |
| 10-11 | Pengujian & Integrasi | Unit/Integration/UAT + issue tracking | Belum |
| 12-13 | Evaluasi & Perbaikan | Kuesioner pengguna, iterasi perbaikan | Belum (5 beta tester sudah bersedia) |
| 14-15 | Finalisasi & Dokumentasi | Laporan akhir, manual pengguna | Belum |
| 16 | Presentasi & Pameran | Presentasi, poster, demo | Belum |

---

## Yang perlu dikerjakan berikutnya (Minggu 3-4)

Sesuai RPS, minggu 3-4 menuntut tiga hal konkret:

**1. Metodologi pengembangan**
Pilih dan justifikasi: Waterfall, Agile, atau Prototyping. Untuk proyek ini
Prototyping/Agile lebih sesuai karena fitur berkembang berdasarkan umpan balik
(terbukti dari cara kerja kita sejauh ini: bangun, uji, perbaiki).

**2. Perancangan sistem**
- Arsitektur sistem (frontend - API - layanan pemrosesan - penyimpanan)
- Struktur data (job, klip, hasil transkrip)
- Desain antarmuka (UI/UX) — sudah ada implementasinya, perlu didokumentasikan
- Diagram alur proses (sudah ada, tinggal diformalkan)

**3. Manajemen proyek**
- WBS (Work Breakdown Structure) dengan pembagian tugas 3 anggota
- Jadwal proyek sampai minggu 16
- Analisis risiko + strategi mitigasi

Risiko nyata yang sudah terjadi dan layak dimasukkan ke analisis risiko:
- YouTube memblokir akses otomatis (mitigasi: update yt-dlp, cookies)
- Ketergantungan pada API pihak ketiga (mitigasi: mode fallback tanpa AI)
- Library berubah/usang — MediaPipe API dihapus (mitigasi: ganti ke OpenCV)
- Keterbatasan perangkat keras untuk transkripsi (mitigasi: pilihan model Whisper)

---

## Pembagian peran tim (usulan untuk WBS)

Karena kelompok terdiri dari 3 orang, rubrik menilai kontribusi merata:

| Peran | Tanggung jawab |
|---|---|
| Anggota 1 | Backend & pipeline pemrosesan video |
| Anggota 2 | Frontend, UI/UX, dokumentasi teknis |
| Anggota 3 | Riset pengguna, pengujian, laporan akhir |

Pembagian di atas hanya usulan — sesuaikan dengan kesepakatan tim, lalu catat
di logbook mingguan sebagai bukti kontribusi.

---

## Catatan yang perlu dikonfirmasi

RPS ini milik **Program Studi Sistem Informasi**. Pastikan ini memang RPS yang
berlaku untuk program studi kamu, karena rubrik dan CPMK bisa berbeda antar prodi.
