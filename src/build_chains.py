# Builds content/chains.json («Строим фразы» + diary samples) from build/chains_src.txt
#   python3 -I build_chains.py <ivrit_dir>
import json, re, sys, glob
ROOT = sys.argv[1]
sys.path.insert(0, ROOT + "/build"); import ktiv
ktiv.load_known(ROOT)
NIK = re.compile("[֑-ׇ]")
def bare(s): return re.sub(r"\s+", " ", re.sub("[^א-ת ]", "", NIK.sub("", (s or "").replace("־", " ")))).strip()

def expand(s):
    m = re.search(r"\{([^{}]*)\}|\(([^()]*)\)", s)
    if not m: return [re.sub(r"\s+", " ", s).strip()]
    opts = m.group(1).split("|") if m.group(1) is not None else ["", m.group(2)]
    out = []
    for o in opts:
        for e in expand(s[:m.start()] + o + s[m.end():]):
            if e not in out: out.append(e)
    return out
def display(s):  # first choice, optional parts left out
    s = re.sub(r"\{([^{}|]*)\|[^{}]*\}", r"\1", s); s = re.sub(r"\([^()]*\)", "", s)
    return re.sub(r"\s+", " ", s).strip()

chains, diary, errors, cur, mode = [], {"full": [], "past": [], "now": []}, [], None, "chains"
for n, line in enumerate(open(ROOT + "/build/chains_src.txt", encoding="utf-8"), 1):
    line = line.rstrip("\n")
    if not line.strip(): continue
    if line.startswith("## diary"): mode = "diary"; dlevel = line.split()[2]; continue
    if mode == "chains" and re.match(r"# [a-z]\d+ \| ", line):
        cid, title, topic, after = [x.strip() for x in line[2:].split(" | ")]
        cur = {"id": cid, "title": title, "topic": topic, "after": after, "steps": []}; chains.append(cur); continue
    if line.startswith("#"): continue
    if "—" in line: errors.append("%d: em dash" % n)
    p = [x.strip() for x in line.split(" | ")]
    if mode == "diary":
        he = [x.strip() for x in p[1].split("/")]; ru = [x.strip() for x in p[2].split("/")]
        if len(he) != 3 or len(ru) != 3: errors.append("%d: diary needs 3+3" % n)
        diary[dlevel].append({"t": p[0], "he": he, "ru": ru}); continue
    if len(p) not in (2, 3): errors.append("%d: fields" % n); continue
    ru, he = p[0], p[1]
    alts = [a.strip() for a in p[2].split(";")] if len(p) == 3 and p[2] else []
    acc = []
    for src in [he] + alts:
        for e in expand(src):
            if e not in acc: acc.append(e)
    for e in list(acc):
        f = ktiv.line(e)
        if bare(f) not in [bare(x) for x in acc]: acc.append(bare(f))
    cur["steps"].append({"ru": ru, "he": display(he), "accept": [display(he)] + [a for a in acc if a != display(he)]})

# every word must be known: course words and forms, vocab, lexicon (prefixes ו ה ב ל מ ש כ stripped)
kn = set(ktiv.KNOWN)
for f in glob.glob(ROOT + "/content/m*.json"):
    if "practice" in f: continue
    for w in json.load(open(f, encoding="utf-8")).get("words", []):
        for x in [w.get("he"), w.get("pl")] + (w.get("forms") or "").split("·"): kn.add(bare(x))
for t in json.load(open(ROOT + "/content/vocab.json", encoding="utf-8"))["topics"]:
    for w in t["words"]:
        kn.add(bare(w["he"])); [kn.add(bare(m)) for m in re.findall("[א-ת][א-ת֑-ׇ]*", w.get("gram", "") + " " + w.get("ex", ""))]
for w in json.load(open(ROOT + "/content/lexicon.json", encoding="utf-8"))["words"]:
    [kn.add(bare(x)) for x in [w[0]] + ((w[2] if len(w) > 2 and w[2] else "").split("·"))]
for f in glob.glob(ROOT + "/content/*practice.json") + [ROOT + "/content/stories.json"]:
    d = json.load(open(f, encoding="utf-8"))
    for t in d.get("texts", []) + d.get("episodes", []):
        for s in t.get("he", []):
            for tok in s.split(): kn.add(bare(tok))
def known(b):
    c = [b]
    for _ in range(3): c += [x[1:] for x in c if len(x) > 2 and x[0] in "והבלמשכ"]
    return any(x in kn for x in c)
unk = {}
for c in chains:
    if not 4 <= len(c["steps"]) <= 6: errors.append(c["id"] + ": steps %d" % len(c["steps"]))
    for s in c["steps"]:
        if not NIK.search(s["he"]): errors.append(c["id"] + ": no nikud")
        for a in s["accept"]:
            if NIK.search(a):
                for tok in a.split():
                    b = bare(tok)
                    if b and not known(b): unk.setdefault(tok.strip(".,!?"), c["id"])
for d in [x for lv in diary.values() for x in lv]:
    for s in d["he"]:
        for tok in s.split():
            b = bare(tok)
            if b and not known(b): unk.setdefault(tok.strip(".,!?"), "diary")
if errors: print("\n".join(errors)); sys.exit(1)
json.dump({"chains": chains, "diary": diary}, open(ROOT + "/content/chains.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("chains ok:", len(chains), "chains,", sum(len(c["steps"]) for c in chains), "steps,", {k: len(v) for k, v in diary.items()}, "diary themes")
print("words to check by eye:", "  ".join(k + "(" + v + ")" for k, v in unk.items()))
