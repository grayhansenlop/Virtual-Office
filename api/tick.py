#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api/tick.py — Vercel Cron Function (setiap 1 menit)
Memajukan simulasi kantor: waktu kerja, selesaikan tugas, update mode karyawan.
Dipanggil otomatis oleh Vercel Cron — tidak perlu browser terbuka.
"""
import json, time, random
from http.server import BaseHTTPRequestHandler
# Import helper state dari state.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from state import read_state, write_state

# Mode karyawan & durasi default (detik)
WORK_DURATION   = 25 * 60   # 25 menit kerja
COFFEE_DURATION = 10 * 60   # 10 menit istirahat
MEET_DURATION   = 30 * 60   # 30 menit rapat

def advance_simulation(state: dict, elapsed_s: int = 60) -> dict:
    """Majukan simulasi sejumlah elapsed_s detik."""
    now = int(time.time())
    if 'last_tick' not in state:
        state['last_tick'] = now - elapsed_s
    elapsed = min(now - state['last_tick'], 600)  # max 10 menit sekali loncat
    state['last_tick'] = now

    roster = state.get('roster', [])
    for p in roster:
        mode     = p.get('mode', 'luang')
        mode_t   = p.get('mode_t', now)
        duration = now - mode_t

        if mode == 'work' and duration >= WORK_DURATION:
            # Selesai kerja → luang sebentar
            cur = p.get('cur', {})
            if cur:
                p['done'] = p.get('done', [])
                p['done'].append({**cur, 'selesai': now})
                if len(p['done']) > 20:
                    p['done'] = p['done'][-20:]
            p['cur']    = {}
            p['mode']   = 'luang'
            p['mode_t'] = now

        elif mode == 'coffee' and duration >= COFFEE_DURATION:
            # Selesai kopi → kembali kerja
            p['mode']   = 'luang'
            p['mode_t'] = now

        elif mode == 'meet' and duration >= MEET_DURATION:
            p['mode']   = 'luang'
            p['mode_t'] = now

        elif mode == 'luang':
            # Ada antrean tugas? mulai kerja
            q = p.get('queue', [])
            if q:
                p['cur']    = q.pop(0)
                p['queue']  = q
                p['mode']   = 'work'
                p['mode_t'] = now

    state['roster'] = roster
    state['sim_updated'] = now
    return state


class handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, obj):
        import json as _j
        b = _j.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        """Vercel Cron memanggil GET /api/tick setiap 1 menit."""
        try:
            state, sha = read_state()
            if not state:
                return self._send(200, {'ok': True, 'msg': 'state kosong, skip'})
            updated = advance_simulation(state)
            write_state(updated, sha)
            self._send(200, {'ok': True, 'msg': 'tick ok', 'ts': updated['last_tick']})
        except Exception as e:
            self._send(500, {'ok': False, 'error': str(e)})

    def do_POST(self):
        self.do_GET()

