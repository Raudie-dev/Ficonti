const CACHE_NAME = 'tributove-v2';
const OFFLINE_URL = '/offline/';

const PRECACHE_ASSETS = [
  '/',
  '/offline/',
  '/static/css/tributove.css',
  '/static/js/tributove.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon.svg',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
];

// Instalación: Precarga de recursos clave
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[PWA-SW] Precaching parcial:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activación: Limpieza de cachés viejos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Estrategia híbrida Network-First con fallback offline para navegación
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Excluir métodos que no sean GET
  if (req.method !== 'GET') {
    return;
  }

  // Si es navegación HTML
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((response) => {
          // Guardar copia fresca en caché
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
          }
          return response;
        })
        .catch(() => {
          return caches.match(req).then((cached) => {
            return cached || caches.match(OFFLINE_URL);
          });
        })
    );
    return;
  }

  // Para estáticos (CSS, JS, Fonts, Icons): Stale-While-Revalidate
  if (
    url.origin === self.location.origin &&
    (url.pathname.startsWith('/static/') || url.pathname.includes('/icons/'))
  ) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const fetchPromise = fetch(req).then((networkRes) => {
          if (networkRes && networkRes.status === 200) {
            const clone = networkRes.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
          }
          return networkRes;
        }).catch(() => null);

        return cached || fetchPromise;
      })
    );
    return;
  }

  // Fallback por defecto: Network first con Cache
  event.respondWith(
    fetch(req).catch(() => caches.match(req))
  );
});