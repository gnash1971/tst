/*
 * Service worker du vestiaire numérique LTT.
 *
 * Stratégie :
 *  - navigation (pages) : réseau d'abord, repli sur le cache hors-ligne ;
 *  - actifs statiques same-origin : cache d'abord puis mise à jour en
 *    arrière-plan (stale-while-revalidate).
 *
 * Le numéro de version du cache invalide l'ancien cache à l'activation.
 * Toute modification de ce fichier déclenche une réinstallation du worker.
 */
'use strict';

var VERSION = 'v1';
var CACHE = 'ltt-' + VERSION;

// Coquille minimale préchargée (repli de navigation hors-ligne).
var PRECACHE = ['/', '/index.html', '/404.html'];

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches
            .open(CACHE)
            .then(function (cache) {
                return cache.addAll(PRECACHE);
            })
            .then(function () {
                return self.skipWaiting();
            })
    );
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches
            .keys()
            .then(function (cles) {
                return Promise.all(
                    cles
                        .filter(function (cle) {
                            return cle !== CACHE;
                        })
                        .map(function (cle) {
                            return caches.delete(cle);
                        })
                );
            })
            .then(function () {
                return self.clients.claim();
            })
    );
});

function metEnCache(requete, reponse) {
    // Ne met en cache que les réponses propres et complètes (pas d'opaques).
    if (reponse && reponse.status === 200 && reponse.type === 'basic') {
        var copie = reponse.clone();
        caches.open(CACHE).then(function (cache) {
            cache.put(requete, copie);
        });
    }
    return reponse;
}

self.addEventListener('fetch', function (event) {
    var requete = event.request;

    if (requete.method !== 'GET') {
        return;
    }
    if (new URL(requete.url).origin !== self.location.origin) {
        return;
    }

    if (requete.mode === 'navigate') {
        // Réseau d'abord : la page reste fraîche en ligne, disponible hors-ligne.
        event.respondWith(
            fetch(requete)
                .then(function (reponse) {
                    return metEnCache(requete, reponse);
                })
                .catch(function () {
                    return caches.match(requete).then(function (cache) {
                        return cache || caches.match('/index.html');
                    });
                })
        );
        return;
    }

    // Actifs statiques : cache d'abord, rafraîchissement en arrière-plan.
    event.respondWith(
        caches.match(requete).then(function (cache) {
            var reseau = fetch(requete)
                .then(function (reponse) {
                    return metEnCache(requete, reponse);
                })
                .catch(function () {
                    return cache;
                });
            return cache || reseau;
        })
    );
});
