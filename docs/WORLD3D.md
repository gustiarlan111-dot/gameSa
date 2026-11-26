# Dunia 3D — interior (Upgrade 3, bagian U2a)

Ruangan bertanda `room3d` (11 ruangan, `tools/worldgen/rooms_hd.py` `ROOMS3D`) dibangun seperti map luar:
lantai datar, dinding belakang dan perabot berdiri sebagai sprite yang condong ke belakang (`TILT`), sama
seperti karakter. U2a menambah tiga hal tanpa melukis ulang perabot.

## 1. Jendela hidup (`src/view3d/room_light.gd`, `src/fx/window_sky.gdshader`)
- Generator mencatat kaca setiap jendela yang tidak menyala (`Room.window(lit=False)`) ke
  `maps.json` → `windows: [[x, y, w, h], …]`. Tujuh ruangan punya jendela: kamar Arland, kamar Sofia,
  kafe, dapur, toko bunga, perpustakaan, rumah Sari.
- Di game, kaca itu ditimpa quad yang menggambar langit pada grid texel yang sama dengan pixel art
  (`floor(UV * size * 2)`). Langit berisi gradasi, awan berjalan, bintang berkelip, bulan, siluet bukit
  dan atap, hujan, dan kilat. Warnanya diambil dari tabel `KEYS` menurut menit (dini hari, fajar, pagi,
  siang, sore, senja, malam). Saat hujan, warnanya menjadi abu-abu dan cahayanya tinggal ×0,22.
- Cahaya matahari masuk lewat:
  - bercak di lantai yang miring mengikuti jam (`RoomLight.skew_at`: +36 px pagi, −36 px sore);
  - berkas cahaya tipis;
  - debu yang melayang di berkas (`CPUParticles3D`, 18 partikel);
  - satu `SpotLight3D` per jendela tanpa bayangan, yang menghangatkan benda di dalam bercak. Detailnya:
    - Letaknya 1,2 m di depan dan 0,8 m di atas jendela, dengan redaman jarak hampir datar (0,3).
      Awalnya lampu ini hanya 0,25 m dari dinding, sehingga dinding di bawah kaca kafe putih terbakar.
    - Lampu ini tidak menerangi dinding belakang. Dinding berada di render layer `WALL_LAYER`, dan
      `light_cull_mask` lampu sorot tidak mencakupnya.
    - Lampu mati di bawah kekuatan 0,2, jadi cahaya bulan cukup berupa bercak dan berkas. Di malam hari,
      slot cahaya per objek GL Compatibility dibutuhkan lampu kamar.
    - Lampu juga mati di preset yang mematikan `lamps`.
- Sejak U2a, generator tidak lagi melukis bercak matahari tetap di bawah jendela untuk ruangan 3D
  (`Room.dynamic_light`).

**Yang dicoba lalu dibatalkan.** Matahari ruangan (`DirectionalLight3D`) sempat diputar supaya masuk dari
jendela, agar bayangan jatuh ke arah penonton. Hasilnya, muka depan perabot dan pasangan menjadi abu-abu
karena membelakangi cahaya, dan muncul garis-garis *shadow acne*. Lukisan perabot mengandaikan cahaya dari
depan-kiri, jadi cahaya kunci ruangan tetap dari arah penonton.

## 2. AO bake (`tools/worldgen/interior.py` `Room._ao`)
Bayangan kontak lama (`drop`) berbentuk huruf L di kanan-bawah setiap perabot, karena cahaya lukisan
datang dari kiri-atas. Arah cahaya sekarang berubah mengikuti jam, jadi di ruangan 3D bayangan itu
diganti oklusi tanpa arah:
- lantai menggelap di sekeliling pita kaki perabot (tinggi pita 4–12 px);
- kegelapan meluruh eksponensial (jarak 3,6 px) dan sedikit lebih panjang ke depan;
- kekuatannya diambil dari parameter `k` lama, jadi perabot yang dulu berbayangan tipis tetap tipis.

