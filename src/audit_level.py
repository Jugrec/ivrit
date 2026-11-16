# Level audit: does any content use a word or a verb form before the lesson that introduces it?
#   python3 -I audit_level.py <ivrit_dir>  -> prints a report
# Position of content: lessons in course order; practice items by "after"; story episodes by "after" (or none).
# A token is "introduced" at the first lesson whose theory, words or exercises contain it (with up to 3 prefix letters
# stripped). Words of modules 1-3 (lexicon) count as known from the start.
import json, re, sys, glob
ROOT = sys.argv[1]
NIK = re.compile("[֑-ׇ]")
HEB = re.compile("[א-ת][א-ת֑-ׇ'״׳\"]*")
def bare(t): return re.sub("[^א-ת]", "", NIK.sub("", t))
def toks(s): return [bare(m) for m in HEB.findall(s or "") if len(bare(m)) >= 2]
def variants(b):
    v = [b]
    for _ in range(3): v += [x[1:] for x in v if len(x) > 2 and x[0] in "והבלמשכ"]
    return v
def texts_of(o):  # every Hebrew string inside an object
    if isinstance(o, str): yield o
    elif isinstance(o, list):
        for x in o: yield from texts_of(x)
    elif isinstance(o, dict):
        for k, x in o.items():
            if k in ("ru", "prompt", "title", "goal", "role", "task", "tr", "explain"): continue
            yield from texts_of(x)
aleph = json.load(open(ROOT + "/content/aleph.json"))
order, intro = [], {}
lex = {bare(w[0]) for w in json.load(open(ROOT + "/content/lexicon.json"))["words"]}
for x in json.load(open(ROOT + "/content/lexicon.json"))["words"]:
    for f in (x[2] if len(x) > 2 and x[2] else "").split("·"): lex.add(bare(f))
units = [json.load(open(ROOT + "/content/" + f)) for f in aleph["units"] if f.startswith("m")]
words = {}
for u in units:
    for w in u.get("words", []): words[w["id"]] = w
for u in units:
    for l in u["lessons"]:
        pos = len(order); order.append(l["id"])
        src = list(texts_of(l.get("theory", []))) + list(texts_of(l.get("exercises", []))) + list(texts_of(l.get("hard", [])))
        for wid in l.get("words", []):
            w = words.get(wid, {}); src += [w.get("he", ""), w.get("pl", "") or ""] + (w.get("forms") or "").split("·")
        for s in src:
            for t in toks(s): intro.setdefault(t, pos)
P = {lid: i for i, lid in enumerate(order)}
MOD = lambda pos: int(re.match(r"m(\d+)", order[pos]).group(1))
# verb forms recognised by their pointing (binyan + tense), with the module that teaches them
SH, HI, TS, SE, PA, QA, HO, DG = "ְ", "ִ", "ֵ", "ֶ", "ַ", "ָ", "ֹ", "ּ"
L = "[א-ת][ׁׂ]?" + DG + "?"   # one letter (with shin/sin dot and dagesh)
PATS = [
 (11, "прошедшее пааль/1-2 лицо", re.compile("^(?:[וש]" + "[ְ-ּ]*)?.*" + L + SH + "(?:ת" + DG + "?" + HI + "י|ת" + DG + "?" + QA + "|ת" + DG + "?" + SH + "|נוּ|ת" + DG + "?" + SE + "[םן])$")),
 (11, "прошедшее ל״ה", re.compile(".*" + HI + "י(?:ת" + HI + "י|ת" + QA + "|ת" + SH + "|נוּ)$")),
 (11, "прошедшее пааль 3 л.", re.compile("^(?:[ו][ְ-ּ]*)?" + L + QA + L + SH + L + "(?:" + QA + "ה|וּ)$")),
 (12, "прошедшее hифъиль", re.compile("^(?:[ו][ְ-ּ]*)?ה" + HI + L + SH + L + HI + "י" + L + "$")),
 (12, "прошедшее hитпаэль", re.compile("^(?:[ו][ְ-ּ]*)?ה" + HI + "ת" + SH)),
 (12, "прошедшее нифъаль", re.compile("^(?:[ו][ְ-ּ]*)?נ" + HI + L + SH + L + PA + L + "$")),
 (14, "будущее пааль", re.compile("^(?:[ו][ְ-ּ]*)?[אתינ]" + DG + "?[" + HI + SE + "]" + L + SH + L + HO + L + "(?:" + HI + "י|וּ)?$")),
 (16, "будущее пиэль", re.compile("^(?:[ו][ְ-ּ]*)?[אתינ]" + DG + "?[ְֲ]" + L + PA + L + "[" + TS + SH + "]" + L + "(?:" + HI + "י|וּ)?$")),
 (16, "будущее hифъиль", re.compile("^(?:[ו][ְ-ּ]*)?[אתינ]" + DG + "?" + PA + L + SH + L + HI + "י" + L + "(?:" + HI + "י|וּ)?$")),
 (17, "будущее hитпаэль", re.compile("^(?:[ו][ְ-ּ]*)?[אתינ]" + DG + "?[" + HI + SE + "]ת" + DG + "?" + SH)),
]
def ptoks(st): return [m.strip("'\"״׳") for m in HEB.findall(st or "")]
known_word = set()
for w in words.values():
    for x in [w.get("he"), w.get("pl")] + (w.get("forms") or "").split("·"): known_word.add(bare(x or ""))
