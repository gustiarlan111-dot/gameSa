# Dunia 3D (Upgrade 3) — interior (U2a), luar ruang (U2b), map mimpi (U2c)

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

---

# U2b — luar ruang

## 4. Sisi 3D objek padat (`tools/extrude_u2b.py`, `src/view3d/prop_extrude.gd`)
Objek luar ruang adalah sprite kit tanpa data kotak, jadi teknik prisma U2a diperluas untuk mengikuti
bentuk siluetnya:
- **Alat offline** menelusuri kontur luar alpha tiap sprite (Moore tracing) dan menyederhanakannya
  (RDP 0,6 px). Hasilnya disimpan di `props.json` sebagai `"ext": {"d": kedalaman, "p": [[x, hu, s, sx, sh], …]}`.
  Game tidak membaca tekstur dari GPU.
- **Dorongan ke belakang.** Setiap tepi kontur didorong ke belakang bidang sprite sejauh `d`.
  - Titik bergerak lurus di tanah (`s = 0`) atau searah sinar kamera (`s = 1`).
  - Alat menaikkan `s` titik demi titik sampai titik belakangnya, dilihat dari kamera permainan,
    tetap jatuh di atas lukisan (toleransi 0,75 px).
  - Hasilnya, gambar dari kamera permainan tidak berubah (diuji di `tests/logic_test.gd` §21). Saat
    kamera bergerak, sisi dan permukaan atas terlihat dan diterangi matahari sungguhan.
- **Kedalaman** = `ch` kotak kaki × 1,6, atau × 0,8 untuk pagar dan rel, dalam batas 4–48 px.
- **Yang dilewati:** pohon, semak, rumput, bunga, struktur terbuka (gazebo, ayunan, jemuran), dan
  bangunan (bangunan sudah punya kotak `_add_volume`).
- **Tanaman.** Pada pot dan tiang berguci, daun hijau beserta bunga di sekitarnya (dilebarkan 3 px)
  dikeluarkan dari kontur, jadi hanya pot atau tiangnya yang bervolume. Kalau tidak, semak terekstrusi
  terbaca sebagai tong hijau.
- **Cakupan:** 85 jenis objek (batu, tiang lampu, bangku, pagar, pot, peti, kios, mobil, sumur, air
  mancur, dan lain-lain).
- **Render:** satu mesh per jenis, satu `MultiMesh` per jenis per area. Paling berat di Plaza: +30
  draw call dan ±10 ribu segitiga.
- Sisi tidak menerima bayangan (alasannya sama dengan prisma U2a), tetapi ikut memberi bayangan.
- Saat objek memudar karena menutupi pasangan, sisinya ikut disembunyikan.
- `kit_extra.py` dan `artkit/registry.py` menghitung ulang `ext` setiap kali menggambar ulang sprite.
  Semua alat menulis `props.json` lewat `tools/propsjson.py` (daftar angka di satu baris).

## 5. Kabut pagi (`src/view3d/world_mist.gd`, `src/fx/mist.gdshader`)
- **Bentuk:** tiga lembar kabut di ketinggian 0,08, 0,3, dan 0,62 m yang mengikuti kamera.
  - Noise diambil di koordinat dunia pada grid 2 px map, sehingga kabut diam di tanah dan hanyut
    oleh angin.
  - Bentuknya gumpalan dengan tanah bersih di antaranya.
  - Tanpa dither: dither Bayer mirip semut televisi di samping sprite yang difilter halus (K7).
- **Waktu** (`strength_at`): paling tebal 05.00–07.00 dan hilang pukul 09.00; tipis saat senja
  (×0,3) dan malam (0,12).
- **Cuaca:** saat hujan minimal 0,45, ×1,2 saat berawan, ×0,4 saat berangin (dengan angin 3× lebih
  cepat).
- **Area:** map alam ×0,8, termasuk Hutan Bisik dan Bukit Bintang yang memakai cahaya mimpi; map kota
  ×0,5. Map mimpi lain dan gua tidak berkabut (bagian dari U2c).
- **Warna:** putih kebiruan saat subuh, merah muda saat senja, biru di malam hari, abu-abu saat hujan.
- Kabut jarak lingkungan 3D bertambah sedikit mengikutinya (+0,0025 × kekuatan). Versi pertama
  +0,006 membuat seluruh layar pudar krem.
- Teras yang ditinggikan berada di atas kabut, jadi kabut berkumpul di tanah rendah.

