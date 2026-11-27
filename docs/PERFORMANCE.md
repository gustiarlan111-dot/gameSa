# Performa (U1)

## Masalah yang dilaporkan
Di Redmi Pad 2 (Mali-G57 MC2, 2560×1600), game tidak mencapai 60 FPS.

## Penyebab
- Game dirancang untuk 1280×720 dan memakai stretch `canvas_items`.
- Dengan stretch itu, dunia 3D, overlay 2D, dan efek layar digambar untuk setiap piksel fisik.
- Di layar 2560×1600, jumlahnya 4,1 juta piksel per frame. Itu 4,4× lebih banyak daripada desain.

## Rincian biaya di 2560×1600, preset Tinggi
Plaza pukul 07.00, saat kabut pagi tebal. Diukur dari timer render GPU di renderer software server.
Angka absolutnya tidak mewakili Mali; yang bermakna hanya perbandingannya.

| Bagian yang dimatikan (sendiri-sendiri) | Waktu render GPU | Hemat |
|---|---|---|
| — (semua nyala) | 659 ms | — |
| sampel blur/bloom di efek layar | 447 ms | 32% |
| seluruh efek layar | 378 ms | 43% |
| kabut | 585 ms | 11% |
| glow 3D | 588 ms | 11% |
| bayangan | 604 ms | 8% |
| lampu, pantulan air | ±659 ms | ±0% |

Kesimpulannya, **efek layar adalah bagian terberat.** Efek ini membaca 12 sampel tambahan untuk
setiap piksel (blur tilt-shift di atas dan bawah layar, ditambah bloom).

## Perubahan

### 1. Efek layar lebih murah, gambar tetap HD (semua preset)
- `src/fx/post25d.gdshader` kini membaca blur dan bloom dari **mipmap layar**, satu sampel untuk
  masing-masing, menggantikan 12 sampel.
- Ketajaman tidak berubah. Blur tilt-shift dan bloom lampu terlihat hampir sama
  (lihat `docs/screens/u1/efek_layar.png`). Halo lampu sedikit lebih halus.
- Hasil di Plaza, Tinggi, 2560×1600: **659 → 550 ms (−17%)**. Diukur dua kali per versi:
  552/549 dan 665/655.

### 2. Panggung resolusi, hanya untuk Sedang/Rendah (`src/game/render_stage.gd`)
- **Kapan dipakai.** Di layar yang setidaknya 2× ukuran desain, dunia digambar di sebuah `SubViewport`.
  Koordinat 2D di dalamnya selalu sama dengan ukuran logis UI (`size_2d_override`).
- **Tinggi/Ultra (bawaan):** dunia digambar di resolusi layar penuh dan ditampilkan 1:1. Hasilnya
  identik dengan tanpa panggung: hanya 0,19% piksel yang berbeda lebih dari 8 level.
- **Sedang/Rendah:** dunia digambar 1280×800 lalu diperbesar 2× dengan filter nearest. UI tetap tajam.
  - Plaza: Sedang 167 ms, Rendah 109 ms.
  - Dibandingkan Tinggi lama (659 ms), penghematannya −75% dan −84%.
  - Harganya, tepi dunia lebih kasar (lihat `docs/screens/u1/detail_1banding1.png`).
- **Mengikuti pengaturan.** Mode berganti langsung saat kualitas grafis diubah, tanpa memuat ulang.
- **Ponsel tidak terpengaruh.** Ponsel 1080p (skala 1,5×) tidak memakai panggung sama sekali.
- **Biaya.** Di Tinggi, satu render target tambahan memakan memori tekstur ±27 MB (189 → 216 MB).
  Biaya GPU-nya tidak terukur (547 ms dengan panggung, 550 ms tanpa).

### 3. Penghitung FPS
Aktifkan lewat **Pengaturan → Penghitung FPS**. Di bawah HUD akan muncul tulisan seperti
`58 FPS · 2560x1600`. Angka di belakangnya adalah ukuran dunia yang sedang digambar.

## Yang dicoba lalu dibatalkan
- **Panggung 1280×800 sebagai bawaan.** Pemilik game menilai gambarnya burik di Redmi Pad 2 dan ingin
  tetap HD.
- **Noise kabut dari tekstur.** Tujuannya mengganti hash dengan pembacaan tekstur. Di renderer software
  hasilnya tidak lebih cepat, dan pola kabutnya berubah. Tanpa bukti di GPU sungguhan, perubahan ini
  tidak dikirim.

## Cara mengulang
```
SHOT_QUALITY=high|medium|low STAGE=0|1 QA_Q='{"taps":false}' \
  xvfb-run -s "-screen 0 2560x1600x24" godot --rendering-driver opengl3 --resolution 2560x1600 \
  --path . tests/bench_map.tscn -- --bench plaza
```
- `STAGE` memaksa panggung nyala (1) atau mati (0).
- `QA_Q` menimpa satu nilai preset: `taps`, `post`, `shadows`, `glow`, `lamps`, `reflect`, atau `mist`.
- Keduanya hanya untuk QA.
