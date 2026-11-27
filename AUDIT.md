# AUDIT — Fase 0, Master Prompt "Upgrade Besar"

Tanggal: 26 November 2026. Basis: `main` = 27be4ea (V8.10). Belum ada kode game yang diubah. Satu-satunya
tambahan di audit ini adalah alat ukur `tests/bench_map.tscn`.

## 1. Ringkasan
Game ini stabil di semua jalur yang bisa diuji di sini. Kedua route tamat oleh autopilot, 58 tes
logika lulus, 32 map lolos validator, dan save lama terbaca. Visualnya sudah HD-2D dengan bayangan,
elevasi, dan pantulan air. Ada tiga hal yang paling jauh dari standar rilis komersial:
1. **Performa dan ukuran belum terbukti di HP.** APK 293 MB, padahal targetnya < 200 MB, dan 69% dari
   ukuran itu adalah tile map yang disimpan lossless. FPS belum pernah diukur di perangkat Android.
2. **Isi dunia 3D masih berupa sprite tegak.** Perabot, bangunan, pagar, dan batu belum jadi mesh.
   Jendela interior selalu menampilkan langit siang. Beberapa NPC tidak punya mata di tampilan samping.
3. **Struktur permainan masih banyak pola "datangi N titik".** Saat ini ada satu ending kanon. Setelah
   Bab 4 tidak ada konflik baru di antara Arland dan Sofia.

## 2. Hal di master prompt baru yang bertentangan dengan keputusan sebelumnya (perlu keputusan)
| # | Master prompt baru | Kondisi / keputusan sebelumnya | Opsi | Rekomendasi |
|---|---|---|---|---|
| K1 | "Tidak ada opsi kualitas grafis" | V8.0 menambah menu Pengaturan dengan preset Rendah/Sedang/Tinggi/Ultra (preset Rendah mematikan bayangan, glow, lampu, efek layar, pantulan) | a) Hapus preset, satu tampilan. b) Satu tampilan di menu, dengan penurunan otomatis diam-diam bila FPS jatuh. c) Biarkan | **b**: pemain melihat satu versi, HP lemah tetap jalan |
| K2 | "Dilarang push langsung ke main" | V8.0–V8.10 di-*fast-forward* ke main atas izin Anda ("Anda push saja") | Mulai sekarang: satu upgrade = satu branch = satu PR | Ikuti aturan baru. Audit ini sudah berupa PR |
| K3 | "Minimal 3 ending + 1 true ending" | Prompt V8: dua route, satu ending kanon. Aturan baru juga melarang mengubah alur utama tanpa izin | a) Ending kanon tetap sebagai *true ending*, ditambah 3 ending lain yang ditentukan pilihan dan hubungan. b) Tetap satu ending | **a**, tetapi butuh izin Anda dan bahan cerita |
| K4 | "Mini-game unik per bab" | Anda meminta "Minigame skip dlu" | a) Kerjakan di U4. b) Tetap ditunda | Tanyakan ke Anda |
| K5 | "Dilarang menempel PNG lama sebagai map" | Tanah map adalah tekstur HD yang **digambar oleh kode** (`tools/worldgen`), bukan PNG lama. Objek berdiri adalah sprite | a) Tanah tetap tekstur kode, objek jadi mesh (U2). b) Tanah juga jadi mesh/terrain 3D | **a**: tanah bertekstur adalah cara HD-2D yang dipakai Octopath |
| K6 | Karakter "pixel art HD buatan sendiri" | Arland & Sofia dirender dari GLB milik Anda (V8.3), bukan pixel art gambar tangan | a) Tetap GLB. b) Gambar ulang pixel art | Tanyakan. GLB tanpa rig membatasi animasi (pegangan tangan, pelukan) |
| K7 | Pixel art "WAJIB filter nearest, tanpa blur" | Tile tanah dan prop memakai filter linear + mipmap (agar tidak berkilau saat kamera bergerak) | a) Nearest + sedikit supersampling. b) Tetap | Uji dulu di HP. Nearest pada kamera miring sering berkilau (*shimmer*) |
| K8 | "100/100 terbukti di HP sungguhan" | Saya tidak punya akses ke HP. Lingkungan ini tidak bisa mengukur FPS (lihat §4) | Anda menjalankan APK benchmark lalu mengirim angkanya | Wajib untuk U1 |

