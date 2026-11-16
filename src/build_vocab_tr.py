import unicodedata
def fix_tr(t):
    # Latin vowels with acute -> Cyrillic + combining acute (same as build_vocab.py)
    m = {"á": "а́", "é": "е́", "ó": "о́", "í": "и́", "ú": "у́", "a": "а", "e": "е", "o": "о", "c": "с", "p": "р", "x": "х", "y": "у"}
    return "".join(m.get(ch, ch) for ch in unicodedata.normalize("NFC", t))
