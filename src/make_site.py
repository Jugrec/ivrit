# Builds the standalone website (PWA) from the same index.html used in Claude.
#   python3 -I make_site.py <ivrit_dir> <out_dir>
# Output: index.html (full document), content/*.json, manifest.json, sw.js, icons/*.png
import json, os, shutil, sys, hashlib
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT + "/content"); os.makedirs(OUT + "/icons")

body = open(SRC + "/index.html", encoding="utf-8").read()
head_end = body.index("<style>")
head_part, rest = body[:head_end], body[head_end:]
head_part = head_part.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
doc = ('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       '<meta name="theme-color" content="#2B5C8A">\n<meta name="description" content="Систематический курс современного иврита: уроки, повторение, чтение, прописные буквы.">\n'
       '<link rel="manifest" href="manifest.json">\n<link rel="icon" href="icons/icon-192.png">\n<link rel="apple-touch-icon" href="icons/icon-192.png">\n'
       + head_part + rest.replace("</style>", "</style>\n</head>\n<body>", 1) + "\n</body>\n</html>\n")
open(OUT + "/index.html", "w", encoding="utf-8").write(doc)

files = sorted(os.listdir(SRC + "/content"))
for f in files: shutil.copy(SRC + "/content/" + f, OUT + "/content/" + f)

# icons: white aleph on the app's blue
font = None
for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
    if os.path.exists(path): font = path; break
for size in (192, 512):
    im = Image.new("RGB", (size, size), (43, 92, 138))
    d = ImageDraw.Draw(im)
    ft = ImageFont.truetype(font, int(size * 0.62))
    d.text((size / 2, size / 2), "א", font=ft, fill=(255, 255, 255), anchor="mm")
    im.save(OUT + "/icons/icon-%d.png" % size)

manifest = {
 "name": "Иврит шаг за шагом", "short_name": "Иврит", "lang": "ru", "dir": "ltr",
 "start_url": "./", "scope": "./", "display": "standalone",
 "background_color": "#F3F5F7", "theme_color": "#2B5C8A",
 "icons": [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
           {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]
}
json.dump(manifest, open(OUT + "/manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# service worker: cache everything for offline use; refresh in the background, new version on next launch
h = hashlib.sha1()
for root, _, fs in os.walk(OUT):
    for f in sorted(fs): h.update(open(os.path.join(root, f), "rb").read())
version = h.hexdigest()[:10]
assets = ["./", "index.html", "manifest.json", "icons/icon-192.png", "icons/icon-512.png"] + ["content/" + f for f in files]
sw = """const CACHE = "ivrit-%s";
const ASSETS = %s;
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
// network first: online the newest version opens at once; offline the cached copy is used
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET" || !e.request.url.startsWith(self.location.origin)) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    try {
      const r = await fetch(e.request, { cache: "no-cache" });
      if (r && r.ok) c.put(e.request, r.clone());
      return r;
    } catch (_) {
      return (await c.match(e.request, { ignoreSearch: true })) || (e.request.mode === "navigate" ? c.match("./") : Response.error());
    }
  }));
});
""" % (version, json.dumps(assets, ensure_ascii=False))
open(OUT + "/sw.js", "w", encoding="utf-8").write(sw)
print("site ok:", len(files), "content files, version", version)