## 3. Fakta di master prompt yang saya cek
| Klaim | Hasil cek | Status |
|---|---|---|
| ±14 fps di beberapa map (1.800+ objek) | Tidak bisa diverifikasi di sini (§4). Map terberat secara struktur adalah Hutan Bisik: 1.862 prop, 4.097 node, VRAM 174 MB | belum terbukti |
| Belum pernah dites di HP | Benar | benar |
| Perabot interior masih sprite tegak | Benar: 11 ruangan `room3d`, perabot berupa quad tegak | benar |
| Jendela interior selalu langit siang | Benar: jendela dilukis menyatu dengan sprite dinding (`tools/worldgen/rooms_hd.py`) | benar |
| Mata NPC hilang dari samping | Sebagian: di tampilan samping **6 dari 22** NPC manusia jelas tanpa mata (Bayu, Bimo, Darmo, Dito, Harun, Ina), 2 belum pasti (Darto, Eko) | sebagian |
| Kumis Pak Darmo aneh | Benar: di tampilan samping dan belakang ada **pita putih besar** melintang wajah | benar |
| Quest banyak pola "kumpulkan benda" | Cerita utama: 17 dari 166 langkah (10%) berupa "kumpulkan/datangi N". Side: ±14 dari 26 side quest berpola cari/antar/kumpulkan, ditambah 30 kepingan bintang, 5 batu, 5 foto | sebagian. Target "hapus 80%" perlu jelas berlaku untuk yang mana |
| Route Sofia tipis | **Dari sisi jumlah, tidak**: Sofia 2.152 baris vs Arland 2.079 (docs/STORY_AUDIT_V8.md). Yang mungkin kurang adalah sudut pandang atau rahasia sendiri, dan itu penilaian cerita | tidak sesuai data |
| Tidak ada konflik baru setelah Bab 4 | Sebagian: Bab 5–6 berisi konflik cermin (Wira–Sari, "The Quiet"), bukan konflik baru antara Arland dan Sofia | sebagian |
| Dialog menggurui | Sudah dikurangi di V8.5 (28 vonis narator dihapus). Masih ada: "harus" 120×, "belajar" 69×, "ternyata" 43× dari 3.714 baris | masih ada |
| 94 cutscene | 62 aksi `cine` di langkah cerita utama (sisanya mungkin di side/event, belum dihitung) | belum dicek penuh |

## 4. Pengukuran

### Tes dan build (dijalankan di audit ini)
| Pemeriksaan | Hasil |
|---|---|
| `tests/logic_test.tscn` | 58 / 58 lulus |
| `tools/maptool.py check` (32 map) | 0 error, 8 peringatan (7 karena prop > 900, 1 lainnya) |
| Autopilot route Sofia / Arland (V8.10) | tamat di `EPI_FREE`, frame 160.977 / 159.127, 0 script error |
| `tests/qa_saves.tscn` (memuat save hasil autopilot) | OK untuk kedua route |
| Build APK | **di CI** (GitHub Actions, sukses untuk 27be4ea). Build APK lokal tidak bisa karena Android SDK tidak terpasang di lingkungan ini |

### Ukuran APK (293,4 MB, dibongkar dari rilis terbaru)
| Isi | Ukuran | Catatan |
|---|---:|---|
| Tile tanah map (120 file .ctex) | **201,4 MB** | disimpan lossless (`compress/mode=0`) |
| Engine (`libgodot`, 2 ABI: arm64-v8a + armeabi-v7a) | 43,7 MB | armeabi-v7a hanya untuk HP 32-bit lama |
| Audio (212 OGG) | 24,3 MB | |
| Tekstur lain (prop, karakter, UI) | 17,3 MB | |
| Sisanya | ±6 MB | |

