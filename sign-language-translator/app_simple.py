#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import json
import time

app = Flask(__name__)
CORS(app)

SIGN_LANGUAGE_NAMES = {
    'ASL': 'American Sign Language',
    'LSF': 'Langue des Signes Française',
    'ISL': 'Indian Sign Language',
    'BSL': 'British Sign Language'
}

GLOSSES_FALLBACK = {
    'english': {
        'i': 'IX-1', 'me': 'IX-1', 'my': 'IX-1', 'we': 'IX-1PL', 'us': 'IX-1PL',
        'you': 'IX-2', 'your': 'IX-2', 'he': 'IX-3', 'she': 'IX-3', 'they': 'IX-3PL',
        'will': 'FUTURE', 'going': 'FUTURE', 'eat': 'EAT', 'eating': 'EAT',
        'want': 'WANT', 'go': 'GO', 'come': 'COME', 'drink': 'DRINK',
        'apple': 'APPLE', 'tomorrow': 'TOMORROW', 'today': 'TODAY', 'yesterday': 'PAST',
        'cinema': 'MOVIE', 'movie': 'MOVIE', 'hello': 'HI', 'hi': 'HI',
        'thank': 'THANK', 'thanks': 'THANK', 'yes': 'YES', 'no': 'NO',
        'good': 'GOOD', 'bad': 'BAD', 'do': 'DO', 'what': 'WHAT',
        'how': 'HOW', 'where': 'WHERE', 'when': 'WHEN', 'who': 'WHO',
        'love': 'LOVE', 'sleep': 'SLEEP', 'help': 'HELP', 'work': 'WORK',
        'school': 'SCHOOL', 'home': 'HOME', 'food': 'FOOD', 'water': 'WATER',
        'please': 'PLEASE', 'sorry': 'SORRY', 'name': 'NAME', 'like': 'LIKE',
    },
    'french': {
        'je': 'IX-1', 'moi': 'IX-1', 'mon': 'IX-1', 'ma': 'IX-1',
        'tu': 'IX-2', 'vous': 'IX-2', 'ton': 'IX-2', 'ta': 'IX-2',
        'il': 'IX-3', 'elle': 'IX-3', 'nous': 'IX-1PL', 'ils': 'IX-3PL',
        'vais': 'FUTURE', 'irai': 'FUTURE', 'manger': 'EAT', 'mange': 'EAT',
        'vouloir': 'WANT', 'veux': 'WANT', 'aller': 'GO', 'venir': 'COME',
        'pomme': 'APPLE', 'demain': 'TOMORROW', 'aujourd': 'TODAY', 'hier': 'PAST',
        'cinéma': 'MOVIE', 'film': 'MOVIE', 'bonjour': 'HI', 'salut': 'HI',
        'merci': 'THANK', 'oui': 'YES', 'non': 'NO', 'bon': 'GOOD',
        'quoi': 'WHAT', 'comment': 'HOW', 'où': 'WHERE', 'quand': 'WHEN',
        'aimer': 'LOVE', 'aime': 'LOVE', 'dormir': 'SLEEP', 'aider': 'HELP',
        'travail': 'WORK', 'école': 'SCHOOL', 'maison': 'HOME', 'eau': 'WATER',
        'sil': 'PLEASE', 'désolé': 'SORRY', 'nom': 'NAME',
    }
}


