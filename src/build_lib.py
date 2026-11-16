"""Compact builders for course units. Exercise tuples:
  ("t", k, prompt, [accept], note)              typed translation
  ("c", k, prompt, [options; first correct], note)
  ("g", k, prompt, he_with___, [accept], note)  gap
  ("x", k, prompt, he, [accept], note)          transform
  ("o", k, prompt, [tokens], note, [alt...])    order
"""
import json

def ex(prefix, i, e):
    kind, k = e[0], e[1]
    eid = "%s%02d" % (prefix, i + 1)
    if kind == "t":
        return {"id": eid, "k": k, "type": "type", "prompt": e[2], "accept": e[3], "note": e[4]}
    if kind == "h":
        return {"id": eid, "k": k, "type": "type", "hard": True, "prompt": "Переведите: " + e[2], "accept": e[3], "note": e[4]}
    if kind == "c":
        return {"id": eid, "k": k, "type": "choice", "prompt": e[2], "options": e[3], "answer": 0, "note": e[4]}
    if kind == "g":
        assert "___" in e[3], eid
        return {"id": eid, "k": k, "type": "gap", "prompt": e[2], "he": e[3], "accept": e[4], "note": e[5]}
    if kind == "x":
        return {"id": eid, "k": k, "type": "transform", "prompt": e[2], "he": e[3], "accept": e[4], "note": e[5]}
    if kind == "o":
        d = {"id": eid, "k": k, "type": "order", "prompt": e[2], "tokens": e[3], "note": e[4]}
        if len(e) > 5 and e[5]:
            d["alt"] = e[5]
        return d
    raise ValueError(kind)

def words(lst):
    out = []
    for w in lst:
        wid, he, tr, ru = w[:4]
        d = {"id": wid, "he": he, "tr": tr, "ru": ru}
        if len(w) > 4 and w[4]:
            d["g"] = w[4]
        if len(w) > 5 and w[5]:
            d.update(w[5])
        out.append(d)
    return out

def lesson(lid, title, theory, word_ids, exercises, hard):
    return {"id": lid, "title": title, "theory": theory, "words": word_ids,
            "exercises": [ex(lid + "e", i, e) for i, e in enumerate(exercises)],
            "hard": [ex(lid + "h", i, ("h",) + tuple(e)) for i, e in enumerate(hard)]}

def p(text): return {"t": "p", "text": text}
def rule(text): return {"t": "rule", "text": text}
def table(head, rows): return {"t": "table", "head": head, "rows": rows}

def check_unit(u):
    wids = {w["id"] for w in u["words"]}
    ids = set()
    allex = []
    for l in u["lessons"]:
        for w in l["words"]:
            assert w in wids, (l["id"], w)
        allex += l["exercises"] + l.get("hard", [])
    if u.get("test"):
        allex += u["test"]["items"]
    for e in allex:
        assert e["id"] not in ids, e["id"]; ids.add(e["id"])
        assert e["k"] in u["skills"], (e["id"], e["k"])
        assert "—" not in json.dumps(e, ensure_ascii=False), e["id"]
    used = {w for l in u["lessons"] for w in l["words"]}
    assert not (wids - used), wids - used
    return len(allex)
