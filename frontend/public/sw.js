const CACHE_NAME = 'eventos-visualizer-v6-2025-11-29';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/offline.html'
];

// Install event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache opened');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event
self.addEventListener('fetch', event => {
  // NEVER cache API calls - always fetch fresh data
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          // Only on network failure, return offline response
          return new Response(JSON.stringify({
            status: 'offline',
            message: 'No hay conexión a internet'
          }), {
            headers: { 'Content-Type': 'application/json' }
          });
        })
    );
    return;
  }

  // For non-API requests: Network First, Cache Fallback
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Clone the response
        const responseToCache = response.clone();

        caches.open(CACHE_NAME)
          .then(cache => {
            // Cache successful responses, but skip chrome-extension and other unsupported schemes
            if (event.request.method === 'GET' &&
                event.request.url.startsWith('http') &&
                !event.request.url.startsWith('chrome-extension://')) {
              cache.put(event.request, responseToCache);
            }
          });

        return response;
      })
      .catch(() => {
        // Return cached version or offline page
        return caches.match(event.request)
          .then(response => {
            if (response) {
              return response;
            }

            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match('/offline.html').then(offlinePage => {
                return offlinePage || new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
              });
            }

            // For other requests (images, etc.) return a proper Response
            return new Response('', { status: 404, statusText: 'Not Found' });
          });
      })
  );
});

// Push notification event
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'Nuevo evento disponible',
    icon: '/icon-192x192.png',
    badge: '/icon-192x192.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    }
  };

  event.waitUntil(
    self.registration.showNotification('Eventos Visualizer', options)
  );
});

// Notification click event  
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});