# Full spelling (כתיב מלא) from pointed text, after the Academy rules, for display without nikud.
#   ktiv(word) -> unpointed word in full spelling
# Rules: holam/kubbutz -> ו; hirik in an open syllable -> י (also before dagesh), not on prefix letters ב כ ל מ ו ש ה;
# consonantal ו in the middle -> וו; consonantal י in the middle before a full vowel -> יי (not next to ו/י);
# plus a list of exceptions checked by hand.
import re
SHVA, HIRIK, TSERE, SEGOL, PATAH, QAMATS, HOLAM, KUBBUTZ, DAGESH = "ְ", "ִ", "ֵ", "ֶ", "ַ", "ָ", "ֹ", "ֻ", "ּ"
HATAF = "ֱֲֳ"
FULLV = "ִֵֶַָֹֻ" + HATAF
MARK = re.compile("[֑-ׇ]")
EXC = {  # bare pointed-less form of the pointed word -> full spelling
 "ירושלים": "ירושלים", "מים": "מים", "שמים": "שמים", "בית": "בית", "זית": "זית", "עין": "עין", "אמא": "אמא",
 "לא": "לא", "ראש": "ראש", "זאת": "זאת", "פה": "פה", "איפה": "איפה", "כה": "כה", "אניה": "אניה",
 "אם": "אם", "דוד": "דוד", "מן": "מן", "עם": "עם", "הנה": "הנה",
 "היתה": "הייתה", "היה": "היה", "היו": "היו", "בעיה": "בעיה", "קריה": "קריה", "ראיה": "ראיה", "מדי": "מדי",
 "יוליה": "יוליה", "תכנית": "תוכנית", "צהרים": "צוהריים", "בירוקרטיה": "בירוקרטיה", "היסטוריה": "היסטוריה", "ראיון": "ריאיון", "עכשו": "עכשיו", "היטק": "הייטק", "מפני": "מפני", "תל": "תל", "קיץ": "קיץ", "ממני": "ממני", "ממך": "ממך", "ממנו": "ממנו", "ממנה": "ממנה", "רשיון": "רישיון",
 # future of היה keeps one yod
 "יהיה": "יהיה", "תהיה": "תהיה", "נהיה": "נהיה", "אהיה": "אהיה", "יהיו": "יהיו", "תהיו": "תהיו", "תהיי": "תהיי",
}
KNOWN = set()   # filled by load_known() or the caller: words of the course, to tell the prefix מִ (מִכָּל) from a root letter (מִטָּה)
def split(word):
    # -> list of [letter, marks]
    out = []
    for c in word:
        if "א" <= c <= "ת": out.append([c, ""])
        elif MARK.match(c) and out: out[-1][1] += c
    return out