Jalur ke < 200 MB (estimasi, keyakinan ±75%): tile tanah lossy WebP kualitas tinggi (201 → ±50–80 MB)
dan membuang ABI 32-bit (−±22 MB). Hasilnya kira-kira 120–150 MB. Kualitas visual WebP harus dibandingkan
dengan mata sebelum dipakai.

### Profiling 32 map (`tests/bench_map.tscn`, PC tanpa GPU, renderer software, 1280×720)
**FPS tidak bisa diukur di sini.** Semua map, termasuk kamar terkecil (19 prop), terkunci di ±7,5 fps karena
renderer software. Angka FPS dari lingkungan ini tidak bermakna. Yang bermakna adalah angka struktur di bawah,
dan angka itu sama di HP.

| Map | Prop | Node | Draw call | Objek/frame | Primitif | VRAM (MB) | Muat (ms, PC) |
|---|---:|---:|---:|---:|---:|---:|---:|
| hutan_bisik | 1862 | 4097 | 170 | 224 | 7532 | 174 | 2460 |
| plaza | 648 | 1738 | 122 | 217 | 11556 | 129 | 664 |
| taman_kota | 873 | 2193 | 129 | 224 | 7214 | 122 | 870 |
| bukit_bintang | 960 | 2209 | 89 | 170 | 9469 | 113 | 679 |
| eternal_garden | 1262 | 2793 | 80 | 161 | 4468 | 112 | 810 |
| dermaga | 916 | 2212 | 167 | 236 | 26564 | 109 | 648 |
| starfall_village | 1088 | 2452 | 77 | 158 | 4158 | 107 | 663 |
| riverside | 895 | 2157 | 149 | 218 | 9400 | 105 | 563 |
| lantern_field | 1137 | 2541 | 133 | 187 | 4492 | 104 | 746 |
| perumahan | 244 | 851 | 113 | 208 | 5882 | 95 | 504 |
| star_path | 918 | 2195 | 87 | 168 | 3738 | 95 | 615 |
| memory_garden | 900 | 2185 | 103 | 184 | 3334 | 93 | 436 |
| jalan_kota | 297 | 959 | 138 | 233 | 5204 | 87 | 339 |
| hall_of_tomorrow | 758 | 1933 | 97 | 178 | 2762 | 87 | 654 |
| clockwork_station | 670 | 1621 | 78 | 159 | 2740 | 86 | 470 |
| rain_garden | 768 | 1789 | 76 | 157 | 3314 | 84 | 482 |
| memory_bridge | 763 | 1914 | 91 | 172 | 2950 | 83 | 329 |
| moonlight_lake | 703 | 1656 | 75 | 156 | 2878 | 82 | 758 |
| kenangan_gazebo | 519 | 1289 | 74 | 168 | 2122 | 74 | 409 |
| arsip_memudar | 521 | 1275 | 80 | 174 | 2238 | 73 | 379 |
| gua_kristal | 106 | 500 | 78 | 132 | 668 | 62 | 468 |
| perpustakaan | 38 | 328 | 99 | 153 | 306 | 59 | 244 |
| cafe | 36 | 325 | 76 | 134 | 268 | 53 | 209 |
| ruang_dua_surat | 30 | 302 | 91 | 172 | 344 | 47 | 199 |
| galeri_komunitas | 38 | 321 | 107 | 188 | 376 | 47 | 228 |
| arcade | 26 | 284 | 86 | 140 | 280 | 42 | 215 |
| ruang_arsip | 16 | 255 | 67 | 148 | 296 | 41 | 216 |
| dapur | 21 | 270 | 76 | 130 | 260 | 41 | 187 |
| arland_room | 19 | 266 | 72 | 126 | 252 | 41 | 285 |
| sofia_room | 20 | 275 | 76 | 130 | 260 | 41 | 159 |
| toko_bunga | 29 | 294 | 92 | 146 | 292 | 41 | 215 |
| rumah_sari | 17 | 260 | 68 | 122 | 244 | 41 | 163 |

