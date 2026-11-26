# QA REPORT — V8.0

## V8.2 (tahap 3) — ringkasan
| Pemeriksaan | Hasil |
|---|---|
| Tes logika | 58 / 58 lulus |
| Validator map: memory_bridge, hall_of_tomorrow, rain_garden | 0 error, 0 titik quest tak terjangkau |
| `--apply` tiga map | hanya `props` yang berubah; pintu dan spawn sama |
| Route Sofia / Arland sampai tamat | `EPI_FREE` di frame 160.077 / 159.427 (identik dengan V8.1), 0 script error |
| Screenshot landmark di game | `docs/screens/v8/dream_landmarks.png` |

---

## V8.1 (tahap 2) — ringkasan
| Pemeriksaan | Hasil |
|---|---|
| Tes logika | **58 / 58 lulus** |
| Validator map (32 area) | 0 error |
| `--apply` Clockwork Station | hanya area itu yang berubah; pintu, spawn, 26 titik quest sama; 0 titik tak terjangkau |
| Route Sofia sampai tamat | `EPI_FREE` di frame 160.077, 118 langkah, 0 script error |
| Route Arland sampai tamat | `EPI_FREE` di frame 159.427, 115 langkah, 0 script error |
| NPC pergi (qa_npc) | Pak Pos 10:00 → pintu timur (Jalan Kota); Rara 17:00 → pintu barat (Taman Kota) — OK |
| NPC datang (qa_npc) | Kak Raka 14:30 dari pintu kafe; Pak Harun 11:00 dari pintu barat — sampai di tempatnya, OK |
| Badai | screenshot hari ke-9 (badai) dengan dan tanpa kilat: `docs/screens/v8/storm.png` |
| Clockwork Station | screenshot spawn, plaza tengah, malam: `docs/screens/v8/clockwork_station.png` |

Tidak diuji: kilat dan pathfinding NPC di perangkat Android nyata (beban CPU grid NPC: 3 baris
sel per frame), dan bermain manual.

---

# V8.0 tahap 1

Lingkungan: Linux x86_64, **Godot 4.3-stable** (official), renderer `opengl3` di Xvfb dengan Mesa
llvmpipe (render CPU). Semua hasil di bawah berasal dari perintah yang benar-benar dijalankan pada
branch `v8.0`. Yang tidak dijalankan ditandai **tidak diuji**.

## Ringkasan

| Pemeriksaan | Sebelum (main) | V8.0 |
|---|---|---|
| Tes logika `tests/logic_test.tscn` | 43 / 43 lulus | **54 / 54 lulus** |
| Validator map `tools/maptool.py check` | 0 error (32 area) | **0 error** (32 area, + aturan tangga baru) |
| Screenshot semua 32 area (spawn) | 32 tampil | **32 tampil, 0 script error** |
| Route Sofia, autopilot dari awal | macet di `PRO_SHARDS` (prolog)* | **tamat** (`EPI_FREE`, langkah `final`) |
| Route Arland, autopilot dari awal | macet di `PRO_SHARDS` (prolog)* | **tamat** (`EPI_FREE`, langkah `final`) |
| Save awal / tengah / akhir dimuat ulang | — | **OK** (PRO_GIFT, C03_PICNIC, EPI_FREE) |
| Save buatan build lama dibaca V8 | — | **OK** (schema 8, tanpa migrasi) |
| Ukuran paket (`--export-pack Android`) | 312,4 MB | **247,9 MB** |
| Game dijalankan dari PCK baru | — | **OK** (plaza, cafe, hutan_bisik) |

\* Macet itu disebabkan autopilot lama yang berjalan lurus tanpa pathfinding, **bukan bug game**:
validator map sudah memastikan ketiga keping cahaya bisa dijangkau dari spawn.

## Alur cerita kedua route
Perintah: `godot --headless --fixed-fps 60 --path . -- --story <route> out 2500000`

| Route | Langkah dilalui | Bab | Frame sampai tamat | Script error |
|---|---|---|---|---|
| Sofia | 115 | PRO → C01 → C02 → C03 → C04 → C05 → C06 → EPI | 155.769 | 0 |
| Arland | 112 | PRO → C01 → C02 → C03 → C04 → C05 → C06 → EPI | 155.119 | 0 |

- Keduanya berakhir di langkah canon ending yang sama (`EPI_FREE`, ditandai `final`). Satu canon
  ending tetap terjaga.
