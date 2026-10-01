"""
Smart reframe: menentukan area pemotongan 9:16 yang mengikuti pembicara dominan.

METODE DETEKSI
Menggunakan detektor wajah berbasis DNN (OpenCV res10 SSD) yang dijalankan
multi-skala: pada keseluruhan frame dan pada beberapa potongan persegi yang
saling bertumpang tindih. Pendekatan potongan persegi ini penting karena
detektor menskalakan masukan menjadi bujur sangkar -- frame 16:9 yang langsung
diskalakan akan membuat wajah tergencet secara horizontal dan gagal terdeteksi.
Jika berkas model DNN tidak tersedia, sistem otomatis memakai Haar cascade
bawaan OpenCV sebagai cadangan.

PERILAKU PEMBINGKAIAN
Area potong MENAHAN posisi pada satu orang, lalu berpindah cepat ketika subjek
dominan berganti secara konsisten. Ini menghindari pergeseran terus-menerus
yang membuat video terasa goyang.

KETERBATASAN
Ini bukan speaker diarization berbasis audio. Wajah dengan kotak terbesar
dipakai sebagai perkiraan pembicara utama.
"""

import os
import cv2
import numpy as np

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
PROTO_PATH = os.path.join(MODEL_DIR, "deploy.prototxt")
CAFFE_PATH = os.path.join(MODEL_DIR, "res10.caffemodel")

SAMPLE_INTERVAL_SECONDS = 0.5
NET_INPUT_SIZE = 640
CONFIDENCE_THRESHOLD = 0.45
TILE_OVERLAP = 0.3
SWITCH_CONFIRM_SAMPLES = 2
SWITCH_MIN_DISTANCE_RATIO = 0.10
TRANSITION_SECONDS = 0.35

_net = None
_haar = None


def _get_net():
    """Muat model DNN sekali saja. Return None kalau berkas model tidak ada."""
    global _net
    if _net is None:
        if os.path.exists(PROTO_PATH) and os.path.exists(CAFFE_PATH):
            _net = cv2.dnn.readNetFromCaffe(PROTO_PATH, CAFFE_PATH)
        else:
            _net = False
    return _net or None


def _get_haar():
    global _haar
    if _haar is None:
        _haar = cv2.CascadeClassifier(
            os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        )
    return _haar


def _dnn_on_region(net, region, offset_x):
    """Jalankan detektor pada satu potongan gambar, kembalikan kotak dalam koordinat frame penuh."""
    h, w = region.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(region, (NET_INPUT_SIZE, NET_INPUT_SIZE)),
        1.0, (NET_INPUT_SIZE, NET_INPUT_SIZE), (104.0, 177.0, 123.0)
    )
    net.setInput(blob)
    det = net.forward()

    boxes = []
    for i in range(det.shape[2]):
        conf = float(det[0, 0, i, 2])
        if conf < CONFIDENCE_THRESHOLD:
            continue
        x1, y1, x2, y2 = det[0, 0, i, 3:7] * np.array([w, h, w, h])
        boxes.append((conf, x1 + offset_x, y1, x2 + offset_x, y2))
    return boxes


def _deduplicate(boxes, min_distance):
    """Gabungkan kotak yang saling berdekatan (hasil tumpang tindih antar potongan)."""
    kept = []
    for box in sorted(boxes, key=lambda b: -b[0]):
        cx = (box[1] + box[3]) / 2
        if all(abs(cx - (k[1] + k[3]) / 2) > min_distance for k in kept):
            kept.append(box)
    return kept


