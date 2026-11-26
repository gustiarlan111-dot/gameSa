"""Story v8: dialogue pass on the templated daily scenes (see docs/STORY_AUDIT_V8.md).

* V49-WE-<EVENT>-A/S (18 world events x 2 routes): only the first narrator line differed; the other
  five lines were the same in all 36 scenes ("Boleh dicoba. Yang penting kita tidak melewatkan hari
  ini." ...). Each is rewritten as its own short conversation about that place, from the route's own
  point of view (Arland's route carries Arland's thoughts, Sofia's route Sofia's).
* V474-RECALL-* / V472-C06-RECALL-*: the repeated narrator verdict after the character's line is
  dropped.
* WE27-* (26 scenes): the generic line "Aku ingin mengingat momen ini tanpa harus membuatnya
  sempurna." / similar is replaced by a line that belongs to that scene.

Scene ids, flags, triggers and choices are untouched, so saves and quests are unaffected.
Idempotent: originals of every touched scene are kept in tools/story_v8_orig.json and restored before
each run. Run: python3 tools/story_v8.py
"""
import copy
import json
from pathlib import Path

A = Path(__file__).resolve().parent.parent / 'assets/data'
SP = A / 'story.json'
OP = Path(__file__).resolve().parent / 'story_v8_orig.json'
s = json.loads(SP.read_text(encoding='utf-8'))
sc = s['scenes']
orig = json.loads(OP.read_text(encoding='utf-8')) if OP.exists() else {}
for k, v in orig.items():
    sc[k] = copy.deepcopy(v)


def keep(k):
    if k not in orig:
        orig[k] = copy.deepcopy(sc[k])


def L(spk, e, t):
    return {"s": spk, "e": e, "t": t}


N, AR, SO = 'narrator', 'arland', 'sofia'

# ---------------------------------------------------------------- V49 world events: A = Arland, S = Sofia
WE = {
    'ARCHIVE_DUST': (
        [L(AR, 'penasaran', "Lipatannya rapi banget. Yang nulis ini pasti orang yang suka ngulang-ngulang kalimat sebelum dikirim."),
         L(SO, 'senyum', "Kayak seseorang yang aku kenal. Yang draf chat-nya bisa tiga versi."),
         L(AR, 'malu', "Dua versi. Yang ketiga cuma tanda baca."),
         L(N, 'neutral', "Sofia meniup debu itu pelan. Arland pura-pura tidak memperhatikan bahwa ia tertawa.")],
        [L(SO, 'penasaran', "Lihat, tintanya luntur di bagian akhir. Kayak yang nulis ragu mau tanda tangan."),
         L(AR, 'serius', "Atau tangannya gemetar. Surat yang penting biasanya bikin tangan gemetar."),
         L(SO, 'senyum', "Kamu ngomong kayak pernah nulis surat begitu."),
         L(AR, 'malu', "...Nggak ada komentar."),
         L(N, 'neutral', "Sofia menyimpan kalimat itu di kepalanya. Suatu hari ia akan menagihnya.")]),
    'BRIDGE_LISTEN': (
        [L(AR, 'penasaran', "Gemanya nggak pernah barengan. Yang satu selalu nyusul."),
         L(SO, 'senyum', "Kayak kita jalan. Kamu di depan, terus nunggu aku di ujung."),
         L(AR, 'malu', "Aku nunggu karena kamu berhenti tiap ada yang bagus buat digambar."),
         L(N, 'neutral', "Arland memperlambat langkah. Kali ini dua gema itu terdengar hampir bersamaan.")],
        [L(SO, 'tersenyum', "Dengar deh, Land. Kalau kita berhenti, gemanya juga berhenti."),
         L(AR, 'penasaran', "Berarti dia ngikutin kita?"),
         L(SO, 'senang', "Atau dia cuma nggak mau jalan sendirian. Aku ngerti perasaannya."),
         L(N, 'neutral', "Mereka melewati jembatan tanpa bicara lagi, dan airnya terdengar lebih jernih.")]),
    'CAVE_ECHO': (
        [L(AR, 'kaget', "Eh, tadi langkah kita bunyi kayak satu orang."),
         L(SO, 'tertawa', "Coba lagi. Kiri, kanan... kamu kecepetan."),
         L(AR, 'senyum', "Aku nyesuaiin, aku nyesuaiin. Kaki kamu kecil, langkahnya banyak."),
         L(N, 'neutral', "Butuh enam kali mencoba. Di percobaan ketujuh, gua itu hanya menggemakan satu langkah.")],
        [L(SO, 'penasaran', "Kristalnya nyala tiap kita jalan sejajar. Kayak ngasih nilai."),
         L(AR, 'tertawa', "Nilai berapa?"),
         L(SO, 'senyum', "Tujuh. Kamu masih suka nyelonong kalau lagi semangat."),
         L(AR, 'malu', "Delapan, deh. Aku kan udah usaha."),
         L(N, 'neutral', "Kristal terdekat menyala sedikit lebih terang, seolah setuju dengan Arland.")]),
    'CLOCKWORK_TEA': (
        [L(AR, 'serius', "Jam-jam di sini jalannya beda semua. Biasanya itu bikin aku stres."),
         L(SO, 'senyum', "Terus sekarang?"),
         L(AR, 'lega', "Sekarang aku cuma mikir tehnya masih hangat. Itu cukup."),
         L(N, 'neutral', "Untuk pertama kalinya Arland tidak melirik jam tangannya selama sepuluh menit penuh.")],
        [L(SO, 'penasaran', "Kamu ngitung putaran roda gigi itu, ya?"),
         L(AR, 'malu', "Dua puluh empat gigi, tiga putaran per... oke, iya."),
         L(SO, 'tertawa', "Aku suka kamu yang begini. Detail kecil aja bisa bikin kamu seneng."),
         L(N, 'neutral', "Sofia membuat sketsa roda gigi itu, lengkap dengan dua puluh empat giginya. Arland mengecek, dan jumlahnya pas.")]),
    'ETERNAL_BLOOM': (
        [L(AR, 'penasaran', "Kalau disiram, kira-kira mekar lebih cepat nggak?"),
         L(SO, 'senyum', "Mungkin. Tapi nanti kita nggak tahu dia mekar sendiri atau karena dipaksa."),
         L(AR, 'serius', "...Iya. Aku juga nggak suka dipaksa siap."),
         L(N, 'neutral', "Arland menaruh kembali botol airnya. Kuncup itu tetap tertutup, dan mereka tidak keberatan.")],
        [L(SO, 'tersenyum', "Aku mau gambar kuncupnya sekarang, sebelum mekar."),
         L(AR, 'bingung', "Bukannya lebih bagus pas udah mekar?"),
         L(SO, 'senyum', "Nanti aku gambar lagi. Biar kelihatan perjalanannya, bukan cuma hasilnya."),
         L(N, 'neutral', "Halaman sketsa itu diberi tanggal hari ini. Halaman sebelahnya sengaja dibiarkan kosong.")]),
    'FENCE_LIGHT': (
        [L(AR, 'senyum', "Lampu rumah Pak Harun nyala duluan. Dia selalu paling rajin."),
         L(SO, 'penasaran', "Kamu hafal urutan lampunya?"),
         L(AR, 'malu', "Dulu aku sering pulang lewat sini sambil nunggu balasan chat kamu."),
         L(N, 'neutral', "Sofia tidak menjawab. Ia hanya menggenggam lengan jaket Arland sampai lampu terakhir menyala.")],
        [L(SO, 'senang', "Satu, dua, tiga... rumah Nenek Sari belum nyala."),
         L(AR, 'khawatir', "Mau mampir? Siapa tahu beliau lupa."),
         L(SO, 'tersenyum', "Kamu tuh. Iya, yuk."),
         L(N, 'neutral', "Mereka mengetuk pintu. Lampu teras Nenek Sari menyala, disusul suara \"Sebentar, Nak!\" dari dalam.")]),
    'GALLERY_CORNER': (
        [L(AR, 'bingung', "Aku cuma lihat garis-garis. Kamu lihat apa?"),
         L(SO, 'senyum', "Berdiri di sebelahku. Sedikit lagi... nah."),
         L(AR, 'kaget', "Oh. Itu wajah. Dua wajah, saling lihat."),
         L(N, 'neutral', "Arland berdiri di situ lebih lama dari yang ia rencanakan. Ia ingin melihat apa yang Sofia lihat.")],
        [L(SO, 'tersenyum', "Pelukisnya pintar. Gambar ini cuma kelihatan utuh kalau dua orang berdiri sejajar."),
         L(AR, 'penasaran', "Kamu bisa bikin yang kayak gini?"),
         L(SO, 'malu', "Lagi aku coba. Buat pameranku nanti. Jangan bilang siapa-siapa dulu."),
         L(AR, 'senang', "Rahasia aman. Paling cuma aku pamerin ke ibuku."),
         L(SO, 'tertawa', "Land!")]),
    'GARDEN_BREEZE': (
        [L(AR, 'penasaran', "Batu ini ada ukiran inisialnya. Tapi lumutnya nutupin setengah."),
         L(SO, 'senyum', "Jangan dikerik. Biar orangnya yang dateng sendiri buat bersihin."),
         L(AR, 'serius', "Kalau orangnya nggak dateng-dateng?"),
         L(SO, 'tersenyum', "Berarti batunya nunggu. Batu jago nunggu."),
         L(N, 'neutral', "Embun menetes dari ujung daun ke ukiran itu, membasuh satu huruf yang sebelumnya tertutup.")],
        [L(SO, 'penasaran', "Pagi-pagi gini batunya dingin, ya. Coba pegang."),
         L(AR, 'kaget', "Dingin banget. Kok kamu tahan?"),
         L(SO, 'senang', "Tanganku nanti hangat lagi. Ada yang mau minjemin saku jaketnya, kan?"),
         L(N, 'neutral', "Arland menyodorkan sakunya tanpa diminta dua kali. Sofia memasukkan tangannya, puas.")]),
    'KITCHEN_STEAM': (
        [L(AR, 'khawatir', "Resepnya bilang 'secukupnya'. Secukupnya itu berapa?"),
         L(SO, 'tertawa', "Sampai rasanya bener. Dicicip, Land, bukan diukur."),
         L(AR, 'malu', "Aku butuh angka, Sof. Aku orang angka."),
         L(SO, 'senyum', "Ya udah. Angkanya: satu cicip lagi."),
         L(N, 'neutral', "Sup itu terlalu asin di cicipan pertama dan pas di cicipan ketiga. Arland mencatat: tiga.")],
        [L(SO, 'senang', "Uapnya bikin kacamata kamu buram. Lucu."),
         L(AR, 'bingung', "Aku nggak lihat apa-apa sekarang. Itu sendok atau sumpit?"),
         L(SO, 'tertawa', "Sini, aku yang aduk. Kamu duduk aja, cantik."),
         L(AR, 'malu', "...Ganteng, Sof. Yang bener ganteng."),
         L(N, 'neutral', "Sofia tidak mengoreksi apa-apa. Ia hanya tersenyum ke arah panci.")]),
    'LANTERN_GLOW49': (
        [L(AR, 'penasaran', "Lentera yang ini nggak mau nyala kalau sendirian."),
         L(SO, 'senyum', "Coba nyalain yang di sebelahnya dulu."),
         L(AR, 'kaget', "Eh, nyala dua-duanya."),
         L(SO, 'tersenyum', "Beberapa hal emang butuh ditemenin dulu baru berani."),
         L(N, 'neutral', "Arland memandangi dua cahaya itu dan diam-diam mengakui bahwa ia termasuk lentera yang seperti itu.")],
        [L(SO, 'tersenyum', "Dulu aku pikir aku lentera yang bisa nyala sendiri."),
         L(AR, 'penasaran', "Sekarang?"),
         L(SO, 'malu', "Sekarang aku tahu nyalanya lebih terang kalau ada lentera lain di dekatku."),
         L(N, 'neutral', "Angin malam lewat, dan tidak satu pun dari dua lentera itu padam.")]),
    'LETTER_LIGHT': (
        [L(AR, 'serius', "Kalau suratnya dilipat begini, kalimat yang ini kebaca duluan."),
         L(SO, 'penasaran', "Kalimat apa?"),
         L(AR, 'malu', "...'Aku datang.' Cuma itu."),
         L(SO, 'tersenyum', "Kalau aku yang nerima, cuma itu juga yang mau aku baca."),
         L(N, 'neutral', "Arland melipat surat itu kembali dengan hati-hati, dengan kalimat itu di bagian luar.")],
        [L(SO, 'penasaran', "Cahayanya jatuh di dua kata yang beda tergantung cara lipatnya. Kayak orang ngomong."),
         L(AR, 'bingung', "Maksudnya?"),
         L(SO, 'senyum', "Kata-katanya sama. Yang beda, bagian mana yang kita mau dengar."),
         L(N, 'neutral', "Sofia memiringkan surat itu. Cahaya berhenti tepat di kata \"tunggu\".")]),
    'MOONLIGHT_RIPPLE': (
        [L(AR, 'khawatir', "Bulannya pecah tiap ada angin. Nggak takut nggak nyatu lagi?"),
         L(SO, 'senyum', "Tungguin sebentar."),
         L(AR, 'lega', "...Oh. Nyatu lagi."),
         L(N, 'neutral', "Mereka menunggu tiga kali angin. Setiap kali pantulan itu pecah, lalu menyatu lagi.")],
        [L(SO, 'tersenyum', "Aku suka danau ini. Dia nggak pura-pura tenang."),
         L(AR, 'penasaran', "Maksudnya?"),
         L(SO, 'senyum', "Kalau ada angin, dia goyang. Terus balik lagi. Nggak ditahan-tahan."),
         L(AR, 'senang', "Kayak kamu kalau lagi kesel sama aku."),
         L(SO, 'tertawa', "Nah itu kamu pinter.")]),
    'RAIN_SHELTER': (
        [L(AR, 'khawatir', "Aku lupa bawa payung. Lagi."),
         L(SO, 'tertawa', "Ketiga kalinya bulan ini."),
         L(AR, 'malu', "Aku catet di HP, Sof. Catatannya aja yang nggak pernah aku buka."),
         L(N, 'neutral', "Mereka berteduh di bawah paviliun, menunggu hujan, dan tidak ada yang buru-buru ingin hujan berhenti.")],
        [L(SO, 'senyum', "Hujan bikin suara lain hilang. Rasanya cuma ada kita."),
         L(AR, 'penasaran', "Kamu suka hujan?"),
         L(SO, 'tersenyum', "Sekarang suka. Dulu nggak."),
         L(AR, 'bingung', "Kenapa berubah?"),
         L(SO, 'malu', "Rahasia. Nanti aku kasih tahu kalau hujannya udah reda.")]),
    'ROOM_NOTE': (
        [L(AR, 'malu', "Catatan ini aku tulis jam dua pagi. Isinya cuma 'jangan lupa bilang makasih ke Sofia'."),
         L(SO, 'penasaran', "Makasih buat apa?"),
         L(AR, 'senyum', "Buat semuanya. Tapi jam dua pagi aku nggak bisa mikir lebih spesifik."),
         L(SO, 'tertawa', "Diterima. Versi spesifiknya aku tunggu."),
         L(N, 'neutral', "Arland menempelkan catatan itu lagi di ujung meja. Hari ini, ia berjanji, ia akan menulis versi lengkapnya.")],
        [L(SO, 'penasaran', "Ini tulisan kamu? Kok kayak resep dokter."),
         L(AR, 'malu', "Itu daftar hal yang mau aku omongin ke kamu. Jangan dibaca!"),
         L(SO, 'senang', "Nomor satu: 'bilang dia cantik pakai warna lavender'. Hmm."),
         L(AR, 'kaget', "Sof!"),
         L(SO, 'tertawa', "Nomor satu udah dicoret, ya. Berarti udah kejadian. Oke, aku lanjut baca.")]),
    'STAR_PATH_PAUSE': (
        [L(AR, 'serius', "Kompasnya muter terus. Aku nggak tahu kita harus ke mana."),
         L(SO, 'senyum', "Ya udah, kita duduk dulu. Bintangnya juga nggak ke mana-mana."),
         L(AR, 'lega', "...Kamu kok tenang banget, sih?"),
         L(SO, 'tersenyum', "Karena aku nggak nyasar sendirian."),
         L(N, 'neutral', "Mereka duduk di tepi jalur. Beberapa menit kemudian jarum kompas berhenti, menunjuk ke arah yang tidak terduga.")],
        [L(SO, 'penasaran', "Kalau kita salah jalan, kira-kira nyampe di mana?"),
         L(AR, 'khawatir', "Jangan ngomong gitu, aku udah bikin rute."),
         L(SO, 'tertawa', "Rute kamu bagus. Tapi tadi aku lihat bintang jatuh di sebelah sana."),
         L(AR, 'senyum', "...Oke. Lima menit ke sana, terus balik ke rute."),
         L(N, 'neutral', "Lima menit itu jadi dua puluh menit. Tidak ada yang mengeluh.")]),
    'STREET_BELLS': (
        [L(AR, 'penasaran', "Loncengnya bunyi beda-beda. Yang ini toko roti, yang ini toko bunga..."),
         L(SO, 'senyum', "Yang ini?"),
         L(AR, 'senang', "Kedai es krim. Aku hafal karena kamu selalu berhenti di situ."),
         L(SO, 'tertawa', "Fitnah. Aku cuma berhenti kalau ada rasa baru."),
         L(N, 'neutral', "Hari ini ada rasa baru. Arland sudah tahu, dan sudah menyiapkan uang kecil di sakunya.")],
        [L(SO, 'tersenyum', "Kamu nyadar nggak, lonceng di jalan ini nggak ada yang barengan bunyinya?"),
         L(AR, 'penasaran', "Iya juga. Kayak gantian."),
         L(SO, 'senyum', "Kayak orang ngobrol. Satu ngomong, yang lain dengerin dulu."),
         L(AR, 'malu', "Aku masih belajar bagian dengerin dulu itu."),
         L(SO, 'tersenyum', "Aku tahu. Kamu udah jauh lebih baik.")]),
    'TOMORROW_CARDS': (
        [L(AR, 'khawatir', "Tiga kartu kosong. Aku kira bakal ada jawabannya di sini."),
         L(SO, 'senyum', "Kamu mau nulis apa kalau boleh nulis satu?"),
         L(AR, 'serius', "...'Masih bareng.' Itu aja. Detailnya nyusul."),
         L(N, 'neutral', "Arland tidak menulis apa pun di kartu itu. Ia hanya memasukkannya ke saku, di sebelah kartu milik Sofia.")],
        [L(SO, 'penasaran', "Kalau kartunya kosong, berarti kita yang nentuin isinya, kan?"),
         L(AR, 'bingung', "Itu yang bikin takut."),
         L(SO, 'tersenyum', "Buat aku itu yang bikin seneng. Nggak ada yang ditulisin orang lain."),
         L(AR, 'lega', "Kalau gitu, kita nulisnya bareng-bareng aja, ya."),
         L(N, 'neutral', "Sofia mengangguk dan menyimpan tiga kartu kosong itu di antara halaman buku sketsanya.")]),
    'WINDOW_STORY': (
        [L(AR, 'penasaran', "Kaca jendela kamu ada tulisan dari spidol. Itu apa?"),
         L(SO, 'malu', "Jangan dibaca. Itu kalimat buat pameran yang belum jadi."),
         L(AR, 'senyum', "Aku cuma kebaca satu kata. 'Pulang'."),
         L(SO, 'tersenyum', "Itu kata yang paling susah. Sisanya gampang."),
         L(N, 'neutral', "Sinar sore bergeser. Arland berpura-pura tidak sempat membaca kata-kata lainnya.")],
        [L(SO, 'tersenyum', "Kalimat ini cuma kelihatan jam segini. Aku nulisnya pakai sisa cat kaca."),
         L(AR, 'penasaran', "Kenapa nggak ditulis di kertas aja?"),
         L(SO, 'senyum', "Karena aku mau kalimatnya muncul cuma pas sore. Pas kamu biasanya dateng."),
         L(AR, 'malu', "...Aku dateng sore karena macet, Sof."),
         L(SO, 'tertawa', "Tetap aja. Macetnya romantis.")]),
}

# ---------------------------------------------------------------- WE27: one generic line each -> a line that belongs there
WE27_GENERIC = {
    "Aku ingin mengingat momen ini tanpa harus membuatnya sempurna.",
    "Aku ingin melihatnya sampai selesai, biar tidak melewatkan bagian kecilnya.",
    "Aku ingin mencatat bagaimana rasanya, bukan cuma bentuknya.",
}
WE27_FIX = {
    'WE27-ARCADE-TIKET-A': L(AR, 'senyum', "Nanti kita titip ke kasir. Siapa tahu pemiliknya balik nyari."),
    'WE27-ARCADE-TIKET-S': L(SO, 'tersenyum', "Kalau nggak ada yang nyari, tiketnya buat kamu aja. Tukar sama gantungan kunci bulan."),
    'WE27-ARLAN-PETA-A': L(AR, 'senyum', "Belokan ketiga aku kasih tanda pohon. Dito pasti hafal pohon itu."),
    'WE27-BUKIT-TELESKOP-A': L(AR, 'senyum', "Kita kasih nama aja. Bintang Arland-dan-Sofia. Panjang, tapi jelas."),
    'WE27-BUKIT-TELESKOP-S': L(SO, 'tertawa', "Namanya terlalu panjang, Land. Kita panggil 'si Satu' aja."),
    'WE27-DERMAGA-PAPAN-A': L(AR, 'senyum', "Aku ukir huruf kecil di bawah bangku. Kecil banget, biar nggak ketahuan petugas."),
    'WE27-DERMAGA-PAPAN-S': L(SO, 'senyum', "Bangku nomor tujuh. Aku hafal karena papannya yang paling berisik."),
    'WE27-DESA-BINTANG-A': L(AR, 'malu', "Nanti rumah kita juga begitu. Satu lampu nyala, biar yang pulang telat nggak nyasar."),
    'WE27-DESA-BINTANG-S': L(SO, 'tersenyum', "Jendela yang paling ujung itu lampunya kuning. Kayak lampu kamar kamu."),
    'WE27-HALTE-HUJAN-A': L(AR, 'senyum', "Sekarang aku malah berharap busnya telat dikit."),
    'WE27-HALTE-HUJAN-S': L(SO, 'malu', "Kalimatnya nanti aja. Hujannya belum selesai, masih ada waktu."),
    'WE27-HUTAN-GEMA-A': L(AR, 'penasaran', "Coba bilang sesuatu. Biar aku dengar gemanya pakai suara kamu."),
    'WE27-HUTAN-GEMA-S': L(SO, 'senyum', "Kalau gitu aku mau ngomong yang berani. Tapi pelan-pelan aja."),
    'WE27-IKAN-PONDOK-A': L(AR, 'senang', "Oke, ikan. Ceritanya dimulai dari seorang cowok yang lupa bawa payung."),
    'WE27-IKAN-PONDOK-S': L(SO, 'penasaran', "Tiga lingkar, jeda, tiga lingkar. Dia kayak lagi ngetuk pintu."),
    'WE27-KAFE-CATATAN-A': L(AR, 'malu', "Aku pernah. Isinya buat kamu. Masih aku simpan di dompet."),
    'WE27-KAFE-CATATAN-S': L(SO, 'tersenyum', "Aku selipin lagi di bawah cangkir. Biar ada orang lain yang senyum habis ini."),
    'WE27-MELATI-MERANGKAI-A': L(AR, 'penasaran', "Jadi yang layu nggak dibuang, Bu? Cuma ditaruh di belakang?"),
    'WE27-MELATI-MERANGKAI-S': L(SO, 'senyum', "Bu Melati, boleh aku bawa satu yang layu? Mau aku gambar."),
    'WE27-PAGI-PLAZA-A': L(AR, 'senyum', "Jangan dipetik, ya. Besok kita cek lagi dia masih di sini atau nggak."),
    'WE27-PAGI-PLAZA-S': L(SO, 'senang', "Lima menit lagi plaza ramai. Bantu aku jagain cahayanya, Land."),
    'WE27-PERPUSTAKAAN-SENYAP-A': L(AR, 'penasaran', "Ada coretan pensil di pinggir halaman. Kayak ada yang ngobrol sama bukunya."),
    'WE27-PERPUSTAKAAN-SENYAP-S': L(SO, 'tersenyum', "Aku tambahin satu coretan juga. Kecil aja, di halaman tiga belas."),
    'WE27-SENJA-DANAU-A': L(AR, 'senyum', "Pas di batu itu. Tiap sore jam lima lewat sepuluh. Aku udah ngitung."),
    'WE27-SENJA-DANAU-S': L(SO, 'senyum', "Daun di sini bunyinya kayak orang bisik-bisik. Aku mau inget suaranya."),
    'WE27-SOFIA-HALAMAN-S': L(SO, 'malu', "Tanpa nama aja. Tapi aku tahu dia bakal nebak itu tulisanku."),
}

changed = 0
for ev, (a_lines, s_lines) in WE.items():
    for suffix, new in (('A', a_lines), ('S', s_lines)):
        k = 'V49-WE-%s-%s' % (ev, suffix)
        keep(k)
        first = orig[k]['lines'][0]                    # the place-setting narrator line stays
        sc[k]['lines'] = [first] + copy.deepcopy(new)
        changed += 1
for k, line in WE27_FIX.items():
    keep(k)
    ls = copy.deepcopy(orig[k]['lines'])
    hits = [i for i, l in enumerate(ls) if l.get('t') in WE27_GENERIC]
    if hits:
        ls[hits[0]] = line
    else:                                              # no generic line: add the new one before the closing line
        ls.insert(max(1, len(ls) - 1), line)
    sc[k]['lines'] = ls
    changed += 1

# ---------------------------------------------------------------- recall scenes: drop the moralising wrap-up
# Two-line recall scenes ended with the same narrator verdict (16x / 12x); the character's own line
# says it better on its own.
MORAL = {
    "Kalimat itu tersimpan sebagai bagian dari ingatan, bukan sebagai jawaban yang paling benar.",
    "Kenangan itu tetap memiliki bekas yang tidak dipoles menjadi sempurna.",
}
for k in list(sc):
    if not (k.startswith('V474-RECALL-') or k.startswith('V472-C06-RECALL-')):
        continue
    ls = (orig[k] if k in orig else sc[k])['lines']
    kept = [l for l in ls if not (l.get('s') == 'narrator' and l.get('t') in MORAL)]
    if kept and len(kept) < len(ls):
        keep(k)
        sc[k]['lines'] = copy.deepcopy(kept)
        changed += 1

