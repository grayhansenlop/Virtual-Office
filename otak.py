#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OTAK LUAR - kecerdasan buatan mandiri untuk Kantor Marketing AI
================================================================
Program terpisah dari aplikasi (hanya butuh Python 3.8+, tanpa pustaka tambahan).
Tugasnya: memahami perintah bahasa sehari-hari/tidak baku dan mengubahnya
menjadi aksi untuk aplikasi kantor, lalu BELAJAR SENDIRI dari pemakaian.

Cara belajar (semuanya online, tersimpan di otak_luar_memori.json):
  1. Label dari LLM  : saat otak ini ragu, aplikasi bertanya ke Claude; jawaban Claude
                       dikirim balik ke sini sebagai contoh latihan (self-training).
  2. Koreksi Bos     : "bukan, maksudku ..." dihitung contoh berbobot tinggi (x3).
  3. Konfirmasi      : "betul" atau tidak ada keberatan = penguatan lemah.
  4. Alias/panggilan : nama panggilan baru (mis. "Wiwi" = Dewi) dipelajari otomatis.
  5. Belajar mandiri : tiap beberapa menit, memori dilatih ulang, akurasi diuji silang,
                       dan ambang "yakin" disesuaikan agar presisi tetap tinggi.

Memori yang terus bertumbuh (v2):
  6. Fakta/pengetahuan : app menyetor ringkasan web & hasil riset (/remember); dicari lagi lewat /recall
                         dan dilampirkan ke jawaban /understand sebagai "ingat".
  7. Belajar mandiri   : perintah yang dipahami dengan sangat yakin ikut jadi contoh latihan berbobot kecil
                         (src "mandiri"), supaya kosakata gaya Anda bertambah tanpa harus dikoreksi.
  8. Pemadatan memori  : contoh kembar digabung (bobot naik), bukan dibuang; cadangan .bak otomatis.
  9. Proxy web         : /fetch?url=... mengambil teks halaman publik atas nama app (app di browser
                         sering diblokir CORS / tidak punya akses web).

Ini pembelajar statistik ringan (Naive Bayes + pencocokan nama + aturan slot), bukan
model bahasa besar. Awalnya terbatas, makin lama makin pas dengan gaya bahasa Anda.