def ktiv(word, prefix_len=0):
    lead = re.match(r"^[^א-ת]*", word).group(0); tail = re.search(r"[^א-ת֑-ׇ]*$", word).group(0)
    core = word[len(lead):len(word) - len(tail)] if tail else word[len(lead):]
    L = split(core)
    if not L: return word
    plain = "".join(l for l, _ in L)
    for k in range(0, 4):   # אֳנִיָּה (ship) is not the name אַנְיָה
        if plain[k:] == "אניה" and "\u05B3" in L[k][1] and all(c in "והבלמשכ" for c in plain[:k]):
            return lead + plain[:k] + "אונייה" + tail
    for k in range(0, 4):   # exceptions, also after prefixes ו ה ב ל מ ש כ
        if plain[k:] in EXC and all(c in "והבלמשכ" for c in plain[:k]):
            return lead + plain[:k] + EXC[plain[k:]] + tail
    out = []
    n = len(L)
    # prefix letters: initial ו ה ב ל מ ש כ carrying a vowel and followed by more letters
    pre = 0
    while pre < n - 2 and L[pre][0] in "והבלמשכ" and pre < 3:
        m = L[pre][1]
        if pre == 0 and L[0][0] in "בכלמ" and (SHVA in m or PATAH in m or QAMATS in m or SEGOL in m): pre += 1; continue
        if pre == 0 and L[0][0] == "מ" and HIRIK in m and DAGESH in L[1][1] and plain[1:] in KNOWN: pre += 1; continue
        if L[pre][0] == "ו" and (SHVA in m or DAGESH in m and not any(v in m for v in FULLV)): pre += 1; continue
        if L[pre][0] in "הש" and (PATAH in m or QAMATS in m or SEGOL in m) and DAGESH in L[pre + 1][1]: pre += 1; continue
        break
    for i, (c, m) in enumerate(L):
        nxt = L[i + 1] if i + 1 < n else None
        prv = L[i - 1] if i > 0 else None
        mid = 0 < i < n - 1
        # consonantal vav / yod
        if c == "ו":
            is_vowel = (HOLAM in m and not any(v in m for v in FULLV.replace(HOLAM, ""))) or (DAGESH in m and not any(v in m for v in FULLV))
            if not is_vowel and mid and i > pre and (prv[0] != "ו") and (nxt[0] != "ו"):
                out.append("וו"); continue
            out.append("ו"); continue
        if c == "י":
            is_mater = prv is not None and HIRIK in prv[1] and not m.strip(DAGESH)
            after_mater = prv is not None and (KUBBUTZ in prv[1] or HOLAM in prv[1])   # מְצֻיֶּנֶת -> מצוינת
            after_shva = prv is not None and not any(v in prv[1] for v in FULLV) and nxt is L[-1] and nxt[0] == "ה"   # ending ־יָה after shva: אַמְבַּטְיָה, אַלֶּרְגְּיָה -> one yod (but בִּנְיָן -> בניין)
            vowel = any(v in m for v in FULLV)
            if not is_mater and not after_mater and not after_shva and mid and i > pre and (vowel or DAGESH in m) and prv[0] not in "ויא" and nxt[0] not in "ויא":
                out.append("יי"); continue
            out.append("י")
        else:
            out.append(c)
        # vowels written as letters after this consonant
        if HOLAM in m and not (nxt and nxt[0] == "ו") and not (nxt and nxt is not L[-1] and nxt[0] == "א" and not any(v in nxt[1] for v in FULLV)): out.append("ו")   # נֹאכַל -> נאכל
        elif KUBBUTZ in m or "\u05B3" in m: out.append("ו")   # kubbutz and hataf-qamats: חֳדָשִׁים -> חודשים
        elif HIRIK in m and c != "י" and i >= pre:
            if nxt is None: pass
            elif nxt[0] == "י": pass                              # hirik male already
            elif SHVA in nxt[1] and DAGESH not in nxt[1]: pass     # closed syllable (shva nach)
            elif nxt is L[-1] and not any(v in nxt[1] for v in FULLV): pass   # word-final closed syllable: אִם
            elif nxt[0] == "א" and not any(v in nxt[1] for v in FULLV + SHVA): pass   # silent aleph: רִאשׁוֹן
            elif c == "ה" and DAGESH in nxt[1] and i <= 2 and all(L[j][0] in "וש" for j in range(i)): pass   # hif'il with assimilated נ: הִגִּיעַ, הִכִּיר
            else: out.append("י")
    return lead + "".join(out) + tail

def line(s):
    return " ".join(ktiv(w) for w in s.split(" "))

def load_known(root):
    import json, glob
    NIK = re.compile("[\u0591-\u05C7]"); bare = lambda x: re.sub("[^\u05D0-\u05EA]", "", NIK.sub("", x or ""))
    for f in glob.glob(root + "/content/m*.json"):
        if "practice" in f: continue
        for w in json.load(open(f, encoding="utf-8"))["words"]:
            KNOWN.add(bare(w["he"])); KNOWN.add(bare(w.get("pl")))
            for x in (w.get("forms") or "").split("·"): KNOWN.add(bare(x))
    for t in json.load(open(root + "/content/vocab.json", encoding="utf-8"))["topics"]:
        for w in t["words"]: KNOWN.add(bare(w["he"]))
    for w in json.load(open(root + "/content/lexicon.json", encoding="utf-8"))["words"]: KNOWN.add(bare(w[0]))
    KNOWN.discard("")
