#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os, time

app = Flask(__name__)
CORS(app)

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
    # French
    'je':'IX-1','tu':'IX-2','il':'IX-3','elle':'IX-3','nous':'IX-1PL',
    'vais':'FUTURE','manger':'EAT','veux':'WANT','aller':'GO',
    'pomme':'APPLE','demain':'TOMORROW','bonjour':'HI','merci':'THANK',
    'oui':'YES','non':'NO','bon':'GOOD','eau':'WATER',
}
SKIP = {
    'a','an','the','is','are','was','were','be','been','to','of','in','on',
    'at','by','for','with','that','this','it','very','just','and','or','but',
    'have','has','had','le','la','les','un','une','des','du','de','et','ou',
    'est','que','ce','se','lui','y','en','sur','avec','par',
}
TIME_GLOSSES = {'FUTURE','TOMORROW','TODAY','PAST','NOW'}
SIGN_DESC = {
    'IX-1':{'handshape':'Index pointé','location':'Poitrine','movement':'Pointer vers soi'},
    'IX-2':{'handshape':'Index pointé','location':'Vers interlocuteur','movement':'Pointer vers la personne'},
    'FUTURE':{'handshape':'Main ouverte paume gauche','location':'Côté visage','movement':'Avancer la main'},
    'TOMORROW':{'handshape':'Main-A','location':'Joue','movement':'Arc vers l\'avant'},
    'HI':{'handshape':'Main-B ouverte','location':'Front','movement':'Agiter vers l\'extérieur'},
    'THANK':{'handshape':'Main plate','location':'Menton','movement':'Avancer vers la personne'},
    'YES':{'handshape':'Poing (S)','location':'Devant soi','movement':'Hocher le poing'},
    'NO':{'handshape':'Index+Majeur tendus','location':'Devant soi','movement':'Fermer les doigts'},
    'WANT':{'handshape':'Mains courbées paumes haut','location':'Devant soi','movement':'Tirer vers soi'},
    'LOVE':{'handshape':'Bras croisés poings','location':'Poitrine','movement':'Croiser les bras'},
    'GOOD':{'handshape':'Main ouverte paume haut','location':'Menton','movement':'Avancer dans l\'autre paume'},
    'EAT':{'handshape':'Main-O plate','location':'Bouche','movement':'Toucher les doigts à la bouche'},
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
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Traducteur LSF</title>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:1.5rem}
.app{max-width:1000px;margin:0 auto;background:#fff;border-radius:16px;box-shadow:0 24px 64px rgba(0,0,0,.3);overflow:hidden}
header{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:1.25rem 2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem}
header h1{font-size:22px}
.tabs{display:flex;gap:.5rem}
.tbtn{padding:.45rem 1.1rem;border:2px solid rgba(255,255,255,.4);background:rgba(255,255,255,.15);color:#fff;border-radius:8px;cursor:pointer;font-weight:700;font-size:13px;transition:all .2s}
.tbtn.active{background:#fff;color:#667eea}
.pane{display:none;padding:1.75rem}
.pane.active{display:block}

/* TEXT TAB */
.controls{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.25rem}
.cg{display:flex;flex-direction:column}
label{font-size:11px;font-weight:800;color:#666;margin-bottom:5px;text-transform:uppercase;letter-spacing:.05em}
select,textarea{padding:.7rem;border:1.5px solid #e0e0e0;border-radius:8px;font:inherit;font-size:14px;transition:border-color .2s}
select:focus,textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.12)}
textarea{grid-column:1/-1;resize:vertical;min-height:90px}
.brow{display:flex;gap:1rem;margin-bottom:1.25rem}
button{flex:1;padding:.75rem;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:700;transition:all .18s}
.btgo{background:#667eea;color:#fff}.btgo:hover:not(:disabled){background:#5568d3}.btgo:disabled{background:#b0b8e8;cursor:not-allowed}
.btsm{background:#f5f5f5;color:#555;border:1.5px solid #e0e0e0;flex:.3}
.res{display:none}.res.active{display:block}
hr{border:none;border-top:2px solid #f0f0f0;margin:1.25rem 0}
.sec{margin-bottom:1.5rem}
.stitle{font-size:11px;font-weight:800;color:#999;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.65rem;padding-bottom:.4rem;border-bottom:2px solid #f0f0f0}
.grow{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;margin-bottom:.4rem}
.gt{background:#667eea;color:#fff;padding:.38rem .9rem;border-radius:999px;font-size:13px;font-weight:700;cursor:pointer;transition:all .15s}
.gt:hover{background:#5568d3;transform:translateY(-1px)}.gt.sel{background:#764ba2}
.scard{display:none;background:linear-gradient(135deg,#f8f6ff,#ede8ff);border:1.5px solid #d4caf0;border-radius:12px;padding:1rem;margin-top:.6rem}
.scard.active{display:block}.scard h4{color:#667eea;font-size:16px;margin-bottom:.65rem}
.sprops{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem}
.sp{background:#fff;border-radius:8px;padding:.6rem;border:1px solid #e4dcf8}
.spl{font-size:10px;font-weight:800;text-transform:uppercase;color:#bbb;margin-bottom:3px}
.spv{font-size:12px;color:#333;line-height:1.4}
.gbox{background:#f9f9fb;border-radius:10px;padding:.85rem 1rem;border:1.5px solid #eee}
.gr{display:flex;gap:.75rem;margin-bottom:.35rem}.gr:last-child{margin-bottom:0}
.gl{font-size:11px;font-weight:700;color:#bbb;width:60px;flex-shrink:0;text-transform:uppercase;margin-top:2px}
.gv{font-size:13px;color:#333;line-height:1.5}
.bs{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700}
.bs-s{background:#e6f4ea;color:#1e6b2e}.bs-q{background:#fff3e0;color:#c45700}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:.65rem}
.metric{background:#f9f9fb;border-radius:10px;padding:.8rem;text-align:center;border:1.5px solid #eee}
.mv{font-size:20px;font-weight:800;color:#667eea}.ml{font-size:10px;color:#aaa;margin-top:3px;text-transform:uppercase;font-weight:700}

/* CAMERA TAB */
.cam-grid{display:grid;grid-template-columns:1fr 320px;gap:1.5rem}
.vid-wrap{position:relative;background:#111;border-radius:12px;overflow:hidden;aspect-ratio:4/3}
#vid{width:100%;height:100%;object-fit:cover;transform:scaleX(-1);display:block}
#cvs{position:absolute;inset:0;width:100%;height:100%;transform:scaleX(-1)}
.vid-overlay{position:absolute;bottom:0;left:0;right:0;padding:.75rem 1rem;background:linear-gradient(transparent,rgba(0,0,0,.75));display:flex;align-items:flex-end;justify-content:space-between}
.live-sign{font-size:26px;font-weight:900;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.5)}
.live-conf{font-size:11px;color:rgba(255,255,255,.7);margin-top:2px}
.timer-ring{width:40px;height:40px}
.timer-ring svg{transform:rotate(-90deg)}
.timer-ring circle{fill:none;stroke:#22c55e;stroke-width:4;stroke-dasharray:100;stroke-dashoffset:100;transition:stroke-dashoffset .08s linear;stroke-linecap:round}

/* Panel */
.panel h3{font-size:12px;font-weight:800;color:#555;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.65rem}
.det-box{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-radius:12px;padding:1rem;text-align:center;margin-bottom:1rem}
.det-sign{font-size:38px;font-weight:900;margin-bottom:3px}
.det-sub{font-size:11px;opacity:.8}
.sentence{background:#f9f9fb;border:1.5px solid #eee;border-radius:10px;padding:.85rem;min-height:70px;font-size:15px;color:#333;font-weight:600;line-height:1.6;word-break:break-word;margin-bottom:.75rem}
.sentence.empty{color:#bbb;font-weight:400;font-size:13px}
.cbtns{display:flex;gap:.6rem;margin-bottom:1rem}
.cb{flex:1;padding:.65rem;border:none;border-radius:8px;cursor:pointer;font-size:13px;font-weight:700;transition:all .15s}
.cb-go{background:#22c55e;color:#fff}.cb-go:hover{background:#16a34a}
.cb-stop{background:#ef4444;color:#fff;display:none}.cb-stop:hover{background:#dc2626}
.cb-cl{background:#f5f5f5;color:#555;border:1.5px solid #e0e0e0;flex:.55}

/* Sign reference grid */
.ref-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.4rem}
.ref-item{background:#f8f6ff;border:1.5px solid #e4dcf8;border-radius:8px;padding:.4rem .5rem;text-align:center;font-size:11px}
.ref-emoji{font-size:18px;display:block;margin-bottom:2px}
.ref-label{font-weight:700;color:#667eea;font-size:10px}
.ref-desc{color:#888;font-size:9px;line-height:1.3;margin-top:2px}

.spin{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,.4);border-top-color:#fff;border-radius:50%;animation:rot .7s linear infinite;vertical-align:middle}
@keyframes rot{to{transform:rotate(360deg)}}
.dbg{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.6);color:#0f0;font-size:11px;font-family:monospace;padding:6px 8px;border-radius:6px;line-height:1.6;display:none}
@media(max-width:720px){body{padding:0}.app{border-radius:0}.pane{padding:1rem}.controls{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}.sprops{grid-template-columns:1fr}.cam-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="app">
<header>
  <div><h1>🤟 Traducteur Langue des Signes</h1><p style="font-size:12px;opacity:.8">Texte → Glosses LSF &nbsp;|&nbsp; Caméra → Mots en temps réel</p></div>
  <div class="tabs">
    <button class="tbtn active" onclick="switchTab('text',this)">📝 Texte</button>
    <button class="tbtn"        onclick="switchTab('cam',this)">📷 Caméra</button>
  </div>
</header>

<!-- ═══ TEXT ═══ -->
<div id="pane-text" class="pane active">
  <div class="controls">
    <div class="cg"><label>Langue source</label>
      <select id="srcLang"><option value="english">English</option><option value="french">Français</option></select></div>
    <div class="cg"><label>Langue des signes</label>
      <select id="tgtSign"><option value="LSF">LSF — Française</option><option value="ASL">ASL — Américaine</option><option value="BSL">BSL — Britannique</option></select></div>
    <textarea id="inputText" placeholder="Ex : Je vais manger une pomme demain"></textarea>
  </div>
  <div class="brow">
    <button class="btgo" id="btnT" onclick="doTranslate()">🔤 TRADUIRE</button>
    <button class="btsm" onclick="clearText()">✕</button>
  </div>
  <div id="textRes" class="res">
    <hr>
    <div class="sec"><div class="stitle">Glosses</div>
      <div class="grow" id="glossRow"></div>
      <div class="scard" id="scard"><h4 id="scGloss"></h4><div class="sprops" id="scProps"></div></div>
      <p style="font-size:11px;color:#bbb;margin-top:.4rem">👆 Cliquez un gloss pour voir comment faire le signe</p>
    </div>
    <div class="sec"><div class="stitle">Grammaire</div>
      <div class="gbox">
        <div class="gr"><span class="gl">Type</span><span id="gType"></span></div>
        <div class="gr"><span class="gl">Notes</span><span class="gv" id="gNotes"></span></div>
      </div>
    </div>
    <div class="sec"><div class="stitle">Stats</div>
      <div class="metrics">
        <div class="metric"><div class="mv" id="mG">—</div><div class="ml">Glosses</div></div>
        <div class="metric"><div class="mv" id="mW">—</div><div class="ml">Mots</div></div>
        <div class="metric"><div class="mv" id="mC">—</div><div class="ml">Confiance</div></div>
        <div class="metric"><div class="mv" id="mT">—</div><div class="ml">Temps</div></div>
      </div>
    </div>
  </div>
</div>

<!-- ═══ CAMERA ═══ -->
<div id="pane-cam" class="pane">
  <div class="cam-grid">
    <div>
      <div class="vid-wrap">
        <video id="vid" autoplay muted playsinline></video>
        <canvas id="cvs"></canvas>
        <div class="dbg" id="dbg"></div>
        <div class="vid-overlay">
          <div>
            <div class="live-sign" id="liveSign">—</div>
            <div class="live-conf" id="liveConf">Activez la caméra</div>
          </div>
          <div class="timer-ring" id="tring" style="display:none">
            <svg width="40" height="40" viewBox="0 0 40 40">
              <circle cx="20" cy="20" r="16" id="tcircle"/>
            </svg>
          </div>
        </div>
      </div>
      <p style="font-size:11px;color:#888;margin-top:.5rem">
        💡 Maintenez le signe <strong>1 seconde</strong> pour l'ajouter à la phrase.
        Activez le débogage pour voir les valeurs brutes.
        <button onclick="toggleDebug()" style="font-size:10px;padding:2px 6px;border:1px solid #ddd;border-radius:4px;background:#f5f5f5;cursor:pointer;margin-left:4px">Debug</button>
      </p>
    </div>

    <div class="panel">
      <h3>Signe détecté</h3>
      <div class="det-box">
        <div class="det-sign" id="panSign">—</div>
        <div class="det-sub" id="panSub">Montrez un signe à la caméra</div>
      </div>

      <h3>Phrase construite</h3>
      <div class="sentence empty" id="sentBox">Les mots reconnus apparaîtront ici…</div>

      <div class="cbtns">
        <button class="cb cb-go"   id="btnStart" onclick="startCam()">▶ Démarrer</button>
        <button class="cb cb-stop" id="btnStop"  onclick="stopCam()">■ Arrêter</button>
        <button class="cb cb-cl"   onclick="clearSent()">✕ Effacer</button>
      </div>

      <h3 style="margin-bottom:.5rem">Signes reconnus</h3>
      <div class="ref-grid" id="refGrid"></div>
    </div>
  </div>
</div>
</div>

<script>
/* ─── Tabs ─────────────────────────────────────────────────── */
function switchTab(name, btn) {
  document.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tbtn').forEach(b => b.classList.remove('active'));
  document.getElementById('pane-' + name).classList.add('active');
  btn.classList.add('active');
}

/* ─── Text → Glosses ────────────────────────────────────────── */
let signDescs = {};
async function doTranslate() {
  const text = document.getElementById('inputText').value.trim();
  if (!text) { alert('Entrez du texte'); return; }
  const btn = document.getElementById('btnT');
  btn.disabled = true; btn.innerHTML = '<span class="spin"></span> Traduction…';
  try {
    const r = await fetch('/api/translate', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ text, language: document.getElementById('srcLang').value,
                              target: document.getElementById('tgtSign').value })
    });
    renderGlosses(await r.json(), text);
  } catch(e) { alert('Erreur: ' + e.message); }
  finally { btn.disabled = false; btn.innerHTML = '🔤 TRADUIRE'; }
}
function renderGlosses(d, orig) {
  signDescs = {};
  (d.sign_descriptions||[]).forEach(s => signDescs[s.gloss] = s);
  const row = document.getElementById('glossRow');
  row.innerHTML = '';
  d.glosses.forEach((g,i) => {
    const s = document.createElement('span');
    s.className = 'gt'; s.textContent = g;
    s.onclick = () => showCard(g, s);
    row.appendChild(s);
    if (i < d.glosses.length-1) {
      const a = document.createElement('span');
      a.style.cssText='color:#ccc;font-size:13px'; a.textContent='→'; row.appendChild(a);
    }
  });
  const isQ = (d.grammar||'').toLowerCase().includes('quest');
  document.getElementById('gType').innerHTML=`<span class="bs ${isQ?'bs-q':'bs-s'}">${d.grammar||'Énoncé'}</span>`;
  document.getElementById('gNotes').textContent = d.grammar_notes||'—';
  document.getElementById('mG').textContent = d.glosses.length;
  document.getElementById('mW').textContent = orig.trim().split(/\s+/).length;
  document.getElementById('mC').textContent = (d.confidence||88)+'%';
  document.getElementById('mT').textContent = (d.time||0)+'ms';
  document.getElementById('scard').classList.remove('active');
  document.getElementById('textRes').classList.add('active');
}
function showCard(g, el) {
  document.querySelectorAll('.gt').forEach(t=>t.classList.remove('sel'));
  el.classList.add('sel');
  const s = signDescs[g];
  document.getElementById('scGloss').textContent = g;
  const p = document.getElementById('scProps');
  p.innerHTML = s
    ? `<div class="sp"><div class="spl">✋ Forme</div><div class="spv">${s.handshape}</div></div>
       <div class="sp"><div class="spl">📍 Position</div><div class="spv">${s.location}</div></div>
       <div class="sp"><div class="spl">↔️ Mouvement</div><div class="spv">${s.movement}</div></div>`
    : `<div class="sp" style="grid-column:1/-1"><div class="spl">Info</div><div class="spv">Pas de description pour <strong>${g}</strong>.</div></div>`;
  document.getElementById('scard').classList.add('active');
}
function clearText() {
  document.getElementById('inputText').value='';
  document.getElementById('textRes').classList.remove('active');
}
document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('inputText').addEventListener('keydown',e=>{if(e.key==='Enter'&&e.ctrlKey)doTranslate()});
  buildRefGrid();
});

/* ═══════════════════════════════════════════════════════════════
   CAMERA SIGN RECOGNITION
═══════════════════════════════════════════════════════════════ */

// ── Sign dictionary (LSF-labelled) ─────────────────────────────
const SIGNS = [
  { key:'BONJOUR', emoji:'👋', fr:'BONJOUR',      en:'Hello',       fingers:[1,1,1,1,1], thumbNeeded:true,  desc:'Main ouverte, 5 doigts levés' },
  { key:'OUI',     emoji:'✊', fr:'OUI',           en:'Yes',         fingers:[0,0,0,0,0], thumbNeeded:false, desc:'Poing fermé, tous les doigts pliés' },
  { key:'BIEN',    emoji:'👍', fr:'BIEN',          en:'Good',        fingers:[0,0,0,0,0], thumbNeeded:true, thumbDir:'up', desc:'Pouce levé, autres doigts fermés' },
  { key:'MAUVAIS', emoji:'👎', fr:'MAUVAIS',       en:'Bad',         fingers:[0,0,0,0,0], thumbNeeded:true, thumbDir:'down', desc:'Pouce baissé, autres doigts fermés' },
  { key:'JE_TAIME',emoji:'🤟', fr:'JE T\'AIME',   en:'I Love You',  fingers:[1,0,0,1], thumbNeeded:true, desc:'Pouce + Index + Auriculaire levés' },
  { key:'PAIX',    emoji:'✌️', fr:'PAIX / DEUX',  en:'Peace / Two', fingers:[0,1,1,0,0], thumbNeeded:false, desc:'Index + Majeur levés (V)' },
  { key:'UN',      emoji:'☝️', fr:'UN',            en:'One',         fingers:[0,1,0,0,0], thumbNeeded:false, desc:'Seulement l\'index levé' },
  { key:'TROIS',   emoji:'3️⃣', fr:'TROIS',        en:'Three',       fingers:[0,1,1,1,0], thumbNeeded:false, desc:'Index + Majeur + Annulaire' },
  { key:'QUATRE',  emoji:'🖐', fr:'QUATRE',        en:'Four',        fingers:[0,1,1,1,1], thumbNeeded:false, desc:'4 doigts levés, pouce fermé' },
  { key:'APPELER', emoji:'🤙', fr:'APPELER',       en:'Call Me',     fingers:[0,0,0,0,1], thumbNeeded:true,  desc:'Pouce + Auriculaire levés (Y)' },
  { key:'ROCK',    emoji:'🤘', fr:'ROCK',          en:'Rock',        fingers:[0,1,0,0,1], thumbNeeded:false, desc:'Index + Auriculaire levés' },
  { key:'OK',      emoji:'👌', fr:'OK',            en:'OK',          fingers:[0,0,1,1,1], thumbNeeded:true,  desc:'Pouce + Annulaire + Auriculaire' },
];

function buildRefGrid() {
  const g = document.getElementById('refGrid');
  SIGNS.forEach(s => {
    g.innerHTML += `<div class="ref-item">
      <span class="ref-emoji">${s.emoji}</span>
      <span class="ref-label">${s.fr}</span>
      <span class="ref-desc">${s.desc}</span>
    </div>`;
  });
}

// ── Finger state detection ──────────────────────────────────────
function dist2(a,b){ return Math.sqrt((a.x-b.x)**2+(a.y-b.y)**2); }

function getStates(lm) {
  // Use distance from wrist: tip farther than pip → extended
  // Multiply by 1.05 as tolerance
  const w = lm[0];
  const index  = dist2(lm[8],w)  > dist2(lm[6],w)  * 1.05;
  const middle = dist2(lm[12],w) > dist2(lm[10],w) * 1.05;
  const ring   = dist2(lm[16],w) > dist2(lm[14],w) * 1.05;
  const pinky  = dist2(lm[20],w) > dist2(lm[18],w) * 1.05;

  // Thumb: tip far from index MCP = extended
  const palmSz = dist2(lm[0], lm[9]);
  const thumbDist = dist2(lm[4], lm[5]);
  const thumb = thumbDist > palmSz * 0.5;

  // Thumb direction for thumbs up / down
  const thumbUp   = lm[4].y < lm[2].y - 0.03;
  const thumbDown = lm[4].y > lm[2].y + 0.03;

  return { thumb, thumbUp, thumbDown, index, middle, ring, pinky, palmSz, thumbDist };
}

function classify(lm) {
  const f = getStates(lm);
  const fi = [f.index, f.middle, f.ring, f.pinky]; // 4 finger states

  // Helper: match finger pattern (1=must be up, 0=must be down, -1=any)
  function match(pat, needThumb, thumbDir) {
    for (let i=0; i<4; i++) {
      if (pat[i]===1 && !fi[i]) return false;
      if (pat[i]===0 && fi[i])  return false;
    }
    if (needThumb !== undefined) {
      if (needThumb && !f.thumb) return false;
      if (!needThumb && f.thumb) return false;
    }
    if (thumbDir === 'up'   && !f.thumbUp)   return false;
    if (thumbDir === 'down' && !f.thumbDown) return false;
    return true;
  }

  for (const s of SIGNS) {
    const pat = s.fingers; // may have 4 or 5 values
    const p4 = pat.length === 5 ? pat.slice(1) : pat; // use last 4 for fingers
    const needThumb = pat.length === 5 ? !!pat[0] : s.thumbNeeded;
    if (match(p4, needThumb, s.thumbDir)) {
      return { sign: s, conf: 82 };
    }
  }
  return { sign: null, conf: 0 };
}

// ── Camera logic ────────────────────────────────────────────────
let mpH = null, mpCam = null, stream = null, running = false;
let holdKey = null, holdStart = 0, cooldownUntil = 0;
const HOLD_MS = 1000;
let sentence = [];
let debugOn = false;

function toggleDebug() {
  debugOn = !debugOn;
  document.getElementById('dbg').style.display = debugOn ? 'block' : 'none';
}

async function startCam() {
  document.getElementById('btnStart').style.display = 'none';
  document.getElementById('btnStop').style.display  = 'block';
  document.getElementById('liveConf').textContent = 'Chargement MediaPipe…';

  const vid = document.getElementById('vid');
  const cvs = document.getElementById('cvs');
  const ctx = cvs.getContext('2d');

  try {
    stream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:'user',width:640,height:480 }});
    vid.srcObject = stream;
    await new Promise(r => { vid.onloadedmetadata = r; });
    cvs.width = vid.videoWidth; cvs.height = vid.videoHeight;
  } catch(e) { alert('Caméra refusée: ' + e.message); resetUI(); return; }

  mpH = new Hands({ locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}` });
  mpH.setOptions({ maxNumHands:1, modelComplexity:0, minDetectionConfidence:.55, minTrackingConfidence:.4 });

  mpH.onResults(res => {
    ctx.clearRect(0, 0, cvs.width, cvs.height);
    if (res.multiHandLandmarks?.length) {
      const lm = res.multiHandLandmarks[0];
      drawConnectors(ctx, lm, HAND_CONNECTIONS, { color:'#667eea', lineWidth:2 });
      drawLandmarks(ctx,  lm, { color:'#fff', fillColor:'#764ba2', radius:3 });

      const { sign, conf } = classify(lm);

      if (debugOn) {
        const f = getStates(lm);
        document.getElementById('dbg').innerHTML =
          `T:${+f.thumb} I:${+f.index} M:${+f.middle} R:${+f.ring} P:${+f.pinky}<br>`+
          `thumbUp:${+f.thumbUp} dn:${+f.thumbDown}<br>`+
          `thumbDist:${f.thumbDist.toFixed(3)} palm:${f.palmSz.toFixed(3)}<br>`+
          `→ ${sign ? sign.fr : '—'}`;
      }
      onDetect(sign, conf);
    } else {
      onDetect(null, 0);
      if (debugOn) document.getElementById('dbg').innerHTML = 'Aucune main détectée';
    }
  });

  running = true;
  mpCam = new Camera(vid, {
    onFrame: async () => { if (running) await mpH.send({ image: vid }); },
    width:640, height:480
  });
  await mpCam.start();
  document.getElementById('liveConf').textContent = '✅ MediaPipe actif — montrez un signe !';
}

function stopCam() {
  running = false;
  if (mpCam)   { mpCam.stop(); mpCam = null; }
  if (mpH)     { mpH.close(); mpH = null; }
  if (stream)  { stream.getTracks().forEach(t=>t.stop()); stream = null; }
  document.getElementById('cvs').getContext('2d').clearRect(0,0,9999,9999);
  resetUI();
}

function resetUI() {
  document.getElementById('btnStart').style.display = 'block';
  document.getElementById('btnStop').style.display  = 'none';
  document.getElementById('liveSign').textContent = '—';
  document.getElementById('liveConf').textContent = 'Activez la caméra';
  document.getElementById('panSign').textContent  = '—';
  document.getElementById('panSub').textContent   = 'Montrez un signe à la caméra';
  document.getElementById('tring').style.display  = 'none';
}

function onDetect(sign, conf) {
  const now = Date.now();
  const inCooldown = now < cooldownUntil;

  // Update live display always
  if (sign) {
    document.getElementById('liveSign').textContent = sign.emoji + ' ' + sign.fr;
    document.getElementById('liveConf').textContent = `Confiance : ${conf}%`;
    document.getElementById('panSign').textContent  = sign.emoji + ' ' + sign.fr;
  } else {
    document.getElementById('liveSign').textContent = '—';
    document.getElementById('liveConf').textContent = 'Aucun signe détecté';
    document.getElementById('panSign').textContent  = '—';
    holdKey = null; holdStart = 0;
    document.getElementById('tring').style.display = 'none';
    return;
  }

  if (inCooldown) {
    document.getElementById('panSub').textContent = '✅ Ajouté ! Montrez le prochain signe…';
    document.getElementById('tring').style.display = 'none';
    return;
  }

  // Hold timer
  if (sign.key !== holdKey) {
    holdKey = sign.key; holdStart = now;
    document.getElementById('tring').style.display = 'block';
  }

  const elapsed = now - holdStart;
  const progress = Math.min(elapsed / HOLD_MS, 1);
  const dashOffset = 100 * (1 - progress);
  document.getElementById('tcircle').style.strokeDashoffset = dashOffset;

  if (progress >= 1) {
    // ✅ Confirmed!
    sentence.push(sign.fr);
    const box = document.getElementById('sentBox');
    box.classList.remove('empty');
    box.textContent = sentence.join('  ›  ');
    cooldownUntil = now + 1500;
    holdKey = null; holdStart = 0;
    document.getElementById('tring').style.display = 'none';
    document.getElementById('panSub').textContent = '✅ Ajouté !';
  } else {
    const rem = ((HOLD_MS - elapsed)/1000).toFixed(1);
    document.getElementById('panSub').textContent = `Maintenez… ${rem}s`;
  }
}

function clearSent() {
  sentence = [];
  const box = document.getElementById('sentBox');
  box.classList.add('empty');
  box.textContent = 'Les mots reconnus apparaîtront ici…';
  holdKey = null; holdStart = 0;
  cooldownUntil = 0;
}
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text','').strip()
    language = data.get('language','french')
    target = data.get('target','LSF')
    start = time.time()
    result = translate_with_slt(text, language, target) or translate_fallback(text, language)
    return jsonify({
        'glosses': result['glosses'],
        'grammar': result['grammar_type'],
        'grammar_notes': result.get('grammar_notes',''),
        'sign_descriptions': result.get('sign_descriptions',[]),
        'confidence': 88,
        'time': int((time.time()-start)*1000),
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