def detect_faces(frame):
    """
    Deteksi wajah pada satu frame secara multi-skala.
    Return list (confidence, x1, y1, x2, y2) dalam koordinat piksel frame.
    """
    h, w = frame.shape[:2]
    net = _get_net()

    if net is not None:
        boxes = _dnn_on_region(net, frame, 0)

        if w > h:
            size = h
            step = size * (1 - TILE_OVERLAP)
            x = 0.0
            while True:
                x1 = int(min(x, max(0, w - size)))
                x2 = min(x1 + size, w)
                boxes += _dnn_on_region(net, frame[:, x1:x2], x1)
                if x2 >= w:
                    break
                x += step

        return _deduplicate(boxes, w * 0.05)

    gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    min_size = max(40, int(h * 0.06))
    return [
        (0.5, float(x), float(y), float(x + fw), float(y + fh))
        for (x, y, fw, fh) in _get_haar().detectMultiScale(gray, 1.1, 5, minSize=(min_size, min_size))
    ]


def sample_dominant_faces(source_path, clip_start, clip_end, on_sample=None):
    """
    Sample video secara berkala, ambil posisi x wajah terbesar tiap sample.
    on_sample: callback opsional (waktu, jumlah_wajah, pusat_x) untuk diagnosa.
    """
    cap = cv2.VideoCapture(source_path)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    samples = []
    t = clip_start
    while t < clip_end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if ok:
            faces = detect_faces(frame)
            center_x = None
            if faces:
                largest = max(faces, key=lambda f: (f[3] - f[1]) * (f[4] - f[2]))
                center_x = (largest[1] + largest[3]) / 2
                samples.append((round(t - clip_start, 2), center_x))
            if on_sample:
                on_sample(t, len(faces), center_x)
        t += SAMPLE_INTERVAL_SECONDS

    cap.release()
    return samples, frame_w, frame_h


def build_hold_segments(samples, frame_w):
    """Ubah sample mentah jadi segmen di mana posisi potong ditahan."""
    if not samples:
        return []

    min_distance = frame_w * SWITCH_MIN_DISTANCE_RATIO
    segments = [(samples[0][0], samples[0][1])]
    current_x = samples[0][1]
    candidate_x = None
    candidate_count = 0
    candidate_time = None

    for t, cx in samples[1:]:
        if abs(cx - current_x) < min_distance:
            candidate_x = None
            candidate_count = 0
            continue

        if candidate_x is not None and abs(cx - candidate_x) < min_distance:
            candidate_count += 1
        else:
            candidate_x = cx
            candidate_count = 1
            candidate_time = t

        if candidate_count >= SWITCH_CONFIRM_SAMPLES:
            current_x = candidate_x
            segments.append((candidate_time, current_x))
            candidate_x = None
            candidate_count = 0

    return segments


def build_crop_x_expression(segments, crop_w, frame_w):
    """Bangun ekspresi ffmpeg: posisi ditahan per segmen, transisi cepat saat berpindah."""
    if not segments:
        return f"{(frame_w - crop_w) / 2:.1f}"

    def clamp(center_x):
        return max(0.0, min(center_x - crop_w / 2, frame_w - crop_w))

    points = [(t, clamp(cx)) for t, cx in segments]

    if len(points) == 1:
        return f"{points[0][1]:.1f}"

    expr = f"{points[-1][1]:.1f}"
    for i in range(len(points) - 1, 0, -1):
        t_switch, x_new = points[i]
        x_prev = points[i - 1][1]
        t_end = t_switch + TRANSITION_SECONDS
        ramp = (
            f"({x_prev:.1f}+({x_new:.1f}-{x_prev:.1f})"
            f"*(t-{t_switch:.2f})/{TRANSITION_SECONDS:.2f})"
        )
        expr = f"if(lt(t,{t_switch:.2f}),{x_prev:.1f},if(lt(t,{t_end:.2f}),{ramp},{expr}))"

    return expr


def get_smart_crop_x_expression(source_path, clip_start, clip_end, crop_w):
    """
    Dipanggil dari clipper.py. Return ekspresi ffmpeg untuk posisi x area potong,
    atau None kalau tidak ada wajah terdeteksi sama sekali (caller akan memakai
    pemotongan tengah statis).
    """
    samples, frame_w, _ = sample_dominant_faces(source_path, clip_start, clip_end)
    if not samples:
        return None

    segments = build_hold_segments(samples, frame_w)
    return build_crop_x_expression(segments, crop_w, frame_w)
