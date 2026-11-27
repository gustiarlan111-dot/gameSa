# CHANGELOG — V8.0 "The Definitive Overhaul"

## Upgrade 1, bagian U1a — panggung resolusi dan penghitung FPS
Detail: `docs/PERFORMANCE.md`.
- **Tablet 2.5K** (misalnya Redmi Pad 2, 2560×1600): dunia game kini digambar pada 1280×800 lalu
  diperbesar 2×. Beban GPU untuk dunia turun ±2/3. Pixel art tetap tajam, dan UI serta teks tetap
  digambar pada resolusi layar.
- Ponsel 1080p tidak berubah.
- **Pengaturan → Penghitung FPS:** menampilkan FPS dan ukuran gambar dunia di bawah HUD (bawaan: mati).

## Upgrade 3, bagian U2e — suasana 3D untuk 7 map mimpi yang tertinggal
Detail: `docs/WORLD3D.md` (U2e). Gambar: `docs/screens/u2e/`.
- **Taman Kenangan:** kelopak lavender, biru, dan merah muda gugur dari pohonnya, ditambah kilau dan kabut tipis.
- **Taman Hujan:** kabut taman basah dan kunang-kunang.
- **Stasiun Jam:** debu emas melayang di cahaya lampu.
- **Jembatan Kenangan:** kabut biru di atas air dan debu bintang.
- **Balai Hari Esok:** kelopak gugur dan kilau emas.
- **Arsip yang Memudar:** kabut abu-abu dan debu kertas.
- **Gazebo, Empat Puluh Tahun Lalu:** kabut siang yang hangat.
- Kini ke-13 map mimpi punya suasana 3D sendiri.

## Upgrade 5, bagian U5d — satu nama untuk satu tempat
- Nama Inggris lama tempat mimpi kini diganti di semua teks yang dibaca pemain: label pintu, misi,
  keterangan, teka-teki, isi Buku, dan dialog (104 teks). Contoh: "Ke Starfall Village" menjadi
  "Ke Desa Bintang Jatuh", "Nyalakan 5 batu bintang di Star Path" menjadi "… di Jalan Bintang".
- Prolog dan tab Istilah menyebut "Memory Book" dan "Buku Kenangan" sebagai benda yang sama.

## Upgrade 5, bagian U5c — cerita fantasi diperjelas
Detail: `docs/STORY_CLARITY.md`. Alur, pilihan, dan ending tetap sama. Hanya penjelasan yang ditambahkan.
- **Prolog:** saat buku pertama kali terbuka, narator menjelaskan dalam 3 kalimat apa itu Buku Kenangan,
  apa itu dunia kenangan, dan kenapa halaman bisa memudar.
- **Lumi:** saat pertama bicara, ia menyebut tugasnya dan menjelaskan bahwa Kabut Lupa dan
  "The Quiet" adalah hal yang sama.
- **Kartu bab:** setiap bab dibuka dengan "Sebelumnya: …", ringkasan 2–3 kalimat.
- **Nama tempat:** 10 map mimpi kini bernama Indonesia, misalnya Padang Lentera dan Jalan Bintang.
  Nama lama ditulis di dalam kurung.
- **Buku → tab "Istilah":** 9 istilah dunia cerita. Setiap istilah terbuka saat babnya tercapai.

## Upgrade 3, bagian U2c — identitas map mimpi
Detail: `docs/WORLD3D.md` (U2c). Gambar: `docs/screens/u2c/`.
- **Lantern Field:** festival lentera dengan lapak, bendera, untaian lentera, dan lentera terbang yang
  naik ke langit malam. Enam lentera cerita kini HD.
- **Star Path:** bukit pengamatan dengan observatorium di ujung jalan, bangku kayu di samping
  teleskop, debu bintang, dan bintang jatuh.
- **Starfall Village:** pasar kecil di dekat alun-alun dan asap dari cerobong tiap pondok.
- **Eternal Garden:** air mancur bertingkat, pergola wisteria, ayunan, dan kelopak sakura yang gugur.
- **Moonlight Lake:** kabut di atas air, kunang-kunang, bangku menghadap danau, dan teratai.
- **Gua Kristal:** debu kristal yang melayang.
- Semua unsur baru tetap masuk akal di tempat nyata, jadi tetap terpakai kalau cerita dibuat realistis.

