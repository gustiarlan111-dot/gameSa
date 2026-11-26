# CHANGELOG — V8.0 "The Definitive Overhaul" (tahap pertama)

Branch: `v8.0` (dari `main` @ `205879b`). Save schema tetap **8**: tidak ada ID quest, map, karakter,
atau story flag yang diubah, jadi semua save lama langsung terbaca tanpa migrasi.

Rilis ini adalah **tahap pertama** dari rencana 14 phase. Isinya fondasi teknis yang paling
berdampak dan bisa diverifikasi. Bagian yang belum dikerjakan tercantum di akhir file ini.

## Elevation 3.0: tangga dan teras yang benar-benar bertingkat
- **Lapisan ketinggian baru** `assets/data/elevation.json` + `src/logic/elevation.gd`. Teras, dinding
  penahan, tebing, ramp, dan tangga kini punya tinggi sungguhan di tampilan 3D. Logika game tetap 2D,
  jadi quest, NPC, collision, pintu, dan save tidak tersentuh.
- Tanah dibangun sebagai mesh grid yang mengikuti ketinggian (`_elevated_tile`). Dinding jadi vertikal,
  dataran tinggi benar-benar di atas, dan dari kamera gameplay setiap piksel lukisan tetap di tempatnya.
- Karakter, NPC, hewan, prop, lampu, dan volume bangunan berdiri di ketinggian tanah di bawahnya.
  Saat naik tangga, karakter naik bertahap.
- Karakter tidak lagi "tertelan" dinding atau tangga: sprite digeser ke arah kamera sepanjang
  garis pandang (`_wall_push`), sehingga posisinya di layar sama tetapi berada di depan dinding.
- Terasa saat dimainkan: kecepatan jalan di tangga 72%, suara langkah tangga baru (`step_stairs`,
  disintesis oleh `tools/sfx_v8.py`, tanpa aset pihak ketiga), dan ritme langkah lebih rapat.
- Diterapkan di **Plaza** (taman utara, teras kafe, 7 tangga) dan **Hutan Bisik** (2 teras tebing,
  2 tangga tebing, ramp tersembunyi di bawah kanopi supaya kamera sinematik tidak melihat celah).
- Validator: `maptool check` dan `tests/logic_test.gd` gagal jika ada tangga tanpa slope tangga atau
  kedua ujungnya setinggi.

## Kamera: karakter tidak lagi hilang di balik pohon
- **Occlusion fade** (`src/fx/occlude_fade.gdshader`): pohon atau prop tinggi yang berdiri di depan
  Arland/Sofia memudar menjadi dither 4×4 (fade halus ±0,15 detik), lalu kembali padat saat tidak
  menghalangi. Bayangan prop tetap utuh, dan angin tetap menggoyangkannya.
- Contoh kasus nyata yang diperbaiki: titik spawn Taman Kota, tempat pasangan sebelumnya tertutup penuh.

## Pengaturan (baru)
- Jendela **Pengaturan** dari layar judul dan menu Jeda (`src/ui/settings_menu.gd`).
- Kualitas grafis **Rendah / Sedang / Tinggi / Ultra** (`GameSettings.quality()`):
  - Rendah: tanpa bayangan matahari, tanpa glow, tanpa pass layar, tanpa lampu real-time.
  - Sedang: bayangan 2048, pass layar hanya grading (tanpa blur/bloom tap).
  - Tinggi: tampilan bawaan sebelum V8 (default).
  - Ultra: bayangan 4096, MSAA 2×.
- **30 / 60 FPS**, volume **musik / suasana / efek suara**, **ukuran kontrol** (4 tingkat), dan
  **joystick kiri/kanan** (layout kidal: tombol pindah ke kiri).
- Disimpan di `user://settings.json` secara atomik (tulis `.tmp` lalu rename), terpisah dari save
  cerita. File rusak atau nilai aneh kembali ke default tanpa crash.

## Ukuran paket −20,6%
- 32 gambar tanah lama `assets/maps/<area>.png` (hanya fallback, karena semua area sudah memakai tile
  HD) dikeluarkan dari ekspor Android lewat `exclude_filter`. File sumbernya **tidak dihapus**, karena
  tools masih bisa memakainya.
- PCK: **312,4 MB → 247,9 MB** (diukur dengan `--export-pack`). Game dijalankan langsung dari PCK
  baru di 3 area tanpa error.

## QA dan tooling
- Autopilot cerita (`--story`) kini memakai **pathfinding A\*** di atas grid collision asli
  (sebelumnya berjalan lurus dan tersangkut pohon di Memory Garden), menyelesaikan puzzle/minigame/
  dialog konfirmasi secara otomatis (dicatat `QA>`), memilih area yang masih punya kegiatan, dan
  mencetak setiap langkah (`STEP>`). Dengan `--headless --fixed-fps 60`, satu route penuh berjalan
  dalam hitungan menit.
- Mode `--shot`: `SHOT_QUALITY`, `SHOT_SETTINGS`, `SHOT_LEFT`, ditambah guard saat game belum siap.
- Tes logika 43 → **54 pemeriksaan** (lapisan ketinggian, tangga semua map, pengaturan).

## File
**Baru:** `src/logic/elevation.gd`, `src/logic/game_settings.gd`, `src/ui/settings_menu.gd`,
`src/fx/occlude_fade.gdshader`, `assets/data/elevation.json`, `assets/audio/sfx/step_stairs.wav`,
`tools/sfx_v8.py`, `docs/V8_AUDIT.md`, `CHANGELOG_V8.md`, `QA_REPORT_V8.md`.
**Diubah:** `src/view3d/world_view_3d.gd`, `src/world.gd`, `src/data.gd`, `src/main.gd`,
`src/game/game.gd`, `src/game/atmosphere.gd`, `src/ui/touch_controls.gd`, `src/ui/pause_menu.gd`,
`src/ui/title_screen.gd`, `tests/logic_test.gd`, `tools/maptool.py`, `export_presets.cfg`,
`docs/MAP_PIPELINE.md`, `README.md`.

## Belum dikerjakan di tahap ini (jujur)
Bagian prompt V8 berikut **belum** diimplementasikan. Sebagian butuh produksi aset atau penulisan
skala besar yang tidak bisa dikerjakan dengan kualitas layak dalam satu sesi, sebagian lagi butuh
perangkat atau masukan Anda:
- Remaster map per area (identitas visual 11 map mimpi, tata ulang Jalan Kota/Riverside/dst.) dan
  elevasi di area selain Plaza/Hutan Bisik.
- Remaster karakter Arland & Sofia (butuh foto referensi dari Anda), sistem ekspresi baru, outfit,
  dan animasi baru (duduk, tangga, pelukan, dll.).
- NPC dengan jadwal harian, perluasan cerita menuju ±6 jam, route eksklusif tambahan, romance 4.0,
  dan minigame baru (memancing, memasak, berkebun, fotografi).
- Musik/tema baru, footstep per permukaan basah/pasir, adaptive music lanjutan.
- Day-night penuh dengan petir/genangan, refleksi air sungguhan, redesign UI menyeluruh.
- Pengukuran FPS/RAM/baterai di ponsel nyata. Build APK dilakukan oleh GitHub Actions, bukan di sini.