Catatan:
- Waktu muat di PC 0,16–2,46 s. Di HP kelas menengah biasanya 2–4× lebih lambat (perkiraan, belum diukur),
  jadi **Hutan Bisik kemungkinan melewati target 3 detik**, dan Taman Kota serta Eternal Garden mendekatinya.
- VRAM map luar 62–174 MB. Untuk HP 4 GB masih aman, tetapi Hutan Bisik paling berat.
- Draw call 67–170 per frame berkat MultiMesh per tekstur. Jumlahnya rendah untuk mobile.

## 5. Tabel masalah
Keparahan: K = kritis (menghalangi rilis), T = tinggi, S = sedang, R = rendah.
| # | Area | Masalah | Keparahan | Dampak skor |
|---|---|---|---|---|
| 1 | Performa | FPS, panas, dan memori belum pernah diukur di HP Android | K | Performa, Stabilitas |
| 2 | Performa | APK 293 MB (target < 200 MB); tile tanah lossless 201 MB | T | Performa, Kesan pertama |
| 3 | Performa | Hutan Bisik: 1.862 prop / 4.097 node / 174 MB VRAM / muat 2,5 s di PC | T | Performa |
| 4 | Performa | Belum ada overlay FPS di dalam game dan belum ada benchmark di HP | S | Performa |
| 5 | Visual | Perabot interior, bangunan, pagar, jembatan, batu masih sprite tegak, belum mesh | T | Visual |
| 6 | Visual | Jendela interior selalu langit siang | S | Visual |
| 7 | Visual | Belum ada ambient occlusion. SSAO tidak tersedia di GL Compatibility, jadi perlu AO yang di-*bake* ke tekstur atau mesh | S | Visual |
| 8 | Visual | 6 map mimpi dan 11 interior belum mendapat identitas visual V8 | S | Visual |
| 9 | Visual | Filter linear (bukan nearest) pada pixel art (K7) | R–S | Visual |
| 10 | Karakter | 6–8 NPC tanpa mata di tampilan samping; Pak Darmo berpita putih di samping/belakang | T | Karakter, Kesan pertama |
| 11 | Karakter | Arland & Sofia dari GLB tanpa rig: lengan menyatu dengan badan, tidak bisa pegangan tangan atau pelukan sungguhan | T | Karakter, Cerita |
| 12 | Karakter | NPC punya jadwal dan bisa datang/pergi lewat pintu, tetapi belum bereaksi pada cuaca, belum mengobrol antar-NPC, dan belum mengingat pilihan pemain | S | Karakter |
| 13 | Quest | Pola "datangi/kumpulkan N" di 17 langkah utama dan ±14 side quest | T | Quest, Gameplay |
| 14 | Cerita | Satu ending; tidak ada konflik baru Arland–Sofia setelah Bab 4 | T | Cerita |
| 15 | Cerita | Bab 1 sangat tipis (35 baris bersama), dialog masih menggurui di sebagian adegan | S | Cerita, Kesan pertama |
| 16 | Cerita | Belum ada STORY_BIBLE.md | S | Cerita |
| 17 | Gameplay | Minigame ditunda atas permintaan Anda (K4) | S | Gameplay |
| 18 | UI/UX | Save 2 slot per route + autosave (target 3 slot manual); belum ada ukuran teks, kecepatan teks, mode buta warna, gamepad, getar | S | UI/UX |
| 19 | Audio | Musik adalah hasil sintesis dari kode (72 lagu). Belum ada tema Arland/Sofia yang berkembang per bab, belum ada musik adaptif | S | Audio |
| 20 | Rilis | Belum ada ikon final, splash, trailer, dan screenshot Play Store | S | Kesan pertama |