# ---------------------------------------------------------------- Bab 6 recall: one line per route, in their own voice
# These 6 pairs were word-for-word the same in both routes and read like slogans. Each now points
# at something that happened in the story (Bab 2 date plan, Bab 4 gallery day and the unsent message).
RECALL = {
    'DATE-A-SEE': L(AR, 'senyum', "Jadwal kencan pertama itu aku bikin per menit. Terus kamu ngajak belok ke toko buku. Ternyata itu bagian paling seru."),
    'DATE-A-REFUSE': L(AR, 'serius', "Aku nggak mau versi yang semuanya sesuai jadwal. Nanti nggak ada toko buku, nggak ada kamu yang bilang 'nggak mau'."),
    'DATE-S-SEE': L(SO, 'tertawa', "Dia nyusun jadwal per menit, terus aku rusak di menit kedua belas. Mukanya waktu itu... aku mau inget itu."),
    'DATE-S-REFUSE': L(SO, 'serius', "Kencan yang sempurna nggak ada artinya kalau aku nggak boleh bilang 'nggak mau ke situ'."),
    'PRESENCE-A-SEE': L(AR, 'sedih', "Aku telat di hari yang paling penting buat dia. Aku nggak mau lupa rasanya, biar nggak kejadian lagi."),
    'PRESENCE-A-REFUSE': L(AR, 'serius', "Aku nggak bisa janji tepat waktu terus. Tapi aku bisa janji bilang dari awal kalau aku kewalahan."),
    'PRESENCE-S-SEE': L(SO, 'sedih', "Kursi kosong itu masih kebayang. Tapi aku juga inget dia lari dari halte sambil meluk proyektor."),
    'PRESENCE-S-REFUSE': L(SO, 'tersenyum', "Aku nggak mau ingatan yang isinya dia dateng tepat waktu. Itu bukan dia. Aku mau dia yang telat, tapi tetap dateng."),
    'AGREEMENT-A-SEE': L(AR, 'senyum', "Kita pernah ribut soal hal kecil, terus habis itu makan mi bareng. Aku mau inget dua-duanya."),
    'AGREEMENT-A-REFUSE': L(AR, 'serius', "Aku nggak mau kita kelihatan akur kalau caranya salah satu dari kita diem aja."),
    'AGREEMENT-S-SEE': L(SO, 'lega', "Waktu aku marah soal pesan yang nggak pernah terkirim itu, dia nggak ngebela diri. Dia dengerin dulu."),
    'AGREEMENT-S-REFUSE': L(SO, 'serius', "Aku nggak mau jadi orang yang bilang 'nggak apa-apa' padahal ada apa-apanya."),
}
for suffix, line in RECALL.items():
    k = 'V472-C06-RECALL-' + suffix
    keep(k)
    sc[k]['lines'] = [copy.deepcopy(line)]
    changed += 1

OP.write_text(json.dumps(orig, ensure_ascii=False, indent=1), encoding='utf-8')
SP.write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('story v8: %d scenes rewritten' % changed)
