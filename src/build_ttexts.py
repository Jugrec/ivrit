# Builds content/ttexts.json (texts made of the words of the day) from build/ttexts_src.py:
#   python3 -I build/build_ttexts.py <ivrit_dir>
# Checks: every token is a course/lexicon/vocab word (prefixes ו ה ב ל מ ש כ stripped) or is in gloss/kf/names;
# no verb form taught after the text's lesson (build/forms.py); no em dash; reports how many words of the topic are used.
import json, re, sys, glob, importlib.util
ROOT = sys.argv[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
src = load("src", ROOT + "/build/ttexts_src.py")
sys.path.insert(0, ROOT + "/build"); import forms
NIK = re.compile("[֑-ׇ]")
def bare(s): return re.sub(r"[^א-ת]", "", NIK.sub("", s))
def plene(s):
    out, prev = "", ""
    for i, c in enumerate(s):
        out += c
        if c in "ֹֻ" and prev != "ו" and not (i + 1 < len(s) and s[i + 1] == "ו"): out += "ו"
        if not ("֑" <= c <= "ׇ"): prev = c
    return out
def keys(w): return {bare(w), bare(plene(w))}
known = set()
def add(w):
    if w: known.update(keys(w))
for f in glob.glob(ROOT + "/content/m*.json"):
    if "practice" in f: continue
    for w in json.load(open(f, encoding="utf-8")).get("words", []):
        add(w["he"]); add(w.get("pl"))
        for x in (w.get("forms") or "").split("·"): add(x.strip())
for w in json.load(open(ROOT + "/content/lexicon.json", encoding="utf-8"))["words"]:
    add(w[0])
    for x in (w[2] if len(w) > 2 and w[2] else "").split("·"): add(x.strip())
VOC = json.load(open(ROOT + "/content/vocab.json", encoding="utf-8"))["topics"]
for t in VOC:
    for w in t["words"]:
        for x in w["he"].split(): add(x)
PFX = "והבלמשכ"
def cands(tok):
    c = [tok]
    for _ in range(3): c += [x[1:] for x in c if len(x) > 2 and x[0] in PFX]
    return c
def is_in(tok, s): return any(c in s for c in cands(tok))
ORDER = lambda l: (int(re.match(r"m(\d+)l(\d+)", l).group(1)), int(re.match(r"m(\d+)l(\d+)", l).group(2)))

names = {k for n, _ in src.NAMES for w in n.split() for k in keys(w)}
out, bad = [], False
for t in src.TEXTS:
    # a gloss word the course already has is not "new": keep it on tap only
    old = [g for g in t["gloss"] if all(is_in(bare(plene(w)), known) or is_in(bare(w), known) for w in g[0].split())]
    t["gloss"] = [g for g in t["gloss"] if g not in old]; t["kf"] = t["kf"] + old
    t["kf"] = t["kf"] + [c for c in src.COMMON if any(bare(w) in bare(" ".join(h for h, _ in t["lines"])) for w in c[0].split()) and c not in t["kf"]]
    extra = {k for he, _ in t["gloss"] + t["kf"] for w in he.split() for k in keys(w)}
    unknown, late = [], []
    for he, ru in t["lines"]:
        if "—" in he + ru: print(t["id"], "em dash"); bad = True
        for tok in he.split():
            k, k2 = bare(plene(tok)), bare(tok)
            if not k: continue
            if not (is_in(k, known) or is_in(k2, known) or is_in(k, names) or is_in(k, extra) or is_in(k2, extra)): unknown.append(tok)
            f = forms.form_of(re.sub(r"[^ְ-ת]", "", tok))
            if f and ORDER(f[0]) > ORDER(t["after"]): late.append(tok + " (" + f[1] + ", " + f[0] + ")")
    # topic words used: a word counts if its bare form (or the base named in a kf note "от X") occurs in the text
    topic = next(x for x in VOC if x["id"] == t["topic"])
    textkeys = set()
    for he, _ in t["lines"]:
        for tok in he.split(): textkeys.update(cands(bare(tok)))
    bases = {bare(m) for _, ru in t["kf"] for m in re.findall(r"от ([֐-׿ ]+?)(?:\)|$|,)", ru)}
    used = [w["id"] for w in topic["words"] if bare(w["he"]) in textkeys or bare(w["he"]) in bases
            or (" " in w["he"] and bare(w["he"].replace(" ", "")) in bare(" ".join(h for h, _ in t["lines"]).replace(" ", "")))]
    print("%-12s %-8s строк %d, слов темы %d из %d%s%s" % (t["id"], t["after"], len(t["lines"]), len(used), len(topic["words"]),
          ("; неизвестны: " + " ".join(unknown)) if unknown else "", ("; рано: " + " ".join(late)) if late else ""))
    if unknown or late: bad = True
    out.append({"id": t["id"], "topic": t["topic"], "title": t["title"], "after": t["after"], "words": used,
                "he": [a for a, _ in t["lines"]], "ru": [b for _, b in t["lines"]], "gloss": [list(g) for g in t["gloss"]],
                "kf": [list(g) for g in src.NAMES] + [list(g) for g in t["kf"]],
                "questions": [{"id": t["id"] + "q" + str(i + 1), "k": "story", "type": "choice", "prompt": p, "options": o, "answer": 0, "note": n}
                              for i, (p, o, n) in enumerate(t["q"])]})
if bad: sys.exit(1)
json.dump({"texts": out}, open(ROOT + "/content/ttexts.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("ttexts ok:", len(out))