## 6. Rencana upgrade (urutan dan estimasi)
Estimasi dalam sesi kerja seperti sesi hari ini (keyakinan rendah, ±50%). Setiap upgrade menjadi satu branch
dan satu PR dengan tes, screenshot sebelum/sesudah, dan skor.
| Urutan | Upgrade | Isi utama | Estimasi | Butuh dari Anda |
|---|---|---|---|---|
| 1 | **U1 Performa** | Overlay FPS tersembunyi, APK benchmark (semua map otomatis, hasil disimpan ke file), tile WebP, hanya arm64, LOD/culling prop jauh, pecah Hutan Bisik | 2–3 sesi | **Jalankan APK benchmark di HP Anda** dan kirim hasilnya |
| 2 | U3a Perbaikan karakter | Mata NPC di semua arah, sprite Pak Darmo, cek semua NPC di 8 arah | 1 sesi | — |
| 3 | U2 Dunia 3D | Perabot dan bangunan jadi mesh bertekstur pixel art, jendela mengikuti jam dan cuaca, AO bake, identitas 6 map mimpi dan 11 interior | 4–6 sesi | Keputusan K5, K7 |
| 4 | U5 Cerita | STORY_BIBLE.md, konflik setelah Bab 4, Bab 1, kurangi dialog menggurui, ending | 3–5 sesi | **Izin K3 dan bahan cerita nyata** |
| 5 | U4 Gameplay & Quest | Ubah quest "kumpulkan" jadi puzzle/aksi, quest bercabang, sistem hubungan, Buku Kenangan | 4–6 sesi | Keputusan K4 |
| 6 | U3b Karakter | Animasi interaksi (pegangan tangan, pelukan, memberi benda), NPC bereaksi pada cuaca dan mengobrol | 2–4 sesi | Keputusan K6 |
| 7 | U6 Audio | Tema Arland/Sofia/cinta per bab, musik adaptif, mixing | 2–3 sesi | Bila ingin kualitas "film": komposer/aset musik sungguhan |
| 8 | U7 UI/UX | 3 slot + autosave, aksesibilitas, gamepad, getar, tes 16:9/18:9/20:9/tablet | 2 sesi | — |
| 9 | U8 Rilis | Onboarding, ikon, splash, screenshot, trailer | 2 sesi | Akun Play Console, tes di beberapa HP |

## 7. Skor awal (sebelum upgrade)
Penilaian jujur berdasarkan yang bisa saya lihat dan ukur di sini. Belum ada yang terbukti di HP.
| Aspek | Skor | Alasan |
|---|---:|---|
| Visual | 7 | HD-2D dengan bayangan, elevasi, pantulan, landmark cerita; tetapi objek masih sprite, interior datar |
| Performa | 3 | Tidak terbukti di HP, APK 293 MB, map terberat berat |
| Gameplay | 5 | Eksplorasi dan pilihan ada; minigame ditunda; banyak "datangi N titik" |
| Quest | 4 | Pola kumpul dominan di side quest; quest bercabang sedikit |
| Cerita | 6 | Dua route lengkap dan konsisten; satu ending; konflik setelah Bab 4 kurang; Bab 1 tipis |
| Karakter | 5 | Arland & Sofia baru; NPC tanpa mata dari samping; tanpa animasi interaksi |
| Audio | 5 | Soundscape per area bagus; musik sintesis tanpa tema per tokoh |
| UI/UX | 6 | Bingkai emas konsisten, pengaturan ada; aksesibilitas dan gamepad belum |
| Stabilitas | 7 | 0 script error di kedua route, save aman; belum diuji di HP |
| Kesan pertama | 5 | Prolog sinematis; ukuran unduhan besar; Bab 1 terburu-buru |
| **Total** | **53 / 100** | |

## 8. Cara mengulang pengukuran
```
godot --path . --rendering-driver opengl3 --resolution 1280x720 tests/bench_map.tscn -- --bench <area>
```
Mencetak satu baris `BENCH> {json}`: waktu muat, waktu frame, draw call, objek, primitif, node, memori, VRAM.
