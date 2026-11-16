# Builds content/ktmap.json: pointed token (key keeps its nikud) -> full spelling without nikud (build/ktiv.py), for every pointed Hebrew token
# of the content whose full spelling differs from what the app derives itself (nikud dropped, ו added for holam/kubbutz).
# The app accepts the full spelling in typed answers made from pointed words (word cards, chains, cloze).
#   python3 -I build/build_ktmap.py <ivrit_dir>     (run after all other content builders)
import json, glob, re, sys
ROOT = sys.argv[1]
sys.path.insert(0, ROOT + "/build"); import ktiv
ktiv.load_known(ROOT)
NIK = re.compile("[֑-ׇ]")
TOK = re.compile("[א-ת֑-ׇ]+")
def plene(s):   # the app's own rule (index.html plene)
    out, base, i, ch = "", "", 0, list(s)
    while i < len(ch):
        c = ch[i]
        if c in "ֹֻ" and base != "ו":
            j = i + 1
            while j < len(ch) and "֑" <= ch[j] <= "ׇ": j += 1
            out += "".join(ch[i:j]) + ("" if j < len(ch) and ch[j] == "ו" else "ו"); i = j; continue
        if not ("֑" <= c <= "ׇ"): base = c
        out += c; i += 1
    return out
toks = set()
def walk(x):
    if isinstance(x, str):
        for t in TOK.findall(x):
            if NIK.search(t): toks.add(t)
    elif isinstance(x, list):
        for y in x: walk(y)
    elif isinstance(x, dict):
        for y in x.values(): walk(y)
for f in glob.glob(ROOT + "/content/*.json"):
    if f.endswith("ktmap.json"): continue
    walk(json.load(open(f, encoding="utf-8")))
m = {}
BAD = {"קוום", "גוור", "בווא", "נייכל", "וליילדים", "במייחד", "ליגוע", "לישוך", "ליפול", "ניהוג", "ניסוע", "מיגן"}   # checked by hand: not real spellings
for t in sorted(toks):
    k = ktiv.ktiv(t); bare = NIK.sub("", t)
    if len(bare) > 1 and re.fullmatch("[\u05D0-\u05EA]+", k) and k != bare and k != NIK.sub("", plene(t)):
        if k in BAD or k.startswith("מיה"): continue
        if t.startswith("מִ") and len(t) > 3 and t[3] == "\u05BC" or (t.startswith("מִ") and "\u05BC" in t[3:6] and bare not in ktiv.KNOWN): 
            if bare not in ktiv.KNOWN and k not in {"מילים", "מיטות", "מידות", "מיסים"}: continue   # prefix מִ (from): מִמּוֹסְקְבָה stays ממוסקבה
        m[t] = k
json.dump(m, open(ROOT + "/content/ktmap.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
# content/spell.json: every spelling the app knows (full spelling and "nikud dropped"), for the offline self-check of free writing
sp = set()
for t in toks:
    for v in (ktiv.ktiv(t), NIK.sub("", plene(t)), NIK.sub("", t)):
        if re.fullmatch("[\u05D0-\u05EA]{2,}", v): sp.add(v)
for v in m.values(): sp.add(v)
json.dump(" ".join(sorted(sp)), open(ROOT + "/content/spell.json", "w", encoding="utf-8"), ensure_ascii=False)
print("spell:", len(sp))
print("ktmap:", len(m), "of", len(toks), "tokens")
