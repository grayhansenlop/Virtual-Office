#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MULAI KANTOR — launcher satu klik
===================================
Jalankan: py mulai_kantor.py
  → otak_luar.py aktif di port 8765
  → Kantor Marketing terbuka di browser port 8000

Berhenti: tutup jendela ini (Ctrl+C)
"""
import os, sys, subprocess, time, threading, webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

# ── Konfigurasi ───────────────────────────────────────────────────────────────
KANTOR_DIR  = os.path.dirname(os.path.abspath(__file__))
OTAK_SCRIPT = r"c:\Users\ASUS\Downloads\otak_luar.py"   # lokasi otak_luar.py
KANTOR_HTML = "index.html"                               # relatif dari folder ini
KANTOR_PORT = 8000
OTAK_PORT   = 8765
PY          = sys.executable   # path Python yang sama dengan launcher ini

# ── Jalankan otak_luar.py sebagai proses terpisah ─────────────────────────────
def start_otak():
    if not os.path.exists(OTAK_SCRIPT):
        print(f"[!] otak_luar.py tidak ditemukan di: {OTAK_SCRIPT}")
        print("    Edit OTAK_SCRIPT di mulai_kantor.py sesuai lokasi file Anda.")
        return None
    print(f"[+] Menjalankan otak_luar.py di port {OTAK_PORT}...")
    proc = subprocess.Popen(
        [PY, OTAK_SCRIPT, "--host", "127.0.0.1", "--port", str(OTAK_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    time.sleep(1.5)  # beri waktu server siap
    if proc.poll() is not None:
        print("[!] otak_luar.py gagal start.")
        return None
    print(f"    Otak luar aktif di http://127.0.0.1:{OTAK_PORT}")
    return proc

# ── Serve HTML via localhost (bukan file://) ───────────────────────────────────
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def log_error(self, *a): pass

def start_web():
    os.chdir(KANTOR_DIR)
    srv = HTTPServer(("127.0.0.1", KANTOR_PORT), QuietHandler)
    print(f"[+] Kantor Marketing di http://127.0.0.1:{KANTOR_PORT}")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

# ── Buka browser setelah server siap ─────────────────────────────────────────
def open_browser():
    url = f"http://127.0.0.1:{KANTOR_PORT}/{KANTOR_HTML}"
    time.sleep(0.8)
    webbrowser.open(url)
    print(f"[+] Browser dibuka di {url}")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  KANTOR MARKETING AI — Launcher")
    print("=" * 55)
    otak_proc = start_otak()
    web_srv   = start_web()
    threading.Thread(target=open_browser, daemon=True).start()
    print("-" * 55)
    print("  Tekan Ctrl+C untuk menghentikan semua.")
    print("=" * 55)
    try:
        while True:
            time.sleep(1)
            # restart otak jika mati
            if otak_proc and otak_proc.poll() is not None:
                print("[!] Otak luar mati, restart...")
                otak_proc = start_otak()
    except KeyboardInterrupt:
        print("\n[+] Menghentikan server...")
        if otak_proc:
            otak_proc.terminate()
        web_srv.shutdown()
        print("    Selesai.")
