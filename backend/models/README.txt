Folder ini berisi model deteksi wajah untuk fitur smart reframe.

- deploy.prototxt    : definisi arsitektur jaringan
- res10.caffemodel   : bobot model (OpenCV res10 SSD face detector)

Jika kedua berkas ini tidak ada, sistem otomatis memakai Haar cascade bawaan
OpenCV sebagai cadangan, dengan akurasi yang lebih rendah.

Untuk mengunduh ulang:
  curl -L -o models/deploy.prototxt https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt
  curl -L -o models/res10.caffemodel https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel
