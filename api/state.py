#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api/state.py — Vercel Serverless Function
GET  /api/state  → baca state kantor dari GitHub
POST /api/state  → simpan state kantor ke GitHub
"""
import json, os, base64, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_OWNER = os.environ.get('GITHUB_OWNER', 'grayhansenlop')
GITHUB_REPO  = os.environ.get('GITHUB_REPO',  'kantor-state')
GITHUB_FILE  = 'kantor_state.json'
API_BASE     = f'https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE}'

def _gh_headers():
    return {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'User-Agent': 'kantor-marketing',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github+json',
    }

def _cors(h):
    h.send_header('Access-Control-Allow-Origin', '*')
    h.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    h.send_header('Access-Control-Allow-Headers', '*')

def read_state():
    """Baca state dari GitHub, return (state_dict, sha)."""
    req = urllib.request.Request(API_BASE, headers=_gh_headers())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        content = base64.b64decode(data['content']).decode('utf-8')
        return json.loads(content), data['sha']
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}, None   # file belum ada
        raise

def write_state(state_dict, sha=None):
    """Tulis state ke GitHub (create atau update)."""
    content_b64 = base64.b64encode(
        json.dumps(state_dict, ensure_ascii=False, indent=2).encode('utf-8')
    ).decode('ascii')
    body = {
        'message': 'update kantor state',
        'content': content_b64,
    }
    if sha:
        body['sha'] = sha
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(API_BASE, data=data, headers=_gh_headers(), method='PUT')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


class handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        _cors(self)
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        _cors(self)
        self.end_headers()

    def do_GET(self):
        try:
            state, sha = read_state()
            self._send(200, {'ok': True, 'state': state, 'sha': sha})
        except Exception as e:
            self._send(500, {'ok': False, 'error': str(e)})

    def do_POST(self):
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            state = body.get('state', {})
            sha   = body.get('sha')
            if not state:
                return self._send(400, {'ok': False, 'error': 'state kosong'})
            result = write_state(state, sha)
            new_sha = result.get('content', {}).get('sha', sha)
            self._send(200, {'ok': True, 'sha': new_sha})
        except Exception as e:
            self._send(500, {'ok': False, 'error': str(e)})

