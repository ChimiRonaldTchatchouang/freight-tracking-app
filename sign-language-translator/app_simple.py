#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string, Response
from flask_cors import CORS
import os, re, time, threading
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from pathlib import Path

app = Flask(__name__)
CORS(app)

# ── Self-host MediaPipe files — download once at startup, serve same-origin ──
_MP_VER = '0.4.1646424915'
_DU_VER = '0.3.1620248257'
_MP_DIR = Path('/tmp/mp_cache')
_MP_FILES = [
    (f'https://unpkg.com/@mediapipe/hands@{_MP_VER}/hands.js',                              'hands.js'),
    (f'https://unpkg.com/@mediapipe/hands@{_MP_VER}/hands_solution_packed_assets_loader.js','hands_solution_packed_assets_loader.js'),
    (f'https://unpkg.com/@mediapipe/hands@{_MP_VER}/hands_solution_packed_assets.data',     'hands_solution_packed_assets.data'),
    (f'https://unpkg.com/@mediapipe/hands@{_MP_VER}/hands_solution_simd_wasm_bin.js',       'hands_solution_simd_wasm_bin.js'),
    (f'https://unpkg.com/@mediapipe/hands@{_MP_VER}/hands_solution_simd_wasm_bin.wasm',     'hands_solution_simd_wasm_bin.wasm'),
    (f'https://unpkg.com/@mediapipe/hands@{_MP_VER}/hands_solution_wasm_bin.js',            'hands_solution_wasm_bin.js'),
    (f'https://unpkg.com/@mediapipe/hands@{_MP_VER}/hands_solution_wasm_bin.wasm',          'hands_solution_wasm_bin.wasm'),
    (f'https://unpkg.com/@mediapipe/drawing_utils@{_DU_VER}/drawing_utils.js',              'drawing_utils.js'),
]
_mp_status = {'ready': False, 'done': 0, 'total': len(_MP_FILES), 'error': ''}

# unpkg (Cloudflare) renvoie 403 aux User-Agent non-navigateur → on se fait
# passer pour un navigateur. jsDelivr sert de miroir si unpkg échoue.
_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

def _fetch_bytes(url):
    req = Request(url, headers={'User-Agent': _UA, 'Accept': '*/*'})
    with urlopen(req, timeout=90) as r:
        return r.read()

_PATCH_VER = '7'  # bump whenever patching logic changes to force cache invalidation

# Emscripten installs an ABORTING getter on Module.arguments (and other legacy
# props) via legacyModuleProp(prop, newName). On modern Chrome the runtime reads
# Module.arguments after startup and hits abort("... has been replaced ..."),
# which kills hands.js. The previous patch looked for a literal 'arguments' but
# the real code uses the *variable* `prop`, so it never matched. These three
# independent strategies each key on `prop` — any single match neutralises it:
_PATCH_STRATEGIES = [
    # 1. Neutralise EVERY Emscripten "trap installer" at once. On modern Chrome
    #    the runtime reads symbols (arguments, printErr, …) that these functions
    #    booby-trap with aborting getters/functions on Module. They all share one
    #    signature: a function whose first statement is
    #      if(!Object.getOwnPropertyDescriptor(Module, X)){ ...install abort... }
    #    Injecting `return;` turns them into no-ops, so the missing symbols stay
    #    undefined and the runtime's own `Module[x] || fallback` paths take over
    #    (e.g. printErr → console.warn). Covers legacyModuleProp,
    #    unexportedRuntimeSymbol, unexportedRuntimeFunction and the
    #    INCOMING_MODULE_JS_API check — present and future.
    (re.compile(r'(function\s+\w+\s*\([^)]*\)\s*\{)'
                r'(\s*if\s*\(\s*!\s*Object\.getOwnPropertyDescriptor\(\s*Module\s*,)'),
     r'\1return;\2'),
    # 2. packed_assets_loader.js: on modern Chrome, Module.dataFileDownloads can
    #    be undefined in the progress callback's else-branch, throwing on every
    #    onprogress event and flooding the console. Guard the read.
    (re.compile(r'Module\.dataFileDownloads\[url\]\.loaded\s*=\s*event\.loaded;'),
     'if(Module.dataFileDownloads&&Module.dataFileDownloads[url])Module.dataFileDownloads[url].loaded=event.loaded;'),
]

def _record_patch(fname, total):
    """Persist the patch result so /mp_status can report it to the browser
    (Render server logs aren't visible from the client)."""
    try:
        pf = _MP_DIR / '.patchinfo'
        prev = pf.read_text() if pf.exists() else ''
        lines = [l for l in prev.splitlines() if not l.startswith(fname + ':')]
        lines.append(f'{fname}:{total}')
        pf.write_text('\n'.join(lines))
    except Exception:
        pass

def _patch_mp(fname, raw):
    """Neutralise the Emscripten legacyModuleProp abort trap so hands.js runs on
    modern Chrome. Applied to every glue .js file (no-op where absent)."""
    if not fname.endswith('.js'):
        return raw
    try:
        text = raw.decode('utf-8')
    except Exception:
        return raw
    total = 0
    for pat, repl in _PATCH_STRATEGIES:
        text, n = pat.subn(repl, text)
        if n:
            total += n
            print(f'[MP] {fname}: patched {n}x [{pat.pattern[:38]}]')
    if total > 0:
        _record_patch(fname, total)
    if 'legacyModuleProp' in text and total == 0:
        print(f'[MP] WARNING {fname}: legacyModuleProp present but no strategy matched')
    return text.encode('utf-8')

_dl_lock = threading.Lock()

def _dl_one(url_fname):
    """Download and patch one MediaPipe file; returns True on success.
    Tries unpkg then the jsDelivr mirror, each with a browser User-Agent."""
    url, fname = url_fname
    dest = _MP_DIR / fname
    if dest.exists() and dest.stat().st_size > 100:
        with _dl_lock:
            _mp_status['done'] += 1
        return True
    alts = [url, url.replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/')]
    last_err = ''
    for attempt in range(3):
        for u in alts:
            host = u.split('/')[2]
            try:
                data = _patch_mp(fname, _fetch_bytes(u))
                dest.write_bytes(data)
                with _dl_lock:
                    _mp_status['done'] += 1
                print(f'[MP] ✓ {fname} ({len(data)//1024} KB) via {host}')
                return True
            except Exception as e:
                last_err = f'{fname} <{host}>: {e}'
                print(f'[MP] fail {last_err} (try {attempt+1})')
        if attempt < 2:
            time.sleep(2 ** attempt)
    with _dl_lock:
        _mp_status['error'] = last_err
    try:  # persist to disk so any gunicorn worker can report it via /mp_status
        (_MP_DIR / '.error').write_text(last_err[:300])
    except Exception:
        pass
    return False

_dl_run_lock = threading.Lock()

def _download_mp():
    # Skip if another thread in this process is already downloading.
    if not _dl_run_lock.acquire(blocking=False):
        return
    try:
        _download_mp_inner()
    finally:
        _dl_run_lock.release()

def _download_mp_inner():
    _MP_DIR.mkdir(exist_ok=True)
    # Invalidate cache if patch version changed (Render may keep /tmp between hot deploys)
    ver_file = _MP_DIR / '.patch_ver'
    if not ver_file.exists() or ver_file.read_text().strip() != _PATCH_VER:
        print(f'[MP] patch version changed → clearing cache for re-download')
        for old in _MP_DIR.glob('*.js'):
            old.unlink(missing_ok=True)
        for old in _MP_DIR.glob('*.wasm'):
            old.unlink(missing_ok=True)
        (_MP_DIR / '.patchinfo').unlink(missing_ok=True)
        (_MP_DIR / '.error').unlink(missing_ok=True)
        _mp_status['done'] = 0

    # Download all files in parallel (4 workers) — cuts cold-start from ~2 min to ~30 s.
    # Retry the whole batch a few times: a transient unpkg failure must NOT leave
    # the server permanently "not ready" (which would force the crashing CDN path).
    for round_no in range(6):
        _mp_status['done'] = 0  # re-counted each round (cached files pass the exists-check)
        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(_dl_one, _MP_FILES))
        if all(results):
            _mp_status['ready'] = True
            ver_file.write_text(_PATCH_VER)
            (_MP_DIR / '.error').unlink(missing_ok=True)
            print(f'[MP] ready — {_mp_status["done"]}/{_mp_status["total"]} files in {_MP_DIR}')
            return
        print(f'[MP] round {round_no + 1}: {_mp_status["done"]}/{_mp_status["total"]} OK — retry missing in 5s')
        time.sleep(5)
    print(f'[MP] still incomplete after retries — {_mp_status["done"]}/{_mp_status["total"]}')

_dl_started = False
_dl_start_lock = threading.Lock()

def _files_on_disk():
    return sum(1 for _u, f in _MP_FILES
               if (_MP_DIR / f).exists() and (_MP_DIR / f).stat().st_size > 100)

def _mp_ready_on_disk():
    ver_file = _MP_DIR / '.patch_ver'
    ver_ok = ver_file.exists() and ver_file.read_text().strip() == _PATCH_VER
    return ver_ok and _files_on_disk() == len(_MP_FILES)

def _ensure_download_started():
    """Idempotently launch the downloader in THIS worker process. A thread
    started at import time does not survive a gunicorn fork, so we (re)start it
    on the first request — guaranteeing it runs in a live, request-serving
    worker. Readiness is read from the shared /tmp filesystem, so any worker
    sees the truth regardless of which one did the download."""
    global _dl_started
    with _dl_start_lock:
        if _dl_started:
            return
        _dl_started = True
    threading.Thread(target=_download_mp, daemon=True).start()

# Kick off at import (covers the single-worker / no-fork case).
_ensure_download_started()

@app.route('/mp/<path:filename>')
def serve_mp(filename):
    _ensure_download_started()
    f = (_MP_DIR / filename).resolve()
    mp_root = _MP_DIR.resolve()
    if not (f == mp_root or str(f).startswith(str(mp_root) + '/')):
        return 'forbidden', 403
    if not f.exists():
        return 'not ready', 503
    mime = ('application/wasm' if filename.endswith('.wasm')
            else 'application/javascript; charset=utf-8' if filename.endswith('.js')
            else 'application/octet-stream')
    resp = Response(f.read_bytes(), mimetype=mime)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Cache-Control'] = 'public, max-age=3600'
    return resp

@app.route('/mp_status')
def mp_status_route():
    _ensure_download_started()
    err = ''
    ef = _MP_DIR / '.error'
    if ef.exists():
        try:
            err = ef.read_text()[:300]
        except Exception:
            err = ''
    patch = ''
    pf = _MP_DIR / '.patchinfo'
    if pf.exists():
        try:
            patch = pf.read_text()[:200].replace('\n', ' ')
        except Exception:
            patch = ''
    return jsonify({
        'done':  _files_on_disk(),
        'total': len(_MP_FILES),
        'ready': _mp_ready_on_disk(),
        'error': err,
        'patch': patch,
    })
# ─────────────────────────────────────────────────────────────────────────────

SIGN_MAP = {
    'i':'IX-1','me':'IX-1','my':'IX-1','we':'IX-1PL','you':'IX-2',
    'he':'IX-3','she':'IX-3','they':'IX-3PL',
    'will':'FUTURE','tomorrow':'TOMORROW','today':'TODAY','yesterday':'PAST',
    'hello':'HI','hi':'HI','thank':'THANK','thanks':'THANK',
    'yes':'YES','no':'NO','please':'PLEASE','sorry':'SORRY',
    'want':'WANT','like':'LIKE','love':'LOVE','need':'NEED',
    'go':'GO','come':'COME','eat':'EAT','drink':'DRINK','sleep':'SLEEP',
    'work':'WORK','know':'KNOW','help':'HELP','stop':'STOP',
    'good':'GOOD','bad':'BAD','happy':'HAPPY','sad':'SAD',
    'home':'HOME','school':'SCHOOL','movie':'MOVIE','cinema':'MOVIE',
    'apple':'APPLE','water':'WATER','food':'FOOD',
    'where':'WHERE','when':'WHEN','what':'WHAT','who':'WHO','how':'HOW',
    'je':'IX-1','tu':'IX-2','il':'IX-3','elle':'IX-3','nous':'IX-1PL',
    'vais':'FUTURE','manger':'EAT','veux':'WANT','aller':'GO',
    'pomme':'APPLE','demain':'TOMORROW','bonjour':'HI','merci':'THANK',
    'oui':'YES','non':'NO','bon':'BON','eau':'EAU',
    # ── Laveau 1868 enrichissements ──────────────────────────────────────────
    'aimer':'AIMER','amour':'AIMER','aime':'AIMER',
    'aller':'ALLER','marcher':'ALLER',
    'arbre':'ARBRE',
    'boire':'BOIRE','boisson':'BOIRE',
    'corps':'CORPS',
    'désirer':'DESIRER','désir':'DESIRER','vouloir':'DESIRER',
    'donner':'DONNER','offrir':'DONNER',
    'fort':'FORT','force':'FORT','puissant':'FORT',
    'monde':'MONDE','terre':'MONDE',
    'promettre':'PROMETTRE','promesse':'PROMETTRE',
    'vrai':'VRAI','vérité':'VRAI','vraiment':'VRAI',
}
SKIP = {
    'a','an','the','is','are','was','were','be','been','to','of','in','on',
    'at','by','for','with','that','this','it','very','just','and','or','but',
    'have','has','had','le','la','les','un','une','des','du','de','et','ou',
    'est','que','ce','se','lui','y','en','sur','avec','par',
}
TIME_GLOSSES = {'FUTURE','TOMORROW','TODAY','PAST','NOW'}
SIGN_DESC = {
    'IX-1':      {'handshape':'Index pointé','location':'Poitrine','movement':'Pointer vers soi'},
    'IX-2':      {'handshape':'Index pointé','location':'Vers interlocuteur','movement':'Pointer vers la personne'},
    'FUTURE':    {'handshape':'Main ouverte paume gauche','location':'Côté visage','movement':'Avancer la main'},
    'TOMORROW':  {'handshape':'Main-A','location':'Joue','movement':'Arc vers l\'avant'},
    'HI':        {'handshape':'Main-B ouverte','location':'Front','movement':'Agiter vers l\'extérieur'},
    'THANK':     {'handshape':'Main plate','location':'Menton','movement':'Avancer vers la personne'},
    'YES':       {'handshape':'Poing (S)','location':'Devant soi','movement':'Hocher le poing'},
    'NO':        {'handshape':'Index+Majeur tendus','location':'Devant soi','movement':'Fermer les doigts'},
    'WANT':      {'handshape':'Mains courbées paumes haut','location':'Devant soi','movement':'Tirer vers soi'},
    'LOVE':      {'handshape':'Bras croisés poings','location':'Poitrine','movement':'Croiser les bras'},
    'GOOD':      {'handshape':'Main ouverte paume haut','location':'Menton','movement':'Avancer dans l\'autre paume'},
    'EAT':       {'handshape':'Main-O plate','location':'Bouche','movement':'Toucher les doigts à la bouche'},
    # ── Laveau 1868 ──────────────────────────────────────────────────────────
    'AIMER':     {'handshape':'Deux mains plates','location':'Poitrine/cœur','movement':'Appuyer les deux mains sur le cœur (Laveau)'},
    'ALLER':     {'handshape':'Index étendus','location':'Devant soi','movement':'Avancer les deux mains, index tournant l\'un autour de l\'autre (Laveau)'},
    'ARBRE':     {'handshape':'Main droite ouverte élevée + main gauche en support','location':'Épaule droite','movement':'Élever le bras droit, main gauche sous le coude (Laveau)'},
    'BOIRE':     {'handshape':'Main droite demi-ouverte','location':'Bouche','movement':'Simuler l\'action de boire (Laveau)'},
    'BON':       {'handshape':'Deux mains ouvertes','location':'Des deux côtés','movement':'Abaisser les deux mains de chaque côté avec expression de bonté (Laveau)'},
    'CORPS':     {'handshape':'Deux mains ouvertes','location':'Haut du corps','movement':'Descendre les deux mains ouvertes jusqu\'à la poitrine (Laveau)'},
    'DESIRER':   {'handshape':'Doigts recourbés','location':'Poitrine','movement':'Ramener les deux mains vers soi depuis le cœur (Laveau)'},
    'DONNER':    {'handshape':'Main droite inclinée','location':'Devant soi','movement':'Incliner la main vers l\'avant, dessus en bas (Laveau)'},
    'EAU':       {'handshape':'Doigts séparés et étendus','location':'Devant soi','movement':'Agiter doucement les doigts séparés (Laveau)'},
    'FORT':      {'handshape':'Deux poings fermés','location':'Épaules','movement':'Fermer les deux poings à la naissance des épaules (Laveau)'},
    'MONDE':     {'handshape':'Deux bras ouverts','location':'Devant soi','movement':'Former un grand cercle avec les deux bras (Laveau)'},
    'PROMETTRE': {'handshape':'Deux index levés','location':'Devant soi','movement':'Lever les deux index côte à côte (Laveau)'},
    'VRAI':      {'handshape':'Main ouverte doigts serrés','location':'Hauteur du front','movement':'Abaisser fortement la main, paume vers le bas, vers la poitrine (Laveau)'},
}

