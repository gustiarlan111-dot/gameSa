# Story v7 — upgrade besar cerita & quest

Semua perubahan dibuat oleh `tools/story_v7.py` (bisa dijalankan ulang; data asli langkah/adegan
yang diubah disimpan di `tools/story_v7_orig.json`). Langkah lama tetap ada, jadi save di langkah
mana pun tetap bisa lanjut (save schema 8). Tetap 2 route dan 1 ending canon.

## Alur baru per bab
| Bab | Perubahan |
|---|---|
| Prolog | Kilasan Lumi dan baris surat tua "Untuk S..., maaf aku..." saat pulang dari Memory Garden. |
| 2 | Arland mengirim jadwal kencan per menit (dua sudut pandang). Di senja dermaga mereka jadian: 3 pilihan kata per route (`V7_JADIAN`). |
| 3 | Arland diam-diam memperbaiki proyektor tua untuk galeri Sofia. Sofia berlatih "aku cuma butuh kamu datang" lalu mundur. Kunjungan ke **Rumah Nenek Sari** (bingkai kosong bertanda W, payung tua) menggantikan dua daftar belanja. Di piknik, kalimat Sofia terpotong oleh "kejutan" Arland. |
| 4 | Draf pesan jam acara Sofia ternyata tidak pernah terkirim (andil kecil Sofia, tanggung jawab utama tetap Arland). Sofia memilih cara melanjutkan presentasi (3 pilihan, bergema di Bab 6). Kunjungan ulang galeri dilewati. |
| 5 | Nenek Sari mulai lupa suara Wira; halaman "W & S" memudar di dunia nyata. Map mimpi baru **Arsip yang Memudar**: teka-teki mendengarkan (3 gema dua suara, jawab dengan benar, salah boleh diulang). Clockwork Station dan Moonlight Lake keluar dari jalur utama (pilihan Moonlight dipindah ke Arsip). |
| 6 | Cermin keempat menawarkan menghapus hari galeri; pemain menolaknya. Klimaks di map baru **Gazebo, Empat Puluh Tahun Lalu**: menyaksikan Sari menunggu dan Wira berlari membawa payung, lalu menceritakan kisah dua sisi sehingga halaman mereka pulang. |
| Epilog | Nenek Sari ingat suara Wira; setelah tamat, foto dipasang di bingkai kosong (Rumah Nenek Sari). |

Lintas bab: 9 baris moral yang menggurui dipangkas atau diganti tindakan; teks objektif meta
("boleh dicoba ulang", "(0/3)", "route lain") dibersihkan.

## Map baru
| Area | Pembuat | Masuk dari |
|---|---|---|
| `rumah_sari` | `tools/worldgen/rooms_hd.py rumah_sari` | Pintu rumah bata merah di Distrik Perumahan |
| `arsip_memudar` | `tools/worldgen/dream_hd.py arsip_memudar` | Halaman abu-abu di Starfall Village (Bab 5) |
| `kenangan_gazebo` | `tools/worldgen/dream_hd.py kenangan_gazebo` | Pintu Hall of Tomorrow (Bab 6) |

## QA
`STORY_STEP=<langkah> STORY_AREA=<area> [STORY_ROTATE=1] godot -- --story <route> <out> <frame,...>`
menjalankan autopilot cerita dari langkah tertentu; `STORY_ROTATE=1` mencoba pilihan bergiliran
(untuk teka-teki gema).
