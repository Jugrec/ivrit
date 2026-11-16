# Builds content/exams.json (ulpan-style tests, levels Aleph and Bet) from build/exams_src.txt
#   python3 -I build_exams.py <ivrit_dir>
import json, re, sys, glob
ROOT = sys.argv[1]
sys.path.insert(0, ROOT + "/build"); import ktiv
ktiv.load_known(ROOT)
NIK = re.compile("[֑-ׇ]")
def bare(s): return re.sub(r"\s+", " ", re.sub("[^א-ת ]", "", NIK.sub("", (s or "").replace("־", " ")))).strip()
NAMES = {"מיכאל", "נועה", "דנה", "דוד"}
exams, errors, ex, part = [], [], None, None
for n, line in enumerate(open(ROOT + "/build/exams_src.txt", encoding="utf-8"), 1):
    line = line.rstrip("\n")
    if not line.strip() or (line.startswith("# ") and not re.match(r"# [a-z]+ \|\| ", line)): continue
    if "—" in line: errors.append("%d: em dash" % n)
    p = [x.strip() for x in re.split(r"\s*\|\|\s*", line[1:].lstrip("#").strip())] if line[0] in "#?=!@~" else None
    if line.startswith("## "):
        part = {"id": p[0], "title": p[1], "items": []}; ex["parts"].append(part)
    elif line.startswith("# "):
        ex = {"id": p[0], "title": p[1], "after": p[2], "parts": []}; exams.append(ex)
    elif line[0] == "@": part["textTitle"] = line[1:].strip()
    elif line[0] == "~": part.setdefault("text", []).append(line[1:].strip())
    elif line[0] == "?":
        opts = [o.strip() for o in p[2].split(" | ")]
        right = [i for i, o in enumerate(opts) if o.startswith("*")]
        if len(right) != 1 or len(opts) < 2: errors.append("%d: one *right option" % n); continue
        opts = [o.lstrip("*") for o in opts]; opts = [opts[right[0]]] + [o for i, o in enumerate(opts) if i != right[0]]
        it = {"type": "choice", "prompt": p[0], "options": opts, "answer": 0}
        if p[1]: it["he"] = p[1]
        part["items"].append(it)
    elif line[0] == "=":
        if "___" not in p[1]: errors.append("%d: gap without ___" % n)
        acc = [a.strip() for a in p[2].split(";")]
        for a in list(acc):
            f = bare(ktiv.ktiv(a))
            if f not in [bare(x) for x in acc]: acc.append(f)
        part["items"].append({"type": "gap", "prompt": p[0], "he": p[1], "accept": acc})
    elif line[0] == "!":
        ex["writing"] = {"title": p[0], "task": p[1], "use": p[2]}
    else: errors.append("%d: ?" % n)
# known words (same sources as the other builders)
kn = set(NAMES)
for f in glob.glob(ROOT + "/content/m*.json"):
    if "practice" in f: continue
    for w in json.load(open(f, encoding="utf-8")).get("words", []):
        for x in [w.get("he"), w.get("pl")] + (w.get("forms") or "").split("·"): kn.update(bare(x).split())
for t in json.load(open(ROOT + "/content/vocab.json", encoding="utf-8"))["topics"]:
    for w in t["words"]: kn.update(bare(w["he"] + " " + w.get("gram", "") + " " + w.get("ex", "")).split())
for w in json.load(open(ROOT + "/content/lexicon.json", encoding="utf-8"))["words"]:
    for x in [w[0]] + ((w[2] if len(w) > 2 and w[2] else "").split("·")): kn.update(bare(x).split())
for f in glob.glob(ROOT + "/content/*practice.json") + [ROOT + "/content/stories.json"]:
    d = json.load(open(f, encoding="utf-8"))
    for t in d.get("texts", []) + d.get("episodes", []):
        for s in t.get("he", []): kn.update(bare(s).split())
def known(b):
    c = [b]
    for _ in range(3): c += [x[1:] for x in c if len(x) > 2 and x[0] in "והבלמשכ"]
    return any(x in kn for x in c)
unk = {}
for e in exams:
    if "writing" not in e: errors.append(e["id"] + ": no writing task")
    for pt in e["parts"]:
        hes = pt.get("text", []) + [pt.get("textTitle", "")]
        for it in pt["items"]:
            hes += [it.get("he", "")] + ([o for o in it.get("options", []) if NIK.search(o)]) + [a for a in it.get("accept", []) if NIK.search(a)]
            for o in it.get("options", []):
                if re.search("[א-ת]", o) and not NIK.search(o): errors.append("option without nikud: " + o)
        for h in hes:
            for tok in bare(h).split():
                if not known(tok): unk.setdefault(tok, e["id"])
if errors: print("\n".join(errors)); sys.exit(1)
json.dump({"exams": exams}, open(ROOT + "/content/exams.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
for e in exams: print("exam", e["id"], {p["id"]: len(p["items"]) for p in e["parts"]}, "text words:", sum(len(s.split()) for p in e["parts"] for s in p.get("text", [])))
print("words to check by eye:", " ".join(k + "(" + v + ")" for k, v in unk.items()))
