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

## Build APK sendiri

Di Godot: **Editor → Manage Export Templates** (unduh 4.3), atur Android SDK dan Java 17 di
**Editor Settings → Export → Android**, lalu **Project → Export → Android → Export Project**.
Langkah lengkap yang dipakai CI ada di `.github/workflows/android.yml`.

## Tes

```
godot --headless --path . tests/logic_test.tscn
```
Memeriksa aturan cerita, quest, save (schema 8), minigame, toko, puzzle, romance, cuaca dan musik.

## Struktur

| Folder | Isi |
|---|---|
| `src/` | kode game (GDScript): dunia, aktor, quest, cutscene, UI, minigame, audio |
| `assets/` | gambar, audio dan data JSON (cerita, quest, map, prop) |
| `fonts/` | font Inter (lisensi OFL) |
| `tests/` | tes logika headless |
| `tools/` | generator aset Python (Pillow, numpy, scipy, matplotlib): NPC (`npc_gen.py`), kit prop HD (`artkit/`, `kit_extra.py`), map HD (`worldgen/`, `hd_remaster.py`) |
