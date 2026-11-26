# CHANGELOG — V8.0 "The Definitive Overhaul"

## V8.9 — map kota: Riverside, Taman Kota, Bukit Bintang bertingkat
Ketiga map kini punya elevasi nyata (sistem yang sama dengan Plaza), tanpa memindahkan titik
quest, pintu, atau spawn.
- **Riverside**:
  - hutan dan padang di utara kini berada di teras (+34) di balik dinding batu, tepat di tepi
    promenade, dengan pagar besi di atasnya;
  - **tangga besar** selebar 312 turun dari jalan setapak tengah ke dek pandang, diapit tiang
    ber-pot bunga dan pot pohon;
  - tangga barat di jalur ke pantai dan tangga timur di dekat bangku;
  - bangku, tempat sampah dan bedeng bunga dipindah ke promenade.
- **Taman Kota**: kuartal timur laut (pelataran gazebo, gerbang Rain Garden, hutan musim gugur)
  menjadi teras (+30) dengan dinding batu dan barisan bunga di atasnya. Tangga batu berada di
  tempat jalan gazebo naik dari halaman timur.
- **Bukit Bintang**:
  - puncak bukit kini benar-benar 70 lebih tinggi dari lembah, jadi tebing di selatan adalah jurang
    sungguhan (bayangan, kamera cutscene);
  - observatorium berdiri di **panggung batu** (+20) dengan tangga depan dan tiang ber-pot bunga;
  - bangku pelataran dipindah ke lantai bawah.
- Dermaga belum diubah. Garis pantainya rapat dengan titik quest, jadi saya kerjakan terpisah.
- Validator: Riverside kembali di bawah 900 prop (895) setelah ditambah pagar.

## V8.8 — tiga map mimpi cerita mendapat identitas sendiri
Sebelumnya, dari titik spawn, map-map ini tampak seperti hutan mimpi yang sama (audit V8, poin 5).
Sekarang landmark setiap map mengikuti perannya di cerita. 10 prop baru digambar dari kode
(`tools/artkit/memoryscape.py`).
- **Memory Garden** (prolog, "The Beginning of Us"):
  - "Gerbang pulang" kini berupa buku raksasa yang terbuka di atas dua pilar berbunga. Halaman
    kirinya bergambar bunga (yang dilihat Sofia), halaman kanannya bintang (yang dilihat Arland),
    dan di antara pilarnya ada tirai cahaya;
  - buku kenangan di atas mimbar menyambut di dekat titik datang;
  - setiap keping cahaya punya alas batu sendiri.
- **Arsip Memudar** (Bab 5): arsip yang benar-benar terlihat seperti arsip. Ada rak-rak tinggi yang
  bagian atasnya memudar ke kabut dan lembaran kertas lepas di rumput. Di gema pertama berdiri
  lemari katalog perpustakaan, dan di gema ketiga ada meja arsip dengan amplop "Untuk Sari" yang
  tidak pernah dikirim (menggantikan kotak surat).
- **Kenangan Gazebo** (Bab 6, Taman Kota empat puluh tahun lalu): lampu taman modern diganti lampu
  gas besi tuang dari masa itu, dan ada tiang poster tua di titik amati "Poster tua". Perubahan di
  map ini paling kecil. Gazebo dan bangku sengaja tetap sama dengan Taman Kota, karena cerita
  bilang "Gazebonya sama. Bangkunya sama."
- Ukuran map, pintu, spawn, titik amati, dan semua titik quest tetap sama. Save schema 8.

## V8.7 — remaster map Perumahan: teras rumah, gang samping, Gang Melati
- Pintu depan tiga rumah di sisi selatan menghadap ke kamera, tetapi map dulu berakhir tepat di
  pintunya dan jalan setapak dari pagar menuju bagian belakang rumah. Sekarang map diperluas ke
  selatan (1200×896 → 1200×1296). Rumah-rumah itu berdiri di **teras** (elevasi nyata 40) dengan
  jalan setapak depan, pot bunga di teras rumah, dan **tangga batu dari tiap pintu** turun ke bawah.
- **Dua gang samping** di antara rumah kini bisa dilewati, dari gerbang pagar trotoar sampai teras.
  Setiap gang punya tangga turun sendiri, jadi total ada 5 tangga.
- Area bawah yang baru: **Gang Melati** (jalan bata dengan lampu) dan **taman warga** berisi
  pos ronda (gazebo), sumur, kebun warga (dipindah dari halaman lama), ayunan, jemuran,
  tempat minum burung, bangku, pohon, dan pagar tanaman. Ayam kini berkeliaran di kebun.
- 3 titik amati baru: Pos Ronda, Ayunan, Jemuran. Masing-masing punya kalimat untuk route Arland
  dan Sofia.