## Upgrade 3, bagian U2b — dunia luar 3D
Detail teknis: `docs/WORLD3D.md` §4–7. Perbandingan sebelum/sesudah: `docs/screens/u2b/`.

**Objek padat bervolume**:
- Ada 1.768 objek di semua map luar (85 jenis, misalnya batu, tiang lampu, bangku, pagar, pot, tong,
  peti, kios, mobil, sumur, dan air mancur).
- Saat kamera bergeser, sisi dan permukaan atas objek terlihat lewat perspektif dan diterangi matahari.
- Dari sudut kamera biasa, lukisannya tidak berubah.
- Bayangannya padat.
- Pada pot dan tiang berguci, hanya pot atau tiangnya yang bervolume; tanamannya tetap sprite.

**Kabut pagi**:
- Gumpalan kabut tanah yang hanyut, paling tebal pukul 05.00–07.00 dan hilang pukul 09.00.
- Tipis saat senja dan malam, lebih tebal saat hujan, menipis saat berangin.
- Terkumpul di tanah rendah; teras berada di atasnya.

**Partikel 3D**:
- Daun dan kelopak gugur dari pohon yang ada di sekitar. Kelopak merah muda dari sakura, daun oranye
  dari pohon musim gugur.
- Kunang-kunang bercahaya di berbagai kedalaman dari senja sampai subuh.
- Kunang-kunang 2D datar yang dulu muncul juga di siang hari kini digantikan.

**Jembatan**:
- Jembatan papan Taman Kota punya pagar kayu di kedua sisi dan dek yang sedikit lebih tinggi.
- Tiga jembatan kanal Plaza melengkung dan punya tiang di keempat sudutnya.
- Pasangan berjalan naik ke jembatan.

**Alat**:
- `tools/extrude_u2b.py`, `tools/bridges_u2b.py`, dan `tools/propsjson.py` (penulis `props.json`
  bersama).
- `kit_extra.py` dan `artkit/registry.py` menghitung ulang sisi 3D setiap kali menggambar ulang sprite.

## Upgrade 3, bagian U2a — interior 3D
Detail teknis: `docs/WORLD3D.md`. Perbandingan sebelum/sesudah: `docs/screens/u2a/`.

**Jendela hidup** di 7 ruangan (kamar Arland, kamar Sofia, kafe, dapur, toko bunga, perpustakaan, rumah Sari):
- Kaca menampilkan langit yang mengikuti jam dan cuaca: pagi, siang, senja, malam berbintang dengan bulan,
  mendung dan hujan, serta kilat. Langit digambar pada grid pixel yang sama dengan pixel art.
- Sebelumnya, jendela selalu menampilkan langit biru siang, termasuk tengah malam.
- Matahari masuk lewat jendela sebagai bercak cahaya di lantai yang miring ke kanan di pagi hari dan ke
  kiri di sore hari, ditambah berkas cahaya, debu yang melayang, dan lampu sorot yang menghangatkan
  perabot. Saat hujan, cahayanya redup dan abu-abu. Di malam hari hanya ada cahaya bulan yang lembut.

**Perabot bervolume** (143 perabot di 11 ruangan, misalnya lemari, rak buku, kabinet, konter, meja, mesin
arcade, peti, dan alas pajangan):
- Saat kamera bergeser, sisi samping dan pita permukaan atas perabot terlihat lewat perspektif.
- Dari sudut kamera biasa, lukisan pixel art tidak berubah sedikit pun.
- Perabot memberi bayangan padat.
- Karakter yang berdiri di depan perabot tidak pernah tertembus.

**AO bake**: bayangan kontak arah tetap (huruf L di kanan-bawah) diganti oklusi lembut di sekeliling kaki
perabot, karena arah cahaya sekarang berubah mengikuti jam.

**Perbaikan kecil**:
- 21 entri perabot kafe lama di `props.json` dihapus. Entri ini tidak dipakai dan gambarnya tidak ada.
- `rooms_hd.py` kini membuang entri perabot yang tidak ada lagi, dan menulis `props.json` dengan format
  aslinya (indentasi 2).

**Dicoba lalu dibatalkan**: matahari yang masuk dari jendela untuk bayangan ke arah penonton. Hasilnya,
muka depan perabot dan pasangan jadi gelap karena membelakangi cahaya.

