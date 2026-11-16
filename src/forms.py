# Verb forms recognised by their pointing: (lesson that teaches it, name). Shared by audit_level.py and build_vocab.py.
# Tokens are matched with dagesh, meteg and shin/sin dots removed (so the order of marks does not matter);
# shuruk is then a plain ו.
import re
SH, HI, TS, SE, PA, QA, HO = "ְ", "ִ", "ֵ", "ֶ", "ַ", "ָ", "ֹ"
L = "[א-ת]"
V = "(?:ו[ְ-ֻ]*|ש[ְ-ֻ]*|כ[ְ-ֻ]*ש[ְ-ֻ]*)?"   # ו / שֶׁ / כְּשֶׁ before the verb
END12 = "(?:ת" + HI + "י|ת" + QA + "|ת" + SH + "|נו|ת" + SE + "[םן])$"     # past 1st/2nd person endings
PATS = [
 ("m12l3", "прошедшее hитпаэль", re.compile("^" + V + "ה" + HI + "ת" + SH)),
 ("m12l2", "прошедшее hифъиль", re.compile("^" + V + "ה(?:" + HI + L + SH + "|" + TS + L + "|ו" + HO + "?" + L + "|" + HO + L + ")[ְ-ֻ]*" + L + ".*" + END12)),
 ("m12l2", "прошедшее hифъиль", re.compile("^" + V + "ה" + HI + L + SH + L + HI + "י" + L + "(?:" + QA + "ה|ו)?$")),
 ("m12l4", "прошедшее нифъаль", re.compile("^" + V + "נ" + HI + L + SH + L + "[" + PA + QA + "]" + L + ".*" + END12)),
 ("m12l4", "прошедшее нифъаль", re.compile("^" + V + "נ" + HI + L + SH + L + PA + L + "$")),
 ("m12l1", "прошедшее пиэль", re.compile("^" + V + L + HI + L + "[" + PA + TS + "]" + L + SH + END12)),
 ("m11l2", "прошедшее ל״ה", re.compile("^" + V + ".*" + HI + "י(?:ת" + HI + "י|ת" + QA + "|ת" + SH + "|נו)$")),
 ("m11l1", "прошедшее", re.compile("^" + V + ".*" + L + SH + END12)),
 ("m11l1", "прошедшее", re.compile("^" + V + L + QA + L + "[" + SH + "ֲ]" + L + "(?:" + QA + "ה|ו)$")),
 ("m12l1", "прошедшее пиэль", re.compile("^" + V + L + HI + L + SH + L + "(?:" + QA + "ה|ו)$")),
 ("m11l1", "прошедшее", re.compile("^" + V + L + QA + L + PA + L + SH + "?$")),
 ("m14l2", "будущее ל״ה", re.compile("^" + V + "[אתינ][" + HI + SE + "]" + L + SH + L + SE + "ה$")),
 ("m14l1", "будущее", re.compile("^" + V + "[אתינ][" + HI + SE + "]" + L + SH + L + PA + L + "(?:" + HI + "י|ו)?$")),
 ("m14l1", "будущее", re.compile("^" + V + "[אתינ][" + HI + SE + "]" + L + SH + L + HO + L + "(?:" + HI + "י|ו)?$")),
 ("m16l1", "будущее пиэль", re.compile("^" + V + "[אתינ][ְֲ]" + L + PA + L + "[" + TS + SH + "]" + L + "(?:" + HI + "י|ו)?$")),
 ("m16l3", "будущее hифъиль", re.compile("^" + V + "[אתינ]" + PA + L + SH + L + HI + "י" + L + "(?:" + HI + "י|ו)?$")),
 ("m17l1", "будущее hитпаэль", re.compile("^" + V + "[אתינ][" + HI + SE + "]ת" + SH)),
]
NOT_VERBS = re.compile("^(?:[והבלמשכ]{0,2})(?:אנחנו|עלי|אף|מתי|אתמול|תלמיד|תלמידה|תלמידים|תלמידות|תרגיל|תרגילים)$")
IRREG_FUT = set("אלך תלך ילך נלך תלכי ילכו תלכו אבוא תבוא יבוא נבוא תבואי יבואו אשב תשב נשב אצא תצא יצא נצא תצאי אתן תתן ניתן תתני אקח תקח נקח תקחי תאכל נאכל".split())
HAYA_FUT = set("אהיה תהיה יהיה נהיה יהיו תהיי תהיו".split())   # «буду» is taught with ע״ו and ל״ה (m14l2)
def form_of(tok):
    b = re.sub("[^\u05D0-\u05EA]", "", tok)
    for k in range(0, 3):
        if b[k:] in HAYA_FUT and all(c in "וש" for c in b[:k]): return "m14l2", "будущее ל״ה"
    if re.match("^[וש]?התחל", b): return "m12l2", "прошедшее hифъиль"   # הִתְחִיל: hifil, looks like hitpael
    for k in range(0, 2):
        if b[k:] in IRREG_FUT and all(c in "וש" for c in b[:k]): return "m14l3", "будущее (неправильные)"
    if NOT_VERBS.match(re.sub("[^א-ת]", "", tok)): return None
    t =re.sub("[ּֽׁׂ]", "", tok)
    for lesson, name, rx in PATS:
        if rx.match(t):
            if name == "прошедшее пиэль" and t.endswith(("ה", "ו")) and SH in t and not re.match("^" + V + "[\u05D0-\u05EA][^\u05D0-\u05EA]*[\u05D0-\u05EA][\u05B0-\u05C2]*\u05BC", re.sub("[\u05C1\u05C2]", "", tok)): continue
            return lesson, name
    return None
