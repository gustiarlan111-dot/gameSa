#!/usr/bin/env python3
"""U5 (option C): the fantasy story, explained for players who do not usually play fantasy.

The plot, the quest steps and the single ending stay as they are. This only adds plain words:

  * the rules of the world, said once in the prologue when the book first opens (what the Memory
    Book is, what the memory worlds are, why a page fades);
  * who Lumi is, and that "Kabut Lupa" and "The Quiet" are the same thing, when Lumi first speaks;
  * a "Sebelumnya..." recap on every chapter card (story.json chapters[].recap);
  * Indonesian names for the dream places, the old English name in brackets (maps.json name);
  * a small glossary for the Memory Book's new "Istilah" tab, opening chapter by chapter
    (memory_book.json glossary).

Idempotent: inserted lines carry "u5c": true and are replaced on every run.
    python3 tools/story_u5c.py
"""
import json
from pathlib import Path

A = Path(__file__).resolve().parents[1] / 'assets/data'

INSERT = {
    # scene id: (insert after the line whose text starts with ..., [(speaker, text, emotion)])
    'P-X02': ('Halaman pertama menampilkan', [
        ('narrator', 'Buku itu adalah Memory Book, Buku Kenangan milik mereka berdua. Setiap kenangan yang mereka buat bersama tertulis di dalamnya sebagai satu halaman.', 'neutral'),
        ('narrator', 'Kalau sebuah halaman dibuka bersama, mereka bisa masuk ke dunia kenangan: tempat yang terbentuk dari kenangan itu. Rasanya seperti mimpi, dan mereka bisa pulang kapan saja.', 'neutral'),
        ('narrator', 'Tapi halaman bisa memudar, yaitu saat ada hal yang dipendam dan tidak diceritakan. Cara menjaganya sederhana: jujur, dan saling mendengar.', 'neutral'),
    ]),
    'C04-X02': ('Aku Lumi.', [
        ('lumi', 'Tugasku menjaga buku kalian, dan memberi tahu halaman mana yang mulai memudar.', 'neutral'),
    ]),
}
INSERT_AFTER_2 = {
    'C04-X02': ('Kalau dua orang berhenti saling mendengar', [
        ('lumi', 'Kabut Lupa itu yang di surat tua disebut "The Quiet". Bukan monster, cuma sunyi yang datang kalau tidak ada yang mau mendengarkan.', 'neutral'),
    ]),
}

RECAP = {
    'C01': 'Arland dan Sofia bertukar hadiah kecil di plaza. Sebuah buku bercahaya muncul: Buku Kenangan milik mereka berdua. Buku itu membawa mereka ke Taman Kenangan, dan di dalamnya ada surat tua yang belum selesai.',
    'C02': 'Teka-teki di kafe membawa mereka ke sebuah surat dua sisi. Surat itu milik Kakek Wira untuk Nenek Sari, pasangan yang kisahnya juga belum selesai.',
    'C03': 'Kencan-kencan kecil: kafe, gazebo, photobooth. Di senja dermaga mereka resmi jadian. Sofia mulai menyiapkan pameran kecilnya.',
    'C04': 'Mereka masak dan piknik bersama. Arland diam-diam memperbaiki proyektor tua untuk pameran Sofia. Di rumah Nenek Sari ada bingkai foto kosong bertanda W.',
    'C05': 'Di hari pameran, kursi Arland kosong. Hujan, kecewa, dan satu halaman buku memudar. Lumi, penjaga buku, mengajak mereka menyalakan lagi lentera dengan saling mendengar dan jujur.',
    'C06': 'Nenek Sari mulai lupa suara Kakek Wira, dan halaman "W & S" memudar. Arland dan Sofia menempuh jalan bintang masing-masing, lalu bersama menolong arsip yang memudar.',
    'EPI': 'Mereka menolak menghapus hari pameran, lalu menyaksikan kenangan empat puluh tahun lalu: Nenek Sari menunggu, Kakek Wira berlari membawa payung. Dengan menceritakannya dari dua sisi, halaman mereka pulang.',
}