- 2 prop baru digambar dari kode: ayunan dan jemuran (`tools/artkit/townsquare.py`).
- Tidak bisa lagi berjalan "di belakang" rumah, yaitu di tanah yang tertutup gambar rumah.
- Semua titik quest, titik amati lama, NPC, pintu (perpustakaan, rumah Nenek Sari, Jalan Kota)
  dan spawn tetap di koordinat lama. Save schema 8, tanpa migrasi.
- Tooling: penulis `elevation.json` dipindah ke `tools/worldgen/terrace.py` (`write_elevation`),
  dipakai oleh Jalan Kota dan Perumahan.

## V8.6 — remaster map Jalan Kota: teras dan Alun-alun Bawah
- Jalan Kota tidak lagi datar. Map diperluas ke selatan (1200×896 → 1200×1296). Jalan dan
  trotoar kini berada di atas **teras** setinggi satu tingkat (elevasi nyata 40, sistem yang sama
  dengan Plaza). Tepinya berupa **dinding penahan** dari batu potong dengan **pagar balustrade**
  dan tiang ber-pot bunga.
- **Dua tangga batu** (barat dan timur) turun ke **Alun-alun Bawah**, area baru yang berisi:
  - pelataran melingkar dengan air mancur bertingkat (koin di dasar kolam) dan 8 lampu;
  - pergola wisteria dengan dua bangku;
  - sudut kafe dengan payung meja dan lapak;
  - promenade selatan dengan lapak, gerobak, papan pengumuman, dan bangku;
  - taman bunga di kaki dinding, pagar tanaman, burung dan kucing.
- 3 titik amati baru: Air Mancur Alun-alun, Pergola Wisteria, Pagar Batu. Masing-masing punya
  kalimat untuk route Arland dan Sofia.
- 6 prop baru digambar dari kode (`tools/artkit/townsquare.py`): balustrade, 3 tiang ber-pot
  bunga, pergola wisteria, pot pohon di kaki tangga.
- `tools/worldgen/terrace.py`: alat bersama untuk melukis dinding teras dan tangga, sehingga map
  lain bisa memakainya.
- Semua yang di utara y=736 tetap di koordinat lama: toko, pintu, titik amati, spawn, titik
  masuk dari Plaza dan Perumahan. Save lama tetap aman (schema 8, tanpa migrasi). Taman pohon yang
  dulu tak terjangkau di selatan trotoar diganti dinding teras.

## V8.5 — dialog: adegan bertemplat ditulis ulang (Phase 07, langkah 1)
- Audit cerita lengkap dengan angka: `docs/STORY_AUDIT_V8.md`.
- `tools/story_v8.py` (bisa dijalankan ulang, teks asli di `tools/story_v8_orig.json`):
  - 36 adegan acara harian `V49-WE-*` yang 5 dari 6 barisnya identik kini masing-masing berupa
    percakapan sendiri tentang tempat itu, dari sudut pandang route (Arland/Sofia), lengkap dengan
    humor dan detail kecil (sup "secukupnya", kacamata berembun, kompas yang berputar, dan lainnya);
  - 26 adegan `WE27-*`: kalimat generiknya diganti kalimat yang khas untuk adegan itu;
  - 28 adegan kilas balik: vonis narator yang menggurui dihapus;
  - 6 pasang kilas balik Bab 6 yang identik di kedua route kini berbeda per route dan merujuk
    kejadian di cerita.
- Baris berulang ≥3×: 18 → 8; "yang penting" 53 → 18; "kenangan" 114 → 66.
- ID adegan, flag, dan pemicu tidak berubah (save aman). Kedua route tamat (EPI_FREE), 0 error.

## V8.4 — potret dialog dari model baru
- 12 ekspresi potret untuk Arland dan Sofia dirender dari GLB yang sama, sehingga wajah di kotak dialog
  kini cocok dengan karakter di dunia game. Ekspresi digambar di atas wajah model
  (`tools/portraits.py`, inpainting OpenCV agar tidak ada tambalan warna), gaya pixel 2× seperti
  potret lama. Arland kini juga punya `tersenyum` dan `pikir`, Sofia punya `serius`.
- Potret V7 disimpan di `portraits_v7/` (tidak ikut APK). Diuji di dialog sungguhan (autopilot
  kamar Sofia, prolog).

## V8.3 (tahap 4) — karakter dari model GLB
- Model Arland & Sofia dari user (`Arland_Sofia_Cuby_3D_V5_Free`) dirender menjadi sprite 8 arah @2x:
  idle (12 frame), jalan (24 frame, kaki melangkah bergantian), dan 16 pose untuk cutscene.
  Alat: `tests/charrender/render_sheets.tscn` + `tools/char_sheets.py`; panduan di `docs/CHARACTERS.md`.
