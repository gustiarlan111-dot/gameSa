"""U3b: town NPCs remember what the couple did. Adds one-time dialog entries to townNpcs in
assets/data/quests.json: after a choice (ribbon colour, where the first date started, the date outfit)
or a finished side quest, the NPC who would know about it brings it up the next time you talk.

Each entry fires once (it sets its own MEM_* flag) and sits after the NPC's quest dialogs but before
the everyday small talk, so it never hides a quest step. Re-running replaces the MEM_* entries.
Usage: python3 tools/npc_memory_u3b.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QP = ROOT / 'assets/data/quests.json'

# (npc, memory id, flag that must be set, npc line (s, e, t), optional route-specific replies)
MEM = [
    ('melati', 'MEM_MELATI_LAVENDER', 'C02_RIBBON_LAVENDER', ('senyum', 'Pita lavender yang kamu pilih waktu itu, Bu Melati masih ingat. Dia suka, kan?'),
     {'arland': ('malu', 'Kayaknya suka, Bu. Dia senyum terus seharian.')}),
    ('melati', 'MEM_MELATI_PEACH', 'C02_RIBBON_PEACH', ('senyum', 'Pita peach waktu itu pilihan yang berani, Nak. Bunganya jadi kelihatan hangat.'), {}),
    ('melati', 'MEM_MELATI_BUNGA', 'SQ_BUNGA_DONE', ('senang', 'Nenek Sari sampai menaruh buket kemarin di jendela. Terima kasih sudah mengantar, ya.'), {}),
    ('juna', 'MEM_JUNA_ARCADE', 'C02_ARCADE_FIRST', ('tertawa', 'Kalian yang kencannya mulai dari arcade itu, kan? Jarang ada yang seberani itu. Bang Juna salut.'), {}),
    ('juna', 'MEM_JUNA_KASET', 'SQ_V7_KASET_DONE', ('senyum', 'Kasetnya Nenek Sari bunyi lagi? Syukurlah. Keroncong itu harus diputar, bukan disimpan.'), {}),
    ('harun', 'MEM_HARUN_TAMAN', 'C02_PARK_FIRST', ('senyum', 'Kalian yang pagi-pagi ke taman waktu itu. Bapak sampai berhenti menyapu, ikut senang lihatnya.'), {}),
    ('harun', 'MEM_HARUN_HEWAN', 'SQ_HEWAN_DONE', ('tertawa', 'Kucing, anjing, sama bebek itu sekarang kalau lihat kalian langsung mendekat. Mereka ingat, lho.'), {}),
    ('rara', 'MEM_RARA_DATE', 'C02_OUTFIT_DATE', ('senang', 'Kak Sofia, baju waktu kencan itu cantik banget! Rara mau pakai yang kayak gitu nanti.'),
     {'sofia': ('malu', 'Makasih, Rara. Kakak juga deg-degan waktu itu.')}),
    ('rara', 'MEM_RARA_CASUAL', 'C02_OUTFIT_CASUAL', ('senyum', 'Kak Sofia waktu itu bajunya santai, tapi tetap keren. Rara suka yang nggak ribet.'), {}),
    ('darmo', 'MEM_DARMO_KUE', 'SQ_KUE_DONE', ('senyum', 'Kue Bu Rini kemarin masih terasa manisnya. Terima kasih sudah jauh-jauh mengantar ke Kakek.'), {}),
    ('sari', 'MEM_SARI_MOCHI', 'SQ_MOCHI_DONE', ('senang', 'Mochi sekarang tidur di keranjang dekat jendela. Sejak kalian menemukannya, dia betah di rumah.'), {}),
    ('sari', 'MEM_SARI_KASET', 'SQ_V7_KASET_DONE', ('senyum', 'Kaset keroncong itu Nenek putar tiap sore sekarang. Kakek dulu paling suka lagu yang ketiga.'), {}),
    ('udin', 'MEM_UDIN_IKAN', 'SQ_IKAN_DONE', ('tertawa', 'Pemancing pemula kita! Lima jenis ikan, Bapak masih cerita ke semua orang.'), {}),
    ('dito', 'MEM_DITO_BATU', 'SQ_BATU_DONE', ('senang', 'Batu berkilau dari Kakak Dito taruh di kotak harta. Paling bagus yang dari Tepi Danau!'), {}),
    ('dito', 'MEM_DITO_MURAL', 'SQ_MURAL_DONE', ('tertawa', 'Muralnya sudah jadi, Kak! Ada gambar Kakak berdua juga, kecil, di pojok. Hehe.'), {}),
    ('pos', 'MEM_POS_SURAT', 'SQ_POS_DONE', ('senang', 'Lima surat waktu itu sampai semua. Kurir terbaik kota, Bapak bilang juga apa.'), {}),
    ('raka', 'MEM_RAKA_RESEP', 'SQ_RESEP3_DONE', ('senyum', 'Kue jahe buatan kalian waktu itu... jujur, pelanggan nanya terus. Mau kerja di sini?'), {}),
    ('raka', 'MEM_RAKA_BUKU', 'SQ_BUKU_DONE', ('senyum', 'Lima buku kafe pulang semua. Rak di pojok jadi lengkap lagi, berkat kalian.'), {}),
    ('laras', 'MEM_LARAS_KARTU', 'SQ_V26_CARDS_S_DONE', ('senyum', 'Kartu cerita yang kamu tulis sudah Bu Laras pajang di dekat meja pinjam.'), {}),
]
GENERIC_WHEN = {'hours', 'minChapter', 'maxChapter', 'weatherIs'}
GENERIC_DO = {'lines', 'sfx', 'emote'}


def is_small_talk(d):
    if not set(d.get('when', {})).issubset(GENERIC_WHEN):
        return False
    return all(a.get('do') in GENERIC_DO for a in d.get('actions', []))


def entry(npc, mid, flag, line, replies):
    acts = [{'do': 'lines', 'lines': [{'s': npc, 'e': line[0], 't': line[1]}]}]
    for route, (e, t) in replies.items():
        acts.append({'do': 'lines', 'lines': [{'s': route, 'e': e, 't': t}], 'route': route})
    acts.append({'do': 'flag', 'id': mid})
    return {'id': mid, 'when': {'flags': [flag], 'notFlags': [mid]}, 'actions': acts}


def main():
    Q = json.loads(QP.read_text(encoding='utf-8'))
    by_id = {n['id']: n for n in Q['townNpcs']}
    added = 0
    for n in Q['townNpcs']:
        n['dialogs'] = [d for d in n.get('dialogs', []) if not str(d.get('id', '')).startswith('MEM_')]
    for npc, mid, flag, line, replies in MEM:
        n = by_id[npc]
        ds = n['dialogs']
        at = next((i for i, d in enumerate(ds) if is_small_talk(d)), len(ds))
        ds.insert(at, entry(npc, mid, flag, line, replies))
        added += 1
    QP.write_text(json.dumps(Q, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('memory dialogs', added)


if __name__ == '__main__':
    main()
