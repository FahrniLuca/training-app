// Service Worker: hält die App offline verfügbar.
// Online: immer zuerst die neueste Version vom Server laden (max. 3 s warten), sonst aus dem Cache.
// Die Trainingsdaten liegen im localStorage und werden online mit GitHub synchronisiert.
const CACHE = 'trainingsbuch-v5';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './apple-touch-icon.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return; // GitHub-API nie cachen
  const key = req.mode === 'navigate' ? './index.html' : req;
  e.respondWith(caches.open(CACHE).then(async cache => {
    const cached = await cache.match(key, { ignoreSearch: true });
    const network = fetch(req, { cache: 'no-cache' }).then(res => { if (res && res.ok) cache.put(key, res.clone()); return res; });
    if (!cached) return network;
    // Netzwerk zuerst, aber nach 3 s (schlechtes Netz) den Cache nehmen
    const timeout = new Promise(r => setTimeout(() => r(cached), 3000));
    return Promise.race([network.catch(() => cached), timeout]);
  }));
});