## 6. Partikel dunia (`src/view3d/world_particles.gd`)
- **Daun dan kelopak:**
  - Gugur dari tajuk pohon di sekitar kamera. Titik pancarnya diperbarui saat kamera bergeser 64 px.
  - Warnanya mengikuti pohon: sakura dan bunga merah muda, pohon musim gugur oranye, pinus dan
    pohon gelap hijau tua, lainnya hijau.
  - Jumlahnya mengikuti kerapatan pohon (12–40). Daun hanyut dan berputar, lebih cepat saat
    berangin, dan berhenti saat hujan.
- **Kunang-kunang 3D:**
  - 50 cahaya di ketinggian 0,2–2,0 m dengan glow malam, aktif dari senja sampai subuh.
  - Ada di map alam dan area ber-ambience *fireflies*. Di map mimpi menyala terus.
  - Menggantikan kunang-kunang 2D datar, yang dulu juga muncul di siang hari.
  - Saat menyala, sistemnya langsung penuh (`preprocess`).
- Kelopak 2D (*petals*) dan kupu-kupu tetap.

## 7. Jembatan (`tools/bridges_u2b.py`)
Jembatan Taman Kota dan tiga jembatan kanal Plaza dulu dilukis rata di permukaan air. Tambalannya
idempoten, hanya mengganti entrinya sendiri:
- **Tinggi** di `elevation.json`:
  - Jembatan Plaza melengkung (tinggi 6/8/6 di tengah kanal).
  - Dek Taman Kota naik 4 dengan landaian 8 px di kedua ujung.
  - Dari kamera permainan gambarnya tetap. Pasangan berjalan naik ke jembatan, dan kamera cutscene
    melihat jembatan sungguhan.
- **Pagar dan tiang** di `maps.json`, dengan sisi 3D:
  - pagar kayu di tepi utara dan selatan dek Taman Kota;
  - tiang di keempat sudut tiap jembatan Plaza (tiang kayu di jembatan papan, patok batu di
    jembatan batu).
- `taman_kota_hd.py` dan `plaza_hd.py` memanggilnya saat `--apply`.
- Catatan: `plaza_hd.py` tidak lagi menghasilkan ulang map Plaza yang ter-commit (111 ribu piksel
  dan daftar prop berbeda), jadi Plaza **tidak** dibuat ulang. Tambalan hanya menyentuh data.

**Uji di layar:** `SHOT_NOVOL=1` mematikan sisi 3D luar ruang, sama seperti prisma interior.

---

# U2c — identitas 6 map mimpi

Setiap map mimpi kini punya ciri yang tidak bisa tertukar. Semuanya tetap masuk akal sebagai tempat
nyata, sebab ada kemungkinan cerita dibuat realistis nanti (opsi A/B, belum diputuskan).

| Map | Landmark (`dream_hd.py` THEMES `specials` + `clear`) | Efek (`world_particles.gd` / `world_mist.gd` `DREAM`) |
|---|---|---|
| Lantern Field | dua lapak festival, bendera segitiga, untaian lentera | 30 lentera terbang naik ke langit, kunang-kunang, kabut tipis hangat |
| Star Path | observatorium di ujung bukit, bangku kayu di samping teleskop | debu bintang biru-putih, bintang jatuh tiap ±4,5 detik (`atmosphere.gd`, ambience *stars*) |
| Starfall Village | lapak pasar dan untaian lentera di dekat alun-alun | asap dari cerobong tiap pondok, percik hangat, kabut tipis, bintang jatuh |
| Eternal Garden | air mancur bertingkat, pergola wisteria, ayunan | kelopak sakura gugur dari pohonnya |
| Moonlight Lake | bangku menghadap danau, teratai di dekat tepi | kabut tebal di atas air (0,6), kunang-kunang |
| Gua Kristal | (tata letak gua tetap) | 48 butir debu kristal toska yang melayang |

- **Lentera cerita Lantern Field.** Enam lentera yang dinyalakan pasangan di Bab 4 adalah sprite 1x
  terakhir di map HD. `tools/lantern_unlit_u2c.py` menggambar versi padam dari `hd_lantern_post`:
  kap kertasnya kusam tanpa halo, dan nama filenya sengaja tanpa "lantern_post" agar tidak diberi
  cahaya oleh `world.gd`. Versi menyala sekarang `hd_lantern_post`. File 1x lama tetap ada karena
  minigame lentera memakainya.
- **Regenerasi.** `dream_hd.py` menghasilkan ulang map yang ter-commit secara identik (dicek di awal
  U2c, berbeda dengan `plaza_hd.py`). Karena itu kelima map dibuat ulang dengan `--apply`. Zona
  `clear` menggeser sebaran pohon di sekitar landmark.
