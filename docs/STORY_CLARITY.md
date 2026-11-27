# U5c — cerita fantasi yang lebih mudah dipahami

Pilihan pemilik game: **C, fantasinya tetap tetapi diperjelas**, dengan **satu ending**. Alur, langkah
quest, pilihan, dan ending tidak berubah. Yang ditambahkan hanya penjelasan dengan kata-kata biasa.
Semua perubahan dibuat oleh satu alat yang bisa dijalankan ulang: `python3 tools/story_u5c.py`.

## Masalah yang ditemukan saat audit
| Temuan | Angka |
|---|---|
| "buku" disebut tanpa pernah dijelaskan apa itu | 137× |
| "halaman" (memudar, pulang, berwarna) tanpa penjelasan aturannya | 183× |
| Lumi baru muncul di Bab 4, tanpa keterangan tugasnya | — |
| "The Quiet" dan "Kabut Lupa" adalah hal yang sama, tetapi tidak pernah dikatakan | 18× The Quiet |
| Nama tempat mimpi berbahasa Inggris (Lantern Field, Star Path, …) | 10 map |
| Tidak ada ringkasan "sebelumnya" untuk pemain yang lama berhenti main | 0 |

## Yang ditambahkan
1. **Aturan dunia di prolog** (adegan `P-X02`, saat buku pertama kali terbuka): 3 baris narator.
   - Apa itu Buku Kenangan.
   - Apa itu dunia kenangan, dan bahwa mereka bisa pulang kapan saja.
   - Kenapa halaman memudar dan cara menjaganya: jujur dan saling mendengar.
2. **Lumi** (adegan `C04-X02`, saat pertama bicara): 2 baris.
   - Tugasnya: menjaga buku dan memberi tahu halaman yang mulai memudar.
   - Kabut Lupa = "The Quiet" di surat tua. Ia bukan monster, melainkan sunyi.
3. **"Sebelumnya: …"** pada kartu judul setiap bab (C01–EPI), 2–3 kalimat.
   - Teksnya ada di `story.json` → `chapters[].recap`.
   - Kartu tampil lebih lama sesuai panjang teks.
4. **Nama tempat berbahasa Indonesia**, dengan nama lama di dalam kurung.
   - Contoh: Padang Lentera (Lantern Field), Desa Bintang Jatuh (Starfall Village), Balai Hari Esok.
   - 10 map mimpi (`maps.json` → `name`).
5. **Tab "Istilah" di Buku**: 9 istilah.
   - Setiap istilah terbuka saat babnya tercapai, jadi tidak membocorkan cerita.
   - Istilah yang belum terbuka tampil sebagai "◇ Belum muncul".
   - Datanya ada di `memory_book.json` → `glossary`.

## Yang sengaja tidak diubah
- Isi dialog lama: tidak ada baris yang dihapus atau ditulis ulang.
- Urutan langkah cerita: Sofia 118 langkah, Arland 115 langkah, identik dengan main.
- Pilihan, flag, ending, dan save. Format save tidak berubah, jadi tidak perlu migrasi.
- Nama internal area (id). Hanya nama tampilan yang berubah.

## Gambar
- `docs/screens/u5c/prolog_aturan.png`: tiga baris aturan di prolog.
- `docs/screens/u5c/kartu_bab.png`: kartu bab, sebelum dan sesudah ada "Sebelumnya".
- `docs/screens/u5c/buku_istilah.png`: tab Istilah di Bab 4. Enam istilah sudah terbuka.

## Cara mengulang
```
python3 tools/story_u5c.py                                     # data (idempotent)
SHOT_CARD=C05 godot --fixed-fps 60 --path . -- --shot sofia plaza 1450 1112 70 card.png
SHOT_BOOK=6 SHOT_STEP=C04_A_WAKE godot --path . -- --shot sofia plaza 1450 1112 70 book.png
```
