# Builds content/stories.json from build/stories_src.py and checks every word:
#   python3 -I build_stories.py <ivrit_dir>
# A token is "known" if (after stripping prefixes ו ה ב ל מ ש כ) it matches a course/lexicon/vocab word or its forms,
# or is listed in the episode gloss (new words) or kf (forms of known words, shown on tap only).
import json, re, sys, glob, importlib.util
ROOT = sys.argv[1]
spec = importlib.util.spec_from_file_location("src", ROOT + "/build/stories_src.py"); src = importlib.util.module_from_spec(spec); spec.loader.exec_module(src)
NIK = re.compile("[֑-ׇ]")
def bare(s): return re.sub(r"[^א-ת]", "", NIK.sub("", s))
def plene(s):  # same idea as the app: holam/kubbutz -> ו
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
for t in json.load(open(ROOT + "/content/vocab.json", encoding="utf-8"))["topics"]:
    for w in t["words"]: add(w["he"])
names = set()
NAMES = getattr(src, "NAMES", [])
for n, _ in NAMES:
    for t in n.split(): names.update(keys(t))
for fam in json.load(open(ROOT + "/content/rootfam.json", encoding="utf-8"))["families"]:
    for w in fam["words"]: add(w["he"])

PFX = "והבלמשכ"
def is_known(tok, extra):
    cands = [tok]
    for _ in range(3):
        cands += [c[1:] for c in cands if len(c) > 2 and c[0] in PFX]
    return any(c in known or c in extra for c in cands)

out, report, bad = [], [], False
for ep in src.EPISODES:
    extra = set()
    kfs = set()
    name_set = {n for n, _ in NAMES}
    ep["gloss"] = [g for g in ep["gloss"] if g[0] not in name_set]   # proper names are not new words (they stay on tap via kf)
    for he, _ in ep["gloss"]:
        for t in he.split(): extra.update(keys(t))
    for he, _ in ep.get("kf", []):
        for t in he.split(): kfs.update(keys(t))
    toks = [t for s, _ in ep["lines"] for t in s.split()]
    unknown, n_gloss = [], 0
    for t in toks:
        k = bare(plene(t)); k2 = bare(t)
        if not k: continue
        if is_known(k, set()) or is_known(k2, set()) or is_known(k, names) or is_known(k, kfs) or is_known(k2, kfs): continue
        if is_known(k, extra) or is_known(k2, extra): n_gloss += 1; continue
        unknown.append(t)
    for s, ru in ep["lines"]:
        if "—" in s + ru: print(ep["id"], "em dash"); bad = True
    total = len([t for t in toks if bare(t)])
    report.append("%s: %d слов, новых по глоссарию %d (%.0f%%), неизвестных %d %s" % (ep["id"], total, n_gloss, 100 * n_gloss / total, len(unknown), " ".join(unknown)))
    if unknown: bad = True
    t = {"id": ep["id"], "title": ep["title"], "level": ep["level"], "after": ep["after"], "he": [a for a, _ in ep["lines"]], "ru": [b for _, b in ep["lines"]],
         "gloss": [list(g) for g in ep["gloss"]],
         "kf": [list(g) for g in NAMES] + [list(g) for g in ep.get("kf", [])] + [[w, "часть выражения " + he + ": " + ru] for he, ru in ep["gloss"] + NAMES if " " in he for w in he.split()],
         "questions": [{"id": ep["id"] + "q" + str(i + 1), "k": "story", "type": "choice", "prompt": p, "options": o, "answer": 0, "note": n} for i, (p, o, n) in enumerate(ep["q"])]}
    if ep.get("nikud"): t["nikud"] = ep["nikud"]
    if ep.get("plain"):
        # hand-written full spelling: same words, only vowel letters ו/י may be added
        assert len(ep["plain"]) == len(ep["lines"]), ep["id"]
        for (he, _), pl in zip(ep["lines"], ep["plain"]):
            a_, b_ = he.split(), pl.split()
            if len(a_) != len(b_): print(ep["id"], "word count differs:", pl); bad = True; continue
            for x, y in zip(a_, b_):
                bx, by = bare(x), bare(y); it = iter(by)
                if not all(c in it for c in bx) or any(c not in "וי" for c in re.sub("", "", by)) and len(by) - len(bx) != sum(1 for c in by if c in "וי") - sum(1 for c in bx if c in "וי"):
                    print(ep["id"], "check spelling:", x, "->", y); bad = True
        t["plain"] = ep["plain"]
    out.append(t)
print("\n".join(report))
if bad: sys.exit(1)
json.dump({"title": "Аня в Хайфе", "episodes": out}, open(ROOT + "/content/stories.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("stories ok:", len(out), "episodes")
