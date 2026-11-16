# Adds hand-checked full spelling ("plain") to texts shown without nikud (level Bet).
#   python3 -I add_plain.py <ivrit_dir>     (run AFTER build_mN.py / build_texts1.py)
import json, glob, sys
sys.path.insert(0, sys.argv[1] + "/build"); import ktiv
ktiv.load_known(sys.argv[1])
n = 0
for f in sorted(glob.glob(sys.argv[1] + "/content/m*-practice.json")):
    d = json.load(open(f, encoding="utf-8")); ch = False
    for t in d.get("texts", []):
        if t.get("nikud") == "off":
            t["plain"] = [ktiv.line(s) for s in t["he"]]; ch = True; n += 1
    if ch: json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("plain added to", n, "texts")