def gram_of(tok):
    b = bare(tok)
    if b in lex or b in known_word or len(b) < 3: return None
    for mod, name, rx in PATS:
        if rx.match(tok): return mod, name
    return None
def first(t):
    best = None
    for v in variants(t):
        if v in lex: return -1
        if v in intro and (best is None or intro[v] < best): best = intro[v]
    return best
def check(where, pos, strings, gloss=()):
    g = set()
    for x in gloss: g.update(variants(bare(x)))
    gram, vocab, unknown = {}, set(), set()
    for s in strings:
        for pt in ptoks(s):
            gm = gram_of(pt)
            if gm and gm[0] > MOD(pos) and not (set(variants(bare(pt))) & g): gram.setdefault(pt, gm[1] + " (м" + str(gm[0]) + ")")
        for t in toks(s):
            if set(variants(t)) & g: continue
            f = first(t)
            if f is None: unknown.add(t)
            elif f > pos: vocab.add(t)
    return gram, vocab, unknown
report = []
# lessons: verb forms from later grammar modules
for u in units:
    for l in u["lessons"]:
        pos = P[l["id"]]
        strs = list(texts_of(l.get("exercises", []))) + list(texts_of(l.get("hard", []))) + list(texts_of(l.get("theory", [])))
        gr, vo, un = check(l["id"], pos, strs)
        if gr: report.append((l["id"] + " (урок)", gr, set(), set()))
for f in sorted(glob.glob(ROOT + "/content/m*-practice.json"), key=lambda x: int(re.search(r"/m(\d+)-", x).group(1))):
    d = json.load(open(f))
    for kind in ("texts", "writing", "dialogs"):
        for it in d.get(kind, []):
            pos = P[it["after"]]
            strs = [it.get("use", "")] if kind == "writing" else list(texts_of(it))
            gr, vo, un = check(it["id"], pos, strs, [x[0] for x in it.get("gloss", [])])
            report.append((it["id"] + " (" + it["after"] + ")", gr, vo, un))
st = json.load(open(ROOT + "/content/stories.json"))
for e in st["episodes"]:
    gl = [x[0] for x in e.get("gloss", [])] + [x[0] for x in e.get("kf", [])]
    found = {}
    for s2 in e["he"]:
        for pt in ptoks(s2):
            gm = gram_of(pt)
            if gm: found.setdefault(gm[0], []).append(pt)
    print(e["id"], "[" + e.get("level", "") + "]", "grammar:", {k: v[:4] for k, v in sorted(found.items())})
for name, gr, vo, un in report:
    if not gr: continue
    print(name, "\n   " + "  ".join(t + " (" + w + ")" for t, w in gr.items()))
print("\nvocabulary ahead, not glossed (count per item):", sum(1 for r in report if r[2]), "items")