## Upgrade 6 (U3b) — karakter dan NPC yang hidup
**Arland & Sofia**
- Siklus **lari** sungguhan, 8 arah, 16 frame.
- **5 emosi** tubuh: senang, malu, sedih, marah, kaget. Saat berbicara, karakter **memerankan ekspresi
  baris dialognya**. NPC memakai gestur kecil (tertawa, mengangguk, malu, terkejut, berpikir).
- **Bergandengan tangan**: mode "Bergandengan Tangan" sebelumnya hanya tersimpan di save tanpa terlihat
  apa-apa. Sekarang keduanya berjalan berdampingan sambil bergandengan, dalam satu sprite yang dirender dari
  kedua GLB sekaligus, di 4 arah dengan langkah serempak.
- **Pelukan sungguhan** di cutscene (`pair` hug): kepala Sofia bersandar di bahu Arland. Sebelumnya dua
  sprite saling mengulurkan tangan.
- **Payung saat hujan**, dan satu payung untuk berdua saat bergandengan.

**NPC**
- **Tetangga mengobrol**: dua NPC yang berdiri berdekatan saling menghadap dan berbicara lewat gelembung
  kata saat pasangan ada di dekatnya. Ada 48 obrolan (`assets/data/npc_chatter.json`):
  - obrolan umum sesuai pagi/siang/sore/malam, hujan atau cerah, dan bab cerita;
  - obrolan khusus 13 pasangan (Bu Rini–Kakek Darmo, Nenek Sari–Oma Ina, Dito–Tika, dan lainnya);
  - gosip tentang hal yang sudah dilakukan pasangan.
- **NPC mengingat pilihan pemain**: 19 dialog sekali-tampil (`tools/npc_memory_u3b.py`). Contoh: Bu Melati
  ingat warna pita yang dipilih Arland, Bang Juna ingat kencan yang dimulai dari arcade, Rara ingat baju
  kencan Sofia, dan Kakek Darmo, Pak Udin, Dito, Pak Pos, Kak Raka, Bu Laras, Nenek Sari ingat side quest
  yang sudah diselesaikan. Dialog ini muncul setelah dialog quest dan sebelum obrolan biasa, jadi tidak
  menutupi langkah quest.
- **Reaksi cuaca**: NPC yang tetap di luar saat hujan memakai payung (17 NPC sudah berteduh lewat jadwal
  mereka sejak sebelumnya). Saat kilat menyambar, NPC yang terlihat tersentak dengan tanda "!", dan Arland
  & Sofia ikut kaget.

## V8.10 — pantulan air, normal map yang tertinggal, bastion Dermaga
- **Pantulan di air** (baru, `src/view3d/water_reflect.gd` + `src/fx/water_reflect.gdshader`):
  - objek berdiri di dekat air terpantul terbalik di permukaannya: pohon, tiang dermaga, pagar,
    alang-alang, pelampung, gubuk;
  - karakter yang berjalan di tepi air (Arland, Sofia, NPC) juga terpantul;
  - pantulan beriak mengikuti permukaan, memudar makin jauh dari kaki, mengikuti cahaya
    siang/malam, dan hanya tampil di atas air terbuka (tidak di dek, dermaga, atau tepian);
  - dibuat tanpa kamera kedua, jadi aman untuk mode GL Compatibility di Android. Maksimal 400
    objek per map; disiapkan sekali saat masuk area (77–145 ms di PC uji);
  - menyala di preset Sedang/Tinggi/Ultra, mati di preset Rendah.
- **Normal map untuk 18 prop baru V8.6–V8.8** (balustrade dan tiangnya, pergola, pot tangga,
  ayunan, jemuran, gerbang buku, mimbar buku, alas keping, rak arsip, meja arsip, katalog kartu,
  tumpukan kertas, tiang poster, lampu gas). Sebelumnya cahaya di prop ini datar. Sekarang semua
  351 prop HD punya normal map.
- **Dermaga**: bukit pandang di pangkal dermaga kini berupa bastion bundar (+24) dengan dinding
  batu melengkung, tangga ke jalan dermaga, dan tiang ber-pot bunga. Titik panorama berada di
  atasnya. Pintu, spawn, dan titik quest tidak berubah.

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
