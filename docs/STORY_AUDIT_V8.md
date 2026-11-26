# Audit cerita V8 (Phase 07, langkah 1)

Diukur dari `assets/data/story.json` dan `quests.json` (hanya adegan yang benar-benar dipanggil oleh
quest atau map: 763 dari 919). Skrip ukur: dijalankan ulang setiap ada perubahan cerita.

## Angka
| | Route Arland | Route Sofia |
|---|---|---|
| Baris dialog (bersama + eksklusif) | 2.079 | 2.152 |
| Kata | 20.548 | 21.038 |
| Perkiraan waktu baca saja | ±2 jam | ±2 jam |

Baris per bab (bersama / Arland / Sofia): PRO 38/58/58 · C01 35/38/38 · C02 124/273/307 ·
C03 70/226/247 · C04 161/180/162 · C05 195/209/226 · C06 164/167/183 · EPI 119/46/46.

Target prompt master: cerita utama ±6 jam. Dengan ±2 jam membaca per route ditambah eksplorasi,
teka-teki, dan minigame, satu route kira-kira 3–4 jam (perkiraan, belum diukur dengan pemain sungguhan).

## Temuan
1. **Adegan bertemplat** (sudah diperbaiki di V8.4, `tools/story_v8.py`):
   - 36 adegan acara harian `V49-WE-*` memiliki 5 dari 6 baris yang identik. Pemain mendengar
     percakapan yang sama 18× per route.
   - 26 adegan `WE27-*` menyisipkan satu kalimat generik yang sama.
   - 28 adegan kilas balik ditutup vonis narator yang sama ("…bukan sebagai jawaban yang paling benar").
   - Hasil: baris berulang ≥3× turun dari 18 menjadi 8 (sisanya umpan balik teka-teki); "yang penting"
     53 → 18; "kenangan" 114 → 66.
2. **Perbedaan route**: dari 120 pasang adegan route, **6 identik kata per kata** (kilas balik Bab 6) dan
   3 lagi lebih dari 60% sama. Ke-6 pasang itu ditulis ulang per route di V8.4. Catatan koreksi:
   versi awal audit ini menyebut "30% baris identik", tetapi angka itu menghitung obrolan bersama di dalam
   adegan yang sudah punya baris khas masing-masing route, dan itu wajar.
3. **Kata yang terlalu sering**: "selalu" 92×, "kenangan" 66×, "terima kasih" 30×. Membuat dialog terasa
   seperti tulisan, bukan obrolan.
4. **Bab 1 sangat tipis** (35 baris bersama + 38 per route) dibanding Bab 2 (±400 per route). Perkenalan
   karakter terasa terburu-buru.
5. Epilog panjang di bagian bersama (119 baris) tetapi pendek per route (46): penutup sudut pandang
   masing-masing kurang terasa.

## Yang butuh keputusan pemilik cerita
Bagian di bawah ini menyentuh isi hubungan Arland dan Sofia, sehingga sebaiknya ditulis dengan bahan
dari pemilik game, bukan dikarang sendiri:
- Momen nyata atau kenangan yang ingin dimasukkan (cara mereka bertemu, kebiasaan kecil, lelucon pribadi).
- Cara mereka biasa bicara satu sama lain (panggilan sayang, bahasa campur, gaya chat).
- Bagian cerita V7 yang menurut pemilik paling kurang.
- Apakah Bab 1 perlu diperpanjang, dan konflik besar (galeri, Bab 4) tetap seperti sekarang atau tidak.

## Usulan urutan kerja berikutnya
1. Menambah monolog batin khas route di adegan bersama yang penting (jadian, hari galeri, klimaks).
2. Memperpanjang Bab 1 dengan perkenalan yang lebih natural (menunggu bahan dari pemilik).
3. Mengurangi "selalu" / "kenangan" / "terima kasih" di dialog yang bukan momen emosional.
