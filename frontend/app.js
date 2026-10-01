const API_BASE_URL = "http://localhost:8000";

const el = (id) => document.getElementById(id);

const analyzeForm = el("analyze-form");
const urlInput = el("youtube-url");
const analyzeBtn = el("analyze-btn");
const clipCount = el("clip-count");
const clipCountVal = el("clip-count-val");
const minDuration = el("min-duration");
const maxDuration = el("max-duration");

const stepAnalyze = el("step-analyze");
const stepSelect = el("step-select");
const candidatesTitle = el("candidates-title");
const candidatesGrid = el("candidates-grid");
const selectAll = el("select-all");
const selectedCount = el("selected-count");
const renderBtn = el("render-btn");
const backBtn = el("back-btn");
const reselectBtn = el("reselect-btn");

const statusEl = el("status");
const resultsEl = el("results");
const clipsGrid = el("clips-grid");
const optSubtitle = el("opt-subtitle");
const optReframe = el("opt-reframe");
const settingsSummary = el("settings-summary");

const CATEGORY_LABELS = {
  kontroversial: "Kontroversial",
  plot_twist: "Plot Twist",
  actionable_insight: "Insight",
  emosional: "Emosional",
  humor: "Humor",
};

let currentJob = null;
const selected = { orientation: "portrait", quality: "1080" };

clipCount.addEventListener("input", () => { clipCountVal.textContent = clipCount.value; });

document.querySelectorAll(".segmented").forEach((group) => {
  const name = group.dataset.name;
  group.querySelectorAll(".seg").forEach((btn) => {
    btn.addEventListener("click", () => {
      group.querySelectorAll(".seg").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selected[name] = btn.dataset.value;
      syncReframe();
    });
  });
});

function syncReframe() {
  const isLandscape = selected.orientation === "landscape";
  optReframe.disabled = isLandscape;
  optReframe.closest(".toggle").classList.toggle("disabled", isLandscape);
}
syncReframe();

function formatTimecode(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function showStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.remove("hidden", "error");
  if (isError) statusEl.classList.add("error");
}
const hideStatus = () => statusEl.classList.add("hidden");

function getCheckedIndexes() {
  return [...candidatesGrid.querySelectorAll("input[type=checkbox]:checked")]
    .map((c) => Number(c.dataset.index));
}

function updateSelectedCount() {
  const n = getCheckedIndexes().length;
  const total = candidatesGrid.querySelectorAll("input[type=checkbox]").length;
  selectedCount.textContent = `${n} dari ${total} dipilih`;
  renderBtn.disabled = n === 0;
}

function showSettingsSummary() {
  const orientasi = selected.orientation === "portrait" ? "Portrait 9:16" : "Landscape 16:9";
  const bagian = [orientasi, `${selected.quality}p`];
  if (optSubtitle.checked) bagian.push("subtitle");
  if (optReframe.checked && selected.orientation === "portrait") bagian.push("ikuti wajah");
  settingsSummary.textContent = `Pengaturan: ${bagian.join(" · ")} — ubah lewat "Ganti video"`;
}

function renderCandidates(data) {
  currentJob = data.job_id;
  candidatesTitle.textContent = data.video_title;
  candidatesGrid.innerHTML = "";

  data.candidates.forEach((c) => {
    const card = document.createElement("label");
    card.className = "candidate-card";

    const score = c.virality_score != null
      ? `<span class="badge badge-score">${c.virality_score}/10</span>` : "";
    const cat = c.category
      ? `<span class="badge badge-category">${CATEGORY_LABELS[c.category] || c.category}</span>` : "";
    const hook = c.hook ? `<p class="clip-hook">"${c.hook}"</p>` : "";

    card.innerHTML = `
      <div class="candidate-head">
        <input type="checkbox" data-index="${c.index}" checked>
        <span class="clip-timecode">${formatTimecode(c.start)} — ${formatTimecode(c.end)} · ${c.duration}s</span>
      </div>
      <div class="badges">${score}${cat}</div>
      <h3>${c.title}</h3>
      ${hook}
      <p class="reason">${c.reason}</p>
      <details class="transcript">
        <summary>Lihat transkrip</summary>
        <p>${c.transcript}</p>
      </details>
    `;
    candidatesGrid.appendChild(card);
  });

  candidatesGrid.querySelectorAll("input[type=checkbox]").forEach((cb) => {
    cb.addEventListener("change", updateSelectedCount);
  });

  selectAll.checked = true;
  updateSelectedCount();
  showSettingsSummary();

  stepAnalyze.classList.add("hidden");
  stepSelect.classList.remove("hidden");
  resultsEl.classList.add("hidden");
}

