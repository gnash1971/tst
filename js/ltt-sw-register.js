/*
 * Enregistrement du service worker (cache hors-ligne).
 * Sans effet en file:// : le SW exige https ou localhost.
 */
(function () {
    'use strict';

    if (!('serviceWorker' in navigator)) {
        return;
    }

    var estLocal = location.hostname === 'localhost' || location.hostname === '127.0.0.1';
    if (location.protocol !== 'https:' && !estLocal) {
        return;
    }

    window.addEventListener('load', function () {
        navigator.serviceWorker.register('/sw.js').catch(function () {
            // Échec silencieux : le site reste pleinement fonctionnel sans SW.
        });
    });
})();
