/**
 * Application immédiate du thème (dans <head>, avant le rendu du body).
 */
(function () {
    'use strict';

    // Intercepte et supprime l'avertissement de production du CDN Tailwind CSS
    // en environnement de production (Netlify ou domaine réel)
    var isLocal = window.location.hostname === 'localhost' || 
                  window.location.hostname === '127.0.0.1' || 
                  window.location.protocol === 'file:';
    if (!isLocal) {
        var originalWarn = console.warn;
        console.warn = function () {
            if (arguments[0] && typeof arguments[0] === 'string' && arguments[0].indexOf('cdn.tailwindcss.com') !== -1) {
                return;
            }
            originalWarn.apply(console, arguments);
        };
    }

    try {
        window.LTT.theme.apply(window.LTT.theme.resolveInitial());
    } catch (error) {
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.classList.remove('dark');
    }
})();