selectAll.addEventListener("change", () => {
  candidatesGrid.querySelectorAll("input[type=checkbox]").forEach((cb) => {
    cb.checked = selectAll.checked;
  });
  updateSelectedCount();
});

function renderResults(data) {
  // Bersihkan video dari hasil sebelumnya.
  clipsGrid.querySelectorAll("video").forEach(video => {
    video.pause();
    video.removeAttribute("src");
    video.load();
  });

  clipsGrid.replaceChildren();

  const portrait = data.settings?.orientation !== "landscape";
  const videos = [];

  data.clips.forEach(clip => {
    const card = document.createElement("div");
    card.className = "clip-card";

    // Video ini dipakai oleh pemutar biasa dan bingkai 3D.
    const video = document.createElement("video");

    video.className =
      `clip-preview ${portrait ? "portrait" : "landscape"}`;

    // Diperlukan agar video dapat digunakan sebagai tekstur 3D.
    // Harus ditetapkan sebelum src.
    video.crossOrigin = "anonymous";

    video.controls = true;
    video.playsInline = true;
    video.preload =
  document.documentElement.classList.contains("mode-ringan")
    ? "metadata"
    : "auto";
    video.src = `${API_BASE_URL}${clip.download_url}`;

    videos.push(video);

    const time = document.createElement("p");
    time.className = "clip-timecode";
    time.textContent =
      `${formatTimecode(clip.start)} - ${formatTimecode(clip.end)}`;

    const title = document.createElement("h3");
    title.textContent = clip.title || "Klip";

    const badges = document.createElement("div");
    badges.className = "badges";

    const badgeData = [
      [
        clip.virality_score == null
          ? ""
          : `${clip.virality_score}/10`,
        "badge-score"
      ],
      [
        CATEGORY_LABELS[clip.category] || clip.category || "",
        "badge-category"
      ]
    ];

    badgeData.forEach(([text, type]) => {
      if (!text) return;

      const badge = document.createElement("span");
      badge.className = `badge ${type}`;
      badge.textContent = text;

      badges.append(badge);
    });

    const download = document.createElement("a");
    download.className = "download-link";
    download.href = video.src;
    download.download = "";
    download.target = "_blank";
    download.rel = "noopener";
    download.textContent = "Unduh klip";

    // Hanya satu video yang bersuara pada satu waktu.
    video.addEventListener("play", () => {
      videos.forEach(other => {
        if (other !== video) other.pause();
      });
    });

    video.addEventListener("error", () => {
      showStatus(
        "Video tidak dapat dimuat. Periksa koneksi backend dan berkas klip.",
        true
      );
    });

    card.append(video, time, badges, title, download);
    clipsGrid.append(card);
  });

  resultsEl.classList.remove("hidden");

  // Kirim daftar video kepada background 3D.
  window.shortClipperVideos = videos;
  window.dispatchEvent(new Event("shortclipper:videos"));
}
analyzeForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const youtubeUrl = urlInput.value.trim();
  if (!youtubeUrl) return;

  const minVal = Number(minDuration.value);
  const maxVal = Number(maxDuration.value);
  if (maxVal <= minVal) {
    showStatus("Durasi maksimum harus lebih besar dari durasi minimum.", true);
    return;
  }

  analyzeBtn.disabled = true;
  showStatus("Mengunduh dan menganalisis video... proses ini bisa memakan waktu beberapa menit.");

  try {
    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        youtube_url: youtubeUrl,
        clip_count: Number(clipCount.value),
        min_duration: minVal,
        max_duration: maxVal,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Terjadi kesalahan saat menganalisis video.");

    hideStatus();
    renderCandidates(data);
  } catch (err) {
    showStatus(err.message, true);
  } finally {
    analyzeBtn.disabled = false;
  }
});

