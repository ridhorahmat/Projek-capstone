"""
Alat diagnosa deteksi wajah.

Menjalankan detektor pada sebuah video dan melaporkan berapa banyak wajah yang
terdeteksi di setiap titik waktu, beserta posisinya. Gunakan ini untuk mengetahui
apakah fitur smart reframe benar-benar bekerja pada video tertentu, tanpa harus
menunggu seluruh pipeline selesai.

Cara pakai (dari folder backend, dengan venv aktif):

    python diagnose_faces.py "outputs/<job_id>/source.mp4"
    python diagnose_faces.py "outputs/<job_id>/source.mp4" --start 60 --end 90
    python diagnose_faces.py "outputs/<job_id>/source.mp4" --save-frames

Opsi --save-frames menyimpan gambar dengan kotak penanda wajah ke folder
diagnose_out/ supaya bisa dilihat langsung hasil deteksinya.
"""

import argparse
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.reframe import detect_faces, _get_net, SAMPLE_INTERVAL_SECONDS  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Diagnosa deteksi wajah pada video")
    parser.add_argument("video", help="path berkas video")
    parser.add_argument("--start", type=float, default=0.0, help="detik mulai")
    parser.add_argument("--end", type=float, default=30.0, help="detik selesai")
    parser.add_argument("--save-frames", action="store_true", help="simpan frame bertanda ke diagnose_out/")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Berkas tidak ditemukan: {args.video}")
        return

    detector = "DNN (res10)" if _get_net() is not None else "Haar cascade (cadangan)"
    print(f"Detektor yang dipakai : {detector}")

    cap = cv2.VideoCapture(args.video)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Resolusi video        : {frame_w}x{frame_h}")
    print(f"Rentang diperiksa     : {args.start:.1f}s - {args.end:.1f}s")
    print()
    print("  waktu   jumlah   posisi-x wajah (piksel)")
    print("  " + "-" * 48)

    if args.save_frames:
        os.makedirs("diagnose_out", exist_ok=True)

    total = 0
    with_face = 0
    t = args.start
    while t < args.end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break

        faces = detect_faces(frame)
        total += 1
        if faces:
            with_face += 1

        posisi = ", ".join(f"{(f[1] + f[3]) / 2:.0f}" for f in faces) or "-"
        print(f"  {t:6.1f}s  {len(faces):5}    {posisi}")

        if args.save_frames:
            marked = frame.copy()
            for conf, x1, y1, x2, y2 in faces:
                cv2.rectangle(marked, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 3)
                cv2.putText(marked, f"{conf:.2f}", (int(x1), int(y1) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.imwrite(f"diagnose_out/t_{t:06.1f}.jpg", marked)

        t += SAMPLE_INTERVAL_SECONDS

    cap.release()

    print()
    print(f"Ringkasan: {with_face} dari {total} sampel memiliki wajah terdeteksi", end="")
    if total:
        print(f" ({with_face / total * 100:.0f}%)")
    else:
        print()

    if total and with_face / total < 0.3:
        print()
        print("Tingkat deteksi rendah. Smart reframe kemungkinan besar akan kembali")
        print("ke pemotongan tengah. Jalankan ulang dengan --save-frames lalu periksa")
        print("gambar di folder diagnose_out/ untuk melihat kondisi frame-nya.")


if __name__ == "__main__":
    main()