Oklusi pojok ruangan dan pita gelap di kaki dinding tetap seperti sebelumnya.

## 3. Volume perabot (`src/view3d/furniture_volume.gd`)
**Masalahnya.** Kotak 3D sungguhan dengan muka depan tegak akan menembus kepala karakter yang berdiri di
depannya. Penyebabnya, sprite karakter condong ke belakang ±0,48 × tingginya.

**Solusinya.** Muka depan tetap sprite lukisan. Di belakangnya ditambahkan prisma: dua sisi dan satu atas.
- Seluruh prisma berada di belakang bidang sprite. Karakter di depan perabot tetap di depan, dan
  kedalaman antarsprite tetap seperti V8.
- Tepi atas prisma dipotong searah sinar kamera (pitch 38°). Dari kamera permainan, siluetnya sama
  persis dengan lukisan (diuji di `tests/logic_test.gd` §20).
- Saat kamera bergeser, perspektif menampakkan sisi yang menghadap tengah layar. Perabot di kiri layar
  menampakkan sisi kanannya, dan sebaliknya. Di bagian bawah layar tampak pula pita tipis permukaan atas.
- Prisma memberi bayangan padat. Prisma tidak menerima bayangan, karena posisinya di belakang sprite
  hanya akibat sprite yang condong. Tanpa itu, sisinya tertutup bayangan muka depannya sendiri.
- Warna sisi diambil dari satu kolom texel di dalam garis tepi muka depan, jadi tidak ada gambar baru.
  Sisi kiri ×0,80 dan sisi kanan ×0,64 (cahaya lukisan dari kiri-atas). Normalnya condong ke atas
  seperti trik normal sprite ruangan. Permukaan atas memakai satu texel dari pojok dalam permukaan atas
  lukisan.
- Saat perabot memudar karena menutupi pasangan, prismanya disembunyikan tetapi bayangannya tetap ada
  (`SHADOWS_ONLY`).

**Data.** `stand_up` di `rooms_hd.py` menyimpan kotak utama setiap perabot, yaitu `box()` terbesar yang
dipanggil langsung oleh fungsi perabot itu, ke `props.json`:

```
"vol": [kiri, atas, lebar, tebal_atas, tinggi_depan]   # px map, dihitung dari titik kaki sprite
```

Ada 143 perabot yang punya blok, misalnya lemari, rak buku, kabinet, konter, meja tulis, mesin arcade,
peti, dan alas pajangan. Ranjang, sofa, tanaman, dan lampu dilukis bebas tanpa `box()`, jadi tetap sprite
saja.

**Kedalaman** (`FurnitureVolume.depth_for`). Kotak yang tampak sama dengan lukisan dari kamera berpitch
38° memiliki:
- tinggi = 1,253 × tinggi muka depan;
- kedalaman = 1,6 × tebal permukaan atas lukisan.

Perhitungan: sinar kamera melalui tepi belakang permukaan atas lukisan dipotongkan dengan bidang atas
kotak.

Kedalaman prisma memakai nilai terbesar dari 1,6 × tebal atas dan ⅓ lebar. Nilainya dibatasi oleh tinggi
blok, ruang kosong ke dinding belakang, dan maksimum 40 px.

**Uji di layar.** `SHOT_NOVOL=1` mematikan prisma untuk screenshot pembanding.

## Biaya
- Satu `MeshInstance3D` (3 muka, 6 segitiga) per perabot berblok: 7–24 per ruangan (perpustakaan 24,
  ruang dua surat 21, arcade 20). Teksturnya
  sama dengan sprite, jadi tidak ada memori tekstur tambahan.
- Satu quad langit, dua mesh aditif, satu emitor debu, dan satu `SpotLight3D` (tanpa bayangan, hanya siang) per
  jendela.
- FPS di HP belum diukur: renderer server terkunci ±7,5 fps (lihat AUDIT.md §4).