renderBtn.addEventListener("click", async () => {
  const chosen = getCheckedIndexes();
  if (!chosen.length || !currentJob) return;

  renderBtn.disabled = true;
  showStatus(`Memotong ${chosen.length} klip...`);

  try {
    const res = await fetch(`${API_BASE_URL}/api/render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_id: currentJob,
        selected: chosen,
        orientation: selected.orientation,
        quality: selected.quality,
        burn_subtitle: optSubtitle.checked,
        smart_reframe: optReframe.checked && selected.orientation === "portrait",
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Terjadi kesalahan saat memotong klip.");

    hideStatus();
    renderResults(data);
  } catch (err) {
    showStatus(err.message, true);
  } finally {
    renderBtn.disabled = false;
  }
});

backBtn.addEventListener("click", () => {
  stepSelect.classList.add("hidden");
  resultsEl.classList.add("hidden");
  stepAnalyze.classList.remove("hidden");
  hideStatus();
});

reselectBtn.addEventListener("click", () => {
  resultsEl.classList.add("hidden");
  stepSelect.classList.remove("hidden");
});

/* ===== BACKGROUND RUANG 3D ===== */
(async () => {
  // Pilih mode ringan saat halaman dibuka.
  const modeRingan = window.matchMedia(
    "(max-width: 900px), " +
    "(hover: none), " +
    "(pointer: coarse), " +
    "(prefers-reduced-motion: reduce)"
  ).matches;

  document.documentElement.classList.toggle(
    "mode-ringan",
    modeRingan
  );

  // Berhenti sebelum memuat Three.js dan membuat dunia 3D.
  if (modeRingan) return;

  if (document.getElementById("studio-bg-3d")) return;

  let renderer;

  try {
    // Memuat Three.js.
    const THREE = await import(
      "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js"
    );

    const reduced = matchMedia(
      "(prefers-reduced-motion: reduce)"
    );

    const pointer = new THREE.Vector2();

    // Dunia 3D dan kabut untuk memperlihatkan kedalaman.
    const scene = new THREE.Scene();

    scene.background = new THREE.Color("#070d17");
    scene.fog = new THREE.FogExp2("#070d17", 0.025);

    // Kamera melihat ke dalam lorong.
    const camera = new THREE.PerspectiveCamera(
      55,
      innerWidth / innerHeight,
      0.1,
      120
    );

    camera.position.set(0, 1.2, 12);

    // Membuat kanvas background secara otomatis.
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "low-power"
    });

    renderer.domElement.id = "studio-bg-3d";
    renderer.domElement.setAttribute("aria-hidden", "true");

    renderer.setPixelRatio(
      Math.min(devicePixelRatio || 1, 1.5)
    );

    renderer.setSize(innerWidth, innerHeight);

    document.body.prepend(renderer.domElement);

    // Pencahayaan ruangan.
    scene.add(
      new THREE.HemisphereLight(
        0x8daeff,
        0x070b12,
        1.1
      )
    );

    const amber = new THREE.PointLight(
      0xffae45,
      60,
      60
    );

    amber.position.set(-7, 5, 5);
    scene.add(amber);

    const teal = new THREE.PointLight(
      0x43d9c8,
      70,
      65
    );

    teal.position.set(7, 2, -8);
    scene.add(teal);

    // =====================================
    // LANTAI 3D
    // =====================================
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(100, 120),

      new THREE.MeshStandardMaterial({
        color: 0x101c2a,
        metalness: 0.35,
        roughness: 0.6
      })
    );

    floor.rotation.x = -Math.PI / 2;
    floor.position.set(0, -4, -35);

    scene.add(floor);

    const grid = new THREE.GridHelper(
      120,
      60,
      0x428d96,
      0x234451
    );

    grid.position.set(0, -3.98, -35);
    scene.add(grid);

    // =====================================
    // LORONG MENUJU KEJAUHAN
    // =====================================
    const tunnel = new THREE.Group();

    const tunnelGeometry = new THREE.EdgesGeometry(
      new THREE.BoxGeometry(24, 14, 0.2)
    );

    for (let i = 0; i < 12; i++) {
      const frame = new THREE.LineSegments(
        tunnelGeometry,

        new THREE.LineBasicMaterial({
          color: i % 2 ? 0x3ab6b1 : 0xd9943e,
          transparent: true,
          opacity: 0.5
        })
      );

      frame.position.set(
        0,
        3,
        5 - i * 7
      );

      tunnel.add(frame);
    }

    scene.add(tunnel);

    // =====================================
    // BINGKAI VIDEO DI KIRI DAN KANAN
    // =====================================
    const cards = [];

    const cardGeometry = new THREE.BoxGeometry(
      2.2,
      3.8,
      0.16
    );

    const cardEdges = new THREE.EdgesGeometry(
      cardGeometry
    );

    for (let i = 0; i < 8; i++) {
      const color = i % 2 ? 0x43d9c8 : 0xffb650;
      const card = new THREE.Group();

      // Badan bingkai.
      const panel = new THREE.Mesh(
        cardGeometry,

        new THREE.MeshStandardMaterial({
          color: 0x142331,
          metalness: 0.45,
          roughness: 0.4
        })
      );

      card.add(panel);

      // Garis tepi bingkai.
      card.add(
        new THREE.LineSegments(
          cardEdges,
          new THREE.LineBasicMaterial({ color })
        )
      );

      // Simbol play.
      const triangle = new THREE.Shape();

      triangle.moveTo(-0.3, 0.4);
      triangle.lineTo(0.4, 0);
      triangle.lineTo(-0.3, -0.4);
      triangle.closePath();

      const play = new THREE.Mesh(
        new THREE.ShapeGeometry(triangle),

        new THREE.MeshBasicMaterial({
          color,
          side: THREE.DoubleSide
        })
      );

      play.position.z = 0.09;
      card.add(play);

      // Menempatkan layar pada jarak yang berbeda.
      card.position.set(
        i % 2 ? 9 : -9,
        (i % 3) * 1.2,
        1 - Math.floor(i / 2) * 12
      );

      card.rotation.y = i % 2 ? -0.35 : 0.35;
      card.userData.baseY = card.position.y;

      scene.add(card);
      cards.push(card);
    }

    // =====================================
    // PARTIKEL DALAM RUANG 3D
    // =====================================
    const positions = new Float32Array(180 * 3);

    for (let i = 0; i < positions.length; i += 3) {
      positions[i] = (Math.random() - 0.5) * 32;
      positions[i + 1] = Math.random() * 15 - 3;
      positions[i + 2] = -Math.random() * 75;
    }

    const particlesGeometry = new THREE.BufferGeometry();

    particlesGeometry.setAttribute(
      "position",
      new THREE.BufferAttribute(positions, 3)
    );

    const particles = new THREE.Points(
      particlesGeometry,

      new THREE.PointsMaterial({
        color: 0xa8dce6,
        size: 0.035,
        transparent: true,
        opacity: 0.65,
        depthWrite: false
      })
    );

    scene.add(particles);

    // =====================================
    // ANIMASI
    // =====================================
    let elapsed = 0;
    let previous = 0;

    function draw(time) {
      // Batasi sekitar 30 frame per detik.
      if (previous && time - previous < 1000 / 30) {
        return;
      }

      const delta = previous
        ? Math.min((time - previous) / 1000, 0.1)
        : 0;

      previous = time;
      elapsed += delta;

      // Kamera bergeser perlahan mengikuti mouse.
      camera.position.x = THREE.MathUtils.damp(
        camera.position.x,
        pointer.x * 0.9,
        3,
        delta
      );

      camera.position.y = THREE.MathUtils.damp(
        camera.position.y,
        1.2 + pointer.y * 0.45,
        3,
        delta
      );

      camera.lookAt(0, 1, -30);

      // Gerakan halus seluruh lorong.
      tunnel.position.z =
        Math.sin(elapsed * 0.18) * 1.3;

      // Bingkai video melayang.
      cards.forEach((card, i) => {
        card.position.y =
          card.userData.baseY +
          Math.sin(elapsed * 0.5 + i) * 0.28;

        card.rotation.z =
          Math.sin(elapsed * 0.3 + i) * 0.035;
      });

      renderer.render(scene, camera);
    }

    // Menghentikan animasi saat tab tidak terlihat,
    // serta mengikuti pengaturan pengurangan gerakan.
    function syncAnimation() {
      renderer.setAnimationLoop(null);
      previous = 0;

      if (document.hidden) return;

      if (reduced.matches) {
        pointer.set(0, 0);
        camera.position.set(0, 1.2, 12);
        camera.lookAt(0, 1, -30);

        renderer.render(scene, camera);
      } else {
        renderer.setAnimationLoop(draw);
      }
    }

    // =====================================
    // INTERAKSI MOUSE
    // =====================================
    window.addEventListener(
      "pointermove",
      (event) => {
        if (
          reduced.matches ||
          event.pointerType !== "mouse"
        ) {
          return;
        }

        pointer.set(
          (event.clientX / innerWidth) * 2 - 1,
          1 - (event.clientY / innerHeight) * 2
        );
      },
      { passive: true }
    );

    document.documentElement.addEventListener(
      "pointerleave",
      () => pointer.set(0, 0)
    );

    window.addEventListener(
      "blur",
      () => pointer.set(0, 0)
    );

    // Sesuaikan kamera dan kanvas ketika layar berubah.
    window.addEventListener("resize", () => {
      camera.aspect = innerWidth / innerHeight;
      camera.updateProjectionMatrix();

      renderer.setPixelRatio(
        Math.min(devicePixelRatio || 1, 1.5)
      );

      renderer.setSize(innerWidth, innerHeight);

      if (!document.hidden) {
        renderer.render(scene, camera);
      }
    });

    document.addEventListener(
      "visibilitychange",
      syncAnimation
    );

    reduced.addEventListener(
      "change",
      syncAnimation
    );

// ===== VIDEO HASIL MENJADI ISI BINGKAI 3D =====

let linkedVideos = [];
let bindings = [];
let videoFrame = 0;

const picker = new THREE.Raycaster();
const mouse = new THREE.Vector2();

const resultsSection = document.getElementById("results");

const showingResults = () =>
  !resultsSection.classList.contains("hidden");

// Memperbarui layar video dan simbol play.
function refreshVideoFrames() {
  const visible = showingResults();

  bindings.forEach(({ screen, play, video }) => {
    screen.visible = visible;
    play.visible = !visible || video.paused || video.ended;
  });

  if (!document.hidden) {
    renderer.render(scene, camera);
  }
}

// Video tetap bergerak saat pengguna menonaktifkan
// animasi dekoratif melalui pengaturan perangkat.
function updateReducedVideo() {
  cancelAnimationFrame(videoFrame);
  videoFrame = 0;

  if (
    !reduced.matches ||
    document.hidden ||
    !showingResults()
  ) {
    return;
  }

  refreshVideoFrames();

  const playing = linkedVideos.some(
    video => !video.paused && !video.ended
  );

  if (playing) {
    videoFrame = requestAnimationFrame(updateReducedVideo);
  }
}

// Menata bingkai di sisi kiri dan kanan lorong.
function placeFrame(card, rank) {
  card.position.set(
    rank % 2 ? 9 : -9,
    (rank % 3) * 1.2,
    1 - Math.floor(rank / 2) * 12
  );

  card.rotation.y = rank % 2 ? -0.35 : 0.35;
  card.userData.baseY = card.position.y;
}

// Video yang sedang diputar dibawa ke bingkai depan.
function showVideoFirst(video) {
  const index = linkedVideos.indexOf(video);

  if (index < 0) return;

  cards.forEach((card, i) => {
    const rank = (i - index + cards.length) % cards.length;
    placeFrame(card, rank);
  });
}

// Menghubungkan setiap video dengan bingkai.
function connectClipVideos() {
  cancelAnimationFrame(videoFrame);

  // Lepaskan tekstur dan event dari hasil sebelumnya.
  bindings.forEach(binding => {
    binding.off();

    binding.screen.removeFromParent();
    binding.screen.geometry.dispose();
    binding.screen.material.dispose();
    binding.texture.dispose();

    binding.play.visible = true;
  });

  bindings = [];
  linkedVideos = window.shortClipperVideos || [];

  // Tambah bingkai jika jumlah hasil lebih dari delapan.
  while (cards.length < linkedVideos.length) {
    const card = new THREE.Group();

    // Salin badan, garis tepi, dan simbol play.
    cards[0].children.slice(0, 3).forEach(child => {
      card.add(child.clone());
    });

    scene.add(card);
    cards.push(card);
  }

  cards.forEach(placeFrame);

  linkedVideos.forEach((video, index) => {
    const card = cards[index];
    const play = card.children[2];

    // Jadikan video sebagai gambar bergerak pada bidang 3D.
    const texture = new THREE.VideoTexture(video);
    texture.colorSpace = THREE.SRGBColorSpace;

    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(1, 1),

      new THREE.MeshBasicMaterial({
        map: texture,
        toneMapped: false
      })
    );

    // Letakkan layar di depan badan bingkai,
    // kemudian simbol play di depan layar.
    screen.position.z = 0.095;
    play.position.z = 0.11;

    card.add(screen);

    // Pertahankan proporsi video agar tidak melebar.
    function fitVideo() {
      const ratio =
        video.videoWidth && video.videoHeight
          ? video.videoWidth / video.videoHeight
          : video.classList.contains("landscape")
            ? 16 / 9
            : 9 / 16;

      const height = Math.min(3.6, 2 / ratio);

      screen.scale.set(height * ratio, height, 1);
      refreshVideoFrames();
    }

    function onPlay() {
      linkedVideos.forEach(other => {
        if (other !== video) other.pause();
      });

      showVideoFirst(video);
      refreshVideoFrames();
      updateReducedVideo();
    }

    const events = {
      loadedmetadata: fitVideo,
      loadeddata: refreshVideoFrames,
      seeked: refreshVideoFrames,
      play: onPlay,
      pause: refreshVideoFrames,
      ended: refreshVideoFrames
    };

    Object.entries(events).forEach(([name, handler]) => {
      video.addEventListener(name, handler);
    });

    bindings.push({
      screen,
      play,
      video,
      texture,

      off: () => {
        Object.entries(events).forEach(([name, handler]) => {
          video.removeEventListener(name, handler);
        });
      }
    });

    fitVideo();
  });

  refreshVideoFrames();
}

// Klik bingkai samping untuk putar atau jeda.
window.addEventListener("click", event => {
  if (!showingResults()) return;

  // Klik pada formulir/kartu tetap ditangani kontrol biasa.
  if (event.target.closest?.(".container")) return;

  mouse.set(
    (event.clientX / innerWidth) * 2 - 1,
    1 - (event.clientY / innerHeight) * 2
  );

  scene.updateMatrixWorld(true);
  picker.setFromCamera(mouse, camera);

  const screens = bindings.map(item => item.screen);

  const hit = picker.intersectObjects(
    screens,
    false
  )[0];

  if (!hit) return;

  const binding = bindings.find(
    item => item.screen === hit.object
  );

  const video = binding.video;

  if (video.paused) {
    video.play().catch(() => {
      showStatus(
        "Silakan tekan tombol putar pada kartu hasil.",
        true
      );
    });
  } else {
    video.pause();
  }
});

// Saat kembali ke pilihan atau mengganti video,
// hentikan pemutaran dan tampilkan dekorasi kembali.
new MutationObserver(() => {
  if (!showingResults()) {
    linkedVideos.forEach(video => video.pause());
  }

  refreshVideoFrames();
}).observe(resultsSection, {
  attributes: true,
  attributeFilter: ["class"]
});

// Hentikan video ketika pengguna meninggalkan tab.
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    linkedVideos.forEach(video => video.pause());
  }

  updateReducedVideo();
});

reduced.addEventListener("change", updateReducedVideo);

window.addEventListener(
  "shortclipper:videos",
  connectClipVideos
);

// Menangani hasil yang sudah tersedia saat 3D selesai dimuat.
connectClipVideos();

    syncAnimation();
  } catch (error) {
    // Gunakan background CSS jika 3D gagal dimuat.
    renderer?.setAnimationLoop(null);
    renderer?.domElement.remove();
    renderer?.dispose();

    console.warn(
      "Background 3D tidak tersedia:",
      error
    );
  }
})();