// Cambia questo numero a ogni rilascio per forzare l'aggiornamento della cache
const CACHE_VERSION = 'v2-2026-11-13';
const CACHE_NAME = 'atmbet-cache-' + CACHE_VERSION;
const ASSETS = ['/logo.png'];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).catch(() => {}));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Pagine, dati e traduzioni: sempre dalla rete; la cache serve solo se sei offline
  const isDynamic = req.mode === 'navigate' || /\.(html|json)$/.test(url.pathname) || url.pathname === '/';
  if (isDynamic) {
    event.respondWith(
      fetch(req, { cache: 'no-store' }).catch(() => caches.match(req))
    );
    return;
  }

  // Immagini e altri file statici: cache veloce con aggiornamento in background
  event.respondWith(
    caches.match(req).then(cached => {
      const net = fetch(req).then(res => {
        if (res && res.ok) { const copy = res.clone(); caches.open(CACHE_NAME).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => cached);
      return cached || net;
    })
  );
});
