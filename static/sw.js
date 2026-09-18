const CACHE_NAME = 'sindatos-shell-v6';
const SHELL_ASSETS = [
  '/',
  '/manifest.json',
  '/static/css/fonts.css',
  '/static/vendor/tailwind.js',
  '/static/vendor/qrcode.min.js',
  '/static/vendor/html5-qrcode.min.js',
  '/static/vendor/lz-string.min.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/favicon.png',
  '/static/icons/logo.png',
  '/static/icons/icon.svg'
];

// Instalación: Pre-cachear todo el App Shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-cacheados recursos del App Shell v5');
      return cache.addAll(SHELL_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activación: Reclamar clientes y limpiar cachés anteriores
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Eliminando caché obsoleta:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Estrategia: Network-First para páginas HTML (App Shell dinámico), Cache-First para estáticos
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 1. Rutas dinámicas de señalización /api/ NUNCA deben cachearse
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // 2. Navegación HTML (páginas): Network-First con fallback a Caché offline
  if (event.request.mode === 'navigate' || url.pathname === '/') {
    event.respondWith(
      fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
        }
        return networkResponse;
      }).catch(() => {
        return caches.match('/') || caches.match(event.request);
      })
    );
    return;
  }

  // 3. Recursos estáticos (JS, CSS, Fuentes, Iconos): Cache-First con fallback a Red
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
        }
        return networkResponse;
      });
    })
  );
});
