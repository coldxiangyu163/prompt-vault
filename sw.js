// PromptVault Service Worker
// Cache-first for static assets, Network-first for data

const CACHE_VERSION = 'pv-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DATA_CACHE = `${CACHE_VERSION}-data`;

const BASE_PATH = '/prompt-vault/';

// Static assets to pre-cache on install
const STATIC_ASSETS = [
  `${BASE_PATH}`,
  `${BASE_PATH}index.html`,
  `${BASE_PATH}app.js`,
  `${BASE_PATH}style.css`,
  `${BASE_PATH}favicon.png`,
  `${BASE_PATH}manifest.json`
];

// Data URLs (network-first)
const DATA_URLS = [
  `${BASE_PATH}data/prompts.json`
];

// Install: pre-cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== DATA_CACHE)
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// Fetch: route requests to appropriate strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin requests
  if (url.origin !== location.origin) return;

  // Data files: network-first (ensure fresh data)
  if (DATA_URLS.some((dataUrl) => url.pathname.endsWith('prompts.json'))) {
    event.respondWith(networkFirst(request, DATA_CACHE));
    return;
  }

  // Static assets: cache-first
  if (url.pathname.startsWith(BASE_PATH)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }
});

// Cache-first strategy: try cache, fallback to network
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // Offline fallback: return cached index.html for navigation requests
    if (request.mode === 'navigate') {
      const fallback = await caches.match(`${BASE_PATH}index.html`);
      if (fallback) return fallback;
    }
    return new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

// Network-first strategy: try network, fallback to cache
async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;

    return new Response(JSON.stringify({ error: 'offline', prompts: [] }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