def translate_with_slt(text, language, target_sign):
    try:
        import sign_language_translator as slt
        lang = slt.get_text_language('english')
        tokens = lang.tokenize(text)
        tags = lang.get_tags(tokens)
        time_g, main_g, seen = [], [], set()
        for token, tag in zip(tokens, tags):
            if 'PUNCTUATION' in str(tag): continue
            t = token.lower()
            if t in lang.omitted_tokens or t in SKIP or not t.strip(): continue
            g = SIGN_MAP.get(t, t.upper())
            if g in seen: continue
            seen.add(g)
            (time_g if g in TIME_GLOSSES else main_g).append(g)
        final = time_g + main_g
        grammar = 'Question' if '?' in text else 'Statement'
        notes = f'{target_sign}: marqueurs temporels en premier, articles supprimés'
        return {'glosses': final or ['NO','TRANSLATION'],'grammar_type':grammar,
                'grammar_notes':notes,'sign_descriptions':
                [{**{'gloss':g},**SIGN_DESC[g]} for g in final if g in SIGN_DESC]}
    except:
        return None

def translate_fallback(text, language):
    time_g, main_g, seen = [], [], set()
    for word in text.lower().split():
        t = word.strip('.,?!;:')
        if t in SKIP or not t: continue
        g = SIGN_MAP.get(t, t.upper())
        if g in seen: continue
        seen.add(g)
        (time_g if g in TIME_GLOSSES else main_g).append(g)
    final = time_g + main_g
    grammar = 'Question' if '?' in text else 'Statement'
    return {'glosses': final or ['NO','TRANSLATION'],'grammar_type':grammar,
            'grammar_notes':'Traduction dictionnaire','sign_descriptions':
            [{**{'gloss':g},**SIGN_DESC[g]} for g in final if g in SIGN_DESC]}

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="SignVoix">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#4f46e5">
<link rel="manifest" href="/manifest.json">
<title>SignVoix — Traducteur LSF</title>
<style>
:root{
  --brand:#4f46e5;--brand-dk:#3730a3;--accent:#7c3aed;
  --green:#059669;--red:#dc2626;--amber:#d97706;
  --bg:#f1f5f9;--card:#fff;--border:#e2e8f0;
  --text:#1e293b;--muted:#64748b;
  --r:12px;--hh:60px;
  --sh:0 1px 3px rgba(0,0,0,.08),0 4px 20px rgba(79,70,229,.07);
  --sh2:0 4px 32px rgba(79,70,229,.18),0 2px 8px rgba(0,0,0,.12);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
  background:var(--bg);color:var(--text);line-height:1.5;-webkit-font-smoothing:antialiased}