- Tidak ada softlock pada alur utama. Yang sebelumnya menahan autopilot adalah keterbatasan
  autopilot sendiri, dan semuanya sudah diatasi: jalan lurus (diganti A\*), puzzle/minigame yang
  menunggu input, area tujuan yang salah di hari bebas, dan jawaban gema yang salah tanpa dicoba ulang.
- Penting: autopilot **melewati** puzzle dan minigame (17–18 kali per route, tercatat `QA>`). Ini
  membuktikan alur cerita bisa diselesaikan, **bukan** bahwa setiap minigame menyenangkan atau bebas
  bug saat dimainkan tangan. Minigame tetap diuji logikanya oleh `logic_test`.
- Frame di atas adalah waktu autopilot yang terburu-buru (±43 menit game time), bukan perkiraan
  durasi bermain manusia.

## Elevasi dan tangga
- 9 tangga (Plaza 7, Hutan Bisik 2) masing-masing menghubungkan dua ketinggian berbeda
  (`maptool` + `logic_test`). Validator terbukti menolak tangga rusak (uji negatif: slope dihapus,
  dan kedua ujung disamakan tingginya → keduanya terdeteksi error).
- Screenshot di bawah, tengah, dan atas tangga tebing Hutan Bisik: karakter terlihat utuh. Versi
  pertama implementasi V8 sempat membuat badan karakter tertelan dinding tangga; itu ditemukan dari
  screenshot lalu diperbaiki (`_wall_push`).
- Kecerahan dinding/tangga sama dengan lukisan aslinya (normal tanah tetap ke atas, tanah tidak
  membayangi dirinya sendiri, karena matahari di game ini berada di belakang adegan).
- Pergerakan 2D, collision, dan pintu tidak berubah. Validator navigasi tetap 0 error.
- Dari kamera gameplay, dataran tinggi di tepi atas layar bergeser hingga ±15 px (efek parallax
  dari kamera perspektif). Di sekitar pemain (tengah layar) pergeserannya praktis nol.

## Kamera / oklusi
- Titik spawn Taman Kota: sebelumnya pasangan tertutup penuh oleh pohon; sekarang pohon memudar
  (dither) dan pasangan terlihat. Lihat `docs/screens/v8/occlusion_taman_kota.png`.
- Bangunan tidak ikut memudar (punya volume 3D). **Tidak diuji**: berjalan di belakang rumah.

## Pengaturan
- `logic_test`: nilai di luar batas dipotong, nilai tak dikenal kembali ke default, preset Rendah
  tersimpan dan mematikan bayangan/pass layar, 30 FPS diterapkan ke `Engine.max_fps`, file
  `settings.json` rusak → default tanpa crash.
- Screenshot: jendela Pengaturan (`docs/screens/v8/settings.png`) serta preset Rendah + joystick
  kanan (`docs/screens/v8/preset_low_left_hand.png`).

## Regresi visual
Semua 32 area dishot ulang di titik spawn dan dibandingkan per piksel dengan baseline. Perbedaan
di area tanpa elevasi (0,1–7% piksel) berasal dari animasi acak (angin, kelopak, kunang-kunang).
Empat area dengan perbedaan terbesar dicek bersebelahan: tidak ada regresi.

## Tidak diuji / keterbatasan
- **Perangkat Android nyata**: FPS, frame pacing, RAM, baterai, background/resume, touch di layar
  sungguhan, resolusi tablet. Render llvmpipe tidak mewakili GPU ponsel, jadi tidak ada klaim FPS.
- **Build APK**: tidak dibangun di sini (tidak ada Android SDK/Java/template). Isi paket diverifikasi
  lewat PCK. APK dibangun oleh GitHub Actions (`.github/workflows/android.yml`).
- Bermain manual end-to-end oleh manusia.
- Temuan collision kecil: ellipse collider hanya diuji pada 5 titik kotak kaki, sehingga di satu
  titik Plaza autopilot sempat tersangkut di tepi ellipse. Pemain manusia bisa memutar; belum diubah.

## Cara mengulang
```
godot --headless --path . --import
godot --headless --path . tests/logic_test.tscn
python3 tools/maptool.py check
godot --headless --fixed-fps 60 --path . -- --story sofia out 2500000     # cari "STEP> EPI_FREE"
godot --headless --fixed-fps 60 --path . tests/qa_saves.tscn              # muat & lanjutkan save
xvfb-run godot --path . --rendering-driver opengl3 --resolution 1280x720 -- --shot sofia hutan_bisik 640 624 60 out.png
```
