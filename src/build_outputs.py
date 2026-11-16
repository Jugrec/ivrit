# Builds content/outputs.json (own sentences at the end of each lesson) from build/outputs_src.txt:
#   python3 -I build/build_outputs.py <ivrit_dir>
# Checks: every module lesson has a task, samples use no verb form taught later (build/forms.py), no em dash.
import json, re, sys, glob
ROOT = sys.argv[1]
sys.path.insert(0, ROOT + "/build"); import forms
ORDER = lambda l: tuple(int(x) for x in re.match(r"m(\d+)l(\d+)", l).groups())
out, cur, bad = {}, None, False
for ln in open(ROOT + "/build/outputs_src.txt", encoding="utf-8"):
    ln = ln.rstrip("\n")
    if not ln.strip() or ln.startswith("#"): continue
    if "—" in ln: print("em dash:", ln); bad = True
    if ln.startswith("= "):
        he, ru = [x.strip() for x in ln[2:].split(" | ")]
        out[cur]["he"].append(he); out[cur]["ru"].append(ru)
        for tok in he.split():
            f = forms.form_of(re.sub(r"[^ְ-ת]", "", tok))
            if f and ORDER(f[0]) > ORDER(cur): print(cur, "рано:", tok, f); bad = True
    else:
        lid, task, use = [x.strip() for x in ln.split(" | ")]
        cur = lid; out[lid] = {"task": task, "use": use, "he": [], "ru": []}
lessons = []
for f in sorted(glob.glob(ROOT + "/content/m*.json")):
    if "practice" in f: continue
    lessons += [l["id"] for l in json.load(open(f, encoding="utf-8")).get("lessons", [])]
miss = [l for l in lessons if l not in out]; extra = [l for l in out if l not in lessons]
if miss or extra: print("нет задания:", miss, "лишние:", extra); bad = True
for k, v in out.items():
    if len(v["he"]) < 2 and not any(" " in h and h.count(".") > 1 for h in v["he"]): print(k, "мало образцов"); bad = True
# topics of the words of the day that fit each lesson's task (module default, lesson override); words are suggested
# only from these topics, so a lesson about countries does not suggest «pepper, banana».
MOD_TOPICS = {4: ["home", "city"], 5: ["describe", "clothes"], 6: ["verbs"], 7: ["verbs", "leisure"], 8: ["people", "home"], 9: ["people", "work"],
  10: ["food", "shopping"], 11: ["verbs", "leisure"], 12: ["verbs", "leisure"], 13: ["home", "food"], 14: ["verbs", "leisure"], 15: ["people", "verbs"],
  16: ["work", "verbs"], 17: ["verbs", "leisure"], 18: ["verbs", "home"], 19: ["leisure", "study"], 20: ["home", "work"], 21: ["work", "home"],
  22: ["feelings", "work"], 23: ["work", "study"], 24: ["soc", "work"], 25: ["soc", "work"], 26: ["people", "leisure"], 27: ["shopping", "work"]}
LES_TOPICS = {"m4l1": ["home", "kitchen"], "m4l2": ["city", "transport"], "m4l3": ["city", "transport"], "m4l4": ["home", "anim", "tech"], "m4l5": ["people", "verbs"],
  "m5l1": ["describe", "home"], "m5l2": ["clothes"], "m5l3": ["home", "describe"], "m5l4": ["people"], "m5l5": ["describe", "city"],
  "m7l3": ["study", "work"], "m8l3": ["time", "work"], "m8l4": ["people", "describe"], "m10l1": ["home", "people"], "m10l2": ["people", "study"],
  "m10l4": ["time", "work"], "m10l5": ["people", "time"], "m11l2": ["food", "shopping"], "m13l2": ["home", "food"], "m13l3": ["clothes", "study"], "m13l4": ["time", "leisure"],
  "m15l1": ["people"], "m15l2": ["food", "shopping"], "m15l3": ["work", "time"], "m15l5": ["leisure"], "m22l2": ["study", "feelings"],
  "m23l2": ["body", "transport"], "m23l3": ["city", "home", "soc"], "m23l4": ["transport", "time"], "m23l5": ["home"], "m24l3": ["people", "work"], "m25l1": ["transport", "time"], "m25l4": ["body"]}
for k, v in out.items(): v["topics"] = LES_TOPICS.get(k) or MOD_TOPICS[int(re.match(r"m(\d+)", k).group(1))]
if bad: sys.exit(1)
json.dump(out, open(ROOT + "/content/outputs.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("outputs ok:", len(out), "уроков")
