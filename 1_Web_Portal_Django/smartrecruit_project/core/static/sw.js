// SmartRecruit Service Worker — Self-Unregister Edition
// This version clears all caches and immediately unregisters to prevent
// the offline page from appearing to authenticated users in live sessions.
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((names) =>
            Promise.all(names.map((name) => caches.delete(name)))
        ).then(() => self.registration.unregister())
    );
});
