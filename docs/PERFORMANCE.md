# Performa (U1)

## Masalah yang dilaporkan
Di Redmi Pad 2, game tidak mencapai 60 FPS. Tablet ini memakai GPU Mali-G57 MC2 dengan layar 2560×1600.

## Penyebab
- Game dirancang untuk 1280×720 dan memakai stretch `canvas_items`.
- Dengan stretch itu, dunia 3D, overlay 2D, dan efek layar (warna, vinyet, bloom) digambar untuk setiap
  piksel fisik layar.
- Di layar 2560×1600, jumlahnya 4,1 juta piksel per frame. Itu 4,4× lebih banyak daripada desain,
  padahal gambarnya sama. GPU kelas MC2 biasanya kehabisan tenaga di pengisian piksel seperti ini,
  bukan di jumlah objek.

## Perbaikan: panggung resolusi (`src/game/render_stage.gd`)
- **Kapan aktif.** Panggung aktif kalau layar setidaknya 2× ukuran desain di kedua sisi
  (`RenderStage.wanted`).
- **Apa yang terjadi.**
  - World, Atmosphere, dan WorldView3D digambar di dalam `SubViewport` berukuran logis
    (1280×800 di Redmi Pad 2).
  - Hasilnya diperbesar dengan filter *nearest*, jadi pixel art tetap tajam.
  - UI (HUD, dialog, menu, gelembung obrolan) tetap digambar di layar asli, jadi teks tetap tajam.
- **Koordinat.** Satuan logis di dalam panggung sama dengan satuan UI. Karena itu gelembung obrolan
  NPC yang memetakan posisi dunia ke UI tetap pas. Ini dicek dengan `SHOT_BUBBLE=1` di 2560×1600:
  posisi gelembungnya identik dengan dan tanpa panggung.
- **Ponsel 1080p tidak memakai panggung.**
  - Skalanya hanya 1,5×. Pembesaran *nearest* yang bukan bilangan bulat akan membuat piksel tidak rata.
  - Ponsel ini tetap digambar native seperti sebelumnya.
  - Kalau angka dari HP menunjukkan ponsel juga lambat, ini keputusan berikutnya.
- **Kekurangan.** Di tablet, tepi karakter dan objek sedikit lebih kasar, karena satu piksel dunia
  menjadi 2×2 piksel layar. Teks dan UI tidak terpengaruh.

## Penghitung FPS
Aktifkan lewat **Pengaturan → Penghitung FPS → Nyala**. Di bawah HUD akan muncul tulisan seperti
`58 FPS · 1280x800`. Ukuran yang ditampilkan adalah ukuran dunia yang sedang digambar. Kalau angkanya
2560x1600, berarti panggung tidak aktif.

## Pengukuran di server
- Lingkungan ini memakai renderer software (llvmpipe), dan FPS-nya terkunci ±7,5. Angka FPS dari sini
  tidak bermakna.
- Yang bisa diukur adalah **waktu render** per frame dari timer GPU dan CPU
  (`RenderingServer.viewport_get_measured_render_time_*`). Hasilnya dicatat oleh `tests/bench_map.tscn`
  pada 2560×1600.

| Map | Waktu render GPU tanpa → dengan panggung | CPU render | Memori tekstur |
|---|---|---|---|
| Plaza | 649 → 223 ms (−66%) | 480 → 194 ms | 189 → 156 MB |
| Taman Kota | 652 → 224 ms (−66%) | 487 → 194 ms | 183 → 150 MB |
| Padang Lentera | 724 → 242 ms (−67%) | 506 → 205 ms | 167 → 134 MB |
| Hutan Bisik | 694 → 250 ms (−64%) | 488 → 213 ms | 234 → 201 MB |
| Kafe Senja | 496 → 168 ms (−66%) | 262 → 133 ms | 90 → 81 MB |

- Angka absolutnya berasal dari CPU server, bukan dari Mali. **Yang berarti hanya perbandingannya.**
- Waktu render turun sekitar 3×, bukan 4×. Sisanya adalah biaya tetap per frame (bayangan dan jumlah
  draw call), yang tidak ikut turun bersama resolusi.

## Cara mengulang
```
STAGE=0|1 xvfb-run -s "-screen 0 2560x1600x24" godot --rendering-driver opengl3 --resolution 2560x1600 \
    --path . tests/bench_map.tscn -- --bench plaza
```
Variabel `STAGE` memaksa panggung nyala (1) atau mati (0). Variabel ini hanya untuk QA.

## Gambar
- `docs/screens/u1/panggung_2560x1600.png`: tangkapan 2560×1600 sebelum dan sesudah. Gelembung obrolan
  dan HUD berada di posisi yang sama. Penghitung FPS terlihat di bawah HUD.
- `docs/screens/u1/detail_1banding1.png`: potongan 1:1. Di sini terlihat yang dikorbankan, yaitu tepi
  yang sedikit lebih kasar.
