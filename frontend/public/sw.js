/**
 * Service Worker for AgriBharat (SEVA)
 * Handles background push notifications when browser tabs are closed.
 */

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: 'AgriBharat Alert', body: event.data.text() };
    }
  }

  const title = data.title || 'AgriBharat: Irrigation Alert';
  const options = {
    body: data.message || data.body || 'New agricultural advisory received.',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: data.dedupKey || 'irrigation-alert',
    renotify: true,
    data: {
      url: data.url || '/',
      id: data.id,
      eventType: data.eventType
    }
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    })
  );
});
