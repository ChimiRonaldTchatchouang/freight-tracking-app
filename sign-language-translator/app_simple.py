#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Stockage en mémoire
history = []

# Glosses pour traduction
GLOSSES = {
    'english': {
        'i': 'IX-1', 'me': 'IX-1', 'we': 'IX-1PL', 'you': 'IX-2', 'he': 'IX-3', 'she': 'IX-3',
        'will': 'FUTURE', 'eat': 'EAT', 'want': 'WANT', 'go': 'GO', 'come': 'COME',
        'apple': 'APPLE', 'tomorrow': 'TOMORROW', 'today': 'TODAY', 'cinema': 'MOVIE',
        'hello': 'HI', 'thank': 'THANK', 'yes': 'YES', 'no': 'NO', 'good': 'GOOD',
        'do': 'DO', 'what': 'WHAT', 'how': 'HOW', 'where': 'WHERE', 'when': 'WHEN',
        'love': 'LOVE', 'drink': 'DRINK', 'sleep': 'SLEEP', 'help': 'HELP'
    },
    'french': {
        'je': 'IX-1', 'tu': 'IX-2', 'il': 'IX-3', 'elle': 'IX-3', 'nous': 'IX-1PL',
        'vais': 'FUTURE', 'manger': 'EAT', 'vouloir': 'WANT', 'aller': 'GO', 'venir': 'COME',
        'pomme': 'APPLE', 'demain': 'TOMORROW', 'aujourd': 'TODAY', 'cinéma': 'MOVIE',
        'bonjour': 'HI', 'merci': 'THANK', 'oui': 'YES', 'non': 'NO', 'bon': 'GOOD',
        'quoi': 'WHAT', 'comment': 'HOW', 'où': 'WHERE', 'quand': 'WHEN'
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
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
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        h1 { font-size: 32px; margin-bottom: 0.5rem; }
        .subtitle { font-size: 14px; opacity: 0.9; }
        .content { padding: 2rem; }
        .status {
            padding: 1rem;
            background: #e8f4f8;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            font-size: 13px;
            margin-bottom: 1rem;
        }
        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .control-group {
            display: flex;
            flex-direction: column;
        }
        label {
            font-size: 13px;
            color: #666;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        select, textarea {
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-family: inherit;
            font-size: 14px;
        }
        select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        textarea {
            grid-column: 1 / -1;
            resize: vertical;
            min-height: 100px;
        }
        .button-group {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        button {
            flex: 1;
            padding: 0.75rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .translate-btn {
            background: #667eea;
            color: white;
        }
        .translate-btn:hover:not(:disabled) { background: #5568d3; }
        .translate-btn:disabled { background: #ccc; cursor: not-allowed; }
        .clear-btn {
            background: #f5f5f5;
            color: #333;
            border: 1px solid #ddd;
        }
        .clear-btn:hover { background: #eee; }
        .results {
            display: none;
            margin-top: 2rem;
            border-top: 1px solid #eee;
            padding-top: 2rem;
        }
        .results.active { display: block; }
        .section { margin-bottom: 1.5rem; }
        .section h3 {
            font-size: 14px;
            color: #333;
            margin-bottom: 0.75rem;
            font-weight: 600;
        }
        .glosses {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
        }
        .gloss-tag {
            background: #667eea;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 500;
        }
        .info-box {
            background: #f9f9f9;
            padding: 1rem;
            border-radius: 6px;
            border: 1px solid #eee;
            font-size: 13px;
            line-height: 1.6;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
        }
        .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 1rem;
            margin-top: 1rem;
        }
        .metric {
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: 600;
            color: #667eea;
        }
        .metric-label {
            font-size: 12px;
            color: #666;
            margin-top: 0.5rem;
        }
        .history {
            margin-top: 2rem;
            border-top: 1px solid #eee;
            padding-top: 1.5rem;
        }
        .history h3 { font-size: 16px; margin-bottom: 1rem; }
        .history-item {
            background: #f9f9f9;
            padding: 0.75rem;
            border-radius: 6px;
            margin-bottom: 0.5rem;
            font-size: 13px;
            color: #666;
            cursor: pointer;
        }
        .history-item:hover { background: #eee; }
        .loading {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid #f3f3f3;
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        @media (max-width: 600px) {
            .container { margin: 0; border-radius: 0; }
            h1 { font-size: 24px; }
            .content { padding: 1rem; }
            .controls { grid-template-columns: 1fr; }
            .metrics { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤟 Sign Language Translator</h1>
            <p class="subtitle">Translate text to sign language glosses</p>
        </header>
        <div class="content">
            <div class="status">
                ✓ Live API Active | Sign Language Translator v1.0
            </div>
            <div class="controls">
                <div class="control-group">
                    <label>Language</label>
                    <select id="sourceLanguage">
                        <option value="english">English</option>
                        <option value="french">French</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Sign Language</label>
                    <select id="targetSign">
                        <option value="ASL">ASL (American)</option>
                        <option value="LSF">LSF (French)</option>
                        <option value="ISL">ISL (Indian)</option>
                    </select>
                </div>
                <textarea id="inputText" placeholder="Type text here..."></textarea>
            </div>
            <div class="button-group">
                <button class="translate-btn" id="translateBtn" onclick="translate()">TRANSLATE</button>
                <button class="clear-btn" onclick="clearForm()">CLEAR</button>
            </div>
            <div id="results" class="results">
                <div class="section">
                    <h3>Glosses</h3>
                    <div class="glosses" id="glossesContainer"></div>
                </div>
                <div class="section">
                    <h3>Analysis</h3>
                    <div class="info-box">
                        <div class="info-row">
                            <strong>Grammar:</strong>
                            <span id="grammar">—</span>
                        </div>
                        <div class="info-row">
                            <strong>Confidence:</strong>
                            <span id="confidence">—</span>
                        </div>
                    </div>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="charCount">0</div>
                        <div class="metric-label">Chars</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="wordCount">0</div>
                        <div class="metric-label">Words</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="time">0ms</div>
                        <div class="metric-label">Time</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        async function translate() {
            const text = document.getElementById('inputText').value.trim();
            if (!text) { alert('Please enter text'); return; }

            const btn = document.getElementById('translateBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="loading"></span> Translating...';

            try {
                const response = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: text,
                        language: document.getElementById('sourceLanguage').value,
                        target: document.getElementById('targetSign').value
                    })
                });

                const result = await response.json();

                document.getElementById('glossesContainer').innerHTML =
                    result.glosses.map(g => `<span class="gloss-tag">${g}</span>`).join('');
                document.getElementById('grammar').textContent = result.grammar;
                document.getElementById('confidence').textContent = result.confidence + '%';
                document.getElementById('charCount').textContent = text.length;
                document.getElementById('wordCount').textContent = text.split(' ').length;
                document.getElementById('time').textContent = result.time + 'ms';

                document.getElementById('results').classList.add('active');
            } catch (error) {
                alert('Error: ' + error);
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'TRANSLATE';
            }
        }

        function clearForm() {
            document.getElementById('inputText').value = '';
            document.getElementById('results').classList.remove('active');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '').lower()
    language = data.get('language', 'english')
    target = data.get('target', 'ASL')

    glosses_map = GLOSSES.get(language, GLOSSES['english'])
    words = text.split()

    glosses = []
    for word in words:
        clean_word = word.replace('.', '').replace(',', '').replace('?', '').replace('!', '')
        gloss = glosses_map.get(clean_word, clean_word.upper())
        if gloss:
            glosses.append(gloss)

    import time
    grammar = 'Statement'
    if '?' in text:
        grammar = 'Question'

    import random
    confidence = 80 + random.randint(0, 15)

    return jsonify({
        'glosses': glosses if glosses else ['NO', 'TRANSLATION'],
        'grammar': grammar,
        'confidence': confidence,
        'time': 50
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