Jalankan:   python3 otak_luar.py                (server di http://127.0.0.1:8765)
Uji cepat:  python3 otak_luar.py --tes "Rina bikinin caption promo dong"
Uji diri:   python3 otak_luar.py --selftest
"""
import argparse, html as _html, ipaddress, json, math, os, re, shutil, socket, sys, threading, time
import urllib.request, urllib.parse
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOME = '/tmp'
DB_PATH = os.environ.get('OTAK_DB', '/tmp/otak_luar_memori.json')

INTENTS = ['task', 'it_fix', 'meeting', 'coffee', 'summon', 'goto', 'focus',
           'duty_add', 'duty_remove', 'interview', 'status', 'praise', 'chat',
           'upload', 'seat', 'stop', 'go', 'line', 'cancel']

# ---------------------------------------------------------------- bahasa tidak baku
SLANG = {
    'gak': 'tidak', 'ga': 'tidak', 'nggak': 'tidak', 'ngga': 'tidak', 'enggak': 'tidak', 'gk': 'tidak', 'tdk': 'tidak',
    'yg': 'yang', 'utk': 'untuk', 'untk': 'untuk', 'dgn': 'dengan', 'dg': 'dengan', 'sdh': 'sudah', 'udah': 'sudah',
    'udh': 'sudah', 'sdah': 'sudah', 'blm': 'belum', 'belom': 'belum', 'bsk': 'besok', 'tlg': 'tolong', 'tolongin': 'tolong',
    'bikinin': 'buatkan', 'bikinkan': 'buatkan', 'buatin': 'buatkan', 'bikin': 'buat', 'gedein': 'perbesar', 'gedeinn': 'perbesar',
    'kecilin': 'perkecil', 'cariin': 'carikan', 'carikan': 'carikan', 'kerjain': 'kerjakan', 'ngerjain': 'kerjakan',
    'nganggur': 'luang', 'menganggur': 'luang', 'senggang': 'luang', 'ngobrolin': 'bahas', 'ngomongin': 'bahas', 'bahasin': 'bahas',
    'ngopi': 'kopi', 'ngurus': 'urus', 'ngurusin': 'urus', 'mengurus': 'urus', 'garapin': 'garap', 'siapin': 'siapkan',
    'cekin': 'periksa', 'ngecek': 'periksa', 'cek': 'periksa', 'betulin': 'betulkan', 'benerin': 'betulkan', 'rapihin': 'rapikan',
    'gimana': 'bagaimana', 'gmn': 'bagaimana', 'kpn': 'kapan', 'trus': 'lalu', 'terus': 'lalu', 'abis': 'setelah',
    'makasih': 'terima kasih', 'thx': 'terima kasih', 'tq': 'terima kasih', 'mksh': 'terima kasih', 'mantul': 'mantap',
    'gercep': 'cepat', 'bgt': 'sekali', 'banget': 'sekali', 'ntar': 'nanti', 'tar': 'nanti', 'skrg': 'sekarang', 'sekarang': 'sekarang',
    'dr': 'dari', 'kpd': 'kepada', 'krn': 'karena', 'spy': 'supaya', 'biar': 'supaya', 'pake': 'pakai', 'pakek': 'pakai',
    'bs': 'bisa', 'liat': 'lihat', 'kasi': 'beri', 'kasih': 'beri', 'aja': 'saja', 'doang': 'saja', 'kesini': 'ke sini',
    'kemari': 'ke sini', 'dateng': 'datang', 'dtg': 'datang', 'balik': 'kembali', 'nongkrong': 'santai', 'rehat': 'istirahat',
    'brief': 'briefing', 'meeting': 'rapat', 'interview': 'wawancara', 'mewawancarai': 'wawancara', 'wawancarai': 'wawancara',
    'gaskeun': 'mulai', 'gas': 'mulai', 'sikat': 'mulai', 'hayuk': 'ayo', 'yuk': 'ayo', 'yok': 'ayo', 'cus': 'ayo',
    'lg': 'sedang', 'lagi': 'lagi', 'sibuk': 'sibuk', 'org': 'orang', 'sm': 'sama', 'jd': 'jadi', 'jg': 'juga', 'dlm': 'dalam',
}
SLANG.update({
    'masukin': 'masukkan', 'masukan': 'masukan', 'masukkan': 'masukkan', 'memasukkan': 'masukkan', 'naro': 'taruh', 'naroh': 'taruh',
    'nyimpen': 'simpan', 'simpenin': 'simpan', 'simpen': 'simpan', 'nyimpan': 'simpan', 'upload': 'unggah', 'ngupload': 'unggah',
    'mengunggah': 'unggah', 'uploadin': 'unggah', 'unggahin': 'unggah', 'kirimin': 'kirim', 'dir': 'folder', 'direktori': 'folder',
    'berkas': 'file', 'dokumen': 'file', 'ngumpul': 'kumpul', 'pada': 'di', 'bubaran': 'bubar', 'hening': 'diam', 'sstt': 'diam',
    'mager': 'malas', 'duduklah': 'duduk', 'tertiblah': 'tertib',
})
FILLER = {'dong', 'deh', 'sih', 'lah', 'kok', 'nih', 'tuh', 'ya', 'yah', 'nah', 'dah', 'lho', 'loh', 'kan', 'tolonglah', 'pls', 'plis'}
TEXT_DROP = FILLER | {'tolong', 'mohon', 'minta', 'suruh', 'bantu', 'coba', 'sekalian', 'lalu', 'kemudian', 'dulu', 'bisa', 'bisakah',
                      'ayo', 'silakan', 'silahkan', 'harap', 'bos', 'pak', 'bu', 'mulai'}
HONOR = {'bu', 'pak', 'mas', 'mbak', 'mba', 'kak', 'kakak', 'bang', 'bro', 'sis', 'si', 'ibu', 'bapak', 'dik', 'dek', 'sdr'}
CONJ = re.compile(r"\s*(?:,\s*)?\b(?:sekalian|sekaligus|lalu|kemudian|terus|trus|habis itu|abis itu|setelah itu|dan juga|serta|sementara itu)\b\s*|[;\n]+|(?<=[.!?])\s+(?=[A-Z])", re.I)
TOKEN = re.compile(r"[\w&']+(?:[.,:/\-][\w&']+)*|[^\w\s]")
DEPT_WORDS = {'marketing': 'mk', 'pemasaran': 'mk', 'desain': 'ds', 'design': 'ds', 'hr': 'hr', 'hrd': 'hr', 'sdm': 'hr',
              'riset': 'rd', 'r&d': 'rd', 'rnd': 'rd', 'finance': 'fn', 'keuangan': 'fn', 'akuntansi': 'fn', 'audit': 'au',
              'proyek': 'pm', 'project': 'pm', 'admin': 'ad', 'administrasi': 'ad', 'lobby': 'lb', 'lobi': 'lb',
              'resepsionis': 'lb', 'it': 'it', 'funding': 'fu', 'pendanaan': 'fu'}
PLACES = [(r'pantry|dapur', 'pantry'), (r'lounge', 'lounge'), (r'lobby|lobi|resepsionis', 'lobby'),
          (r'ruang it', 'ruang_it'), (r'ruang (?:finance|keuangan|funding)', 'ruang_finance'),
          (r'(?:ruang )?(?:rapat|meeting) besar|aula', 'meeting_besar'), (r'ruang (?:rapat|meeting)|ruang rapat', 'ruang_rapat'),
          (r'meja|tempat duduk|kursi', 'meja')]

# ---------------------------------------------------------------- contoh awal (bibit)
SEED = {
    'task': ["NAMA buatkan caption untuk promo akhir bulan", "NAMA tolong buatkan desain banner", "NAMA buat laporan riset kompetitor",
             "NAMA carikan referensi visual", "susun rencana kampanye bulan depan", "NAMA kerjakan analisis iklan",
             "tolong tulis artikel blog tentang produk baru", "NAMA garap konten reels natal", "buatkan slogan untuk toko",
             "NAMA riset pasar anak muda", "siapkan proposal untuk klien", "NAMA analisis performa iklan minggu ini",
             "NAMA mulai buat poster promo", "NAMA tolong periksa harga pesaing", "NAMA rancang strategi konten bulan depan",
             "buat copy iklan untuk produk baru", "NAMA desainkan logo sederhana", "NAMA rekap data penjualan minggu ini"],
    'it_fix': ["NAMA perbesar tombol kirim", "ubah warna tombol jadi hijau", "tampilan terlalu kecil tolong perbaiki",
               "NAMA font nya kekecilan perbesar", "kontras teks kurang jelas tolong perbaiki", "perbaiki layout chat berantakan",
               "ada bug di tampilan betulkan", "tombol nya kekecilan", "tambahkan tombol baru di panel", "rapikan tampilan UI",
               "ganti warna background lebih gelap", "NAMA ubah ukuran huruf di panel laporan", "tampilan aplikasi kurang rapi"],
    'meeting': ["semua kumpul kita rapat", "ayo rapat sekarang", "kumpul kita bahas target bulan depan", "adakan rapat tim marketing",
                "briefing pagi semua", "rapat bahas strategi", "kita ngobrol bareng soal anggaran", "panggil semua ke ruang rapat",
                "NAMA ajak tim rapat", "semua kumpul di ruang meeting besar", "ayo kita rapat mingguan", "rapat umum sekarang"],
    'coffee': ["semua istirahat dulu kopi", "NAMA kopi dulu sana", "break kopi sepuluh menit", "waktunya istirahat santai dulu",
               "istirahat dulu", "ayo kopi bareng", "NAMA istirahat dulu", "semua boleh istirahat", "NAMA ayo santai sebentar"],
    'summon': ["NAMA ke sini sebentar", "panggil NAMA menghadap", "NAMA temui saya", "suruh NAMA datang ke ruangan saya",
               "NAMA tolong ke sini", "NAMA menghadap sekarang", "NAMA datang ke meja saya", "NAMA ke ruangan saya"],
    'goto': ["NAMA ke pantry", "NAMA pergi ke lobby", "NAMA kembali ke meja", "NAMA ke ruang IT", "NAMA ke ruang meeting besar",
             "NAMA santai di lounge", "suruh NAMA ke ruang finance", "NAMA kembali ke mejamu", "NAMA ke ruang rapat"],
    'focus': ["NAMA fokus ke konten reels", "NAMA alihkan pekerjaan ke riset kompetitor", "NAMA ganti fokus kerjamu jadi analisis iklan",
              "NAMA fokuskan ke email marketing", "NAMA sekarang fokus ke desain poster", "NAMA pekerjaan rutinmu ganti jadi riset tren"],
    'duty_add': ["NAMA mulai sekarang kamu juga urus newsletter mingguan", "tambah tupoksi NAMA urus laporan bulanan",
                 "NAMA tugas tambahan kamu update katalog", "mulai sekarang NAMA bertanggung jawab atas jadwal posting",
                 "sekarang NAMA ikut tangani sosial media", "NAMA tupoksi barumu moderasi komentar"],
    'duty_remove': ["NAMA tidak lagi urus newsletter", "hapus tugas laporan bulanan dari NAMA", "NAMA lepas tugas moderasi komentar",
                    "mulai sekarang NAMA tidak usah urus katalog", "NAMA tidak lagi bertanggung jawab atas jadwal posting"],
    'interview': ["NAMA wawancara Budi untuk posisi desainer", "wawancara Sari buat posisi copywriter", "tolong wawancara kandidat Andi sebagai analis",
                  "mulai wawancara Dina posisi admin", "NAMA wawancara pelamar Rudi untuk posisi staf"],
    'status': ["NAMA lagi apa", "bagaimana progres tim", "siapa yang sedang sibuk", "status kerjaan NAMA", "ada update apa hari ini",
               "kondisi kantor bagaimana", "NAMA sudah selesai belum", "siapa yang lagi luang", "laporan NAMA sampai mana", "progres hari ini"],
    'praise': ["NAMA kerjamu bagus terima kasih", "mantap semua terima kasih", "kerja bagus NAMA", "keren sekali hasilnya",
               "terima kasih tim kerja bagus", "hebat NAMA", "NAMA mantap hasilnya", "bagus sekali semuanya"],
    'chat': ["NAMA halo apa kabar", "NAMA menurutmu bagaimana", "NAMA lagi memikirkan apa", "hai NAMA", "NAMA kamu suka kerja di sini",
             "NAMA ada saran buat saya", "NAMA bisa jelaskan", "pagi NAMA", "NAMA apa pendapatmu", "NAMA tanya sesuatu boleh"],
}

SEED.update({
    'upload': ["NAMA masukkan pdf laporan NAMA ke folder NAMA", "NAMA masukin file laporan ke folder NAMA", "NAMA upload laporan ke drive",
               "simpan laporan NAMA di folder NAMA", "NAMA taruh pdf laporan ke folder baru", "NAMA unggah semua laporan ke folder masing masing",
               "kirim laporan NAMA ke drive folder NAMA", "NAMA buat folder baru lalu masukkan pdf laporan",
               "NAMA simpan pdf laporan ke folder sesuai nama", "NAMA upload semua laporan ke drive", "masukkan laporan NAMA ke folder NAMA",
               "NAMA tolong pindahkan file pdf laporan ke folder NAMA kalau belum ada buat baru"],
    'seat': ["semua kembali ke meja", "tertib semua duduk", "NAMA balik ke meja", "bubar semua kembali bekerja",
             "rapat selesai silakan kembali", "semua duduk", "kembali ke tempat masing masing", "NAMA duduk", "semua tertib"],
    'stop': ["semua diam dengarkan saya", "tenang semua", "perhatian semua", "NAMA diam dulu", "stop semua berhenti dulu",
             "diam", "simak baik baik", "semua berhenti sebentar"],
    'go': ["lanjutkan saja", "silakan lanjut", "teruskan kerjanya", "lanjut semua", "NAMA lanjut kerja", "kembali seperti biasa"],
    'line': ["semua berbaris menghadap saya", "kumpul ke sini semua", "semua ke depan", "merapat semua", "semua mendekat"],
    'cancel': ["batalkan semua tugas", "hentikan semua pekerjaan", "NAMA batalkan tugasmu", "hapus antrean tugas semua"],
})

STOP = {'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'itu', 'ini', 'saya', 'kamu', 'anda', 'aku', 'dengan', 'atau', 'kita', 'nya'}


def lev(a, b):
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 1:
        return 2
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def stem(w):
    if len(w) > 5:
        for suf in ('kan', 'lah', 'nya', 'in', 'i'):
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[:-len(suf)]
                break
    if len(w) > 5:
        for pre in ('meny', 'meng', 'mem', 'men', 'me', 'ber', 'per', 'ter', 'di', 'ng'):
            if w.startswith(pre) and len(w) - len(pre) >= 4:
                w = w[len(pre):]
                break
    return w


def norm_tokens(tokens):
    out = []
    for t in tokens:
        low = t.lower()
        low = SLANG.get(low, low)
        out.extend(low.split())
    return out


def feats_from_text(masked):
    """masked: teks yang namanya sudah diganti 'nama'."""
    toks = [t for t in norm_tokens(TOKEN.findall(masked)) if t not in FILLER]
    words = [t for t in toks if re.match(r"\w", t) and t not in HONOR]
    f = []
    for i, w in enumerate(words):
        if re.fullmatch(r"\d[\d.,]*", w):
            w = 'angka'
        f.append('u:' + w)
        s = stem(w)
        if s != w:
            f.append('s:' + s)
        if len(w) >= 5:
            f.append('p:' + w[:4])
        if i:
            f.append('b:' + words[i - 1] + '_' + w)
    if '?' in masked:
        f.append('u:tanya')
    return f


class NB:
    def __init__(self):
        self.cc = defaultdict(float)
        self.fc = defaultdict(lambda: defaultdict(float))
        self.tot = defaultdict(float)
        self.vocab = defaultdict(float)

    def add(self, intent, feats, w=1.0):
        self.cc[intent] += w
        for f in feats:
            self.fc[intent][f] += w
            self.tot[intent] += w
            self.vocab[f] += w

    def predict(self, feats):
        known = [f for f in feats if f in self.vocab]
        uni = [f for f in feats if f.startswith('u:') and f != 'u:nama']
        unk = (sum(1 for f in uni if f not in self.vocab) / len(uni)) if uni else 0.0
        if not known or not self.cc:
            return None, 0.0, 1.0
        V = len(self.vocab) + 1
        tc = sum(self.cc.values())
        z = {}
        for c in self.cc:
            s = math.log((self.cc[c] + 1) / (tc + len(INTENTS)))
            den = self.tot[c] + 0.5 * V
            for f in known:
                s += math.log((self.fc[c].get(f, 0.0) + 0.5) / den)
            z[c] = s
        T = 1 + 0.12 * len(known)
        m = max(z.values())
        ex = {c: math.exp((v - m) / T) for c, v in z.items()}
        S = sum(ex.values())
        best = max(ex, key=ex.get)
        return best, ex[best] / S, unk


class Brain:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.lock = threading.RLock()
        self.samples = []          # {'t','i','w','s','ts'}
        self.aliases = {}          # alias -> NamaKanonik
        self.alias_cand = {}       # "alias|Nama" -> hitung
        self.stats = defaultdict(int)
        self.thr = 0.70
        self.cv_acc = None
        self.wrong = 0
        self.dirty = False
        self.last_study = 0
        self.facts = []            # {'k','s','u','ts','n'}
        self.history = []          # {'t','i','c','ts'}
        self.last_bak = 0
        self.nb = NB()
        self.load()
        self.rebuild()

    # ---------- penyimpanan
    def load(self):
        try:
            with open(self.path, encoding='utf-8') as fh:
                d = json.load(fh)
            self.samples = d.get('samples', [])
            self.aliases = d.get('aliases', {})
            self.alias_cand = d.get('alias_cand', {})
            self.stats.update(d.get('stats', {}))
            self.thr = d.get('thr', 0.70)
            self.cv_acc = d.get('cv_acc')
            self.wrong = d.get('wrong', 0)
            self.facts = d.get('facts', [])
            self.history = d.get('history', [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            d = {'samples': self.samples[-6000:], 'aliases': self.aliases, 'alias_cand': self.alias_cand,
                 'stats': dict(self.stats), 'thr': self.thr, 'cv_acc': self.cv_acc, 'wrong': self.wrong, 'saved': time.time(),
                 'facts': self.facts[-3000:], 'history': self.history[-500:]}
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as fh:
                json.dump(d, fh, ensure_ascii=False)
            try:
                if os.path.exists(self.path) and time.time() - self.last_bak > 600:
                    shutil.copyfile(self.path, self.path + '.bak')
                    self.last_bak = time.time()
            except Exception:
                pass
            os.replace(tmp, self.path)

    # ---------- fakta / pengetahuan yang bertumbuh
    @staticmethod
    def _words(t):
        return {w for w in re.findall(r"[a-z0-9]{4,}", str(t).lower()) if w not in STOP}

    def remember(self, topic, text, url=''):
        with self.lock:
            topic, text = str(topic or '').strip()[:80], str(text or '').strip()[:600]
            if not topic or len(text) < 8:
                return {'ok': False, 'error': 'topik/teks kosong'}
            for f in self.facts:
                if f['k'].lower() == topic.lower() and f['s'][:60] == text[:60]:
                    f['n'] = f.get('n', 0) + 1
                    f['ts'] = int(time.time())
                    self.dirty = True
                    return {'ok': True, 'baru': False, 'total': len(self.facts)}
            self.facts.append({'k': topic, 's': text, 'u': str(url or '')[:200], 'ts': int(time.time()), 'n': 0})
            if len(self.facts) > 3000:
                self.facts.sort(key=lambda f: (f.get('n', 0), f['ts']))
                self.facts = self.facts[-2800:]
            self.stats['fakta'] += 1
            self.dirty = True
            return {'ok': True, 'baru': True, 'total': len(self.facts)}

    def recall(self, q, n=3):
        with self.lock:
            qw = self._words(q)
            if not qw or not self.facts:
                return []
            sc = []
            for f in self.facts:
                fw = self._words(f['k']) | self._words(f['s'])
                o = len(qw & fw)
                if o:
                    sc.append((o + 0.5 * len(qw & self._words(f['k'])), f))
            sc.sort(key=lambda x: -x[0])
            out = []
            for _, f in sc[:n]:
                f['n'] = f.get('n', 0) + 1
                out.append({'k': f['k'], 's': f['s'], 'u': f.get('u', '')})
            if out:
                self.dirty = True
            return out

    def compact(self):
        """gabung contoh kembar (teks+intent sama): bobot naik, jumlah baris turun."""
        with self.lock:
            m = {}
            for s in self.samples:
                k = (s['t'].lower(), s['i'])
                if k in m:
                    m[k]['w'] = min(6.0, m[k].get('w', 1.0) + s.get('w', 1.0) * (0.5 if s.get('s') == 'mandiri' else 1.0))
                    m[k]['ts'] = max(m[k].get('ts', 0), s.get('ts', 0))
                else:
                    m[k] = dict(s)
            self.samples = sorted(m.values(), key=lambda s: s.get('ts', 0))[-6000:]

    def _seed_nb(self):
        nb = NB()
        for intent, arr in SEED.items():
            for s in arr:
                nb.add(intent, feats_from_text(s.replace('NAMA', 'nama')), 1.0)
        return nb

    def rebuild(self):
        with self.lock:
            nb = self._seed_nb()
            for s in self.samples:
                nb.add(s['i'], feats_from_text(s['t']), s.get('w', 1.0))
            self.nb = nb

    # ---------- nama & klausa
    def _name_map(self, roster):
        m = {}
        for r in roster:
            m[r['name'].lower()] = r['name']
        for a, n in self.aliases.items():
            if n.lower() in m:
                m[a] = m[n.lower()]
        return m

    def _match_name(self, low, nmap, orig=None):
        if low in nmap:
            return nmap[low]
        if len(low) >= 5 and orig and orig[:1].isupper() and ('u:' + SLANG.get(low, low)) not in self.nb.vocab:
            for k, v in nmap.items():
                if len(k) >= 5 and lev(low, k) <= 1:
                    return v
        return None

    def _segment(self, text, nmap):
        parts = [p for p in CONJ.split(text) if p and p.strip()]
        out = []
        for p in parts:
            cur = p
            while True:
                cut = None
                for m in re.finditer(r",\s*", cur):
                    before, after = cur[:m.start()], cur[m.end():]
                    at = [t for t in TOKEN.findall(after) if t.lower() not in HONOR][:1]
                    content = [t for t in TOKEN.findall(before) if re.match(r"\w", t) and not self._match_name(t.lower(), nmap, t)
                               and t.lower() not in HONOR]
                    if at and self._match_name(at[0].lower(), nmap, at[0]) and len(content) >= 2:
                        cut = m
                        break
                if not cut:
                    break
                out.append(cur[:cut.start()])
                cur = cur[cut.end():]
            out.append(cur)
        return [o.strip() for o in out if o.strip()]

    def _analyse(self, clause, nmap, depts):
        toks = TOKEN.findall(clause)
        names, masked, clean = [], [], []
        skip_honor = False
        low_all = [t.lower() for t in toks]
        for i, t in enumerate(toks):
            low = t.lower()
            nm = self._match_name(low, nmap, t) if re.match(r"\w", t) and len(low) >= 3 else None
            if nm:
                if nm not in names:
                    names.append(nm)
                masked.append('nama')
                continue
            if low in HONOR and i + 1 < len(toks) and self._match_name(toks[i + 1].lower(), nmap, toks[i + 1]):
                continue
            masked.append(t)
            for w in norm_tokens([t]):
                if re.match(r"\w", w) and w not in TEXT_DROP:
                    clean.append(w)
        joined = ' '.join(low_all)
        dept = None
        mt = re.search(r"\b(?:tim|divisi|bagian|kepala)\s+([\w&]+)", joined)
        if mt:
            c = DEPT_WORDS.get(mt.group(1))
            if c and (not depts or c in depts):
                dept = c
        allf = bool(re.search(r"\b(semua|seluruh|kalian|semuanya|bareng|all)\b", joined))
        text = ' '.join(clean)
        text = (text[:1].upper() + text[1:]) if text else ''
        unk_actor = False
        if not names:
            for t in toks:
                if t.lower() in HONOR or not re.match(r"\w", t):
                    continue
                lw = SLANG.get(t.lower(), t.lower())
                if t[:1].isupper() and len(t) >= 3 and ('u:' + lw) not in self.nb.vocab and t.lower() not in self.aliases:
                    unk_actor = True
                break
        return {'orig': clause, 'names': names, 'masked': ' '.join(masked), 'dept': dept, 'all': allf,
                'unk_actor': unk_actor, 'text': text, 'norm': ' '.join(w for w in norm_tokens([t.lower() for t in masked]) if w != 'nama')}

    # ---------- slot
    def _build(self, intent, cl, carry, selected, roster):
        names = cl['names']
        used_sel = False
        who = list(names)
        if not who and cl['dept']:
            who = ['dept:' + cl['dept']]
        if not who and cl['all']:
            who = ['semua']
        if not who and carry:
            who = list(carry)
        if not who and selected:
            who = [selected]
            used_sel = True
        txt, norm = cl['text'], cl['norm']
        pen = 0.6 if used_sel else 1.0

        def per(t, extra=None, wl=None):
            return [dict({'t': t, 'who': w}, **(extra or {})) for w in (wl or who)]

        if intent == 'task':
            if len(txt) < 6:
                return None, 0
            wl = who or ['auto']
            return per('task', {'text': txt}, wl), (pen if names or not who else pen)
        if intent == 'it_fix':
            if len(txt) < 6:
                return None, 0
            itn = [r['name'] for r in roster if r.get('dept') == 'it' and r['name'] in names]
            return per('it_fix', {'text': txt}, itn or ['auto']), 1.0
        if intent == 'meeting':
            m = re.search(r"\b(?:soal|tentang|mengenai|bahas|membahas|agenda)\s+(.+)$", norm)
            tp = m.group(1).strip().capitalize() if m else ''
            return [{'t': 'meeting', 'who': ('dept:' + cl['dept']) if cl['dept'] else 'semua', 'text': tp}], 1.0
        if intent == 'coffee':
            return per('coffee', None, who or ['semua']), pen
        if intent in ('summon', 'goto', 'focus', 'duty_add', 'duty_remove', 'chat'):
            if not who or who == ['semua']:
                return None, 0
        if intent == 'summon':
            return per('summon'), pen
        if intent == 'goto':
            place = None
            for rx, p in PLACES:
                if re.search(rx, norm):
                    place = p
                    break
            if not place and re.search(r"\b(kembali|meja)\b", norm):
                place = 'meja'
            if not place:
                return None, 0
            return per('goto', {'place': place}), pen
        if intent == 'focus':
            m = re.search(r"(?:fokus(?:kan)?|alihkan(?: pekerjaan)?|ganti fokus(?: kerja\w*)?)\s*(?:ke|jadi|menjadi|pada)?\s*(.+)$", norm)
            t = m.group(1).strip() if m else ''
            if len(t) < 3:
                return None, 0
            return per('focus', {'text': t.capitalize()}), pen
        if intent in ('duty_add', 'duty_remove'):
            t = re.sub(r"\b(mulai sekarang|sekarang|juga|tupoksi\w*|tugas tambahan|tugas pokok|tugas|tanggung jawab\w*|bertanggung jawab|tidak lagi|tidak usah|hapus|lepas|kamu|ikut|atas|dari|baru\w*)\b", ' ', norm)
            t = re.sub(r"\s+", ' ', t).strip()
            if len(t) < 3:
                return None, 0
            return per(intent, {'text': t.capitalize()}), pen
        if intent == 'interview':
            m = re.search(r"\bwawancara\b\s*(?:kandidat|pelamar|calon|si|bapak|ibu|mas|mbak|\s)*([A-Za-z][\w.'\-]*(?:\s+[A-Za-z][\w.'\-]*){0,2}?)\s+(?:untuk|sebagai|posisi|jadi|buat)\b",
                          re.sub(r"\b[Ww]awancara\w*|\b[Ii]nterview\b", 'wawancara', cl['orig']))
            p = re.search(r"\b(?:untuk posisi|untuk|sebagai|posisi|jadi|buat)\s+(?:posisi\s+)?(.+?)[.!?]*$", cl['orig'], re.I)
            hr = [r['name'] for r in roster if r.get('dept') == 'hr' and r['name'] in names]
            if not m or not p:
                return None, 0
            return [{'t': 'interview', 'who': (hr[0] if hr else 'auto'), 'cand': m.group(1).strip(), 'pos': p.group(1).strip()}], 1.0
        if intent == 'upload':
            adm = [r['name'] for r in roster if r.get('dept') == 'ad']
            actor = next((n for n in names if n in adm), None) or (adm[0] if adm else 'auto')
            owners = [n for n in names if n not in adm]
            fm = re.search(r"folder\s+(?:baru\s+)?(?:bernama\s+|namanya\s+|dengan nama\s+)?([A-Za-z0-9_\-]+(?:\s+[A-Za-z0-9_\-]+)?)", cl['orig'], re.I)
            folder = ''
            if fm:
                ws = fm.group(1).split()
                bad = {'baru', 'sesuai', 'masing', 'ya', 'dong', 'sekarang', 'dan', 'lalu', 'kalau', 'jika', 'bila', 'nanti', 'itu', 'ini', 'nya'}
                keep = []
                for w in ws:
                    if w.lower() in bad:
                        break
                    keep.append(w)
                folder = ' '.join(keep)
            if folder and not owners:
                fo = next((n for n in (r['name'] for r in roster) if n.lower() == folder.lower()), None)
                if fo and fo not in adm:
                    owners = [fo]
            return [{'t': 'upload', 'who': actor, 'owners': owners, 'owner': owners[0] if len(owners) == 1 else ('semua' if not owners else ''),
                     'folder': folder, 'what': 'laporan'}], 1.0
        if intent in ('seat', 'stop', 'go', 'line', 'cancel'):
            return per(intent, None, who or ['semua']), pen
        if intent == 'status':
            return per('status', None, who or ['semua']), pen
        if intent == 'praise':
            return per('praise', None, who or ['semua']), pen
        if intent == 'chat':
            return per('chat', {'text': cl['orig']}, who[:1]), pen
        return None, 0

    # ---------- paham
    def understand(self, text, roster, depts=None, selected=None, ctx=None):
        with self.lock:
            self.stats['requests'] += 1
            text = (text or '').strip()
            roster = roster or []
            nmap = self._name_map(roster)
            low = text.lower()
            resp = {'ok': True, 'confident': False, 'conf': 0.0, 'acts': [], 'reply': None, 'ask': None,
                    'src': 'otak_luar', 'thr': round(self._thr(), 3)}
            if re.search(r"\bsiapa\b.*\b(luang|nganggur|santai|senggang|free|kosong|menganggur)\b", low) and roster and any('st' in r for r in roster):
                who = [r['name'] for r in roster if str(r.get('st', '')).startswith('luang')]
                resp.update(confident=True, conf=0.95, reply={'who': 'Sistem', 'text': ('Yang sedang luang: ' + ', '.join(who) + '.') if who else 'Semua sedang sibuk.'})
                self.stats['local'] += 1
                return resp
            if re.search(r"\bsiapa\b.*\b(sibuk|bekerja|kerja|ngerjain|mengerjakan)\b", low) and roster and any('st' in r for r in roster):
                who = [r['name'] + ' (' + str(r['st']).replace('bekerja: ', '') + ')' for r in roster if str(r.get('st', '')).startswith('bekerja')]
                resp.update(confident=True, conf=0.95, reply={'who': 'Sistem', 'text': ('Yang sedang bekerja: ' + '; '.join(who) + '.') if who else 'Tidak ada yang sedang bekerja.'})
                self.stats['local'] += 1
                return resp
            clauses = [self._analyse(c, nmap, depts) for c in self._segment(text, nmap)]
            acts, confs, carry, why = [], [], None, []
            for cl in clauses:
                feats = feats_from_text(cl['masked'])
                intent, p, unk = self.nb.predict(feats)
                if not intent:
                    confs.append(0.0)
                    why.append('tak dikenal')
                    continue
                built, pen = self._build(intent, cl, carry, selected, roster)
                c = p * (1 - 0.5 * unk) * (pen if built else 0) * (0.5 if cl.get('unk_actor') else 1.0)
                confs.append(c)
                why.append('%s %.2f' % (intent, c))
                if built:
                    acts += built
                    if cl['names']:
                        carry = cl['names']
            conf = min(confs) if confs else 0.0
            resp['acts'] = acts
            resp['conf'] = round(conf, 3)
            resp['why'] = why
            resp['confident'] = bool(acts) and conf >= self._thr() and len(acts) <= 8
            if resp['confident']:
                self.stats['local'] += 1
                self._self_train(text, clauses, acts, conf)
            ing = self.recall(text, 3)
            if ing:
                resp['ingat'] = ing
            return resp

    def _self_train(self, text, clauses, acts, conf):
        """perintah yang sangat yakin dipahami -> contoh berbobot kecil (kosakata Anda bertambah sendiri)."""
        try:
            if len(clauses) != 1 or not acts or conf < min(0.97, self._thr() + 0.12):
                return
            cl, intent = clauses[0], acts[0]['t']
            if intent not in INTENTS or intent == 'chat':
                return
            masked = cl['masked']
            if any(s['t'] == masked and s['i'] == intent for s in self.samples[-400:]):
                return
            self.samples.append({'t': masked, 'i': intent, 'w': 0.3, 's': 'mandiri', 'ts': int(time.time())})
            self.nb.add(intent, feats_from_text(masked), 0.3)
            self.history.append({'t': text[:160], 'i': intent, 'c': round(conf, 3), 'ts': int(time.time())})
            self.history = self.history[-500:]
            self.stats['mandiri'] += 1
            self.dirty = True
        except Exception:
            pass

    def _thr(self):
        return min(0.95, self.thr + min(0.10, self.wrong * 0.01))

    # ---------- belajar
    def learn(self, text, acts, w=1.0, src='llm', roster=None, depts=None, verdict=None):
        with self.lock:
            roster = roster or []
            nmap = self._name_map(roster)
            if verdict == 'salah':
                self.wrong += 1
                self.stats['salah'] += 1
                self.dirty = True
                return {'ok': True, 'catatan': 'ditandai salah, ambang yakin dinaikkan'}
            seq = []
            for a in acts or []:
                t = a.get('t')
                if t not in INTENTS:
                    continue
                key = (t, a.get('text', ''))
                if not seq or seq[-1][0] != key:
                    seq.append((key, a))
            clauses = [self._analyse(c, nmap, depts) for c in self._segment(text, nmap)]
            pairs = []
            if seq and len(seq) == len(clauses):
                pairs = [(clauses[i], seq[i][1]) for i in range(len(seq))]
            elif len(seq) == 1:
                one = self._analyse(text, nmap, depts)
                pairs = [(one, seq[0][1])]
            n = 0
            for cl, a in pairs:
                self._alias_learn(cl, a, nmap, src)
                masked = self._mask_aliases(cl['masked'], cl, nmap)
                self.samples.append({'t': masked, 'i': a['t'], 'w': float(w), 's': src, 'ts': int(time.time())})
                self.nb.add(a['t'], feats_from_text(masked), float(w))
                n += 1
            if n:
                self.stats['dipelajari'] += n
                self.stats['dari_' + src] += n
                if src == 'koreksi':
                    self.stats['koreksi'] += 1
                self.dirty = True
            return {'ok': True, 'dipelajari': n}

    def _mask_aliases(self, masked, cl, nmap):
        return masked

    def _alias_learn(self, cl, act, nmap, src):
        who = act.get('who')
        if not who or who in ('auto', 'semua') or str(who).startswith('dept:'):
            return
        canon = [n for n in nmap.values() if n == who]
        if not canon or who in cl['names']:
            return
        toks = TOKEN.findall(cl['orig'])
        for pos, tok in enumerate(toks):
            low = tok.lower()
            if not (tok[:1].isupper() or pos < 2):
                continue
            if len(low) < 3 or not re.fullmatch(r"[a-z]+", low) or low in SLANG or low in STOP or low in HONOR or low in FILLER:
                continue
            freq = self.nb.vocab.get('u:' + SLANG.get(low, low), 0)
            key = low + '|' + who
            if freq == 0 or key in self.alias_cand:
                inc = 2 if (src == 'koreksi' or (src == 'llm' and tok[:1].isupper() and freq == 0)) else 1
                self.alias_cand[key] = self.alias_cand.get(key, 0) + inc
                if self.alias_cand[key] >= 2 and low not in self.aliases:
                    self.aliases[low] = who
                    self.stats['alias_baru'] += 1

    # ---------- belajar mandiri
    def study(self, force=False):
        with self.lock:
            if not (self.dirty or force):
                return
            self.compact()
            self.rebuild()
            usr = [s for s in self.samples if s['i'] in INTENTS and s.get('s') != 'mandiri']
            if len(usr) >= 15:
                K = 5
                folds = [usr[i::K] for i in range(K)]
                res = []
                for k in range(K):
                    nb = self._seed_nb()
                    for j in range(K):
                        if j != k:
                            for s in folds[j]:
                                nb.add(s['i'], feats_from_text(s['t']), s.get('w', 1.0))
                    for s in folds[k]:
                        pr, p, unk = nb.predict(feats_from_text(s['t']))
                        res.append((p * (1 - 0.5 * unk), pr == s['i']))
                self.cv_acc = round(sum(1 for _, ok in res if ok) / len(res), 3)
                best = None
                t = 0.50
                while t <= 0.951:
                    sub = [ok for c, ok in res if c >= t]
                    if len(sub) >= 8 and sum(sub) / len(sub) >= 0.93:
                        best = round(t, 3)
                        break
                    t += 0.025
                self.thr = best if best is not None else 0.85
            self.last_study = time.time()
            self.dirty = False
            self.stats['sesi_belajar'] += 1
            self.save()

    def report(self):
        with self.lock:
            req = max(1, self.stats.get('requests', 0))
            return {'ok': True, 'contoh_bibit': sum(len(v) for v in SEED.values()), 'contoh_belajar': len(self.samples),
                    'alias': self.aliases, 'ambang_yakin': round(self._thr(), 3), 'akurasi_uji_silang': self.cv_acc,
                    'permintaan': self.stats.get('requests', 0), 'dijawab_sendiri': self.stats.get('local', 0),
                    'persen_mandiri': round(100 * self.stats.get('local', 0) / req, 1), 'dilaporkan_salah': self.wrong,
                    'koreksi': self.stats.get('koreksi', 0), 'sesi_belajar': self.stats.get('sesi_belajar', 0),
                    'fakta_tersimpan': len(self.facts), 'riwayat': len(self.history), 'kosakata': len(self.nb.vocab),
                    'contoh_mandiri': self.stats.get('mandiri', 0)}


def _public_host(host):
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return False
    for i in infos:
        ip = ipaddress.ip_address(i[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return bool(infos)


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlparse(newurl)
        if u.scheme not in ('http', 'https') or not u.hostname or not _public_host(u.hostname):
            raise ValueError('redirect ke alamat tidak diizinkan')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_text(url, limit=12000):
    u = urllib.parse.urlparse(str(url or '').strip())
    if u.scheme not in ('http', 'https') or not u.hostname:
        return {'ok': False, 'error': 'hanya http/https'}
    if not _public_host(u.hostname):
        return {'ok': False, 'error': 'hanya alamat internet publik yang boleh diambil'}
    try:
        op = urllib.request.build_opener(_SafeRedirect)
        rq = urllib.request.Request(u.geturl(), headers={'User-Agent': 'Mozilla/5.0 OtakLuar/2', 'Accept': 'text/html,application/json,text/plain;q=0.9,*/*;q=0.5',
                                                         'Accept-Language': 'id,en;q=0.8'})
        with op.open(rq, timeout=15) as r:
            raw = r.read(900000)
            ct = r.headers.get('Content-Type', '')
            enc = r.headers.get_content_charset() or 'utf-8'
        txt = raw.decode(enc, 'replace')
        if 'html' in ct.lower() or re.match(r"\s*<", txt):
            txt = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", ' ', txt)
            txt = re.sub(r"(?s)<[^>]+>", ' ', txt)
            txt = _html.unescape(txt)
        txt = re.sub(r"\s+", ' ', txt).strip()
        return {'ok': True, 'text': txt[:limit], 'type': ct, 'len': len(txt)}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:200]}


# BRAIN diinisialisasi di bagian bawah (setelah class handler terdefinisi)
BRAIN = None  # placeholder; diisi oleh blok inisialisasi di akhir file
DEMO_NAMES = ['Rina', 'Dimas', 'Sari', 'Bayu', 'Lia', 'Nadia', 'Eko', 'Maya', 'Tono', 'Fajar', 'Hendra', 'Citra', 'Arman', 'Maharani',
              'Fira', 'Akbar', 'Dewi', 'Galih', 'Wulan', 'Hesti', 'Joko', 'Sinta', 'Bima', 'Kirana', 'Rizal', 'Putri', 'Fikri',
              'Rendra', 'Salsa', 'Laras', 'Teguh', 'Nirmala']
DEMO_DEP = ['mk', 'mk', 'mk', 'mk', 'ds', 'rd', 'rd', 'hr', 'hr', 'ds', 'mk', 'ds', 'rd', 'pm', 'fn', 'fn', 'ad', 'au', 'au', 'fo', 'fo',
            'lb', 'it', 'it', 'it', 'it', 'it', 'fo', 'fo', 'fu', 'fu', 'fu']
DEMO_ROSTER = [{'name': n, 'dept': d, 'st': 'luang'} for n, d in zip(DEMO_NAMES, DEMO_DEP)]


class handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _norm_path(self):
        """Strip prefix /otak agar path routing tetap konsisten di Vercel maupun lokal."""
        p = self.path
        if p.startswith('/otak'):
            p = p[5:] or '/'
        return p

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        p = self._norm_path()
        if p.startswith('/health'):
            return self._send(200, {'ok': True, 'nama': 'otak_luar', 'versi': 2})
        if p.startswith('/stats'):
            return self._send(200, BRAIN.report())
        if p.startswith('/fetch'):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(p).query)
            return self._send(200, fetch_text((q.get('url') or [''])[0]))
        if p.startswith('/memory'):
            with BRAIN.lock:
                return self._send(200, {'ok': True, 'fakta': BRAIN.facts[-30:], 'riwayat': BRAIN.history[-30:], 'total_fakta': len(BRAIN.facts)})
        if p.startswith('/export'):
            return self._send(200, {'samples': BRAIN.samples, 'aliases': BRAIN.aliases})
        self._send(404, {'ok': False})

    def do_POST(self):
        try:
            n = int(self.headers.get('Content-Length') or 0)
            d = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
        except Exception:
            return self._send(400, {'ok': False, 'error': 'JSON tidak valid'})
        p = self._norm_path()
        try:
            if p.startswith('/understand'):
                r = BRAIN.understand(d.get('text'), d.get('roster'), d.get('depts'), d.get('selected'), d.get('ctx'))
                return self._send(200, r)
            if p.startswith('/fetch'):
                return self._send(200, fetch_text(d.get('url')))
            if p.startswith('/remember'):
                return self._send(200, BRAIN.remember(d.get('topic'), d.get('text'), d.get('url')))
            if p.startswith('/recall'):
                return self._send(200, {'ok': True, 'hasil': BRAIN.recall(d.get('q'), int(d.get('n') or 3))})
            if p.startswith('/learn'):
                r = BRAIN.learn(d.get('text'), d.get('acts'), d.get('w', 1.0), d.get('src', 'llm'), d.get('roster'), d.get('depts'), d.get('verdict'))
                return self._send(200, r)
        except Exception as e:
            return self._send(500, {'ok': False, 'error': str(e)})
        self._send(404, {'ok': False})


def study_loop():
    while True:
        time.sleep(60)
        try:
            BRAIN.study()
        except Exception:
            pass


def selftest():
    import tempfile
    global BRAIN
    BRAIN = Brain(os.path.join(tempfile.mkdtemp(), 'x.json'))
    ok = 0
    cases = [("Rina bikinin caption buat promo akhir bulan dong", 'task', 'Rina'),
             ("semua kumpul dong kita rapat soal target bulan depan", 'meeting', 'semua'),
             ("Dimas ngopi dulu sana", 'coffee', 'Dimas'),
             ("Kirana tombol kirimnya kekecilan, gedein dikit", 'it_fix', None),
             ("panggil Sari ke sini", 'summon', 'Sari'),
             ("Bayu ke pantry ya", 'goto', 'Bayu'),
             ("Tono wawancara Budi untuk posisi desainer", 'interview', None),
             ("Dewi masukin pdf laporan Akbar ke folder Akbar, kalau belum ada folder nya buat baru", 'upload', 'Dewi'),
             ("tlg simpenin laporan Teguh di drive folder Teguh", 'upload', 'Dewi'),
             ("semua tertib duduk dulu", 'seat', 'semua'),
             ("diam semua dengarkan saya", 'stop', 'semua'),
             ("udah lanjut aja semuanya", 'go', 'semua')]
    for t, intent, who in cases:
        r = BRAIN.understand(t, DEMO_ROSTER)
        good = bool(r['acts']) and r['acts'][0]['t'] == intent and (who is None or r['acts'][0]['who'] == who)
        ok += good
        print(('OK  ' if good else 'GAGAL'), t, '->', [(a['t'], a['who']) for a in r['acts']], r['conf'], r.get('why'))
    print('seed: %d/%d' % (ok, len(cases)))
    # belajar kata gaul baru + alias
    r0 = BRAIN.understand("Wiwi sikat bikin poster diskon dong", DEMO_ROSTER)
    print('sebelum belajar:', r0['confident'], r0['conf'], [(a['t'], a['who']) for a in r0['acts']])
    lab = [{'t': 'task', 'who': 'Dewi', 'text': 'Buat poster diskon'}]
    for t in ["Wiwi sikat bikin poster diskon dong", "Wiwi tolong bikinin poster promo gajian", "Wiwi bikin banner diskon akhir tahun"]:
        BRAIN.learn(t, lab, 1.0, 'llm', DEMO_ROSTER)
    BRAIN.study(force=True)
    r1 = BRAIN.understand("Wiwi bikin poster diskon lagi", DEMO_ROSTER)
    print('sesudah belajar:', r1['confident'], r1['conf'], [(a['t'], a['who']) for a in r1['acts']], 'alias:', BRAIN.aliases)
    print(BRAIN.remember('Pemasaran digital', 'Pemasaran digital memakai kanal online seperti media sosial dan mesin pencari.', 'http://x'))
    print('recall:', BRAIN.recall('strategi pemasaran media sosial'))
    print('fetch lokal diblokir:', fetch_text('http://127.0.0.1:8765/health'))
    print(json.dumps(BRAIN.report(), ensure_ascii=False))
    return ok == len(cases)



# ── Vercel Serverless entrypoint ──────────────────────────────────────────────
# BRAIN diinisialisasi sekali per container instance.
# Memori disimpan di /tmp/otak_luar_memori.json (persisten dalam 1 instance).
import threading as _th
try:
    BRAIN = Brain()
    _th.Thread(target=study_loop, daemon=True).start()
except Exception as _e:
    import sys
    print('BRAIN init error:', _e, file=sys.stderr)