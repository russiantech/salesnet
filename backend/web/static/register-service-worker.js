// if ('serviceWorker' in navigator) {
//     window.addEventListener('load', () => {
//         navigator.serviceWorker.register('./static/service-worker.js')
//             .then((registration) => {
//                 console.log('Service Worker registered with scope:', registration.scope);
//             })
//             .catch((error) => {
//                 console.log('Service Worker registration failed:', error);
//             });
//     });
// }

// <!-- PWA Manifest -->
// <link rel="manifest" href="{{ url_for('static', filename='manifest.json') }}">

// <!-- Theme color for the app -->
// <meta name="theme-color" content="#317EFB">

// <!-- Service Worker Registration -->


// USING FLASK SYNTAX HERE DID'NT WORK AS service worker is unable to locate: {{ url_for('static', filename='service-worker.js') }} giving errors below:
/*
A bad HTTP response code (404) was received when fetching the script.
 register-service-worker.js:29 Service Worker registration failed: TypeError: Failed to register a ServiceWorker for scope ('http://localhost:8001/') with script ('http://localhost:8001/%7B%7B%20url_for('static',%20filename='service-worker.js')%20%7D%7D'): A bad HTTP response code (404) was received when fetching the script.
*/

//   if ("serviceWorker" in navigator) {
//     navigator.serviceWorker.register("{{ url_for('static', filename='service-worker.js') }}")
//       .then(registration => {
//         console.log("Service Worker registered with scope:", registration.scope);
//       })
//       .catch(error => {
//         console.log("Service Worker registration failed:", error);
//       });
//   }

if ('serviceWorker' in navigator) {
window.addEventListener('load', () => {
    navigator.serviceWorker.register('./static/service-worker.js')
        .then((registration) => {
            console.log('Service Worker registered with scope:', registration.scope);
        })
        .catch((error) => {
            console.log('Service Worker registration failed:', error);
        });
});
}

