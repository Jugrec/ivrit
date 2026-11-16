# Builds content/vocab.json (thematic "words of the day") from build/vocab_src/*.txt
#   python3 -I build_vocab.py <ivrit_dir>
# Source line: he | translit | ru | grammar | example he | example ru
# Topic header: "# id | Title"
import json, os, re, sys, glob, unicodedata

ROOT = sys.argv[1]
SRC = ROOT + "/build/vocab_src"
NIK = re.compile("[֑-ׇ]")
HEB = re.compile("[א-ת]")
LAT = re.compile("[A-Za-gi-z\u00C0-\u024F]")   # h is used for ה, as in the course

def bare(s):
    s = NIK.sub("", s).replace("־", " ").replace("׳", "'").replace("'", "")
    s = re.sub(r"[^א-ת ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

def fix_tr(t):
    # Latin vowels with acute -> Cyrillic + combining acute
    m = {"á": "а́", "é": "е́", "ó": "о́", "í": "и́", "ú": "у́", "a": "а", "e": "е", "o": "о", "c": "с", "p": "р", "x": "х", "y": "у"}
    return "".join(m.get(ch, ch) for ch in unicodedata.normalize("NFC", t))

# cloze: find the headword (or a form named in the grammar note) inside the example sentence
sys.path.insert(0, ROOT + "/build"); import ktiv
HR = re.compile("[\u05D0-\u05EA][\u05D0-\u05EA\u0591-\u05C7]*(?:[ ][\u05D0-\u05EA][\u05D0-\u05EA\u0591-\u05C7]*)*")
def letters(tok):  # -> list of (letter, marks)
    out = []
    for c in tok:
        if "\u05D0" <= c <= "\u05EA": out.append([c, ""])
        elif NIK.match(c) and out: out[-1][1] += c
    return out
def tokw(t, k=0):  # pointed letters of a token from letter k on (punctuation dropped)
    return "".join(l + m for l, m in letters(t)[k:])
def strip_pre(word, keys, maxk=3):
    for k in range(0, maxk + 1):
        if k > len(word) or (k and word[k - 1] not in "והבלמשכ"): break
        if word[k:] in keys and len(word) - k >= 2: return k
    return None
def cloze(he, gram, ex):
    toks = ex.split(" ")
    if "{" in ex:   # explicit gap marked in the source: pre{answer}
        i = next(j for j, t in enumerate(toks) if "{" in t)
        pre = toks[i].split("{")[0]; ans = ex.split("{")[1].split("}")[0]
        n = ans.count(" ") + 1
        cz = {"i": i, "pre": re.sub(r"[^\u05D0-\u05EA\u0591-\u05C7]", "", pre), "ans": ans}
    else:
        cz = None
        hw = he.split(" ")
        if len(hw) > 1:   # multi-word headword: consecutive tokens, the article ה allowed inside
            hb = [bare(x) for x in hw]
            for i in range(len(toks) - len(hw) + 1):
                w0 = "".join(l for l, _ in letters(toks[i]))
                k = strip_pre(w0, {hb[0]})
                if k is None: continue
                ok = True
                for j in range(1, len(hw)):
                    wj = "".join(l for l, _ in letters(toks[i + j]))
                    if wj != hb[j] and not (wj[:1] == "ה" and wj[1:] == hb[j]): ok = False; break
                if ok:
                    L = letters(toks[i]); n = len(hw)
                    cz = {"i": i, "pre": "".join(l + m for l, m in L[:k]),
                          "ans": " ".join([tokw(toks[i], k)] + [tokw(toks[i + j]) for j in range(1, n)])}
                    break
        else:
            keys = {}
            for c in [he] + [m.strip() for m in HR.findall(gram or "")]:
                if " " not in c.strip(): keys.setdefault(bare(c), c)
            for i, t in enumerate(toks):
                L = letters(t); word = "".join(l for l, _ in L)
                k = strip_pre(word, keys)
                if k is not None:
                    n = 1; cz = {"i": i, "pre": "".join(l + m for l, m in L[:k]), "ans": tokw(t, k)}; break
        if not cz: return None
    if n > 1: cz["n"] = n
    cz["acc"] = list(dict.fromkeys([bare(ktiv.line(cz["ans"])), bare(cz["ans"])]))   # full spelling first: it is shown as the answer
    return cz

# grammar level of an example: the latest lesson among its verb forms (past / future / binyanim), see forms.py
import forms
LEX0 = {bare(w[0]) for w in json.load(open(ROOT + "/content/lexicon.json", encoding="utf-8"))["words"]}
def lkey(lid): m = re.match(r"m(\d+)l(\d+)", lid); return (int(m.group(1)), int(m.group(2)))
# forms the pattern detector does not catch (imperatives, irregular futures), checked by eye
LEVEL_FIX = {"פְּתַח אֶת": "m18l1", "זְרֹק אֶת": "m18l1", "תֵּן לִי": "m18l2", "נִפָּגֵשׁ": "m17l3", "נַעֲשֶׂה": "m14l2",
             "תִּכְתְּבִי": "m14l1", "תִּפְתְּחוּ": "m14l1", "תְּכַבֶּה": "m16l2", "יֵרֵד": "m14l3", "נָתַנּוּ": "m11l1"}
def level_of(ex):
    fix = [v for k, v in LEVEL_FIX.items() if k in ex]
    if fix: return max(fix, key=lkey)
    found = [forms.form_of(t)[0] for t in re.findall("[\u05D0-\u05EA][\u05D0-\u05EA\u0591-\u05C7]*", ex.replace("{", "").replace("}", "")) if forms.form_of(t) and bare(t) not in LEX0]
    return max(found, key=lkey) if found else None

# words the learner already has in the course
known = set()
for f in glob.glob(ROOT + "/content/m*.json") + [ROOT + "/content/drill1.json", ROOT + "/content/roots1.json"]:
    if "practice" in f: continue
    for w in json.load(open(f, encoding="utf-8")).get("words", []):
        known.add(bare(w["he"]))
lex = json.load(open(ROOT + "/content/lexicon.json", encoding="utf-8"))
for w in lex["words"]:
    known.add(bare(w[0]))

# extra examples: build/vocab_src/ex*.txt  "headword | example | translation"
EXTRA = {}
for path in sorted(glob.glob(SRC + "/ex*.txt")):
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if not line.strip() or line.startswith("#"): continue
        p = [x.strip() for x in line.split("|")]
        if len(p) != 3: print("bad example line", path, n); sys.exit(1)
        EXTRA[p[0]] = (p[1], p[2])

topics, seen, errors, dropped = [], {}, [], []
for path in sorted(glob.glob(SRC + "/[0-9]*.txt")):
    cur = None
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip(): continue
        where = os.path.basename(path) + ":" + str(n)
        if line.startswith("#"):
            tid, title = [x.strip() for x in line[1:].split("|")]
            cur = {"id": tid, "title": title, "words": []}; topics.append(cur); continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) != 6: errors.append(where + ": expected 6 fields, got %d" % len(parts)); continue
        he, tr, ru, gram, ex, exru = parts
        if not ex and he in EXTRA: ex, exru = EXTRA.pop(he)
        tr = fix_tr(tr)
        if not HEB.search(he) or not NIK.search(he): errors.append(where + ": headword without nikud: " + he)
        if LAT.search(tr): errors.append(where + ": latin letters in translit: " + tr)
        if "{" in ex and (ex.count("{") != 1 or ex.count("}") != 1): errors.append(where + ": bad gap braces")
        if "—" in line: errors.append(where + ": em dash")
        if bool(ex) != bool(exru): errors.append(where + ": example without translation")
        if ex and not NIK.search(ex): errors.append(where + ": example without nikud")
        key = bare(he)
        if key in known: dropped.append(he + " (уже в курсе)"); continue
        if key in seen: dropped.append(he + " (повтор, есть в " + seen[key] + ")"); continue
        seen[key] = cur["id"]
        w = {"id": cur["id"] + ":" + key.replace(" ", "_"), "he": he, "tr": tr, "ru": ru}
        if gram: w["gram"] = gram
        if ex:
            cz = cloze(he, gram, ex)
            # a cloze card asks for the form in the sentence: verbs wait for the present of all binyanim and the
            # infinitive (m7), other words for adjectives and plurals (m5); tenses and moods for their own lesson
            base = "m7l2" if (gram and ("наст." in gram or "прош." in gram)) or re.match("^ל[\u05B0-\u05BC]*[\u05D0-\u05EA]", he) and " " not in he and (gram or "").startswith("наст") else "m5l1"
            need = level_of(ex)
            if cz: cz["after"] = max([base] + ([need] if need else []), key=lkey)
            ex = ex.replace("{", "").replace("}", "")
            w["ex"] = ex; w["exru"] = exru
            if cz: w["cz"] = cz
        cur["words"].append(w)

