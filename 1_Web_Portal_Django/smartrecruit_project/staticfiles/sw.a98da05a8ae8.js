const CACHE_NAME = 'smartrecruit-cache-v15';
const OFFLINE_URL = '/offline/';

// Assets to pre-cache
const PRECACHE_ASSETS = [
    '/',
    OFFLINE_URL,
    '/static/css/base.css',
    '/static/css/professional_ui.css',
    '/static/images/nebula_bg.png'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => 
            Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME) return caches.delete(name);
                })
            )
        )
    );
    self.clients.claim();
});

// Stale-While-Revalidate strategy
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    
    // For HTML navigation requests, try network first, then cache, then offline page
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                return caches.match(event.request).then((response) => {
                    return response || caches.match(OFFLINE_URL);
                });
            })
        );
        return;
    }

    // Stale-while-revalidate for static assets
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request).then((networkResponse) => {
                if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
                    const responseToCache = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
                }
                return networkResponse;
            }).catch(() => null);

            return cachedResponse || fetchPromise;
        })
    );
});

// Push notification listener
self.addEventListener('push', (event) => {
    let data = { title: 'SmartRecruit', body: 'New update from the system!' };

    if (event.data) {
        data = event.data.json();
    }

    const options = {
        body: data.body,
        icon: '/static/images/pwa-icon-192.png',
        badge: '/static/images/pwa-icon-192.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: '2'
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/')
    );
});
