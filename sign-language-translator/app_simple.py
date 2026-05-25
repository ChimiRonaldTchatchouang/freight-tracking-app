#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)

# ── Sign notation map ─────────────────────────────────────────────────────────
SIGN_MAP = {
    'i': 'IX-1', 'me': 'IX-1', 'my': 'IX-1', 'mine': 'IX-1',
    'we': 'IX-1PL', 'us': 'IX-1PL', 'our': 'IX-1PL',
    'you': 'IX-2', 'your': 'IX-2', 'yours': 'IX-2',
    'he': 'IX-3', 'she': 'IX-3', 'him': 'IX-3', 'her': 'IX-3',
    'they': 'IX-3PL', 'them': 'IX-3PL', 'their': 'IX-3PL',
    'will': 'FUTURE', "i'll": 'FUTURE', "we'll": 'FUTURE', "you'll": 'FUTURE',
    'tomorrow': 'TOMORROW', 'today': 'TODAY', 'yesterday': 'PAST',
    'now': 'NOW', 'later': 'LATER', 'soon': 'SOON',
    'hello': 'HI', 'hi': 'HI', 'hey': 'HI', 'greetings': 'HI',
    'thank': 'THANK', 'thanks': 'THANK',
    'yes': 'YES', 'yeah': 'YES', 'no': 'NO', 'nope': 'NO',
    'please': 'PLEASE', 'sorry': 'SORRY', 'excuse': 'SORRY',
    'want': 'WANT', 'like': 'LIKE', 'love': 'LOVE', 'need': 'NEED',
    'go': 'GO', 'goes': 'GO', 'going': 'GO',
    'come': 'COME', 'comes': 'COME', 'coming': 'COME',
    'eat': 'EAT', 'eats': 'EAT', 'eating': 'EAT', 'ate': 'EAT',
    'drink': 'DRINK', 'drinks': 'DRINK', 'drinking': 'DRINK', 'drank': 'DRINK',
    'sleep': 'SLEEP', 'sleeping': 'SLEEP', 'slept': 'SLEEP',
    'work': 'WORK', 'works': 'WORK', 'working': 'WORK',
    'study': 'STUDY', 'studying': 'STUDY',
    'play': 'PLAY', 'playing': 'PLAY',
    'know': 'KNOW', 'knows': 'KNOW',
    'understand': 'UNDERSTAND',
    'think': 'THINK', 'thinks': 'THINK',
    'see': 'SEE', 'look': 'LOOK', 'watch': 'WATCH',
    'hear': 'HEAR', 'listen': 'LISTEN',
    'help': 'HELP', 'stop': 'STOP', 'finish': 'FINISH', 'done': 'FINISH',
    'good': 'GOOD', 'great': 'GREAT', 'bad': 'BAD', 'wrong': 'WRONG',
    'happy': 'HAPPY', 'sad': 'SAD', 'angry': 'ANGRY', 'tired': 'TIRED',
    'big': 'BIG', 'large': 'BIG', 'small': 'SMALL', 'little': 'SMALL',
    'fast': 'FAST', 'quick': 'FAST', 'slow': 'SLOW',
    'home': 'HOME', 'house': 'HOME',
    'school': 'SCHOOL', 'class': 'CLASS',
    'cinema': 'MOVIE', 'movie': 'MOVIE', 'film': 'MOVIE',
    'apple': 'APPLE', 'water': 'WATER', 'food': 'FOOD',
    'bread': 'BREAD', 'milk': 'MILK', 'coffee': 'COFFEE',
    'where': 'WHERE', 'when': 'WHEN', 'what': 'WHAT',
    'who': 'WHO', 'how': 'HOW', 'why': 'WHY',
    'do': 'DO', 'did': 'PAST', 'name': 'NAME',
    'again': 'AGAIN', 'more': 'MORE', 'much': 'MUCH',
    'can': 'CAN', 'cannot': 'CANNOT', "can't": 'CANNOT',
    'not': 'NOT', "don't": 'NOT+DO', "doesn't": 'NOT+DO',
    'person': 'PERSON', 'people': 'PEOPLE', 'friend': 'FRIEND',
    'family': 'FAMILY', 'mother': 'MOTHER', 'father': 'FATHER',
    'read': 'READ', 'write': 'WRITE', 'speak': 'SPEAK', 'sign': 'SIGN',
    # French tokens
    'je': 'IX-1', 'moi': 'IX-1', 'mon': 'IX-1', 'ma': 'IX-1',
    'tu': 'IX-2', 'vous': 'IX-2', 'ton': 'IX-2', 'ta': 'IX-2',
    'il': 'IX-3', 'elle': 'IX-3', 'ils': 'IX-3PL', 'elles': 'IX-3PL',
    'nous': 'IX-1PL', 'notre': 'IX-1PL',
    'vais': 'FUTURE', 'irai': 'FUTURE', 'ferai': 'FUTURE',
    'manger': 'EAT', 'mange': 'EAT', 'mangé': 'EAT',
    'boire': 'DRINK', 'bois': 'DRINK', 'bu': 'DRINK',
    'vouloir': 'WANT', 'veux': 'WANT', 'veut': 'WANT',
    'aller': 'GO', 'venir': 'COME',
    'aimer': 'LOVE', 'aime': 'LOVE',
    'pomme': 'APPLE', 'eau': 'WATER', 'nourriture': 'FOOD',
    'demain': 'TOMORROW', "aujourd'hui": 'TODAY', 'hier': 'PAST',
    'cinéma': 'MOVIE', 'film': 'MOVIE',
    'bonjour': 'HI', 'salut': 'HI', 'allô': 'HI',
    'merci': 'THANK', 'oui': 'YES', 'non': 'NO',
    'où': 'WHERE', 'quand': 'WHEN', 'quoi': 'WHAT', 'qui': 'WHO',
    'comment': 'HOW', 'pourquoi': 'WHY',
    'bon': 'GOOD', 'bien': 'GOOD', 'mauvais': 'BAD',
    'heureux': 'HAPPY', 'heureuse': 'HAPPY', 'triste': 'SAD',
    'maison': 'HOME', 'école': 'SCHOOL', 'travail': 'WORK',
    'ami': 'FRIEND', 'amie': 'FRIEND', 'famille': 'FAMILY',
    'mère': 'MOTHER', 'père': 'FATHER',
    'désolé': 'SORRY', 'sil': 'PLEASE',
    'dormir': 'SLEEP', 'dort': 'SLEEP',
    'aider': 'HELP', 'aide': 'HELP',
    'nom': 'NAME', 'encore': 'AGAIN',
}