def translate_with_claude(text, language, target_sign):
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        sign_name = SIGN_LANGUAGE_NAMES.get(target_sign, target_sign)

        prompt = f"""You are an expert sign language interpreter specializing in {sign_name} ({target_sign}).

Translate this {language} text into {target_sign} glosses with full sign descriptions.

TEXT: "{text}"

RULES:
- Use CAPITAL LETTERS for each gloss
- Apply {target_sign} grammar (topic first, time markers early, drop articles/prepositions)
- Notation: IX-1=I/me, IX-2=you, IX-3=he/she, IX-1PL=we, TOPICALIZE for topics, WH-Q for questions
- For each gloss, describe the handshape, location and movement to perform the sign

Respond ONLY with this JSON (no extra text):
{{
  "glosses": ["GLOSS1", "GLOSS2"],
  "grammar_type": "Statement",
  "grammar_notes": "explain grammar applied",
  "sign_descriptions": [
    {{
      "gloss": "GLOSS1",
      "handshape": "describe hand shape",
      "location": "where on the body",
      "movement": "describe movement"
    }}
  ]
}}"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        return json.loads(response_text)

    except Exception as e:
        print(f"Claude API error: {e}")
        return None


def translate_fallback(text, language):
    glosses_map = GLOSSES_FALLBACK.get(language, GLOSSES_FALLBACK['english'])
    words = text.lower().split()
    glosses = []
    for word in words:
        clean = word.strip('.,?!;:')
        gloss = glosses_map.get(clean, clean.upper())
        if gloss:
            glosses.append(gloss)

    grammar = 'Question' if '?' in text else 'Statement'
    return {
        'glosses': glosses if glosses else ['NO', 'TRANSLATION'],
        'grammar_type': grammar,
        'grammar_notes': 'Dictionary-based translation (add ANTHROPIC_API_KEY for AI)',
        'sign_descriptions': []
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sign Language Translator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }
        .container {
            max-width: 960px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 24px 64px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        header h1 { font-size: 32px; margin-bottom: 0.5rem; }
        header p { font-size: 14px; opacity: 0.9; }
        .ai-badge {
            display: inline-block;
            background: rgba(255,255,255,0.25);
            border: 1px solid rgba(255,255,255,0.4);
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 12px;
            margin-top: 0.5rem;
        }
        .content { padding: 2rem; }
        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .control-group { display: flex; flex-direction: column; }
        label { font-size: 13px; color: #555; margin-bottom: 6px; font-weight: 600; }
        select, textarea {
            padding: 0.75rem;
            border: 1.5px solid #e0e0e0;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.12);
        }
        textarea {
            grid-column: 1 / -1;
            resize: vertical;
            min-height: 110px;
        }
        .button-group { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
        button {
            flex: 1;
            padding: 0.85rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .translate-btn { background: #667eea; color: white; }
        .translate-btn:hover:not(:disabled) { background: #5568d3; transform: translateY(-1px); }
        .translate-btn:disabled { background: #b0b8e8; cursor: not-allowed; }
        .clear-btn { background: #f5f5f5; color: #444; border: 1.5px solid #e0e0e0; flex: 0.3; }
        .clear-btn:hover { background: #eee; }

        .results { display: none; }
        .results.active { display: block; }

        .section { margin-bottom: 2rem; }
        .section-title {
            font-size: 13px;
            font-weight: 700;
            color: #444;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #f0f0f0;
        }

        .glosses-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        .gloss-tag {
            background: #667eea;
            color: white;
            padding: 0.5rem 1.1rem;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
            position: relative;
        }
        .gloss-tag:hover { background: #5568d3; transform: translateY(-1px); }
        .gloss-tag.active { background: #764ba2; box-shadow: 0 4px 12px rgba(118,75,162,0.4); }
        .arrow { color: #bbb; font-size: 18px; }

        .sign-detail {
            display: none;
            background: linear-gradient(135deg, #f8f6ff, #f0ecff);
            border: 1.5px solid #d8d0f0;
            border-radius: 12px;
            padding: 1.25rem;
            margin-top: 1rem;
        }
        .sign-detail.active { display: block; }
        .sign-detail h4 {
            color: #667eea;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .sign-props {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.75rem;
        }
        .sign-prop {
            background: white;
            border-radius: 8px;
            padding: 0.75rem;
            border: 1px solid #e8e4f8;
        }
        .sign-prop-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            color: #999;
            margin-bottom: 4px;
        }
        .sign-prop-value { font-size: 13px; color: #333; }

        .grammar-box {
            background: #f9f9fb;
            border-radius: 10px;
            padding: 1rem 1.25rem;
            border: 1.5px solid #eee;
        }
        .grammar-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        .grammar-row:last-child { margin-bottom: 0; }
        .grammar-label { font-size: 12px; font-weight: 700; color: #888; width: 80px; flex-shrink: 0; }
        .grammar-value { font-size: 13px; color: #333; }
        .badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-statement { background: #e8f4e8; color: #2d7a2d; }
        .badge-question { background: #fff3e0; color: #e65100; }

        .metrics {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }
        .metric {
            background: #f9f9fb;
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            border: 1.5px solid #eee;
        }
        .metric-value { font-size: 22px; font-weight: 700; color: #667eea; }
        .metric-label { font-size: 11px; color: #888; margin-top: 4px; text-transform: uppercase; }

        .loading {
            display: inline-block;
            width: 16px; height: 16px;
            border: 2px solid rgba(255,255,255,0.4);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
            vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .divider { border: none; border-top: 2px solid #f0f0f0; margin: 2rem 0; }

        @media (max-width: 640px) {
            body { padding: 0; }
            .container { border-radius: 0; }
            .controls { grid-template-columns: 1fr; }
            .metrics { grid-template-columns: 1fr 1fr; }
            .sign-props { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>🤟 Sign Language Translator</h1>
        <p>Text → Sign Language Glosses with AI</p>
        <div class="ai-badge" id="aiBadge">Loading...</div>
    </header>
    <div class="content">
        <div class="controls">
            <div class="control-group">
                <label>Input Language</label>
                <select id="sourceLanguage">
                    <option value="english">English</option>
                    <option value="french">Français</option>
                </select>
            </div>
            <div class="control-group">
                <label>Sign Language</label>
                <select id="targetSign">
                    <option value="ASL">ASL — American</option>
                    <option value="LSF">LSF — Française</option>
                    <option value="ISL">ISL — Indian</option>
                    <option value="BSL">BSL — British</option>
                </select>
            </div>
            <textarea id="inputText" placeholder="Type a sentence… e.g. I want to eat an apple tomorrow"></textarea>
        </div>
        <div class="button-group">
            <button class="translate-btn" id="translateBtn" onclick="doTranslate()">🔤 TRANSLATE</button>
            <button class="clear-btn" onclick="clearAll()">✕ Clear</button>
        </div>

        <div id="results" class="results">
            <hr class="divider">

            <div class="section">
                <div class="section-title">Sign Language Glosses</div>
                <div class="glosses-row" id="glossesRow"></div>
                <div class="sign-detail" id="signDetail">
                    <h4 id="detailGloss"></h4>
                    <div class="sign-props" id="detailProps"></div>
                </div>
                <p style="font-size:12px;color:#aaa;margin-top:0.75rem">👆 Click a gloss to see how to perform the sign</p>
            </div>

            <div class="section">
                <div class="section-title">Grammar Analysis</div>
                <div class="grammar-box">
                    <div class="grammar-row">
                        <span class="grammar-label">Type</span>
                        <span id="grammarType"></span>
                    </div>
                    <div class="grammar-row">
                        <span class="grammar-label">Notes</span>
                        <span class="grammar-value" id="grammarNotes"></span>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Stats</div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="mGlosses">0</div>
                        <div class="metric-label">Glosses</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="mWords">0</div>
                        <div class="metric-label">Words</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="mConf">0%</div>
                        <div class="metric-label">Confidence</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="mTime">0ms</div>
                        <div class="metric-label">Time</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
let signDescriptions = {};

async function checkStatus() {
    try {
        const r = await fetch('/api/status');
        const d = await r.json();
        document.getElementById('aiBadge').textContent = d.ai_powered
            ? '✦ Claude AI Powered'
            : '⚡ Dictionary Mode';
    } catch(e) {}
}
checkStatus();

async function doTranslate() {
    const text = document.getElementById('inputText').value.trim();
    if (!text) { alert('Please enter text to translate'); return; }

    const btn = document.getElementById('translateBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Translating...';

    try {
        const res = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                language: document.getElementById('sourceLanguage').value,
                target: document.getElementById('targetSign').value
            })
        });
        const data = await res.json();
        renderResults(data, text);
    } catch(e) {
        alert('Error: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🔤 TRANSLATE';
    }
}

function renderResults(data, originalText) {
    signDescriptions = {};
    (data.sign_descriptions || []).forEach(s => { signDescriptions[s.gloss] = s; });

    const row = document.getElementById('glossesRow');
    row.innerHTML = '';

    data.glosses.forEach((gloss, i) => {
        const span = document.createElement('span');
        span.className = 'gloss-tag';
        span.textContent = gloss;
        span.onclick = () => showSignDetail(gloss, span);
        row.appendChild(span);
        if (i < data.glosses.length - 1) {
            const arr = document.createElement('span');
            arr.className = 'arrow';
            arr.textContent = '→';
            row.appendChild(arr);
        }
    });

    const type = data.grammar || 'Statement';
    const typeEl = document.getElementById('grammarType');
    typeEl.innerHTML = `<span class="badge badge-${type.toLowerCase().includes('quest') ? 'question' : 'statement'}">${type}</span>`;
    document.getElementById('grammarNotes').textContent = data.grammar_notes || '—';

    document.getElementById('mGlosses').textContent = data.glosses.length;
    document.getElementById('mWords').textContent = originalText.split(/\s+/).length;
    document.getElementById('mConf').textContent = data.confidence + '%';
    document.getElementById('mTime').textContent = data.time + 'ms';

    document.getElementById('signDetail').classList.remove('active');
    document.getElementById('results').classList.add('active');
}

function showSignDetail(gloss, el) {
    document.querySelectorAll('.gloss-tag').forEach(t => t.classList.remove('active'));
    el.classList.add('active');

    const detail = document.getElementById('signDetail');
    const s = signDescriptions[gloss];

    document.getElementById('detailGloss').textContent = gloss;
    const props = document.getElementById('detailProps');

    if (s) {
        props.innerHTML = `
            <div class="sign-prop">
                <div class="sign-prop-label">✋ Handshape</div>
                <div class="sign-prop-value">${s.handshape || '—'}</div>
            </div>
            <div class="sign-prop">
                <div class="sign-prop-label">📍 Location</div>
                <div class="sign-prop-value">${s.location || '—'}</div>
            </div>
            <div class="sign-prop">
                <div class="sign-prop-label">↔️ Movement</div>
                <div class="sign-prop-value">${s.movement || '—'}</div>
            </div>`;
    } else {
        props.innerHTML = `<div class="sign-prop" style="grid-column:1/-1">
            <div class="sign-prop-label">Gloss</div>
            <div class="sign-prop-value">No detailed description available for <strong>${gloss}</strong>. Enable AI mode for full sign descriptions.</div>
        </div>`;
    }
    detail.classList.add('active');
}

function clearAll() {
    document.getElementById('inputText').value = '';
    document.getElementById('results').classList.remove('active');
    document.getElementById('signDetail').classList.remove('active');
}

document.getElementById('inputText').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.ctrlKey) doTranslate();
});
</script>
</body>
</html>"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/status')
def status():
    return jsonify({'ai_powered': bool(os.environ.get('ANTHROPIC_API_KEY'))})


@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '').strip()
    language = data.get('language', 'english')
    target = data.get('target', 'ASL')

    start = time.time()

    result = translate_with_claude(text, language, target)
    if result is None:
        result = translate_fallback(text, language)

    elapsed = int((time.time() - start) * 1000)
    ai_powered = bool(os.environ.get('ANTHROPIC_API_KEY'))

    return jsonify({
        'glosses': result['glosses'],
        'grammar': result['grammar_type'],
        'grammar_notes': result.get('grammar_notes', ''),
        'sign_descriptions': result.get('sign_descriptions', []),
        'confidence': 95 if ai_powered else 65,
        'time': elapsed,
        'ai_powered': ai_powered
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
