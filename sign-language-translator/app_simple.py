#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os, time

app = Flask(__name__)
CORS(app)

SIGN_MAP = {
    'i':'IX-1','me':'IX-1','my':'IX-1','mine':'IX-1',
    'we':'IX-1PL','us':'IX-1PL','our':'IX-1PL',
    'you':'IX-2','your':'IX-2','yours':'IX-2',
    'he':'IX-3','she':'IX-3','him':'IX-3','her':'IX-3',
    'they':'IX-3PL','them':'IX-3PL','their':'IX-3PL',
    'will':'FUTURE',"i'll":'FUTURE',"we'll":'FUTURE',"you'll":'FUTURE',
    'tomorrow':'TOMORROW','today':'TODAY','yesterday':'PAST',
    'now':'NOW','later':'LATER','soon':'SOON',
    'hello':'HI','hi':'HI','hey':'HI',
    'thank':'THANK','thanks':'THANK',
    'yes':'YES','yeah':'YES','no':'NO','nope':'NO',
    'please':'PLEASE','sorry':'SORRY',
    'want':'WANT','like':'LIKE','love':'LOVE','need':'NEED',
    'go':'GO','goes':'GO','going':'GO',
    'come':'COME','comes':'COME','coming':'COME',
    'eat':'EAT','eats':'EAT','eating':'EAT','ate':'EAT',
    'drink':'DRINK','drinks':'DRINK','drinking':'DRINK',
    'sleep':'SLEEP','sleeping':'SLEEP',
    'work':'WORK','works':'WORK','working':'WORK',
    'know':'KNOW','think':'THINK','see':'SEE','help':'HELP',
    'stop':'STOP','finish':'FINISH','done':'FINISH',
    'good':'GOOD','bad':'BAD','happy':'HAPPY','sad':'SAD',
    'home':'HOME','school':'SCHOOL','movie':'MOVIE','cinema':'MOVIE',
    'apple':'APPLE','water':'WATER','food':'FOOD',
    'where':'WHERE','when':'WHEN','what':'WHAT','who':'WHO','how':'HOW','why':'WHY',
    'do':'DO','name':'NAME','again':'AGAIN','more':'MORE',
    'can':'CAN','not':'NOT','friend':'FRIEND','family':'FAMILY',
    # French
    'je':'IX-1','tu':'IX-2','il':'IX-3','elle':'IX-3','nous':'IX-1PL',
    'vais':'FUTURE','manger':'EAT','veux':'WANT','aller':'GO',
    'pomme':'APPLE','demain':'TOMORROW','bonjour':'HI','merci':'THANK',
    'oui':'YES','non':'NO','bon':'GOOD','eau':'WATER',
    'où':'WHERE','quand':'WHEN','quoi':'WHAT','qui':'WHO','comment':'HOW',
}
SKIP = {
    'a','an','the','is','are','was','were','be','been','being',
    'to','of','in','on','at','by','for','with','that','this','it',
    'very','just','also','so','and','or','but','have','has','had',
    'le','la','les','un','une','des','du','de','au','et','ou','est','que','ce','se',
}
TIME_GLOSSES = {'FUTURE','TOMORROW','TODAY','PAST','NOW','LATER','SOON'}
SIGN_DESC = {
    'IX-1':{'handshape':'Index finger pointing','location':'Your chest','movement':'Point to yourself'},
    'IX-2':{'handshape':'Index finger pointing','location':'Toward listener','movement':'Point at them'},
    'FUTURE':{'handshape':'Open hand, palm left','location':'Side of face','movement':'Move forward from face'},
    'TOMORROW':{'handshape':'A-handshape','location':'Cheek','movement':'Arc hand forward'},
    'TODAY':{'handshape':'Both Y-hands palms up','location':'Front of body','movement':'Drop hands down twice'},
    'HI':{'handshape':'Open B-hand','location':'Forehead','movement':'Wave outward'},
    'THANK':{'handshape':'Flat hand','location':'Chin/lips','movement':'Move forward toward person'},
    'YES':{'handshape':'S-handshape (fist)','location':'Front of body','movement':'Nod fist up and down'},
    'NO':{'handshape':'Index+middle extended','location':'Front of body','movement':'Snap fingers closed'},
    'WANT':{'handshape':'Curved hands palms up','location':'Front of body','movement':'Pull both hands toward you'},
    'LOVE':{'handshape':'Both fists crossed','location':'Chest','movement':'Cross arms on chest'},
    'GO':{'handshape':'Both index fingers','location':'Front of body','movement':'Both hands arc forward'},
    'EAT':{'handshape':'Flat-O hand','location':'Mouth','movement':'Touch fingertips to mouth'},
    'DRINK':{'handshape':'C-handshape','location':'Mouth','movement':'Tilt toward mouth'},
    'GOOD':{'handshape':'Open hand palm up','location':'Chin','movement':'Move forward into other palm'},
    'BAD':{'handshape':'Open hand palm in','location':'Mouth','movement':'Flick outward'},
    'HAPPY':{'handshape':'Open hand palm to chest','location':'Chest','movement':'Brush upward twice'},
    'HELP':{'handshape':'A-hand on open palm','location':'Front of body','movement':'Lift open palm upward'},
    'MOVIE':{'handshape':'Open hand wiggling','location':'Front of face','movement':'Slide side to side'},
    'APPLE':{'handshape':'X-handshape','location':'Cheek','movement':'Twist at cheek'},
    'WATER':{'handshape':'W-handshape','location':'Chin','movement':'Tap chin twice'},
    'WHERE':{'handshape':'Index finger up','location':'Front','movement':'Shake side to side'},
    'WHAT':{'handshape':'Open hands palms up','location':'Front','movement':'Shrug or brush palm'},
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
        notes = f'{target_sign} grammar: articles removed'
        if time_g: notes += f', temporal first: {" ".join(time_g)}'
        return {'glosses': final or ['NO','TRANSLATION'],'grammar_type':grammar,'grammar_notes':notes,
                'sign_descriptions':[{**{'gloss':g},**SIGN_DESC[g]} for g in final if g in SIGN_DESC]}
    except Exception as e:
        print(f"SLT error: {e}")
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
            'grammar_notes':'Dictionary translation','sign_descriptions':
            [{**{'gloss':g},**SIGN_DESC[g]} for g in final if g in SIGN_DESC]}

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign Language Translator</title>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:1.5rem}
.app{max-width:960px;margin:0 auto;background:#fff;border-radius:16px;box-shadow:0 24px 64px rgba(0,0,0,.3);overflow:hidden}
header{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:1.5rem 2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem}
header h1{font-size:24px}
header p{font-size:13px;opacity:.85;margin-top:2px}
.tabs{display:flex;gap:.5rem}
.tab-btn{padding:.5rem 1.2rem;border:2px solid rgba(255,255,255,.4);background:rgba(255,255,255,.15);color:#fff;border-radius:8px;cursor:pointer;font-weight:700;font-size:13px;transition:all .2s}
.tab-btn.active{background:#fff;color:#667eea}
.tab-pane{display:none;padding:2rem}
.tab-pane.active{display:block}

/* ── TEXT TAB ─────────────────────────────────────── */
.controls{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}
.cg{display:flex;flex-direction:column}
label{font-size:11px;font-weight:800;color:#666;margin-bottom:5px;text-transform:uppercase;letter-spacing:.05em}
select,textarea{padding:.75rem;border:1.5px solid #e0e0e0;border-radius:8px;font:inherit;font-size:14px;transition:border-color .2s}
select:focus,textarea:focus{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.12)}
textarea{grid-column:1/-1;resize:vertical;min-height:100px}
.btn-row{display:flex;gap:1rem;margin-bottom:1.5rem}
button{flex:1;padding:.8rem;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:700;transition:all .18s}
.btn-go{background:#667eea;color:#fff}
.btn-go:hover:not(:disabled){background:#5568d3;transform:translateY(-1px)}
.btn-go:disabled{background:#b0b8e8;cursor:not-allowed}
.btn-sm{background:#f5f5f5;color:#555;border:1.5px solid #e0e0e0;flex:.3}
.results{display:none}
.results.active{display:block}
hr{border:none;border-top:2px solid #f0f0f0;margin:1.5rem 0}
.sec{margin-bottom:1.5rem}
.sec-title{font-size:11px;font-weight:800;color:#999;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.75rem;padding-bottom:.5rem;border-bottom:2px solid #f0f0f0}
.gloss-row{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:.5rem}
.gtag{background:#667eea;color:#fff;padding:.4rem 1rem;border-radius:999px;font-size:13px;font-weight:700;cursor:pointer;transition:all .15s}
.gtag:hover{background:#5568d3;transform:translateY(-1px)}
.gtag.sel{background:#764ba2;box-shadow:0 4px 14px rgba(118,75,162,.4)}
.hint{font-size:11px;color:#bbb;margin-top:.4rem}
.sign-card{display:none;background:linear-gradient(135deg,#f8f6ff,#ede8ff);border:1.5px solid #d4caf0;border-radius:12px;padding:1.1rem;margin-top:.75rem}
.sign-card.active{display:block}
.sign-card h4{color:#667eea;font-size:17px;margin-bottom:.75rem}
.sprops{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem}
.sprop{background:#fff;border-radius:8px;padding:.65rem;border:1px solid #e4dcf8}
.sprop-l{font-size:10px;font-weight:800;text-transform:uppercase;color:#bbb;margin-bottom:3px}
.sprop-v{font-size:12px;color:#333;line-height:1.4}
.gbox{background:#f9f9fb;border-radius:10px;padding:.9rem 1.1rem;border:1.5px solid #eee}
.gr{display:flex;gap:.75rem;margin-bottom:.4rem}
.gr:last-child{margin-bottom:0}
.gl{font-size:11px;font-weight:700;color:#bbb;width:65px;flex-shrink:0;text-transform:uppercase;margin-top:2px}
.gv{font-size:13px;color:#333;line-height:1.5}
.badge-s{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700}
.badge-st{background:#e6f4ea;color:#1e6b2e}
.badge-q{background:#fff3e0;color:#c45700}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem}
.metric{background:#f9f9fb;border-radius:10px;padding:.9rem;text-align:center;border:1.5px solid #eee}
.mval{font-size:20px;font-weight:800;color:#667eea}
.mlbl{font-size:10px;color:#aaa;margin-top:3px;text-transform:uppercase;font-weight:700}

/* ── CAMERA TAB ───────────────────────────────────── */
.cam-layout{display:grid;grid-template-columns:1fr 340px;gap:1.5rem;align-items:start}
.cam-wrap{position:relative;background:#0d0d0d;border-radius:12px;overflow:hidden;aspect-ratio:4/3}
#camVideo{width:100%;height:100%;object-fit:cover;transform:scaleX(-1);display:block}
#camCanvas{position:absolute;top:0;left:0;width:100%;height:100%;transform:scaleX(-1)}
.cam-overlay{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,.7));padding:1rem;display:flex;align-items:flex-end;justify-content:space-between}
.cam-sign-big{font-size:28px;font-weight:900;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.5)}
.cam-conf{font-size:12px;color:rgba(255,255,255,.7);margin-top:2px}
.cam-timer{width:44px;height:44px;position:relative}
.cam-timer svg{transform:rotate(-90deg)}
.cam-timer circle{fill:none;stroke:#667eea;stroke-width:4;stroke-dasharray:113;stroke-dashoffset:113;transition:stroke-dashoffset .1s linear;stroke-linecap:round}
.cam-panel{}
.cam-panel h3{font-size:13px;font-weight:800;color:#555;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.75rem}
.detected-word{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-radius:12px;padding:1.25rem;text-align:center;margin-bottom:1rem}
.detected-word .sign-name{font-size:36px;font-weight:900;margin-bottom:4px}
.detected-word .sign-sub{font-size:12px;opacity:.8}
.sentence-box{background:#f9f9fb;border:1.5px solid #eee;border-radius:10px;padding:1rem;min-height:80px;font-size:16px;color:#333;font-weight:600;line-height:1.6;word-break:break-word;margin-bottom:.75rem}
.sentence-box.empty{color:#bbb;font-weight:400;font-size:14px}
.cam-btns{display:flex;gap:.75rem}
.cbtn{flex:1;padding:.7rem;border:none;border-radius:8px;cursor:pointer;font-size:13px;font-weight:700;transition:all .15s}
.cbtn-start{background:#22c55e;color:#fff}
.cbtn-start:hover{background:#16a34a}
.cbtn-stop{background:#ef4444;color:#fff;display:none}
.cbtn-stop:hover{background:#dc2626}
.cbtn-clear{background:#f5f5f5;color:#555;border:1.5px solid #e0e0e0;flex:.6}
.cam-hint{font-size:11px;color:#aaa;margin-top:.5rem;line-height:1.5}
.loading-bar{height:3px;background:linear-gradient(90deg,#667eea,#764ba2);width:0;transition:width .3s;border-radius:3px;margin-top:.5rem}

.spin{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,.4);border-top-color:#fff;border-radius:50%;animation:rot .7s linear infinite;vertical-align:middle}
@keyframes rot{to{transform:rotate(360deg)}}
@media(max-width:700px){
  body{padding:0} .app{border-radius:0}
  .tab-pane{padding:1.25rem}
  .controls{grid-template-columns:1fr}
  .metrics{grid-template-columns:1fr 1fr}
  .sprops{grid-template-columns:1fr}
  .cam-layout{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="app">
  <header>
    <div>
      <h1>🤟 Sign Language Translator</h1>
      <p>Text → Glosses &nbsp;|&nbsp; Camera → Words (real-time)</p>
    </div>
    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('text')">📝 Text</button>
      <button class="tab-btn" onclick="switchTab('camera')">📷 Camera</button>
    </div>
  </header>

  <!-- ═══════════ TEXT TAB ═══════════ -->
  <div id="tab-text" class="tab-pane active">
    <div class="controls">
      <div class="cg"><label>Language</label>
        <select id="srcLang"><option value="english">English</option><option value="french">Français</option></select>
      </div>
      <div class="cg"><label>Sign Language</label>
        <select id="tgtSign">
          <option value="ASL">ASL — American</option>
          <option value="LSF">LSF — Française</option>
          <option value="BSL">BSL — British</option>
          <option value="ISL">ISL — Indian</option>
        </select>
      </div>
      <textarea id="inputText" placeholder="Type a sentence…  e.g.  I will eat an apple tomorrow"></textarea>
    </div>
    <div class="btn-row">
      <button class="btn-go" id="btnTranslate" onclick="doTranslate()">🔤 TRANSLATE</button>
      <button class="btn-sm" onclick="clearText()">✕</button>
    </div>
    <div id="textResults" class="results">
      <hr>
      <div class="sec">
        <div class="sec-title">Sign Language Glosses</div>
        <div class="gloss-row" id="glossRow"></div>
        <div class="sign-card" id="signCard">
          <h4 id="cardGloss"></h4>
          <div class="sprops" id="cardProps"></div>
        </div>
        <p class="hint">👆 Click a gloss to see how to perform the sign</p>
      </div>
      <div class="sec">
        <div class="sec-title">Grammar</div>
        <div class="gbox">
          <div class="gr"><span class="gl">Type</span><span id="gType"></span></div>
          <div class="gr"><span class="gl">Notes</span><span class="gv" id="gNotes"></span></div>
        </div>
      </div>
      <div class="sec">
        <div class="sec-title">Stats</div>
        <div class="metrics">
          <div class="metric"><div class="mval" id="mG">—</div><div class="mlbl">Glosses</div></div>
          <div class="metric"><div class="mval" id="mW">—</div><div class="mlbl">Words</div></div>
          <div class="metric"><div class="mval" id="mC">—</div><div class="mlbl">Confidence</div></div>
          <div class="metric"><div class="mval" id="mT">—</div><div class="mlbl">Time</div></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════ CAMERA TAB ═══════════ -->
  <div id="tab-camera" class="tab-pane">
    <div class="cam-layout">
      <!-- Video feed -->
      <div>
        <div class="cam-wrap">
          <video id="camVideo" autoplay muted playsinline></video>
          <canvas id="camCanvas"></canvas>
          <div class="cam-overlay">
            <div>
              <div class="cam-sign-big" id="liveSign">—</div>
              <div class="cam-conf" id="liveConf">Show a sign to the camera</div>
            </div>
            <div class="cam-timer" id="timerWrap" style="display:none">
              <svg width="44" height="44" viewBox="0 0 44 44">
                <circle cx="22" cy="22" r="18" id="timerCircle"/>
              </svg>
            </div>
          </div>
        </div>
        <div class="loading-bar" id="mpLoading"></div>
        <p class="cam-hint" id="camHint" style="margin-top:.6rem">Click <strong>Start Camera</strong> — MediaPipe Hands will load and detect your signs in real time.</p>
      </div>
      <!-- Side panel -->
      <div class="cam-panel">
        <h3>Detected Sign</h3>
        <div class="detected-word">
          <div class="sign-name" id="panelSign">—</div>
          <div class="sign-sub" id="panelSub">Hold sign 1.5s to add to sentence</div>
        </div>
        <h3>Sentence</h3>
        <div class="sentence-box empty" id="sentenceBox">Your recognized words will appear here…</div>
        <div class="cam-btns">
          <button class="cbtn cbtn-start" id="btnStart" onclick="startCamera()">▶ Start Camera</button>
          <button class="cbtn cbtn-stop"  id="btnStop"  onclick="stopCamera()">■ Stop</button>
          <button class="cbtn cbtn-clear" onclick="clearSentence()">✕ Clear</button>
        </div>
        <p class="cam-hint" style="margin-top:.75rem">
          Supported signs: 👋 HELLO &nbsp;✊ YES &nbsp;👍 GOOD &nbsp;❤️ I LOVE YOU &nbsp;✌️ PEACE &nbsp;☝️ ONE &nbsp;✌️ TWO &nbsp;3️⃣ THREE &nbsp;🖐 FOUR &nbsp;🤙 CALL ME &nbsp;🤟 ILY
        </p>
      </div>
    </div>
  </div>
</div>

<script>
/* ── Tab switching ─────────────────────────────────────────────── */
function switchTab(name) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
}

/* ══════════════════════════════════════════════════════════════════
   TEXT → GLOSSES
═══════════════════════════════════════════════════════════════════ */
let signDescs = {};

async function doTranslate() {
  const text = document.getElementById('inputText').value.trim();
  if (!text) { alert('Please enter text'); return; }
  const btn = document.getElementById('btnTranslate');
  btn.disabled = true; btn.innerHTML = '<span class="spin"></span> Translating…';
  try {
    const r = await fetch('/api/translate', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ text, language: document.getElementById('srcLang').value,
                              target: document.getElementById('tgtSign').value })
    });
    const d = await r.json();
    renderGlosses(d, text);
  } catch(e) { alert('Error: ' + e.message); }
  finally { btn.disabled = false; btn.innerHTML = '🔤 TRANSLATE'; }
}

function renderGlosses(d, original) {
  signDescs = {};
  (d.sign_descriptions||[]).forEach(s => signDescs[s.gloss] = s);
  const row = document.getElementById('glossRow');
  row.innerHTML = '';
  d.glosses.forEach((g, i) => {
    const s = document.createElement('span');
    s.className = 'gtag'; s.textContent = g;
    s.onclick = () => showSignCard(g, s);
    row.appendChild(s);
    if (i < d.glosses.length-1) {
      const a = document.createElement('span');
      a.style.cssText = 'color:#ccc;font-size:14px'; a.textContent = '→';
      row.appendChild(a);
    }
  });
  const isQ = (d.grammar||'').toLowerCase().includes('quest');
  document.getElementById('gType').innerHTML =
    `<span class="badge-s ${isQ?'badge-q':'badge-st'}">${d.grammar||'Statement'}</span>`;
  document.getElementById('gNotes').textContent = d.grammar_notes||'—';
  document.getElementById('mG').textContent = d.glosses.length;
  document.getElementById('mW').textContent = original.trim().split(/\s+/).length;
  document.getElementById('mC').textContent = (d.confidence||88)+'%';
  document.getElementById('mT').textContent = (d.time||0)+'ms';
  document.getElementById('signCard').classList.remove('active');
  document.getElementById('textResults').classList.add('active');
}

function showSignCard(gloss, el) {
  document.querySelectorAll('.gtag').forEach(t => t.classList.remove('sel'));
  el.classList.add('sel');
  const s = signDescs[gloss];
  document.getElementById('cardGloss').textContent = gloss;
  const props = document.getElementById('cardProps');
  if (s) {
    props.innerHTML = `
      <div class="sprop"><div class="sprop-l">✋ Handshape</div><div class="sprop-v">${s.handshape||'—'}</div></div>
      <div class="sprop"><div class="sprop-l">📍 Location</div><div class="sprop-v">${s.location||'—'}</div></div>
      <div class="sprop"><div class="sprop-l">↔️ Movement</div><div class="sprop-v">${s.movement||'—'}</div></div>`;
  } else {
    props.innerHTML = `<div class="sprop" style="grid-column:1/-1">
      <div class="sprop-l">Info</div><div class="sprop-v">No detailed description for <strong>${gloss}</strong>.</div></div>`;
  }
  document.getElementById('signCard').classList.add('active');
}

function clearText() {
  document.getElementById('inputText').value = '';
  document.getElementById('textResults').classList.remove('active');
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('inputText').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.ctrlKey) doTranslate();
  });
});

/* ══════════════════════════════════════════════════════════════════
   CAMERA → SIGN RECOGNITION
═══════════════════════════════════════════════════════════════════ */
let mpCamera = null, mpHands = null, cameraStream = null;
let holdSign = null, holdStart = 0, holdDuration = 1500;
let sentence = [];
let isRunning = false;

const SIGNS = {
  'HELLO':     { emoji:'👋', label:'HELLO',       desc:'Open palm, all 5 fingers up' },
  'YES':       { emoji:'✊', label:'YES',          desc:'Closed fist' },
  'GOOD':      { emoji:'👍', label:'GOOD',         desc:'Thumbs up' },
  'BAD':       { emoji:'👎', label:'BAD',          desc:'Thumbs down' },
  'ILY':       { emoji:'🤟', label:'I LOVE YOU',   desc:'Thumb + Index + Pinky extended' },
  'PEACE':     { emoji:'✌️', label:'PEACE / TWO',  desc:'Index + Middle extended' },
  'ONE':       { emoji:'☝️', label:'ONE',          desc:'Index finger up only' },
  'THREE':     { emoji:'3️⃣', label:'THREE',       desc:'Index + Middle + Ring' },
  'FOUR':      { emoji:'🖐', label:'FOUR',         desc:'All fingers except thumb' },
  'CALLME':    { emoji:'🤙', label:'CALL ME',      desc:'Thumb + Pinky extended (Y)' },
  'ROCK':      { emoji:'🤘', label:'ROCK',         desc:'Index + Pinky extended' },
};

function getFingerStates(lm) {
  // lm = array of 21 landmarks {x, y, z}
  // Thumb: compare tip x to mcp x (for mirrored view)
  const thumbUp = lm[4].x > lm[3].x; // mirrored: right hand thumb extends to the right
  const indexUp  = lm[8].y  < lm[6].y;
  const middleUp = lm[12].y < lm[10].y;
  const ringUp   = lm[16].y < lm[14].y;
  const pinkyUp  = lm[20].y < lm[18].y;
  return { thumb: thumbUp, index: indexUp, middle: middleUp, ring: ringUp, pinky: pinkyUp };
}

function classifySign(lm, handedness) {
  const f = getFingerStates(lm);

  // Thumb direction for thumbs up/down
  const thumbTipY = lm[4].y;
  const thumbMcpY = lm[2].y;
  const thumbPointingUp   = thumbTipY < thumbMcpY - 0.05;
  const thumbPointingDown = thumbTipY > thumbMcpY + 0.05;

  const ext = [f.thumb, f.index, f.middle, f.ring, f.pinky];
  const count = ext.filter(Boolean).length;

  // All 5 → HELLO
  if (f.thumb && f.index && f.middle && f.ring && f.pinky) return { key:'HELLO', conf:90 };

  // Thumb+Index+Pinky → ILY
  if (f.thumb && f.index && !f.middle && !f.ring && f.pinky) return { key:'ILY', conf:90 };

  // Thumb+Pinky → CALL ME
  if (f.thumb && !f.index && !f.middle && !f.ring && f.pinky) return { key:'CALLME', conf:85 };

  // Index+Pinky → ROCK
  if (!f.thumb && f.index && !f.middle && !f.ring && f.pinky) return { key:'ROCK', conf:80 };

  // Thumbs up → GOOD
  if (thumbPointingUp && !f.index && !f.middle && !f.ring && !f.pinky) return { key:'GOOD', conf:88 };

  // Thumbs down → BAD
  if (thumbPointingDown && !f.index && !f.middle && !f.ring && !f.pinky) return { key:'BAD', conf:85 };

  // Index+Middle → PEACE
  if (!f.thumb && f.index && f.middle && !f.ring && !f.pinky) return { key:'PEACE', conf:88 };

  // Index only → ONE
  if (!f.thumb && f.index && !f.middle && !f.ring && !f.pinky) return { key:'ONE', conf:85 };

  // Three fingers → THREE
  if (!f.thumb && f.index && f.middle && f.ring && !f.pinky) return { key:'THREE', conf:82 };

  // Four fingers → FOUR
  if (!f.thumb && f.index && f.middle && f.ring && f.pinky) return { key:'FOUR', conf:80 };

  // Fist → YES
  if (!f.thumb && !f.index && !f.middle && !f.ring && !f.pinky) return { key:'YES', conf:78 };

  return { key: null, conf: 0 };
}

async function startCamera() {
  document.getElementById('btnStart').style.display = 'none';
  document.getElementById('btnStop').style.display = 'block';
  document.getElementById('camHint').textContent = 'Loading MediaPipe Hands model…';
  const bar = document.getElementById('mpLoading');
  bar.style.width = '30%';

  const video = document.getElementById('camVideo');
  const canvas = document.getElementById('camCanvas');
  const ctx = canvas.getContext('2d');

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode:'user', width:640, height:480 } });
    video.srcObject = cameraStream;
    await new Promise(r => video.onloadedmetadata = r);
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  } catch(e) {
    alert('Camera access denied: ' + e.message);
    resetCameraUI(); return;
  }

  bar.style.width = '60%';

  mpHands = new Hands({ locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}` });
  mpHands.setOptions({ maxNumHands:1, modelComplexity:1, minDetectionConfidence:.65, minTrackingConfidence:.5 });

  mpHands.onResults(results => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      const lm = results.multiHandLandmarks[0];
      const handedness = results.multiHandedness[0].label;
      drawConnectors(ctx, lm, HAND_CONNECTIONS, { color:'#667eea', lineWidth:2 });
      drawLandmarks(ctx, lm, { color:'#fff', fillColor:'#764ba2', radius:4 });
      const { key, conf } = classifySign(lm, handedness);
      updateDetection(key, conf);
    } else {
      updateDetection(null, 0);
    }
  });

  bar.style.width = '90%';
  isRunning = true;

  mpCamera = new Camera(video, {
    onFrame: async () => { if (isRunning) await mpHands.send({ image: video }); },
    width: 640, height: 480
  });
  await mpCamera.start();

  bar.style.width = '100%';
  setTimeout(() => bar.style.width = '0', 800);
  document.getElementById('camHint').textContent = '✅ MediaPipe active — show a sign to the camera!';
}

function stopCamera() {
  isRunning = false;
  if (mpCamera) { mpCamera.stop(); mpCamera = null; }
  if (mpHands)  { mpHands.close(); mpHands = null; }
  if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; }
  const canvas = document.getElementById('camCanvas');
  canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
  resetCameraUI();
}

function resetCameraUI() {
  document.getElementById('btnStart').style.display = 'block';
  document.getElementById('btnStop').style.display = 'none';
  document.getElementById('liveSign').textContent = '—';
  document.getElementById('liveConf').textContent = 'Show a sign to the camera';
  document.getElementById('panelSign').textContent = '—';
  document.getElementById('panelSub').textContent = 'Hold sign 1.5s to add to sentence';
  document.getElementById('timerWrap').style.display = 'none';
  document.getElementById('camHint').textContent = 'Click Start Camera to begin.';
}

let lastKey = null, confirmTimer = null;

function updateDetection(key, conf) {
  const liveSign = document.getElementById('liveSign');
  const liveConf = document.getElementById('liveConf');
  const panelSign = document.getElementById('panelSign');
  const panelSub  = document.getElementById('panelSub');
  const timerWrap = document.getElementById('timerWrap');
  const circle    = document.getElementById('timerCircle');

  if (!key || conf < 70) {
    liveSign.textContent = '—';
    liveConf.textContent = 'No sign detected';
    panelSign.textContent = '—';
    panelSub.textContent = 'Show a sign clearly to the camera';
    timerWrap.style.display = 'none';
    holdSign = null; holdStart = 0;
    return;
  }

  const info = SIGNS[key];
  liveSign.textContent = info.emoji + ' ' + info.label;
  liveConf.textContent = `Confidence: ${conf}%`;
  panelSign.textContent = info.emoji + ' ' + info.label;

  if (key !== holdSign) {
    holdSign = key; holdStart = Date.now();
    timerWrap.style.display = 'block';
  }

  const elapsed = Date.now() - holdStart;
  const progress = Math.min(elapsed / holdDuration, 1);
  const dashOffset = 113 * (1 - progress);
  circle.style.strokeDashoffset = dashOffset;

  if (progress < 1) {
    const rem = ((holdDuration - elapsed) / 1000).toFixed(1);
    panelSub.textContent = `Hold for ${rem}s to add…`;
  } else {
    // Confirmed!
    addToSentence(info.label);
    timerWrap.style.display = 'none';
    panelSub.textContent = '✅ Added! Show next sign…';
    holdSign = null; holdStart = 0;
    // Brief cooldown
    isRunning = false;
    setTimeout(() => { isRunning = true; }, 1200);
  }
}

function addToSentence(word) {
  sentence.push(word);
  const box = document.getElementById('sentenceBox');
  box.classList.remove('empty');
  box.textContent = sentence.join('  →  ');
}

function clearSentence() {
  sentence = [];
  const box = document.getElementById('sentenceBox');
  box.classList.add('empty');
  box.textContent = 'Your recognized words will appear here…';
  holdSign = null; holdStart = 0;
}
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text','').strip()
    language = data.get('language','english')
    target = data.get('target','ASL')
    start = time.time()
    result = translate_with_slt(text, language, target) or translate_fallback(text, language)
    elapsed = int((time.time() - start) * 1000)
    return jsonify({
        'glosses': result['glosses'],
        'grammar': result['grammar_type'],
        'grammar_notes': result.get('grammar_notes',''),
        'sign_descriptions': result.get('sign_descriptions',[]),
        'confidence': 88,
        'time': elapsed,
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