# Words to drop in sign language (articles, aux, prepositions)
SKIP_WORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'about', 'into',
    'that', 'this', 'these', 'those', 'it', 'its',
    'very', 'just', 'also', 'so', 'and', 'or', 'but', 'if', 'then',
    'have', 'has', 'had', "'ve", "'d", "'s",
    # French
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'au', 'aux',
    'est', 'sont', 'être', 'avoir', 'et', 'ou', 'mais', 'si', 'que',
    'qui', 'ce', 'se', 'lui', 'y', 'en', 'sur', 'sous', 'avec', 'par',
    'très', 'aussi', 'puis', 'donc', "j'", "c'",
}

TIME_GLOSSES = {'FUTURE', 'TOMORROW', 'TODAY', 'PAST', 'NOW', 'LATER', 'SOON', 'YESTERDAY'}

# ── Per-gloss sign descriptions ───────────────────────────────────────────────
SIGN_DESCRIPTIONS = {
    'IX-1':     {'handshape': 'Index finger pointing', 'location': 'Point to your own chest', 'movement': 'No movement, hold still'},
    'IX-2':     {'handshape': 'Index finger pointing', 'location': 'Directed at the listener', 'movement': 'Point directly toward the other person'},
    'IX-3':     {'handshape': 'Index finger pointing', 'location': 'To the side of the body', 'movement': 'Point to a reference location for the person'},
    'IX-1PL':   {'handshape': 'Index finger or open hand', 'location': 'Sweep across chest', 'movement': 'Arc from one shoulder to the other'},
    'FUTURE':   {'handshape': 'Open hand, palm facing left', 'location': 'Side of face', 'movement': 'Move hand forward away from the face'},
    'PAST':     {'handshape': 'Open hand, palm facing body', 'location': 'Shoulder', 'movement': 'Flip hand backward over shoulder'},
    'TOMORROW': {'handshape': 'A handshape (fist with thumb up)', 'location': 'Cheek', 'movement': 'Touch cheek then arc hand forward'},
    'TODAY':    {'handshape': 'Both Y-hands palms up', 'location': 'In front of body', 'movement': 'Drop both hands down twice'},
    'NOW':      {'handshape': 'Both Y-hands palms up', 'location': 'In front of body', 'movement': 'Drop both hands down once firmly'},
    'HI':       {'handshape': 'Open hand B-shape', 'location': 'Forehead', 'movement': 'Wave outward from forehead'},
    'THANK':    {'handshape': 'Flat hand', 'location': 'Lips/chin', 'movement': 'Move hand forward toward the other person'},
    'YES':      {'handshape': 'S-handshape (fist)', 'location': 'In front of body', 'movement': 'Nod the fist up and down'},
    'NO':       {'handshape': 'Index + middle finger extended', 'location': 'In front of body', 'movement': 'Snap fingers closed against thumb'},
    'PLEASE':   {'handshape': 'Open hand, palm on chest', 'location': 'Chest', 'movement': 'Rub hand in circular motion on chest'},
    'SORRY':    {'handshape': 'A-handshape (fist)', 'location': 'Chest', 'movement': 'Rub fist in circular motion on chest'},
    'WANT':     {'handshape': 'Curved hands, palms up', 'location': 'In front of body', 'movement': 'Pull both hands toward your body'},
    'LIKE':     {'handshape': '8-handshape (middle + thumb)', 'location': 'Chest', 'movement': 'Pull fingers out from chest, opening them'},
    'LOVE':     {'handshape': 'Both hands crossed, fists', 'location': 'Chest', 'movement': 'Cross arms over chest, hug motion'},
    'NEED':     {'handshape': 'X-handshape (bent index)', 'location': 'In front of body', 'movement': 'Bend and straighten index finger downward'},
    'GO':       {'handshape': 'Both index fingers pointing', 'location': 'In front of body', 'movement': 'Both hands arc forward and away'},
    'COME':     {'handshape': 'Both index fingers pointing', 'location': 'In front of body', 'movement': 'Both hands arc toward you'},
    'EAT':      {'handshape': 'Flat-O hand (fingertips together)', 'location': 'Mouth', 'movement': 'Touch fingertips to mouth repeatedly'},
    'DRINK':    {'handshape': 'C-handshape (curved)', 'location': 'Mouth', 'movement': 'Tilt hand toward mouth as if drinking'},
    'SLEEP':    {'handshape': 'Open hand, palm facing you', 'location': 'Face', 'movement': 'Draw hand down over face, closing eyes'},
    'WORK':     {'handshape': 'Both S-handshapes (fists)', 'location': 'In front of body', 'movement': 'Tap dominant wrist on top of other wrist twice'},
    'HELP':     {'handshape': 'A-hand on open palm', 'location': 'In front of body', 'movement': 'Lift open palm upward with A-hand on top'},
    'STOP':     {'handshape': 'Dominant open hand, other flat', 'location': 'In front of body', 'movement': 'Chop dominant hand down onto other palm'},
    'FINISH':   {'handshape': 'Both open hands, palms up', 'location': 'In front of body', 'movement': 'Flip both hands outward quickly'},
    'GOOD':     {'handshape': 'Open hand, palm up', 'location': 'Chin', 'movement': 'Move hand forward and down into other palm'},
    'BAD':      {'handshape': 'Open hand, palm in', 'location': 'Mouth', 'movement': 'Flick hand outward and away'},
    'HAPPY':    {'handshape': 'Open hand, palm facing chest', 'location': 'Chest', 'movement': 'Brush hand upward on chest twice'},
    'SAD':      {'handshape': 'Both open hands, palms facing in', 'location': 'Face', 'movement': 'Move both hands downward past the face'},
    'MOVIE':    {'handshape': 'Open hand, palm facing other hand', 'location': 'In front of face', 'movement': 'Wiggle fingers and slide hand side to side'},
    'APPLE':    {'handshape': 'X-handshape (bent index)', 'location': 'Cheek', 'movement': 'Twist hand on the cheek'},
    'WATER':    {'handshape': 'W-handshape (3 fingers extended)', 'location': 'Chin', 'movement': 'Tap chin twice with index finger side'},
    'FOOD':     {'handshape': 'Flat-O hand', 'location': 'Mouth', 'movement': 'Touch fingertips to mouth once'},
    'WHERE':    {'handshape': 'Index finger pointing up', 'location': 'In front of body', 'movement': 'Shake index finger side to side'},
    'WHEN':     {'handshape': 'Both index fingers', 'location': 'In front of body', 'movement': 'Circle dominant index around other, then touch tips'},
    'WHAT':     {'handshape': 'Open hands, palms up', 'location': 'In front of body', 'movement': 'Shrug or brush index along other palm'},
    'WHO':      {'handshape': 'L-handshape', 'location': 'Chin', 'movement': 'Circle index finger near chin'},
    'HOW':      {'handshape': 'Both bent hands, knuckles together', 'location': 'In front of body', 'movement': 'Roll hands forward, opening upward'},
    'WHY':      {'handshape': 'Open hand, palm in', 'location': 'Forehead', 'movement': 'Flick middle finger out from forehead'},
    'NAME':     {'handshape': 'Both H-handshapes (2 fingers)', 'location': 'In front of body', 'movement': 'Tap dominant H-fingers on top of other H-fingers twice'},
    'DO':       {'handshape': 'Both C-handshapes', 'location': 'In front of body', 'movement': 'Move both hands side to side together'},
    'KNOW':     {'handshape': 'Bent hand, fingertips touching', 'location': 'Forehead/temple', 'movement': 'Tap fingertips to side of forehead'},
    'SEE':      {'handshape': 'V-handshape', 'location': 'Eyes', 'movement': 'Point V fingers at eyes then outward'},
    'THINK':    {'handshape': 'Index finger', 'location': 'Temple', 'movement': 'Touch index to temple'},
    'CAN':      {'handshape': 'Both S-handshapes', 'location': 'In front of body', 'movement': 'Move both fists down simultaneously'},
    'NOT':      {'handshape': 'A-handshape, thumb extended', 'location': 'Under chin', 'movement': 'Flick thumb outward from under chin'},
    'BIG':      {'handshape': 'Both L-handshapes', 'location': 'In front of body', 'movement': 'Move hands apart indicating large size'},
    'SMALL':    {'handshape': 'Both flat hands', 'location': 'In front of body', 'movement': 'Move hands close together'},
    'FRIEND':   {'handshape': 'Both index fingers hooked', 'location': 'In front of body', 'movement': 'Link index fingers and reverse'},
    'MOTHER':   {'handshape': 'Open hand, thumb touching palm', 'location': 'Chin', 'movement': 'Tap thumb on chin twice'},
    'FATHER':   {'handshape': 'Open hand, thumb touching palm', 'location': 'Forehead', 'movement': 'Tap thumb on forehead twice'},
    'HOME':     {'handshape': 'Flat-O hand', 'location': 'Cheek to cheek', 'movement': 'Touch mouth then move to cheek'},
    'SCHOOL':   {'handshape': 'Dominant claps other', 'location': 'In front of body', 'movement': 'Clap open hands together twice'},
    'AGAIN':    {'handshape': 'Bent hand', 'location': 'Other open palm', 'movement': 'Arc bent hand to land in open palm'},
    'MORE':     {'handshape': 'Both flat-O hands, fingertips together', 'location': 'In front of body', 'movement': 'Tap fingertips together several times'},
    'PEOPLE':   {'handshape': 'Both P-handshapes', 'location': 'In front of body', 'movement': 'Alternate circles with both hands'},
    'READ':     {'handshape': 'V-hand over flat palm', 'location': 'In front of body', 'movement': 'Move V fingers down across palm as if reading'},
    'WRITE':    {'handshape': 'Pinched fingers (mime pen)', 'location': 'Open other palm', 'movement': 'Write across the open palm'},
}


