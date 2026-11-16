# Builds content/situations.json (mini-dialogues for «Ситуации») from build/situations_src.txt
#   python3 -I build_situations.py <ivrit_dir>
import json, re, sys, glob
ROOT = sys.argv[1]
NIK = re.compile("[֑-ׇ]")
def bare(s): return re.sub(r"\s+", " ", re.sub("[^א-ת ]", "", NIK.sub("", (s or "").replace("־", " ")))).strip()
NAMES = {"יוליה", "איל", "מיכל", "דני"}
voc = json.load(open(ROOT + "/content/vocab.json", encoding="utf-8"))
topics = {t["id"]: t for t in voc["topics"]}
sits, errors, cur, dl = [], [], None, None
for n, line in enumerate(open(ROOT + "/build/situations_src.txt", encoding="utf-8"), 1):
    line = line.rstrip("\n")
    if not line.strip() or (line.startswith("# ")): continue
    if "—" in line: errors.append("%d: em dash" % n)
    if line.startswith("## "):
        tid, title = [x.strip() for x in line[3:].split(" | ")]
        if tid not in topics: errors.append("%d: unknown topic %s" % (n, tid))
        cur = {"id": tid, "title": title, "dialogs": []}; sits.append(cur); continue
    if line.startswith("### "):
        ttl, aft = [x.strip() for x in line[4:].split(" | ")]
        dl = {"title": ttl, "after": aft, "turns": []}; cur["dialogs"].append(dl); continue
    p = [x.strip() for x in line[1:].split(" | ")]
    if line[0] == ">":
        who, rest = line[1:].split(" | ", 1)
        lines = []
        for v in rest.split(" || "):
            q = [x.strip() for x in v.split(" | ")]
            if len(q) != 2: errors.append("%d: variant needs he | ru" % n); continue
            lines.append({"he": q[0], "ru": q[1]})
        dl["turns"].append({"who": who.strip(), "lines": lines, "opts": []})
    elif line[0] in "+-":
        if len(p) not in (2, 3): errors.append("%d: option needs he | ru [| why]" % n); continue
        o = {"he": p[0], "ru": p[1]}
        if len(p) == 3: o["why"] = p[2]
        if line[0] == "+": o["ok"] = True
        dl["turns"][-1]["opts"].append(o)
    else: errors.append("%d: ?" % n)
for s in sits:
    for d in s["dialogs"]:
        for t in d["turns"]:
            nok = sum(1 for o in t["opts"] if o.get("ok"))
            if nok < 1 or len(t["opts"]) - nok < 2: errors.append(s["id"] + " / " + d["title"] + ": need 1+ right and 2+ wrong")
            for x in [l["he"] for l in t["lines"]] + [o["he"] for o in t["opts"]]:
                if not NIK.search(x): errors.append("no nikud: " + x)
# known words: course, vocab (with phrases), lexicon, texts, stories
kn = set()
for f in glob.glob(ROOT + "/content/m*.json"):
    if "practice" in f: continue
    for w in json.load(open(f, encoding="utf-8")).get("words", []):
        for x in [w.get("he"), w.get("pl")] + (w.get("forms") or "").split("·"): kn.update(bare(x).split())
for t in voc["topics"]:
    for w in t["words"]:
        kn.update(bare(w["he"]).split()); kn.update(bare(w.get("gram", "") + " " + w.get("ex", "")).split())
for w in json.load(open(ROOT + "/content/lexicon.json", encoding="utf-8"))["words"]:
    for x in [w[0]] + ((w[2] if len(w) > 2 and w[2] else "").split("·")): kn.update(bare(x).split())
for f in glob.glob(ROOT + "/content/*practice.json") + [ROOT + "/content/stories.json", ROOT + "/content/chains.json"]:
    d = json.load(open(f, encoding="utf-8"))
    for t in d.get("texts", []) + d.get("episodes", []):
        for s in t.get("he", []): kn.update(bare(s).split())
    for c in d.get("chains", []):
        for st in c["steps"]: kn.update(bare(st["he"]).split())
kn |= NAMES
def known(b):
    c = [b]
    for _ in range(3): c += [x[1:] for x in c if len(x) > 2 and x[0] in "והבלמשכ"]
    return any(x in kn for x in c)
unk = {}
for s in sits:
    for d in s["dialogs"]:
        for t in d["turns"]:
            for x in [l["he"] for l in t["lines"]] + [o["he"] for o in t["opts"]]:
                for tok in bare(x).split():
                    if not known(tok): unk.setdefault(tok, s["id"])
# the full phrase list of each situation from vocab_src/05.txt (also phrases already in the course)
sys.path.insert(0, ROOT + "/build")
from build_vocab_tr import fix_tr
ph, tid = {}, None
for line in open(ROOT + "/build/vocab_src/05.txt", encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith("# "): tid = line[2:].split(" | ")[0].strip(); ph[tid] = []; continue
    q = [x.strip() for x in line.split("|")]
    if len(q) >= 3: ph[tid].append({"he": q[0], "tr": fix_tr(q[1]), "ru": q[2]})
for x in sits: x["phrases"] = ph.get(x["id"], [])
if errors: print("\n".join(errors)); sys.exit(1)
json.dump({"situations": sits}, open(ROOT + "/content/situations.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("situations ok:", len(sits), "situations,", sum(len(s["dialogs"]) for s in sits), "dialogs,", sum(len(d["turns"]) for s in sits for d in s["dialogs"]), "turns")
print("phrases per topic:", {s["id"]: len(topics[s["id"]]["words"]) for s in sits})
print("words to check by eye:", " ".join(k + "(" + v + ")" for k, v in unk.items()))