if errors:
    print("\n".join(errors)); sys.exit(1)
if EXTRA: print("examples for unknown headwords:", ", ".join(EXTRA))
# every word of every example must be a known word or form (catches misspelled nikud)
kn = set(known)
for t in topics:
    for w in t["words"]:
        kn.add(bare(w["he"]))
        for m in re.findall("[\u05D0-\u05EA][\u05D0-\u05EA\u0591-\u05C7]*", w.get("gram", "")): kn.add(bare(m))
for f in glob.glob(ROOT + "/content/m*.json"):
    if "practice" in f: continue
    for w in json.load(open(f, encoding="utf-8")).get("words", []):
        kn.add(bare(w.get("pl") or "")); [kn.add(bare(x)) for x in (w.get("forms") or "").split("·")]
for w in lex["words"]:
    [kn.add(bare(x)) for x in ((w[2] if len(w) > 2 and w[2] else "").split("·"))]
def known_tok(b):
    c = [b]
    for _ in range(3): c += [x[1:] for x in c if len(x) > 2 and x[0] in "והבלמשכ"]
    return any(x in kn for x in c)
unk = {}
for t in topics:
    for w in t["words"]:
        for tok in w.get("ex", "").split():
            b = bare(tok)
            if b and not known_tok(b): unk.setdefault(tok.strip(".,!?:\"«»"), w["he"])
print("example words to check by eye:", len(unk))
print("  " + "  ".join(k + "(" + v + ")" for k, v in unk.items()))
out = {"note": "Слова дня: тематический словарь для ежедневных карточек (сверх слов уроков).", "topics": topics}
json.dump(out, open(ROOT + "/content/vocab.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("vocab ok:", sum(len(t["words"]) for t in topics), "words in", len(topics), "topics;",
      sum(1 for t in topics for w in t["words"] if "cz" in w), "cloze of", sum(1 for t in topics for w in t["words"] if "ex" in w), "examples")
for t in topics:
    for w in t["words"]:
        if "ex" in w and "cz" not in w: print("  no cloze:", w["he"], "|", w["ex"])
for t in topics: print("  ", t["id"], len(t["words"]))
if dropped: print("dropped:", ", ".join(dropped))
