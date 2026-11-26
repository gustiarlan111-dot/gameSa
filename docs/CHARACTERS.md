# Mengganti karakter Arland & Sofia (V8.3)

Karakter utama digambar dari model 3D (GLB) yang dirender menjadi sprite 8 arah. Game tetap memakai
sprite (ringan untuk HP, menyatu dengan dunia HD-2D), tetapi bentuk dan warnanya berasal dari model.

## File
| File | Isi |
|---|---|
| `assets/characters/<id>/model/<Nama>.glb` | model sumber (tidak ikut APK, lihat `exclude_filter`) |
| `assets/characters/<id>/idle_8dir_v53@2x.png` | diam, 12 frame × 8 arah, 96×144 px per frame |
| `assets/characters/<id>/walk_8dir_v53@2x.png` | jalan, 24 frame × 8 arah |
| `assets/characters/<id>/poses_v53@2x.png` | 16 pose (urutan `Actor.POSES`) × 4 arah × 2 frame |
| `assets/characters/<id>/*_v53.png`, `poses.png` | sprite pixel lama 1x (masih ada; dipakai jika file @2x dihapus) |

Baris arah (sama dengan `Actor.facing8`): 0 bawah, 1 kiri-bawah, 2 kiri, 3 kiri-atas, 4 atas,
5 kanan-atas, 6 kanan, 7 kanan-bawah.

## Langkah mengganti model
1. Taruh GLB baru di `assets/characters/arland/model/Arland.glb` (atau Sofia). Syarat: tinggi sekitar
   2 unit, kaki di y = 0, wajah menghadap +Z, warna vertex atau tekstur.
2. `godot --headless --path . --import`
3. Render frame: `xvfb-run godot --path . --rendering-driver opengl3 tests/charrender/render_sheets.tscn`
   (di Windows/macOS cukup jalankan scene itu dari editor). Frame mentah tersimpan di
   `user://charframes/`.
4. Susun sheet: `python3 tools/char_sheets.py "<folder user://charframes>"`
5. Jalankan game dan cek, lalu `godot --headless --path . tests/logic_test.tscn`.

## Animasi tanpa rig
Model saat ini tidak punya rig, jadi gerak dibuat oleh shader `tests/charrender/walk_rig.gdshader`:
- kaki: kedua kaki dirapatkan ke porosnya masing-masing dan "selaput" geometri di antara paha
  dibuang, jadi terlihat dua kaki; berayun 26° dari pinggul; lutut kaki belakang menekuk 38°;
- lengan: hanya bagian terluar (lengan + tangan, |x| > 0.305) yang berayun 38° berlawanan dengan kaki;
- badan bernapas, naik sedikit di antara langkah, bisa membungkuk dan duduk (lutut ditekuk).

Batas yang ditemukan saat pengujian:
- Lengan menyatu dengan badan pada model ini. Ayunan jalan di atas 38° membuat punggung menggembung,
  dan gestur pose dibatasi ±22°. Melambai, bersorak,
  dan tos tampil sebagai bahasa tubuh kecil, bukan lengan terangkat.
- Wajah dari samping murni kurang terbaca, jadi arah samping dirender di 72°.
- Ukuran (`HEIGHT` di `tools/char_sheets.py`): Arland 134 px, Sofia 126 px (@2x), sama dengan sprite lama.

Dengan model yang punya rig dan animasi (idle, jalan, gestur), `render_sheets.gd` bisa memutar
AnimationPlayer per frame, sehingga gestur lengan menjadi utuh.

## Kembali ke sprite lama
Hapus ketiga file `*@2x.png` di folder karakter. `Actor` otomatis memakai sprite 1x lama.