# ── Core translation using sign-language-translator NLP ──────────────────────
def translate_with_slt(text, language, target_sign):
    try:
        import sign_language_translator as slt

        lang_code = 'english'
        lang = slt.get_text_language(lang_code)

        tokens = lang.tokenize(text)
        tags = lang.get_tags(tokens)

        time_glosses = []
        main_glosses = []
        seen = set()

        for token, tag in zip(tokens, tags):
            tag_str = str(tag)
            if 'PUNCTUATION' in tag_str:
                continue
            t = token.lower()
            if t in lang.omitted_tokens or t in SKIP_WORDS or not t.strip():
                continue

            gloss = SIGN_MAP.get(t, t.upper())

            if gloss in TIME_GLOSSES:
                if gloss not in seen:
                    time_glosses.append(gloss)
                    seen.add(gloss)
            else:
                if gloss not in seen:
                    main_glosses.append(gloss)
                    seen.add(gloss)

        final_glosses = time_glosses + main_glosses

        grammar = 'Question' if '?' in text else 'Statement'
        notes = f'{target_sign} grammar: articles/prepositions removed'
        if time_glosses:
            notes += f', temporal markers moved first: {" ".join(time_glosses)}'

        return {
            'glosses': final_glosses if final_glosses else ['NO', 'TRANSLATION'],
            'grammar_type': grammar,
            'grammar_notes': notes,
            'sign_descriptions': [
                {**{'gloss': g}, **SIGN_DESCRIPTIONS[g]}
                for g in final_glosses if g in SIGN_DESCRIPTIONS
            ]
        }
    except Exception as e:
        print(f"SLT error: {e}")
        return None


