#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string, Response
from flask_cors import CORS
import os, re, time, threading
from urllib.request import urlopen
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
_mp_status = {'ready': False, 'done': 0, 'total': len(_MP_FILES)}

_ASSERT_PAT = re.compile(
    r'Object\.getOwnPropertyDescriptor\(Module,\s*["\']arguments["\']\)'
)
# Matches the defineProperty getter: someFunc("Module.arguments has been replaced...")
# Works even if 'abort' is renamed by the minifier (e.g. 'la', 'ia', etc.)
_ABORT_ARGS_PAT = re.compile(
    r'\b\w+\s*\(\s*["\']Module\.arguments has been replaced[^"\']*["\']\s*\)'
)

def _patch_mp(fname, raw):
    """Neutralise two Emscripten checks that conflict with hands.js Module.arguments."""
    if fname in ('hands_solution_simd_wasm_bin.js', 'hands_solution_wasm_bin.js'):
        try:
            text = raw.decode('utf-8')
            # Patch 1: assert(!Object.getOwnPropertyDescriptor(Module,"arguments"),...)
            p1 = _ASSERT_PAT.sub('false', text)
            # Patch 2: getter abort("Module.arguments has been replaced...") in defineProperty
            p2 = _ABORT_ARGS_PAT.sub('(0)', p1)
            n = (p1 != text) + (p2 != p1)
            if n:
                print(f'[MP] patched {n} assertion(s) in {fname}')
            return p2.encode('utf-8')
        except Exception as e:
            print(f'[MP] patch error {fname}: {e}')
    return raw

def _download_mp():
    _MP_DIR.mkdir(exist_ok=True)
    for url, fname in _MP_FILES:
        dest = _MP_DIR / fname
        if dest.exists() and dest.stat().st_size > 100:
            _mp_status['done'] += 1
            continue
        for attempt in range(3):
            try:
                with urlopen(url, timeout=90) as r:
                    data = _patch_mp(fname, r.read())
                dest.write_bytes(data)
                _mp_status['done'] += 1
                break
            except Exception as e:
                print(f'[MP] download failed {fname} attempt {attempt+1}: {e}')
                if attempt < 2:
                    time.sleep(2 ** attempt)
    _mp_status['ready'] = (_mp_status['done'] == _mp_status['total'])
    print(f'[MP] ready={_mp_status["ready"]} — {_mp_status["done"]}/{_mp_status["total"]} files in {_MP_DIR}')

threading.Thread(target=_download_mp, daemon=True).start()

@app.route('/mp/<path:filename>')
def serve_mp(filename):
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
    return jsonify(_mp_status)
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
<meta name="theme-color" content="#4f46e5">
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
    <button class="tab-btn active" onclick="switchTab('cam',this)">📷 Caméra</button>
    <button class="tab-btn"        onclick="switchTab('text',this)">📝 Texte</button>
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
    /Object\.getOwnPropertyDescriptor\(Module,\s*["']arguments['"]\)/g, 'false'
  );
  // Patch 2: defineProperty getter abort("Module.arguments has been replaced...")
  // Matches even if 'abort' was renamed by the minifier
  var p2 = p1.replace(
    /\b\w+\s*\(\s*["']Module\.arguments has been replaced[^"']*['"]\s*\)/g, '(0)'
  );
  var nPatches = (p1 !== text ? 1 : 0) + (p2 !== p1 ? 1 : 0);
  appLog(nPatches > 0 ? 'ok' : 'warn',
    'Patch ' + fname + ': ' + (nPatches > 0 ? nPatches + ' assertion(s) WASM neutralisée(s) ✓' : 'patterns absents (déjà patchés côté serveur ✓)'));
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
  buildRefGrid();
  pollMPStatus();
});

/* ── MEDIAPIPE STATUS POLL (background) ───────────────── */
function pollMPStatus() {
  fetch('/mp_status')
    .then(function(r) { return r.json(); })
    .then(function(s) {
      var pill = document.getElementById('mpPill');
      if (s.ready) {
        pill.className = 'mp-pill ready';
        pill.textContent = '✓ IA prête';
        appLog('ok', 'Serveur: ' + s.done + '/' + s.total + ' fichiers MediaPipe disponibles');
      } else {
        pill.className = 'mp-pill loading';
        pill.textContent = '⏳ ' + s.done + '/' + s.total;
        setTimeout(pollMPStatus, 3000);
      }
    })
    .catch(function() { setTimeout(pollMPStatus, 5000); });
}

/* ── MEDIAPIPE LOADER ─────────────────────────────────── */
var _mpLoaded = false, _useLocal = false;

function _loadScript(src) {
  return new Promise(function(resolve, reject) {
    var s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = function() { reject(new Error('Échec: ' + src)); };
    document.head.appendChild(s);
  });
}

