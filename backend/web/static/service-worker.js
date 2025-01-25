// console.log(window.domain)

const CACHE_NAME = "techa-cache-v1";
const urlsToCache = [
  "/",
  "/static/css/backend-plugin.min.css",
  "/static/css/backend.css",
  "/static/vendor/-fortawesome/fontawesome-free/css/all.min.css",
  "/static/vendor/line-awesome/dist/line-awesome/css/line-awesome.min.css",
  "/static/vendor/remixicon/fonts/remixicon.css",
  "/static/css/dropdownCheckboxes.css",
  "/static/images/logo/logo.png",
  "/static/js/backend-bundle.min.js",
  "/static/js/table-treeview.js",
  "/static/js/customizer.js",
  "/static/js/chart-custom.js",
  "/static/js/app.js",
  "/static/js/dropdownCheckboxes.min.js"
];
// Install the service worker
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
});
// Fetch assets from the cache
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});



// const CACHE_NAME = 'v1';
// const CACHE_ASSETS = [
//     '/',
//     '/static/css/styles.css',
//     '/static/js/vendor/jquery-3.5.1.min.js',
//     '/static/js/vendor/bootstrap.bundle.min.js',
//     '/static/js/vendor/OverlayScrollbars.min.js',
//     '/static/js/common.js',
//     '/static/img/favicon/favicon-192x192.png',
//     '/static/img/favicon/favicon-512x512.png'
// ];

// // Install the service worker
// self.addEventListener('install', (event) => {
//     event.waitUntil(
//         caches.open(CACHE_NAME).then((cache) => {
//             return cache.addAll(CACHE_ASSETS);
//         })
//     );
// });

// // Fetch assets from the cache
// self.addEventListener('fetch', (event) => {
//     event.respondWith(
//         caches.match(event.request).then((response) => {
//             return response || fetch(event.request);
//         })
//     );
// });

// Activate the service worker
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
});
