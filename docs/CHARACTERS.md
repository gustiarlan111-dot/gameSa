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

## Upgrade 6 (U3b): lari, emosi, bergandengan, pelukan
- **Siklus lari** 8 arah, 16 frame (`run_8dir_v53@2x.png`). Langkah lebih panjang, lutut menekuk lebih dalam,
  badan condong ke depan. Actor memakainya saat berlari. Kalau file tidak ada, Actor kembali ke siklus jalan
  yang dipercepat.
- **5 pose emosi** (baris 16–20 `poses_v53@2x.png`): `senang`, `malu`, `sedih`, `marah`, `kaget`. Bahasa
  tubuh (condong, bahu, tangan ≤22°) ditambah gerak kecil di Actor (lompat kecil, goyang, turun, getar,
  tersentak). Saat dialog, pembicara otomatis memakai pose yang cocok dengan ekspresi baris
  (`src/logic/acting.gd`). Pose dari cutscene selalu diutamakan.
- **Pasangan dalam satu sprite** (`tests/charrender/render_couple.tscn`). Kedua GLB dirender bersama
  dengan rig yang sama. Sofia diskalakan 0,9325 agar tingginya sama dengan sprite tunggalnya. Hasil:
  `assets/characters/couple/hand_walk@2x.png` (12 frame × 4 arah), `hand_idle@2x.png`, `hug@2x.png`
  (frame 160×144 @2x). Rig sekarang punya `arm_lk`/`arm_rk`, jadi tangan yang digandeng tidak ikut berayun.
  - **Bergandengan**: mode "Bergandengan Tangan" (aksi romansa) sekarang benar-benar terlihat. Pemain
    menggambar sprite pasangan, dan partner ikut tersembunyi di sisinya (`World._hand_walk`). Saat cutscene,
    keduanya kembali menjadi dua sprite.
  - **Pelukan**: perintah cutscene `pair` dengan `kind: hug` memakai sprite pelukan (kepala Sofia di bahu
    Arland). Baris 0 dipakai bila Arland di kiri, baris 3 bila Sofia di kiri.
  - Batasan: lengan model menyatu dengan badan, jadi tangan yang bergandengan bertemu di sela tubuh
    (tidak terlihat jari bertaut), dan pelukan bekerja karena lengan tersembunyi di balik tubuh pasangan.
- Mengulang: `KIND_ONLY=hand_walk|hand_idle|hug xvfb-run godot --path . --rendering-driver opengl3
  tests/charrender/render_couple.tscn`, lalu `python3 tools/char_sheets.py --couple <charframes>`.

## Potret dialog (V8.4)
- `tests/charrender/render_portrait.tscn` merender kepala dan bahu dari depan
  (env `P_SIZE=1.5 P_Y=1.40`), lalu `python3 tools/portraits.py "<folder user://portraitframes>"`
  membuat 12 ekspresi: normal, tersenyum, senang, tertawa, malu, kaget, sedih, khawatir, serius,
  pikir, lega, jatuh_cinta.
- Model hanya punya satu wajah, jadi ekspresi digambar di atasnya pada kanvas 88×110: mata asli
  dihapus dengan inpainting OpenCV (gradasi kulit diteruskan, tanpa tambalan warna rata), lalu mata,
  alis, mulut, rona pipi, air mata, keringat, dan hati digambar, kemudian diperbesar 2× tanpa
  penghalusan (176×220, gaya pixel).
- Posisi fitur per karakter ada di `FACE` dalam `tools/portraits.py`. Jika model diganti, ukur ulang
  posisinya dari render dasar.
- Potret gambar tangan V7 disimpan di `assets/characters/<id>/portraits_v7/` (tidak ikut APK).
  Untuk kembali, salin isinya ke `portraits/`.

## Kembali ke sprite lama
Hapus ketiga file `*@2x.png` di folder karakter. `Actor` otomatis memakai sprite 1x lama.