NAMES = {
    'memory_garden': 'Taman Kenangan (Memory Garden)',
    'lantern_field': 'Padang Lentera (Lantern Field)',
    'star_path': 'Jalan Bintang (Star Path)',
    'starfall_village': 'Desa Bintang Jatuh (Starfall Village)',
    'eternal_garden': 'Taman Abadi (Eternal Garden)',
    'rain_garden': 'Taman Hujan — Lima Cahaya yang Tak Terucap',
    'clockwork_station': 'Stasiun Jam — Waktu yang Tidak Bisa Kembali',
    'moonlight_lake': 'Danau Cahaya Bulan — Dua Pantulan',
    'memory_bridge': 'Jembatan Kenangan — Lima Konstelasi',
    'hall_of_tomorrow': 'Balai Hari Esok — Tiga Masa Depan',
}

GLOSSARY = [
    ('PRO', 'Memory Book (Buku Kenangan)', 'Buku milik Arland dan Sofia. Setiap kenangan yang mereka buat bersama menjadi satu halaman.'),
    ('PRO', 'Dunia kenangan', 'Tempat yang terbentuk dari sebuah kenangan, seperti mimpi. Mereka masuk lewat halaman buku dan bisa pulang kapan saja.'),
    ('PRO', 'Halaman memudar', 'Tanda ada hal yang dipendam dan belum diceritakan. Halaman berwarna lagi saat mereka jujur dan saling mendengar.'),
    ('C01', 'Surat dua sisi', 'Surat tua Kakek Wira untuk Nenek Sari. Satu cerita dari dua sudut pandang, seperti cara game ini bercerita lewat dua route.'),
    ('C01', 'The Quiet / Kabut Lupa', 'Bukan monster. Ini kesunyian yang datang saat dua orang berhenti saling mendengarkan, dan membuat lentera serta halaman meredup.'),
    ('C04', 'Lumi', 'Lentera kecil yang bisa bicara, lahir dari halaman pertama buku mereka. Ia menjaga buku dan menunjukkan halaman yang mulai memudar.'),
    ('C04', 'Lentera dan cahaya', 'Di dunia kenangan, lentera menyala dari kata-kata yang benar-benar didengar. Menyalakannya berarti memperbaiki satu salah paham.'),
    ('C05', 'Batu bintang', 'Penunjuk jalan di Jalan Bintang. Nyalakan satu per satu untuk menemukan arah.'),
    ('C06', 'Gema dua suara', 'Potongan suara Kakek Wira dan Nenek Sari di Arsip yang Memudar. Dengarkan baik-baik, lalu pasangkan dengan benar.'),
]


def _insert(lines, prefix, new):
    for i, l in enumerate(lines):
        if l.get('t', '').startswith(prefix):
            add = [{'s': s, 't': t, 'e': e, 'u5c': True} for s, t, e in new]
            return lines[:i + 1] + add + lines[i + 1:], True
    return lines, False


def main():
    sp = A / 'story.json'
    S = json.loads(sp.read_text(encoding='utf-8'))
    sc = S['scenes']
    for sid in set(INSERT) | set(INSERT_AFTER_2):
        sc[sid]['lines'] = [l for l in sc[sid]['lines'] if not l.get('u5c')]     # earlier runs
    for table in (INSERT, INSERT_AFTER_2):
        for sid, (prefix, new) in table.items():
            sc[sid]['lines'], ok = _insert(sc[sid]['lines'], prefix, new)
            assert ok, (sid, prefix)
    for c in S['chapters']:
        if c['id'] in RECAP:
            c['recap'] = RECAP[c['id']]
    sp.write_text(json.dumps(S, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    mp = A / 'maps.json'
    M = json.loads(mp.read_text(encoding='utf-8'))
    for a, n in NAMES.items():
        M['areas'][a]['name'] = n
    mp.write_text(json.dumps(M, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    bp = A / 'memory_book.json'
    B = json.loads(bp.read_text(encoding='utf-8'))
    B['glossary'] = [{'chapter': c, 'term': t, 'text': x} for c, t, x in GLOSSARY]
    bp.write_text(json.dumps(B, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('story: %d lines inserted, %d recaps; %d place names; %d glossary terms'
          % (sum(len(v[1]) for v in INSERT.values()) + sum(len(v[1]) for v in INSERT_AFTER_2.values()), len(RECAP), len(NAMES), len(GLOSSARY)))


if __name__ == '__main__':
    main()
