# Builds content/rootfam.json (root families + word patterns) from build/roots_src/families.txt
#   python3 -I build_roots.py <ivrit_dir>
# Checks: nikud, no latin in translit, root letters present in order, same spelling as course/vocab words.
import json, re, sys, glob, unicodedata
ROOT = sys.argv[1]
NIK = re.compile("[֑-ׇ]")
FIN = str.maketrans("ךםןףץ", "כמנפצ")
def bare(s): return re.sub(r"[^א-ת]", "", NIK.sub("", s))
def fix_tr(t):
    m = {"á": "а́", "é": "е́", "ó": "о́", "í": "и́", "ú": "у́"}
    return "".join(m.get(c, c) for c in unicodedata.normalize("NFC", t))

PATTERNS = {
 "pa":       ["קָטַל", "паъаль: «он сделал»"],
 "piel":     ["קִטֵּל", "пиэль: «он сделал» (часто усиленное или направленное действие)"],
 "hifil":    ["הִקְטִיל", "hифъиль: заставил, вызвал, сделал так, чтобы"],
 "hitpael":  ["הִתְקַטֵּל", "hитпаэль: действие над собой или друг с другом"],
 "nifal":    ["נִקְטַל", "нифъаль: «сделалось само», страдательное"],
 "miktal":   ["מִקְטָל", "место или предмет"],
 "maktel":   ["מַקְטֵל", "инструмент, прибор"],
 "kattal":   ["קַטָּל", "профессия"],
 "kotel":    ["קוֹטֵל", "тот, кто делает (настоящее время паъаль)"],
 "mekatel":  ["מְקַטֵּל", "тот, кто делает (настоящее время пиэль)"],
 "ktila":    ["קְטִילָה", "название действия (от паъаль)"],
 "kittul":   ["קִטּוּל", "название действия (от пиэль)"],
 "haktala":  ["הַקְטָלָה", "название действия (от hифъиль)"],
 "katul":    ["קָטוּל", "результат: «сделанный»"],
 "mekuttal": ["מְקֻטָּל", "результат: «сделанный» (от пиэль)"],
 "segol":    ["קֶטֶל", "существительное-сеголат"],
 "other":    ["", "другое слово этого корня"],
}

known = {}
for f in glob.glob(ROOT + "/content/m*.json"):
    if "practice" in f: continue
    for w in json.load(open(f, encoding="utf-8")).get("words", []): known.setdefault(bare(w["he"]), w["he"])
for t in json.load(open(ROOT + "/content/vocab.json", encoding="utf-8"))["topics"]:
    for w in t["words"]: known.setdefault(bare(w["he"]), w["he"])

fams, errors, warn, cur, seen = [], [], [], None, set()
for n, line in enumerate(open(ROOT + "/build/roots_src/families.txt", encoding="utf-8"), 1):
    line = line.strip()
    if not line: continue
    if line.startswith("#"):
        r, ru = [x.strip() for x in line[1:].split("|")]
        letters = [c for c in NIK.sub("", r) if "א" <= c <= "ת"]
        cur = {"root": r, "ru": ru, "letters": "".join(letters), "words": []}; fams.append(cur); continue
    p = [x.strip() for x in line.split("|")]
    if len(p) != 4: errors.append("%d: 4 fields expected" % n); continue
    he, tr, ru, pat = p; tr = fix_tr(tr)
    if not NIK.search(he): errors.append("%d: no nikud %s" % (n, he))
    if re.search("[A-Za-gi-zÀ-ɏ]", tr): errors.append("%d: latin in %s" % (n, tr))
    if pat not in PATTERNS: errors.append("%d: unknown pattern %s" % (n, pat))
    if "—" in line: errors.append("%d: em dash" % n)
    b = bare(he).translate(FIN); rl = cur["letters"].translate(FIN)
    # root letters must appear in order (weak letters may vanish in some forms: allow one missing י/ו/ה/נ)
    it = iter(b); missing = [c for c in rl if c not in it]
    if missing and not all(c in "יוהנ" for c in missing): errors.append("%d: root %s not in %s" % (n, cur["root"], he))
    if he in seen: errors.append("%d: duplicate %s" % (n, he))
    seen.add(he)
    if bare(he) in known and known[bare(he)] != he: warn.append("%s в словах курса: %s" % (he, known[bare(he)]))
    cur["words"].append({"he": he, "tr": tr, "ru": ru, "p": pat})

if errors: print("\n".join(errors)); sys.exit(1)
json.dump({"patterns": PATTERNS, "families": fams}, open(ROOT + "/content/rootfam.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("rootfam ok:", len(fams), "roots,", sum(len(f["words"]) for f in fams), "words")
for w in warn: print("  nikud differs:", w)
