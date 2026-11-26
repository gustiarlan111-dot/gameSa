# V8.0 — Audit teknis (Phase 01)

Audit dilakukan langsung pada source di branch `main` (commit `205879b`) dengan Godot 4.3-stable,
bukan dari dokumentasi. Semua angka di bawah berasal dari perintah yang benar-benar dijalankan.

## Baseline sebelum perubahan

| Pemeriksaan | Perintah | Hasil |
|---|---|---|
| Import aset | `godot --headless --path . --import` | selesai ±2 menit, 0 error |
| Tes logika | `godot --headless --path . tests/logic_test.tscn` | 43 pemeriksaan, 0 gagal |
| Validator map | `python3 tools/maptool.py check` | 32 area, **0 error**, 9 peringatan |
| Screenshot tiap area | `godot --path . -- --shot sofia <area> <spawn> 90 out.png` (Xvfb, OpenGL3) | 32/32 area tampil, tanpa script error |
| Ukuran paket | `godot --headless --export-pack Android out.pck` | 312,4 MB |

Error validator lama yang disebut di MAP_PIPELINE.md (`arland_room a_frame`, 3 quest point
`jalan_kota`, 2 quest point `perpustakaan`) **sudah tidak muncul lagi**; catatan di dokumen itu basi.

## Arsitektur (ringkas)
- `src/world.gd` menjalankan seluruh gameplay di koordinat 2D (gerak, collision, NPC, pintu, quest,
  cutscene, save). Lapisan 2D-nya disembunyikan.
- `src/view3d/world_view_3d.gd` mencerminkan dunia 2D itu ke 3D setiap frame: tile tanah sebagai
  plane, prop sebagai quad miring (MultiMesh per tekstur), aktor sebagai Sprite3D.
- Kamera 3D perspektif, pitch 38°, FOV 32°. Renderer GL Compatibility.
- Save: atomic write (`.tmp` → rename), rotasi `.bak`/`.bak2`, CRC32, deteksi schema lebih baru,
  pemulihan dari backup. Sudah kuat; tidak perlu dirombak.

## Temuan

### Kritis / prioritas tinggi
1. **Elevasi hanya ilusi lukisan.** Tangga, dinding penahan, dan tebing dicat di tanah datar.
   Logika 2D tidak punya ketinggian, dan di 3D karakter tidak pernah naik. Hanya `plaza` (7 tangga)
   dan `hutan_bisik` (2 tangga tebing) yang punya tangga. → **Diperbaiki di V8** (Elevation 3.0).
2. **Karakter hilang di balik pohon.** Di titik spawn Taman Kota (2300, 880) Arland dan Sofia
   tertutup penuh oleh pohon di depan mereka. Tidak ada penanganan oklusi di luar cutscene.
   → **Diperbaiki di V8** (fade dither).
3. **Tidak ada menu pengaturan sama sekali**: tidak ada preset grafis, batas FPS, volume, ukuran
   kontrol, atau posisi joystick. Untuk game Android ini kekurangan besar. → **Ditambahkan di V8.**

### Sedang
4. **64,5 MB tekstur mati di APK.** Ke-32 area sudah memakai tile HD (`assets/maps/hd/`), tetapi
   gambar tanah lama `assets/maps/<area>.png` tetap ikut diekspor (hanya dipakai sebagai fallback
   jika tile kosong). → **Dikeluarkan dari ekspor di V8**, file sumbernya tetap ada untuk tools.
5. **Identitas visual map mimpi lemah.** Sekitar 11 map mimpi (memory_garden, star_path,
   starfall_village, eternal_garden, rain_garden, clockwork_station, moonlight_lake, memory_bridge,
   hall_of_tomorrow, arsip_memudar, kenangan_gazebo) dari titik spawn tampak serupa: pohon
   berwarna, kristal, jalan setapak. Clockwork Station tidak menampilkan jam/stasiun dan Memory
   Bridge tidak menampilkan jembatan di dekat spawn. → **Sebagian dikerjakan**: Clockwork Station (V8.1),
   Memory Bridge, Hall of Tomorrow, Rain Garden (V8.2), Memory Garden, Arsip Memudar, Kenangan Gazebo (V8.8).
   Sisa: star_path, starfall_village, eternal_garden, moonlight_lake.
6. **Map padat untuk Android kelas bawah**: 7 area punya lebih dari 900 prop (hutan_bisik 1.862,
   eternal_garden 1.262). Saat ini aman karena MultiMesh per tekstur, tetapi FPS di perangkat
   nyata belum diukur. → Preset Rendah di V8 membantu; pengukuran perangkat masih perlu.
7. `lantern_field` memakai 2 prop resolusi 1x di map HD (`lantern_off`, `v41_lantern_off_lantern`).

### Rendah / catatan
8. Mosaik mawar angin di lantai Plaza tampak sebagai "segitiga oranye" saat cahaya pagi. Ini desain
   yang disengaja, bukan artefak.
9. `main.gd` mode QA `--shot` mengakses `game.world` sebelum `game` ada jika boot lambat (hanya
   tooling QA). → **Diberi guard di V8.**
10. Tidak ditemukan kredensial atau secret di repo. Keystore yang ada di CI hanya debug keystore
    standar Android yang dibuat saat build. `.gitignore` sudah mengabaikan `.godot/`, `build/`,
    `*.keystore`, `*.jks`.

## Yang tidak dapat diaudit di lingkungan ini
- FPS, RAM, baterai, dan perilaku background/resume di **perangkat Android nyata**. Render di sini
  memakai Mesa llvmpipe (CPU), sehingga angka FPS-nya tidak mewakili ponsel.
- Build APK lokal (Android SDK, Java 17, export template). Build APK tetap dilakukan GitHub Actions.
