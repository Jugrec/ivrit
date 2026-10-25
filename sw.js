const CACHE = "ivrit-71cd71afa0";
const ASSETS = ["./", "index.html", "manifest.json", "icons/icon-192.png", "icons/icon-512.png", "content/aleph.json", "content/drill1.json", "content/lexicon.json", "content/m10-practice.json", "content/m10.json", "content/m11-practice.json", "content/m11.json", "content/m12-practice.json", "content/m12.json", "content/m13-practice.json", "content/m13.json", "content/m14-practice.json", "content/m14.json", "content/m15-practice.json", "content/m15.json", "content/m16-practice.json", "content/m16.json", "content/m17-practice.json", "content/m17.json", "content/m18-practice.json", "content/m18.json", "content/m19-practice.json", "content/m19.json", "content/m20-practice.json", "content/m20.json", "content/m21-practice.json", "content/m21.json", "content/m22-practice.json", "content/m22.json", "content/m23-practice.json", "content/m23.json", "content/m4-practice.json", "content/m4.json", "content/m5-practice.json", "content/m5.json", "content/m6-practice.json", "content/m6.json", "content/m7-practice.json", "content/m7.json", "content/m8-practice.json", "content/m8.json", "content/m9-practice.json", "content/m9.json", "content/roots1.json"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(e.request, { ignoreSearch: true });
    const net = fetch(e.request).then(r => { if (r && (r.ok || r.type === "opaque")) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