async function _waitServerReady(maxSec) {
  appLog('info', 'Attente des fichiers MediaPipe sur le serveur (max ' + maxSec + 's)…');
  for (var i = 0; i < maxSec / 2; i++) {
    try {
      var st = await fetch('/mp_status').then(function(r) { return r.json(); });
      document.getElementById('liveConf').textContent = 'Préparation IA: ' + st.done + '/' + st.total + '…';
      if (st.ready) {
        appLog('ok', 'Serveur prêt: ' + st.done + '/' + st.total + ' fichiers (assertion WASM neutralisée)');
        return true;
      }
    } catch(e) { appLog('warn', '/mp_status injoignable: ' + e.message); }
    await new Promise(function(r) { setTimeout(r, 2000); });
  }
  appLog('warn', 'Délai ' + maxSec + 's dépassé — fichiers serveur non prêts');
  return false;
}

async function ensureMP() {
  if (_mpLoaded) return;
  appLog('info', '── Chargement MediaPipe Hands v0.4.1646424915 ──');
  document.getElementById('liveConf').textContent = 'Chargement du modèle IA…';
  document.getElementById('mpPill').className = 'mp-pill loading';
  document.getElementById('mpPill').textContent = '⏳ Chargement…';

  try {
    var ok = await _waitServerReady(180);
    if (ok) {
      appLog('info', 'Chargement hands.js depuis /mp/ (auto-hébergé)…');
      await _loadScript('/mp/hands.js');
      appLog('info', 'Chargement drawing_utils.js depuis /mp/…');
      await _loadScript('/mp/drawing_utils.js');
      _useLocal = true; _mpLoaded = true;
      document.getElementById('mpPill').className = 'mp-pill ready';
      document.getElementById('mpPill').textContent = '✓ IA prête';
      appLog('ok', 'MediaPipe chargé en local ✓ — pas de CORS, WASM patché');
      return;
    }
  } catch(e) {
    appLog('warn', 'Chargement local échoué: ' + e.message);
  }

  // CDN fallback — pinned version, same as local
  appLog('warn', 'Fallback vers CDN unpkg (version 0.4.1646424915)…');
  appLog('warn', 'ATTENTION: WASM non patché — des crashs peuvent survenir selon le navigateur');
  document.getElementById('liveConf').textContent = 'Fallback CDN en cours…';
  try {
    await _loadScript('https://unpkg.com/@mediapipe/hands@0.4.1646424915/hands.js');
    await _loadScript('https://unpkg.com/@mediapipe/drawing_utils@0.3.1620248257/drawing_utils.js');
    _useLocal = false; _mpLoaded = true;
    document.getElementById('mpPill').className = 'mp-pill ready';
    document.getElementById('mpPill').textContent = '✓ CDN (fallback)';
    appLog('ok', 'MediaPipe chargé via CDN unpkg (fallback)');
  } catch(e) {
    document.getElementById('mpPill').className = 'mp-pill error';
    document.getElementById('mpPill').textContent = '✗ Erreur IA';
    appLog('err', 'ÉCHEC TOTAL MediaPipe — détection impossible: ' + e.message);
    throw e;
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

function _allSigns() { return SIGNS.concat(BIMANUAL_SIGNS); }

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
var mpH = null, rafId = null, stream = null, running = false;
var holdKey = null, holdStart = 0, cooldownUntil = 0;
var sentence = [], _sentenceObjs = [], debugOn = false;
var _errCount = 0;
var _inactivityTimer = null, _phraseCompleteTimer = null;
var HOLD_MS = 1000;
// hold ring circumference: 2π × r18 ≈ 113
var HOLD_CIRC = 113;
var HAND_COLOURS = [['#6366f1','#7c3aed'],['#22c55e','#059669']];

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

  mpH = new Hands({
    locateFile: function(f) {
      // SIMD absent → redirect vers équivalent non-SIMD
      if (!simdOk && f.indexOf('simd_wasm_bin') !== -1) {
        f = f.replace('simd_wasm_bin', 'wasm_bin');
      }
      // CDN mode: retourner Blob URL patché si disponible
      if (patchedUrls[f]) return patchedUrls[f];
      return _useLocal
        ? '/mp/' + f
        : 'https://unpkg.com/@mediapipe/hands@0.4.1646424915/' + f;
    }
  });

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
  document.getElementById('cvs').getContext('2d').clearRect(0, 0, 9999, 9999);
  appLog('info', 'Caméra et modèle arrêtés');
  _resetCamUI();
}

function _resetCamUI() {
  document.getElementById('btnStart').style.display  = 'inline-flex';
  document.getElementById('btnStop').style.display   = 'none';
  document.getElementById('idleOverlay').style.display = 'flex';
  document.getElementById('vidOverlay').style.display  = 'none';
  document.getElementById('holdRing').style.display    = 'none';
  document.getElementById('liveSign').textContent = '—';
  document.getElementById('heroEmoji').textContent = '🤷';
  document.getElementById('heroSign').textContent  = 'En attente…';
  document.getElementById('heroEn').textContent    = 'Activez la caméra';
  document.getElementById('confFill').style.width  = '0%';
  holdKey = null; holdStart = 0;
}

/* ── DETECTION HANDLER ────────────────────────────────── */
function _onDetect(sign, conf, fingers) {
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
    return render_template_string(HTML)

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