/* ── HEADER ── */
header{
  position:fixed;top:0;left:0;right:0;height:var(--hh);
  background:linear-gradient(135deg,var(--brand),var(--accent));
  display:flex;align-items:center;padding:0 1.25rem;gap:.85rem;
  z-index:100;box-shadow:0 2px 16px rgba(79,70,229,.35)
}
.brand{display:flex;align-items:center;gap:.55rem;flex:1;min-width:0}
.brand-icon{font-size:24px;line-height:1;flex-shrink:0}
.brand-name{font-size:17px;font-weight:800;color:#fff;line-height:1.1}
.brand-sub{font-size:9px;color:rgba(255,255,255,.65);letter-spacing:.06em;text-transform:uppercase}
.tabs{display:flex;gap:.3rem}
.tab-btn{
  padding:.38rem .8rem;border:1.5px solid rgba(255,255,255,.35);
  background:rgba(255,255,255,.12);color:#fff;border-radius:7px;
  cursor:pointer;font-weight:700;font-size:12px;transition:all .18s;white-space:nowrap
}
.tab-btn.active{background:#fff;color:var(--brand);border-color:#fff}
.mp-pill{
  font-size:10px;padding:.22rem .55rem;border-radius:20px;
  font-weight:700;white-space:nowrap;flex-shrink:0;transition:all .3s
}
.mp-pill.loading{background:rgba(255,255,255,.2);color:rgba(255,255,255,.9)}
.mp-pill.ready{background:#bbf7d0;color:#064e3b}
.mp-pill.error{background:#fecaca;color:#7f1d1d}

/* ── MAIN ── */
main{padding-top:calc(var(--hh) + 1.25rem);padding-bottom:1.25rem;
  max-width:1080px;margin:0 auto;padding-left:1.25rem;padding-right:1.25rem}
.pane{display:none}.pane.active{display:block}

/* ── CAMERA LAYOUT ── */
.cam-grid{display:grid;grid-template-columns:1fr 330px;gap:1.25rem;align-items:start}

/* Video card */
.vid-card{
  background:#0d1117;border-radius:var(--r);overflow:hidden;
  position:relative;aspect-ratio:4/3;box-shadow:var(--sh2)
}
#vid{width:100%;height:100%;object-fit:cover;transform:scaleX(-1);display:block}
#cvs{position:absolute;inset:0;width:100%;height:100%;transform:scaleX(-1)}
.vid-overlay{
  position:absolute;bottom:0;left:0;right:0;
  padding:.8rem 1rem;
  background:linear-gradient(transparent,rgba(0,0,0,.82));
  display:flex;align-items:flex-end;justify-content:space-between
}
.live-sign{font-size:26px;font-weight:900;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.5)}
.live-conf{font-size:11px;color:rgba(255,255,255,.6);margin-top:2px}
.hold-ring{width:42px;height:42px;flex-shrink:0}
.hold-ring svg{transform:rotate(-90deg);display:block}
.hold-ring circle{fill:none;stroke:#22c55e;stroke-width:4;
  stroke-dasharray:113;stroke-dashoffset:113;
  transition:stroke-dashoffset .08s linear;stroke-linecap:round}
.idle-overlay{
  position:absolute;inset:0;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:#0d1117;color:#fff;gap:.85rem;text-align:center;padding:2rem
}
.idle-overlay .big-icon{font-size:52px}
.idle-overlay p{font-size:13px;opacity:.55;max-width:240px;line-height:1.55}
.dbg-box{
  position:absolute;top:8px;left:8px;
  background:rgba(0,0,0,.75);color:#00ff88;
  font-family:'SF Mono',monospace;font-size:10px;
  padding:6px 9px;border-radius:7px;line-height:1.65;
  display:none;backdrop-filter:blur(3px);max-width:200px
}

/* ── CARD ── */
.card{background:var(--card);border-radius:var(--r);border:1px solid var(--border);box-shadow:var(--sh);overflow:hidden}
.card-hdr{
  padding:.6rem 1rem;font-size:10px;font-weight:800;
  text-transform:uppercase;letter-spacing:.07em;
  color:var(--muted);border-bottom:1px solid var(--border);background:#f8fafc
}

/* Detection hero card */
.detect-hero{
  background:linear-gradient(135deg,var(--brand),var(--accent));
  border-radius:var(--r);padding:1.1rem 1rem;text-align:center;
  box-shadow:var(--sh2)
}
.hero-emoji{font-size:44px;line-height:1;display:block;margin-bottom:.3rem}
.hero-sign{font-size:28px;font-weight:900;color:#fff;line-height:1.1}
.hero-en{font-size:12px;color:rgba(255,255,255,.65);margin-top:3px}
.conf-track{margin-top:.7rem;background:rgba(255,255,255,.18);border-radius:3px;height:5px;overflow:hidden}
.conf-fill{height:100%;background:#4ade80;border-radius:3px;transition:width .18s}

/* Sentence wrap */
.sent-wrap{
  min-height:72px;padding:.75rem;
  display:flex;flex-wrap:wrap;gap:.35rem;
  align-items:flex-start;align-content:flex-start
}
.sent-empty{color:#cbd5e1;font-size:12px;font-style:italic;align-self:center;width:100%;text-align:center;padding:.3rem 0}
.word-chip{
  background:linear-gradient(135deg,#ede9fe,#ddd6fe);
  color:var(--brand-dk);padding:.3rem .7rem;border-radius:999px;
  font-size:12px;font-weight:700;border:1px solid #c4b5f4;
  display:flex;align-items:center;gap:.25rem
}
.word-chip button{
  background:none;border:none;cursor:pointer;font-size:9px;
  color:#7c3aed;opacity:.55;padding:0;line-height:1;transition:opacity .15s
}
.word-chip button:hover{opacity:1}
#predBar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;min-height:28px;margin-top:8px;padding:0 2px}
#phraseSuggest{font-size:.8rem;color:#8b5cf6;font-style:italic;margin-top:3px;min-height:16px;padding:0 2px}
.pred-label{font-size:.72rem;color:#9ca3af;white-space:nowrap;margin-right:2px}
.pred-btn{background:#ede9fe;color:#5b21b6;border:1px solid #c4b5fd;border-radius:999px;
  padding:4px 12px;font-size:.78rem;cursor:pointer;transition:background .15s;white-space:nowrap}
.pred-btn:hover{background:#ddd6fe}
.pred-complete{color:#059669;font-weight:700;font-size:.82rem}

/* Buttons */
.btn{
  display:inline-flex;align-items:center;justify-content:center;gap:.35rem;
  padding:.6rem .85rem;border:none;border-radius:8px;
  cursor:pointer;font-size:12px;font-weight:700;transition:all .15s
}
.btn-primary{background:var(--brand);color:#fff}
.btn-primary:hover{background:var(--brand-dk);transform:translateY(-1px)}
.btn-stop{background:#fee2e2;color:var(--red);border:1px solid #fca5a5}
.btn-stop:hover{background:var(--red);color:#fff}
.btn-ghost{background:#f8f9fb;color:var(--muted);border:1px solid var(--border)}
.btn-ghost:hover{background:#ede9fe;color:var(--brand);border-color:#c4b5f4}
.btn-speak{background:linear-gradient(135deg,#ecfdf5,#d1fae5);color:#065f46;border:1px solid #6ee7b7}
.btn-speak:hover{background:var(--green);color:#fff;border-color:var(--green)}
.btn-block{width:100%}
.cam-btns{display:flex;gap:.55rem;padding:.75rem}
.cam-extra{padding:0 .75rem .75rem}

/* Signs ref mini-grid */
.ref-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.3rem;padding:.6rem}
.ref-item{
  background:#faf8ff;border:1px solid #e4dcf8;border-radius:7px;
  padding:.4rem .2rem;text-align:center;cursor:default;transition:background .15s;position:relative
}
.ref-item:hover{background:#ede9fe}
.ref-item.bi{background:#f0fff4;border-color:#bbf7d0}
.ref-item.bi:hover{background:#d1fae5}
.ref-emoji{font-size:18px;display:block}
.ref-label{font-size:8.5px;font-weight:700;color:var(--brand);line-height:1.3;margin-top:2px;display:block}
.bi-badge{
  position:absolute;top:2px;right:2px;
  background:var(--green);color:#fff;font-size:6px;font-weight:800;
  padding:0 3px;border-radius:3px;line-height:1.6;letter-spacing:.02em
}
/* ── LEARN SERVICE ── */
.btn-learn{background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;border:none;margin-top:.45rem}
.btn-learn:hover{filter:brightness(1.08)}
.learn-body{padding:.75rem 1rem;display:flex;flex-direction:column;gap:.65rem}
.fp-display-wrap{background:#f8fafc;border-radius:8px;padding:.55rem .75rem;border:1px solid var(--border)}
.fp-label-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:.4rem}
.fp-label{font-size:10px;font-weight:800;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.btn-recap{background:none;border:1.5px solid var(--border);border-radius:6px;padding:2px 8px;font-size:11px;cursor:pointer;font-weight:700;color:var(--muted)}
.btn-recap:hover{background:#f1f5f9;color:var(--text)}
.fp-display{display:flex;gap:.4rem;flex-wrap:wrap;align-items:center}
.fp-finger{display:flex;flex-direction:column;align-items:center;gap:2px;min-width:38px}
.fp-finger .fp-icon{font-size:20px;line-height:1}
.fp-finger .fp-name{font-size:8px;font-weight:800;color:var(--muted);letter-spacing:.04em}
.fp-finger.up .fp-icon{color:#059669}
.fp-finger.down .fp-icon{color:#cbd5e1}
.fp-tag{font-size:10px;background:#e0e7ff;color:var(--brand);border-radius:5px;padding:1px 7px;font-weight:700}
.learn-fields{display:flex;flex-direction:column;gap:.45rem}
.learn-label{font-size:10px;font-weight:700;color:var(--muted);display:block;margin-bottom:1px}
.learn-input{
  width:100%;padding:.45rem .65rem;border:1.5px solid var(--border);border-radius:7px;
  font:inherit;font-size:13px;outline:none;transition:border-color .15s
}
.learn-input:focus{border-color:var(--brand)}
.learn-row{display:flex;gap:.5rem}
.learn-actions{display:flex;gap:.5rem}
.ref-item.custom{background:#fff7ed;border-color:#fed7aa}
.ref-item.custom:hover{background:#fff0da}
.custom-badge{
  position:absolute;top:2px;left:2px;
  background:var(--amber);color:#fff;font-size:6px;font-weight:800;
  padding:0 3px;border-radius:3px;line-height:1.6
}
.ref-del{
  position:absolute;top:2px;right:2px;
  background:#fecaca;color:#dc2626;border:none;border-radius:3px;
  font-size:8px;padding:0 3px;cursor:pointer;line-height:1.6;font-weight:800
}
.ref-del:hover{background:#dc2626;color:#fff}
.learned-hdr{
  padding:.4rem .75rem;font-size:10px;font-weight:800;
  text-transform:uppercase;letter-spacing:.07em;
  color:#92400e;border-top:1px solid #fed7aa;background:#fff7ed
}

/* ── TEXT PANE ── */
.text-card{padding:1.25rem}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-bottom:.85rem}
.fl{display:block;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:.35rem}
select,textarea{
  width:100%;padding:.6rem .8rem;border:1.5px solid var(--border);border-radius:8px;
  font:inherit;font-size:14px;background:#fff;color:var(--text);
  transition:border-color .2s,box-shadow .2s;outline:none;-webkit-appearance:none
}
select:focus,textarea:focus{border-color:var(--brand);box-shadow:0 0 0 3px rgba(79,70,229,.1)}
textarea{resize:vertical;min-height:100px;grid-column:1/-1}
.tr-btn{
  width:100%;padding:.8rem;
  background:linear-gradient(135deg,var(--brand),var(--accent));
  color:#fff;border:none;border-radius:8px;
  font-size:15px;font-weight:800;cursor:pointer;
  display:flex;align-items:center;justify-content:center;gap:.5rem;
  transition:all .2s
}
.tr-btn:hover:not(:disabled){filter:brightness(1.07);transform:translateY(-1px);box-shadow:0 4px 16px rgba(79,70,229,.28)}
.tr-btn:disabled{opacity:.6;cursor:not-allowed;transform:none}
.spin{width:15px;height:15px;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;border-radius:50%;animation:_spin .6s linear infinite;display:inline-block;vertical-align:middle}
@keyframes _spin{to{transform:rotate(360deg)}}
.sec-hdr{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:.6rem}
.result-block{border-top:1px solid var(--border);margin-top:1.1rem;padding-top:1.1rem}
.gloss-row{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center;margin-bottom:.6rem}
.gtag{
  background:linear-gradient(135deg,var(--brand),var(--accent));color:#fff;
  padding:.35rem .8rem;border-radius:999px;font-size:12px;font-weight:700;
  border:none;cursor:pointer;transition:all .15s
}
.gtag:hover{filter:brightness(1.1);transform:translateY(-1px)}
.gtag.sel{box-shadow:0 0 0 3px rgba(79,70,229,.28)}
.garrow{color:#cbd5e1;font-size:12px}
.sign-card{
  background:linear-gradient(135deg,#f8f6ff,#ede8ff);border:1px solid #d4caf0;
  border-radius:10px;padding:.9rem;margin-bottom:.75rem;display:none
}
.sign-card.active{display:block}
.sign-card h4{color:var(--brand);font-size:14px;margin-bottom:.6rem}
.sprops{display:grid;grid-template-columns:repeat(3,1fr);gap:.45rem}
.sp{background:#fff;border-radius:7px;padding:.55rem;border:1px solid #e4dcf8}
.spl{font-size:9px;font-weight:800;text-transform:uppercase;color:#bbb;margin-bottom:2px}
.spv{font-size:11px;color:#333;line-height:1.4}
.gram-box{background:#f9f9fb;border-radius:9px;padding:.8rem .95rem;border:1px solid #eee;margin-bottom:.7rem}
.gram-row{display:flex;gap:.65rem;margin-bottom:.3rem}.gram-row:last-child{margin:0}
.gl{font-size:10px;font-weight:700;color:#bbb;width:55px;flex-shrink:0;text-transform:uppercase;margin-top:2px}
.gv{font-size:12px;color:#333;line-height:1.5}
.badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700}
.badge-s{background:#e6f4ea;color:#1e6b2e}.badge-q{background:#fff3e0;color:#c45700}
.mets{display:grid;grid-template-columns:repeat(4,1fr);gap:.55rem}
.met{background:#f9f9fb;border-radius:9px;padding:.7rem;text-align:center;border:1px solid #eee}
.mv{font-size:20px;font-weight:800;color:var(--brand)}.ml{font-size:9px;color:#aaa;margin-top:2px;text-transform:uppercase;font-weight:700}

/* ── LOG PANEL ── */
.log-panel{background:var(--card);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--sh);overflow:hidden}
.log-toggle{display:flex;align-items:center;justify-content:space-between;padding:.6rem 1rem;cursor:pointer;user-select:none;background:#f8fafc}
.log-toggle:hover{background:#f1f5f9}
.log-title{font-size:11px;font-weight:700;color:var(--muted);display:flex;align-items:center;gap:.4rem}
.log-cnt{background:#e0e7ff;color:var(--brand);font-size:9px;padding:1px 5px;border-radius:7px;font-weight:800}
.log-icon{font-size:11px;color:#94a3b8;transition:transform .2s}
.log-icon.open{transform:rotate(180deg)}
.log-body{display:none;background:#0f172a;max-height:240px;overflow-y:auto;padding:.5rem .7rem}
.log-body.open{display:block}
.log-line{font-family:'SF Mono','Fira Code',monospace;font-size:9.5px;line-height:1.75;padding:1px 0;border-bottom:1px solid rgba(255,255,255,.03)}
.log-line .ts{color:#475569}
.log-line .lv{font-weight:800;margin:0 .4rem;display:inline-block;min-width:32px;font-size:9px}
.log-line.info .lv{color:#60a5fa}.log-line.ok .lv{color:#34d399}
.log-line.warn .lv{color:#fbbf24}.log-line.err .lv{color:#f87171}
.log-line .msg{color:#e2e8f0}
.log-acts{display:none;padding:.45rem .7rem;gap:.45rem;border-top:1px solid rgba(255,255,255,.05);background:#0f172a}
.log-acts.open{display:flex}
.log-abtn{flex:1;padding:.3rem;border:1px solid #1e293b;border-radius:5px;background:#1e293b;color:#94a3b8;font-size:10px;font-weight:700;cursor:pointer;transition:all .15s}
.log-abtn:hover{background:#334155;color:#e2e8f0}

/* ── SIDE STACK ── */
.side-stack{display:flex;flex-direction:column;gap:1rem}

/* ── DIALOGUE (bidirectionnel) ── */
.talk-wrap{max-width:640px;margin:0 auto;display:flex;flex-direction:column;gap:1rem}
.status-bar{display:flex;align-items:center;gap:.6rem;background:var(--card);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--sh);padding:.7rem .9rem}
.status-chip{flex:1;display:flex;flex-direction:column;gap:2px;cursor:pointer;padding:.35rem .5rem;border-radius:9px;transition:background .15s}
.status-chip:hover{background:#f1f5f9}
.sc-label{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.sc-val{font-size:14px;font-weight:800;color:var(--brand);display:flex;align-items:center;gap:.35rem}
.status-swap{font-size:18px;color:#cbd5e1;flex-shrink:0}
.btn-status-edit{flex-shrink:0;width:34px;height:34px;border:1px solid var(--border);border-radius:9px;background:var(--card);cursor:pointer;font-size:15px;color:var(--muted);transition:all .15s}
.btn-status-edit:hover{background:#e0e7ff;color:var(--brand)}
.mode-hint{font-size:11px;color:var(--muted);text-align:center;padding:.2rem;line-height:1.5}
.mode-hint strong{color:var(--brand)}

.listen-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--sh);padding:1rem;display:flex;flex-direction:column;gap:.85rem;align-items:center}
.listen-live{width:100%;min-height:64px;background:#f8fafc;border:1.5px dashed var(--border);border-radius:10px;padding:.8rem 1rem;font-size:18px;line-height:1.45;color:var(--text);text-align:center;display:flex;align-items:center;justify-content:center}
.listen-live.listening{border-color:var(--brand);border-style:solid;background:#eef2ff}
.listen-live .interim{color:var(--muted);font-style:italic}
.mic-btn{display:flex;align-items:center;gap:.55rem;padding:.85rem 1.7rem;border:none;border-radius:999px;background:linear-gradient(135deg,var(--brand),var(--accent));color:#fff;font-size:16px;font-weight:800;cursor:pointer;box-shadow:0 4px 16px rgba(79,70,229,.3);transition:all .18s;min-height:52px}
.mic-btn:hover{filter:brightness(1.07);transform:translateY(-1px)}
.mic-btn.active{background:linear-gradient(135deg,var(--red),#b91c1c);box-shadow:0 4px 16px rgba(220,38,38,.35);animation:_pulse 1.3s ease-in-out infinite}
@keyframes _pulse{0%,100%{box-shadow:0 4px 16px rgba(220,38,38,.35)}50%{box-shadow:0 4px 26px rgba(220,38,38,.6)}}
.mic-btn:disabled{opacity:.55;cursor:not-allowed;filter:grayscale(.5)}
.listen-manual{width:100%;display:flex;gap:.5rem}
.listen-manual input{flex:1;padding:.6rem .75rem;border:1px solid var(--border);border-radius:9px;font-size:14px}
.listen-manual button{padding:.6rem 1rem;border:none;border-radius:9px;background:var(--brand);color:#fff;font-weight:700;cursor:pointer;font-size:13px}

.conv-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--sh);overflow:hidden;display:flex;flex-direction:column}
.conv-hdr{display:flex;align-items:center;justify-content:space-between;padding:.7rem 1rem;background:#f8fafc;border-bottom:1px solid var(--border);font-size:12px;font-weight:800;color:var(--muted)}
.conv-hdr button{border:1px solid var(--border);background:var(--card);border-radius:7px;padding:.25rem .55rem;cursor:pointer;font-size:12px;color:var(--muted)}
.conv-hdr button:hover{background:#fee2e2;color:var(--red)}
.conv-body{max-height:340px;overflow-y:auto;padding:.85rem;display:flex;flex-direction:column;gap:.6rem}
.conv-empty{text-align:center;color:#cbd5e1;font-size:13px;padding:2rem 1rem}
.bubble{max-width:82%;padding:.6rem .85rem;border-radius:13px;font-size:15px;line-height:1.4;position:relative;word-break:break-word}
.bubble .bmeta{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;opacity:.7;margin-bottom:3px;display:flex;align-items:center;gap:.3rem}
.bubble.me{align-self:flex-end;background:linear-gradient(135deg,var(--brand),var(--accent));color:#fff;border-bottom-right-radius:4px}
.bubble.other{align-self:flex-start;background:#f1f5f9;color:var(--text);border-bottom-left-radius:4px}
.bubble .breplay{margin-left:.4rem;cursor:pointer;opacity:.75}
.bubble .breplay:hover{opacity:1}

/* ── MODAL ── */
.modal-overlay{position:fixed;inset:0;background:rgba(15,23,42,.55);backdrop-filter:blur(3px);z-index:200;display:flex;align-items:center;justify-content:center;padding:1.25rem}
.modal-card{background:var(--card);border-radius:16px;box-shadow:var(--sh2);padding:1.5rem;max-width:440px;width:100%;max-height:90vh;overflow-y:auto}
.modal-card h3{font-size:17px;font-weight:800;color:var(--text);margin-bottom:.4rem}
.modal-card .mc-sub{font-size:12px;color:var(--muted);margin-bottom:1.1rem;line-height:1.5}
.status-group{margin-bottom:1.1rem}
.status-group>label{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);display:block;margin-bottom:.5rem}
.status-opts{display:grid;grid-template-columns:1fr 1fr;gap:.5rem}
.status-opt{display:flex;flex-direction:column;align-items:center;gap:.25rem;padding:.7rem .5rem;border:2px solid var(--border);border-radius:11px;cursor:pointer;transition:all .15s;text-align:center;background:var(--card)}
.status-opt:hover{border-color:#c7d2fe;background:#f8fafc}
.status-opt.sel{border-color:var(--brand);background:#eef2ff}
.status-opt .so-icon{font-size:22px;line-height:1}
.status-opt .so-name{font-size:13px;font-weight:800;color:var(--text)}
.status-opt .so-desc{font-size:9.5px;color:var(--muted);line-height:1.3}
.modal-card .btn-primary{width:100%;margin-top:.3rem}

/* ── RESPONSIVE ── */
@media(max-width:720px){
  :root{--hh:54px}
  main{padding-left:.75rem;padding-right:.75rem}
  .cam-grid{grid-template-columns:1fr}
  .ref-grid{grid-template-columns:repeat(5,1fr)}
  .mets{grid-template-columns:repeat(2,1fr)}
  .sprops{grid-template-columns:1fr}
  .form-grid{grid-template-columns:1fr}
  .brand-sub{display:none}
  .status-opts{grid-template-columns:1fr}
}
@media(max-width:460px){
  .tlab{display:none}                 /* onglets en icônes seules pour éviter le débordement */
  .tab-btn{padding:.38rem .55rem;font-size:15px}
  header{gap:.5rem;padding:0 .85rem}
}
</style>
</head>
<body>

<!-- ══ HEADER ══════════════════════════════════════════════════ -->
<header>
  <div class="brand">
    <span class="brand-icon">🤟</span>
    <div>
      <div class="brand-name">SignVoix</div>
      <div class="brand-sub">Traducteur LSF temps réel</div>
    </div>
  </div>
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('cam',this)">📷<span class="tlab"> Caméra</span></button>
    <button class="tab-btn"        onclick="switchTab('talk',this)">💬<span class="tlab"> Dialogue</span></button>
    <button class="tab-btn"        onclick="switchTab('text',this)">📝<span class="tlab"> Texte</span></button>
  </div>
  <div class="mp-pill loading" id="mpPill">⏳ …</div>
</header>

<main>

<!-- ══ CAMERA PANE ═══════════════════════════════════════════ -->
<div id="pane-cam" class="pane active">
  <div class="cam-grid">

    <!-- Left: video -->
    <div>
      <div class="vid-card" id="vidCard">
        <video id="vid" autoplay muted playsinline></video>
        <canvas id="cvs"></canvas>
        <div class="dbg-box" id="dbgBox"></div>

        <!-- Idle overlay (hidden when cam is running) -->
        <div class="idle-overlay" id="idleOverlay">
          <span class="big-icon">📷</span>
          <p>Appuyez sur <strong>Démarrer</strong> pour activer la caméra et détecter vos signes LSF en temps réel</p>
        </div>

        <!-- Live overlay (visible when cam is running) -->
        <div class="vid-overlay" id="vidOverlay" style="display:none">
          <div>
            <div class="live-sign" id="liveSign">—</div>
            <div class="live-conf" id="liveConf"></div>
          </div>
          <div class="hold-ring" id="holdRing" style="display:none">
            <svg width="42" height="42" viewBox="0 0 42 42">
              <circle cx="21" cy="21" r="18" id="holdCircle"/>
            </svg>
          </div>
        </div>
      </div>

      <div style="display:flex;align-items:center;justify-content:space-between;margin-top:.5rem;padding:0 .1rem">
        <p style="font-size:11px;color:#94a3b8">💡 Maintenez un signe <strong>1 s</strong> pour l'ajouter à la phrase</p>
        <button onclick="toggleDebug()" style="font-size:10px;padding:2px 8px;border:1px solid var(--border);border-radius:6px;background:var(--card);cursor:pointer;color:var(--muted)">🔬 Debug</button>
      </div>
    </div>

    <!-- Right: panel stack -->
    <div class="side-stack">

      <!-- Detected sign hero -->
      <div class="detect-hero" id="detectHero">
        <span class="hero-emoji" id="heroEmoji">🤷</span>
        <div class="hero-sign" id="heroSign">En attente…</div>
        <div class="hero-en"   id="heroEn">Activez la caméra</div>
        <div class="conf-track"><div class="conf-fill" id="confFill" style="width:0%"></div></div>
      </div>

      <!-- Camera controls -->
      <div class="card">
        <div class="cam-btns">
          <button class="btn btn-primary" id="btnStart" onclick="startCam()" style="flex:1">▶ Démarrer</button>
          <button class="btn btn-stop"    id="btnStop"  onclick="stopCam()"  style="flex:1;display:none">■ Arrêter</button>
          <button class="btn btn-ghost"   onclick="clearSentence()">✕</button>
        </div>
        <div class="cam-extra">
          <button class="btn btn-speak btn-block" onclick="speakSentence()">🔊 Lire la phrase à voix haute</button>
          <button class="btn btn-learn btn-block" id="btnLearn" onclick="captureSign()" style="display:none">📚 Apprendre ce signe</button>
        </div>
      </div>

      <!-- Learn panel — shown when capturing a new sign -->
      <div class="card" id="learnPanel" style="display:none">
        <div class="card-hdr">📚 Apprendre un nouveau signe</div>
        <div class="learn-body">
          <div class="fp-display-wrap">
            <div class="fp-label-row">
              <span class="fp-label">Position des doigts capturée :</span>
              <button class="btn-recap" onclick="refreshCapture()">📸 Re-capturer</button>
            </div>
            <div class="fp-display" id="fpDisplay"></div>
          </div>
          <div class="learn-fields">
            <label class="learn-label">Nom français *</label>
            <input id="learnFr" type="text" placeholder="ex : Bonjour, Merci, Manger…" class="learn-input" autocomplete="off">
            <div class="learn-row">
              <div style="flex:0 0 76px">
                <label class="learn-label">Emoji</label>
                <input id="learnEmoji" type="text" placeholder="✋" class="learn-input" maxlength="4" style="text-align:center;font-size:16px">
              </div>
              <div style="flex:1">
                <label class="learn-label">Anglais (optionnel)</label>
                <input id="learnEn" type="text" placeholder="ex : Hello" class="learn-input">
              </div>
            </div>
          </div>
          <div class="learn-actions">
            <button class="btn btn-primary" onclick="saveLearnedSign()" style="flex:1">💾 Sauvegarder</button>
            <button class="btn btn-ghost" onclick="cancelLearn()" title="Annuler">✕</button>
          </div>
        </div>
      </div>

      <!-- Sentence builder -->
      <div class="card">
        <div class="card-hdr">Phrase construite</div>
        <div class="sent-wrap" id="sentWrap">
          <span class="sent-empty" id="sentEmpty">Les signes reconnus apparaîtront ici…</span>
        </div>
        <div id="phraseSuggest"></div>
        <div id="predBar"></div>
      </div>

      <!-- Signs reference -->
      <div class="card">
        <div class="card-hdr">Signes disponibles (LSF)</div>
        <div class="ref-grid" id="refGrid"></div>
        <div id="learnedSignsSec" style="display:none">
          <div class="learned-hdr">✎ Mes signes appris</div>
          <div class="ref-grid" id="learnedRefGrid"></div>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- ══ DIALOGUE PANE (bidirectionnel) ════════════════════════ -->
<div id="pane-talk" class="pane">
  <div class="talk-wrap">

    <!-- Statuts des interlocuteurs -->
    <div class="status-bar" id="statusBar">
      <div class="status-chip" onclick="openStatusModal()">
        <span class="sc-label">Moi</span>
        <span class="sc-val" id="scMe">👂 Entendant</span>
      </div>
      <span class="status-swap">⇄</span>
      <div class="status-chip" onclick="openStatusModal()">
        <span class="sc-label">L'autre personne</span>
        <span class="sc-val" id="scOther">👂 Entendant</span>
      </div>
      <button class="btn-status-edit" onclick="openStatusModal()" title="Changer les statuts">⚙</button>
    </div>
    <div class="mode-hint" id="modeHint"></div>

    <!-- Reconnaissance vocale : la personne entendante parle → texte -->
    <div class="listen-card" id="listenCard">
      <div class="listen-live" id="listenLive">Appuyez sur le micro puis parlez — le texte s'affichera ici.</div>
      <button class="mic-btn" id="micBtn" onclick="toggleListen()">
        <span id="micIcon">🎙️</span><span id="micLabel">Écouter</span>
      </button>
      <div class="listen-manual" id="listenManual" style="display:none">
        <input id="manualText" type="text" placeholder="Ou tapez le message ici…" onkeydown="if(event.key==='Enter')sendManual()">
        <button onclick="sendManual()">Envoyer</button>
      </div>
    </div>

    <!-- Historique de conversation -->
    <div class="conv-card">
      <div class="conv-hdr">
        <span>💬 Conversation</span>
        <button onclick="clearConversation()" title="Effacer la conversation">🗑 Effacer</button>
      </div>
      <div class="conv-body" id="convBody">
        <div class="conv-empty" id="convEmpty">La conversation apparaîtra ici — signes reconnus et paroles transcrites.</div>
      </div>
    </div>

  </div>
</div>

<!-- ══ TEXT PANE ════════════════════════════════════════════ -->
<div id="pane-text" class="pane">
  <div class="card text-card">
    <div class="form-grid">
      <div><label class="fl">Langue source</label>
        <select id="srcLang"><option value="french">Français</option><option value="english">English</option></select></div>
      <div><label class="fl">Langue des signes</label>
        <select id="tgtSign"><option value="LSF">LSF — Française</option><option value="ASL">ASL — Américaine</option><option value="BSL">BSL — Britannique</option></select></div>
      <div style="grid-column:1/-1"><label class="fl">Texte à traduire</label>
        <textarea id="inputText" placeholder="Ex : Je vais manger une pomme demain. Bonjour, comment vas-tu ?"></textarea></div>
    </div>
    <div style="display:flex;gap:.55rem">
      <button class="tr-btn" id="btnTr" onclick="doTranslate()">🔤 Traduire en LSF</button>
      <button class="btn btn-ghost" style="flex:.22;min-width:44px" onclick="clearText()">✕</button>
    </div>

    <div id="textResult" style="display:none">
      <div class="result-block">
        <div class="sec-hdr">Glosses LSF</div>
        <div class="gloss-row" id="glossRow"></div>
        <p style="font-size:11px;color:#94a3b8;margin-top:.2rem">👆 Cliquez un gloss pour voir comment faire le signe</p>
      </div>
      <div class="sign-card" id="signCard">
        <h4 id="scGloss"></h4>
        <div class="sprops" id="scProps"></div>
      </div>
      <div class="result-block">
        <div class="sec-hdr">Grammaire</div>
        <div class="gram-box">
          <div class="gram-row"><span class="gl">Type</span><span class="gv" id="gType"></span></div>
          <div class="gram-row"><span class="gl">Notes</span><span class="gv" id="gNotes"></span></div>
        </div>
      </div>
      <div class="result-block">
        <div class="sec-hdr">Statistiques</div>
        <div class="mets">
          <div class="met"><div class="mv" id="mG">—</div><div class="ml">Glosses</div></div>
          <div class="met"><div class="mv" id="mW">—</div><div class="ml">Mots</div></div>
          <div class="met"><div class="mv" id="mC">—</div><div class="ml">Confiance</div></div>
          <div class="met"><div class="mv" id="mT">—</div><div class="ml">Temps ms</div></div>
        </div>
      </div>
    </div>
  </div>
</div>

</main>

<!-- ══ STATUS MODAL ═════════════════════════════════════════ -->
<div class="modal-overlay" id="statusModal" style="display:none">
  <div class="modal-card">
    <h3>👥 Qui communique ?</h3>
    <p class="mc-sub">Choisissez votre situation et celle de la personne en face. L'interface s'adaptera automatiquement.</p>
    <div class="status-group">
      <label>Je suis…</label>
      <div class="status-opts" id="meOpts"></div>
    </div>
    <div class="status-group">
      <label>L'autre personne est…</label>
      <div class="status-opts" id="otherOpts"></div>
    </div>
    <button class="btn btn-primary" onclick="saveStatus()">✓ Valider</button>
  </div>
</div>

<!-- ══ LOG PANEL ════════════════════════════════════════════ -->
<div style="max-width:1080px;margin:0 auto;padding:0 1.25rem 1.5rem">
  <div class="log-panel">
    <div class="log-toggle" onclick="toggleLog()">
      <span class="log-title">📋 Journal de diagnostic <span class="log-cnt" id="logCnt">0</span></span>
      <span class="log-icon" id="logIcon">▼</span>
    </div>
    <div class="log-body" id="logBody"></div>
    <div class="log-acts" id="logActs">
      <button class="log-abtn" onclick="copyLogs()">📋 Copier tout</button>
      <button class="log-abtn" onclick="clearLogs()">🗑 Effacer</button>
    </div>
  </div>
</div>

<script>
/* ── TABS ──────────────────────────────────────────────── */
function switchTab(name, btn) {
  document.querySelectorAll('.pane').forEach(function(p) { p.classList.remove('active'); });
  document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
  document.getElementById('pane-' + name).classList.add('active');
  btn.classList.add('active');
  // Première ouverture du Dialogue sans statut configuré → propose la config
  if (name === 'talk' && !localStorage.getItem('lsf_status')) {
    setTimeout(openStatusModal, 250);
  }
}

/* ── LOG SYSTEM ────────────────────────────────────────── */
var _logs = [], _logOpen = false, _logN = 0;
var _LV = { info:'INFO', ok:'OK  ', warn:'WARN', err:'ERR ' };

function appLog(type, msg) {
  var t = new Date().toTimeString().substring(0, 8);
  _logs.push({ t: t, type: type, msg: msg });
  if (_logs.length > 300) _logs.shift();
  _logN++;
  document.getElementById('logCnt').textContent = _logN > 99 ? '99+' : _logN;
  var div = document.createElement('div');
  div.className = 'log-line ' + (type || 'info');
  div.innerHTML = '<span class="ts">' + t + '</span>'
    + '<span class="lv">' + (_LV[type] || 'INFO') + '</span>'
    + '<span class="msg">' + _esc(msg) + '</span>';
  var body = document.getElementById('logBody');
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
  console.log('[' + (type || 'info').toUpperCase() + ']', msg);
}
function _esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function toggleLog() {
  _logOpen = !_logOpen;
  document.getElementById('logBody').classList.toggle('open', _logOpen);
  document.getElementById('logActs').classList.toggle('open', _logOpen);
  var icon = document.getElementById('logIcon');
  icon.textContent = _logOpen ? '▲' : '▼';
  icon.classList.toggle('open', _logOpen);
}
function copyLogs() {
  var txt = _logs.map(function(l) {
    return '[' + l.t + '] [' + (l.type||'info').toUpperCase() + '] ' + l.msg;
  }).join('\n');
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(txt)
      .then(function() { appLog('ok', 'Logs copiés dans le presse-papiers (' + _logs.length + ' entrées)'); });
  } else {
    prompt('Copiez ces logs :', txt);
  }
}
function clearLogs() {
  _logs = []; _logN = 0;
  document.getElementById('logBody').innerHTML = '';
  document.getElementById('logCnt').textContent = '0';
}

// WASM patch state
var _blobUrls = [], _wasmAborted = false, _onerrorCount = 0;

async function _fetchAndPatchJs(url) {
  var fname = url.split('/').pop();
  appLog('info', 'Patch WASM: téléchargement ' + fname + '…');
  var resp = await fetch(url, { mode: 'cors', cache: 'no-cache' });
  if (!resp.ok) throw new Error('HTTP ' + resp.status + ' — ' + fname);
  var text = await resp.text();
  // Patch 1: assert(!Object.getOwnPropertyDescriptor(Module,"arguments"),...)
  var p1 = text.replace(
    /Object\.getOwnPropertyDescriptor\(Module,\s*["'`]arguments["'`]\)/g, 'false'
  );
  // Patch 2: defineProperty getter abort("Module.arguments has been replaced...")
  // Handles double-quotes, single-quotes, and backtick template literals; also
  // matches when 'abort' was renamed to a single letter by the minifier.
  var p2 = p1.replace(
    /\b\w+\s*\(\s*["'`]Module\.arguments has been replaced[^"'`]*["'`]\s*\)/g, '(0)'
  );
  var nPatches = (p1 !== text ? 1 : 0) + (p2 !== p1 ? 1 : 0);
  appLog(nPatches > 0 ? 'ok' : 'warn',
    'Patch ' + fname + ': ' + (nPatches > 0 ? nPatches + ' assertion(s) WASM neutralisée(s) ✓' : 'patterns absents (fichiers CDN non patchables — risque de crash WASM)'));
  var blobUrl = URL.createObjectURL(new Blob([p2], {type: 'application/javascript'}));
  _blobUrls.push(blobUrl);
  return blobUrl;
}

function _revokeBlobUrls() {
  _blobUrls.forEach(function(u) { URL.revokeObjectURL(u); });
  _blobUrls = [];
}

// Global error capture — flood-limited, WASM abort detector
window.onerror = function(msg, src, line) {
  _onerrorCount++;
  if (_onerrorCount <= 10) {
    appLog('err', 'JS Exception: ' + msg + ' — ' + (src || '?') + ':' + line);
  } else if (_onerrorCount === 11) {
    appLog('err', 'Flood d\'erreurs détecté — logs JS supprimés (voir console navigateur)');
  }
  if (msg && msg.indexOf('Module.arguments') !== -1 && !_wasmAborted) {
    _wasmAborted = true;
    appLog('err', '⚠ WASM abandonné (Module.arguments) — arrêt automatique. Rechargez la page.');
    setTimeout(function() { if (running) stopCam(); }, 100);
  }
  return false;
};
window.addEventListener('unhandledrejection', function(e) {
  var reason = e.reason && e.reason.message ? e.reason.message : String(e.reason);
  _onerrorCount++;
  if (_onerrorCount <= 10) {
    appLog('err', 'Promise rejetée: ' + reason);
  }
  if (reason && reason.indexOf('Module.arguments') !== -1 && !_wasmAborted) {
    _wasmAborted = true;
    appLog('err', '⚠ WASM abandonné (Module.arguments) — arrêt automatique. Rechargez la page.');
    setTimeout(function() { if (running) stopCam(); }, 100);
  }
});

document.addEventListener('DOMContentLoaded', function() {
  appLog('info', 'App initialisée');
  appLog('info', 'Navigateur: ' + navigator.userAgent.substring(0, 120));
  var ua = navigator.userAgent;
  var ios = /iP(hone|ad|od)/.test(ua);
  var android = /Android/.test(ua);
  appLog('info', 'Plateforme: ' + (ios ? 'iOS' : android ? 'Android' : 'Desktop') + ' | RAM: ' + (navigator.deviceMemory || '?') + ' GB');
  _loadLearnedSigns();
  buildRefGrid();
  _bgPreload().catch(function() {}); // Précharge MediaPipe en arrière-plan (rejet géré au clic)
  // Dialogue bidirectionnel
  _loadStatus();
  _loadConv();
  _applyStatusUI();
  _renderConvAll();
  _initSR();
  _registerSW();
});

/* ── LEARNING SERVICE ────────────────────────────────── */
function _loadLearnedSigns() {
  try {
    var raw = localStorage.getItem('lsf_learned_signs');
    if (raw) { LEARNED_SIGNS = JSON.parse(raw); }
  } catch(e) { LEARNED_SIGNS = []; }
}

function _saveLearnedSigns() {
  try { localStorage.setItem('lsf_learned_signs', JSON.stringify(LEARNED_SIGNS)); } catch(e) {}
}

function _updateFingerDisplay(f) {
  var dp = document.getElementById('fpDisplay');
  if (!dp || !f) return;
  var fingers = [
    { name:'Pouce', abbr:'P',  val: f.thumb  },
    { name:'Index', abbr:'I',  val: f.index  },
    { name:'Maj.',  abbr:'M',  val: f.middle },
    { name:'Ann.',  abbr:'A',  val: f.ring   },
    { name:'Aur.',  abbr:'Au', val: f.pinky  },
  ];
  var html = '';
  fingers.forEach(function(fi) {
    html += '<div class="fp-finger ' + (fi.val ? 'up' : 'down') + '" title="' + fi.name + '">'
          + '<span class="fp-icon">' + (fi.val ? '☝️' : '✊') + '</span>'
          + '<span class="fp-name">' + fi.abbr + '</span></div>';
  });
  if (f.thumbUp)   html += '<span class="fp-tag">👍 haut</span>';
  if (f.thumbDown) html += '<span class="fp-tag">👎 bas</span>';
  dp.innerHTML = html;
}

function captureSign() {
  if (!running) { appLog('warn', 'Démarrez la caméra avant d\'apprendre un signe'); return; }
  if (!_lastFingers) { appLog('warn', '⚠ Aucune main détectée — montrez votre signe à la caméra'); return; }
  _capturedFingers = Object.assign({}, _lastFingers);
  document.getElementById('learnPanel').style.display = 'block';
  _updateFingerDisplay(_capturedFingers);
  if (_lastSign && _lastSign.emoji) document.getElementById('learnEmoji').value = _lastSign.emoji;
  document.getElementById('learnFr').value = '';
  document.getElementById('learnEn').value = '';
  document.getElementById('learnFr').focus();
  appLog('info', '📸 Geste capturé — entrez son nom puis sauvegardez');
}

function refreshCapture() {
  if (!_lastFingers) { appLog('warn', 'Aucune main détectée'); return; }
  _capturedFingers = Object.assign({}, _lastFingers);
  _updateFingerDisplay(_capturedFingers);
  appLog('info', '📸 Geste re-capturé');
}

function saveLearnedSign() {
  var fr = document.getElementById('learnFr').value.trim();
  if (!fr) { document.getElementById('learnFr').focus(); return; }
  var emoji = document.getElementById('learnEmoji').value.trim() || '✋';
  var en    = document.getElementById('learnEn').value.trim()    || fr;
  var key   = fr.toUpperCase().replace(/[\s\-]/g,'_').replace(/[^A-Z0-9_ÀÂÇÉÈÊËÎÏÔÙÛÜŸ]/gi,'').substring(0,24);
  if (!key) key = 'SIGNE_' + Date.now();
  var f = _capturedFingers;
  var sign = {
    key: key, emoji: emoji, fr: fr, en: en,
    desc: 'Signe appris : ' + fr,
    p: {
      thumb:  f.thumb,  index:  f.index,  middle: f.middle,
      ring:   f.ring,   pinky:  f.pinky,
      dir:    f.thumbUp ? 'up' : (f.thumbDown ? 'down' : null)
    },
    learned: true, timestamp: Date.now()
  };
  var idx = LEARNED_SIGNS.findIndex(function(s) { return s.key === key; });
  if (idx >= 0) { LEARNED_SIGNS[idx] = sign; appLog('ok', '✏️ Signe «' + fr + '» mis à jour'); }
  else          { LEARNED_SIGNS.push(sign);  appLog('ok', '✅ Signe «' + fr + '» appris — total: ' + LEARNED_SIGNS.length); }
  _saveLearnedSigns();
  cancelLearn();
  buildRefGrid();
}

function cancelLearn() {
  _capturedFingers = null;
  var p = document.getElementById('learnPanel');
  if (p) p.style.display = 'none';
}

function deleteLearnedSign(key) {
  var s = LEARNED_SIGNS.find(function(x) { return x.key === key; });
  LEARNED_SIGNS = LEARNED_SIGNS.filter(function(x) { return x.key !== key; });
  _saveLearnedSigns();
  buildRefGrid();
  if (s) appLog('info', 'Signe «' + s.fr + '» supprimé');
}

var _capturedFingers = null;

/* ── MEDIAPIPE LOADER ─────────────────────────────────── */
var _mpLoaded = false, _useLocal = true, _mpPromise = null;

function _loadScript(src) {
  return new Promise(function(resolve, reject) {
    var s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = function() { reject(new Error('Échec chargement: ' + src)); };
    document.head.appendChild(s);
  });
}

// Poll /mp_status every 2s for up to maxSec seconds; keeps pill updated.
async function _waitServerReady(maxSec) {
  for (var i = 0; i < maxSec / 2; i++) {
    try {
      var st = await fetch('/mp_status').then(function(r) { return r.json(); });
      var pill = document.getElementById('mpPill');
      if (pill && !_mpLoaded) {
        pill.className = 'mp-pill loading';
        pill.textContent = '⏳ ' + st.done + '/' + st.total;
      }
      if (st.ready) {
        appLog('ok', 'Serveur prêt: ' + st.done + '/' + st.total + ' fichiers MediaPipe');
        appLog(st.patch && st.patch.indexOf(':0') === -1 ? 'ok' : 'warn',
          'Patch WASM (legacyModuleProp) : ' + (st.patch || 'aucune info'));
        return true;
      }
    } catch(e) {}
    await new Promise(function(r) { setTimeout(r, 2000); });
  }
  try {
    var st = await fetch('/mp_status').then(function(r) { return r.json(); });
    appLog('warn', 'Serveur IA pas prêt après ' + maxSec + 's — ' + st.done + '/' + st.total
      + ' fichiers' + (st.error ? ' — dernière erreur: ' + st.error : ''));
  } catch(e) {
    appLog('warn', 'Serveur IA pas prêt après ' + maxSec + 's (statut injoignable)');
  }
  return false;
}

// Single-flight loader — utilise TOUJOURS les fichiers auto-hébergés (patchés
// côté serveur). Le CDN unpkg n'est JAMAIS utilisé en repli : ses fichiers WASM
// ne sont pas patchables et plantent avec « Module.arguments has been replaced ».
// Mieux vaut attendre le serveur (patché, sûr) que charger un build qui va
// systématiquement s'abandonner.
function _bgPreload() {
  if (_mpPromise) return _mpPromise;
  _mpPromise = (async function() {
    appLog('info', '── Pré-chargement MediaPipe Hands v0.4.1646424915 (arrière-plan) ──');
    var ok = await _waitServerReady(180);   // démarrage à froid Render : jusqu'à 3 min
    if (!ok) {
      var pill = document.getElementById('mpPill');
      if (pill) { pill.className = 'mp-pill error'; pill.textContent = '⏳ IA en préparation'; }
      appLog('warn', 'IA pas encore prête — le serveur télécharge les fichiers. Cliquez Démarrer pour réessayer.');
      _mpPromise = null;   // autorise une nouvelle tentative au prochain clic
      throw new Error('server-not-ready');
    }
    await _loadScript('/mp/hands.js');
    await _loadScript('/mp/drawing_utils.js');
    _useLocal = true;
    _mpLoaded = true;
    var pill = document.getElementById('mpPill');
    if (pill) { pill.className = 'mp-pill ready'; pill.textContent = '✓ IA prête'; }
    appLog('ok', 'MediaPipe prêt — local (WASM patché ✓) — cliquez Démarrer !');
  })();
  return _mpPromise;
}

// Appelé par startCam() — instantané si _bgPreload() a déjà fini ; sinon attend
// (et réessaie) les fichiers auto-hébergés. Ne charge jamais le CDN.
async function ensureMP() {
  if (_mpLoaded) return;
  var lc = document.getElementById('liveConf');
  if (lc) lc.textContent = 'Préparation de l\'IA… (téléchargement serveur)';
  try {
    await _bgPreload();
  } catch(e) {
    if (lc) lc.textContent = '';
    throw new Error('IA pas encore prête — patientez quelques secondes puis réessayez');
  }
}

/* ── LSF SIGN DICTIONARY ──────────────────────────────── */
// p fields: true=doigt levé, false=doigt baissé, null=peu importe
// thumbDir: 'up'|'down'|null
var SIGNS = [
  { key:'BONJOUR',  emoji:'👋', fr:'BONJOUR',     en:'Hello',       desc:'5 doigts ouverts, main levée',            p:{thumb:true, index:true,  middle:true,  ring:true,  pinky:true,  dir:null} },
  { key:'OUI',      emoji:'✊', fr:'OUI',          en:'Yes',         desc:'Poing fermé, tous doigts repliés',        p:{thumb:false,index:false, middle:false, ring:false, pinky:false, dir:null} },
  { key:'BIEN',     emoji:'👍', fr:'BIEN',         en:'Good',        desc:'Pouce levé vers le haut, poing sinon',    p:{thumb:true, index:false, middle:false, ring:false, pinky:false, dir:'up'} },
  { key:'MAUVAIS',  emoji:'👎', fr:'MAUVAIS',      en:'Bad',         desc:'Pouce pointé vers le bas, poing sinon',   p:{thumb:true, index:false, middle:false, ring:false, pinky:false, dir:'down'} },
  { key:'JE_TAIME', emoji:'🤟', fr:'JE T\'AIME',  en:'I Love You',  desc:'Pouce + Index + Auriculaire levés',       p:{thumb:true, index:true,  middle:false, ring:false, pinky:true,  dir:null} },
  { key:'PAIX',     emoji:'✌️', fr:'PAIX',         en:'Peace / 2',   desc:'Index + Majeur levés en V',              p:{thumb:false,index:true,  middle:true,  ring:false, pinky:false, dir:null} },
  { key:'UN',       emoji:'☝️', fr:'UN',           en:'One',         desc:'Index seul levé, autres fermés',          p:{thumb:false,index:true,  middle:false, ring:false, pinky:false, dir:null} },
  { key:'TROIS',    emoji:'3️⃣', fr:'TROIS',        en:'Three',       desc:'Index + Majeur + Annulaire levés',        p:{thumb:false,index:true,  middle:true,  ring:true,  pinky:false, dir:null} },
  { key:'QUATRE',   emoji:'🖐️', fr:'QUATRE',       en:'Four',        desc:'4 doigts levés, pouce replié',            p:{thumb:false,index:true,  middle:true,  ring:true,  pinky:true,  dir:null} },
  { key:'APPELER',  emoji:'🤙', fr:'APPELER',      en:'Call Me',     desc:'Pouce + Auriculaire levés (Shaka)',       p:{thumb:true, index:false, middle:false, ring:false, pinky:true,  dir:null} },
  { key:'ROCK',     emoji:'🤘', fr:'ROCK',         en:'Rock On',     desc:'Index + Auriculaire levés, pouce bas',    p:{thumb:false,index:true,  middle:false, ring:false, pinky:true,  dir:null} },
  { key:'OK',       emoji:'👌', fr:'OK',           en:'OK',          desc:'Majeur + Annulaire + Auriculaire levés',  p:{thumb:true, index:false, middle:true,  ring:true,  pinky:true,  dir:null} },
  // ── Laveau 1868 ───────────────────────────────────────────────────────────
  { key:'DEUX',     emoji:'✌', fr:'DEUX',          en:'Two',         desc:'Pouce + Index levés (Laveau: "ouvrez le pouce et l\'index droit")',
    p:{thumb:true, index:true,  middle:false, ring:false, pinky:false, dir:null} },
  { key:'BOIRE_S',  emoji:'🥤', fr:'BOIRE',        en:'Drink',       desc:'Pouce + Index + Majeur levés, annulaire et auriculaire repliés (main demi-ouverte, Laveau)',
    p:{thumb:true, index:true,  middle:true,  ring:false, pinky:false, dir:null} },
];

function buildRefGrid() {
  var g = document.getElementById('refGrid');
  g.innerHTML = '';
  SIGNS.forEach(function(s) {
    var d = document.createElement('div');
    d.className = 'ref-item';
    d.title = s.desc;
    d.innerHTML = '<span class="ref-emoji">' + s.emoji + '</span><span class="ref-label">' + s.fr + '</span>';
    g.appendChild(d);
  });
  BIMANUAL_SIGNS.forEach(function(s) {
    var d = document.createElement('div');
    d.className = 'ref-item bi';
    d.title = s.desc;
    d.innerHTML = '<span class="bi-badge">2M</span><span class="ref-emoji">' + s.emoji + '</span><span class="ref-label">' + s.fr + '</span>';
    g.appendChild(d);
  });
  // Learned signs section
  var sec = document.getElementById('learnedSignsSec');
  var lg  = document.getElementById('learnedRefGrid');
  if (sec && lg) {
    sec.style.display = LEARNED_SIGNS.length ? 'block' : 'none';
    lg.innerHTML = '';
    LEARNED_SIGNS.forEach(function(s) {
      var d = document.createElement('div');
      d.className = 'ref-item custom';
      d.title = s.desc;
      d.innerHTML = '<span class="custom-badge">✎</span>'
        + '<button class="ref-del" onclick="deleteLearnedSign(\'' + s.key.replace(/'/g, "\\'") + '\')" title="Supprimer">✕</button>'
        + '<span class="ref-emoji">' + s.emoji + '</span>'
        + '<span class="ref-label">' + s.fr + '</span>';
      lg.appendChild(d);
    });
  }
}

/* ── HAND CLASSIFICATION ──────────────────────────────── */
function _dist(a, b) {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
}

function getFingers(lm) {
  var w = lm[0]; // wrist
  // finger tip farther from wrist than PIP × 1.08 threshold = extended
  function ext(tip, pip) {
    return _dist(lm[tip], w) > _dist(lm[pip], w) * 1.08;
  }
  var index  = ext(8,  6);
  var middle = ext(12, 10);
  var ring   = ext(16, 14);
  var pinky  = ext(20, 18);
  // thumb: tip far from index MCP relative to palm width (index-MCP to pinky-MCP)
  var palmW = _dist(lm[5], lm[17]);
  var thumb = _dist(lm[4], lm[5]) > palmW * 0.55;
  var thumbUp   = lm[4].y < lm[2].y - 0.025;
  var thumbDown = lm[4].y > lm[2].y + 0.025;
  return { thumb: thumb, index: index, middle: middle, ring: ring, pinky: pinky,
           thumbUp: thumbUp, thumbDown: thumbDown, palmW: palmW };
}

function classify(lm) {
  var f = getFingers(lm);
  for (var i = 0; i < SIGNS.length; i++) {
    var s = SIGNS[i], p = s.p;
    if (p.thumb  !== null && p.thumb  !== f.thumb)  continue;
    if (p.index  !== null && p.index  !== f.index)  continue;
    if (p.middle !== null && p.middle !== f.middle)  continue;
    if (p.ring   !== null && p.ring   !== f.ring)    continue;
    if (p.pinky  !== null && p.pinky  !== f.pinky)   continue;
    if (p.dir === 'up'   && !f.thumbUp)   continue;
    if (p.dir === 'down' && !f.thumbDown) continue;
    return { sign: s, conf: 82, f: f };
  }
  // Check custom learned signs (lower confidence; built-ins take priority)
  for (var j = 0; j < LEARNED_SIGNS.length; j++) {
    var ls = LEARNED_SIGNS[j], lp = ls.p;
    if (lp.thumb  !== null && lp.thumb  !== f.thumb)  continue;
    if (lp.index  !== null && lp.index  !== f.index)  continue;
    if (lp.middle !== null && lp.middle !== f.middle)  continue;
    if (lp.ring   !== null && lp.ring   !== f.ring)    continue;
    if (lp.pinky  !== null && lp.pinky  !== f.pinky)   continue;
    if (lp.dir === 'up'   && !f.thumbUp)   continue;
    if (lp.dir === 'down' && !f.thumbDown) continue;
    return { sign: ls, conf: 75, f: f };
  }
  return { sign: null, conf: 0, f: f };
}

/* ── BIMANUAL SIGN DICTIONARY (2 mains simultanées) ─────── */
// Tiré du Petit Dictionnaire de Laveau (1868) + LSF contemporaine
// dom = main dominante (droite utilisateur), non = main non-dominante
// rel: 'close' = poignets proches (<0.35), 'apart' = poignets éloignés (>0.42), 'any' = sans contrainte
var BIMANUAL_SIGNS = [
  // ── Du dictionnaire Laveau (1868) ──────────────────────────────────────────
  { key:'FORT',       emoji:'💪', fr:'FORT',        en:'Strong / Powerful',
    desc:'Deux poings serrés aux épaules (Laveau: "bien fermer les deux poings")',
    dom:{thumb:false,index:false,middle:false,ring:false,pinky:false,dir:null},
    non:{thumb:false,index:false,middle:false,ring:false,pinky:false,dir:null},
    rel:'any', bimanual:true },

  { key:'MONDE',      emoji:'🌍', fr:'MONDE',       en:'World',
    desc:'Les deux bras forment un grand cercle, mains ouvertes très écartées (Laveau)',
    dom:{thumb:true,index:true,middle:true,ring:true,pinky:true,dir:null},
    non:{thumb:true,index:true,middle:true,ring:true,pinky:true,dir:null},
    rel:'apart', bimanual:true },

  { key:'PROMETTRE',  emoji:'🤝', fr:'PROMETTRE',   en:'Promise',
    desc:'Les deux index levés côte à côte (Laveau: "signe de promettre")',
    dom:{thumb:false,index:true,middle:false,ring:false,pinky:false,dir:null},
    non:{thumb:false,index:true,middle:false,ring:false,pinky:false,dir:null},
    rel:'close', bimanual:true },

  // ── LSF contemporaine ───────────────────────────────────────────────────────
  { key:'EXCELLENT',  emoji:'✨', fr:'EXCELLENT',   en:'Excellent',
    desc:'Les deux pouces levés vers le haut',
    dom:{thumb:true,index:false,middle:false,ring:false,pinky:false,dir:'up'},
    non:{thumb:true,index:false,middle:false,ring:false,pinky:false,dir:'up'},
    rel:'any', bimanual:true },

  { key:'BRAVO',      emoji:'👏', fr:'BRAVO',       en:'Bravo / Applause',
    desc:'Les deux mains ouvertes rapprochées — applaudir',
    dom:{thumb:true,index:true,middle:true,ring:true,pinky:true,dir:null},
    non:{thumb:true,index:true,middle:true,ring:true,pinky:true,dir:null},
    rel:'close', bimanual:true },

  { key:'VICTOIRE',   emoji:'🏆', fr:'VICTOIRE',    en:'Victory / Peace ×2',
    desc:'Les deux mains en V — victoire double',
    dom:{thumb:false,index:true,middle:true,ring:false,pinky:false,dir:null},
    non:{thumb:false,index:true,middle:true,ring:false,pinky:false,dir:null},
    rel:'any', bimanual:true },

  { key:'MUSIQUE',    emoji:'🎵', fr:'MUSIQUE',     en:'Music',
    desc:'Les deux mains "rock" — musique / concert',
    dom:{thumb:false,index:true,middle:false,ring:false,pinky:true,dir:null},
    non:{thumb:false,index:true,middle:false,ring:false,pinky:true,dir:null},
    rel:'any', bimanual:true },

  { key:'DOUBLE_AMOUR',emoji:'🤟',fr:'AMOUR FORT',  en:'Much Love',
    desc:'Les deux mains ILY — aimer très fort (forme emphatique)',
    dom:{thumb:true,index:true,middle:false,ring:false,pinky:true,dir:null},
    non:{thumb:true,index:true,middle:false,ring:false,pinky:true,dir:null},
    rel:'any', bimanual:true },

  { key:'DONNER',     emoji:'🎁', fr:'DONNER',      en:'Give / Offer',
    desc:'Main dominante ouverte, non-dominante fermée (Laveau: "signe d\'offrir")',
    dom:{thumb:true,index:true,middle:true,ring:true,pinky:true,dir:null},
    non:{thumb:false,index:false,middle:false,ring:false,pinky:false,dir:null},
    rel:'close', bimanual:true },

  { key:'ENSEIGNER',  emoji:'🎓', fr:'ENSEIGNER',   en:'Teach / Learn',
    desc:'Index dominant pointé sur la main non-dominante ouverte (lire/enseigner)',
    dom:{thumb:false,index:true,middle:false,ring:false,pinky:false,dir:null},
    non:{thumb:true,index:true,middle:true,ring:true,pinky:true,dir:null},
    rel:'close', bimanual:true },

  { key:'PARFAIT',    emoji:'👌', fr:'PARFAIT',     en:'Perfect',
    desc:'Les deux mains OK simultanément',
    dom:{thumb:true,index:false,middle:true,ring:true,pinky:true,dir:null},
    non:{thumb:true,index:false,middle:true,ring:true,pinky:true,dir:null},
    rel:'any', bimanual:true },
];

function _bimatchFinger(f, p) {
  if (p.thumb  !== null && p.thumb  !== f.thumb)  return false;
  if (p.index  !== null && p.index  !== f.index)  return false;
  if (p.middle !== null && p.middle !== f.middle)  return false;
  if (p.ring   !== null && p.ring   !== f.ring)    return false;
  if (p.pinky  !== null && p.pinky  !== f.pinky)   return false;
  if (p.dir === 'up'   && !f.thumbUp)   return false;
  if (p.dir === 'down' && !f.thumbDown) return false;
  return true;
}

function _matchRelDist(dist, rel) {
  if (!rel || rel === 'any') return true;
  if (rel === 'close') return dist < 0.35;
  if (rel === 'apart') return dist > 0.42;
  return true;
}

function classifyBimanual(lm0, lm1) {
  if (!lm0 || lm0.length < 21 || !lm1 || lm1.length < 21) return { sign: null, conf: 0 };
  var f0 = getFingers(lm0), f1 = getFingers(lm1);
  var w0 = lm0[0], w1 = lm1[0];
  var dx = w0.x - w1.x, dy = w0.y - w1.y;
  var dist = Math.sqrt(dx*dx + dy*dy);

  // Dominant = lower x in raw frame (= user's right hand, appears right in mirrored view)
  var domF = w0.x <= w1.x ? f0 : f1;
  var nonF = w0.x <= w1.x ? f1 : f0;

  for (var i = 0; i < BIMANUAL_SIGNS.length; i++) {
    var s = BIMANUAL_SIGNS[i];
    if (!_matchRelDist(dist, s.rel)) continue;
    // Try direct ordering
    if (_bimatchFinger(domF, s.dom) && _bimatchFinger(nonF, s.non)) {
      return { sign: s, conf: 80, domF: domF, nonF: nonF, dist: dist };
    }
    // Try reversed ordering (for asymmetric signs, catches left-handed users)
    if (_bimatchFinger(domF, s.non) && _bimatchFinger(nonF, s.dom)) {
      return { sign: s, conf: 78, domF: domF, nonF: nonF, dist: dist };
    }
  }
  return { sign: null, conf: 0 };
}

/* ── PHRASES COMMUNES + PRÉDICTION ───────────────────── */
var COMMON_PHRASES = [
  {keys:['HI'],                          fr:'Bonjour !',                   en:'Hello!'},
  {keys:['HI','GOOD'],                   fr:'Bonjour, ça va bien ?',       en:'Hello, doing well?'},
  {keys:['IX-1','GOOD'],                 fr:'Je vais bien.',                en:"I'm doing well."},
  {keys:['IX-1','LIKE','IX-2'],          fr:"Je t'aime.",                   en:'I love you.'},
  {keys:['THANK','IX-2'],                fr:'Merci à toi.',                 en:'Thank you.'},
  {keys:['IX-1','SORRY'],                fr:'Je suis désolé.',              en:"I'm sorry."},
  {keys:['IX-2','WANT','HELP'],          fr:"Tu as besoin d'aide ?",        en:'Do you need help?'},
  {keys:['PLEASE','HELP'],               fr:"Aide-moi s'il te plaît.",      en:'Help me please.'},
  {keys:['IX-1','WANT','EAT'],           fr:'Je veux manger.',              en:'I want to eat.'},
  {keys:['IX-1','WANT','DRINK'],         fr:'Je veux boire.',               en:'I want to drink.'},
  {keys:['IX-1','GO','HOME'],            fr:'Je rentre à la maison.',       en:"I'm going home."},
  {keys:['YES','IX-1','KNOW'],           fr:'Oui, je sais.',                en:'Yes, I know.'},
  {keys:['NO','SORRY'],                  fr:'Non, désolé.',                 en:'No, sorry.'},
  {keys:['IX-1','HAPPY'],                fr:'Je suis heureux.',             en:"I'm happy."},
];

function _allSigns() { return SIGNS.concat(BIMANUAL_SIGNS).concat(LEARNED_SIGNS); }

function getPredictions(currentKeys) {
  var n = currentKeys.length;
  var seen = {}, results = [];
  COMMON_PHRASES.forEach(function(p) {
    if (p.keys.length <= n) return;
    for (var i = 0; i < n; i++) {
      if (p.keys[i] !== currentKeys[i]) return;
    }
    var nk = p.keys[n];
    if (seen[nk]) return;
    seen[nk] = true;
    var obj = _allSigns().find(function(s) { return s.key === nk; });
    if (obj) results.push({nextKey: nk, signObj: obj, hint: p.fr});
  });
  return results;
}

function _exactPhraseMatch(currentKeys) {
  return COMMON_PHRASES.find(function(p) {
    return p.keys.length === currentKeys.length &&
           p.keys.every(function(k, i) { return k === currentKeys[i]; });
  }) || null;
}

function _bestPhraseHint(currentKeys) {
  var n = currentKeys.length, best = null;
  COMMON_PHRASES.forEach(function(p) {
    if (p.keys.length <= n) return;
    for (var i = 0; i < n; i++) {
      if (p.keys[i] !== currentKeys[i]) return;
    }
    if (!best || p.keys.length < best.keys.length) best = p;
  });
  return best;
}

function _updatePredictions() {
  var currentKeys = _sentenceObjs.map(function(s) { return s.key; });
  var bar = document.getElementById('predBar');
  var sug = document.getElementById('phraseSuggest');
  if (!bar || !sug) return;

  var exact = _exactPhraseMatch(currentKeys);
  if (exact) {
    bar.innerHTML = '<span class="pred-complete">✅ ' + exact.fr + '</span>';
    sug.textContent = '';
    clearTimeout(_phraseCompleteTimer);
    _phraseCompleteTimer = setTimeout(function() {
      appLog('ok', '📢 Phrase reconnue — lecture : «' + exact.fr + '»');
      speakFR(exact.fr);
    }, 600);
    return;
  }

  var preds = getPredictions(currentKeys);
  var hint  = _bestPhraseHint(currentKeys);
  sug.innerHTML = hint ? '<span>→ <em>' + hint.fr + '</em></span>' : '';

  if (!preds.length) { bar.innerHTML = ''; return; }
  var html = '<span class="pred-label">Suite probable :</span>';
  preds.forEach(function(p) {
    html += '<button class="pred-btn" onclick="_addPredSign(\'' + p.nextKey + '\')" title="' + p.hint + '">'
          + p.signObj.emoji + ' ' + p.signObj.fr + '</button>';
  });
  bar.innerHTML = html;
}

function _addPredSign(key) {
  var obj = _allSigns().find(function(s) { return s.key === key; });
  if (obj) _addWord(obj);
}

/* ── CAMERA & DETECTION LOOP ──────────────────────────── */
// Pre-define window.Module now, before hands.js ever loads.
// packed_assets_loader.js line 54 references Module as a bare global — if Module
// is undefined (e.g. after delete window.Module in a previous stop), it throws
// ReferenceError. Initialising here ensures the global always exists.
window.Module = window.Module || {};

var mpH = null, rafId = null, stream = null, running = false;
var holdKey = null, holdStart = 0, cooldownUntil = 0;
var sentence = [], _sentenceObjs = [], debugOn = false;
var _errCount = 0;
var _inactivityTimer = null, _phraseCompleteTimer = null;
var HOLD_MS = 1000;
// hold ring circumference: 2π × r18 ≈ 113
var HOLD_CIRC = 113;
var HAND_COLOURS = [['#6366f1','#7c3aed'],['#22c55e','#059669']];
// Learning service
var _lastFingers = null, _lastSign = null;
var LEARNED_SIGNS = [];

function toggleDebug() {
  debugOn = !debugOn;
  document.getElementById('dbgBox').style.display = debugOn ? 'block' : 'none';
  appLog('info', 'Mode debug: ' + (debugOn ? 'activé' : 'désactivé'));
}

async function startCam() {
  if (running) return;
  // Unlock TTS in user gesture — required on iOS/Safari
  _wasmAborted = false; _onerrorCount = 0;
  try {
    var u = new SpeechSynthesisUtterance(' '); u.volume = 0;
    speechSynthesis.speak(u);
    setTimeout(function() { speechSynthesis.cancel(); }, 80);
  } catch(_) {}

  document.getElementById('btnStart').style.display = 'none';
  document.getElementById('btnStop').style.display  = 'inline-flex';
  document.getElementById('btnLearn').style.display = 'block';
  document.getElementById('idleOverlay').style.display = 'none';
  document.getElementById('vidOverlay').style.display  = 'flex';
  document.getElementById('liveConf').textContent = 'Accès caméra…';
  appLog('info', '── Démarrage de la caméra ──');

  var vid = document.getElementById('vid');
  var cvs = document.getElementById('cvs');
  var ctx = cvs.getContext('2d');

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'user' }, width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    });
    var track = stream.getVideoTracks()[0];
    appLog('ok', 'Caméra accordée: ' + (track ? track.label : 'inconnue'));
  } catch(e1) {
    appLog('warn', 'Caméra HD refusée (' + e1.message + ') — essai mode dégradé…');
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      appLog('ok', 'Caméra accordée (mode dégradé)');
    } catch(e2) {
      appLog('err', 'Caméra refusée: ' + e2.message);
      alert('Impossible d\'accéder à la caméra : ' + e2.message);
      _resetCamUI();
      return;
    }
  }

  vid.srcObject = stream;
  await new Promise(function(r) { vid.onloadedmetadata = r; setTimeout(r, 4000); });
  try { await vid.play(); } catch(_) {}

  function setSize() {
    cvs.width  = vid.videoWidth  || 640;
    cvs.height = vid.videoHeight || 480;
  }
  setSize();
  vid.addEventListener('resize', setSize);
  appLog('info', 'Résolution vidéo: ' + (vid.videoWidth || '?') + '×' + (vid.videoHeight || '?'));

  // Load MediaPipe
  try { await ensureMP(); }
  catch(e) {
    appLog('err', 'Chargement MediaPipe impossible: ' + e.message);
    _resetCamUI(); return;
  }

  document.getElementById('liveConf').textContent = 'Initialisation du modèle…';
  appLog('info', 'Détection support SIMD WebAssembly…');
  var simdOk = false;
  try {
    simdOk = WebAssembly.validate(new Uint8Array([
      0,97,115,109,1,0,0,0,1,5,1,96,0,1,123,3,2,1,0,10,10,1,8,0,65,0,253,15,253,98,11
    ]));
  } catch(_) {}
  appLog('info', 'SIMD: ' + (simdOk ? 'supporté ✓' : 'non supporté — utilisation du fichier WASM non-SIMD'));

  // Blob URL patch: only needed for CDN fallback (local files are already patched server-side).
  // Loading the WASM JS from a Blob URL sets scriptDirectory='' in Emscripten,
  // which can break the packed-assets loader path resolution.
  var patchedUrls = {};
  if (!_useLocal) {
    var cdnBase = 'https://unpkg.com/@mediapipe/hands@0.4.1646424915/';
    appLog('info', 'Mode CDN — patch WASM client-side (' + (simdOk ? 'SIMD + non-SIMD' : 'non-SIMD') + ')…');
    try {
      if (simdOk) {
        patchedUrls['hands_solution_simd_wasm_bin.js'] =
          await _fetchAndPatchJs(cdnBase + 'hands_solution_simd_wasm_bin.js');
      }
      patchedUrls['hands_solution_wasm_bin.js'] =
        await _fetchAndPatchJs(cdnBase + 'hands_solution_wasm_bin.js');
      appLog('ok', 'Patch CDN appliqué ✓');
    } catch(e) {
      appLog('warn', 'Patch CDN partiel: ' + e.message);
    }
  } else {
    appLog('ok', 'Mode local — fichiers WASM déjà patchés côté serveur, Blob URL non utilisé ✓');
  }

  // Pre-define window.Module with locateFile so that hands_solution_packed_assets_loader.js
  // (loaded as a global script) shares the same Module object as hands_solution_simd_wasm_bin.js.
  // Both files do: var Module = typeof Module !== 'undefined' ? Module : {}
  // Pre-defining ensures they reference the same global instance.
  function _mpLocate(f) {
    if (!simdOk && f.indexOf('simd_wasm_bin') !== -1) {
      f = f.replace('simd_wasm_bin', 'wasm_bin');
    }
    if (patchedUrls[f]) return patchedUrls[f];
    return _useLocal
      ? '/mp/' + f
      : 'https://unpkg.com/@mediapipe/hands@0.4.1646424915/' + f;
  }
  window.Module = (typeof window.Module === 'object' && window.Module) ? window.Module : {};
  window.Module['locateFile'] = _mpLocate;

  mpH = new Hands({ locateFile: _mpLocate });

  mpH.setOptions({
    maxNumHands: 2,
    modelComplexity: 0,
    minDetectionConfidence: 0.55,
    minTrackingConfidence: 0.40
  });
  appLog('info', 'Modèle: maxMains=2 (bimanuel activé), complexité=0, détection≥55%, suivi≥40%');

  mpH.onResults(function(res) {
    ctx.clearRect(0, 0, cvs.width, cvs.height);
    var lms = res.multiHandLandmarks;
    var handCount = lms ? lms.length : 0;

    if (!handCount) {
      _onDetect(null, 0, null);
      if (debugOn) document.getElementById('dbgBox').textContent = 'Aucune main';
      return;
    }

    // Draw all hands with distinct colours
    for (var hi = 0; hi < handCount; hi++) {
      var c = HAND_COLOURS[hi] || HAND_COLOURS[0];
      drawConnectors(ctx, lms[hi], HAND_CONNECTIONS, {color: c[0], lineWidth: 2});
      drawLandmarks(ctx, lms[hi], {color:'#fff', fillColor: c[1], radius: 3});
    }

    // ── 2-hand bimanual classification ──
    if (handCount >= 2) {
      var bi = classifyBimanual(lms[0], lms[1]);
      if (bi.sign) {
        _onDetect(bi.sign, bi.conf, bi.domF);
        if (debugOn) {
          var df = bi.domF, nf = bi.nonF;
          document.getElementById('dbgBox').innerHTML =
            '👐 BIMANUEL dist=' + bi.dist.toFixed(2) + '<br>' +
            'D T:'+(df.thumb|0)+' I:'+(df.index|0)+' M:'+(df.middle|0)+' R:'+(df.ring|0)+' P:'+(df.pinky|0)+'<br>' +
            'G T:'+(nf.thumb|0)+' I:'+(nf.index|0)+' M:'+(nf.middle|0)+' R:'+(nf.ring|0)+' P:'+(nf.pinky|0)+'<br>' +
            '→ '+bi.sign.fr;
        }
        return;
      }
    }

    // ── Fallback: classify dominant hand (lower x = user's right) ──
    var domLm = lms[0];
    if (handCount >= 2 && lms[1][0].x < lms[0][0].x) domLm = lms[1];
    var r = classify(domLm);
    _onDetect(r.sign, r.conf, r.f);
    if (debugOn) {
      var f = r.f;
      document.getElementById('dbgBox').innerHTML =
        (handCount >= 2 ? '✋✋ 2 mains (unimanuel)<br>' : '') +
        'T:'+(f.thumb|0)+' I:'+(f.index|0)+' M:'+(f.middle|0)+' R:'+(f.ring|0)+' P:'+(f.pinky|0)+'<br>' +
        'thumbUp:'+(f.thumbUp|0)+' dn:'+(f.thumbDown|0)+'<br>' +
        'palmW: '+f.palmW.toFixed(3)+'<br>' +
        '→ '+(r.sign ? r.sign.fr : '—');
    }
  });

  appLog('ok', '── Détection démarrée (20 fps) — ' + SIGNS.length + ' signes unimanuel + ' + BIMANUAL_SIGNS.length + ' signes bimanuel ──');
  running = true; _errCount = 0;
  var lastTs = 0;
  var FRAME_MS = 1000 / 20;

  function loop(ts) {
    if (!running) return;
    rafId = requestAnimationFrame(loop);
    if (ts - lastTs >= FRAME_MS && vid.readyState >= 2) {
      lastTs = ts;
      try {
        mpH.send({ image: vid });
        _errCount = 0;
      } catch(e) {
        _errCount++;
        if (_errCount === 1) appLog('err', 'mpH.send() erreur: ' + e.message);
        if (_errCount >= 10) {
          appLog('err', 'Arrêt après 10 erreurs consécutives — rechargez la page');
          stopCam(); return;
        }
      }
    }
  }
  rafId = requestAnimationFrame(loop);
  document.getElementById('liveConf').textContent = '✅ Actif — montrez un signe LSF !';
}

function stopCam() {
  running = false;
  if (rafId)  { cancelAnimationFrame(rafId); rafId = null; }
  if (mpH)    { try { mpH.close(); } catch(_) {} mpH = null; }
  if (stream) { stream.getTracks().forEach(function(t) { t.stop(); }); stream = null; }
  _revokeBlobUrls();
  // Reset Module state for next startCam(), but NEVER delete window.Module —
  // packed_assets_loader.js (already loaded as a <script>) uses it as a bare
  // global; deleting it causes ReferenceError on every subsequent start.
  window.Module = {};
  document.getElementById('cvs').getContext('2d').clearRect(0, 0, 9999, 9999);
  appLog('info', 'Caméra et modèle arrêtés');
  _resetCamUI();
}

function _resetCamUI() {
  document.getElementById('btnStart').style.display  = 'inline-flex';
  document.getElementById('btnStop').style.display   = 'none';
  document.getElementById('btnLearn').style.display  = 'none';
  document.getElementById('idleOverlay').style.display = 'flex';
  document.getElementById('vidOverlay').style.display  = 'none';
  document.getElementById('holdRing').style.display    = 'none';
  document.getElementById('liveSign').textContent = '—';
  document.getElementById('heroEmoji').textContent = '🤷';
  document.getElementById('heroSign').textContent  = 'En attente…';
  document.getElementById('heroEn').textContent    = 'Activez la caméra';
  document.getElementById('confFill').style.width  = '0%';
  holdKey = null; holdStart = 0;
  cancelLearn();
}

/* ── DETECTION HANDLER ────────────────────────────────── */
function _onDetect(sign, conf, fingers) {
  if (fingers) { _lastFingers = fingers; }  // persist for learning capture
  if (sign)    { _lastSign    = sign;    }
  var now = Date.now();
  if (!sign) {
    document.getElementById('liveSign').textContent  = '—';
    document.getElementById('liveConf').textContent  = 'Aucun signe détecté';
    document.getElementById('heroEmoji').textContent = '🤷';
    document.getElementById('heroSign').textContent  = 'Aucun signe';
    document.getElementById('heroEn').textContent    = 'Montrez un signe à la caméra';
    document.getElementById('confFill').style.width  = '0%';
    document.getElementById('holdRing').style.display = 'none';
    holdKey = null; holdStart = 0;
    return;
  }

  var biTag = sign.bimanual ? ' 👐' : '';
  document.getElementById('liveSign').textContent  = sign.emoji + ' ' + sign.fr + biTag;
  document.getElementById('liveConf').textContent  = 'Confiance : ' + conf + '%' + (sign.bimanual ? ' · 2 mains' : '');
  document.getElementById('heroEmoji').textContent = sign.emoji;
  document.getElementById('heroSign').textContent  = sign.fr + (sign.bimanual ? ' 👐' : '');
  document.getElementById('heroEn').textContent    = sign.en;
  document.getElementById('confFill').style.width  = conf + '%';

  if (now < cooldownUntil) {
    document.getElementById('heroEn').textContent = '✅ Ajouté ! Prochain signe…';
    document.getElementById('holdRing').style.display = 'none';
    return;
  }

  if (sign.key !== holdKey) {
    holdKey = sign.key; holdStart = now;
    document.getElementById('holdRing').style.display = 'block';
    document.getElementById('holdCircle').style.strokeDashoffset = HOLD_CIRC;
  }

  var elapsed  = now - holdStart;
  var progress = Math.min(elapsed / HOLD_MS, 1);
  document.getElementById('holdCircle').style.strokeDashoffset =
    (HOLD_CIRC * (1 - progress)).toFixed(1);

  if (progress >= 1) {
    _addWord(sign);
    cooldownUntil = now + 1500;
    holdKey = null; holdStart = 0;
    document.getElementById('holdRing').style.display = 'none';
    document.getElementById('heroEn').textContent = '✅ Ajouté !';
    appLog('ok', (sign.bimanual ? '👐 Bimanuel: ' : '✋ Signe: ') + sign.fr + ' (' + sign.en + ') — phrase: ' + sentence.join(' › '));
    speakFR(sign.fr);
  } else {
    var rem = ((HOLD_MS - elapsed) / 1000).toFixed(1);
    document.getElementById('heroEn').textContent = 'Maintenez… ' + rem + 's';
  }
}

/* ── SENTENCE BUILDER ─────────────────────────────────── */
function _addWord(sign) {
  var idx = sentence.length;
  sentence.push(sign.fr);
  _sentenceObjs.push(sign);
  var empty = document.getElementById('sentEmpty');
  if (empty) empty.remove();
  var chip = document.createElement('div');
  chip.className = 'word-chip';
  chip.dataset.idx = idx;
  chip.innerHTML = '<span>' + sign.emoji + ' ' + sign.fr + '</span>'
    + '<button onclick="_removeWord(' + idx + ')" title="Supprimer ce mot">✕</button>';
  document.getElementById('sentWrap').appendChild(chip);
  _updatePredictions();
  // Inactivity auto-read (3s after last sign, ≥2 mots)
  clearTimeout(_inactivityTimer);
  _inactivityTimer = setTimeout(function() {
    if (sentence.length < 2) return;
    var keys = _sentenceObjs.map(function(s) { return s.key; });
    var exact = _exactPhraseMatch(keys);
    var txt = exact ? exact.fr : sentence.join(', ');
    appLog('info', '⏱ Lecture auto : «' + txt + '»');
    speakFR(txt);
    addConv('me', 'sign', txt);
  }, 3000);
}

function _removeWord(idx) {
  sentence.splice(idx, 1);
  _sentenceObjs.splice(idx, 1);
  _rebuildSent();
  _updatePredictions();
  appLog('info', 'Mot retiré — phrase: [' + sentence.join(', ') + ']');
}

function _rebuildSent() {
  var wrap = document.getElementById('sentWrap');
  wrap.innerHTML = '';
  if (!sentence.length) {
    wrap.innerHTML = '<span class="sent-empty" id="sentEmpty">Les signes reconnus apparaîtront ici…</span>';
    return;
  }
  sentence.forEach(function(w, i) {
    var chip = document.createElement('div');
    chip.className = 'word-chip';
    var em = (_sentenceObjs[i] && _sentenceObjs[i].emoji) ? _sentenceObjs[i].emoji + ' ' : '';
    chip.innerHTML = '<span>' + em + w + '</span><button onclick="_removeWord(' + i + ')" title="Supprimer">✕</button>';
    wrap.appendChild(chip);
  });
}

function clearSentence() {
  sentence = []; _sentenceObjs = []; holdKey = null; holdStart = 0; cooldownUntil = 0;
  clearTimeout(_inactivityTimer); clearTimeout(_phraseCompleteTimer);
  _rebuildSent();
  _updatePredictions();
  appLog('info', 'Phrase effacée');
}

/* ── TTS ──────────────────────────────────────────────── */
var _ttsVoice = null;
function _initVoices() {
  var voices = speechSynthesis.getVoices();
  _ttsVoice = voices.find(function(v) { return v.lang === 'fr-FR'; })
           || voices.find(function(v) { return v.lang.startsWith('fr'); })
           || voices[0] || null;
  if (_ttsVoice) appLog('info', 'Voix TTS: ' + _ttsVoice.name + ' [' + _ttsVoice.lang + ']');
  else            appLog('warn', 'Aucune voix française TTS — la synthèse peut être silencieuse');
}
if (window.speechSynthesis) {
  speechSynthesis.onvoiceschanged = _initVoices;
  setTimeout(_initVoices, 400);
} else {
  appLog('warn', 'SpeechSynthesis API non disponible sur ce navigateur');
}

function speakFR(text) {
  if (!window.speechSynthesis || !text) return;
  speechSynthesis.cancel();
  var u = new SpeechSynthesisUtterance(text);
  u.lang = 'fr-FR'; u.rate = 0.9; u.pitch = 1; u.volume = 1;
  if (_ttsVoice) u.voice = _ttsVoice;
  u.onerror = function(e) { appLog('warn', 'TTS erreur: ' + e.error); };
  speechSynthesis.speak(u);
}

function speakSentence() {
  if (!sentence.length) { speakFR('Aucun mot'); return; }
  var keys = _sentenceObjs.map(function(s) { return s.key; });
  var exact = _exactPhraseMatch(keys);
  var txt = exact ? exact.fr : sentence.join(', ');
  appLog('info', '🔊 Lecture : «' + txt + '»' + (exact ? ' (phrase naturelle)' : ''));
  speakFR(txt);
  addConv('me', 'sign', txt);
}

/* ══ DIALOGUE BIDIRECTIONNEL ═══════════════════════════════
   Statuts + reconnaissance vocale (parole→texte) + historique */

var STATUSES = [
  { key:'deaf-mute', icon:'🤟', name:'Sourd-Muet', desc:'Signe (LSF)',           canHear:false, canSpeak:false },
  { key:'deaf',      icon:'🧏', name:'Sourd',      desc:'Parle, n\'entend pas',  canHear:false, canSpeak:true  },
  { key:'mute',      icon:'🤫', name:'Muet',       desc:'Entend, ne parle pas',  canHear:true,  canSpeak:false },
  { key:'normal',    icon:'👂', name:'Entendant',  desc:'Entend et parle',       canHear:true,  canSpeak:true  }
];
function _statusByKey(k) {
  for (var i=0;i<STATUSES.length;i++){ if (STATUSES[i].key===k) return STATUSES[i]; }
  return STATUSES[3];
}

var userStatus = 'deaf-mute', otherStatus = 'normal';
var _pendingMe = null, _pendingOther = null;

function _loadStatus() {
  try {
    var raw = localStorage.getItem('lsf_status');
    if (raw) { var o = JSON.parse(raw); userStatus = o.me || userStatus; otherStatus = o.other || otherStatus; }
  } catch(e) {}
}
function _saveStatusLS() {
  try { localStorage.setItem('lsf_status', JSON.stringify({ me:userStatus, other:otherStatus })); } catch(e) {}
}

function _renderStatusBar() {
  var me = _statusByKey(userStatus), ot = _statusByKey(otherStatus);
  var em = document.getElementById('scMe'), eo = document.getElementById('scOther');
  if (em) em.textContent = me.icon + ' ' + me.name;
  if (eo) eo.textContent = ot.icon + ' ' + ot.name;
  var hint = document.getElementById('modeHint');
  if (hint) {
    var parts = [];
    if (!me.canSpeak) parts.push('Vous signez → l\'app <strong>parle</strong> pour vous');
    if (!me.canHear)  parts.push('L\'autre parle → l\'app <strong>écrit</strong> pour vous');
    hint.innerHTML = parts.length ? parts.join(' · ') : 'Communication libre dans les deux sens';
  }
}

function _applyStatusUI() {
  var me = _statusByKey(userStatus), ot = _statusByKey(otherStatus);
  // Le micro (parole→texte) sert quand l'autre PEUT parler (sinon rien à écouter)
  var listenCard = document.getElementById('listenCard');
  if (listenCard) listenCard.style.opacity = ot.canSpeak ? '1' : '.55';
  // Bouton "Apprendre ce signe" déjà géré ailleurs ; ici on n'enlève rien.
  _renderStatusBar();
}

function openStatusModal() {
  _pendingMe = userStatus; _pendingOther = otherStatus;
  _buildStatusOpts('meOpts', 'me');
  _buildStatusOpts('otherOpts', 'other');
  document.getElementById('statusModal').style.display = 'flex';
}

function _buildStatusOpts(containerId, which) {
  var c = document.getElementById(containerId);
  if (!c) return;
  c.innerHTML = '';
  var cur = which === 'me' ? _pendingMe : _pendingOther;
  STATUSES.forEach(function(s) {
    var d = document.createElement('div');
    d.className = 'status-opt' + (s.key === cur ? ' sel' : '');
    d.innerHTML = '<span class="so-icon">' + s.icon + '</span>'
      + '<span class="so-name">' + s.name + '</span>'
      + '<span class="so-desc">' + s.desc + '</span>';
    d.onclick = function() {
      if (which === 'me') _pendingMe = s.key; else _pendingOther = s.key;
      _buildStatusOpts(containerId, which);
    };
    c.appendChild(d);
  });
}

function saveStatus() {
  userStatus = _pendingMe || userStatus;
  otherStatus = _pendingOther || otherStatus;
  _saveStatusLS();
  document.getElementById('statusModal').style.display = 'none';
  _applyStatusUI();
  appLog('info', 'Statuts : moi=' + userStatus + ', autre=' + otherStatus);
}

/* ── RECONNAISSANCE VOCALE (Web Speech API) ──────────────── */
var _SR = window.SpeechRecognition || window.webkitSpeechRecognition || null;
var _rec = null, _listening = false;

function _initSR() {
  if (!_SR) {
    appLog('warn', 'SpeechRecognition non supportée — saisie manuelle activée');
    var mb = document.getElementById('micBtn');
    if (mb) { mb.disabled = true; document.getElementById('micLabel').textContent = 'Micro indisponible'; }
    var lm = document.getElementById('listenManual');
    if (lm) lm.style.display = 'flex';
    return;
  }
  _rec = new _SR();
  _rec.lang = 'fr-FR';
  _rec.continuous = true;
  _rec.interimResults = true;
  _rec.onresult = function(ev) {
    var interim = '', finalTxt = '';
    for (var i = ev.resultIndex; i < ev.results.length; i++) {
      var tr = ev.results[i][0].transcript;
      if (ev.results[i].isFinal) finalTxt += tr; else interim += tr;
    }
    var live = document.getElementById('listenLive');
    if (finalTxt.trim()) {
      addConv('other', 'speech', finalTxt.trim());
      if (live) live.innerHTML = '<span class="interim">…</span>';
    } else if (live) {
      live.innerHTML = '<span class="interim">' + (interim || '…') + '</span>';
    }
  };
  _rec.onerror = function(ev) {
    appLog('warn', 'Reconnaissance vocale : ' + ev.error);
    if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') {
      _stopListen();
      var lm = document.getElementById('listenManual');
      if (lm) lm.style.display = 'flex';
    }
  };
  _rec.onend = function() {
    // Redémarre si l'utilisateur veut toujours écouter (continuous coupe parfois)
    if (_listening) { try { _rec.start(); } catch(e) { _setMicUI(false); _listening = false; } }
  };
}

function toggleListen() {
  if (!_SR) { sendManual(); return; }
  if (_listening) _stopListen(); else _startListen();
}
function _startListen() {
  if (!_rec) _initSR();
  if (!_rec) return;
  try {
    _rec.start();
    _listening = true;
    _setMicUI(true);
    var live = document.getElementById('listenLive');
    if (live) { live.classList.add('listening'); live.innerHTML = '<span class="interim">🎧 À l\'écoute…</span>'; }
    appLog('info', '🎙️ Écoute démarrée');
  } catch(e) { appLog('warn', 'Impossible de démarrer l\'écoute : ' + e.message); }
}
function _stopListen() {
  _listening = false;
  if (_rec) { try { _rec.stop(); } catch(e) {} }
  _setMicUI(false);
  var live = document.getElementById('listenLive');
  if (live) { live.classList.remove('listening'); live.textContent = 'Appuyez sur le micro puis parlez.'; }
  appLog('info', '🎙️ Écoute arrêtée');
}
function _setMicUI(on) {
  var b = document.getElementById('micBtn');
  if (!b) return;
  b.classList.toggle('active', on);
  document.getElementById('micIcon').textContent = on ? '⏹' : '🎙️';
  document.getElementById('micLabel').textContent = on ? 'Arrêter' : 'Écouter';
}
function sendManual() {
  var inp = document.getElementById('manualText');
  if (!inp) return;
  var t = inp.value.trim();
  if (!t) return;
  addConv('other', 'speech', t);
  inp.value = '';
}

/* ── HISTORIQUE DE CONVERSATION ──────────────────────────── */
var CONV = [];
function _loadConv() {
  try { var raw = localStorage.getItem('lsf_conv'); if (raw) CONV = JSON.parse(raw); } catch(e) { CONV = []; }
}
function _saveConv() {
  try { localStorage.setItem('lsf_conv', JSON.stringify(CONV.slice(-100))); } catch(e) {}
}
function addConv(who, kind, text) {
  if (!text) return;
  var entry = { t: Date.now(), who: who, kind: kind, text: text };
  CONV.push(entry);
  if (CONV.length > 100) CONV.shift();
  _saveConv();
  _appendConvBubble(entry);
  // Si l'autre a parlé et que JE n'entends pas, le texte s'affiche (déjà) ;
  // si l'autre a parlé et que JE peux entendre, pas besoin. Rien à vocaliser.
}
function _fmtTime(ms) {
  var d = new Date(ms);
  function p(n){ return (n<10?'0':'')+n; }
  return p(d.getHours()) + ':' + p(d.getMinutes());
}
function _appendConvBubble(e) {
  var body = document.getElementById('convBody');
  if (!body) return;
  var empty = document.getElementById('convEmpty');
  if (empty) empty.remove();
  var b = document.createElement('div');
  b.className = 'bubble ' + (e.who === 'me' ? 'me' : 'other');
  var icon = e.kind === 'sign' ? '🤟' : '🎙️';
  var label = e.who === 'me' ? 'Moi' : 'L\'autre';
  var replay = (e.who === 'me')
    ? ' <span class="breplay" title="Relire" onclick="speakFR(' + _jsQuote(e.text) + ')">🔊</span>'
    : '';
  b.innerHTML = '<div class="bmeta">' + icon + ' ' + label + ' · ' + _fmtTime(e.t) + replay + '</div>'
    + _escapeHtml(e.text);
  body.appendChild(b);
  body.scrollTop = body.scrollHeight;
}
function _escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, function(c) {
    return { '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c];
  });
}
function _jsQuote(s) { return "'" + String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'") + "'"; }

function _renderConvAll() {
  var body = document.getElementById('convBody');
  if (!body) return;
  body.innerHTML = '';
  if (!CONV.length) {
    body.innerHTML = '<div class="conv-empty" id="convEmpty">La conversation apparaîtra ici — signes reconnus et paroles transcrites.</div>';
    return;
  }
  CONV.forEach(_appendConvBubble);
}
function clearConversation() {
  CONV = [];
  _saveConv();
  _renderConvAll();
  appLog('info', 'Conversation effacée');
}

/* ── TEXT → GLOSSES ───────────────────────────────────── */
var _sDescs = {};
async function doTranslate() {
  var text = document.getElementById('inputText').value.trim();
  if (!text) { alert('Entrez du texte à traduire'); return; }
  var btn = document.getElementById('btnTr');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span> Traduction en cours…';
  try {
    var r = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        language: document.getElementById('srcLang').value,
        target:   document.getElementById('tgtSign').value
      })
    });
    _renderResult(await r.json(), text);
  } catch(e) {
    alert('Erreur de traduction : ' + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔤 Traduire en LSF';
  }
}

function _renderResult(d, orig) {
  _sDescs = {};
  (d.sign_descriptions || []).forEach(function(s) { _sDescs[s.gloss] = s; });
  var row = document.getElementById('glossRow');
  row.innerHTML = '';
  d.glosses.forEach(function(g, i) {
    var b = document.createElement('button');
    b.className = 'gtag'; b.textContent = g;
    b.onclick = function() { _showCard(g, b); };
    row.appendChild(b);
    if (i < d.glosses.length - 1) {
      var a = document.createElement('span');
      a.className = 'garrow'; a.textContent = '→';
      row.appendChild(a);
    }
  });
  var isQ = (d.grammar || '').toLowerCase().includes('quest');
  document.getElementById('gType').innerHTML =
    '<span class="badge ' + (isQ ? 'badge-q' : 'badge-s') + '">' + (d.grammar || 'Énoncé') + '</span>';
  document.getElementById('gNotes').textContent = d.grammar_notes || '—';
  document.getElementById('mG').textContent = d.glosses.length;
  document.getElementById('mW').textContent = orig.trim().split(/\s+/).length;
  document.getElementById('mC').textContent = (d.confidence || 88) + '%';
  document.getElementById('mT').textContent = d.time || 0;
  document.getElementById('signCard').classList.remove('active');
  document.getElementById('textResult').style.display = 'block';
}

function _showCard(g, el) {
  document.querySelectorAll('.gtag').forEach(function(t) { t.classList.remove('sel'); });
  el.classList.add('sel');
  var s = _sDescs[g];
  document.getElementById('scGloss').textContent = g;
  var p = document.getElementById('scProps');
  p.innerHTML = s
    ? '<div class="sp"><div class="spl">✋ Forme</div><div class="spv">' + s.handshape + '</div></div>' +
      '<div class="sp"><div class="spl">📍 Position</div><div class="spv">' + s.location + '</div></div>' +
      '<div class="sp"><div class="spl">↔️ Mouvement</div><div class="spv">' + s.movement + '</div></div>'
    : '<div class="sp" style="grid-column:1/-1"><div class="spl">Info</div><div class="spv">Pas de description pour <strong>' + g + '</strong>.</div></div>';
  document.getElementById('signCard').classList.add('active');
}

function clearText() {
  document.getElementById('inputText').value = '';
  document.getElementById('textResult').style.display = 'none';
}

/* ── PWA : service worker ────────────────────────────────── */
// Enregistré après l'événement 'load' : pendant le démarrage à froid de Render,
// la requête /sw.js peut être avortée. On attend donc que la page soit stable,
// et un échec reste silencieux (fonctionnalité non critique).
function _registerSW() {
  if (!('serviceWorker' in navigator)) return;
  function reg() {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).then(function() {
      appLog('ok', '📲 PWA prête (installable / cache hors-ligne)');
    }).catch(function(e) {
      appLog('info', 'PWA : service worker non enregistré (' + (e && e.message ? e.message : 'ignoré') + ')');
    });
  }
  if (document.readyState === 'complete') reg();
  else window.addEventListener('load', reg);
}

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('inputText').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) doTranslate();
  });
});
</script>
</body>
</html>"""

@app.route('/')
def index():
    _ensure_download_started()
    return render_template_string(HTML)

# ── PWA : manifest + service worker (installable / cache hors-ligne) ──
_MANIFEST = {
    "name": "SignVoix — Traducteur LSF",
    "short_name": "SignVoix",
    "description": "Communication LSF bidirectionnelle en temps réel",
    "start_url": "/",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#f1f5f9",
    "theme_color": "#4f46e5",
    "lang": "fr",
    "icons": [
        {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}
    ],
}

@app.route('/manifest.json')
def manifest():
    return jsonify(_MANIFEST)

_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
    '<rect width="512" height="512" rx="112" fill="#4f46e5"/>'
    '<text x="50%" y="52%" font-size="300" text-anchor="middle" '
    'dominant-baseline="central">\U0001F91F</text></svg>'
)

@app.route('/icon.svg')
def icon_svg():
    return Response(_ICON_SVG, mimetype='image/svg+xml')

# Service worker : network-first pour tout, avec repli sur le cache hors-ligne.
_SW_JS = """
const CACHE = 'signvoix-v1';
const SHELL = ['/', '/manifest.json', '/icon.svg'];
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  // Ne pas mettre l'API en cache
  if (req.url.indexOf('/api/') !== -1) return;
  e.respondWith(
    fetch(req).then((res) => {
      if (res && res.status === 200 && res.type === 'basic') {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req).then((m) => m || caches.match('/')))
  );
});
"""

@app.route('/sw.js')
def service_worker():
    return Response(_SW_JS, mimetype='application/javascript')

@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    language = data.get('language', 'french')
    target = data.get('target', 'LSF')
    start = time.time()
    result = translate_with_slt(text, language, target) or translate_fallback(text, language)
    return jsonify({
        'glosses':           result['glosses'],
        'grammar':           result['grammar_type'],
        'grammar_notes':     result.get('grammar_notes', ''),
        'sign_descriptions': result.get('sign_descriptions', []),
        'confidence':        88,
        'time':              int((time.time() - start) * 1000),
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
