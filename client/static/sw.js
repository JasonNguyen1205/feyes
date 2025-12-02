// Service Worker for Visual AOI Client
// Chromium-optimized offline support and caching

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `visual-aoi-${CACHE_VERSION}`;

// Assets to cache on installation
const STATIC_ASSETS = [
    '/',
    '/static/professional.css',
    '/static/chromium-optimizations.css',
    '/static/script.js'
];

// API endpoints to cache with network-first strategy
const API_ENDPOINTS = [
    '/api/cameras',
    '/api/products',
    '/api/camera/status'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[Service Worker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[Service Worker] Installed successfully');
                return self.skipWaiting(); // Activate immediately
            })
            .catch(error => {
                console.error('[Service Worker] Installation failed:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');

    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(name => name.startsWith('visual-aoi-') && name !== CACHE_NAME)
                        .map(name => {
                            console.log(`[Service Worker] Deleting old cache: ${name}`);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[Service Worker] Activated successfully');
                return self.clients.claim(); // Take control immediately
            })
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }

    // API requests - Network first, fallback to cache
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Static assets - Cache first, fallback to network
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(cacheFirstStrategy(request));
        return;
    }

    // HTML pages - Network first with cache fallback
    if (request.headers.get('accept').includes('text/html')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Images - Cache first with network fallback
    if (request.headers.get('accept').includes('image/')) {
        event.respondWith(cacheFirstStrategy(request));
        return;
    }

    // Default - Network first
    event.respondWith(networkFirstStrategy(request));
});

// Network-first strategy (fresh data preferred)
async function networkFirstStrategy(request) {
    const cache = await caches.open(CACHE_NAME);

    try {
        // Try network first
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        // Network failed, try cache
        console.log(`[Service Worker] Network failed for ${request.url}, using cache`);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // No cache either, return offline page or error
        return new Response('Offline - No cached version available', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

// Cache-first strategy (speed preferred)
async function cacheFirstStrategy(request) {
    const cache = await caches.open(CACHE_NAME);

    // Check cache first
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    // Cache miss, fetch from network
    try {
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error(`[Service Worker] Failed to fetch ${request.url}:`, error);

        return new Response('Resource not available', {
            status: 404,
            statusText: 'Not Found',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

// Message handler for cache management
self.addEventListener('message', (event) => {
    if (event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }

    if (event.data.action === 'clearCache') {
        event.waitUntil(
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(name => caches.delete(name))
                );
            }).then(() => {
                console.log('[Service Worker] All caches cleared');
                event.ports[0].postMessage({ success: true });
            })
        );
    }

    if (event.data.action === 'getCacheSize') {
        event.waitUntil(
            caches.open(CACHE_NAME).then(cache => {
                return cache.keys().then(keys => {
                    event.ports[0].postMessage({
                        cacheSize: keys.length,
                        cacheName: CACHE_NAME
                    });
                });
            })
        );
    }
});

// Background sync for offline actions (if supported)
if ('sync' in self.registration) {
    self.addEventListener('sync', (event) => {
        console.log('[Service Worker] Background sync:', event.tag);

        if (event.tag === 'sync-inspection-results') {
            event.waitUntil(syncInspectionResults());
        }
    });
}

async function syncInspectionResults() {
    console.log('[Service Worker] Syncing inspection results...');
    // Implement sync logic here when needed
    return Promise.resolve();
}

// Push notification support (if needed in future)
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push received:', event);

    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Visual AOI Notification';
    const options = {
        body: data.body || 'New inspection result available',
        icon: '/static/icon-192.png',
        badge: '/static/badge-72.png',
        vibrate: [200, 100, 200],
        data: data
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] Notification clicked:', event);

    event.notification.close();

    event.waitUntil(
        clients.openWindow('/')
    );
});

console.log('[Service Worker] Loaded successfully');
