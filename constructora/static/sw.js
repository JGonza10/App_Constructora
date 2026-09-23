// Service worker minimo: solo existe para que el navegador considere la app
// "instalable" (icono en la pantalla de inicio del celular, modo standalone).
// A proposito NO cachea nada: casi toda la app son formularios protegidos
// por CSRF y con sesion — servir una pagina vieja del cache rompe el
// siguiente POST con un token caducado. Siempre va a la red.
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  event.respondWith(fetch(event.request));
});
