# Arland & Sofia: Our Little Universe

Game petualangan romantis 2D untuk Android, dibuat dengan **Godot 4.3**. Dua sudut pandang
(route Arland dan route Sofia), satu ending kanon, sepenuhnya offline.

## Pasang di Android (paling mudah)

1. Buka halaman **[Releases → latest](../../releases/tag/latest)**.
2. Unduh `ArlandSofia.apk` ke ponsel.
3. Buka file itu dan izinkan "pasang dari sumber tidak dikenal" bila diminta.

APK dibuat otomatis oleh GitHub Actions setiap ada push ke `main`
(tab **Actions → Build APK**, file juga tersedia sebagai artifact `ArlandSofia-apk`).

## Jalankan di komputer

1. Unduh **Godot 4.3** (versi standar, bukan .NET): https://godotengine.org/download/archive/4.3-stable/
2. Unduh repo ini (**Code → Download ZIP**, lalu ekstrak) atau `git clone`.
3. Buka Godot → **Import** → pilih file `project.godot` di folder ini → **Import & Edit**.
   Impor aset pertama kali butuh beberapa menit.
4. Tekan **F5** (Run Project).

Kontrol di PC: WASD/panah untuk berjalan, Shift untuk lari, E/Spasi untuk interaksi,
M untuk Memory Book, Esc untuk jeda.

**Pengaturan** (layar judul atau menu Jeda): kualitas grafis Rendah/Sedang/Tinggi/Ultra, 30/60 FPS,
volume musik/suasana/efek, ukuran kontrol sentuh, dan joystick kiri/kanan. Tersimpan di
`user://settings.json`, terpisah dari save cerita. Preset Rendah mematikan bayangan, glow, lampu,
efek layar, dan pantulan air (V8.10).

## Build APK sendiri

Di Godot: **Editor → Manage Export Templates** (unduh 4.3), atur Android SDK dan Java 17 di
**Editor Settings → Export → Android**, lalu **Project → Export → Android → Export Project**.
Langkah lengkap yang dipakai CI ada di `.github/workflows/android.yml`.

## Tes

```
godot --headless --path . tests/logic_test.tscn
```
Memeriksa aturan cerita, quest, save (schema 8), minigame, toko, puzzle, romance, cuaca, musik,
lapisan ketinggian (tangga) dan pengaturan.

Uji alur cerita penuh (headless, cepat): `godot --headless --fixed-fps 60 --path . -- --story sofia out 1500000`
menjalankan autopilot sampai tamat dan mencetak setiap langkah (`STEP>`). Lihat `QA_REPORT_V8.md`.

## Struktur

| Folder | Isi |
|---|---|
| `src/` | kode game (GDScript): dunia, aktor, quest, cutscene, UI, minigame, audio |
| `assets/` | gambar, audio dan data JSON (cerita, quest, map, prop) |
| `fonts/` | font Inter (lisensi OFL) |
| `tests/` | tes logika headless |
| `tools/` | generator aset Python (Pillow, numpy, scipy, matplotlib): NPC (`npc_gen.py`), kit prop HD (`artkit/`, `kit_extra.py`), map HD (`worldgen/`, `hd_remaster.py`) |