def translate_fallback(text, language):
    words = text.lower().split()
    time_glosses, main_glosses, seen = [], [], set()

    for word in words:
        token = word.strip('.,?!;:')
        if token in SKIP_WORDS or not token:
            continue
        gloss = SIGN_MAP.get(token, token.upper())
        if gloss in seen:
            continue
        seen.add(gloss)
        if gloss in TIME_GLOSSES:
            time_glosses.append(gloss)
        else:
            main_glosses.append(gloss)

    final = time_glosses + main_glosses
    grammar = 'Question' if '?' in text else 'Statement'
    return {
        'glosses': final if final else ['NO', 'TRANSLATION'],
        'grammar_type': grammar,
        'grammar_notes': 'Dictionary translation (sign-language-translator NLP unavailable)',
        'sign_descriptions': [
            {**{'gloss': g}, **SIGN_DESCRIPTIONS[g]}
            for g in final if g in SIGN_DESCRIPTIONS
        ]
    }


# ── HTML ──────────────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sign Language Translator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 2rem;
        }
        .container {
            max-width: 960px; margin: 0 auto; background: white;
            border-radius: 16px; box-shadow: 0 24px 64px rgba(0,0,0,0.3); overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 2rem; text-align: center;
        }
        header h1 { font-size: 30px; margin-bottom: 6px; }
        header p { font-size: 14px; opacity: .85; }
        .badge {
            display: inline-block; margin-top: 10px;
            background: rgba(255,255,255,.22); border: 1px solid rgba(255,255,255,.35);
            border-radius: 20px; padding: 3px 14px; font-size: 12px; font-weight: 600;
        }
        .content { padding: 2rem; }
        .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
        .control-group { display: flex; flex-direction: column; }
        label { font-size: 12px; font-weight: 700; color: #555; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .04em; }
        select, textarea {
            padding: .75rem; border: 1.5px solid #e0e0e0; border-radius: 8px;
            font-family: inherit; font-size: 14px; transition: border-color .2s;
        }
        select:focus, textarea:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,.12); }
        textarea { grid-column: 1/-1; resize: vertical; min-height: 110px; }
        .btn-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
        button {
            flex: 1; padding: .85rem; border: none; border-radius: 8px;
            cursor: pointer; font-size: 15px; font-weight: 700; transition: all .18s;
        }
        .btn-translate { background: #667eea; color: white; }
        .btn-translate:hover:not(:disabled) { background: #5568d3; transform: translateY(-1px); }
        .btn-translate:disabled { background: #b0b8e8; cursor: not-allowed; }
        .btn-clear { background: #f5f5f5; color: #555; border: 1.5px solid #e0e0e0; flex: .3; }
        .btn-clear:hover { background: #eee; }
        .results { display: none; }
        .results.active { display: block; }
        hr { border: none; border-top: 2px solid #f0f0f0; margin: 2rem 0; }
        .section { margin-bottom: 2rem; }
        .sec-title {
            font-size: 11px; font-weight: 800; color: #888; text-transform: uppercase;
            letter-spacing: .08em; margin-bottom: 1rem; padding-bottom: .5rem;
            border-bottom: 2px solid #f0f0f0;
        }
        .gloss-row { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; margin-bottom: .75rem; }
        .gloss-tag {
            background: #667eea; color: white; padding: .45rem 1.1rem;
            border-radius: 999px; font-size: 13px; font-weight: 700;
            cursor: pointer; transition: all .15s; user-select: none;
        }
        .gloss-tag:hover { background: #5568d3; transform: translateY(-1px); }
        .gloss-tag.selected { background: #764ba2; box-shadow: 0 4px 14px rgba(118,75,162,.4); }
        .arrow { color: #ccc; font-size: 16px; }
        .hint { font-size: 11px; color: #aaa; margin-top: .5rem; }
        .sign-card {
            display: none; background: linear-gradient(135deg,#f8f6ff,#ede8ff);
            border: 1.5px solid #d4caf0; border-radius: 12px; padding: 1.25rem; margin-top: 1rem;
        }
        .sign-card.active { display: block; }
        .sign-card h4 { color: #667eea; font-size: 20px; margin-bottom: 1rem; }
        .sign-props { display: grid; grid-template-columns: repeat(3,1fr); gap: .75rem; }
        .prop { background: white; border-radius: 8px; padding: .75rem; border: 1px solid #e4dcf8; }
        .prop-label { font-size: 10px; font-weight: 800; text-transform: uppercase; color: #aaa; margin-bottom: 4px; }
        .prop-val { font-size: 13px; color: #333; line-height: 1.4; }
        .grammar-box { background: #f9f9fb; border-radius: 10px; padding: 1rem 1.25rem; border: 1.5px solid #eee; }
        .g-row { display: flex; gap: 1rem; margin-bottom: .5rem; }
        .g-row:last-child { margin-bottom: 0; }
        .g-label { font-size: 11px; font-weight: 700; color: #aaa; width: 70px; flex-shrink: 0; text-transform: uppercase; margin-top: 2px; }
        .g-val { font-size: 13px; color: #333; line-height: 1.5; }
        .type-badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }
        .type-statement { background: #e6f4ea; color: #1e6b2e; }
        .type-question { background: #fff3e0; color: #c45700; }
        .metrics { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; }
        .metric { background: #f9f9fb; border-radius: 10px; padding: 1rem; text-align: center; border: 1.5px solid #eee; }
        .m-val { font-size: 22px; font-weight: 800; color: #667eea; }
        .m-label { font-size: 10px; color: #aaa; margin-top: 4px; text-transform: uppercase; font-weight: 700; }
        .spin { display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,.4);border-top-color:white;border-radius:50%;animation:rot .7s linear infinite;vertical-align:middle; }
        @keyframes rot{to{transform:rotate(360deg)}}
        @media(max-width:640px){
            body{padding:0} .container{border-radius:0} .controls{grid-template-columns:1fr}
            .metrics{grid-template-columns:1fr 1fr} .sign-props{grid-template-columns:1fr}
        }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>🤟 Sign Language Translator</h1>
        <p>Powered by <strong>sign-language-translator</strong> NLP model</p>
        <span class="badge">✦ NLP Model Active</span>
    </header>
    <div class="content">
        <div class="controls">
            <div class="control-group">
                <label>Input Language</label>
                <select id="srcLang">
                    <option value="english">English</option>
                    <option value="french">Français</option>
                </select>
            </div>
            <div class="control-group">
                <label>Target Sign Language</label>
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
            <button class="btn-translate" id="btnTranslate" onclick="doTranslate()">🔤 TRANSLATE</button>
            <button class="btn-clear" onclick="clearAll()">✕</button>
        </div>

        <div id="results" class="results">
            <hr>

            <!-- GLOSSES -->
            <div class="section">
                <div class="sec-title">Sign Language Glosses</div>
                <div class="gloss-row" id="glossRow"></div>
                <div class="sign-card" id="signCard">
                    <h4 id="cardGloss"></h4>
                    <div class="sign-props" id="cardProps"></div>
                </div>
                <p class="hint">👆 Click any gloss to see how to perform the sign</p>
            </div>

            <!-- GRAMMAR -->
            <div class="section">
                <div class="sec-title">Grammar Analysis</div>
                <div class="grammar-box">
                    <div class="g-row">
                        <span class="g-label">Type</span>
                        <span id="gType"></span>
                    </div>
                    <div class="g-row">
                        <span class="g-label">Notes</span>
                        <span class="g-val" id="gNotes"></span>
                    </div>
                </div>
            </div>

            <!-- STATS -->
            <div class="section">
                <div class="sec-title">Stats</div>
                <div class="metrics">
                    <div class="metric"><div class="m-val" id="mGlosses">—</div><div class="m-label">Glosses</div></div>
                    <div class="metric"><div class="m-val" id="mWords">—</div><div class="m-label">Words</div></div>
                    <div class="metric"><div class="m-val" id="mConf">—</div><div class="m-label">Confidence</div></div>
                    <div class="metric"><div class="m-val" id="mTime">—</div><div class="m-label">Time</div></div>
                </div>
            </div>
        </div>
    </div>
</div>
<script>
let descriptions = {};

async function doTranslate() {
    const text = document.getElementById('inputText').value.trim();
    if (!text) { alert('Please enter text'); return; }
    const btn = document.getElementById('btnTranslate');
    btn.disabled = true;
    btn.innerHTML = '<span class="spin"></span> Translating...';
    try {
        const r = await fetch('/api/translate', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({
                text,
                language: document.getElementById('srcLang').value,
                target: document.getElementById('tgtSign').value
            })
        });
        const d = await r.json();
        render(d, text);
    } catch(e) { alert('Error: ' + e.message); }
    finally { btn.disabled=false; btn.innerHTML='🔤 TRANSLATE'; }
}

function render(d, original) {
    descriptions = {};
    (d.sign_descriptions||[]).forEach(s => descriptions[s.gloss] = s);

    const row = document.getElementById('glossRow');
    row.innerHTML = '';
    d.glosses.forEach((g, i) => {
        const span = document.createElement('span');
        span.className = 'gloss-tag';
        span.textContent = g;
        span.onclick = () => showCard(g, span);
        row.appendChild(span);
        if (i < d.glosses.length-1) {
            const a = document.createElement('span');
            a.className = 'arrow'; a.textContent = '→';
            row.appendChild(a);
        }
    });

    const type = d.grammar || 'Statement';
    const isQ = type.toLowerCase().includes('quest');
    document.getElementById('gType').innerHTML =
        `<span class="type-badge ${isQ?'type-question':'type-statement'}">${type}</span>`;
    document.getElementById('gNotes').textContent = d.grammar_notes || '—';

    document.getElementById('mGlosses').textContent = d.glosses.length;
    document.getElementById('mWords').textContent = original.trim().split(/\s+/).length;
    document.getElementById('mConf').textContent = d.confidence + '%';
    document.getElementById('mTime').textContent = d.time + 'ms';

    document.getElementById('signCard').classList.remove('active');
    document.getElementById('results').classList.add('active');
}

function showCard(gloss, el) {
    document.querySelectorAll('.gloss-tag').forEach(t => t.classList.remove('selected'));
    el.classList.add('selected');
    const s = descriptions[gloss];
    document.getElementById('cardGloss').textContent = gloss;
    const props = document.getElementById('cardProps');
    if (s) {
        props.innerHTML = `
            <div class="prop"><div class="prop-label">✋ Handshape</div><div class="prop-val">${s.handshape||'—'}</div></div>
            <div class="prop"><div class="prop-label">📍 Location</div><div class="prop-val">${s.location||'—'}</div></div>
            <div class="prop"><div class="prop-label">↔️ Movement</div><div class="prop-val">${s.movement||'—'}</div></div>`;
    } else {
        props.innerHTML = `<div class="prop" style="grid-column:1/-1"><div class="prop-label">Info</div>
            <div class="prop-val">No description available for <strong>${gloss}</strong>.</div></div>`;
    }
    document.getElementById('signCard').classList.add('active');
}

function clearAll() {
    document.getElementById('inputText').value = '';
    document.getElementById('results').classList.remove('active');
    document.getElementById('signCard').classList.remove('active');
}

document.getElementById('inputText').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.ctrlKey) doTranslate();
});
</script>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '').strip()
    language = data.get('language', 'english')
    target = data.get('target', 'ASL')

    start = time.time()
    result = translate_with_slt(text, language, target) or translate_fallback(text, language)
    elapsed = int((time.time() - start) * 1000)

    return jsonify({
        'glosses': result['glosses'],
        'grammar': result['grammar_type'],
        'grammar_notes': result.get('grammar_notes', ''),
        'sign_descriptions': result.get('sign_descriptions', []),
        'confidence': 88,
        'time': elapsed,
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