- Model tanpa rig, jadi gerak dibuat dengan rig prosedural di shader: dua kaki terpisah yang melangkah
  bergantian, lutut kaki belakang menekuk, tangan berayun 38° berlawanan dengan kaki, badan naik turun.
  Gestur pose dibatasi ±22° karena lengan menyatu dengan badan pada model ini (docs/CHARACTERS.md).
- Sprite lama tidak dihapus (dipakai lagi bila file @2x dihapus). GLB sumber tidak ikut APK.
- Potret dialog masih gambar lama.

## V8.2 (tahap 3)
Save schema tetap 8; hanya prop di tiga map mimpi yang berubah (pintu, spawn, titik quest sama).

### Landmark map mimpi
Empat aset baru digambar dari kode (`tools/artkit/dreamscape.py`, kit v6 + normal map):
- **Memory Bridge**: tiang **lentera bintang** di kedua sisi jembatan (3 per sisi) dan sebagai lampu
  jalur, serta **gerbang konstelasi** (bulan sabit + lima bintang untuk lima konstelasi) di plaza
  kedatangan. Gerbangnya bisa dilewati.
- **Hall of Tomorrow**: **Balai Hari Esok** akhirnya ada: balai berkolom dengan tiga pintu bercahaya
  (tiga masa depan) di belakang tiga lengkung, dengan matahari terbit di pedimennya.
- **Rain Garden**: **paviliun kaca** dengan rantai hujan dan lentera gantung menaungi altar lentera.
  Pemain bisa berdiri di bawahnya.

---

## V8.1 (tahap 2)
Save schema tetap 8; tidak ada ID quest, map, karakter, atau flag yang berubah.

### Clockwork Station punya identitas sendiri
- Empat aset baru digambar dari kode (`tools/artkit/clockwork.py`, aturan kit v6, plus normal map):
  **menara jam** (~7× tinggi karakter, jam berhenti di 10:10, roda gigi terlihat lewat jendela
  bundar), **gerbong kereta tua** di atas rel, **lampu peron berjam**, dan **roda gigi kuningan**
  setengah terkubur.
- Menara berdiri di atas plaza teka-teki jam utama; gerbong terlihat langsung dari titik spawn;
  lampu jam menggantikan lampu emas di sepanjang jalur; roda gigi menggantikan sebagian pohon.
- `dream_hd.py`: zona `clear` agar pohon tidak tumbuh di belakang landmark tinggi. Hanya area
  clockwork_station yang berubah; pintu, spawn, dan semua titik quest tetap sama (maptool 0 error).

### Living NPC: datang dan pergi lewat pintu
- Saat jadwal NPC berganti ketika pemain ada di area itu, NPC berjalan ke **pintu di rute
  terpendek menuju area tujuannya** (`World.first_hop`). Contoh: Pak Pos keluar lewat timur
  ke Jalan Kota. NPC yang datang muncul dari pintu asalnya (Kak Raka keluar dari pintu kafe) lalu
  berjalan ke tempatnya. Sebelumnya NPC langsung hilang atau muncul di tempat.
- NPC memakai pathfinding grid (A\*, sel 16 px) yang dibangun bertahap 3 baris per frame setelah masuk
  area, jadi tidak ada patah-patah di HP. Jika jalan buntu, NPC menyerah dengan aman (batas waktu
  sesuai jarak).
- Saat masuk area, pergantian langkah cerita, atau lompat waktu, NPC tetap langsung ditempatkan,
  supaya penempatan cerita tidak berubah.

### Weather 3.0: badai petir
- Sekitar separuh hari hujan menjadi badai: kilat (overlay lembut + cahaya 3D dingin dari atas,
  kedipan ganda, tidak pernah berkedip cepat), guntur yang datang 0,5–2,5 detik kemudian (makin jauh
  makin pelan), dan hujan lebih deras miring tertiup angin. Urutan cuaca harian tidak berubah.
- Suara `thunder.wav` disintesis sendiri (`tools/sfx_v8.py`), tanpa aset pihak ketiga.
- Pengaturan baru **Kilat petir: Nyala/Mati** untuk pemain yang peka terhadap kilatan (guntur tetap).

### QA
- Tes logika 54 → **58** (rute pintu NPC, badai hanya di sebagian hari hujan, opsi kilat, file suara).
- `tests/qa_npc.tscn`: skenario NPC pergi (Pak Pos → timur, Rara → barat) dan datang
  (Kak Raka dari kafe, Pak Harun dari barat) — semuanya OK.
- Kedua route dijalankan ulang dengan autopilot sampai tamat (lihat QA_REPORT_V8.md).

---

## V8.0 (tahap pertama)

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
